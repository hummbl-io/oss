"""Canon Registry Primitive — governs promotion from draft to canonical status.

Closes the governance feedback loop: admission -> authority -> execution ->
receipt -> evidence -> PROMOTION. Enforces D5 (NO_AUTO_PROMOTION): no agent
can promote an artifact to canonical status without operator approval.

Canon levels (sequential transitions required):
    draft -> reviewed -> validated -> adopted -> canonical
    Deprecation can occur from any level -> deprecated

Schema: hummbl_governance/data/canon_registry.schema.json
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "canon_registry.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


class CanonLevel(str, Enum):
    """Canon levels in the promotion pipeline."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    ADOPTED = "adopted"
    CANONICAL = "canonical"
    DEPRECATED = "deprecated"


# Valid forward transitions (sequential promotion)
_FORWARD_TRANSITIONS: dict[str, str] = {
    CanonLevel.DRAFT.value: CanonLevel.REVIEWED.value,
    CanonLevel.REVIEWED.value: CanonLevel.VALIDATED.value,
    CanonLevel.VALIDATED.value: CanonLevel.ADOPTED.value,
    CanonLevel.ADOPTED.value: CanonLevel.CANONICAL.value,
}

# Levels that require peer review to advance past
_REVIEW_REQUIRED_FROM = {CanonLevel.REVIEWED.value}


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_canon_registry(proposal: dict[str, Any]) -> None:
    """Validate a canon-registry promotion proposal against schema v1.0.0.

    Raises:
        ValidationError: If the proposal does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(proposal, schema)
    if errors:
        raise ValidationError(
            f"Canon registry schema validation failed: {'; '.join(errors)}"
        )


def validate_transition(
    current: str, proposed: str
) -> None:
    """Validate that a canon-level transition is allowed.

    Args:
        current: Current canon level.
        proposed: Proposed next canon level.

    Raises:
        ValueError: If the transition is not valid.
    """
    if current == proposed:
        raise ValueError(
            f"Canon transition rejected: current and proposed are both '{current}'"
        )

    # Deprecation is allowed from any level
    if proposed == CanonLevel.DEPRECATED.value:
        return

    # Check forward transition
    expected_next = _FORWARD_TRANSITIONS.get(current)
    if expected_next is None:
        raise ValueError(
            f"Canon transition rejected: no forward transition from '{current}'"
        )
    if proposed != expected_next:
        raise ValueError(
            f"Canon transition rejected: '{current}' -> '{proposed}' "
            f"(expected '{current}' -> '{expected_next}')"
        )


def validate_operator_approval(proposal: dict[str, Any]) -> None:
    """Enforce D5 (NO_AUTO_PROMOTION): operator must explicitly approve.

    Args:
        proposal: The canon-registry promotion proposal dict.

    Raises:
        ValueError: If operator_approval is not True.
    """
    authority = proposal.get("authority", {})
    if not isinstance(authority, dict):
        raise ValueError("Canon promotion rejected: authority gate missing or invalid")

    if not authority.get("operator_approval", False):
        raise ValueError(
            "Canon promotion rejected: D5 (NO_AUTO_PROMOTION) violation — "
            "operator_approval must be True"
        )

    approver_id = authority.get("approver_id", "")
    if not approver_id or not isinstance(approver_id, str):
        raise ValueError(
            "Canon promotion rejected: approver_id must be a non-empty string"
        )


def validate_review_required(proposal: dict[str, Any]) -> None:
    """Validate that peer review is present when required.

    Review is required for the reviewed -> validated transition.

    Args:
        proposal: The canon-registry promotion proposal dict.

    Raises:
        ValueError: If review is required but not present or verdict is fail.
    """
    current = proposal.get("current_canon_level", "")
    if current not in _REVIEW_REQUIRED_FROM:
        return

    review = proposal.get("review")
    if not isinstance(review, dict):
        raise ValueError(
            "Canon promotion rejected: review gate required for "
            f"'{current}' -> next level transition"
        )

    verdict = review.get("review_verdict", "")
    if verdict == "fail":
        raise ValueError(
            "Canon promotion rejected: review_verdict is 'fail'"
        )

    reviewer_ids = review.get("reviewer_ids", [])
    if not isinstance(reviewer_ids, list) or len(reviewer_ids) == 0:
        raise ValueError(
            "Canon promotion rejected: at least one reviewer_id is required"
        )


def validate_promotion(proposal: dict[str, Any]) -> None:
    """Full canon promotion validation: schema + transition + D5 + review.

    Args:
        proposal: The canon-registry promotion proposal dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If transition, operator approval, or review validation fails.
    """
    validate_canon_registry(proposal)
    validate_transition(
        proposal["current_canon_level"], proposal["proposed_canon_level"]
    )
    validate_operator_approval(proposal)
    validate_review_required(proposal)


__all__ = [
    "CanonLevel",
    "validate_canon_registry",
    "validate_transition",
    "validate_operator_approval",
    "validate_review_required",
    "validate_promotion",
]
