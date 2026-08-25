#!/usr/bin/env python3
"""Unified test runner for the hummbl-io/oss monorepo.

Runs pytest independently across each package in packages/ to avoid root
import and namespace collisions, and aggregates results.
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES_DIR = REPO_ROOT / "packages"


def main() -> int:
    packages = [
        ("hummbl", PACKAGES_DIR / "hummbl"),
        ("hummbl-kernel", PACKAGES_DIR / "hummbl-kernel"),
        ("hummbl-governance", PACKAGES_DIR / "hummbl-governance"),
    ]

    total_failures = 0
    total_ran = 0

    print("=" * 60)
    print("HUMMBL OSS Monorepo Test Runner")
    print("=" * 60)

    for name, path in packages:
        if not path.is_dir() or not (path / "tests").exists():
            continue
        print(f"\n--> Testing package: {name} ({path.relative_to(REPO_ROOT)})")
        cmd = [sys.executable, "-m", "pytest", "tests/", "-q"]
        res = subprocess.run(cmd, cwd=path)
        total_ran += 1
        if res.returncode != 0:
            print(f"[FAIL] Package {name} failed with exit code {res.returncode}")
            total_failures += 1
        else:
            print(f"[PASS] Package {name} passed")

    print("\n" + "=" * 60)
    print(f"Summary: {total_ran} packages tested, {total_failures} failures")
    print("=" * 60)

    return 1 if total_failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
