#!/usr/bin/env python3
"""Static schema registry generator.

Scans a schemas/ directory and generates a manifest.json listing all schemas
with their IDs, versions, and tuple types.

Usage:
    python scripts/static_registry.py
    python scripts/static_registry.py --schemas-dir /path/to/schemas --output manifest.json

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMAS_DIR = REPO_ROOT / "schemas"
DEFAULT_OUTPUT = REPO_ROOT / "registry" / "manifest.json"


def generate_manifest(schemas_dir: Path) -> dict[str, Any]:
    """Generate a registry manifest from a schemas directory."""
    schemas = []
    for p in sorted(schemas_dir.glob("*.schema.json")):
        with p.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        props = schema.get("properties", {})
        tuple_type = None
        tt_schema = props.get("tuple_type", {})
        if isinstance(tt_schema, dict):
            tuple_type = tt_schema.get("const")
        schemas.append({
            "schema_id": p.name,
            "url": schema.get("$id", ""),
            "version": schema.get("version", "unknown"),
            "title": schema.get("title", ""),
            "tuple_type": tuple_type,
        })
    return {
        "registry_version": "0.1.0",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_count": len(schemas),
        "schemas": schemas,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas-dir", default=str(DEFAULT_SCHEMAS_DIR),
                        help="Directory containing schema files")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="Output manifest file path")
    args = parser.parse_args(argv)

    schemas_dir = Path(args.schemas_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = generate_manifest(schemas_dir)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated manifest with {manifest['schema_count']} schemas at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
