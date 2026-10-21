#!/usr/bin/env python3
"""Validate external import records and fixture integrity across the repository.

Enforces:
1. Schema conformance: each *.import.json matches schemas/public/external-import-record-v1.schema.json.
2. Cryptographic integrity: file size, sha256, and git_blob_sha match local disk bytes.
3. Selection completeness: no unlisted files in target fixture directories; no missing files.
4. Rights and attribution: declared license files and attribution strings exist in corpus.

Exit 0 on success; 1 on failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _compute_hashes(content: bytes) -> tuple[str, str]:
    sha256 = hashlib.sha256(content).hexdigest()
    git_blob_sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\x00" + content).hexdigest()
    return sha256, git_blob_sha


def _simple_validate(instance: Any, schema: dict[str, Any], path: str = "") -> list[str]:
    """Minimal schema validator for external-import records using stdlib."""
    errors: list[str] = []
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "object" and not isinstance(instance, dict):
            return [f"{path}: expected object, got {type(instance).__name__}"]
        elif expected_type == "array" and not isinstance(instance, list):
            return [f"{path}: expected array, got {type(instance).__name__}"]
        elif expected_type == "string" and not isinstance(instance, str):
            return [f"{path}: expected string, got {type(instance).__name__}"]
        elif expected_type == "integer" and (isinstance(instance, bool) or not isinstance(instance, int)):
            return [f"{path}: expected integer, got {type(instance).__name__}"]
        elif expected_type == "boolean" and not isinstance(instance, bool):
            return [f"{path}: expected boolean, got {type(instance).__name__}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, dict):
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            for key in instance:
                if key not in allowed:
                    errors.append(f"{path}: unexpected property {key!r}")
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required field {req!r}")
        for k, prop_schema in schema.get("properties", {}).items():
            if k in instance:
                sub_path = f"{path}.{k}" if path else k
                errors.extend(_simple_validate(instance[k], prop_schema, sub_path))

    elif isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        for idx, item in enumerate(instance):
            sub_path = f"{path}[{idx}]"
            errors.extend(_simple_validate(item, item_schema, sub_path))

    return errors


def check_external_imports(root: Path) -> tuple[int, list[str]]:
    """Scan and verify all external import records under root."""
    schema_path = root / "schemas" / "public" / "external-import-record-v1.schema.json"
    if not schema_path.exists():
        return 1, [f"Schema not found: {schema_path}"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return 1, [f"Failed to parse schema: {exc}"]

    record_files = sorted(root.glob("packages/**/provenance/*.import.json"))
    if not record_files:
        return 1, ["No *.import.json records found in repository."]

    errors: list[str] = []
    print(f"Found {len(record_files)} external import record(s).")

    for rf in record_files:
        rel_rf = rf.relative_to(root)
        print(f"Checking {rel_rf}...")
        try:
            record = json.loads(rf.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel_rf}: Failed to parse JSON: {exc}")
            continue

        schema_errors = _simple_validate(record, schema)
        if schema_errors:
            errors.extend([f"{rel_rf}: {err}" for err in schema_errors])
            continue

        inventory = record["integrity"]["inventory"]
        if len(inventory) != record["integrity"]["file_count"]:
            errors.append(
                f"{rel_rf}: declared file_count {record['integrity']['file_count']} != inventory length {len(inventory)}"
            )

        fixture_dirs: set[Path] = set()
        recorded_filenames: dict[Path, set[str]] = {}

        for item in inventory:
            dest_rel = Path(item["destination_path"])
            dest_file = root / dest_rel
            parent_dir = dest_file.parent
            fixture_dirs.add(parent_dir)
            recorded_filenames.setdefault(parent_dir, set()).add(dest_file.name)

            if not dest_file.exists():
                errors.append(f"{rel_rf}: destination file does not exist: {dest_rel}")
                continue

            content = dest_file.read_bytes()
            if len(content) != item["bytes"]:
                errors.append(
                    f"{rel_rf}: size mismatch for {dest_rel}: expected {item['bytes']}, got {len(content)}"
                )

            sha256, git_blob = _compute_hashes(content)
            if sha256 != item["sha256"]:
                errors.append(
                    f"{rel_rf}: sha256 mismatch for {dest_rel}: expected {item['sha256']}, got {sha256}"
                )
            if git_blob != item["git_blob_sha"]:
                errors.append(
                    f"{rel_rf}: git_blob_sha mismatch for {dest_rel}: expected {item['git_blob_sha']}, got {git_blob}"
                )

        # Check for unlisted files in target fixture directories
        for fdir in fixture_dirs:
            if not fdir.exists():
                continue
            disk_files = {p.name for p in fdir.iterdir() if p.is_file()}
            expected_files = recorded_filenames.get(fdir, set())
            unlisted = disk_files - expected_files
            if unlisted:
                errors.append(
                    f"{rel_rf}: unlisted file(s) found in {fdir.relative_to(root)}: {sorted(unlisted)}"
                )

        # Check rights and attributions
        rights = record["rights"]
        for lic_file_rel in rights.get("license_files", []):
            lic_path = root / lic_file_rel
            if not lic_path.exists():
                errors.append(f"{rel_rf}: declared license file does not exist: {lic_file_rel}")
            else:
                lic_text = lic_path.read_text(encoding="utf-8")
                for attr in rights.get("attributions", []):
                    if attr not in lic_text:
                        errors.append(
                            f"{rel_rf}: attribution string {attr!r} not found in {lic_file_rel}"
                        )

    return (1 if errors else 0), errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="Repository root directory",
    )
    args = parser.parse_args()

    exit_code, errors = check_external_imports(args.root)
    if errors:
        print("\n--- EXTERNAL IMPORT CHECK FAILURES ---", file=sys.stderr)
        for err in errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        print(f"\nFailed with {len(errors)} error(s).", file=sys.stderr)
        return exit_code

    print("\nAll external import records and fixture digests verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
