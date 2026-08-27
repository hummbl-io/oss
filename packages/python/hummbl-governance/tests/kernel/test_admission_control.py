"""Tests for admission_control primitive — bounded promotion from candidate 004."""

import json
from pathlib import Path

import pytest
from hummbl_governance.kernel.admission_control import (
    validate_admission,
    validate_admission_control,
    validate_gateway_emitted_fields,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_proposal() -> dict:
    """Minimal valid admission-control proposal with all 3 novel fields."""
    return {
        "schema_version": "1.0.0",
        "authority": {
            "owner_instruction_present": True,
            "authority_scope": "repo:hummbl-governance",
            "review_required": False,
        },
        "executor": {
            "actor_id": "claude-code",
            "executor_id": "claude-code",
        },
        "scope": {
            "reversibility": "reversible",
            "target_paths": ["hummbl_governance/services/"],
        },
        "evidence": {
            "evidence_refs": ["git:f7f81c31", "bus:BUS-CANON-001"],
        },
        "receipt": {
            "receipt_hash": "sha256:abc123",
            "receipt_sequence": 1,
        },
        "cost_latency": {
            "max_runtime_minutes": 30,
            "max_model_escalations": 2,
            "preferred_model_lane": "T1-BYOK",
        },
        "data_sensitivity": {
            "classification": "internal",
            "secrets_allowed": False,
            "pii_allowed": False,
            "doctrine": False,
        },
        "context_freshness": {
            "source_of_record": ["git:main"],
            "freshness_required": True,
        },
    }


class TestSchemaValidation:
    def test_valid_proposal_passes(self):
        proposal = _valid_proposal()
        validate_admission_control(proposal)  # should not raise

    def test_missing_required_field_fails(self):
        proposal = _valid_proposal()
        del proposal["authority"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_missing_schema_version_fails(self):
        proposal = _valid_proposal()
        del proposal["schema_version"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_invalid_schema_version_pattern(self):
        proposal = _valid_proposal()
        proposal["schema_version"] = "v1"  # not semver
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_additional_properties_rejected(self):
        proposal = _valid_proposal()
        proposal["unknown_field"] = "value"
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)


class TestCostLatencyField:
    def test_valid_cost_latency(self):
        proposal = _valid_proposal()
        proposal["cost_latency"] = {
            "max_runtime_minutes": 60,
            "max_model_escalations": 3,
            "preferred_model_lane": "T2-ZEN",
            "max_cloud_sessions": 1,
            "escalation_allowed": ["T3-FREE"],
        }
        validate_admission_control(proposal)

    def test_invalid_model_lane_rejected(self):
        proposal = _valid_proposal()
        proposal["cost_latency"]["preferred_model_lane"] = "T4-INVALID"
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_missing_required_cost_latency_field(self):
        proposal = _valid_proposal()
        del proposal["cost_latency"]["max_model_escalations"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_negative_runtime_rejected(self):
        proposal = _valid_proposal()
        proposal["cost_latency"]["max_runtime_minutes"] = 0
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)


class TestDataSensitivityField:
    def test_valid_data_sensitivity(self):
        proposal = _valid_proposal()
        proposal["data_sensitivity"] = {
            "classification": "restricted",
            "secrets_allowed": False,
            "pii_allowed": True,
            "allowed_surfaces": ["protected", "operating"],
            "allowed_model_tiers": ["T1-BYOK"],
            "doctrine": True,
        }
        validate_admission_control(proposal)

    def test_invalid_classification_rejected(self):
        proposal = _valid_proposal()
        proposal["data_sensitivity"]["classification"] = "top_secret"
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_doctrine_flag_routes_cross_check(self):
        proposal = _valid_proposal()
        proposal["data_sensitivity"]["doctrine"] = True
        validate_admission_control(proposal)  # schema allows it


class TestContextFreshnessField:
    def test_valid_proposer_emitted_only(self):
        proposal = _valid_proposal()
        proposal["context_freshness"] = {
            "source_of_record": ["git:main", "receipt:abc123"],
            "freshness_required": True,
        }
        validate_admission_control(proposal)

    def test_gateway_emitted_fields_allowed_in_schema(self):
        """Schema allows gateway-emitted fields; convention enforced separately."""
        proposal = _valid_proposal()
        proposal["context_freshness"] = {
            "source_of_record": ["git:main"],
            "freshness_required": True,
            "freshness_checked_at": "2026-06-23T12:00:00Z",
            "stale_sources": [],
        }
        validate_admission_control(proposal)  # schema-valid


class TestGatewayEmittedConvention:
    def test_clean_proposal_no_violations(self):
        proposal = _valid_proposal()
        assert validate_gateway_emitted_fields(proposal, is_proposer=True) == []

    def test_proposer_supplying_gateway_field_flagged(self):
        proposal = _valid_proposal()
        proposal["context_freshness"]["freshness_checked_at"] = "2026-06-23T12:00:00Z"
        violations = validate_gateway_emitted_fields(proposal, is_proposer=True)
        assert len(violations) == 1
        assert "freshness_checked_at" in violations[0]

    def test_gateway_setting_field_not_flagged(self):
        proposal = _valid_proposal()
        proposal["context_freshness"]["freshness_checked_at"] = "2026-06-23T12:00:00Z"
        # is_proposer=False → gateway-supplied → OK
        violations = validate_gateway_emitted_fields(proposal, is_proposer=False)
        assert violations == []


class TestFullAdmissionValidation:
    def test_valid_admission_passes(self):
        proposal = _valid_proposal()
        validate_admission(proposal)  # should not raise

    def test_proposer_violation_raises_value_error(self):
        proposal = _valid_proposal()
        proposal["context_freshness"]["stale_sources"] = ["git:old-ref"]
        with pytest.raises(ValueError, match="GATEWAY-EMITTED"):
            validate_admission(proposal, is_proposer=True)


class TestInvariant:
    """Admission is not truth; admission is governed permission."""

    def test_admission_without_receipt_fails(self):
        """No receipt = no proof of admission = rejected."""
        proposal = _valid_proposal()
        del proposal["receipt"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_admission_without_authority_fails(self):
        """No authority = no governed permission = rejected."""
        proposal = _valid_proposal()
        del proposal["authority"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)

    def test_admission_without_scope_fails(self):
        """No scope = unbounded transition = rejected."""
        proposal = _valid_proposal()
        del proposal["scope"]
        with pytest.raises(ValidationError):
            validate_admission_control(proposal)


SCHEMA_PATH = Path(__file__).parent.parent.parent / "hummbl_governance" / "data" / "admission_control.schema.json"


class TestSchemaFile:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists()

    def test_schema_file_is_valid_json(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        assert schema["title"] == "Admission Control Primitive v1"
        assert "$id" in schema
        assert "cost_latency" in schema["properties"]
        assert "data_sensitivity" in schema["properties"]
        assert "context_freshness" in schema["properties"]
