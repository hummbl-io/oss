#!/usr/bin/env python3
"""Pre-push CI check — catch common CI-blocking issues before pushing.

Runs locally before `git push` to catch:
1. SHA-pinning violations — GitHub Actions `uses:` refs that are not SHA-pinned
2. Disallowed actions — mutable refs (@main, @v4) or known-deprecated actions
3. Branch protection check name mismatches — workflow job names that don't
   match the required status checks configured on the target branch

Usage:
    python scripts/pre-push-ci-check.py [--repo .] [--strict]

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
    2 — --strict mode and warnings were found
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
USES_PATTERN = re.compile(r"^\s*(?:-\s+)?uses:\s+(\S+)")

# Actions that are known-deprecated or should never be used
DISALLOWED_ACTIONS: set[str] = {
    "actions/checkout@v1",
    "actions/checkout@v2",
    "actions/checkout@v3",
    "actions/setup-python@v1",
    "actions/setup-python@v2",
    "actions/setup-python@v3",
    "actions/setup-python@v4",
    "actions/upload-artifact@v1",
    "actions/upload-artifact@v2",
    "actions/upload-artifact@v3",
    "actions/download-artifact@v1",
    "actions/download-artifact@v2",
    "actions/download-artifact@v3",
    "actions/github-script@v1",
    "actions/github-script@v2",
    "actions/github-script@v3",
}

# Mutable ref suffixes that should never appear in production workflows
MUTABLE_REFS = ("@main", "@master", "@latest", "@HEAD")


@dataclass
class Finding:
    check: str
    severity: str  # "error" or "warning"
    file: str
    message: str


@dataclass
class CheckResult:
    name: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def parse_workflow_uses(text: str) -> list[tuple[int, str]]:
    """Extract (line_number, action_ref) pairs from workflow text."""
    results: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        m = USES_PATTERN.match(line)
        if m:
            results.append((i, m.group(1)))
    return results


def extract_job_names(text: str) -> dict[str, str]:
    """Extract job_id -> display_name mapping from workflow text.

    Returns dict where keys are job IDs and values are the `name:` field
    (or the job ID itself if no name is specified).
    """
    jobs: dict[str, str] = {}
    current_job: str | None = None
    in_jobs = False
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue
        # Detect top-level `jobs:` key
        if re.match(r"^jobs:\s*$", stripped):
            in_jobs = True
            current_job = None
            continue
        # Exit jobs block on next top-level key
        if in_jobs and not line.startswith(" ") and not line.startswith("\t"):
            in_jobs = False
            current_job = None
            continue
        if not in_jobs:
            continue
        # Job key (indented 2 spaces, ends with colon)
        m = re.match(r"^  (\w[\w-]*)\s*:", stripped)
        if m:
            current_job = m.group(1)
            jobs[current_job] = current_job
            continue
        # Name field inside a job (indented 4+ spaces)
        if current_job:
            nm = re.match(r"^ {4,}name:\s+(.+)$", stripped)
            if nm:
                jobs[current_job] = nm.group(1).strip().strip('"').strip("'")
    return jobs


def check_sha_pinning(workflow_path: Path, root: Path) -> list[Finding]:
    """Check that all `uses:` refs in GitHub workflows are SHA-pinned."""
    findings: list[Finding] = []
    rel = workflow_path.relative_to(root / ".github" / "workflows")
    text = workflow_path.read_text(encoding="utf-8", errors="replace")

    for line_no, ref in parse_workflow_uses(text):
        # Local action paths (./ or .//) are fine
        if ref.startswith("./"):
            continue
        # Docker images (docker://) are out of scope
        if ref.startswith("docker://"):
            continue

        action_name, _, version = ref.partition("@")
        if not version:
            findings.append(
                Finding(
                    check="sha-pinning",
                    severity="error",
                    file=str(rel),
                    message=f"line {line_no}: {ref} has no @ref — must be SHA-pinned",
                )
            )
            continue

        # Check for mutable refs
        if any(version.endswith(suffix) for suffix in MUTABLE_REFS):
            findings.append(
                Finding(
                    check="sha-pinning",
                    severity="error",
                    file=str(rel),
                    message=f"line {line_no}: {ref} uses mutable ref '{version}' — pin to SHA",
                )
            )
            continue

        # Check if it's a SHA (40-char hex)
        if SHA_PATTERN.match(version):
            continue

        # Tag refs like v4, v7.0.1 — not SHA-pinned
        findings.append(
            Finding(
                check="sha-pinning",
                severity="error",
                file=str(rel),
                message=f"line {line_no}: {ref} uses tag '{version}' — pin to 40-char SHA",
            )
        )

    return findings


def check_disallowed_actions(workflow_path: Path, root: Path) -> list[Finding]:
    """Check for explicitly disallowed actions."""
    findings: list[Finding] = []
    rel = workflow_path.relative_to(root / ".github" / "workflows")
    text = workflow_path.read_text(encoding="utf-8", errors="replace")

    for line_no, ref in parse_workflow_uses(text):
        if ref in DISALLOWED_ACTIONS:
            findings.append(
                Finding(
                    check="disallowed-actions",
                    severity="error",
                    file=str(rel),
                    message=f"line {line_no}: {ref} is disallowed — use SHA-pinned version",
                )
            )

    return findings


def check_branch_protection_names(ci_workflow_path: Path, root: Path) -> list[Finding]:
    """Check that the ci aggregate job exists and matches branch protection.

    If `gh` CLI is available and authenticated, queries the branch protection
    configuration and verifies that every required check name appears as a
    job in the primary CI workflow.
    """
    findings: list[Finding] = []
    if not ci_workflow_path.exists():
        findings.append(
            Finding(
                check="branch-protection",
                severity="error",
                file=".github/workflows/ci.yml",
                message="primary CI workflow not found",
            )
        )
        return findings

    text = ci_workflow_path.read_text(encoding="utf-8", errors="replace")
    job_names = extract_job_names(text)

    # The ci aggregate job must exist
    if "ci" not in job_names:
        findings.append(
            Finding(
                check="branch-protection",
                severity="error",
                file=".github/workflows/ci.yml",
                message="no 'ci' aggregate job found — branch protection requires it",
            )
        )

    # Try to query branch protection via gh CLI
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{_get_repo_slug(root)}/branches/main/protection",
                "--jq",
                ".required_status_checks.contexts[]?",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            findings.append(
                Finding(
                    check="branch-protection",
                    severity="warning",
                    file=".github/workflows/ci.yml",
                    message="could not query branch protection via gh CLI — skipping cross-check",
                )
            )
            return findings

        required_checks = [c.strip() for c in result.stdout.splitlines() if c.strip()]
        for check_name in required_checks:
            if check_name not in job_names.values() and check_name not in job_names:
                findings.append(
                    Finding(
                        check="branch-protection",
                        severity="error",
                        file=".github/workflows/ci.yml",
                        message=f"required check '{check_name}' not found in workflow jobs",
                    )
                )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        findings.append(
            Finding(
                check="branch-protection",
                severity="warning",
                file=".github/workflows/ci.yml",
                message="gh CLI not available — skipping branch protection cross-check",
            )
        )

    return findings


def _get_repo_slug(root: Path) -> str:
    """Extract org/repo slug from git remote origin URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=5,
        )
        url = result.stdout.strip()
        # Handle SSH (git@github.com:org/repo.git) and HTTPS (https://github.com/org/repo.git)
        if url.startswith("git@"):
            path = url.split(":", 1)[1]
        else:
            path = url.split("/", 3)[-1] if "/" in url else ""
        path = path.removesuffix(".git")
        return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def run_checks(root: Path) -> list[CheckResult]:
    """Run all pre-push checks and return results."""
    results: list[CheckResult] = []
    workflows_dir = root / ".github" / "workflows"

    if not workflows_dir.exists():
        results.append(
            CheckResult(
                name="workflows-dir",
                findings=[
                    Finding(
                        check="workflows-dir",
                        severity="error",
                        file=".github/workflows/",
                        message="no .github/workflows/ directory found",
                    )
                ],
            )
        )
        return results

    workflow_files = sorted(f for f in workflows_dir.iterdir() if f.suffix in (".yml", ".yaml"))

    # Check 1: SHA pinning
    sha_findings: list[Finding] = []
    for wf in workflow_files:
        sha_findings.extend(check_sha_pinning(wf, root))
    results.append(CheckResult(name="sha-pinning", findings=sha_findings))

    # Check 2: Disallowed actions
    disallowed_findings: list[Finding] = []
    for wf in workflow_files:
        disallowed_findings.extend(check_disallowed_actions(wf, root))
    results.append(CheckResult(name="disallowed-actions", findings=disallowed_findings))

    # Check 3: Branch protection check names
    ci_workflow = workflows_dir / "ci.yml"
    bp_findings = check_branch_protection_names(ci_workflow, root)
    results.append(CheckResult(name="branch-protection", findings=bp_findings))

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-push CI check — catch SHA-pinning, disallowed actions, "
        "and branch protection mismatches before pushing"
    )
    parser.add_argument("--repo", default=".", help="Repository root (default: .)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if warnings are found (not just errors)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    results = run_checks(root)

    has_errors = False
    has_warnings = False

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}")
        for f in result.findings:
            marker = "ERROR" if f.severity == "error" else "WARN"
            print(f"  {marker} {f.file}: {f.message}")
        if any(f.severity == "error" for f in result.findings):
            has_errors = True
        if any(f.severity == "warning" for f in result.findings):
            has_warnings = True

    print()
    if has_errors:
        print("RESULT: FAIL — fix errors before pushing")
        return 1
    if has_warnings and args.strict:
        print("RESULT: FAIL (strict) — warnings found in strict mode")
        return 2
    if has_warnings:
        print("RESULT: PASS (with warnings)")
    else:
        print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
