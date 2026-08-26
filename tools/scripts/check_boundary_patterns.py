#!/usr/bin/env python3
"""Check for internal/private artifacts that must not enter the public repo.

Enforces the AGENTS.md "Public/private boundary" policy by scanning
committed file names for internal artifact naming conventions.

Exits 1 on any match. Exits 0 if clean.

Approach: file-name-based detection is false-positive safe. Content
scanning for broad words like "handoff" or "AAR" produces too many
false positives (comments, .gitignore entries, changelog references).
File names follow strict internal naming conventions that don't
collide with public package file names.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Internal artifact file-name patterns (case-insensitive).
# These match the naming conventions used in private repos for
# handoffs, AARs, receipts, session transcripts, and fleet inventory.
DENYFILE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^HANDOFF[-_]", re.I), "internal handoff document"),
    (re.compile(r"^HANDOFF$", re.I), "internal handoff document"),
    (re.compile(r"^AAR[-_]", re.I), "After Action Review (belongs in private repo)"),
    (re.compile(r"^RECEIPT[-_]", re.I), "internal receipt artifact"),
    (re.compile(r"^SESSION[-_]?(TRANSCRIPT|LOG)", re.I), "session transcript/log"),
    (re.compile(r"^FLEET[-_]?INVENTORY", re.I), "fleet inventory file"),
    (re.compile(r"^AUDIT[-_]?\d", re.I), "internal audit file (dated audit belongs in private repo)"),
    (re.compile(r"^BACKCHANNEL", re.I), "backchannel log"),
    (re.compile(r"^RETIRED[-_]", re.I), "retired/internal retirement index"),
    (re.compile(r"^INTERNAL[-_]", re.I), "internal-only file"),
]

# Directories that indicate internal artifact collections.
DENYDIR_NAMES = {
    "handoffs", "receipts", "backchannel", "session-transcripts",
    "fleet-inventory", "audit-matrices", "internal-infra",
}

# File extensions to scan for content-based checks (fleet topology files).
SCAN_EXTENSIONS = {".json", ".yaml", ".yml"}

# Dirs to skip entirely.
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules",
             ".venv", "venv", "dist", "build", ".eggs", ".mypy_cache"}


def check_filenames(root: Path) -> list[tuple[str, str]]:
    """Check file and directory names against denylist.

    Skips packages/ directory — package code legitimately implements
    'receipt' and 'handoff' as governance domain concepts (receipt_engine.py,
    handoff_event.schema.json, etc.). The concern is internal artifact files
    at the repo root or in docs/, not package source code.
    """
    hits = []
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        # Skip package source code — governance packages legitimately
        # implement receipt/handoff primitives as domain concepts.
        if "packages" in path.parts:
            continue
        name = path.name
        # Skip this script
        if name == "check_boundary_patterns.py":
            continue
        # Check file name against patterns
        for pattern, desc in DENYFILE_PATTERNS:
            if pattern.search(name):
                hits.append((str(path), desc))
                break
        # Check if any parent dir is a denied directory name
        for part in path.parts[:-1]:
            if part.lower() in DENYDIR_NAMES:
                hits.append((str(path), f"file in denied directory '{part}'"))
                break
    return hits


def check_fleet_topology(root: Path) -> list[tuple[str, str]]:
    """Check JSON/YAML files for fleet topology leakage (many repo entries)."""
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Fleet topology files list many repos with git_host or private infra.
        # Flag any file with >20 repo-like entries containing git_host.
        if "git_host" in text and text.count('"name"') > 20:
            hits.append((str(path), "fleet topology file with >20 repo entries and git_host field"))
    return hits


def main() -> int:
    root = Path(".")
    total_hits = 0

    for path_str, desc in check_filenames(root):
        print(f"[DENY] {path_str}: {desc}")
        total_hits += 1

    for path_str, desc in check_fleet_topology(root):
        print(f"[DENY] {path_str}: {desc}")
        total_hits += 1

    if total_hits:
        print()
        print(f"Boundary check FAILED: {total_hits} denylist match(es) found.")
        print("These files match internal/private artifact naming conventions.")
        print("See AGENTS.md 'Public/private boundary'.")
        return 1

    print("Boundary check PASSED: no internal artifacts detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
