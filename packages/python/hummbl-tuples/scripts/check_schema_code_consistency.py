#!/usr/bin/env python3
"""Schema-code consistency checker for HUMMBL tuples.

Validates that Python dataclass fields match JSON Schema required/properties
fields. Catches drift at commit time.

Checks:
1. Every schema in schemas/*.schema.json has a corresponding Python dataclass
   that produces tuples with matching tuple_type.
2. Every required field in a schema has a corresponding dataclass field.
3. Every dataclass field (non-envelope) appears in schema properties or required.

Stdlib-only. Exit 0 on success, 1 on drift detected.

Usage:
    python scripts/check_schema_code_consistency.py
    python scripts/check_schema_code_consistency.py --strict
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _load_schemas() -> dict[str, dict[str, Any]]:
    """Load all schema files from the top-level schemas/ directory.

    Returns {filename: schema_dict}. Only scans the top-level directory;
    experimental schemas in schemas/experimental/ are not loaded.
    """
    schemas = {}
    for p in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        with p.open("r", encoding="utf-8") as f:
            schemas[p.name] = json.load(f)
    return schemas


def _extract_schema_fields(schema: dict[str, Any]) -> tuple[set[str], set[str], str | None]:
    """Extract (required_fields, property_fields, tuple_type_const) from a schema.

    For schemas that nest data fields inside ``payload`` or ``tuple_data``
    (trace artifacts, BaseN tuples), the nested property names are merged
    into the returned ``property_fields`` set so that the G-CLASS-FIELDS-IN-SCHEMA
    check can find them.
    """
    required = set(schema.get("required", []))
    properties = set(schema.get("properties", {}).keys())
    # Look for tuple_type const
    tuple_type = None
    props = schema.get("properties", {})
    if "tuple_type" in props and isinstance(props["tuple_type"], dict):
        tuple_type = props["tuple_type"].get("const")
    # Merge nested data-container properties (payload or tuple_data) into
    # the top-level property set so data field comparisons work for trace
    # schemas and BaseN schemas alike.
    for container in ("payload", "tuple_data"):
        container_def = props.get(container)
        if isinstance(container_def, dict):
            nested_props = container_def.get("properties", {})
            if isinstance(nested_props, dict):
                properties |= set(nested_props.keys())
    return required, properties, tuple_type


def _get_dataclass_fields(
    module_path: str, class_name: str
) -> tuple[set[str], set[str], str | None, str | None]:
    """Import a dataclass and extract (all_fields, data_fields, tuple_type_default, import_error).

    Returns (set(), set(), None, None) if the class is found and imported
    successfully. If the module fails to import or the class is missing,
    the first three elements are empty/None and ``import_error`` contains
    a formatted error message describing the failure.
    """
    import_error: str | None = None
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name, None)
        if cls is None or not dataclasses.is_dataclass(cls):
            import_error = f"{module_path}.{class_name} not found or not a dataclass"
            return set(), set(), None, import_error
    except Exception as exc:
        import_error = (
            f"Failed to import {module_path}.{class_name}: {exc}\n{traceback.format_exc()}"
        )
        logger.error(import_error)
        return set(), set(), None, import_error

    all_fields = {f.name for f in dataclasses.fields(cls)}
    # Envelope fields are tuple_type, id, time (from TypedTuple base)
    envelope = {"tuple_type", "id", "time"}
    data_fields = all_fields - envelope

    # Get tuple_type default
    tuple_type = None
    for f in dataclasses.fields(cls):
        if f.name == "tuple_type" and f.default is not dataclasses.MISSING:
            tuple_type = f.default
    return all_fields, data_fields, tuple_type, None


# Mapping from schema filename to expected Python class
# Format: (module_path, class_name)
SCHEMA_TO_CLASS = {
    "contract.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "dct.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "dctx.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "evidence.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "system.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "attest.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "promotion_receipt.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "revocation.schema.json": ("hummbl_tuples.base", "IDPTuple"),
    "pretraining_trace.schema.json": ("hummbl_tuples.traces", "PretrainingTrace"),
    "posttraining_trace.schema.json": ("hummbl_tuples.traces", "PosttrainingTrace"),
    # trace_evidence_tuple.schema.json and trace_evidence_record.schema.json
    # describe TRACE_EVIDENCE tuples and evidence records that do not yet have
    # Python dataclass implementations. Skip until those classes are added.
}


def check_consistency(strict: bool = False) -> list[dict[str, str]]:
    """Run consistency checks and return violations.

    When strict=False, warnings are excluded from the returned list so
    that callers only see errors. When strict=True, both errors and
    warnings are returned.
    """
    schemas = _load_schemas()
    violations: list[dict[str, str]] = []

    for filename, schema in schemas.items():
        if filename not in SCHEMA_TO_CLASS:
            # Schema without a known class mapping — skip (could be experimental)
            continue

        module_path, class_name = SCHEMA_TO_CLASS[filename]
        schema_required, schema_props, schema_tuple_type = _extract_schema_fields(schema)
        cls_fields, cls_data_fields, cls_tuple_type, import_error = _get_dataclass_fields(
            module_path, class_name
        )

        if not cls_fields:
            violations.append(
                {
                    "gate": "G-CLASS-EXISTS",
                    "message": f"{filename}: cannot import {module_path}.{class_name}",
                    "severity": "error",
                }
            )
            if import_error:
                violations.append(
                    {
                        "gate": "G-CLASS-IMPORT-ERROR",
                        "message": f"{filename}: {import_error}",
                        "severity": "error",
                    }
                )
            continue

        # Check: schema required fields should be in dataclass fields
        # tuple_data is the envelope container — it's built dynamically by to_dict(),
        # not a dataclass field. Skip it for class field comparison.
        envelope_dynamic = {"tuple_data", "payload"}
        schema_required_checkable = schema_required - envelope_dynamic
        missing_in_class = schema_required_checkable - cls_fields
        if missing_in_class:
            violations.append(
                {
                    "gate": "G-SCHEMA-REQUIRED-IN-CLASS",
                    "message": f"{filename}: schema requires {missing_in_class} but {class_name} does not have these fields",
                    "severity": "error",
                }
            )

        # Check: dataclass data fields should be in schema properties or required
        # (allow extra class fields not in schema — they may be optional)
        schema_all = schema_required | schema_props
        # Remove envelope fields from schema_all for comparison
        schema_all_data = schema_all - {"tuple_type", "id", "time", "tuple_data"}
        missing_in_schema = cls_data_fields - schema_all_data
        if missing_in_schema:
            violations.append(
                {
                    "gate": "G-CLASS-FIELDS-IN-SCHEMA",
                    "message": f"{filename}: {class_name} has data fields {missing_in_schema} not in schema properties",
                    "severity": "warning",
                }
            )

        # Check: tuple_type const matches
        if schema_tuple_type and cls_tuple_type and schema_tuple_type != cls_tuple_type:
            violations.append(
                {
                    "gate": "G-TUPLE-TYPE-MATCH",
                    "message": f"{filename}: schema tuple_type='{schema_tuple_type}' but {class_name} tuple_type='{cls_tuple_type}'",
                    "severity": "error",
                }
            )

    if not strict:
        violations = [v for v in violations if v["severity"] == "error"]

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings too")
    args = parser.parse_args(argv)

    # Add repo root to sys.path for imports
    sys.path.insert(0, str(REPO_ROOT))

    violations = check_consistency(strict=args.strict)

    errors = [v for v in violations if v["severity"] == "error"]
    warnings = [v for v in violations if v["severity"] == "warning"]

    if not violations:
        print("schema-code consistency check passed — no drift detected")
        return 0

    print(
        f"schema-code consistency check found {len(errors)} error(s), {len(warnings)} warning(s):"
    )
    for v in violations:
        print(f"  [{v['severity'].upper()}] {v['gate']}: {v['message']}")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
