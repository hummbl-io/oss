"""Specification-derived GateBench seed evaluator.

No proprietary founder-mode source is imported or copied. These minimal rules encode
the public planning invariants needed for the first synthetic vertical pilot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .base120 import BASE120_CODES


class GateBenchError(ValueError):
    """A GateBench seed case is malformed."""


class Base120CaseError(ValueError):
    """A Base120 quality GateBench case is malformed."""


@dataclass(frozen=True, slots=True)
class GateBenchResult:
    case_id: str
    severity: str
    disposition: str
    reasons: tuple[str, ...]


EXPECTED_DISPOSITIONS = {"accept", "reject", "abstain"}


def _require_nonempty_string(case: dict[str, Any], field: str) -> str:
    value = case[field]
    if not isinstance(value, str) or not value:
        raise GateBenchError(f"{field} must be a non-empty string")
    return value


def _require_unique_string_list(case: dict[str, Any], field: str) -> list[str]:
    value = case[field]
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(set(value)) != len(value)
    ):
        raise GateBenchError(f"{field} must be a list of unique non-empty strings")
    return value


@dataclass(frozen=True, slots=True)
class Base120Result:
    case_id: str
    severity: str
    disposition: str
    reasons: tuple[str, ...]


def evaluate_case(case: dict[str, Any]) -> GateBenchResult:
    """Evaluate receipt laundering and independence in a synthetic seed case."""

    required = {
        "case_id",
        "severity",
        "claim",
        "evidence_refs",
        "receipt_refs",
        "author_id",
        "evaluator_id",
        "expected_disposition",
    }
    missing = sorted(required - case.keys())
    if missing:
        raise GateBenchError(f"missing fields: {', '.join(missing)}")
    if not isinstance(case["severity"], str) or case["severity"] not in {"P0", "P1", "P2"}:
        raise GateBenchError("severity must be P0, P1, or P2")
    _require_nonempty_string(case, "case_id")
    _require_nonempty_string(case, "claim")
    evidence_refs = _require_unique_string_list(case, "evidence_refs")
    _require_unique_string_list(case, "receipt_refs")
    _require_nonempty_string(case, "author_id")
    _require_nonempty_string(case, "evaluator_id")
    if (
        not isinstance(case["expected_disposition"], str)
        or case["expected_disposition"] not in EXPECTED_DISPOSITIONS
    ):
        raise GateBenchError("expected_disposition must be accept, reject, or abstain")

    reasons: list[str] = []
    if not evidence_refs:
        reasons.append("claim lacks evidence; receipts cannot substitute")
    if case["author_id"] == case["evaluator_id"]:
        reasons.append("author cannot self-qualify")
    disposition = "reject" if reasons else "accept"
    return GateBenchResult(case["case_id"], case["severity"], disposition, tuple(reasons))


def evaluate_base120_case(case: dict[str, Any]) -> Base120Result:
    """Evaluate Base120 cognitive structuring quality in a skill's output.

    Checks that the output has:
    - ``Base120 Cognitive Structuring`` header
    - At least one Why/Reveals/Action finding or analysis block
    - ``Base120 Applied:`` footer with codes
    - All codes in the footer are valid Base120 operator codes
    """
    required = {"case_id", "severity", "skill_name", "base120_output"}
    missing = sorted(required - case.keys())
    if missing:
        raise Base120CaseError(f"missing fields: {', '.join(missing)}")
    if case["severity"] not in {"P0", "P1", "P2"}:
        raise Base120CaseError("severity must be P0, P1, or P2")
    if not isinstance(case["base120_output"], str):
        raise Base120CaseError("base120_output must be a string")

    output: str = case["base120_output"]
    reasons: list[str] = []

    # Check header
    if "Base120 Cognitive Structuring" not in output:
        reasons.append("missing Base120 Cognitive Structuring header")

    # Check Why/Reveals/Action analysis
    has_why = "Why:" in output
    has_reveals = "Reveals:" in output
    has_action = "Action:" in output
    if not (has_why and has_reveals and has_action):
        missing_parts = []
        if not has_why:
            missing_parts.append("Why")
        if not has_reveals:
            missing_parts.append("Reveals")
        if not has_action:
            missing_parts.append("Action")
        reasons.append(
            f"missing cognitive analysis: {', '.join(missing_parts)} "
            "— Base120 requires Why/Reveals/Action"
        )

    # Check footer
    footer_match = re.search(r"Base120 Applied:\s*(.+)", output)
    if not footer_match:
        reasons.append("missing Base120 Applied footer with operator codes")
    else:
        # Extract codes from footer
        footer_text = footer_match.group(1).strip()
        codes = [c.strip() for c in footer_text.split(",") if c.strip()]
        if not codes:
            reasons.append("Base120 Applied footer has no operator codes")
        else:
            invalid_codes = [c for c in codes if c not in BASE120_CODES]
            if invalid_codes:
                reasons.append(f"invalid Base120 operator codes: {', '.join(invalid_codes)}")

    disposition = "reject" if reasons else "accept"
    return Base120Result(case["case_id"], case["severity"], disposition, tuple(reasons))
