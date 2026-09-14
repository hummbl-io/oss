"""Minimal JSON Schema validator -- stdlib only.

Supports a subset of JSON Schema Draft 2020-12 sufficient to validate
CLP ledger entries, shared state documents, and HUMMBL contract schemas.
No third-party dependencies.

Supported keywords:
    type, required, properties, enum, pattern, minimum, maximum,
    minLength, maxLength, minItems, maxItems, items, additionalProperties,
    const, oneOf, anyOf
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# JSON Schema type name -> Python type(s)
_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
    "null": (type(None),),
}


class ValidationError(Exception):
    """Raised when a value fails schema validation."""

    def __init__(self, message: str, path: str = "") -> None:
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


def _json_equal(a: Any, b: Any) -> bool:
    """Type-aware equality for JSON Schema semantics.

    Python's bool is a subclass of int, so True == 1 and False == 0.
    JSON Schema treats booleans and numbers as distinct types. This
    function ensures bool != int/float in comparisons used by const
    and enum validation.
    """
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    return a == b


def _check_str(inst: Any, sch: dict[str, Any], p: str) -> list[str]:
    """Validate string keywords: pattern, minLength, maxLength."""
    if not isinstance(inst, str):
        return []
    errs: list[str] = []
    if "pattern" in sch:
        try:
            if not re.search(sch["pattern"], inst):
                errs.append(f"{p}: {inst!r} does not match pattern {sch['pattern']!r}")
        except re.error as e:
            errs.append(f"{p}: invalid regex pattern {sch['pattern']!r}: {e}")
    if "minLength" in sch and len(inst) < sch["minLength"]:
        errs.append(f"{p}: string length {len(inst)} < minLength {sch['minLength']}")
    if "maxLength" in sch and len(inst) > sch["maxLength"]:
        errs.append(f"{p}: string length {len(inst)} > maxLength {sch['maxLength']}")
    return errs


def _check_num(inst: Any, sch: dict[str, Any], p: str) -> list[str]:
    """Validate number keywords: minimum, maximum."""
    # bool is a subclass of int in Python, but JSON Schema treats bool != number
    if isinstance(inst, bool) or not isinstance(inst, (int, float)):
        return []
    errs: list[str] = []
    if "minimum" in sch and inst < sch["minimum"]:
        errs.append(f"{p}: {inst} < minimum {sch['minimum']}")
    if "maximum" in sch and inst > sch["maximum"]:
        errs.append(f"{p}: {inst} > maximum {sch['maximum']}")
    return errs


def _check_obj(inst: Any, sch: dict[str, Any], p: str) -> list[str]:
    """Validate object keywords: required, properties, additionalProperties."""
    if not isinstance(inst, dict):
        return []
    errs: list[str] = []
    for req in sch.get("required", []):
        if req not in inst:
            errs.append(f"{p}: missing required property {req!r}")
    props = sch.get("properties", {})
    for key, ps in props.items():
        if key in inst:
            sp = f"{p}.{key}" if p else key
            errs.extend(validate(inst[key], ps, sp))
    if "additionalProperties" in sch:
        ap = sch["additionalProperties"]
        known = set(props.keys())
        for key in inst:
            if key not in known:
                if ap is False:
                    errs.append(f"{p}: unexpected property {key!r}")
                elif isinstance(ap, dict):
                    sp = f"{p}.{key}" if p else key
                    errs.extend(validate(inst[key], ap, sp))
    return errs


def _check_arr(inst: Any, sch: dict[str, Any], p: str) -> list[str]:
    """Validate array keywords: minItems, maxItems, items."""
    if not isinstance(inst, list):
        return []
    errs: list[str] = []
    if "minItems" in sch and len(inst) < sch["minItems"]:
        errs.append(f"{p}: array length {len(inst)} < minItems {sch['minItems']}")
    if "maxItems" in sch and len(inst) > sch["maxItems"]:
        errs.append(f"{p}: array length {len(inst)} > maxItems {sch['maxItems']}")
    if "items" in sch:
        for i, item in enumerate(inst):
            errs.extend(validate(item, sch["items"], f"{p}[{i}]"))
    return errs


def _check_combo(inst: Any, sch: dict[str, Any], p: str) -> list[str]:
    """Validate oneOf, anyOf keywords."""
    errs: list[str] = []
    if "oneOf" in sch:
        n = sum(1 for s in sch["oneOf"] if not validate(inst, s, p))
        if n != 1:
            errs.append(f"{p}: expected exactly one of oneOf to match, got {n}")
    if "anyOf" in sch and not any(not validate(inst, s, p) for s in sch["anyOf"]):
        errs.append(f"{p}: none of anyOf schemas matched")
    return errs


def validate(instance: Any, schema: dict[str, Any], path: str = "") -> list[str]:
    """Validate *instance* against *schema*.

    Returns a list of error strings (empty = valid).
    """
    # Boolean schemas (Draft 2020-12): true = always valid, false = always invalid
    if schema is True:
        return []
    if schema is False:
        return [f"{path}: schema is false, no value is valid"]

    # const -- early return (type-aware: bool != int/float in JSON Schema)
    if "const" in schema and not _json_equal(instance, schema["const"]):
        return [f"{path}: expected const {schema['const']!r}, got {instance!r}"]

    # type -- early return
    if "type" in schema:
        type_name = schema["type"]
        type_names = set(type_name) if isinstance(type_name, list) else {type_name}
        # bool is a subclass of int in Python, but JSON Schema treats them as distinct
        if isinstance(instance, bool):
            if "boolean" not in type_names:
                return [f"{path}: expected type {type_name!r}, got bool"]
        elif isinstance(instance, float) and instance.is_integer() and "integer" in type_names:
            pass  # float with zero fractional part is a valid integer in JSON Schema
        else:
            expected = tuple(t for name in type_names for t in _TYPE_MAP.get(name, ()))
            if expected and not isinstance(instance, expected):
                return [f"{path}: expected type {type_name!r}, got {type(instance).__name__}"]

    errors: list[str] = []
    if "enum" in schema and not any(_json_equal(instance, v) for v in schema["enum"]):
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")
    errors.extend(_check_str(instance, schema, path))
    errors.extend(_check_num(instance, schema, path))
    errors.extend(_check_obj(instance, schema, path))
    errors.extend(_check_arr(instance, schema, path))
    errors.extend(_check_combo(instance, schema, path))
    return errors


def validate_file(
    instance_path: str | Path,
    schema_path: str | Path,
) -> tuple[bool, list[str]]:
    """Validate a JSON file against a JSON Schema file.

    Returns (is_valid, errors).
    """
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    errors = validate(instance, schema)
    return len(errors) == 0, errors


def validate_entry_dict(
    entry: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a ledger entry dict against the CLP schema.

    If no schema is provided, loads the default from bundled schemas.
    """
    if schema is None:
        from hummbl_contracts.schema_loader import load_schema

        schema = load_schema("cognition/clp.ledger_entry")
    errors = validate(entry, schema)
    return len(errors) == 0, errors


def validate_state_dict(
    state: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a shared state dict against the CLP schema."""
    if schema is None:
        from hummbl_contracts.schema_loader import load_schema

        schema = load_schema("cognition/clp.shared_state")
    errors = validate(state, schema)
    return len(errors) == 0, errors
