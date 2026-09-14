"""L2a: Run CI contract locally before push, scoped to the diff.

This module reads a target repo's ci/contract.v1.json (or equivalent) and
runs the relevant checks locally before the push reaches remote CI. The
goal is to catch defects at the start of the river rather than downstream.

Scoping: the contract is filtered to checks relevant to the diff. A test-only
change runs test+lint but skips install-smoke and arbiter. A workflow change
runs only the pre-push-ci-check subset. This reduces local run time and
focuses on what matters.

If no ci/contract.v1.json exists in the target repo, falls back to running
the standard checks (test, lint) if the tooling is available.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence


@dataclass
class CheckResult:
    """Result of running a single CI check locally."""

    check_id: str
    authority: str  # "required" or "advisory"
    passed: bool
    output: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class LocalCIResult:
    """Aggregate result of running the CI contract locally."""

    repo: str
    checks_run: list[CheckResult] = field(default_factory=list)
    all_passed: bool = True
    skipped: list[str] = field(default_factory=list)

    @property
    def required_passed(self) -> bool:
        return all(c.passed for c in self.checks_run if c.authority == "required")

    def summary(self) -> str:
        lines = [f"Local CI: {self.repo}"]
        for c in self.checks_run:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  {status} {c.check_id} ({c.authority}) {c.duration_seconds:.1f}s")
        if self.skipped:
            lines.append(f"  SKIP {', '.join(self.skipped)}")
        lines.append(f"  Overall: {'PASS' if self.required_passed else 'FAIL'}")
        return "\n".join(lines)


def load_contract(repo_path: Path) -> Optional[dict]:
    """Load ci/contract.v1.json from the target repo.

    Returns None if no contract file exists.
    """
    contract_path = repo_path / "ci" / "contract.v1.json"
    if not contract_path.exists():
        return None
    with open(contract_path) as f:
        return json.load(f)


def get_diff_files(
    repo_path: Path, base: str = "origin/main", head: str = "HEAD"
) -> list[str]:
    """Get the list of changed files relative to base.

    ``head`` is the commit whose changes are being pushed (passed by the
    pre-push hook); defaults to ``HEAD`` (the checkout) for interactive use.
    """
    if head and head != "HEAD":
        # Diff against the merge-base so only the branch's own changes are
        # seen — not unrelated changes that landed on base since the branch
        # diverged (origin/main advances while a branch sits un-pushed).
        mb = subprocess.run(
            ["git", "merge-base", base, head],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if mb.returncode == 0 and mb.stdout.strip():
            base = mb.stdout.strip()
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Fall back to staged + unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
    return [f for f in result.stdout.strip().split("\n") if f]


def scope_checks(contract: dict, diff_files: Sequence[str]) -> list[dict]:
    """Determine which checks to run based on the diff.

    Scoping rules:
    - If all changes are docs-only (.md, docs/, _internal/): skip all checks
    - If changes include .github/workflows/: run ci-pinning checks
    - If changes include .py files: run test + lint
    - If changes include scripts/: run security
    - install-smoke and arbiter-governance: only with --full-contract
    """
    checks = contract.get("checks", [])
    docs_config = contract.get("docs_only", {})
    docs_dirs = set(docs_config.get("directories", []))
    docs_suffixes = set(docs_config.get("suffixes", []))

    def is_docs_file(path: str) -> bool:
        if any(path.startswith(d + "/") or path == d for d in docs_dirs):
            return True
        return any(path.endswith(s) for s in docs_suffixes)

    if not diff_files:
        return []

    all_docs = all(is_docs_file(f) for f in diff_files)
    if all_docs:
        return []

    has_python = any(f.endswith(".py") for f in diff_files)
    has_workflows = any(f.startswith(".github/workflows/") for f in diff_files)
    has_scripts = any(f.startswith("scripts/") for f in diff_files)

    scoped = []
    for check in checks:
        cid = check["id"]
        if cid == "test" and has_python:
            scoped.append(check)
        elif cid == "lint" and has_python:
            scoped.append(check)
        elif cid == "security" and (has_python or has_scripts):
            scoped.append(check)
        elif cid in ("install-smoke", "arbiter-governance", "coverage-matrix-validate"):
            # Skip expensive checks unless --full-contract
            continue
        elif has_workflows and cid == "lint":
            scoped.append(check)
        else:
            # Include check if it's not explicitly skipped
            if cid not in ("install-smoke", "arbiter-governance", "coverage-matrix-validate"):
                scoped.append(check)

    return scoped


def run_check(check: dict, repo_path: Path, python_exe: str) -> CheckResult:
    """Run a single CI check locally."""
    import time

    check_id = check["id"]
    authority = check.get("authority", "required")
    commands = check.get("commands", [])
    timeout = check.get("timeout_seconds", 300)

    start = time.monotonic()
    output_parts = []
    error = None

    for cmd in commands:
        resolved = [python_exe if c == "{python}" else c for c in cmd]
        try:
            result = subprocess.run(
                resolved,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                error = result.stderr or result.stdout
                return CheckResult(
                    check_id=check_id,
                    authority=authority,
                    passed=False,
                    output=result.stdout,
                    duration_seconds=time.monotonic() - start,
                    error=error,
                )
            output_parts.append(result.stdout)
        except subprocess.TimeoutExpired:
            return CheckResult(
                check_id=check_id,
                authority=authority,
                passed=False,
                output="",
                duration_seconds=time.monotonic() - start,
                error=f"timed out after {timeout}s",
            )
        except FileNotFoundError as e:
            return CheckResult(
                check_id=check_id,
                authority=authority,
                passed=False,
                output="",
                duration_seconds=time.monotonic() - start,
                error=f"command not found: {e}",
            )

    return CheckResult(
        check_id=check_id,
        authority=authority,
        passed=True,
        output="\n".join(output_parts),
        duration_seconds=time.monotonic() - start,
    )


def run_local_ci(
    repo_path: Path,
    full_contract: bool = False,
    python_exe: Optional[str] = None,
    head: Optional[str] = None,
) -> LocalCIResult:
    """Run the CI contract locally, scoped to the diff.

    Args:
        repo_path: Path to the target repo.
        full_contract: If True, run all checks including install-smoke and arbiter.
        python_exe: Python executable to use. Defaults to sys.executable.

    Returns:
        LocalCIResult with per-check results.
    """
    if python_exe is None:
        python_exe = sys.executable

    repo_path = Path(repo_path).resolve()
    result = LocalCIResult(repo=str(repo_path))

    contract = load_contract(repo_path)
    if contract is None:
        # No contract file — check if diff is docs-only before running tests
        diff_files = get_diff_files(repo_path, head=head or "HEAD")
        if not diff_files or _is_docs_only(diff_files):
            # Empty diff (tag push, no remote) or docs-only — skip tests
            result.skipped = ["test", "lint"] if diff_files else []
            result.all_passed = True
            return result
        # Not docs-only — run basic test + lint if available
        result.checks_run.append(_run_basic_test(repo_path, python_exe))
        result.checks_run.append(_run_basic_lint(repo_path, python_exe))
        result.all_passed = result.required_passed
        return result

    diff_files = get_diff_files(repo_path, head=head or "HEAD")

    if full_contract:
        checks_to_run = contract.get("checks", [])
    else:
        checks_to_run = scope_checks(contract, diff_files)
        skipped_ids = {
            c["id"] for c in contract.get("checks", [])
        } - {c["id"] for c in checks_to_run}
        result.skipped = sorted(skipped_ids)

    if not checks_to_run:
        result.all_passed = True
        return result

    for check in checks_to_run:
        cr = run_check(check, repo_path, python_exe)
        result.checks_run.append(cr)
        if not cr.passed and cr.authority == "required":
            result.all_passed = False

    return result


def _is_docs_only(diff_files: Sequence[str]) -> bool:
    """Check if all changed files are docs-only (no code changes).

    Used by the no-contract fallback path to skip pytest for docs-only pushes.
    Considers these docs-only: .md, .txt, .rst, .adoc, LICENSE, CHANGELOG,
    files under docs/, .github/ (workflows/ISSUE_TEMPLATE), and image files.
    """
    docs_suffixes = {".md", ".txt", ".rst", ".adoc", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
    docs_names = {"LICENSE", "CHANGELOG", "CODE_OF_CONDUCT", "CONTRIBUTING", "SECURITY"}
    docs_prefixes = ("docs/", ".github/", "_internal/")

    for f in diff_files:
        if f in docs_names:
            continue
        if any(f.startswith(p) for p in docs_prefixes):
            continue
        if any(f.endswith(s) for s in docs_suffixes):
            continue
        return False
    return True


def _run_basic_test(repo_path: Path, python_exe: str) -> CheckResult:
    """Fallback: run pytest if no contract exists."""
    import time

    start = time.monotonic()
    try:
        result = subprocess.run(
            [python_exe, "-m", "pytest", "tests/", "-x", "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return CheckResult(
            check_id="test",
            authority="required",
            passed=result.returncode == 0,
            output=result.stdout,
            duration_seconds=time.monotonic() - start,
            error=result.stderr if result.returncode != 0 else None,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return CheckResult(
            check_id="test",
            authority="required",
            passed=False,
            duration_seconds=time.monotonic() - start,
            error=str(e),
        )


def _run_basic_lint(repo_path: Path, python_exe: str) -> CheckResult:
    """Fallback: run ruff if no contract exists."""
    import time

    start = time.monotonic()
    try:
        result = subprocess.run(
            [python_exe, "-m", "ruff", "check", "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return CheckResult(
            check_id="lint",
            authority="required",
            passed=result.returncode == 0,
            output=result.stdout,
            duration_seconds=time.monotonic() - start,
            error=result.stderr if result.returncode != 0 else None,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return CheckResult(
            check_id="lint",
            authority="required",
            passed=False,
            duration_seconds=time.monotonic() - start,
            error=str(e),
        )
