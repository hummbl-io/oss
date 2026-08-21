"""Tests for the Authority Sweeper primitive (P34).

P34 sweeps expired authority grants, revokes them, and tracks notifications.
Enforces K6 (AUTHORITY): expired grants must be revoked with operator approval.
"""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.authority_sweeper import (
    build_sweep_record,
    find_expired_grants,
    run_sweep,
    validate_authority_sweeper,
    validate_operator_approval,
    validate_revocation_consistency,
    validate_sweep,
)
from hummbl_governance.schema_validator import ValidationError


NOW = "2026-07-15T12:00:00Z"


def _valid_sweep_record(**overrides):
    base = {
        "schema_version": "1.0.0",
        "sweep_id": "sweep-001",
        "sweep_timestamp": NOW,
        "grants_scanned": 10,
        "grants_expired": 2,
        "grants_revoked": 2,
        "revocations": [
            {
                "grant_id": "g-001",
                "agent_id": "agent-a",
                "role_id": "role-1",
                "authority": "deploy",
                "expired_at": "2026-07-14T10:00:00Z",
                "revoked_at": NOW,
                "notification_sent": True,
            },
            {
                "grant_id": "g-002",
                "agent_id": "agent-b",
                "role_id": "role-2",
                "authority": "approve",
                "expired_at": "2026-07-13T08:00:00Z",
                "revoked_at": NOW,
                "notification_sent": True,
            },
        ],
        "authority": {
            "sweep_operator_id": "operator-001",
            "operator_approval": True,
        },
        "receipt": {
            "receipt_hash": "abc123",
            "receipt_sequence": 42,
        },
    }
    base.update(overrides)
    return base


def _grant(grant_id, agent_id, expires_at, status="active", role_id="role-1", authority="deploy"):
    return {
        "grant_id": grant_id,
        "agent_id": agent_id,
        "role_id": role_id,
        "authority": authority,
        "expires_at": expires_at,
        "status": status,
    }


class TestSchemaValidation:
    def test_valid_record_passes(self):
        record = _valid_sweep_record()
        validate_authority_sweeper(record)

    def test_missing_required_field_fails(self):
        record = _valid_sweep_record()
        del record["sweep_id"]
        with pytest.raises(ValidationError, match="sweep_id"):
            validate_authority_sweeper(record)

    def test_bad_schema_version_fails(self):
        record = _valid_sweep_record(schema_version="not-a-version")
        with pytest.raises(ValidationError, match="schema_version"):
            validate_authority_sweeper(record)

    def test_negative_grants_scanned_fails(self):
        record = _valid_sweep_record(grants_scanned=-1)
        with pytest.raises(ValidationError, match="grants_scanned"):
            validate_authority_sweeper(record)

    def test_additional_property_fails(self):
        record = _valid_sweep_record()
        record["unexpected"] = "field"
        with pytest.raises(ValidationError, match="unexpected"):
            validate_authority_sweeper(record)

    def test_revocation_missing_required_field_fails(self):
        record = _valid_sweep_record()
        del record["revocations"][0]["grant_id"]
        with pytest.raises(ValidationError, match="grant_id"):
            validate_authority_sweeper(record)


class TestOperatorApproval:
    def test_valid_approval_passes(self):
        record = _valid_sweep_record()
        validate_operator_approval(record)

    def test_no_operator_approval_fails(self):
        record = _valid_sweep_record()
        record["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval must be True"):
            validate_operator_approval(record)

    def test_missing_operator_id_fails(self):
        record = _valid_sweep_record()
        record["authority"]["sweep_operator_id"] = ""
        with pytest.raises(ValueError, match="sweep_operator_id"):
            validate_operator_approval(record)

    def test_missing_authority_gate_fails(self):
        record = _valid_sweep_record()
        record["authority"] = "not-a-dict"
        with pytest.raises(ValueError, match="authority gate"):
            validate_operator_approval(record)


class TestRevocationConsistency:
    def test_consistent_counts_pass(self):
        record = _valid_sweep_record()
        validate_revocation_consistency(record)

    def test_count_mismatch_fails(self):
        record = _valid_sweep_record(grants_revoked=3)
        with pytest.raises(ValueError, match="grants_revoked=3"):
            validate_revocation_consistency(record)

    def test_missing_notification_sent_fails(self):
        record = _valid_sweep_record()
        del record["revocations"][0]["notification_sent"]
        with pytest.raises(ValueError, match="notification_sent"):
            validate_revocation_consistency(record)

    def test_empty_revocations_with_zero_count_passes(self):
        record = _valid_sweep_record(
            grants_expired=0,
            grants_revoked=0,
            revocations=[],
        )
        validate_revocation_consistency(record)


class TestFullSweepValidation:
    def test_valid_record_passes(self):
        record = _valid_sweep_record()
        validate_sweep(record)

    def test_schema_failure_propagates(self):
        record = _valid_sweep_record()
        del record["sweep_id"]
        with pytest.raises(ValidationError):
            validate_sweep(record)

    def test_operator_approval_failure_propagates(self):
        record = _valid_sweep_record()
        record["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval"):
            validate_sweep(record)

    def test_revocation_consistency_failure_propagates(self):
        record = _valid_sweep_record(grants_revoked=99)
        with pytest.raises(ValueError, match="grants_revoked=99"):
            validate_sweep(record)


class TestFindExpiredGrants:
    def test_finds_expired_grants(self):
        grants = [
            _grant("g-1", "agent-a", "2026-07-14T10:00:00Z"),
            _grant("g-2", "agent-b", "2026-07-16T10:00:00Z"),  # not expired
            _grant("g-3", "agent-c", "2026-07-10T10:00:00Z"),
        ]
        expired = find_expired_grants(grants, now=NOW)
        assert len(expired) == 2
        assert {g["grant_id"] for g in expired} == {"g-1", "g-3"}

    def test_skips_already_revoked(self):
        grants = [
            _grant("g-1", "agent-a", "2026-07-14T10:00:00Z", status="revoked"),
            _grant("g-2", "agent-b", "2026-07-10T10:00:00Z"),
        ]
        expired = find_expired_grants(grants, now=NOW)
        assert len(expired) == 1
        assert expired[0]["grant_id"] == "g-2"

    def test_skips_already_expired_status(self):
        grants = [
            _grant("g-1", "agent-a", "2026-07-14T10:00:00Z", status="expired"),
        ]
        expired = find_expired_grants(grants, now=NOW)
        assert len(expired) == 0

    def test_skips_grants_without_expiry(self):
        grants = [
            {"grant_id": "g-1", "agent_id": "a", "status": "active"},
        ]
        expired = find_expired_grants(grants, now=NOW)
        assert len(expired) == 0

    def test_empty_list_returns_empty(self):
        assert find_expired_grants([], now=NOW) == []

    def test_exact_expiry_boundary_is_expired(self):
        grants = [
            _grant("g-1", "agent-a", NOW),  # exactly now → expired
        ]
        expired = find_expired_grants(grants, now=NOW)
        assert len(expired) == 1


class TestBuildSweepRecord:
    def test_builds_valid_record(self):
        expired = [
            _grant("g-1", "agent-a", "2026-07-14T10:00:00Z"),
            _grant("g-2", "agent-b", "2026-07-13T08:00:00Z"),
        ]
        record = build_sweep_record(
            sweep_id="sweep-001",
            sweep_operator_id="operator-001",
            grants_scanned=10,
            expired_grants=expired,
            receipt_hash="abc123",
            receipt_sequence=42,
            sweep_timestamp=NOW,
        )
        validate_sweep(record)  # should not raise
        assert record["grants_expired"] == 2
        assert record["grants_revoked"] == 2
        assert len(record["revocations"]) == 2
        assert record["revocations"][0]["grant_id"] == "g-1"
        assert record["revocations"][0]["notification_sent"] is True

    def test_empty_expired_list(self):
        record = build_sweep_record(
            sweep_id="sweep-002",
            sweep_operator_id="operator-001",
            grants_scanned=5,
            expired_grants=[],
            receipt_hash="def456",
            sweep_timestamp=NOW,
        )
        validate_sweep(record)
        assert record["grants_expired"] == 0
        assert record["grants_revoked"] == 0
        assert record["revocations"] == []


class TestRunSweep:
    def test_full_sweep_with_expired_grants(self):
        grants = [
            _grant("g-1", "agent-a", "2026-07-14T10:00:00Z"),
            _grant("g-2", "agent-b", "2026-07-16T10:00:00Z"),  # not expired
            _grant("g-3", "agent-c", "2026-07-10T10:00:00Z"),
        ]
        record = run_sweep(
            grants=grants,
            sweep_id="sweep-001",
            sweep_operator_id="operator-001",
            receipt_hash="abc123",
            receipt_sequence=42,
            now=NOW,
        )
        validate_sweep(record)
        assert record["grants_scanned"] == 3
        assert record["grants_expired"] == 2
        assert record["grants_revoked"] == 2

    def test_full_sweep_no_expired(self):
        grants = [
            _grant("g-1", "agent-a", "2026-07-16T10:00:00Z"),
        ]
        record = run_sweep(
            grants=grants,
            sweep_id="sweep-002",
            sweep_operator_id="operator-001",
            receipt_hash="def456",
            now=NOW,
        )
        validate_sweep(record)
        assert record["grants_expired"] == 0
        assert record["grants_revoked"] == 0

    def test_full_sweep_empty_grants(self):
        record = run_sweep(
            grants=[],
            sweep_id="sweep-003",
            sweep_operator_id="operator-001",
            receipt_hash="ghi789",
            now=NOW,
        )
        validate_sweep(record)
        assert record["grants_scanned"] == 0
        assert record["grants_expired"] == 0
