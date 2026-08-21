"""Tests for the Trust Adjuster primitive (P36).

P36 creates a compliance-to-identity loop: violations reduce an agent's
trust tier. Enforces K3 (IDENTITY): trust tier changes require evidence
and operator approval.
"""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.trust_adjuster import (
    build_adjustment,
    compute_proposed_tier,
    run_adjustment,
    validate_adjustment,
    validate_operator_approval,
    validate_severity_consistency,
    validate_tier_transition,
    validate_trust_adjuster,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_adjustment(**overrides):
    base = {
        "schema_version": "1.0.0",
        "adjustment_id": "adj-001",
        "agent_id": "agent-a",
        "current_trust_tier": "TRUSTED",
        "proposed_trust_tier": "MEDIUM",
        "violation_refs": ["viol-001", "viol-002"],
        "severity": "medium",
        "adjustment_reason": "Two compliance violations in 24h window",
        "authority": {
            "adjusted_by": "operator-001",
            "operator_approval": True,
            "automated": False,
        },
        "receipt": {
            "receipt_hash": "abc123",
            "receipt_sequence": 42,
        },
    }
    base.update(overrides)
    return base


class TestSchemaValidation:
    def test_valid_record_passes(self):
        validate_trust_adjuster(_valid_adjustment())

    def test_missing_required_field_fails(self):
        record = _valid_adjustment()
        del record["adjustment_id"]
        with pytest.raises(ValidationError, match="adjustment_id"):
            validate_trust_adjuster(record)

    def test_bad_schema_version_fails(self):
        record = _valid_adjustment(schema_version="bad")
        with pytest.raises(ValidationError, match="schema_version"):
            validate_trust_adjuster(record)

    def test_invalid_trust_tier_fails(self):
        record = _valid_adjustment(current_trust_tier="GOD")
        with pytest.raises(ValidationError, match="current_trust_tier"):
            validate_trust_adjuster(record)

    def test_empty_violation_refs_fails(self):
        record = _valid_adjustment(violation_refs=[])
        with pytest.raises(ValidationError, match="violation_refs"):
            validate_trust_adjuster(record)

    def test_invalid_severity_fails(self):
        record = _valid_adjustment(severity="extreme")
        with pytest.raises(ValidationError, match="severity"):
            validate_trust_adjuster(record)

    def test_additional_property_fails(self):
        record = _valid_adjustment()
        record["unexpected"] = True
        with pytest.raises(ValidationError, match="unexpected"):
            validate_trust_adjuster(record)


class TestOperatorApproval:
    def test_valid_approval_passes(self):
        validate_operator_approval(_valid_adjustment())

    def test_no_approval_fails(self):
        record = _valid_adjustment()
        record["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval must be True"):
            validate_operator_approval(record)

    def test_empty_adjusted_by_fails(self):
        record = _valid_adjustment()
        record["authority"]["adjusted_by"] = ""
        with pytest.raises(ValueError, match="adjusted_by"):
            validate_operator_approval(record)

    def test_missing_authority_gate_fails(self):
        record = _valid_adjustment()
        record["authority"] = "not-a-dict"
        with pytest.raises(ValueError, match="authority gate"):
            validate_operator_approval(record)


class TestTierTransition:
    def test_valid_reduction_passes(self):
        validate_tier_transition(_valid_adjustment())

    def test_promotion_fails(self):
        record = _valid_adjustment(
            current_trust_tier="MEDIUM",
            proposed_trust_tier="TRUSTED",
        )
        with pytest.raises(ValueError, match="higher than current"):
            validate_tier_transition(record)

    def test_no_change_fails(self):
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="TRUSTED",
        )
        with pytest.raises(ValueError, match="no change"):
            validate_tier_transition(record)

    def test_invalid_current_tier_fails(self):
        record = _valid_adjustment(current_trust_tier="INVALID")
        with pytest.raises(ValueError, match="current_trust_tier"):
            validate_tier_transition(record)


class TestSeverityConsistency:
    def test_valid_medium_passes(self):
        validate_severity_consistency(_valid_adjustment())

    def test_low_severity_1_step(self):
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="MEDIUM-HIGH",
            severity="low",
        )
        validate_severity_consistency(record)

    def test_high_severity_3_steps(self):
        record = _valid_adjustment(
            current_trust_tier="OWNER",
            proposed_trust_tier="MEDIUM",
            severity="high",
        )
        validate_severity_consistency(record)

    def test_critical_must_be_revoked(self):
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="MEDIUM",
            severity="critical",
        )
        with pytest.raises(ValueError, match="critical.*REVOKED"):
            validate_severity_consistency(record)

    def test_critical_to_revoked_passes(self):
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="REVOKED",
            severity="critical",
        )
        validate_severity_consistency(record)

    def test_insufficient_reduction_fails(self):
        # medium requires 2 steps, but only 1 applied
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="MEDIUM-HIGH",  # only 1 step
            severity="medium",  # requires 2
        )
        with pytest.raises(ValueError, match="at least 2 tier step"):
            validate_severity_consistency(record)

    def test_more_reduction_than_required_passes(self):
        # high requires 3 steps, but applying 4 is OK (operator discretion)
        record = _valid_adjustment(
            current_trust_tier="OWNER",
            proposed_trust_tier="PROBATIONARY",  # 4 steps
            severity="high",  # requires 3
        )
        validate_severity_consistency(record)


class TestFullValidation:
    def test_valid_record_passes(self):
        validate_adjustment(_valid_adjustment())

    def test_schema_failure_propagates(self):
        record = _valid_adjustment()
        del record["agent_id"]
        with pytest.raises(ValidationError):
            validate_adjustment(record)

    def test_operator_failure_propagates(self):
        record = _valid_adjustment()
        record["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval"):
            validate_adjustment(record)

    def test_transition_failure_propagates(self):
        record = _valid_adjustment(
            current_trust_tier="MEDIUM",
            proposed_trust_tier="TRUSTED",
        )
        with pytest.raises(ValueError, match="higher than current"):
            validate_adjustment(record)

    def test_severity_failure_propagates(self):
        record = _valid_adjustment(
            current_trust_tier="TRUSTED",
            proposed_trust_tier="MEDIUM-HIGH",
            severity="medium",
        )
        with pytest.raises(ValueError, match="at least 2"):
            validate_adjustment(record)


class TestComputeProposedTier:
    def test_low_1_step(self):
        assert compute_proposed_tier("TRUSTED", "low") == "MEDIUM-HIGH"

    def test_medium_2_steps(self):
        assert compute_proposed_tier("TRUSTED", "medium") == "MEDIUM"

    def test_high_3_steps(self):
        assert compute_proposed_tier("OWNER", "high") == "MEDIUM"

    def test_critical_to_revoked(self):
        assert compute_proposed_tier("TRUSTED", "critical") == "REVOKED"

    def test_clamps_at_revoked(self):
        # low from PROBATIONARY should still be REVOKED (can't go lower)
        assert compute_proposed_tier("PROBATIONARY", "low") == "REVOKED"

    def test_high_from_medium_clamps(self):
        # high from MEDIUM: 3 steps → clamped to REVOKED
        assert compute_proposed_tier("MEDIUM", "high") == "REVOKED"

    def test_invalid_tier_raises(self):
        with pytest.raises(ValueError, match="Invalid current_tier"):
            compute_proposed_tier("GOD", "low")

    def test_invalid_severity_raises(self):
        with pytest.raises(ValueError, match="Invalid severity"):
            compute_proposed_tier("TRUSTED", "extreme")


class TestBuildAdjustment:
    def test_builds_valid_record(self):
        record = build_adjustment(
            adjustment_id="adj-001",
            agent_id="agent-a",
            current_trust_tier="TRUSTED",
            severity="medium",
            violation_refs=["viol-001"],
            adjusted_by="operator-001",
            receipt_hash="abc123",
            adjustment_reason="Two violations",
        )
        validate_adjustment(record)
        assert record["proposed_trust_tier"] == "MEDIUM"
        assert record["authority"]["operator_approval"] is True

    def test_automated_flag(self):
        record = build_adjustment(
            adjustment_id="adj-002",
            agent_id="agent-b",
            current_trust_tier="MEDIUM",
            severity="low",
            violation_refs=["viol-002"],
            adjusted_by="compliance-pipeline",
            receipt_hash="def456",
            adjustment_reason="Auto-adjustment",
            automated=True,
        )
        validate_adjustment(record)
        assert record["authority"]["automated"] is True
        assert record["proposed_trust_tier"] == "PROBATIONARY"


class TestRunAdjustment:
    def test_full_run(self):
        record = run_adjustment(
            adjustment_id="adj-003",
            agent_id="agent-c",
            current_trust_tier="OWNER",
            severity="critical",
            violation_refs=["viol-003", "viol-004"],
            adjusted_by="operator-001",
            receipt_hash="ghi789",
            adjustment_reason="Critical violation",
        )
        validate_adjustment(record)
        assert record["proposed_trust_tier"] == "REVOKED"

    def test_low_severity_run(self):
        record = run_adjustment(
            adjustment_id="adj-004",
            agent_id="agent-d",
            current_trust_tier="MEDIUM-HIGH",
            severity="low",
            violation_refs=["viol-005"],
            adjusted_by="operator-001",
            receipt_hash="jkl012",
            adjustment_reason="Minor violation",
        )
        validate_adjustment(record)
        assert record["proposed_trust_tier"] == "MEDIUM"


class TestEdgeCases:
    def test_revoked_agent_cannot_be_reduced_further(self):
        # REVOKED → any severity → still REVOKED (clamped)
        record = _valid_adjustment(
            current_trust_tier="REVOKED",
            proposed_trust_tier="REVOKED",
            severity="low",
        )
        # This should fail at tier_transition (no change)
        with pytest.raises(ValueError, match="no change"):
            validate_tier_transition(record)

    def test_owner_critical_direct_to_revoked(self):
        record = run_adjustment(
            adjustment_id="adj-005",
            agent_id="agent-e",
            current_trust_tier="OWNER",
            severity="critical",
            violation_refs=["viol-006"],
            adjusted_by="operator-001",
            receipt_hash="mno345",
            adjustment_reason="Critical",
        )
        assert record["proposed_trust_tier"] == "REVOKED"
