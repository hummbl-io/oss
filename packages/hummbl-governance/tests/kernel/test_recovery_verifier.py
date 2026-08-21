"""Tests for the Recovery Verifier primitive (P29)."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.recovery_verifier import (
    validate_recovery_verifier,
    validate_root_cause,
    validate_recovery_operator_approval,
    validate_recovery,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_verification(**overrides):
    """Build a valid recovery-verification record with optional overrides."""
    base = {
        "schema_version": "1.0.0",
        "halt_event_id": "halt-001",
        "halt_source": "kill_switch",
        "root_cause_analysis": {
            "identified": True,
            "analysis_summary": "Memory exhaustion due to unbounded queue.",
            "root_cause_category": "resource_exhaustion",
            "fix_applied": True,
            "fix_description": "Added bounded queue with backpressure.",
        },
        "evidence": {
            "evidence_refs": ["ref-001", "ref-002"],
            "test_results_ref": "tests/run-001",
            "health_check_ref": "health/probe-001",
        },
        "operator_approval": {
            "approved": True,
            "approver_id": "operator-001",
            "approval_timestamp": "2026-01-01T00:00:00Z",
            "conditions": ["monitor for 30 minutes"],
        },
        "receipt": {
            "receipt_hash": "abc123",
            "receipt_sequence": 42,
        },
        "re_engagement_plan": {
            "strategy": "gradual",
            "monitoring_duration_minutes": 30,
            "rollback_on_failure": True,
        },
    }
    base.update(overrides)
    return base


class TestSchemaValidation:
    def test_valid_verification_passes(self):
        verification = _valid_verification()
        validate_recovery_verifier(verification)

    def test_missing_required_field_fails(self):
        verification = _valid_verification()
        del verification["operator_approval"]
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_missing_nested_required_field_fails(self):
        verification = _valid_verification()
        del verification["root_cause_analysis"]["analysis_summary"]
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_invalid_halt_source_fails(self):
        verification = _valid_verification(halt_source="unknown_source")
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_invalid_schema_version_fails(self):
        verification = _valid_verification(schema_version="1.0")
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_empty_halt_event_id_fails(self):
        verification = _valid_verification(halt_event_id="")
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_empty_evidence_refs_fails(self):
        verification = _valid_verification(
            evidence={"evidence_refs": []}
        )
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_additional_properties_fails(self):
        verification = _valid_verification()
        verification["unexpected_field"] = "value"
        with pytest.raises(ValidationError):
            validate_recovery_verifier(verification)

    def test_valid_halt_source_enums(self):
        for source in [
            "kill_switch",
            "circuit_breaker",
            "manual",
            "kernel_panic",
            "external",
        ]:
            verification = _valid_verification(halt_source=source)
            validate_recovery_verifier(verification)


class TestRootCause:
    def test_identified_true_ok(self):
        verification = _valid_verification()
        validate_root_cause(verification)

    def test_identified_false_fails(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": False,
                "analysis_summary": "Cause not yet determined.",
            }
        )
        with pytest.raises(ValueError, match="identified must be True"):
            validate_root_cause(verification)

    def test_fix_applied_without_description_fails(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Memory exhaustion.",
                "fix_applied": True,
                "fix_description": "",
            }
        )
        with pytest.raises(ValueError, match="fix_description"):
            validate_root_cause(verification)

    def test_fix_applied_with_description_ok(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Memory exhaustion.",
                "fix_applied": True,
                "fix_description": "Bounded queue added.",
            }
        )
        validate_root_cause(verification)

    def test_fix_not_applied_ok(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Cause identified; fix pending.",
                "fix_applied": False,
            }
        )
        validate_root_cause(verification)

    def test_missing_root_cause_analysis_fails(self):
        verification = _valid_verification()
        del verification["root_cause_analysis"]
        with pytest.raises(ValueError, match="root_cause_analysis"):
            validate_root_cause(verification)

    def test_root_cause_analysis_not_dict_fails(self):
        verification = _valid_verification()
        verification["root_cause_analysis"] = "not-a-dict"
        with pytest.raises(ValueError, match="root_cause_analysis"):
            validate_root_cause(verification)


class TestOperatorApproval:
    def test_approved_ok(self):
        verification = _valid_verification()
        validate_recovery_operator_approval(verification)

    def test_not_approved_fails(self):
        verification = _valid_verification(
            operator_approval={
                "approved": False,
                "approver_id": "operator-001",
            }
        )
        with pytest.raises(ValueError, match="approved must be True"):
            validate_recovery_operator_approval(verification)

    def test_empty_approver_id_fails(self):
        verification = _valid_verification(
            operator_approval={
                "approved": True,
                "approver_id": "",
            }
        )
        with pytest.raises(ValueError, match="approver_id"):
            validate_recovery_operator_approval(verification)

    def test_missing_approver_id_fails(self):
        verification = _valid_verification(
            operator_approval={
                "approved": True,
            }
        )
        with pytest.raises(ValueError, match="approver_id"):
            validate_recovery_operator_approval(verification)

    def test_missing_operator_approval_fails(self):
        verification = _valid_verification()
        del verification["operator_approval"]
        with pytest.raises(ValueError, match="operator_approval"):
            validate_recovery_operator_approval(verification)

    def test_operator_approval_not_dict_fails(self):
        verification = _valid_verification()
        verification["operator_approval"] = "not-a-dict"
        with pytest.raises(ValueError, match="operator_approval"):
            validate_recovery_operator_approval(verification)


class TestFullRecovery:
    def test_valid_full_recovery(self):
        verification = _valid_verification()
        validate_recovery(verification)

    def test_full_recovery_schema_failure(self):
        verification = _valid_verification()
        del verification["halt_event_id"]
        with pytest.raises(ValidationError):
            validate_recovery(verification)

    def test_full_recovery_root_cause_failure(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": False,
                "analysis_summary": "Pending.",
            }
        )
        with pytest.raises(ValueError, match="identified must be True"):
            validate_recovery(verification)

    def test_full_recovery_operator_approval_failure(self):
        verification = _valid_verification(
            operator_approval={
                "approved": False,
                "approver_id": "operator-001",
            }
        )
        with pytest.raises(ValueError, match="approved must be True"):
            validate_recovery(verification)

    def test_full_recovery_fix_without_description(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Memory exhaustion.",
                "fix_applied": True,
                "fix_description": "",
            }
        )
        with pytest.raises(ValueError, match="fix_description"):
            validate_recovery(verification)

    def test_full_recovery_circuit_breaker_source(self):
        verification = _valid_verification(halt_source="circuit_breaker")
        validate_recovery(verification)

    def test_full_recovery_manual_source(self):
        verification = _valid_verification(halt_source="manual")
        validate_recovery(verification)

    def test_full_recovery_without_re_engagement_plan(self):
        verification = _valid_verification()
        del verification["re_engagement_plan"]
        validate_recovery(verification)

    def test_full_recovery_minimal(self):
        verification = {
            "schema_version": "1.0.0",
            "halt_event_id": "halt-001",
            "halt_source": "kill_switch",
            "root_cause_analysis": {
                "identified": True,
                "analysis_summary": "Identified and fixed.",
            },
            "evidence": {
                "evidence_refs": ["ref-001"],
            },
            "operator_approval": {
                "approved": True,
                "approver_id": "operator-001",
            },
            "receipt": {
                "receipt_hash": "abc123",
            },
        }
        validate_recovery(verification)


class TestEdgeCases:
    def test_fix_applied_false_ignores_fix_description(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Identified; no fix needed.",
                "fix_applied": False,
                "fix_description": "",
            }
        )
        validate_root_cause(verification)

    def test_fix_applied_false_with_description_ok(self):
        verification = _valid_verification(
            root_cause_analysis={
                "identified": True,
                "analysis_summary": "Identified.",
                "fix_applied": False,
                "fix_description": "Not needed.",
            }
        )
        validate_root_cause(verification)

    def test_approver_id_whitespace_only_fails(self):
        verification = _valid_verification(
            operator_approval={
                "approved": True,
                "approver_id": "   ",
            }
        )
        with pytest.raises(ValueError, match="approver_id"):
            validate_recovery_operator_approval(verification)

    def test_all_halt_sources_valid(self):
        for source in [
            "kill_switch",
            "circuit_breaker",
            "manual",
            "kernel_panic",
            "external",
        ]:
            verification = _valid_verification(halt_source=source)
            validate_recovery(verification)
