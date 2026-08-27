#!/usr/bin/env python3
"""Validate that registry entries with exists:true actually exist on disk.

Bulk text replacement (e.g. founder-mode -> hummbl-governance) rewrites paths
syntactically but cannot update boolean flags. This script catches stale
``exists: true`` flags before test time by checking the filesystem.

Usage::

    python scripts/validate_registry_paths.py [path/to/registry.json]

Exit code 0 = all exists:true paths verified, 1 = mismatches found.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def _entries_with_paths(registry):
    """Yield (entry_index, path_index, path_obj) for entries[].paths[]."""
    if not isinstance(registry, dict):
        return
    for ei, entry in enumerate(registry.get("entries", [])):
        if not isinstance(entry, dict):
            continue
        for pi, p in enumerate(entry.get("paths", [])):
            if isinstance(p, dict):
                yield ei, pi, p


def validate(registry_path: Path, repo_root: Path) -> int:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    mismatches = []
    checked = 0
    for ei, pi, p in _entries_with_paths(data):
        if not p.get("exists_checked"):
            continue
        declared = p.get("exists")
        rel = p.get("path")
        if not rel:
            continue
        # Resolve relative to repo root; paths are repo-relative.
        # Glob patterns are matched against the filesystem.
        if any(c in rel for c in "*?"):
            matches = glob.glob(str(repo_root / rel))
            actual = len(matches) > 0
        else:
            resolved = (repo_root / rel).resolve()
            actual = resolved.exists()
        checked += 1
        if declared and not actual:
            mismatches.append(f"  entries[{ei}].paths[{pi}] path={rel} exists=true but NOT FOUND on disk")
        elif not declared and actual:
            mismatches.append(f"  entries[{ei}].paths[{pi}] path={rel} exists=false but FOUND on disk")
    print(f"Checked {checked} paths in {registry_path.name}")
    if mismatches:
        print(f"FAIL: {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(m)
        return 1
    print("OK: all exists flags match filesystem")
    return 0


def main(argv):
    repo_root = Path(__file__).resolve().parent.parent
    default = repo_root / "docs" / "memory_system_registry.candidate.json"
    target = Path(argv[1]) if len(argv) > 1 else default
    if not target.is_file():
        print(f"registry not found: {target}")
        return 2
    return validate(target, repo_root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
