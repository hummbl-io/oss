#!/usr/bin/env python3
"""Pre-flight check: fail if test files exist in the working tree but are
not tracked by git.

Origin: hummbl-cognition PR #21 committed 52 test files that were sitting
untracked in the working tree. CI ran ``pytest tests/`` but only 114 tests
executed (the 8 tracked files) instead of the full 1791 — the 47 untracked
test files were invisible to CI because they were never committed. This
script catches that class of bug at pre-flight time.

Usage::

    python scripts/validation/check_untracked_tests.py            # scan cwd
    python scripts/validation/check_untracked_tests.py /path       # scan a tree

The script shells out to ``git ls-files`` and ``git status`` to determine
which files under ``tests/`` are tracked. It exits non-zero if any
``test_*.py`` or ``*_test.py`` file is untracked.

Exit codes:
    0 — no untracked test files (or not a git repo)
    1 — untracked test files found
    2 — usage error
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TEST_PATTERNS = ("test_*.py", "*_test.py")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def _is_test_file(path: Path) -> bool:
    name = path.name
    return (
        (name.startswith("test_") and name.endswith(".py"))
        or (name.endswith("_test.py"))
    )


def check_repo(repo: Path) -> list[Path]:
    """Return a list of untracked test files under ``repo/tests/``."""
    # Confirm this is a git repo
    toplevel = _git(repo, "rev-parse", "--show-toplevel")
    if not toplevel:
        return []

    repo_root = Path(toplevel)

    # Get all untracked files. `git status --porcelain` collapses untracked
    # directories into a single "?? dir/" entry, which hides individual files.
    # `git ls-files --others --exclude-standard` lists every untracked file
    # individually (respecting .gitignore).
    listing = _git(repo_root, "ls-files", "--others", "--exclude-standard")
    untracked: list[Path] = []
    for line in listing.splitlines():
        raw = line.strip().strip('"')
        if not raw:
            continue
        p = repo_root / raw
        if not p.is_file():
            continue
        # Only care about files under a tests/ directory
        try:
            p.relative_to(repo_root / "tests")
        except ValueError:
            continue
        if _is_test_file(p):
            untracked.append(p)

    return sorted(untracked)


def main(argv: list[str]) -> int:
    args = argv[1:]
    repo = Path(args[0]).resolve() if args else Path.cwd()

    if not repo.exists():
        print(f"path not found: {repo}", file=sys.stderr)
        return 2

    untracked = check_repo(repo)
    if not untracked:
        print("no untracked test files found")
        return 0

    print(f"FAIL: {len(untracked)} untracked test file(s) found:", file=sys.stderr)
    for p in untracked:
        print(f"  {p}", file=sys.stderr)
    print(
        "\nThese test files exist in the working tree but are not committed.\n"
        "CI will not run them. Stage and commit them before pushing.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
