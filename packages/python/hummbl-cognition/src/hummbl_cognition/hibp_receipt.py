"""HIBP breach-exposure receipt schema and validator.

Provides a receipt structure for Have I Been Pwned (HIBP) breach-exposure
intelligence checks. Governs which actions are safe, which require human
approval, and which are forbidden.

Key invariants:
  - Personal emails in query_subject must be redacted before persistence.
  - API keys must never appear in the receipt (only api_key_used boolean).
  - Forbidden actions (storing raw passwords, public exposure) are tracked.
  - Operator approval is required for personal-email lookups.
  - PwnedPassword queries must use k-anonymity (SHA-1 prefix range only).

Reference: issue #1105
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from hummbl_cognition._json_utils import canonical_json as _canonical_json
from hummbl_cognition._timeutils import utc_now as _utc_now

__all__ = [
    "HIBPReceiptError",
    "create_hibp_receipt",
    "validate_hibp_receipt",
    "compute_hibp_receipt_hash",
]

VALID_QUERY_TYPES = {
    "breachedaccount",
    "breaches",
    "breachname",
    "dataclasses",
    "pwnedpassword",
    "pwnedpasswordsrange",
}
VALID_MODES = {"advisory_only", "approved_lookup", "forbidden"}
VALID_APPROVAL = {"not_required", "approved", "denied", "pending"}

# Query types that require operator approval (personal data involved)
APPROVAL_REQUIRED_TYPES = {"breachedaccount", "pwnedpassword", "pwnedpasswordsrange"}

# Query types that are safe without approval (aggregate/public data)
NO_APPROVAL_TYPES = {"breaches", "breachname", "dataclasses"}
ALLOWED_RECEIPT_FIELDS = {
    "receipt_id",
    "timestamp",
    "query_type",
    "query_subject",
    "query_subject_redacted",
    "api_key_used",
    "operator_approval",
    "operator_approval_by",
    "mode",
    "findings_count",
    "findings_summary",
    "actions_taken",
    "forbidden_actions_avoided",
    "redacted",
    "receipt_hash",
}
ALLOWED_FINDING_KEYS = {
    "breach_name",
    "breach_date",
    "data_classes",
    "is_verified",
    "is_sensitive",
}


class HIBPReceiptError(Exception):
    """Raised when HIBP receipt validation fails."""


def _new_receipt_id() -> str:
    return f"hibp-{uuid.uuid4()}"


def compute_hibp_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_hibp_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the HIBP breach-exposure schema."""
    errors: list[str] = []

    required = [
        "receipt_id",
        "timestamp",
        "query_type",
        "query_subject",
        "operator_approval",
        "mode",
        "findings_count",
        "receipt_hash",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    unexpected = sorted(set(receipt) - ALLOWED_RECEIPT_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    query_type = receipt.get("query_type", "")
    if query_type and query_type not in VALID_QUERY_TYPES:
        errors.append(f"query_type: {query_type!r} not in {sorted(VALID_QUERY_TYPES)}")

    mode = receipt.get("mode", "")
    if mode and mode not in VALID_MODES:
        errors.append(f"mode: {mode!r} not in {sorted(VALID_MODES)}")

    approval = receipt.get("operator_approval", "")
    if approval and approval not in VALID_APPROVAL:
        errors.append(
            f"operator_approval: {approval!r} not in {sorted(VALID_APPROVAL)}"
        )

    # Approval-required query types must have approved status
    if query_type in APPROVAL_REQUIRED_TYPES:
        if receipt.get("mode") == "approved_lookup" and approval != "approved":
            errors.append(
                f"query_type '{query_type}' requires operator_approval='approved' "
                f"when mode='approved_lookup', got '{approval}'"
            )
        if receipt.get("mode") == "advisory_only" and approval == "approved":
            errors.append(
                f"query_type '{query_type}' with mode='advisory_only' should not "
                f"have operator_approval='approved'"
            )

    # No-approval types should not require approval
    if query_type in NO_APPROVAL_TYPES and approval == "pending":
        errors.append(
            f"query_type '{query_type}' does not require approval — "
            f"operator_approval should be 'not_required', not 'pending'"
        )

    # Forbidden mode must not have findings
    if mode == "forbidden" and receipt.get("findings_count", 0) > 0:
        errors.append("mode='forbidden' must have findings_count=0")

    # Redaction checks
    for field in ("redacted", "query_subject_redacted", "api_key_used"):
        if field not in receipt:
            errors.append(f"missing required field: {field}")

    if not receipt.get("redacted", True):
        errors.append("redacted must be true — sensitive data must be redacted")

    if (
        not receipt.get("query_subject_redacted", True)
        and query_type == "breachedaccount"
    ):
        errors.append(
            "query_subject_redacted must be true for breachedaccount queries "
            "(personal email must be redacted)"
        )

    findings_summary = receipt.get("findings_summary", [])
    if findings_summary:
        if not isinstance(findings_summary, list):
            errors.append("findings_summary must be a list")
        else:
            for i, finding in enumerate(findings_summary):
                if not isinstance(finding, dict):
                    errors.append(f"findings_summary {i}: must be a dict")
                    continue
                extra = sorted(set(finding) - ALLOWED_FINDING_KEYS)
                if extra:
                    errors.append(f"findings_summary {i}: unexpected fields: {extra}")

    # API key must never be in the receipt as a string
    for key, val in receipt.items():
        if isinstance(val, str) and val.startswith("hibp-") and key != "receipt_id":
            errors.append(
                f"potential API key found in field '{key}' — keys must never be in receipts"
            )

    # Hash verification
    expected_hash = compute_hibp_receipt_hash(receipt)
    stored_hash = receipt.get("receipt_hash", "")
    if isinstance(stored_hash, str) and not re.fullmatch(r"[a-f0-9]{64}", stored_hash):
        errors.append("receipt_hash must be 64 lowercase hex characters")
    if receipt.get("receipt_hash") != expected_hash:
        errors.append(
            "receipt_hash does not match computed hash — receipt may be tampered"
        )

    return len(errors) == 0, errors


def create_hibp_receipt(
    *,
    query_type: str,
    query_subject: str,
    mode: str = "advisory_only",
    operator_approval: str = "not_required",
    findings_count: int = 0,
    findings_summary: list[dict[str, Any]] | None = None,
    actions_taken: list[str] | None = None,
    forbidden_actions_avoided: list[str] | None = None,
    operator_approval_by: str = "",
    api_key_used: bool = False,
    query_subject_redacted: bool = True,
    redacted: bool = True,
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate an HIBP breach-exposure receipt.

    Args:
        query_type: Type of HIBP query (breachedaccount, breaches, etc.).
        query_subject: Subject of the query (email, domain, hash prefix).
        mode: Receipt mode — advisory_only, approved_lookup, or forbidden.
        operator_approval: Approval status.
        findings_count: Number of breach findings.
        findings_summary: Optional list of breach summary dicts.
        actions_taken: Optional list of actions taken.
        forbidden_actions_avoided: Optional list of actions correctly avoided.
        operator_approval_by: Who approved/denied.
        api_key_used: Whether an HIBP API key was used.
        query_subject_redacted: Whether query_subject is redacted.
        redacted: Whether receipt is redacted.

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        HIBPReceiptError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "query_type": query_type,
        "query_subject": query_subject,
        "query_subject_redacted": query_subject_redacted,
        "api_key_used": api_key_used,
        "operator_approval": operator_approval,
        "mode": mode,
        "findings_count": findings_count,
        "redacted": redacted,
    }

    if operator_approval_by:
        receipt["operator_approval_by"] = operator_approval_by
    if findings_summary:
        receipt["findings_summary"] = findings_summary
    if actions_taken:
        receipt["actions_taken"] = actions_taken
    if forbidden_actions_avoided:
        receipt["forbidden_actions_avoided"] = forbidden_actions_avoided

    receipt["receipt_hash"] = compute_hibp_receipt_hash(receipt)

    is_valid, errors = validate_hibp_receipt(receipt)
    if not is_valid:
        raise HIBPReceiptError("receipt failed validation: " + "; ".join(errors))

    return receipt
