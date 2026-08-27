"""Check current release metadata claims across public package surfaces."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from zipfile import ZipFile

EXPECTED_PRIMITIVES = "36"
EXPECTED_TESTS = "2430"

STALE_PATTERNS = {
    "old_current_version": r"Current package version\*\*: `1\.1\.0`",
    "old_primitive_claim": r"\b26 governance primitives\b",
    "old_test_1032": r"\b1032 (?:passing )?tests\b",
    "old_test_1244": r"\b1244 tests\b",
    "old_test_1970": r"\b1970 (?:collected )?tests\b",
    "old_governance_yml_tests_1970": r"\btests:\s*1970\b",
    "old_governance_yml_tests": r"\btests:\s*1849\b",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def wheel_metadata(path: Path) -> str:
    with ZipFile(path) as zf:
        metadata_name = next(name for name in zf.namelist() if name.endswith(".dist-info/METADATA"))
        return zf.read(metadata_name).decode("utf-8", errors="replace")


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def check_no_stale_patterns(
    name: str,
    text: str,
    failures: list[str],
    *,
    labels: set[str] | None = None,
) -> None:
    for label, pattern in STALE_PATTERNS.items():
        if labels is not None and label not in labels:
            continue
        if re.search(pattern, text):
            failures.append(f"{name}: stale metadata pattern present: {label}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, help="Optional built wheel to inspect")
    args = parser.parse_args(argv)

    root = Path.cwd()
    failures: list[str] = []

    pyproject = tomllib.loads(read_text(root / "pyproject.toml"))
    expected_version = pyproject.get("project", {}).get("version", "")
    readme = read_text(root / "README.md")
    security = read_text(root / "SECURITY.md")
    repo_health = read_text(root / "docs" / "REPO_HEALTH.md")
    test_count_authority = read_text(root / "docs" / "TEST_COUNT_AUTHORITY.md")
    public_claims = read_text(root / "docs" / "public-claims.md")
    governance = read_text(root / "hummbl_governance" / "governance.yml")

    require(
        bool(expected_version),
        "pyproject.toml missing a project.version value",
        failures,
    )
    require(
        f"provides {EXPECTED_PRIMITIVES} governance primitives" in readme,
        "README missing expected implemented primitive count claim",
        failures,
    )
    require(
        EXPECTED_TESTS in readme,
        "README missing expected package test collection count",
        failures,
    )
    require(
        f"its {EXPECTED_PRIMITIVES}\nimplemented governance primitives" in security
        or f"its {EXPECTED_PRIMITIVES} implemented governance primitives" in security,
        "SECURITY.md missing expected implemented primitive scope",
        failures,
    )
    require(
        f"collects {EXPECTED_TESTS} tests" in security,
        "SECURITY.md missing expected package test collection count",
        failures,
    )
    require(
        f"Current package version**: `{expected_version}`" in repo_health,
        "docs/REPO_HEALTH.md missing current package version",
        failures,
    )
    require(
        f"Package version is `{expected_version}`" in public_claims,
        "docs/public-claims.md missing current package version",
        failures,
    )
    require(
        f"{EXPECTED_TESTS} tests collected" in test_count_authority,
        "docs/TEST_COUNT_AUTHORITY.md missing expected package test collection count",
        failures,
    )
    require(
        f"version: {expected_version}" in governance,
        "hummbl_governance/governance.yml missing expected package version",
        failures,
    )
    require(
        f"version: {expected_version}" in readme,
        "README governance.yml example missing expected package version",
        failures,
    )
    require(
        f"tests: {EXPECTED_TESTS}" in governance,
        "hummbl_governance/governance.yml missing expected test count",
        failures,
    )

    current_surface_texts = {
        "README.md": readme,
        "SECURITY.md": security,
        "docs/REPO_HEALTH.md": repo_health,
        "docs/public-claims.md": public_claims,
        "hummbl_governance/governance.yml": governance,
    }
    for name, text in current_surface_texts.items():
        check_no_stale_patterns(name, text, failures)
    check_no_stale_patterns(
        "docs/TEST_COUNT_AUTHORITY.md",
        test_count_authority,
        failures,
        labels={"old_test_1970"},
    )

    if args.wheel:
        metadata = wheel_metadata(args.wheel)
        require(
            f"Version: {expected_version}" in metadata,
            "wheel METADATA missing expected version",
            failures,
        )
        require(
            f"provides {EXPECTED_PRIMITIVES} governance primitives" in metadata,
            "wheel METADATA missing expected primitive count",
            failures,
        )
        require(
            EXPECTED_TESTS in metadata,
            "wheel METADATA missing expected test count",
            failures,
        )
        check_no_stale_patterns(str(args.wheel), metadata, failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("release metadata check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
