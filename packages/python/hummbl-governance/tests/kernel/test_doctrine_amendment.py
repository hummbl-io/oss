"""Tests for the Doctrine Amendment primitive (P38) — enforces D7."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.doctrine_amendment import (
    AmendmentType,
    AmendmentStatus,
    validate_doctrine_amendment,
    validate_operator_approval,
    validate_amendment_evidence,
    validate_review_consistency,
    validate_amendment,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_amendment(status="proposed"):
    """Build a valid doctrine amendment record."""
    amendment = {
        "schema_version": "1.0.0",
        "amendment_id": "am-001",
        "target_invariant": "K9",
        "amendment_type": "modify",
        "change_description": "Expand K9 scope to include read-only state mutations",
        "proposed_text": "Every governed state mutation declares a rollback path...",
        "impact_analysis": {
            "affected_primitives": ["rollback"],
            "breaking_change": False,
            "migration_plan": "Update rollback schema to include read-only flag",
        },
        "amendment_status": status,
        "authority": {
            "operator_approval": True,
            "approver_id": "operator-001",
        },
        "evidence": {
            "evidence_refs": ["incident-001", "audit-001"],
            "rationale": "K9 scope was too narrow for read-only mutations",
        },
        "receipt": {"receipt_hash": "am-hash-001"},
    }
    if status in ("approved", "rejected", "ratified"):
        amendment["review"] = {
            "reviewer_id": "operator-001",
            "review_outcome": "approved" if status in ("approved", "ratified") else "rejected",
            "review_notes": "Reviewed and approved",
        }
    return amendment


class TestSchemaValidation:
    def test_valid_proposed_passes(self):
        validate_doctrine_amendment(_valid_amendment("proposed"))

    def test_valid_ratified_with_review_passes(self):
        validate_doctrine_amendment(_valid_amendment("ratified"))

    def test_missing_required_field_fails(self):
        with pytest.raises(ValidationError):
            validate_doctrine_amendment({"schema_version": "1.0.0"})

    def test_invalid_target_invariant_fails(self):
        a = _valid_amendment()
        a["target_invariant"] = "K99"
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_invalid_amendment_type_fails(self):
        a = _valid_amendment()
        a["amendment_type"] = "invalid"
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_invalid_status_fails(self):
        a = _valid_amendment()
        a["amendment_status"] = "invalid"
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_empty_change_description_fails(self):
        a = _valid_amendment()
        a["change_description"] = ""
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_empty_evidence_refs_fails(self):
        a = _valid_amendment()
        a["evidence"]["evidence_refs"] = []
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_additional_properties_rejected(self):
        a = _valid_amendment()
        a["extra_field"] = "not allowed"
        with pytest.raises(ValidationError):
            validate_doctrine_amendment(a)

    def test_all_k_invariants_valid_targets(self):
        for k in ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11"]:
            a = _valid_amendment()
            a["amendment_id"] = f"am-{k}"
            a["target_invariant"] = k
            validate_doctrine_amendment(a)

    def test_all_d_invariants_valid_targets(self):
        for d in ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]:
            a = _valid_amendment()
            a["amendment_id"] = f"am-{d}"
            a["target_invariant"] = d
            validate_doctrine_amendment(a)


class TestOperatorApproval:
    """D7 requires operator approval for any invariant change."""

    def test_valid_approval_passes(self):
        validate_operator_approval(_valid_amendment())

    def test_no_approval_fails(self):
        """Ungated amendments are blocked — core D7 enforcement."""
        a = _valid_amendment()
        a["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval must be True"):
            validate_operator_approval(a)

    def test_missing_approver_id_fails(self):
        a = _valid_amendment()
        a["authority"]["approver_id"] = ""
        with pytest.raises(ValueError, match="approver_id"):
            validate_operator_approval(a)

    def test_whitespace_approver_id_fails(self):
        a = _valid_amendment()
        a["authority"]["approver_id"] = "   "
        with pytest.raises(ValueError, match="approver_id"):
            validate_operator_approval(a)

    def test_missing_authority_fails(self):
        a = _valid_amendment()
        a["authority"] = None
        with pytest.raises(ValueError, match="authority"):
            validate_operator_approval(a)


class TestAmendmentEvidence:
    def test_valid_evidence_passes(self):
        validate_amendment_evidence(_valid_amendment())

    def test_empty_evidence_refs_fails(self):
        a = _valid_amendment()
        a["evidence"]["evidence_refs"] = []
        with pytest.raises(ValueError, match="evidence_refs"):
            validate_amendment_evidence(a)

    def test_missing_evidence_fails(self):
        a = _valid_amendment()
        a["evidence"] = None
        with pytest.raises(ValueError, match="evidence"):
            validate_amendment_evidence(a)


class TestReviewConsistency:
    def test_proposed_without_review_ok(self):
        validate_review_consistency(_valid_amendment("proposed"))

    def test_under_review_without_review_ok(self):
        validate_review_consistency(_valid_amendment("under_review"))

    def test_approved_without_review_fails(self):
        a = _valid_amendment("approved")
        del a["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_review_consistency(a)

    def test_rejected_without_review_fails(self):
        a = _valid_amendment("rejected")
        del a["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_review_consistency(a)

    def test_ratified_without_review_fails(self):
        a = _valid_amendment("ratified")
        del a["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_review_consistency(a)

    def test_approved_with_empty_reviewer_id_fails(self):
        a = _valid_amendment("approved")
        a["review"]["reviewer_id"] = ""
        with pytest.raises(ValueError, match="reviewer_id"):
            validate_review_consistency(a)

    def test_withdrawn_without_review_ok(self):
        validate_review_consistency(_valid_amendment("withdrawn"))


class TestFullValidation:
    def test_valid_proposed_passes(self):
        validate_amendment(_valid_amendment("proposed"))

    def test_valid_ratified_with_review_passes(self):
        validate_amendment(_valid_amendment("ratified"))

    def test_no_operator_approval_fails(self):
        """D7 blocks ungated amendments — full validation must catch this."""
        a = _valid_amendment()
        a["authority"]["operator_approval"] = False
        with pytest.raises(ValueError, match="operator_approval must be True"):
            validate_amendment(a)

    def test_missing_evidence_fails(self):
        a = _valid_amendment()
        a["evidence"]["evidence_refs"] = []
        # Schema validation catches minItems:1 before semantic validation
        with pytest.raises(ValidationError, match="evidence_refs"):
            validate_amendment(a)

    def test_approved_without_review_fails(self):
        a = _valid_amendment("approved")
        del a["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_amendment(a)

    def test_schema_failure_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_amendment({"schema_version": "1.0.0"})


class TestAmendmentTypeEnum:
    def test_enum_values(self):
        assert AmendmentType.ADD.value == "add"
        assert AmendmentType.MODIFY.value == "modify"
        assert AmendmentType.REMOVE.value == "remove"
        assert AmendmentType.SUPERSEDE.value == "supersede"

    def test_enum_count(self):
        assert len(list(AmendmentType)) == 4


class TestAmendmentStatusEnum:
    def test_enum_values(self):
        assert AmendmentStatus.PROPOSED.value == "proposed"
        assert AmendmentStatus.UNDER_REVIEW.value == "under_review"
        assert AmendmentStatus.APPROVED.value == "approved"
        assert AmendmentStatus.REJECTED.value == "rejected"
        assert AmendmentStatus.RATIFIED.value == "ratified"
        assert AmendmentStatus.WITHDRAWN.value == "withdrawn"

    def test_enum_count(self):
        assert len(list(AmendmentStatus)) == 6
