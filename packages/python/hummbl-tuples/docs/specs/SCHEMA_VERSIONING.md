# Schema Versioning and Migration Strategy (A6)

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #32 (A6: Draft schema versioning and migration strategy)
- **Date:** 2026-07-01

## Summary

This document defines how HUMMBL tuple schemas evolve over time, how version information is recorded, and how old-format tuples can be migrated to new formats.

## Versioning Model

### Schema version field

Every schema MUST include a `schema_version` field in its `$id`:

```
"$id": "https://hummbl.dev/schemas/tuples/contract.schema.json"
```

The URL path implies the version. When a breaking change is made:
1. The schema file is renamed: `contract.schema.json` → `contract.v2.schema.json`
2. The old schema is kept for backward compatibility
3. A migration function is added to `scripts/migrate_tuples.py`

### Tuple version field

Tuples do NOT carry a schema version field by default. The schema version is implied by the tuple structure. The migration CLI detects the source version by inspecting the tuple's fields.

### Semantic versioning for schemas

- **Major (vN)**: Breaking changes — removed fields, changed types, changed enum values
- **Minor**: Additive changes — new optional fields, new enum values (backward compatible)
- **Patch**: Documentation, description, or formatting changes (no structural impact)

Only major version changes require migration. Minor and patch changes are backward compatible.

### Version detection

The migration CLI detects the source version by:
1. Checking for presence/absence of fields
2. Checking field types
3. Checking enum values

Each migration function declares its source and target versions explicitly.

## Migration Strategy

### Migration CLI

`scripts/migrate_tuples.py` provides:

```
python scripts/migrate_tuples.py --input old.json --output new.json --target-version v2
python scripts/migrate_tuples.py --input-dir old_dir/ --output-dir new_dir/ --target-version v2
```

### Migration functions

Each migration is a Python function registered in a migration registry:

```python
MIGRATIONS = {
    ("v1", "v2"): migrate_v1_to_v2,
    ("v2", "v3"): migrate_v2_to_v3,
}
```

A migration function:
1. Takes a tuple dict as input
2. Returns a new tuple dict with the target version's structure
3. Records what was changed in a migration log
4. Preserves all data that hasn't changed

### Chained migrations

If a tuple needs to migrate from v1 to v3, the CLI chains v1→v2 and v2→v3 migrations automatically.

### Migration log

Each migration produces a log entry:

```json
{
  "source_version": "v1",
  "target_version": "v2",
  "tuple_id": "...",
  "changes": ["added field X", "renamed field Y to Z"],
  "migrated_at": "2026-07-01T00:00:00Z"
}
```

## Backward Compatibility Rules

1. **Adding optional fields**: Always backward compatible. Old tuples remain valid.
2. **Removing fields**: Breaking change. Requires major version bump and migration.
3. **Changing field types**: Breaking change. Requires major version bump and migration.
4. **Adding enum values**: Backward compatible (old tuples still valid).
5. **Removing enum values**: Breaking change. Requires major version bump and migration.
6. **Changing required to optional**: Backward compatible.
7. **Changing optional to required**: Breaking change. Requires major version bump and migration.

## Do Not Infer

- Do not infer that migration preserves all semantic meaning (some information may be lost).
- Do not infer that backward-compatible changes are always safe (they may affect downstream consumers).
- Do not infer that the migration CLI is a substitute for testing.
- Do not infer that schema versioning is the same as tuple versioning (tuples do not carry version fields).

## Non-goals

- Not a full schema registry (that's issue #37, B5)
- Not a runtime version negotiation protocol
- Not a replacement for integration testing
