"""Rollback Primitive — enforces K9 (REVERSIBILITY).

Every governed action must declare a rollback path or be explicitly marked
irreversible with a recorded risk acceptance. This primitive closes the
reversibility loop: no action may proceed without either a concrete
rollback plan (reversible / partially_reversible) or a documented risk
acceptance signed by an operator (irreversible).

K9 scoping (operator constraint 2026-07-14): applies to governed durable-
state mutations and irreversible external side effects only.

Schema: hummbl_governance/data/rollback.schema.json
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic
from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "rollback.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


class Reversibility(str, Enum):
    """Reversibility classifications for governed actions."""

    REVERSIBLE = "reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"


# Reversibility levels that require a rollback plan
_PLAN_REQUIRED = {Reversibility.REVERSIBLE.value, Reversibility.PARTIALLY_REVERSIBLE.value}


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_rollback(declaration: dict[str, Any]) -> None:
    """Validate a rollback declaration against schema v1.0.0.

    Raises:
        ValidationError: If the declaration does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(declaration, schema)
    if errors:
        raise ValidationError(
            f"Rollback schema validation failed: {'; '.join(errors)}"
        )


def validate_reversibility(declaration: dict[str, Any]) -> None:
    """Enforce K9 (REVERSIBILITY): rollback plan or risk acceptance required.

    - If reversibility is 'reversible' or 'partially_reversible', rollback_plan
      must be present with at least 1 step.
    - If reversibility is 'irreversible', irreversibility_acceptance must be
      present with risk_description and acceptor_id.

    Args:
        declaration: The rollback declaration dict.

    Raises:
        ValueError: If the reversibility requirements are not met.
    """
    reversibility = declaration.get("reversibility", "")

    if reversibility in _PLAN_REQUIRED:
        rollback_plan = declaration.get("rollback_plan")
        if not isinstance(rollback_plan, dict):
            raise ValueError(
                f"Rollback declaration rejected: rollback_plan required for "
                f"reversibility='{reversibility}'"
            )

        steps = rollback_plan.get("rollback_steps")
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError(
                f"Rollback declaration rejected: rollback_plan must contain "
                f"at least one rollback_step for reversibility='{reversibility}'"
            )

    elif reversibility == Reversibility.IRREVERSIBLE.value:
        acceptance = declaration.get("irreversibility_acceptance")
        if not isinstance(acceptance, dict):
            raise ValueError(
                "Rollback declaration rejected: irreversibility_acceptance "
                "required for reversibility='irreversible'"
            )

        risk_description = acceptance.get("risk_description")
        if not risk_description or not isinstance(risk_description, str):
            raise ValueError(
                "Rollback declaration rejected: irreversibility_acceptance "
                "must include a non-empty risk_description"
            )

        acceptor_id = acceptance.get("acceptor_id")
        if not acceptor_id or not isinstance(acceptor_id, str):
            raise ValueError(
                "Rollback declaration rejected: irreversibility_acceptance "
                "must include a non-empty acceptor_id"
            )


def validate_rollback_declaration(declaration: dict[str, Any]) -> None:
    """Full rollback declaration validation: schema + reversibility (K9).

    Args:
        declaration: The rollback declaration dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If reversibility validation fails.
    """
    validate_rollback(declaration)
    validate_reversibility(declaration)


def raise_on_rollback_violation(declaration: dict[str, Any]) -> None:
    """Validate rollback declaration and raise KernelPanic(K9) on violation.

    K9 scoping: applies to governed durable-state mutations and irreversible
    external side effects. A declaration that fails schema or reversibility
    validation is a K9 (REVERSIBILITY) violation.

    Args:
        declaration: The rollback declaration dict.

    Raises:
        KernelPanic: With invariant=K9 if schema or reversibility validation
            fails. The underlying error type is noted in the detail.
    """
    try:
        validate_rollback_declaration(declaration)
    except ValidationError as e:
        raise KernelPanic(
            invariant=KernelInvariant.REVERSIBILITY,
            detail=f"K9 (REVERSIBILITY) violation — schema invalid: {e}",
            severity="CRITICAL",
        ) from e
    except ValueError as e:
        raise KernelPanic(
            invariant=KernelInvariant.REVERSIBILITY,
            detail=f"K9 (REVERSIBILITY) violation — {e}",
            severity="CRITICAL",
        ) from e


__all__ = [
    "Reversibility",
    "validate_rollback",
    "validate_reversibility",
    "validate_rollback_declaration",
    "raise_on_rollback_violation",
]
