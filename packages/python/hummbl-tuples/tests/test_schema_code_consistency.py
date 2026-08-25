#!/usr/bin/env python3
"""Test fixtures for schema-code consistency checker.

These tests verify that the consistency checker correctly detects drift
and passes when schemas and code are aligned.
"""

import sys
from pathlib import Path

# Add scripts dir to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_schema_code_consistency import (
    _load_schemas,
    _extract_schema_fields,
    _get_dataclass_fields,
    check_consistency,
)


def test_schemas_loadable():
    """All schema files should be valid JSON."""
    schemas = _load_schemas()
    assert len(schemas) > 0, "No schemas found"
    for filename, schema in schemas.items():
        assert isinstance(schema, dict), f"{filename} is not a dict"
        assert "type" in schema, f"{filename} missing 'type' field"


def test_extract_schema_fields():
    """Schema field extraction should work for a known schema."""
    schemas = _load_schemas()
    contract = schemas.get("contract.schema.json")
    assert contract is not None, "contract.schema.json not found"
    required, props, tuple_type = _extract_schema_fields(contract)
    assert "tuple_type" in required, "tuple_type should be required"
    assert tuple_type == "CONTRACT", f"tuple_type const should be CONTRACT, got {tuple_type}"
    assert "state" in props, "state should be in properties"


def test_dataclass_importable():
    """IDPTuple should be importable and have expected fields."""
    all_fields, data_fields, tuple_type, import_error = _get_dataclass_fields("hummbl_tuples.base", "IDPTuple")
    assert len(all_fields) > 0, "IDPTuple has no fields"
    assert "tuple_type" in all_fields, "tuple_type should be a field"
    assert tuple_type is not None or "tuple_type" in all_fields, "tuple_type should exist"
    assert import_error is None, f"Unexpected import error: {import_error}"


def test_consistency_checker_runs():
    """Consistency checker should run without crashing."""
    violations = check_consistency(strict=False)
    # It may find violations (that's the point), but it should not crash
    assert isinstance(violations, list), "check_consistency should return a list"


def test_no_class_exists_violations():
    """All mapped classes should be importable (no G-CLASS-EXISTS errors)."""
    violations = check_consistency(strict=False)
    class_errors = [v for v in violations if v["gate"] == "G-CLASS-EXISTS"]
    assert len(class_errors) == 0, f"Classes not found: {[v['message'] for v in class_errors]}"


if __name__ == "__main__":
    test_schemas_loadable()
    test_extract_schema_fields()
    test_dataclass_importable()
    test_consistency_checker_runs()
    test_no_class_exists_violations()
    print("All consistency checker tests passed")
