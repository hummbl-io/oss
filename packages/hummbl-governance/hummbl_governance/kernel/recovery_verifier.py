"""Recovery Verifier Primitive — governs re-engagement after a halt.

Enforces K10 (RECOVERY): re-engagement after halt requires root-cause
verification, evidence collection, and operator approval. Gates the
kill_switch/circuit_breaker recovery path.

K10 scoping (operator constraint 2026-07-14): applies to re-engagement
after halt, quarantine, or open breaker only.

Gates:
    - root_cause_analysis.identified must be True
    - if fix_applied is True, fix_description must be non-empty
    - operator_approval.approved must be True
    - operator_approval.approver_id must be non-empty

Schema: hummbl_governance/data/recovery_verifier.schema.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic
from hummbl_governance.schema_validator import SchemaValidator, ValidationError

_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "recovery_verifier.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH) as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_recovery_verifier(verification: dict[str, Any]) -> None:
    """Validate a recovery-verification record against schema v1.

    Raises:
        ValidationError: If the verification does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(verification, schema)
    if errors:
        raise ValidationError(
            f"Recovery verifier schema validation failed: {'; '.join(errors)}"
        )


def validate_root_cause(verification: dict[str, Any]) -> None:
    """Enforce K10 (RECOVERY) root-cause gate.

    root_cause_analysis.identified must be True. If fix_applied is True,
    fix_description must be a non-empty string.

    Args:
        verification: The recovery-verification record dict.

    Raises:
        ValueError: If root cause is not identified or fix description is
            missing when a fix was applied.
    """
    root_cause = verification.get("root_cause_analysis", {})
    if not isinstance(root_cause, dict):
        raise ValueError(
            "Recovery rejected: root_cause_analysis gate missing or invalid"
        )

    if not root_cause.get("identified", False):
        raise ValueError(
            "Recovery rejected: K10 (RECOVERY) violation — "
            "root_cause_analysis.identified must be True"
        )

    if root_cause.get("fix_applied", False):
        fix_description = root_cause.get("fix_description", "")
        if not fix_description or not isinstance(fix_description, str):
            raise ValueError(
                "Recovery rejected: fix_applied is True but fix_description "
                "is empty or missing"
            )


def validate_recovery_operator_approval(verification: dict[str, Any]) -> None:
    """Enforce K10 (RECOVERY) operator-approval gate.

    operator_approval.approved must be True and approver_id must be a
    non-empty string.

    Args:
        verification: The recovery-verification record dict.

    Raises:
        ValueError: If operator approval is not granted or approver_id is
            missing.
    """
    operator_approval = verification.get("operator_approval", {})
    if not isinstance(operator_approval, dict):
        raise ValueError(
            "Recovery rejected: operator_approval gate missing or invalid"
        )

    if not operator_approval.get("approved", False):
        raise ValueError(
            "Recovery rejected: K10 (RECOVERY) violation — "
            "operator_approval.approved must be True"
        )

    approver_id = operator_approval.get("approver_id", "")
    if not isinstance(approver_id, str) or not approver_id.strip():
        raise ValueError(
            "Recovery rejected: approver_id must be a non-empty string"
        )


def validate_recovery(verification: dict[str, Any]) -> None:
    """Full recovery validation: schema + root_cause + operator_approval.

    Args:
        verification: The recovery-verification record dict.

    Raises:
        ValidationError: If schema validation fails.
        ValueError: If root-cause or operator-approval validation fails.
    """
    validate_recovery_verifier(verification)
    validate_root_cause(verification)
    validate_recovery_operator_approval(verification)


def raise_on_recovery_violation(verification: dict[str, Any]) -> None:
    """Validate recovery record and raise KernelPanic(K10) on violation.

    K10 scoping: applies to re-engagement after halt, quarantine, or open
    breaker. A verification record that fails schema, root-cause, or
    operator-approval validation is a K10 (RECOVERY) violation.

    Args:
        verification: The recovery-verification record dict.

    Raises:
        KernelPanic: With invariant=K10 if schema, root-cause, or
            operator-approval validation fails.
    """
    try:
        validate_recovery(verification)
    except ValidationError as e:
        raise KernelPanic(
            invariant=KernelInvariant.RECOVERY,
            detail=f"K10 (RECOVERY) violation — schema invalid: {e}",
            severity="CRITICAL",
        ) from e
    except ValueError as e:
        raise KernelPanic(
            invariant=KernelInvariant.RECOVERY,
            detail=f"K10 (RECOVERY) violation — {e}",
            severity="CRITICAL",
        ) from e


__all__ = [
    "validate_recovery_verifier",
    "validate_root_cause",
    "validate_recovery_operator_approval",
    "validate_recovery",
    "raise_on_recovery_violation",
]
