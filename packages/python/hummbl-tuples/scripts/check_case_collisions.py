#!/usr/bin/env python3
"""Detect case-collision paths in the git-tracked file index.

On case-insensitive filesystems (Windows, macOS default), two git-tracked
paths that differ only by letter case (e.g. ``docs/specs/`` and
``DOCS/specs/``) silently collide to the same on-disk directory. This
causes files to be staged under the wrong path, breaking tests and CI
on case-sensitive systems (Linux) while appearing to work locally.

This script scans ``git ls-files`` output and fails if any two tracked
paths collide case-insensitively.

Usage::

    python scripts/check_case_collisions.py          # scan repo
    python scripts/check_case_collisions.py --strict  # exit 1 on any collision

Exit codes:
    0 — no collisions found
    1 — collision(s) found (with --strict, or always when run in CI)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Known pre-existing case collisions that are grandfathered in.
# Any NEW collision not in this list will fail the check.
# Format: lowercase path that has multiple case variants
KNOWN_COLLISIONS_FILE = "scripts/case_collision_known.txt"


def load_known_collisions() -> set[str]:
    """Load the list of known pre-existing case collisions to skip."""
    known_path = REPO_ROOT / KNOWN_COLLISIONS_FILE
    if not known_path.exists():
        return set()
    lines = known_path.read_text(encoding="utf-8").splitlines()
    return {line.strip().lower() for line in lines if line.strip() and not line.startswith("#")}


def get_tracked_files() -> list[str]:
    """Return the list of git-tracked files."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def find_case_collisions(files: list[str]) -> dict[str, list[str]]:
    """Group tracked paths by their lowercase form and return collisions.

    Returns a dict mapping lowercase_path -> list of actual paths that
    collide on that lowercase form (length > 1 means a collision).
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for f in files:
        groups[f.lower()].append(f)
    return {key: sorted(vals) for key, vals in groups.items() if len(vals) > 1}


def find_directory_collisions(files: list[str]) -> dict[str, list[str]]:
    """Detect directory-level case collisions.

    Two files in directories that differ only by case (e.g.
    ``docs/specs/foo.md`` and ``DOCS/specs/bar.md``) will collide on
    case-insensitive filesystems even if the filenames differ.
    """
    dir_groups: dict[str, list[str]] = defaultdict(list)
    for f in files:
        parts = f.split("/")
        # Check each directory level prefix
        for i in range(len(parts) - 1):
            prefix = "/".join(parts[: i + 1])
            dir_groups[prefix.lower()].append(prefix)

    collisions: dict[str, list[str]] = {}
    for key, vals in dir_groups.items():
        unique_dirs = sorted(set(vals))
        if len(unique_dirs) > 1:
            collisions[key] = unique_dirs
    return collisions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect case-collision paths in git-tracked files."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any collision is found.",
    )
    args = parser.parse_args()

    # In CI, always be strict
    is_ci = os.environ.get("CI") is not None or os.environ.get("GITHUB_ACTIONS") == "true"
    strict = args.strict or is_ci

    files = get_tracked_files()
    if not files:
        print("No tracked files found. Is this a git repo?")
        return 1

    known = load_known_collisions()

    file_collisions = find_case_collisions(files)
    dir_collisions = find_directory_collisions(files)

    # Filter out known pre-existing collisions
    new_file_collisions = {k: v for k, v in file_collisions.items() if k not in known}
    new_dir_collisions = {k: v for k, v in dir_collisions.items() if k not in known}

    # Report known collisions as warnings
    if known:
        known_file = {k: v for k, v in file_collisions.items() if k in known}
        known_dir = {k: v for k, v in dir_collisions.items() if k in known}
        if known_file or known_dir:
            print(f"INFO: {len(known_file) + len(known_dir)} known pre-existing collision(s) skipped:")
            for lower, actuals in sorted(known_file.items()):
                print(f"  [known] {lower} -> {actuals}")
            for lower, actuals in sorted(known_dir.items()):
                print(f"  [known] {lower} -> {actuals}")
            print(f"       (listed in {KNOWN_COLLISIONS_FILE})")
            print()

    if not new_file_collisions and not new_dir_collisions:
        print(f"OK: No new case collisions found among {len(files)} tracked files.")
        return 0

    exit_code = 0
    if new_file_collisions:
        print("FAIL: New file-level case collisions detected:")
        for lower, actuals in sorted(new_file_collisions.items()):
            print(f"  {lower} -> {actuals}")
        exit_code = 1

    if new_dir_collisions:
        print("FAIL: New directory-level case collisions detected:")
        for lower, actuals in sorted(new_dir_collisions.items()):
            print(f"  {lower} -> {actuals}")
        exit_code = 1

    if exit_code and strict:
        return 1

    if exit_code and not strict:
        print("\n(Warnings only — run with --strict or in CI to fail.)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
