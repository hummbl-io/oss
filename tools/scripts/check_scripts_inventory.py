#!/usr/bin/env python3
"""Validates the repository scripts inventory against the scripts lifecycle contract.

Ensures that every script in tools/ and .github/scripts/ has an owner,
classification, invocation contract, failure behavior, system boundary,
and test path, and that no uncataloged automation drifts into the repository.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_CLASSIFICATIONS = {"maintain", "connect", "productize", "deprecate", "retire"}

SECRET_PATTERNS = [
    re.compile(r"(?i)(?:api[_-]?key|secret|password|bearer|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9]{82}"),
    re.compile(r"(?<![0-9])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(?![0-9])"),
]

EXCLUDED_NAMES = {
    "__init__.py",
}


def is_test_file(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.js")


def discover_repo_scripts(root: Path) -> set[str]:
    """Find all runnable scripts under tools/ and .github/scripts/."""
    discovered: set[str] = set()

    search_dirs = [root / "tools", root / ".github" / "scripts"]
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for p in sdir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix not in {".py", ".mjs", ".sh", ".js"}:
                continue
            if is_test_file(p):
                continue
            if p.name in EXCLUDED_NAMES:
                continue
            if "__pycache__" in p.parts or ".pytest_cache" in p.parts:
                continue
            rel_path = p.relative_to(root).as_posix()
            discovered.add(rel_path)

    return discovered


def validate_inventory(root: Path, inventory_file: Path) -> tuple[list[str], list[str]]:
    """Validates scripts inventory against disk reality and contract rules.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not inventory_file.exists():
        return [f"Inventory file not found: {inventory_file}"], []

    try:
        data = json.loads(inventory_file.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Failed to parse JSON in {inventory_file}: {e}"], []

    if data.get("schema_version") != "hummbl.repository-scripts.v1":
        errors.append(f"Invalid schema_version: expected 'hummbl.repository-scripts.v1', got {data.get('schema_version')!r}")

    scripts = data.get("scripts")
    if not isinstance(scripts, list):
        return [f"'scripts' must be a list in {inventory_file}"], []

    registered_paths: set[str] = set()

    for idx, item in enumerate(scripts):
        path_str = item.get("path")
        if not path_str or not isinstance(path_str, str):
            errors.append(f"Script #{idx}: missing or invalid 'path'")
            continue

        normalized_path = Path(path_str).as_posix()
        if normalized_path in registered_paths:
            errors.append(f"Duplicate entry for script path: {normalized_path}")
        registered_paths.add(normalized_path)

        # 1. Existence on disk
        target_path = root / normalized_path
        if not target_path.exists():
            errors.append(f"Registered script does not exist on disk: {normalized_path}")

        # 2. Classification
        cls = item.get("classification")
        if cls not in VALID_CLASSIFICATIONS:
            errors.append(f"{normalized_path}: invalid classification '{cls}' (must be one of {sorted(VALID_CLASSIFICATIONS)})")

        # 3. Required fields
        for req_field in ("owner", "invocation_contract", "system_boundary", "failure_behavior", "test_path"):
            val = item.get(req_field)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"{normalized_path}: missing or empty required field '{req_field}'")

        # 4. Secret scan on inventory text
        for pat in SECRET_PATTERNS:
            for field in ("invocation_contract", "system_boundary", "integration_notes"):
                text = item.get(field, "")
                if text and pat.search(text):
                    errors.append(f"{normalized_path}: potential secret or unredacted boundary pattern in '{field}'")

    # 5. Parity check: all runnable scripts in tools/ and .github/scripts/ must be registered
    discovered = discover_repo_scripts(root)
    unregistered = discovered - registered_paths
    for unreg in sorted(unregistered):
        errors.append(f"Unregistered executable script in repository: {unreg} (must be added to {inventory_file.name})")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository scripts inventory against lifecycle contracts.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root directory")
    parser.add_argument("--inventory", type=Path, default=None, help="Path to scripts inventory file")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    inventory_file = (args.inventory or (root / "tools" / "scripts-inventory.json")).resolve()

    errors, warnings = validate_inventory(root, inventory_file)

    for w in warnings:
        print(f"[WARN] {w}", file=sys.stderr)

    if errors:
        print(f"Scripts Inventory Validation FAILED ({len(errors)} errors):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"Scripts Inventory Validation PASSED: {inventory_file.name} is complete and in parity with disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
