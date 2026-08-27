"""Thin wrapper over hummbl_governance.SchemaValidator (lazy import).

The canonical stdlib-only JSON Schema Draft 2020-12 validator lives in the
``hummbl_governance`` package. This module preserves the functional API that
``hummbl_cognition`` historically exposed (``validate``, ``validate_file``,
``validate_entry_dict``, ``validate_state_dict``) plus domain helpers that load
CLP schemas from ``contracts/cognition/schemas/``.

hummbl_governance is imported lazily inside each function so that importing
``hummbl_cognition`` does not hard-require the package at interpreter
startup. This keeps scripts that invoke the cognition CLI via a plain
``python3`` (outside the hummbl-cognition venv) working as before.

Re-integrates with hummbl-governance >= 0.3.0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "validate",
    "validate_file",
    "validate_entry_dict",
    "validate_state_dict",
    "ValidationError",
]


class ValidationError(Exception):
    """Raised when a value fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


_validator = None


def _get_validator():
    global _validator
    if _validator is None:
        from hummbl_governance import SchemaValidator

        _validator = SchemaValidator()
    return _validator


def validate(instance: Any, schema: dict[str, Any], path: str = "") -> list[str]:
    """Validate *instance* against *schema*. Returns list of error strings (empty = valid)."""
    return _get_validator().validate(instance, schema, path)


def validate_file(
    instance_path: str | Path,
    schema_path: str | Path,
) -> tuple[bool, list[str]]:
    """Validate a JSON file against a JSON Schema file. Returns (is_valid, errors)."""
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    errors = validate(instance, schema)
    return len(errors) == 0, errors


def validate_entry_dict(
    entry: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a ledger entry dict against the CLP schema.

    If no schema is provided, loads the default from contracts/.
    """
    if schema is None:
        schema = _load_default_schema("clp.ledger_entry.schema.json")
    errors = validate(entry, schema)
    return len(errors) == 0, errors


def validate_state_dict(
    state: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a shared state dict against the CLP schema."""
    if schema is None:
        schema = _load_default_schema("clp.shared_state.schema.json")
    errors = validate(state, schema)
    return len(errors) == 0, errors


def _load_default_schema(filename: str) -> dict[str, Any]:
    """Load a schema from contracts/cognition/schemas/."""
    import subprocess

    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        schema_path = Path(root) / "contracts" / "cognition" / "schemas" / filename
        if schema_path.exists():
            return json.loads(schema_path.read_text(encoding="utf-8"))
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        pass

    schema_path = Path("contracts") / "cognition" / "schemas" / filename
    if schema_path.exists():
        return json.loads(schema_path.read_text(encoding="utf-8"))

    pkg_schema_path = Path(__file__).resolve().parent / "schemas" / filename
    if pkg_schema_path.exists():
        return json.loads(pkg_schema_path.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        f"Schema file not found: {filename}. "
        "Ensure contracts/cognition/schemas/ or package schemas/ exists."
    )
