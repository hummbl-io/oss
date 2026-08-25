#!/usr/bin/env python3
"""Migrate schemas and examples from TUPLES_v1 to TUPLES_v2 (layered convergence).

Changes:
  Layer 1 (all schemas/examples):
    - Add required `id` field (string, minLength 1)
    - Add required `time` field (string, minLength 1)
    - Remove `timestamp` from required/properties (renamed to `time`)
    - Remove `entry_id` from properties (renamed to `id`)

  Layer 2 (IDP schemas/examples only — contract, dct, dctx, evidence, attest, system):
    - Add required `state` field (string, enum: ok/blocked/error)
    - Add required `drift` field (number, minimum 0)
    - Add required `tier` field (integer, minimum 0)
    - Add required `agent` field (string)
    - Add required `tool` field (string)

Stdlib-only. Idempotent — safe to run multiple times.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = REPO_ROOT / "examples"

# IDP tuple types that get Layer 2 governance fields
IDP_TYPES = frozenset({
    "CONTRACT", "DCT", "DCTX", "EVIDENCE", "ATTEST", "SYSTEM",
})

# Schema files that correspond to IDP types
IDP_SCHEMA_FILES = frozenset({
    "contract.schema.json",
    "dct.schema.json",
    "dctx.schema.json",
    "evidence.schema.json",
    "attest.schema.json",
    "system.schema.json",
})


def _short_id() -> str:
    return str(uuid.uuid4())[:12]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Schema migration
# ---------------------------------------------------------------------------

LAYER_1_PROPERTIES = {
    "id": {"type": "string", "minLength": 1},
    "time": {"type": "string", "minLength": 1},
}

LAYER_2_PROPERTIES = {
    "state": {"type": "string", "enum": ["ok", "blocked", "error"]},
    "drift": {"type": "number", "minimum": 0},
    "tier": {"type": "integer", "minimum": 0},
    "agent": {"type": "string"},
    "tool": {"type": "string"},
}


def migrate_schema(path: Path) -> bool:
    """Migrate a single schema file. Returns True if modified."""
    with open(path) as f:
        schema = json.load(f)

    modified = False
    props = schema.setdefault("properties", {})
    required = schema.get("required", [])

    # Layer 1: add id and time
    if "id" not in props:
        props["id"] = LAYER_1_PROPERTIES["id"]
        modified = True
    if "time" not in props:
        props["time"] = LAYER_1_PROPERTIES["time"]
        modified = True

    # Rename timestamp -> time
    if "timestamp" in props:
        del props["timestamp"]
        modified = True
    if "timestamp" in required:
        required = [("time" if r == "timestamp" else r) for r in required]
        modified = True

    # Rename entry_id -> id
    if "entry_id" in props:
        del props["entry_id"]
        modified = True
    if "entry_id" in required:
        required = [("id" if r == "entry_id" else r) for r in required]
        modified = True

    # Add id, time to required if not present
    for field in ("id", "time"):
        if field not in required:
            # Insert after tuple_type
            idx = required.index("tuple_type") + 1 if "tuple_type" in required else 0
            required.insert(idx, field)
            modified = True

    # Layer 2: IDP schemas get governance fields
    if path.name in IDP_SCHEMA_FILES:
        for field, prop_def in LAYER_2_PROPERTIES.items():
            if field not in props:
                props[field] = prop_def
                modified = True
            if field not in required:
                required.append(field)
                modified = True

    # Remove signature from required (Layer 4, optional)
    if "signature" in required:
        required.remove("signature")
        modified = True

    if modified:
        schema["required"] = required
        # Reorder properties: Layer 1 first, then Layer 2, then domain, then tuple_data
        ordered_props = {}
        layer_order = ["tuple_type", "id", "time"]
        layer_2_order = ["state", "drift", "tier", "agent", "tool"]
        # Layer 1
        for k in layer_order:
            if k in props:
                ordered_props[k] = props[k]
        # Layer 2 (if IDP)
        if path.name in IDP_SCHEMA_FILES:
            for k in layer_2_order:
                if k in props:
                    ordered_props[k] = props[k]
        # Domain-specific (everything else except tuple_data and Layer 4)
        layer_4 = {"args_hash", "signature", "previous_hash", "contract_id", "dct_id", "dct_chain_depth"}
        for k, v in props.items():
            if k not in ordered_props and k != "tuple_data" and k not in layer_4:
                ordered_props[k] = v
        # Layer 4
        for k in sorted(layer_4):
            if k in props:
                ordered_props[k] = props[k]
        # tuple_data last
        if "tuple_data" in props:
            ordered_props["tuple_data"] = props["tuple_data"]
        schema["properties"] = ordered_props

        with open(path, "w") as f:
            json.dump(schema, f, indent=2)
            f.write("\n")

    return modified


# ---------------------------------------------------------------------------
# Example migration
# ---------------------------------------------------------------------------

def migrate_example(path: Path) -> bool:
    """Migrate a single example file. Returns True if modified."""
    with open(path) as f:
        example = json.load(f)

    modified = False
    tuple_type = example.get("tuple_type", "")

    # Layer 1: add id if missing
    if "id" not in example:
        # Use entry_id if available, otherwise generate
        if "entry_id" in example:
            example["id"] = example.pop("entry_id")
        else:
            example["id"] = _short_id()
        modified = True
    elif "entry_id" in example:
        del example["entry_id"]
        modified = True

    # Layer 1: rename timestamp -> time
    if "time" not in example:
        if "timestamp" in example:
            example["time"] = example.pop("timestamp")
        else:
            example["time"] = _utc_now()
        modified = True
    elif "timestamp" in example:
        del example["timestamp"]
        modified = True

    # Layer 2: IDP types get governance fields
    if tuple_type in IDP_TYPES:
        if "state" not in example:
            example["state"] = "ok"
            modified = True
        if "drift" not in example:
            example["drift"] = 0.0
            modified = True
        if "tier" not in example:
            example["tier"] = 1
            modified = True
        if "agent" not in example:
            example["agent"] = "claude-code"
            modified = True
        if "tool" not in example:
            example["tool"] = "governance.tuple"
            modified = True

    if modified:
        # Reorder keys: Layer 1 first, Layer 2, domain, tuple_data last
        ordered = {}
        key_order = ["tuple_type", "id", "time"]
        if tuple_type in IDP_TYPES:
            key_order += ["state", "drift", "tier", "agent", "tool"]

        for k in key_order:
            if k in example:
                ordered[k] = example[k]
        for k, v in example.items():
            if k not in ordered and k != "tuple_data":
                ordered[k] = v
        if "tuple_data" in example:
            ordered["tuple_data"] = example["tuple_data"]

        with open(path, "w") as f:
            json.dump(ordered, f, indent=2)
            f.write("\n")

    return modified


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== Migrating schemas ===")
    schema_count = 0
    for schema_path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        if migrate_schema(schema_path):
            print(f"  MIGRATED {schema_path.name}")
            schema_count += 1
        else:
            print(f"  OK       {schema_path.name}")

    print(f"\n=== Migrating examples ===")
    example_count = 0
    for example_path in sorted(EXAMPLES_DIR.rglob("*.json")):
        if migrate_example(example_path):
            print(f"  MIGRATED {example_path.relative_to(REPO_ROOT)}")
            example_count += 1
        else:
            print(f"  OK       {example_path.relative_to(REPO_ROOT)}")

    print(f"\nMigrated {schema_count} schema(s), {example_count} example(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
