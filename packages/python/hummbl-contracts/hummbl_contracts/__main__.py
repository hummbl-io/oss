"""CLI for hummbl-contracts schema validation.

Usage:
    python -m hummbl_contracts list
    python -m hummbl_contracts validate <schema> <data_file>
    python -m hummbl_contracts validate-inline <schema> <json_string>

Examples:
    python -m hummbl_contracts list
    python -m hummbl_contracts validate cognition/clp.ledger_entry entry.json
    python -m hummbl_contracts validate governance/governor_decision_record record.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _cmd_list() -> int:
    """List all available schemas."""
    from hummbl_contracts.schema_loader import list_schemas

    schemas = list_schemas()
    if not schemas:
        print("No schemas found.", file=sys.stderr)
        return 1
    print(f"Available schemas ({len(schemas)}):")
    print()
    for name in schemas:
        print(f"  {name}")
    return 0


def _cmd_validate(schema_name: str, data_path: str) -> int:
    """Validate a data file against a named schema."""
    from hummbl_contracts.schema_loader import load_schema
    from hummbl_contracts.schema_validator import validate

    # Load schema
    try:
        schema = load_schema(schema_name)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Load data
    data_file = Path(data_path)
    if not data_file.exists():
        print(f"Error: data file not found: {data_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(data_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {data_path}: {e}", file=sys.stderr)
        return 1

    # Validate
    errors = validate(data, schema)
    if not errors:
        print(f"PASS: {data_path} validates against {schema_name}")
        return 0
    else:
        print(f"FAIL: {data_path} has {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1


def _cmd_validate_inline(schema_name: str, json_string: str) -> int:
    """Validate inline JSON against a named schema."""
    from hummbl_contracts.schema_loader import load_schema
    from hummbl_contracts.schema_validator import validate

    try:
        schema = load_schema(schema_name)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    errors = validate(data, schema)
    if not errors:
        print(f"PASS: input validates against {schema_name}")
        return 0
    else:
        print(f"FAIL: {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 1

    cmd = sys.argv[1]

    if cmd == "list":
        return _cmd_list()
    elif cmd == "validate":
        if len(sys.argv) != 4:
            print("Usage: python -m hummbl_contracts validate <schema> <data_file>")
            return 1
        return _cmd_validate(sys.argv[2], sys.argv[3])
    elif cmd == "validate-inline":
        if len(sys.argv) != 4:
            print("Usage: python -m hummbl_contracts validate-inline <schema> <json_string>")
            return 1
        return _cmd_validate_inline(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: list, validate, validate-inline")
        return 1


if __name__ == "__main__":
    sys.exit(main())
