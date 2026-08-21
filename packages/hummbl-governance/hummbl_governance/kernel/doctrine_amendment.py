"""Doctrine Amendment Primitive — enforces D7 (DOCTRINE_AMENDMENT).

Governs changes to invariants themselves (K1-K11, D1-D7). No invariant or
doctrine amendment may take effect without operator approval and a recorded
receipt. Ungated amendments are blocked at the promotion gate.

D7 scoping (operator constraint 2026-06-26): no invariant or doctrine
amendment may take effect without operator approval and a recorded receipt.
Ungated amendments are blocked.

Schema: hummbl_governance/data/doctrine_amendment.schema.json
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "doctrine_amendment.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


class AmendmentType(str, Enum):
    """Types of invariant amendments."""

    ADD = "add"
    MODIFY = "modify"
    REMOVE = "remove"
    SUPERSEDE = "supersede"


class AmendmentStatus(str, Enum):
    """Status of an amendment."""

    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RATIFIED = "ratified"
    WITHDRAWN = "withdrawn"


# Statuses that require a review record
_REVIEW_REQUIRED = {
    AmendmentStatus.APPROVED.value,
    AmendmentStatus.REJECTED.value,
    AmendmentStatus.RATIFIED.value,
}

# Valid target invariants
_VALID_TARGETS = {
    "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7",
}


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_doctrine_amendment(amendment: dict[str, Any]) -> None:
    """Validate an amendment record against schema v1.0.0.

    Raises:
        ValidationError: If the record does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(amendment, schema)
    if errors:
        raise ValidationError(
            f"Doctrine amendment schema validation failed: {'; '.join(errors)}"
        )


def validate_operator_approval(amendment: dict[str, Any]) -> None:
    """Enforce D7 (DOCTRINE_AMENDMENT) operator-approval gate.

    D7 requires operator approval for any invariant change. The
    authority.operator_approval must be True and authority.approver_id
    must be a non-empty string.

    Args:
        amendment: The amendment record dict.

    Raises:
        ValueError: If operator approval is not granted or approver_id
            is missing.
    """
    authority = amendment.get("authority", {})
    if not isinstance(authority, dict):
        raise ValueError(
            "Amendment rejected: authority gate missing or invalid"
        )

    if not authority.get("operator_approval", False):
        raise ValueError(
            "Amendment rejected: D7 (DOCTRINE_AMENDMENT) violation — "
            "authority.operator_approval must be True. "
            "Ungated amendments are blocked."
        )

    approver_id = authority.get("approver_id", "")
    if not isinstance(approver_id, str) or not approver_id.strip():
        raise ValueError(
            "Amendment rejected: authority.approver_id must be a "
            "non-empty string"
        )


def validate_amendment_evidence(amendment: dict[str, Any]) -> None:
    """Enforce D7 evidence gate.

    The amendment must have at least one evidence reference supporting
    the change.

    Args:
        amendment: The amendment record dict.

    Raises:
        ValueError: If evidence is missing or insufficient.
    """
    evidence = amendment.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError(
            "Amendment rejected: evidence gate missing or invalid"
        )

    evidence_refs = evidence.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or len(evidence_refs) == 0:
        raise ValueError(
            "Amendment rejected: D7 (DOCTRINE_AMENDMENT) violation — "
            "evidence.evidence_refs must have at least one entry"
        )


def validate_review_consistency(amendment: dict[str, Any]) -> None:
    """Validate that review record is present when required.

    If amendment_status is 'approved', 'rejected', or 'ratified', a
    review record must be present with reviewer_id and review_outcome.

    Args:
        amendment: The amendment record dict.

    Raises:
        ValueError: If review is required but missing or incomplete.
    """
    status = amendment.get("amendment_status", "")

    if status in _REVIEW_REQUIRED:
        review = amendment.get("review")
        if not isinstance(review, dict):
            raise ValueError(
                f"Amendment rejected: amendment_status='{status}' requires "
                f"a review record with reviewer_id and review_outcome"
            )

        reviewer_id = review.get("reviewer_id", "")
        if not reviewer_id or not isinstance(reviewer_id, str):
            raise ValueError(
                "Amendment rejected: review.reviewer_id must be a "
                "non-empty string"
            )

        review_outcome = review.get("review_outcome", "")
        if not review_outcome:
            raise ValueError(
                "Amendment rejected: review.review_outcome must be present"
            )


def validate_amendment(amendment: dict[str, Any]) -> None:
    """Full doctrine amendment validation: schema + operator approval (D7) +
    evidence + review consistency.

    Args:
        amendment: The amendment record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If operator-approval, evidence, or review consistency
            validation fails.
    """
    validate_doctrine_amendment(amendment)
    validate_operator_approval(amendment)
    validate_amendment_evidence(amendment)
    validate_review_consistency(amendment)


__all__ = [
    "AmendmentType",
    "AmendmentStatus",
    "validate_doctrine_amendment",
    "validate_operator_approval",
    "validate_amendment_evidence",
    "validate_review_consistency",
    "validate_amendment",
]
