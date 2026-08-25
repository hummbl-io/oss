"""Tests for the Canon Registry primitive (P27)."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.canon_registry import (
    CanonLevel,
    validate_canon_registry,
    validate_transition,
    validate_operator_approval,
    validate_review_required,
    validate_promotion,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_proposal(**overrides):
    """Build a valid canon-registry proposal with optional overrides."""
    base = {
        "schema_version": "1.0.0",
        "artifact_id": "art-001",
        "artifact_type": "research_artifact",
        "current_canon_level": "draft",
        "proposed_canon_level": "reviewed",
        "authority": {
            "operator_approval": True,
            "approver_id": "operator-001",
        },
        "evidence": {
            "evidence_refs": ["ref-001"],
        },
        "receipt": {
            "receipt_hash": "abc123",
        },
    }
    base.update(overrides)
    return base


class TestSchemaValidation:
    def test_valid_proposal_passes(self):
        proposal = _valid_proposal()
        validate_canon_registry(proposal)

    def test_missing_required_field_fails(self):
        proposal = _valid_proposal()
        del proposal["authority"]
        with pytest.raises(ValidationError):
            validate_canon_registry(proposal)

    def test_invalid_artifact_type_fails(self):
        proposal = _valid_proposal(artifact_type="unknown_type")
        with pytest.raises(ValidationError):
            validate_canon_registry(proposal)

    def test_invalid_canon_level_fails(self):
        proposal = _valid_proposal(current_canon_level="invalid")
        with pytest.raises(ValidationError):
            validate_canon_registry(proposal)


class TestTransitionValidation:
    def test_draft_to_reviewed_ok(self):
        validate_transition("draft", "reviewed")

    def test_reviewed_to_validated_ok(self):
        validate_transition("reviewed", "validated")

    def test_validated_to_adopted_ok(self):
        validate_transition("validated", "adopted")

    def test_adopted_to_canonical_ok(self):
        validate_transition("adopted", "canonical")

    def test_any_to_deprecated_ok(self):
        for level in ["draft", "reviewed", "validated", "adopted", "canonical"]:
            validate_transition(level, "deprecated")

    def test_skip_level_fails(self):
        with pytest.raises(ValueError, match="expected 'draft' -> 'reviewed'"):
            validate_transition("draft", "validated")

    def test_backward_fails(self):
        with pytest.raises(ValueError, match="expected 'reviewed' -> 'validated'"):
            validate_transition("reviewed", "draft")

    def test_same_level_fails(self):
        with pytest.raises(ValueError, match="both 'draft'"):
            validate_transition("draft", "draft")

    def test_canonical_no_forward_fails(self):
        with pytest.raises(ValueError, match="no forward transition"):
            validate_transition("canonical", "adopted")


class TestOperatorApproval:
    def test_approved_ok(self):
        proposal = _valid_proposal()
        validate_operator_approval(proposal)

    def test_not_approved_fails(self):
        proposal = _valid_proposal(
            authority={"operator_approval": False, "approver_id": "op-001"}
        )
        with pytest.raises(ValueError, match="D5.*NO_AUTO_PROMOTION"):
            validate_operator_approval(proposal)

    def test_missing_approver_id_fails(self):
        proposal = _valid_proposal(
            authority={"operator_approval": True, "approver_id": ""}
        )
        with pytest.raises(ValueError, match="approver_id"):
            validate_operator_approval(proposal)

    def test_missing_authority_fails(self):
        proposal = _valid_proposal()
        del proposal["authority"]
        with pytest.raises(ValueError, match="D5.*NO_AUTO_PROMOTION"):
            validate_operator_approval(proposal)


class TestReviewRequired:
    def test_review_not_required_for_draft(self):
        proposal = _valid_proposal(current_canon_level="draft")
        validate_review_required(proposal)

    def test_review_required_for_reviewed_to_validated(self):
        proposal = _valid_proposal(
            current_canon_level="reviewed",
            proposed_canon_level="validated",
        )
        with pytest.raises(ValueError, match="review gate required"):
            validate_review_required(proposal)

    def test_review_pass_ok(self):
        proposal = _valid_proposal(
            current_canon_level="reviewed",
            proposed_canon_level="validated",
            review={
                "reviewer_ids": ["reviewer-001"],
                "review_verdict": "pass",
            },
        )
        validate_review_required(proposal)

    def test_review_fail_rejected(self):
        proposal = _valid_proposal(
            current_canon_level="reviewed",
            proposed_canon_level="validated",
            review={
                "reviewer_ids": ["reviewer-001"],
                "review_verdict": "fail",
            },
        )
        with pytest.raises(ValueError, match="review_verdict is 'fail'"):
            validate_review_required(proposal)

    def test_review_no_reviewers_rejected(self):
        proposal = _valid_proposal(
            current_canon_level="reviewed",
            proposed_canon_level="validated",
            review={
                "reviewer_ids": [],
                "review_verdict": "pass",
            },
        )
        with pytest.raises(ValueError, match="at least one reviewer_id"):
            validate_review_required(proposal)


class TestFullPromotion:
    def test_valid_full_promotion(self):
        proposal = _valid_proposal()
        validate_promotion(proposal)

    def test_full_promotion_with_review(self):
        proposal = _valid_proposal(
            current_canon_level="reviewed",
            proposed_canon_level="validated",
            review={
                "reviewer_ids": ["reviewer-001"],
                "review_verdict": "pass",
            },
        )
        validate_promotion(proposal)

    def test_full_promotion_deprecation(self):
        proposal = _valid_proposal(
            current_canon_level="canonical",
            proposed_canon_level="deprecated",
        )
        validate_promotion(proposal)

    def test_full_promotion_d5_violation(self):
        proposal = _valid_proposal(
            authority={"operator_approval": False, "approver_id": "op-001"}
        )
        with pytest.raises(ValueError, match="D5"):
            validate_promotion(proposal)

    def test_full_promotion_skip_level(self):
        proposal = _valid_proposal(
            current_canon_level="draft",
            proposed_canon_level="validated",
        )
        with pytest.raises(ValueError, match="expected 'draft' -> 'reviewed'"):
            validate_promotion(proposal)


class TestCanonLevel:
    def test_enum_values(self):
        assert CanonLevel.DRAFT.value == "draft"
        assert CanonLevel.REVIEWED.value == "reviewed"
        assert CanonLevel.VALIDATED.value == "validated"
        assert CanonLevel.ADOPTED.value == "adopted"
        assert CanonLevel.CANONICAL.value == "canonical"
        assert CanonLevel.DEPRECATED.value == "deprecated"
