"""Admission Control Primitive — validator for governed state transitions.

Bounded promotion from candidate 004 (admission-gate-doctrine).
Invariant: admission is not truth; admission is governed permission for
state transition under authority, executor, scope, evidence, and receipt.

Three novel fields (cost_latency, data_sensitivity, context_freshness)
are validated against schema v1.0.0 with proposer-emitted vs
gateway-emitted field enforcement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "admission_control.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_admission_control(proposal: dict[str, Any]) -> None:
    """Validate an admission-control proposal against schema v1.0.0.

    Raises:
        ValidationError: If the proposal does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(proposal, schema)
    if errors:
        raise ValidationError(
            f"Admission control schema validation failed: {'; '.join(errors)}"
        )


def validate_gateway_emitted_fields(
    proposal: dict[str, Any], *, is_proposer: bool = False
) -> list[str]:
    """Check that proposer-emitted fields do not contain gateway-emitted values.

    The schema cannot express 'this field must not be set by the proposer'
    — this validator enforces the convention programmatically.

    Args:
        proposal: The admission-control proposal dict.
        is_proposer: If True, check that gateway-emitted fields are NOT
            present (the proposer must not supply them). If False, no
            check is performed (gateway is allowed to set them).

    Returns:
        List of violations (empty if clean).
    """
    if not is_proposer:
        return []

    violations: list[str] = []

    ctx = proposal.get("context_freshness", {})
    if not isinstance(ctx, dict):
        return violations

    # freshness_checked_at and stale_sources are GATEWAY-EMITTED ONLY.
    # If they are present in a proposer-supplied proposal, that's a violation.
    # The gateway sets these after validation; the proposer must not.
    if "freshness_checked_at" in ctx:
        violations.append(
            "context_freshness.freshness_checked_at is GATEWAY-EMITTED ONLY; "
            "proposer must not supply this field"
        )
    if "stale_sources" in ctx:
        violations.append(
            "context_freshness.stale_sources is GATEWAY-EMITTED ONLY; "
            "proposer must not supply this field"
        )

    return violations


def validate_admission(
    proposal: dict[str, Any], *, is_proposer: bool = False
) -> None:
    """Full admission validation: schema + gateway-emitted field convention.

    Args:
        proposal: The admission-control proposal dict.
        is_proposer: If True, enforce that gateway-emitted fields are absent.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If gateway-emitted field convention is violated.
    """
    validate_admission_control(proposal)
    violations = validate_gateway_emitted_fields(proposal, is_proposer=is_proposer)
    if violations:
        raise ValueError(
            "Admission validation failed: " + "; ".join(violations)
        )


__all__ = [
    "validate_admission_control",
    "validate_gateway_emitted_fields",
    "validate_admission",
]
