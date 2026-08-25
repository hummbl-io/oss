"""Trust Adjuster Primitive (P36) — compliance-to-identity loop.

When an agent accumulates compliance violations, the TrustAdjuster reduces
that agent's trust tier. This closes the loop between compliance monitoring
and identity enforcement: violations have consequences on the agent's
ability to act in the fleet.

Enforces K3 (IDENTITY): trust tier changes require evidence (violation_refs)
and operator approval. Severity maps to tier reduction steps:
    low      → 1 step down
    medium   → 2 steps down
    high     → 3 steps down
    critical → direct to REVOKED

Trust tiers (from IdentityEngine):
    OWNER > TRUSTED > MEDIUM-HIGH > MEDIUM > PROBATIONARY > REVOKED

Schema: hummbl_governance/data/trust_adjuster.schema.json
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "trust_adjuster.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None

# Trust tier ordering from highest to lowest (matches IdentityEngine.TRUST_TIERS)
TRUST_TIER_ORDER: list[str] = [
    "OWNER",
    "TRUSTED",
    "MEDIUM-HIGH",
    "MEDIUM",
    "PROBATIONARY",
    "REVOKED",
]

# Severity → tier reduction steps
_SEVERITY_STEPS: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 99,  # direct to REVOKED
}


class Severity(str, Enum):
    """Violation severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_trust_adjuster(adjustment: dict[str, Any]) -> None:
    """Validate a trust adjustment record against schema v1.0.0.

    Raises:
        ValidationError: If the record does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(adjustment, schema)
    if errors:
        raise ValidationError(
            f"Trust adjuster schema validation failed: {'; '.join(errors)}"
        )


def validate_operator_approval(adjustment: dict[str, Any]) -> None:
    """Enforce the operator-approval gate for tier reductions.

    Trust tier reductions require operator approval. Automated adjustments
    must still have operator_approval=True (the operator pre-authorizes the
    automated pipeline).

    Args:
        adjustment: The trust adjustment record dict.

    Raises:
        ValueError: If operator_approval is not True or adjusted_by is empty.
    """
    authority = adjustment.get("authority", {})
    if not isinstance(authority, dict):
        raise ValueError(
            "Trust adjustment rejected: authority gate missing or invalid"
        )

    if not authority.get("operator_approval", False):
        raise ValueError(
            "Trust adjustment rejected: operator_approval must be True — "
            "tier reductions without operator authorization are not permitted"
        )

    adjusted_by = authority.get("adjusted_by", "")
    if not adjusted_by or not isinstance(adjusted_by, str):
        raise ValueError(
            "Trust adjustment rejected: adjusted_by must be a non-empty string"
        )


def validate_tier_transition(adjustment: dict[str, Any]) -> None:
    """Validate that the tier transition is a reduction, not an increase.

    TrustAdjuster only reduces tiers. Promotions must go through the
    IdentityEngine's promotion path (probation → confirmed), not through
    this primitive.

    Args:
        adjustment: The trust adjustment record dict.

    Raises:
        ValueError: If the proposed tier is higher than the current tier,
            or if either tier is invalid.
    """
    current = adjustment.get("current_trust_tier", "")
    proposed = adjustment.get("proposed_trust_tier", "")

    if current not in TRUST_TIER_ORDER:
        raise ValueError(
            f"Trust adjustment rejected: current_trust_tier '{current}' "
            f"is not a valid tier"
        )
    if proposed not in TRUST_TIER_ORDER:
        raise ValueError(
            f"Trust adjustment rejected: proposed_trust_tier '{proposed}' "
            f"is not a valid tier"
        )

    current_idx = TRUST_TIER_ORDER.index(current)
    proposed_idx = TRUST_TIER_ORDER.index(proposed)

    if proposed_idx < current_idx:
        raise ValueError(
            f"Trust adjustment rejected: proposed tier '{proposed}' is higher "
            f"than current tier '{current}' — TrustAdjuster can only reduce tiers; "
            f"use IdentityEngine promotion path for tier increases"
        )

    if proposed_idx == current_idx:
        raise ValueError(
            f"Trust adjustment rejected: current and proposed tiers are both "
            f"'{current}' — no change"
        )


def validate_severity_consistency(adjustment: dict[str, Any]) -> None:
    """Validate that severity maps to the correct tier reduction.

    The proposed tier must be consistent with the severity level:
    - low → 1 step down
    - medium → 2 steps down
    - high → 3 steps down
    - critical → direct to REVOKED

    If the proposed reduction is MORE severe than the severity implies,
    that's acceptable (operator discretion). If it's LESS severe, reject.

    Args:
        adjustment: The trust adjustment record dict.

    Raises:
        ValueError: If the reduction is less severe than the severity implies.
    """
    current = adjustment.get("current_trust_tier", "")
    proposed = adjustment.get("proposed_trust_tier", "")
    severity = adjustment.get("severity", "")

    current_idx = TRUST_TIER_ORDER.index(current)
    proposed_idx = TRUST_TIER_ORDER.index(proposed)
    actual_steps = proposed_idx - current_idx

    expected_steps = _SEVERITY_STEPS.get(severity, 0)

    # Critical must always go to REVOKED
    if severity == "critical":
        if proposed != "REVOKED":
            raise ValueError(
                f"Trust adjustment rejected: severity 'critical' requires "
                f"proposed_trust_tier 'REVOKED', got '{proposed}'"
            )
        return

    # The reduction must be at least as severe as the severity implies
    if actual_steps < expected_steps:
        raise ValueError(
            f"Trust adjustment rejected: severity '{severity}' requires at least "
            f"{expected_steps} tier step(s) down, but only {actual_steps} step(s) "
            f"applied ({current} → {proposed})"
        )


def validate_adjustment(adjustment: dict[str, Any]) -> None:
    """Full trust adjustment validation: schema + operator + transition + severity.

    Args:
        adjustment: The trust adjustment record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If operator approval, transition, or severity validation fails.
    """
    validate_trust_adjuster(adjustment)
    validate_operator_approval(adjustment)
    validate_tier_transition(adjustment)
    validate_severity_consistency(adjustment)


def compute_proposed_tier(
    current_tier: str,
    severity: str,
) -> str:
    """Compute the proposed tier based on current tier and severity.

    Args:
        current_tier: Current trust tier.
        severity: Violation severity (low, medium, high, critical).

    Returns:
        Proposed trust tier after reduction.

    Raises:
        ValueError: If current_tier or severity is invalid.
    """
    if current_tier not in TRUST_TIER_ORDER:
        raise ValueError(f"Invalid current_tier: '{current_tier}'")
    if severity not in _SEVERITY_STEPS:
        raise ValueError(f"Invalid severity: '{severity}'")

    current_idx = TRUST_TIER_ORDER.index(current_tier)
    steps = _SEVERITY_STEPS[severity]

    # Clamp to REVOKED (last index)
    proposed_idx = min(current_idx + steps, len(TRUST_TIER_ORDER) - 1)
    return TRUST_TIER_ORDER[proposed_idx]


def build_adjustment(
    adjustment_id: str,
    agent_id: str,
    current_trust_tier: str,
    severity: str,
    violation_refs: list[str],
    adjusted_by: str,
    receipt_hash: str,
    adjustment_reason: str,
    receipt_sequence: int = 0,
    automated: bool = False,
) -> dict[str, Any]:
    """Build a valid trust adjustment record.

    Computes the proposed tier from severity and assembles a record
    conforming to trust_adjuster.schema.json.

    Args:
        adjustment_id: Unique identifier for this adjustment.
        agent_id: Agent whose tier is being adjusted.
        current_trust_tier: Current trust tier.
        severity: Violation severity (low/medium/high/critical).
        violation_refs: References to compliance violations.
        adjusted_by: Operator or system authorizing the adjustment.
        receipt_hash: Hash-chained proof.
        adjustment_reason: Human-readable explanation.
        receipt_sequence: Sequence ID for ordering.
        automated: Whether this was triggered automatically.

    Returns:
        A trust adjustment record dict.
    """
    proposed = compute_proposed_tier(current_trust_tier, severity)
    return {
        "schema_version": "1.0.0",
        "adjustment_id": adjustment_id,
        "agent_id": agent_id,
        "current_trust_tier": current_trust_tier,
        "proposed_trust_tier": proposed,
        "violation_refs": violation_refs,
        "severity": severity,
        "adjustment_reason": adjustment_reason,
        "authority": {
            "adjusted_by": adjusted_by,
            "operator_approval": True,
            "automated": automated,
        },
        "receipt": {
            "receipt_hash": receipt_hash,
            "receipt_sequence": receipt_sequence,
        },
    }


def run_adjustment(
    adjustment_id: str,
    agent_id: str,
    current_trust_tier: str,
    severity: str,
    violation_refs: list[str],
    adjusted_by: str,
    receipt_hash: str,
    adjustment_reason: str,
    receipt_sequence: int = 0,
    automated: bool = False,
) -> dict[str, Any]:
    """Build and validate a trust adjustment in one call.

    Args:
        Same as build_adjustment.

    Returns:
        A validated trust adjustment record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If any validation gate fails.
    """
    record = build_adjustment(
        adjustment_id=adjustment_id,
        agent_id=agent_id,
        current_trust_tier=current_trust_tier,
        severity=severity,
        violation_refs=violation_refs,
        adjusted_by=adjusted_by,
        receipt_hash=receipt_hash,
        adjustment_reason=adjustment_reason,
        receipt_sequence=receipt_sequence,
        automated=automated,
    )
    validate_adjustment(record)
    return record


__all__ = [
    "Severity",
    "TRUST_TIER_ORDER",
    "validate_trust_adjuster",
    "validate_operator_approval",
    "validate_tier_transition",
    "validate_severity_consistency",
    "validate_adjustment",
    "compute_proposed_tier",
    "build_adjustment",
    "run_adjustment",
]
