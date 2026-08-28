"""Schema loader for bundled HUMMBL contract schemas.

Discovers and loads JSON Schema files from the schemas/ directory
shipped with the package.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Root of the schemas directory, relative to this file's package
_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _schema_name(path: Path) -> str:
    """Convert a schema file path to a logical name.

    Example: schemas/cognition/clp.ledger_entry.schema.json -> cognition/clp.ledger_entry
    """
    relative = path.relative_to(_SCHEMAS_DIR)
    name = relative.as_posix()
    # Strip .schema.json or .json suffix
    if name.endswith(".schema.json"):
        name = name[: -len(".schema.json")]
    elif name.endswith(".json"):
        name = name[: -len(".json")]
    return name


def list_schemas() -> list[str]:
    """List all available schema names.

    Returns sorted list of schema names like:
        ['cognition/clp.ledger_entry', 'governance/governor_decision_record', ...]
    """
    if not _SCHEMAS_DIR.exists():
        return []
    schemas = []
    for path in sorted(_SCHEMAS_DIR.rglob("*.json")):
        if path.name == ".gitkeep":
            continue
        schemas.append(_schema_name(path))
    return schemas


def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by logical name.

    Args:
        name: Schema name like 'cognition/clp.ledger_entry' or
              'governance/governor_decision_record'.

    Returns:
        Parsed JSON Schema dict.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    # Try with .schema.json first, then .json
    path = _SCHEMAS_DIR / f"{name}.schema.json"
    if not path.exists():
        path = _SCHEMAS_DIR / f"{name}.json"
    if not path.exists():
        available = list_schemas()
        raise FileNotFoundError(
            f"Schema not found: {name!r}. "
            f"Available schemas: {available}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def schema_path(name: str) -> Path:
    """Return the filesystem path for a schema by logical name.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    path = _SCHEMAS_DIR / f"{name}.schema.json"
    if not path.exists():
        path = _SCHEMAS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {name!r}")
    return path
