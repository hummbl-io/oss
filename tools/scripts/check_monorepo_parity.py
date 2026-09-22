#!/usr/bin/env python3
"""Automated CI validator for monorepo package parity and lockfile presence.

Enforces Issue #264 requirements:
1. Every package in packages/python/ must be documented in docs/PACKAGES.md.
2. Every package in packages/python/ must be present in AGENTS.md and .github/workflows/ci.yml matrix.
3. Every package in packages/python/ with third-party dependencies must include a requirements.lock.

Stdlib only, Python 3.11+.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
try:
    import tomllib
except ImportError:
    import toml as tomllib  # type: ignore[no-redef]


def get_actual_packages(repo_root: Path) -> set[str]:
    pkg_dir = repo_root / "packages" / "python"
    if not pkg_dir.exists():
        return set()
    return {
        d.name for d in pkg_dir.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_"))
    }


def check_docs_packages_parity(repo_root: Path, actual_pkgs: set[str]) -> list[str]:
    errors = []
    packages_doc = repo_root / "docs" / "architecture" / "PACKAGES.md"
    if not packages_doc.exists():
        packages_doc = repo_root / "docs" / "PACKAGES.md"
    if not packages_doc.exists():
        return [f"Missing {packages_doc}"]

    content = packages_doc.read_text(encoding="utf-8")
    for pkg in sorted(actual_pkgs):
        # Match `pkg` in backticks or markdown table row
        pattern = rf"[`|]\s*{re.escape(pkg)}\s*[`|]"
        if not re.search(pattern, content):
            errors.append(f"Package '{pkg}' is absent from {packages_doc.name}")
    return errors


def check_agents_md_parity(repo_root: Path, actual_pkgs: set[str]) -> list[str]:
    errors = []
    agents_md = repo_root / "AGENTS.md"
    if not agents_md.exists():
        return [f"Missing {agents_md}"]

    content = agents_md.read_text(encoding="utf-8")
    for pkg in sorted(actual_pkgs):
        if pkg not in content:
            errors.append(f"Package '{pkg}' is absent from AGENTS.md")
    return errors


def check_ci_matrix_parity(repo_root: Path, actual_pkgs: set[str]) -> list[str]:
    errors = []
    ci_yml = repo_root / ".github" / "workflows" / "ci.yml"
    if not ci_yml.exists():
        return [f"Missing {ci_yml}"]

    content = ci_yml.read_text(encoding="utf-8")
    matrix_match = re.search(r"package:\s*\[(.*?)\]", content, re.DOTALL)
    if not matrix_match:
        return ["Could not locate package matrix in .github/workflows/ci.yml"]

    ci_pkgs = {p.strip().strip("'\"") for p in matrix_match.group(1).split(",")}
    for pkg in sorted(actual_pkgs):
        if pkg not in ci_pkgs:
            errors.append(f"Package '{pkg}' is missing from .github/workflows/ci.yml test matrix")
    return errors


def check_lockfile_presence(repo_root: Path, actual_pkgs: set[str]) -> list[str]:
    errors = []
    pkg_dir = repo_root / "packages" / "python"
    for pkg in sorted(actual_pkgs):
        pyproject = pkg_dir / pkg / "pyproject.toml"
        if not pyproject.exists():
            continue
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            errors.append(f"Failed to parse {pyproject}: {e}")
            continue

        deps = data.get("project", {}).get("dependencies", [])
        if deps:
            lockfile = pkg_dir / pkg / "requirements.lock"
            if not lockfile.exists():
                errors.append(
                    f"Package '{pkg}' declares dependencies {deps} but lacks requirements.lock"
                )
    return errors


def run_all_checks(repo_root: Path) -> tuple[int, list[str]]:
    actual_pkgs = get_actual_packages(repo_root)
    if not actual_pkgs:
        return 1, ["No packages found under packages/python"]

    all_errors: list[str] = []
    all_errors.extend(check_docs_packages_parity(repo_root, actual_pkgs))
    all_errors.extend(check_agents_md_parity(repo_root, actual_pkgs))
    all_errors.extend(check_ci_matrix_parity(repo_root, actual_pkgs))
    all_errors.extend(check_lockfile_presence(repo_root, actual_pkgs))

    if all_errors:
        return 1, all_errors
    return 0, [f"All {len(actual_pkgs)} monorepo packages satisfy documentation parity and lockfile enforcement."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify monorepo package parity and lockfile presence")
    parser.add_argument("--root", default=".", help="Monorepo root directory")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    code, messages = run_all_checks(root)
    for msg in messages:
        prefix = "FAIL: " if code != 0 else "PASS: "
        print(f"{prefix}{msg}")
    return code


if __name__ == "__main__":
    sys.exit(main())
