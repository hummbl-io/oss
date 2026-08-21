"""Tests for the Rollback primitive (P28) — enforces K9 (REVERSIBILITY)."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.rollback import (
    Reversibility,
    validate_rollback,
    validate_reversibility,
    validate_rollback_declaration,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_reversible(**overrides):
    """Build a valid reversible rollback declaration with optional overrides."""
    base = {
        "schema_version": "1.0.0",
        "action_id": "act-001",
        "reversibility": "reversible",
        "rollback_plan": {
            "rollback_steps": [
                {
                    "step_id": "step-1",
                    "description": "Restore database from snapshot",
                    "estimated_duration_minutes": 15,
                    "data_loss": False,
                }
            ],
            "checkpoint_ref": "ckpt-001",
        },
        "authority": {
            "declared_by": "operator-001",
        },
        "receipt": {
            "receipt_hash": "abc123",
        },
    }
    base.update(overrides)
    return base


def _valid_irreversible(**overrides):
    """Build a valid irreversible rollback declaration with optional overrides."""
    base = {
        "schema_version": "1.0.0",
        "action_id": "act-002",
        "reversibility": "irreversible",
        "irreversibility_acceptance": {
            "risk_description": "Permanent deletion of user records",
            "risk_severity": "high",
            "mitigation_refs": ["mit-001"],
            "acceptor_id": "operator-001",
        },
        "authority": {
            "declared_by": "operator-001",
        },
        "receipt": {
            "receipt_hash": "def456",
        },
    }
    base.update(overrides)
    return base


class TestSchemaValidation:
    def test_valid_reversible_passes(self):
        declaration = _valid_reversible()
        validate_rollback(declaration)

    def test_valid_irreversible_passes(self):
        declaration = _valid_irreversible()
        validate_rollback(declaration)

    def test_missing_required_field_fails(self):
        declaration = _valid_reversible()
        del declaration["authority"]
        with pytest.raises(ValidationError):
            validate_rollback(declaration)

    def test_missing_action_id_fails(self):
        declaration = _valid_reversible()
        del declaration["action_id"]
        with pytest.raises(ValidationError):
            validate_rollback(declaration)

    def test_invalid_reversibility_enum_fails(self):
        declaration = _valid_reversible(reversibility="unknown")
        with pytest.raises(ValidationError):
            validate_rollback(declaration)

    def test_invalid_schema_version_fails(self):
        declaration = _valid_reversible(schema_version="not-a-version")
        with pytest.raises(ValidationError):
            validate_rollback(declaration)


class TestReversibilityReversible:
    def test_reversible_with_plan_ok(self):
        declaration = _valid_reversible()
        validate_reversibility(declaration)

    def test_reversible_missing_plan_fails(self):
        declaration = _valid_reversible()
        del declaration["rollback_plan"]
        with pytest.raises(ValueError, match="rollback_plan required"):
            validate_reversibility(declaration)

    def test_reversible_empty_steps_fails(self):
        declaration = _valid_reversible(
            rollback_plan={"rollback_steps": [], "checkpoint_ref": "ckpt-001"}
        )
        with pytest.raises(ValueError, match="at least one rollback_step"):
            validate_reversibility(declaration)

    def test_reversible_missing_steps_fails(self):
        declaration = _valid_reversible(
            rollback_plan={"checkpoint_ref": "ckpt-001"}
        )
        with pytest.raises(ValueError, match="at least one rollback_step"):
            validate_reversibility(declaration)


class TestReversibilityPartiallyReversible:
    def test_partially_reversible_with_plan_ok(self):
        declaration = _valid_reversible(
            reversibility="partially_reversible",
            rollback_plan={
                "rollback_steps": [
                    {"step_id": "step-1", "description": "Restore config"}
                ],
                "partial_rollback_scope": ["config"],
            },
        )
        validate_reversibility(declaration)

    def test_partially_reversible_missing_plan_fails(self):
        declaration = _valid_reversible(reversibility="partially_reversible")
        del declaration["rollback_plan"]
        with pytest.raises(ValueError, match="rollback_plan required"):
            validate_reversibility(declaration)

    def test_partially_reversible_empty_steps_fails(self):
        declaration = _valid_reversible(
            reversibility="partially_reversible",
            rollback_plan={"rollback_steps": []},
        )
        with pytest.raises(ValueError, match="at least one rollback_step"):
            validate_reversibility(declaration)


class TestReversibilityIrreversible:
    def test_irreversible_with_acceptance_ok(self):
        declaration = _valid_irreversible()
        validate_reversibility(declaration)

    def test_irreversible_missing_acceptance_fails(self):
        declaration = _valid_irreversible()
        del declaration["irreversibility_acceptance"]
        with pytest.raises(ValueError, match="irreversibility_acceptance required"):
            validate_reversibility(declaration)

    def test_irreversible_missing_risk_description_fails(self):
        declaration = _valid_irreversible(
            irreversibility_acceptance={
                "risk_severity": "high",
                "acceptor_id": "operator-001",
            }
        )
        with pytest.raises(ValueError, match="risk_description"):
            validate_reversibility(declaration)

    def test_irreversible_missing_acceptor_id_fails(self):
        declaration = _valid_irreversible(
            irreversibility_acceptance={
                "risk_description": "Permanent deletion",
                "risk_severity": "high",
            }
        )
        with pytest.raises(ValueError, match="acceptor_id"):
            validate_reversibility(declaration)

    def test_irreversible_empty_acceptor_id_fails(self):
        declaration = _valid_irreversible(
            irreversibility_acceptance={
                "risk_description": "Permanent deletion",
                "risk_severity": "high",
                "acceptor_id": "",
            }
        )
        with pytest.raises(ValueError, match="acceptor_id"):
            validate_reversibility(declaration)


class TestFullValidation:
    def test_valid_reversible_full_ok(self):
        declaration = _valid_reversible()
        validate_rollback_declaration(declaration)

    def test_valid_irreversible_full_ok(self):
        declaration = _valid_irreversible()
        validate_rollback_declaration(declaration)

    def test_valid_partially_reversible_full_ok(self):
        declaration = _valid_reversible(
            reversibility="partially_reversible",
            rollback_plan={
                "rollback_steps": [
                    {"step_id": "step-1", "description": "Restore config"}
                ],
                "partial_rollback_scope": ["config"],
            },
        )
        validate_rollback_declaration(declaration)

    def test_full_reversible_missing_plan_fails(self):
        declaration = _valid_reversible()
        del declaration["rollback_plan"]
        with pytest.raises(ValueError, match="rollback_plan required"):
            validate_rollback_declaration(declaration)

    def test_full_irreversible_missing_acceptance_fails(self):
        declaration = _valid_irreversible()
        del declaration["irreversibility_acceptance"]
        with pytest.raises(ValueError, match="irreversibility_acceptance required"):
            validate_rollback_declaration(declaration)

    def test_full_schema_failure(self):
        declaration = _valid_reversible()
        del declaration["receipt"]
        with pytest.raises(ValidationError):
            validate_rollback_declaration(declaration)


class TestEdgeCases:
    def test_empty_steps_list_rejected(self):
        declaration = _valid_reversible(
            rollback_plan={"rollback_steps": []}
        )
        with pytest.raises(ValueError, match="at least one rollback_step"):
            validate_reversibility(declaration)

    def test_missing_acceptor_id_rejected(self):
        declaration = _valid_irreversible(
            irreversibility_acceptance={
                "risk_description": "Permanent deletion",
                "risk_severity": "high",
            }
        )
        with pytest.raises(ValueError, match="acceptor_id"):
            validate_reversibility(declaration)

    def test_empty_risk_description_rejected(self):
        declaration = _valid_irreversible(
            irreversibility_acceptance={
                "risk_description": "",
                "risk_severity": "high",
                "acceptor_id": "operator-001",
            }
        )
        with pytest.raises(ValueError, match="risk_description"):
            validate_reversibility(declaration)

    def test_rollback_plan_not_dict_rejected(self):
        declaration = _valid_reversible(rollback_plan="not-a-dict")
        with pytest.raises(ValueError, match="rollback_plan required"):
            validate_reversibility(declaration)

    def test_acceptance_not_dict_rejected(self):
        declaration = _valid_irreversible(irreversibility_acceptance="not-a-dict")
        with pytest.raises(ValueError, match="irreversibility_acceptance required"):
            validate_reversibility(declaration)


class TestReversibilityEnum:
    def test_enum_values(self):
        assert Reversibility.REVERSIBLE.value == "reversible"
        assert Reversibility.PARTIALLY_REVERSIBLE.value == "partially_reversible"
        assert Reversibility.IRREVERSIBLE.value == "irreversible"
