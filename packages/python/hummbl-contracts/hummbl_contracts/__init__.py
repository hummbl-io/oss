"""hummbl-contracts -- HUMMBL contract schemas and validation engine.

Stdlib-only JSON Schema validator (Draft 2020-12 subset) with bundled
contract schemas for the HUMMBL ecosystem.

Public API:
    validate(instance, schema, path="") -> list[str]
    validate_file(instance_path, schema_path) -> (bool, list[str])
    validate_entry_dict(entry, schema=None) -> (bool, list[str])
    validate_state_dict(state, schema=None) -> (bool, list[str])
    load_schema(name) -> dict
    list_schemas() -> list[str]
    ValidationError -- raised on validation failure
"""

from __future__ import annotations

from hummbl_contracts.schema_validator import (
    ValidationError,
    validate,
    validate_entry_dict,
    validate_file,
    validate_state_dict,
)
from hummbl_contracts.schema_loader import list_schemas, load_schema

__version__ = "0.1.0"

__all__ = [
    "ValidationError",
    "list_schemas",
    "load_schema",
    "validate",
    "validate_entry_dict",
    "validate_file",
    "validate_state_dict",
]
