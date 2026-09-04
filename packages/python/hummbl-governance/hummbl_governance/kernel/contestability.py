"""Contestability Primitive — enforces D6 (CONTESTABILITY).

Allows affected parties to flag an AI decision for human review, suspending
the decision's effects until review completes. Enforces D6: affected parties
can flag AI decisions for human review. Requires evidence or justification
for the contest, not just a bare flag.

D6 scoping (operator constraint 2026-06-26): requires evidence or
justification for the contest, not just a bare flag.

Schema: hummbl_governance/data/contestability.schema.json
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "contestability.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


class ContestStatus(str, Enum):
    """Status of a contestation."""

    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    OVERTURNED = "overturned"
    WITHDRAWN = "withdrawn"


class ReviewOutcome(str, Enum):
    """Outcome of a human review."""

    UPHELD = "upheld"
    OVERTURNED = "overturned"
    MODIFIED = "modified"
    ESCALATED = "escalated"


# Statuses that require a review record
_REVIEW_REQUIRED = {ContestStatus.UPHELD.value, ContestStatus.OVERTURNED.value}


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_contestability(contest: dict[str, Any]) -> None:
    """Validate a contestability record against schema v1.0.0.

    Raises:
        ValidationError: If the record does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(contest, schema)
    if errors:
        raise ValidationError(
            f"Contestability schema validation failed: {'; '.join(errors)}"
        )


def validate_contest_evidence(contest: dict[str, Any]) -> None:
    """Enforce D6 (CONTESTABILITY) evidence gate.

    D6 requires evidence or justification for the contest, not just a
    bare flag. The contest_reason must be non-empty (enforced by schema)
    and contest_evidence.evidence_refs must have at least one entry
    (enforced by schema). This function performs additional semantic
    validation beyond the schema.

    Args:
        contest: The contestability record dict.

    Raises:
        ValueError: If the evidence gate is not satisfied.
    """
    reason = contest.get("contest_reason", "")
    if not reason or not isinstance(reason, str) or not reason.strip():
        raise ValueError(
            "Contest rejected: D6 (CONTESTABILITY) violation — "
            "contest_reason must be a non-empty string with substantive justification"
        )

    evidence = contest.get("contest_evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError(
            "Contest rejected: contest_evidence must be present and valid"
        )

    evidence_refs = evidence.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or len(evidence_refs) == 0:
        raise ValueError(
            "Contest rejected: D6 (CONTESTABILITY) violation — "
            "contest_evidence.evidence_refs must have at least one entry"
        )


def validate_review_consistency(contest: dict[str, Any]) -> None:
    """Validate that review record is present when required.

    If contest_status is 'upheld' or 'overturned', a review record must
    be present with reviewer_id and review_outcome.

    Args:
        contest: The contestability record dict.

    Raises:
        ValueError: If review is required but missing or incomplete.
    """
    status = contest.get("contest_status", "")

    if status in _REVIEW_REQUIRED:
        review = contest.get("review")
        if not isinstance(review, dict):
            raise ValueError(
                f"Contest rejected: contest_status='{status}' requires a "
                f"review record with reviewer_id and review_outcome"
            )

        reviewer_id = review.get("reviewer_id", "")
        if not reviewer_id or not isinstance(reviewer_id, str):
            raise ValueError(
                "Contest rejected: review.reviewer_id must be a non-empty string"
            )

        review_outcome = review.get("review_outcome", "")
        if not review_outcome:
            raise ValueError(
                "Contest rejected: review.review_outcome must be present"
            )


def validate_contest(contest: dict[str, Any]) -> None:
    """Full contestability validation: schema + evidence (D6) + review consistency.

    Args:
        contest: The contestability record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If evidence or review consistency validation fails.
    """
    validate_contestability(contest)
    validate_contest_evidence(contest)
    validate_review_consistency(contest)


__all__ = [
    "ContestStatus",
    "ReviewOutcome",
    "validate_contestability",
    "validate_contest_evidence",
    "validate_review_consistency",
    "validate_contest",
]
