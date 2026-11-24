#!/usr/bin/env python3
"""Verify public primitive/package counts and tree versions against ground truth.

``claim_drift.py`` catches risky *wording* (superlatives, uncited compliance
claims) via regex heuristics. It does not — and by design cannot — verify that
a specific number in a README matches the actual codebase, because it never
computes a ground-truth value to compare against.

This script closes that specific gap for the two counts most prone to silent
drift in this repo (written after the 2026-09-11 "34 primitives" public-claims
drift incident — the audit narrative is retained in the internal archive, not
published here — and docs/artifacts/CASE_STUDY_claims_remediation.md documents
a prior, independent occurrence of the same bug class — "25 Modules" on the
old homepage):

  - Implemented primitive count: computed from
    ``hummbl_governance.primitive_registry.PrimitiveRegistry``, the repo's own
    declared "authoritative runtime source" for the primitive inventory.
  - Python package count: computed by counting directories under
    ``packages/python/`` that contain a ``pyproject.toml`` (the same
    definition the root README already uses in prose).
  - README Python package tree versions: compared with ``[project].version``
    in each package's ``pyproject.toml``; every package must have a table row.

It does NOT verify test-pass counts or PyPI-live counts. Those require an
external receipt (a CI run, a PyPI API call) rather than a local, deterministic
computation, and docs/public-claims.md already has an explicit policy against
promoting local counts as if they were that receipt. Extend CHECKS below only
with counts that are computable purely from files already in this repo.

Usage::

    python scripts/check_public_count_claims.py
    python scripts/check_public_count_claims.py --repo-root /path/to/oss

Exit code 0 = every checked count and tree version matches ground truth.
Exit code 1 = at least one mismatch found (printed with expected vs. found).
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
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
        matches = _iter_count_matches(pattern, text)
        if not matches:
            # Not an error: the file may not currently state this count.
            continue
        for line_no, m in matches:
            found = int(m.group(1))
            if found != check.expected:
                problems.append(
                    f"[{check.name}] {path}:{line_no}: found {found}, "
                    f"expected {check.expected} (source of truth) -- "
                    f"'{m.group(0)}'"
                )
    return problems


_SCOPE_PREFIX = r"(?m)^(?=[^\n]*hummbl-governance)[^\n]*?"


def _governance_scoped(pattern: re.Pattern[str]) -> re.Pattern[str]:
    """Restrict a count pattern to lines that name hummbl-governance.

    Other package READMEs describe their own primitives (base120's reasoning
    primitives, a package's own capability count); only a statement about
    hummbl-governance may be compared to the governance total (review on #527).
    """
    return re.compile(_SCOPE_PREFIX + pattern.pattern, pattern.flags)


def _iter_count_matches(
    pattern: re.Pattern[str], text: str
) -> list[tuple[int, re.Match[str]]]:
    """Every count occurrence, as (1-based line number, match).

    The scoped line-start prefix consumes text, so applying it to the whole
    document with ``finditer`` finds only the first count on a line: after the
    first match ends, ``^`` cannot match mid-line again. Scanning line by line
    with the prefix stripped yields every count on a qualifying line (review
    on #527).
    """
    src = pattern.pattern
    scoped = src.startswith(_SCOPE_PREFIX)
    body = src[len(_SCOPE_PREFIX):] if scoped else src
    body_re = re.compile(body, pattern.flags & ~re.MULTILINE)
    found: list[tuple[int, re.Match[str]]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if scoped and "hummbl-governance" not in line:
            continue
        found.extend((line_no, m) for m in body_re.finditer(line))
    return found


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
        primitive_targets.append((governance_root / "ROADMAP.md", pattern))
        primitive_targets.append((governance_root / "docs" / "public-claims.md", pattern))
        primitive_targets.append((oss_root / "docs" / "architecture" / "NOMENCLATURE.md", pattern))
    primitive_targets.append((governance_root / "docs" / "hero.svg", re.compile(r"(\d+)\s+(?:implemented\s+)?primitives\b")))

    python_packages_dir = oss_root / "packages" / "python"
    if python_packages_dir.is_dir():
        for pkg_dir in sorted(python_packages_dir.iterdir()):
            if pkg_dir.is_dir() and pkg_dir != governance_root and (pkg_dir / "README.md").is_file():
                for pattern in primitive_patterns:
                    primitive_targets.append((pkg_dir / "README.md", _governance_scoped(pattern)))

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


def check_package_table_versions(oss_root: Path) -> list[str]:
    """Require one README Python package row per manifest, with its tree version.

    The Python table is identified by its Package/Tree/PyPI/Status header.
    Registry versions are not consulted; only [project].version is compared.
    Missing, duplicate or malformed rows fail closed instead of being skipped.
    """
    prefix = "[package_table_versions]"
    readme = oss_root / "README.md"
    python_dir = oss_root / "packages" / "python"
    problems: list[str] = []
    if not python_dir.is_dir():
        return [f"{prefix} expected directory not found: {python_dir}"]
    manifests = sorted(python_dir.glob("*/pyproject.toml"))
    if not manifests:
        return [f"{prefix} no Python package manifests found: {python_dir}"]

    versions: dict[str, str] = {}
    names = {path.parent.name for path in manifests}
    for path in manifests:
        try:
            with path.open("rb") as stream:
                data = tomllib.load(stream)
            project = data.get("project", {})
            version = project.get("version") if isinstance(project, dict) else None
            if not isinstance(version, str) or not version.strip():
                problems.append(f"{prefix} {path}: missing or invalid [project].version")
            else:
                versions[path.parent.name] = version
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            problems.append(f"{prefix} cannot read {path}: {exc}")

    try:
        lines = readme.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return problems + [f"{prefix} cannot read {readme}: {exc}"]

    def cells(line: str) -> list[str]:
        # Markdown permits either outer delimiter to be omitted. Remove at
        # most one: extra delimiters represent empty cells, not decoration.
        line = line.strip().removeprefix("|").removesuffix("|")
        return [cell.strip() for cell in line.split("|")]

    headers = [
        index for index, line in enumerate(lines)
        if cells(line) == ["Package", "Tree", "PyPI", "Status"]
    ]
    if len(headers) != 1:
        return problems + [f"{prefix} {readme}: expected exactly one Python package table"]
    header = headers[0]
    if header + 1 >= len(lines) or len(cells(lines[header + 1])) != 4 or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells(lines[header + 1])
    ):
        return problems + [f"{prefix} {readme}:{header + 2}: malformed table separator"]

    seen: set[str] = set()
    for index in range(header + 2, len(lines)):
        line = lines[index].strip()
        if "|" not in line:
            break
        row = cells(line)
        if len(row) != 4:
            problems.append(f"{prefix} {readme}:{index + 1}: malformed package row")
            continue
        name = row[0].strip("`")
        if name in seen:
            problems.append(f"{prefix} {readme}:{index + 1}: duplicate package row: {name}")
        seen.add(name)
        if name not in names:
            problems.append(f"{prefix} {readme}:{index + 1}: unknown Python package: {name}")
        elif name in versions and row[1] != versions[name]:
            problems.append(
                f"{prefix} {readme}:{index + 1}: {name} table says {row[1]!r}, "
                f"pyproject.toml says {versions[name]!r} (source of truth)"
            )
    for name in sorted(names - seen):
        problems.append(f"{prefix} {readme}: missing package row: {name}")
    return problems


def _current_governance_version(oss_root: Path) -> str | None:
    """[project].version of hummbl-governance in this tree, or None if unreadable."""
    manifest = oss_root / "packages" / "python" / "hummbl-governance" / "pyproject.toml"
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r'(?m)^\[project\][^\[]*?^version\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else None


_VERSION_TOKEN = re.compile(r"(?<![\w.])v?(\d+\.\d+(?:\.\d+)?)(?![\w.])")


def check_cross_package_nomenclature(
    oss_root: Path,
    expected_primitives: int | None = None,
) -> list[str]:
    """Check active monorepo READMEs for drifted DCT expansion and stale governance counts.

    Bounded to root README.md and packages/python/*/README.md (excluding dated
    research archives and historical authority snapshots).

    Count scope (review on #525):
    - In packages/python/hummbl-governance/README.md every count line is checked,
      because its lines rarely repeat the package name.
    - Elsewhere only lines that name hummbl-governance are checked.
    - A line that pins a version other than the current hummbl-governance
      version is a historical statement and is not compared to today's count.
    """
    prefix = "[nomenclature]"
    problems: list[str] = []
    targets: list[Path] = []
    root_readme = oss_root / "README.md"
    if root_readme.is_file():
        targets.append(root_readme)
    python_dir = oss_root / "packages" / "python"
    if python_dir.is_dir():
        targets.extend(sorted(python_dir.glob("*/README.md")))
    governance_readme = python_dir / "hummbl-governance" / "README.md"
    current_version = _current_governance_version(oss_root)

    drifted_dct = re.compile(r"\bDelegation\s+Context\s+Token\b", re.IGNORECASE)
    gov_prim_count = re.compile(r"(\d+)\s+(?:implemented\s+)?(?:governance\s+)?primitives\b", re.IGNORECASE)

    for path in targets:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            problems.append(f"{prefix} cannot read {path}: {exc}")
            continue
        in_governance_readme = path.resolve() == governance_readme.resolve()
        for line_no, line in enumerate(lines, start=1):
            if drifted_dct.search(line):
                problems.append(
                    f"{prefix} {path}:{line_no}: drifted DCT expansion "
                    "'Delegation Context Token' — use 'Delegation Capability Token' "
                    "for DCT and 'Delegation Context' for DCTX "
                    "(see docs/architecture/NOMENCLATURE.md)"
                )
            if expected_primitives is None:
                continue
            if not in_governance_readme and "hummbl-governance" not in line.lower():
                continue
            versions = {m.group(1) for m in _VERSION_TOKEN.finditer(line)}
            if current_version and versions and current_version not in versions:
                continue  # historical, versioned statement
            for match in gov_prim_count.finditer(line):
                found = int(match.group(1))
                if found != expected_primitives:
                    problems.append(
                        f"{prefix} {path}:{line_no}: hummbl-governance primitive count "
                        f"says {found}, expected {expected_primitives} "
                        f"(or link to PRIMITIVES.md / docs/public-claims.md) -- '{match.group(0)}'"
                    )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to the oss monorepo root (default: inferred from this script's location)",
    )
    args = parser.parse_args()
    oss_root = args.repo_root
    if oss_root is None:
        oss_root = next(
            (parent for parent in Path(__file__).resolve().parents
             if (parent / "packages" / "python" / "hummbl-governance").is_dir()),
            None,
        )
        if oss_root is None:
            parser.error("cannot infer monorepo root; supply --repo-root")
    oss_root = oss_root.resolve()

    checks = build_checks(oss_root)
    problems: list[str] = []
    expected_primitives: int | None = None
    for check in checks:
        if check.name == "implemented_primitives":
            expected_primitives = check.expected
        problems.extend(find_mismatches(check))
        print(f"{check.name}: ground truth = {check.expected}")

    problems.extend(check_package_table_versions(oss_root))
    print("package_table_versions: ground truth = packages/python/*/pyproject.toml")

    problems.extend(check_cross_package_nomenclature(oss_root, expected_primitives))
    print("nomenclature: checked root and package READMEs for DCT drift and governance primitive counts")

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

    print("\nAll checked public counts and tree versions match ground truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
