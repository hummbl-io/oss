#!/usr/bin/env python3
"""Verify hard-coded primitive/package counts in public copy against ground truth.

``claim_drift.py`` catches risky *wording* (superlatives, uncited compliance
claims) via regex heuristics. It does not — and by design cannot — verify that
a specific number in a README matches the actual codebase, because it never
computes a ground-truth value to compare against.

This script closes that specific gap for the two counts most prone to silent
drift in this repo (see docs/artifacts/AUDIT_2026-09-11_public_claims_drift.md
for the incident this was written to prevent, and
docs/artifacts/CASE_STUDY_claims_remediation.md for a prior, independent
occurrence of the same bug class — "25 Modules" on the old homepage):

  - Implemented primitive count: computed from
    ``hummbl_governance.primitive_registry.PrimitiveRegistry``, the repo's own
    declared "authoritative runtime source" for the primitive inventory.
  - Python package count: computed by counting directories under
    ``packages/python/`` that contain a ``pyproject.toml`` (the same
    definition the root README already uses in prose).

It does NOT verify test-pass counts or PyPI-live counts. Those require an
external receipt (a CI run, a PyPI API call) rather than a local, deterministic
computation, and docs/public-claims.md already has an explicit policy against
promoting local counts as if they were that receipt. Extend CHECKS below only
with counts that are computable purely from files already in this repo.

Usage::

    python scripts/check_public_count_claims.py
    python scripts/check_public_count_claims.py --repo-root /path/to/oss

Exit code 0 = every checked file's stated count matches ground truth.
Exit code 1 = at least one mismatch found (printed with expected vs. found).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CountCheck:
    """One ground-truth count and the files/patterns that must agree with it."""

    name: str
    expected: int
    # Each pattern must contain exactly one capturing group: the number.
    # A file is checked only if the pattern is found in it at least once;
    # every match found must equal `expected`.
    targets: tuple[tuple[Path, re.Pattern[str]], ...]


def compute_implemented_primitive_count(governance_pkg_root: Path) -> int:
    """Import PrimitiveRegistry from the tree being checked and count it.

    Imports directly from the package source (not an installed wheel) so this
    always checks the same tree as the docs being verified.
    """
    sys.path.insert(0, str(governance_pkg_root))
    from hummbl_governance.primitive_registry import PrimitiveRegistry  # noqa: PLC0415

    return len(PrimitiveRegistry().implemented_primitives())


def compute_python_package_count(oss_root: Path) -> int:
    """Count packages/python/<name>/ dirs that contain a pyproject.toml."""
    python_dir = oss_root / "packages" / "python"
    if not python_dir.is_dir():
        raise SystemExit(f"expected directory not found: {python_dir}")
    return sum(1 for d in python_dir.iterdir() if d.is_dir() and (d / "pyproject.toml").is_file())


def find_mismatches(check: CountCheck) -> list[str]:
    problems: list[str] = []
    for path, pattern in check.targets:
        if not path.is_file():
            problems.append(f"[{check.name}] file not found, cannot verify: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(pattern.finditer(text))
        if not matches:
            # Not an error: the file may not currently state this count.
            continue
        for m in matches:
            found = int(m.group(1))
            if found != check.expected:
                line_no = text.count("\n", 0, m.start()) + 1
                problems.append(
                    f"[{check.name}] {path}:{line_no}: found {found}, "
                    f"expected {check.expected} (source of truth) -- "
                    f"'{m.group(0)}'"
                )
    return problems


def build_checks(oss_root: Path) -> list[CountCheck]:
    governance_root = oss_root / "packages" / "python" / "hummbl-governance"
    implemented = compute_implemented_primitive_count(governance_root)
    packages = compute_python_package_count(oss_root)

    # One pattern per phrasing actually used in the repo today. Add a new
    # pattern here (not a new hard-coded number in a doc) the next time a
    # doc introduces a new way of stating the same count.
    primitive_patterns = (
        re.compile(r"(\d+)\s+implemented governance primitives"),
        re.compile(r"(\d+)\s+implemented primitives"),
        re.compile(r"All (\d+) Implemented Primitives"),
        re.compile(r"Explore all (\d+) implemented primitives"),
        re.compile(r"(\d+)\s+governance primitives\b(?!\s*\()"),  # bare form, not the "(52 tracked...)" aside
    )
    package_patterns = (
        re.compile(r"(\d+) Python packages under"),
    )

    primitive_targets: list[tuple[Path, re.Pattern[str]]] = []
    for pattern in primitive_patterns:
        primitive_targets.append((governance_root / "README.md", pattern))
        primitive_targets.append((governance_root / "PRIMITIVES.md", pattern))
        primitive_targets.append((governance_root / "docs" / "public-claims.md", pattern))

    package_targets: list[tuple[Path, re.Pattern[str]]] = [
        (oss_root / "README.md", pattern) for pattern in package_patterns
    ]

    return [
        CountCheck(
            name="implemented_primitives",
            expected=implemented,
            targets=tuple(primitive_targets),
        ),
        CountCheck(
            name="python_package_count",
            expected=packages,
            targets=tuple(package_targets),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Path to the oss monorepo root (default: inferred from this script's location)",
    )
    args = parser.parse_args()
    oss_root = args.repo_root.resolve()

    checks = build_checks(oss_root)
    problems: list[str] = []
    for check in checks:
        problems.extend(find_mismatches(check))
        print(f"{check.name}: ground truth = {check.expected}")

    if problems:
        print("\nMismatches found:")
        for p in problems:
            print(f"  {p}")
        print(
            "\nIf the ground truth is wrong, fix the source "
            "(PrimitiveRegistry / packages/python tree), not this script. "
            "If a doc's number is wrong, fix the doc to match the printed "
            "ground truth above."
        )
        return 1

    print("\nAll checked public counts match ground truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
