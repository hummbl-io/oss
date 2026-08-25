"""Authority Sweeper Primitive (P34) — sweeps expired authority grants.

Enforces K6 (AUTHORITY): authority grants have scope, limit, and expiry.
Expired grants must be revoked and the affected agent notified. The sweeper
scans the authority exercise log, identifies grants past their expiry, and
produces a revocation record with notification tracking.

Related invariants:
    K6 (AUTHORITY) — every authority exercise is scoped, limited, and receipted.
    K3 (IDENTITY)  — revoked grants remove the agent's authority to act.

Schema: hummbl_governance/data/authority_sweeper.schema.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "authority_sweeper.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_authority_sweeper(sweep_record: dict[str, Any]) -> None:
    """Validate a sweep record against schema v1.0.0.

    Raises:
        ValidationError: If the record does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(sweep_record, schema)
    if errors:
        raise ValidationError(
            f"Authority sweeper schema validation failed: {'; '.join(errors)}"
        )


def validate_operator_approval(sweep_record: dict[str, Any]) -> None:
    """Enforce the operator-approval gate.

    A sweep that revokes authority grants must be explicitly approved by
    an operator. Auto-sweeps without operator approval are rejected.

    Args:
        sweep_record: The sweep record dict.

    Raises:
        ValueError: If operator_approval is not True or sweep_operator_id is empty.
    """
    authority = sweep_record.get("authority", {})
    if not isinstance(authority, dict):
        raise ValueError(
            "Authority sweeper rejected: authority gate missing or invalid"
        )

    if not authority.get("operator_approval", False):
        raise ValueError(
            "Authority sweeper rejected: operator_approval must be True — "
            "automatic sweeps without operator authorization are not permitted"
        )

    operator_id = authority.get("sweep_operator_id", "")
    if not operator_id or not isinstance(operator_id, str):
        raise ValueError(
            "Authority sweeper rejected: sweep_operator_id must be a non-empty string"
        )


def validate_revocation_consistency(sweep_record: dict[str, Any]) -> None:
    """Validate that revocation count matches the revocations list.

    The grants_revoked field must equal len(revocations). Each revocation
    must have a notification_sent field.

    Args:
        sweep_record: The sweep record dict.

    Raises:
        ValueError: If counts are inconsistent or revocations are malformed.
    """
    revocations = sweep_record.get("revocations", [])
    grants_revoked = sweep_record.get("grants_revoked", 0)

    if not isinstance(revocations, list):
        raise ValueError(
            "Authority sweeper rejected: revocations must be a list"
        )

    if len(revocations) != grants_revoked:
        raise ValueError(
            f"Authority sweeper rejected: grants_revoked={grants_revoked} "
            f"but revocations list has {len(revocations)} entries"
        )

    for i, rev in enumerate(revocations):
        if not isinstance(rev, dict):
            raise ValueError(
                f"Authority sweeper rejected: revocation[{i}] is not a dict"
            )
        if "notification_sent" not in rev:
            raise ValueError(
                f"Authority sweeper rejected: revocation[{i}] missing "
                f"notification_sent field"
            )


def validate_sweep(sweep_record: dict[str, Any]) -> None:
    """Full sweep validation: schema + operator approval + revocation consistency.

    Args:
        sweep_record: The sweep record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If operator approval or revocation consistency fails.
    """
    validate_authority_sweeper(sweep_record)
    validate_operator_approval(sweep_record)
    validate_revocation_consistency(sweep_record)


def find_expired_grants(
    grants: list[dict[str, Any]],
    now: str | None = None,
) -> list[dict[str, Any]]:
    """Identify grants that have passed their expiry timestamp.

    A grant is expired if its 'expires_at' field is in the past relative
    to 'now' and its 'status' is not already 'revoked' or 'expired'.

    Args:
        grants: List of grant dicts, each with 'expires_at' (ISO 8601)
            and optionally 'status' fields.
        now: Reference timestamp (ISO 8601). Defaults to current UTC time.

    Returns:
        List of expired grant dicts (subset of input).
    """
    if now is None:
        now = _utcnow()

    expired: list[dict[str, Any]] = []
    for grant in grants:
        status = grant.get("status", "active")
        if status in ("revoked", "expired"):
            continue
        expires_at = grant.get("expires_at", "")
        if not expires_at:
            continue
        if expires_at <= now:
            expired.append(grant)
    return expired


def build_sweep_record(
    sweep_id: str,
    sweep_operator_id: str,
    grants_scanned: int,
    expired_grants: list[dict[str, Any]],
    receipt_hash: str,
    receipt_sequence: int = 0,
    sweep_timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a valid sweep record from expired grants.

    Args:
        sweep_id: Unique identifier for this sweep.
        sweep_operator_id: Operator authorizing the sweep.
        grants_scanned: Total grants examined.
        expired_grants: List of expired grant dicts to revoke.
        receipt_hash: Hash-chained proof.
        receipt_sequence: Sequence ID for ordering.
        sweep_timestamp: When the sweep ran. Defaults to now.

    Returns:
        A sweep record dict conforming to authority_sweeper.schema.json.
    """
    if sweep_timestamp is None:
        sweep_timestamp = _utcnow()

    revocations: list[dict[str, Any]] = []
    for grant in expired_grants:
        revocations.append(
            {
                "grant_id": grant.get("grant_id", ""),
                "agent_id": grant.get("agent_id", ""),
                "role_id": grant.get("role_id", ""),
                "authority": grant.get("authority", ""),
                "expired_at": grant.get("expires_at", ""),
                "revoked_at": sweep_timestamp,
                "notification_sent": True,
            }
        )

    return {
        "schema_version": "1.0.0",
        "sweep_id": sweep_id,
        "sweep_timestamp": sweep_timestamp,
        "grants_scanned": grants_scanned,
        "grants_expired": len(expired_grants),
        "grants_revoked": len(revocations),
        "revocations": revocations,
        "authority": {
            "sweep_operator_id": sweep_operator_id,
            "operator_approval": True,
        },
        "receipt": {
            "receipt_hash": receipt_hash,
            "receipt_sequence": receipt_sequence,
        },
    }


def run_sweep(
    grants: list[dict[str, Any]],
    sweep_id: str,
    sweep_operator_id: str,
    receipt_hash: str,
    receipt_sequence: int = 0,
    now: str | None = None,
) -> dict[str, Any]:
    """Execute a full sweep: find expired grants, build record, validate.

    Convenience function that combines find_expired_grants + build_sweep_record
    + validate_sweep.

    Args:
        grants: List of all authority grants to scan.
        sweep_id: Unique identifier for this sweep.
        sweep_operator_id: Operator authorizing the sweep.
        receipt_hash: Hash-chained proof.
        receipt_sequence: Sequence ID for ordering.
        now: Reference timestamp. Defaults to current UTC time.

    Returns:
        A validated sweep record dict.

    Raises:
        ValidationError: If the built record fails schema validation.
        ValueError: If operator approval or consistency validation fails.
    """
    expired = find_expired_grants(grants, now=now)
    record = build_sweep_record(
        sweep_id=sweep_id,
        sweep_operator_id=sweep_operator_id,
        grants_scanned=len(grants),
        expired_grants=expired,
        receipt_hash=receipt_hash,
        receipt_sequence=receipt_sequence,
        sweep_timestamp=now,
    )
    validate_sweep(record)
    return record


__all__ = [
    "validate_authority_sweeper",
    "validate_operator_approval",
    "validate_revocation_consistency",
    "validate_sweep",
    "find_expired_grants",
    "build_sweep_record",
    "run_sweep",
]
