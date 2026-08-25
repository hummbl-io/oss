"""Tests for the Contestability primitive (P31) — enforces D6."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.contestability import (
    ContestStatus,
    ReviewOutcome,
    validate_contestability,
    validate_contest_evidence,
    validate_review_consistency,
    validate_contest,
)
from hummbl_governance.schema_validator import ValidationError


def _valid_contest(status="flagged"):
    """Build a valid contestability record."""
    contest = {
        "schema_version": "1.0.0",
        "contest_id": "ct-001",
        "decision_id": "dec-001",
        "contest_reason": "Decision made without considering affected party's input",
        "contest_evidence": {
            "evidence_refs": ["log-001", "output-001"],
            "affected_party_id": "user-001",
            "impact_description": "User was not notified of automated decision",
        },
        "contest_status": status,
        "authority": {
            "flagged_by": "user-001",
        },
        "receipt": {"receipt_hash": "ct-hash-001"},
    }
    if status in ("upheld", "overturned"):
        contest["review"] = {
            "reviewer_id": "operator-001",
            "review_outcome": "upheld" if status == "upheld" else "overturned",
            "review_notes": "Reviewed and found decision was correct",
        }
    return contest


class TestSchemaValidation:
    def test_valid_flagged_passes(self):
        validate_contestability(_valid_contest("flagged"))

    def test_valid_upheld_with_review_passes(self):
        validate_contestability(_valid_contest("upheld"))

    def test_valid_overturned_with_review_passes(self):
        validate_contestability(_valid_contest("overturned"))

    def test_missing_required_field_fails(self):
        with pytest.raises(ValidationError):
            validate_contestability({"schema_version": "1.0.0"})

    def test_invalid_contest_status_fails(self):
        c = _valid_contest()
        c["contest_status"] = "invalid"
        with pytest.raises(ValidationError):
            validate_contestability(c)

    def test_empty_contest_reason_fails(self):
        c = _valid_contest()
        c["contest_reason"] = ""
        with pytest.raises(ValidationError):
            validate_contestability(c)

    def test_empty_evidence_refs_fails(self):
        c = _valid_contest()
        c["contest_evidence"]["evidence_refs"] = []
        with pytest.raises(ValidationError):
            validate_contestability(c)

    def test_additional_properties_rejected(self):
        c = _valid_contest()
        c["extra_field"] = "not allowed"
        with pytest.raises(ValidationError):
            validate_contestability(c)


class TestContestEvidence:
    """D6 requires evidence or justification, not a bare flag."""

    def test_valid_evidence_passes(self):
        validate_contest_evidence(_valid_contest())

    def test_empty_reason_fails(self):
        c = _valid_contest()
        c["contest_reason"] = "   "
        with pytest.raises(ValueError, match="contest_reason"):
            validate_contest_evidence(c)

    def test_missing_evidence_refs_fails(self):
        c = _valid_contest()
        c["contest_evidence"]["evidence_refs"] = []
        with pytest.raises(ValueError, match="evidence_refs"):
            validate_contest_evidence(c)

    def test_none_reason_fails(self):
        c = _valid_contest()
        c["contest_reason"] = None
        with pytest.raises(ValueError):
            validate_contest_evidence(c)


class TestReviewConsistency:
    def test_flagged_without_review_ok(self):
        validate_review_consistency(_valid_contest("flagged"))

    def test_under_review_without_review_ok(self):
        validate_review_consistency(_valid_contest("under_review"))

    def test_upheld_without_review_fails(self):
        c = _valid_contest("upheld")
        del c["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_review_consistency(c)

    def test_overturned_without_review_fails(self):
        c = _valid_contest("overturned")
        del c["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_review_consistency(c)

    def test_upheld_with_empty_reviewer_id_fails(self):
        c = _valid_contest("upheld")
        c["review"]["reviewer_id"] = ""
        with pytest.raises(ValueError, match="reviewer_id"):
            validate_review_consistency(c)

    def test_withdrawn_without_review_ok(self):
        validate_review_consistency(_valid_contest("withdrawn"))


class TestFullValidation:
    def test_valid_flagged_passes(self):
        validate_contest(_valid_contest("flagged"))

    def test_valid_upheld_with_review_passes(self):
        validate_contest(_valid_contest("upheld"))

    def test_missing_evidence_fails(self):
        c = _valid_contest()
        c["contest_evidence"]["evidence_refs"] = []
        # Schema validation catches minItems:1 before semantic validation
        with pytest.raises(ValidationError, match="evidence_refs"):
            validate_contest(c)

    def test_upheld_without_review_fails(self):
        c = _valid_contest("upheld")
        del c["review"]
        with pytest.raises(ValueError, match="review record"):
            validate_contest(c)

    def test_schema_failure_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_contest({"schema_version": "1.0.0"})


class TestContestStatusEnum:
    def test_enum_values(self):
        assert ContestStatus.FLAGGED.value == "flagged"
        assert ContestStatus.UNDER_REVIEW.value == "under_review"
        assert ContestStatus.UPHELD.value == "upheld"
        assert ContestStatus.OVERTURNED.value == "overturned"
        assert ContestStatus.WITHDRAWN.value == "withdrawn"

    def test_enum_count(self):
        assert len(list(ContestStatus)) == 5


class TestReviewOutcomeEnum:
    def test_enum_values(self):
        assert ReviewOutcome.UPHELD.value == "upheld"
        assert ReviewOutcome.OVERTURNED.value == "overturned"
        assert ReviewOutcome.MODIFIED.value == "modified"
        assert ReviewOutcome.ESCALATED.value == "escalated"

    def test_enum_count(self):
        assert len(list(ReviewOutcome)) == 4
