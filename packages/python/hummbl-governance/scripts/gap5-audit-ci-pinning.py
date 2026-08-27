#!/usr/bin/env python3
"""Gap-5: Audit CI workflows for unpinned GitHub Actions.

Checks all .github/workflows/*.yml files for GitHub Actions that use
floating tags (e.g., v4) instead of SHA-pinned references (e.g.,
@abc123def456...). SHA pinning prevents supply chain attacks where a
compromised tag is moved to malicious code.

Usage:
    python scripts/gap5-audit-ci-pinning.py [--repo PATH]
    python scripts/gap5-audit-ci-pinning.py --strict  # exit 1 on violations

NIST 800-53 CM-6 (Configuration Settings), SI-7 (Software Integrity),
SLSA Level 2+.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Pattern: uses: owner/repo@ref
# Pinned: uses: actions/checkout@abc123def4567890abcdef1234567890abcdef1234 # v4.2.2
# Unpinned: uses: actions/checkout@v4 or uses: actions/checkout@main
USES_PATTERN = re.compile(r"uses:\s*([^\s]+)@([^\s]+)")

# SHA is 40 hex chars
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

# Floating tags: v1, v1.2, v1.2.3, main, master, latest
FLOATING_PATTERN = re.compile(r"^(v\d+|v\d+\.\d+|v\d+\.\d+\.\d+|main|master|latest)$")


def audit_workflow(filepath: Path) -> list[dict]:
    """Audit a single workflow file for unpinned actions.

    Returns list of violations (dicts with line, action, ref).
    """
    violations = []
    with open(filepath, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            match = USES_PATTERN.search(line)
            if not match:
                continue

            action = match.group(1)
            ref = match.group(2)

            # Check if ref is a SHA (40 hex chars)
            if SHA_PATTERN.match(ref):
                continue  # Pinned — OK

            # Check if ref is a floating tag
            if FLOATING_PATTERN.match(ref):
                violations.append({
                    "file": str(filepath),
                    "line": line_num,
                    "action": action,
                    "ref": ref,
                    "issue": "floating tag (not SHA-pinned)",
                })
            elif ref.startswith("refs/tags/") or ref.startswith("refs/heads/"):
                violations.append({
                    "file": str(filepath),
                    "line": line_num,
                    "action": action,
                    "ref": ref,
                    "issue": "branch/tag ref (not SHA-pinned)",
                })
            # Local actions (./path) are OK
            elif action.startswith("./"):
                continue

    return violations


def audit_repo(repo_path: Path) -> list[dict]:
    """Audit all workflow files in a repo.

    Returns list of all violations across all workflow files.
    """
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.exists():
        return []

    all_violations = []
    for wf in workflows_dir.glob("*.yml"):
        all_violations.extend(audit_workflow(wf))
    for wf in workflows_dir.glob("*.yaml"):
        all_violations.extend(audit_workflow(wf))

    return all_violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit CI workflows for unpinned actions")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 if any violations found")
    args = parser.parse_args()

    repo_path = Path(args.repo)
    violations = audit_repo(repo_path)

    print("CI Action SHA Pinning Audit")
    print(f"  Repo: {repo_path.resolve()}")

    if not violations:
        print("  Status: ALL PINNED (SHA)")
        print("  Violations: 0")
        return 0

    print(f"  Status: {len(violations)} UNPINNED action(s)")
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    {v['file']}:{v['line']} - {v['action']}@{v['ref']} ({v['issue']})")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
