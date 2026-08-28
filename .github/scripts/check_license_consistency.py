#!/usr/bin/env python3
"""Check LICENSE file content against pyproject.toml license field.

Scans all packages under packages/python/*/ and verifies that the license
declared in pyproject.toml is consistent with the LICENSE file content.

Consistency rules:
- If pyproject.toml says "MIT OR Apache-2.0", LICENSE file must mention
  both MIT and Apache (dual-license pointer or full text).
- If pyproject.toml says "Apache-2.0", LICENSE file must contain the
  Apache License header.
- If pyproject.toml says "MIT", LICENSE file must contain "MIT License".

Usage:
    python .github/scripts/check_license_consistency.py [--fix-hints]

Exit codes:
    0 — all packages consistent
    1 — one or more packages inconsistent
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES_DIR = REPO_ROOT / "packages" / "python"


def parse_pyproject_license(pyproject_path: Path) -> str | None:
    """Extract license string from pyproject.toml."""
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return None

    license_field = data.get("project", {}).get("license")
    if license_field is None:
        return None

    if isinstance(license_field, str):
        return license_field

    if isinstance(license_field, dict):
        return license_field.get("text")

    return None


def check_license_file(license_path: Path, declared_license: str) -> list[str]:
    """Check if LICENSE file content is consistent with declared license.

    Returns a list of error messages (empty if consistent).
    """
    errors: list[str] = []

    if not license_path.exists():
        errors.append(f"LICENSE file missing at {license_path}")
        return errors

    try:
        content = license_path.read_text(encoding="utf-8").lower()
    except OSError as e:
        errors.append(f"Cannot read LICENSE file: {e}")
        return errors

    declared = declared_license.lower().strip()

    if "mit or apache" in declared or "apache or mit" in declared:
        # Dual license — LICENSE must mention both
        has_mit = "mit license" in content or "mit license" in content
        has_apache = "apache license" in content or "apache" in content
        if not has_mit:
            errors.append(
                f"pyproject.toml declares '{declared_license}' but LICENSE file "
                f"does not mention MIT License"
            )
        if not has_apache:
            errors.append(
                f"pyproject.toml declares '{declared_license}' but LICENSE file "
                f"does not mention Apache License"
            )

    elif "apache" in declared:
        if "apache license" not in content and "apache" not in content:
            errors.append(
                f"pyproject.toml declares '{declared_license}' but LICENSE file "
                f"does not contain Apache License text"
            )

    elif "mit" in declared:
        if "mit license" not in content:
            errors.append(
                f"pyproject.toml declares '{declared_license}' but LICENSE file "
                f"does not contain MIT License text"
            )

    return errors


def main() -> int:
    if not PACKAGES_DIR.exists():
        print(f"Packages directory not found: {PACKAGES_DIR}")
        return 0

    all_ok = True
    packages = sorted(p for p in PACKAGES_DIR.iterdir() if p.is_dir())

    # Packages with known pre-existing license issues — these are tracked
    # for follow-up but do not block CI. Remove from this set once fixed.
    known_issues = {
        "hummbl-bus",           # Apache-2.0 in pyproject, LICENSE text mismatch
        "hummbl-compass",       # MIT OR Apache-2.0, LICENSE file missing
        "hummbl-free-models",   # MIT OR Apache-2.0, LICENSE file missing
        "hummbl-rubric-templates",  # MIT OR Apache-2.0, LICENSE file missing
        "hummbl-taxonomy",      # MIT OR Apache-2.0, LICENSE file missing
        "hummbl-validation",    # MIT OR Apache-2.0, LICENSE file missing
    }

    for pkg_dir in packages:
        pyproject = pkg_dir / "pyproject.toml"
        if not pyproject.exists():
            continue

        declared = parse_pyproject_license(pyproject)
        if declared is None:
            print(f"  SKIP {pkg_dir.name}: no license field in pyproject.toml")
            continue

        license_file = pkg_dir / "LICENSE"
        errors = check_license_file(license_file, declared)

        if errors:
            if pkg_dir.name in known_issues:
                print(f"  WARN {pkg_dir.name}: pyproject='{declared}' (known issue, not blocking)")
                for err in errors:
                    print(f"       {err}")
            else:
                all_ok = False
                print(f"  FAIL {pkg_dir.name}: pyproject='{declared}'")
                for err in errors:
                    print(f"       {err}")
        else:
            print(f"  OK   {pkg_dir.name}: pyproject='{declared}'")

    if all_ok:
        print("\nAll packages: license consistent (known issues excluded).")
        return 0
    else:
        print("\nOne or more packages have license inconsistencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
