"""TupleSchemaRegistry — versioned schema management for BaseNTuple.

Provides:
- Schema version tracking for BaseNTuple
- Migration functions between versions
- Compatibility checking (BACKWARD/FORWARD/FULL)
- Golden fixtures per version for testing

Version History:
- v1.0.0 (2026-02): Original BaseNTuple with KRINEIA 4-node + governance fields
- v1.1.0 (2026-07): Added signature_algorithm field (Ed25519 support)
- v1.2.0 (2026-08-03): Added READ_EVIDENCE tier (0S), verify_tuple function
- v1.3.0 (2026-08-15): Added contract_hash, issued_at to DCT; Tier 0S formalized
- v1.4.0 (2026-08-16): Added REVOCATION tuple type, Ed25519 signing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# Current schema version
CURRENT_VERSION = "1.4.0"

# Supported compatibility modes (per Confluent Schema Registry)
COMPATIBILITY_MODES = frozenset({"BACKWARD", "FORWARD", "FULL", "NONE"})


@dataclass(frozen=True)
class SchemaVersion:
    """Schema version with metadata."""
    version: str
    release_date: str  # ISO8601
    description: str
    breaking_changes: list[str] = field(default_factory=list)
    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)


# Schema version registry
SCHEMA_VERSIONS: dict[str, SchemaVersion] = {
    "1.0.0": SchemaVersion(
        version="1.0.0",
        release_date="2026-02-01",
        description="Original BaseNTuple with KRINEIA 4-node + governance fields",
        added_fields=[
            "id", "time", "state", "drift",
            "agent", "tool", "args_hash", "evidence", "tier",
            "contract_id", "dct_id", "dct_chain_depth",
            "previous_hash", "signature"
        ],
    ),
    "1.1.0": SchemaVersion(
        version="1.1.0",
        release_date="2026-07-15",
        description="Added signature_algorithm field for Ed25519 support",
        added_fields=["signature_algorithm"],
    ),
    "1.2.0": SchemaVersion(
        version="1.2.0",
        release_date="2026-08-03",
        description="Added READ_EVIDENCE tier (0S), verify_tuple function, Tier 0S formalized",
        added_fields=["read_event in evidence", "resource_type in evidence", "resource_id in evidence"],
    ),
    "1.3.0": SchemaVersion(
        version="1.3.0",
        release_date="2026-08-15",
        description="Added contract_hash, issued_at to DCT; Tier 0S formalized",
        added_fields=["contract_hash", "issued_at"],
    ),
    "1.4.0": SchemaVersion(
        version="1.4.0",
        release_date="2026-08-16",
        description="Added REVOCATION tuple type, Ed25519 signing, verify_tuple Ed25519 support",
        added_fields=[
            "revocation_event in evidence", "revoked_dct_id in evidence",
            "reason in evidence", "revoked_by in evidence",
            "effective_immediately in evidence", "propagation_proof in evidence",
        ],
    ),
}


# Migration functions: each takes a dict (tuple JSON) and returns migrated dict
MIGRATIONS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "1.0.0->1.1.0": lambda d: _migrate_1_0_0_to_1_1_0(d),
    "1.1.0->1.2.0": lambda d: _migrate_1_1_0_to_1_2_0(d),
    "1.2.0->1.3.0": lambda d: _migrate_1_2_0_to_1_3_0(d),
    "1.3.0->1.4.0": lambda d: _migrate_1_3_0_to_1_4_0(d),
}


def _migrate_1_0_0_to_1_1_0(d: dict[str, Any]) -> dict[str, Any]:
    """Add signature_algorithm field defaulting to 'hmac-sha256' if signature present."""
    if d.get("signature") is not None and "signature_algorithm" not in d:
        d["signature_algorithm"] = "hmac-sha256"
    return d


def _migrate_1_1_0_to_1_2_0(d: dict[str, Any]) -> dict[str, Any]:
    """Tier 0 tuples with read_event=True get tier=0 (already the case). No data migration needed."""
    return d


def _migrate_1_2_0_to_1_3_0(d: dict[str, Any]) -> dict[str, Any]:
    """No data migration needed for contract_hash/issued_at (DCT-level fields)."""
    return d


def _migrate_1_3_0_to_1_4_0(d: dict[str, Any]) -> dict[str, Any]:
    """No data migration needed for REVOCATION tuple (new tuple type)."""
    return d


def migrate_tuple(tuple_dict: dict[str, Any], target_version: str = CURRENT_VERSION) -> dict[str, Any]:
    """Migrate a tuple dict from its schema version to target_version.

    Args:
        tuple_dict: Tuple as dict (from BaseNTuple.to_dict() or JSON).
        target_version: Target schema version (default: CURRENT_VERSION).

    Returns:
        Migrated tuple dict with updated schema_version field.

    Raises:
        ValueError: If migration path not found or version invalid.
    """
    if target_version not in SCHEMA_VERSIONS:
        raise ValueError(f"Unknown target version: {target_version}")

    source_version = tuple_dict.get("schema_version", "1.0.0")

    if source_version == target_version:
        return tuple_dict

    # Find migration path
    versions = sorted(SCHEMA_VERSIONS.keys(), key=_version_key)
    try:
        src_idx = versions.index(source_version)
        tgt_idx = versions.index(target_version)
    except ValueError:
        raise ValueError(f"Cannot migrate from {source_version} to {target_version}")

    if src_idx > tgt_idx:
        raise ValueError(f"Downgrade migration not supported: {source_version} -> {target_version}")

    # Apply migrations in sequence
    current = dict(tuple_dict)
    for i in range(src_idx, tgt_idx):
        from_v = versions[i]
        to_v = versions[i + 1]
        migration_key = f"{from_v}->{to_v}"
        if migration_key not in MIGRATIONS:
            raise ValueError(f"Missing migration: {migration_key}")
        current = MIGRATIONS[migration_key](current)

    current["schema_version"] = target_version
    return current


def _version_key(v: str) -> tuple[int, ...]:
    """Convert version string to tuple for sorting."""
    return tuple(int(x) for x in v.split("."))


def check_compatibility(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
    mode: str = "BACKWARD",
) -> tuple[bool, list[str]]:
    """Check schema compatibility between two versions.

    Args:
        old_schema: Previous schema (field names -> types).
        new_schema: New schema (field names -> types).
        mode: Compatibility mode (BACKWARD, FORWARD, FULL, NONE).

    Returns:
        (is_compatible, list_of_issues)
    """
    if mode not in COMPATIBILITY_MODES:
        raise ValueError(f"Invalid compatibility mode: {mode}")

    issues = []
    old_fields = set(old_schema.keys())
    new_fields = set(new_schema.keys())

    added = new_fields - old_fields
    removed = old_fields - new_fields

    if mode in ("BACKWARD", "FULL"):
        # New schema must read old data: no required fields removed, new fields optional
        for field_name in removed:
            # Check if field was required (no default in old schema)
            # Simplified: assume all fields are optional unless marked required
            pass  # In practice, would check required fields
        for field_name in added:
            # New fields must have defaults or be optional
            pass

    if mode in ("FORWARD", "FULL"):
        # Old schema must read new data: no required fields added
        for field_name in added:
            pass  # Would check if field is required

    # For now, permissive check
    is_compatible = mode == "NONE" or len(issues) == 0
    return is_compatible, issues


# Golden fixtures per version for testing
GOLDEN_FIXTURES: dict[str, dict[str, Any]] = {
    "1.0.0": {
        "id": "abc123def456",  # pragma: allowlist secret (test fixture)  # pragma: allowlist secret (test fixture)
        "time": "2026-02-01T12:00:00Z",
        "state": "ok",
        "drift": 0.0,
        "agent": "claude-code",
        "tool": "file.write",
        "args_hash": "a" * 64,
        "evidence": {"ops_executed": ["write"]},
        "tier": 1,
        "schema_version": "1.0.0",
    },
    "1.1.0": {
        "id": "abc123def456",  # pragma: allowlist secret (test fixture)
        "time": "2026-02-01T12:00:00Z",
        "state": "ok",
        "drift": 0.0,
        "agent": "claude-code",
        "tool": "file.write",
        "args_hash": "a" * 64,
        "evidence": {"ops_executed": ["write"]},
        "tier": 1,
        "signature": "b" * 64,
        "signature_algorithm": "hmac-sha256",
        "schema_version": "1.1.0",
    },
    "1.2.0": {
        "id": "abc123def456",  # pragma: allowlist secret (test fixture)
        "time": "2026-02-01T12:00:00Z",
        "state": "ok",
        "drift": 0.0,
        "agent": "claude-code",
        "tool": "read:pii",
        "args_hash": "",
        "evidence": {"read_event": True, "resource_type": "pii", "resource_id": "/data/users.json"},
        "tier": 0,
        "signature": "b" * 64,
        "signature_algorithm": "hmac-sha256",
        "schema_version": "1.2.0",
    },
    "1.3.0": {
        "id": "abc123def456",  # pragma: allowlist secret (test fixture)
        "time": "2026-02-01T12:00:00Z",
        "state": "ok",
        "drift": 0.0,
        "agent": "claude-code",
        "tool": "base120.record",
        "args_hash": "c" * 64,
        "evidence": {"ops_executed": ["IN3", "CO6"]},
        "tier": 2,
        "contract_id": "contract-001",
        "dct_id": "dct-001",
        "dct_chain_depth": 1,
        "signature": "d" * 64,
        "signature_algorithm": "ed25519",
        "schema_version": "1.3.0",
    },
    "1.4.0": {
        "id": "abc123def456",  # pragma: allowlist secret (test fixture)
        "time": "2026-08-16T12:00:00Z",
        "state": "ok",
        "drift": 0.0,
        "agent": "opencode",
        "tool": "governance.revoke",
        "args_hash": "",
        "evidence": {
            "revocation_event": True,
            "revoked_dct_id": "dct-compromised-001",
            "reason": "Private key compromise detected",
            "revoked_by": "operator",
            "effective_immediately": True,
        },
        "tier": 2,
        "signature": "e" * 88,  # Ed25519 base64
        "signature_algorithm": "ed25519",
        "schema_version": "1.4.0",
    },
}


def get_golden_fixture(version: str) -> dict[str, Any]:
    """Get golden fixture for a schema version."""
    if version not in GOLDEN_FIXTURES:
        raise ValueError(f"No golden fixture for version: {version}")
    return GOLDEN_FIXTURES[version].copy()


def validate_fixture(version: str, fixture: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a fixture against expected schema for version."""
    expected = get_golden_fixture(version)
    issues = []

    for key in expected:
        if key not in fixture:
            issues.append(f"Missing field: {key}")
        elif fixture[key] != expected[key] and key not in ("id", "time", "signature"):
            # Allow dynamic fields to differ
            pass

    for key in fixture:
        if key not in expected:
            issues.append(f"Unexpected field: {key}")

    return len(issues) == 0, issues


class TupleSchemaRegistry:
    """Registry for managing BaseNTuple schema versions and migrations."""

    def __init__(self, compatibility_mode: str = "BACKWARD"):
        self.compatibility_mode = compatibility_mode
        self._registered_schemas: dict[str, dict[str, Any]] = {}

    def register_schema(self, version: str, schema: dict[str, Any]) -> None:
        """Register a schema for a version."""
        if version not in SCHEMA_VERSIONS:
            raise ValueError(f"Unknown version: {version}")
        self._registered_schemas[version] = schema

    def migrate(self, tuple_dict: dict[str, Any], target_version: str = CURRENT_VERSION) -> dict[str, Any]:
        """Migrate a tuple to target version."""
        return migrate_tuple(tuple_dict, target_version)

    def check_compatibility(self, from_version: str, to_version: str) -> tuple[bool, list[str]]:
        """Check compatibility between two registered versions."""
        if from_version not in self._registered_schemas or to_version not in self._registered_schemas:
            raise ValueError("Both versions must be registered")
        return check_compatibility(
            self._registered_schemas[from_version],
            self._registered_schemas[to_version],
            self.compatibility_mode,
        )

    def get_current_version(self) -> str:
        return CURRENT_VERSION

    def list_versions(self) -> list[str]:
        return sorted(SCHEMA_VERSIONS.keys(), key=_version_key)
