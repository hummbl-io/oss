"""Observability-to-Action receipt schema and validator.

Provides a receipt structure for agentic SRE workflows that move from
telemetry observation to proposed or executed action. The receipt
distinguishes telemetry, hypothesis, recommendation, approval,
execution, and validation stages.

Key invariants:
  - Human approval is required before mutating production systems.
  - Rollback route is required for all executed actions.
  - Evidence references are replayable or explicitly marked ephemeral.
  - Sensitive logs/secrets are redacted before receipt persistence.
  - Schema supports advisory-only and human-approved execution modes.

Reference: issue #1118
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from hummbl_cognition._json_utils import canonical_json as _canonical_json
from hummbl_cognition._timeutils import utc_now as _utc_now

__all__ = [
    "ObservabilityReceiptError",
    "create_obs_action_receipt",
    "validate_obs_action_receipt",
    "compute_receipt_hash",
]


VALID_CONFIDENCE = {"none", "weak", "moderate", "strong", "unknown"}
VALID_APPROVAL_STATUS = {"not_required", "pending", "approved", "rejected", "expired"}
VALID_MODES = {"advisory_only", "human_approved_execution"}
ALLOWED_FIELDS = {
    "receipt_id", "timestamp", "incident_id", "telemetry_source", "query_path",
    "time_window", "incident_context", "agent_hypothesis", "evidence_refs",
    "confidence", "proposed_action", "authority_required", "human_approval_status",
    "human_approval_by", "human_approval_timestamp", "executed_action",
    "execution_actor", "execution_timestamp", "rollback_route",
    "post_action_validation", "post_incident_learning", "mode", "redacted",
    "receipt_hash",
}


class ObservabilityReceiptError(Exception):
    """Raised when receipt validation fails."""


def _new_receipt_id() -> str:
    return f"obs-action-{uuid.uuid4()}"


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_obs_action_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the observability-to-action schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    # Required fields
    required = [
        "receipt_id", "timestamp", "incident_id", "telemetry_source",
        "query_path", "time_window", "agent_hypothesis", "confidence",
        "proposed_action", "authority_required", "human_approval_status",
        "mode", "redacted", "receipt_hash",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(receipt) - ALLOWED_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    if errors:
        return False, errors

    # Type checks
    if not isinstance(receipt.get("receipt_id"), str):
        errors.append("receipt_id must be a string")
    if not isinstance(receipt.get("timestamp"), str):
        errors.append("timestamp must be a string")
    if not isinstance(receipt.get("incident_id"), str):
        errors.append("incident_id must be a string")
    if not isinstance(receipt.get("telemetry_source"), str):
        errors.append("telemetry_source must be a string")
    if not isinstance(receipt.get("query_path"), str):
        errors.append("query_path must be a string")
    if not isinstance(receipt.get("agent_hypothesis"), str):
        errors.append("agent_hypothesis must be a string")
    if not isinstance(receipt.get("proposed_action"), str):
        errors.append("proposed_action must be a string")
    if not isinstance(receipt.get("authority_required"), bool):
        errors.append("authority_required must be a boolean")
    if not isinstance(receipt.get("receipt_hash"), str):
        errors.append("receipt_hash must be a string")

    # Enum checks
    confidence = receipt.get("confidence")
    if not isinstance(confidence, str) or not confidence.strip():
        errors.append("confidence must be a non-empty string")
    elif confidence not in VALID_CONFIDENCE:
        errors.append(f"confidence: {confidence!r} not in {sorted(VALID_CONFIDENCE)}")

    approval = receipt.get("human_approval_status")
    if not isinstance(approval, str) or not approval.strip():
        errors.append("human_approval_status must be a non-empty string")
    elif approval not in VALID_APPROVAL_STATUS:
        errors.append(f"human_approval_status: {approval!r} not in {sorted(VALID_APPROVAL_STATUS)}")

    mode = receipt.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        errors.append("mode must be a non-empty string")
    elif mode not in VALID_MODES:
        errors.append(f"mode: {mode!r} not in {sorted(VALID_MODES)}")

    # time_window structure
    tw = receipt.get("time_window")
    if tw and isinstance(tw, dict):
        if "start" not in tw or "end" not in tw:
            errors.append("time_window must have 'start' and 'end' fields")
    else:
        errors.append("time_window must be an object with 'start' and 'end'")

    # Execution invariants
    executed = receipt.get("executed_action")
    if executed:
        if not receipt.get("rollback_route"):
            errors.append("rollback_route is required when executed_action is set")
        if not receipt.get("execution_actor"):
            errors.append("execution_actor is required when executed_action is set")
        if not receipt.get("execution_timestamp"):
            errors.append("execution_timestamp is required when executed_action is set")
        if receipt.get("mode") != "human_approved_execution":
            errors.append("mode must be 'human_approved_execution' when an action is executed")
        if receipt.get("human_approval_status") != "approved":
            errors.append("human_approval_status must be 'approved' when an action is executed")

    if receipt.get("mode") == "human_approved_execution" and receipt.get("human_approval_status") != "approved":
        errors.append("human_approved_execution mode requires human_approval_status=approved")

    # Advisory mode must not have executed_action
    if receipt.get("mode") == "advisory_only" and executed:
        errors.append("advisory_only mode must not include executed_action")

    # Redaction check
    if not receipt.get("redacted", True):
        errors.append("redacted must be true — sensitive data must be redacted before persistence")

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_obs_action_receipt(
    *,
    incident_id: str,
    telemetry_source: str,
    query_path: str,
    time_window: dict[str, str],
    agent_hypothesis: str,
    confidence: str,
    proposed_action: str,
    authority_required: bool = True,
    human_approval_status: str = "pending",
    mode: str = "advisory_only",
    incident_context: str = "",
    evidence_refs: list[str] | None = None,
    human_approval_by: str = "",
    human_approval_timestamp: str = "",
    executed_action: str = "",
    execution_actor: str = "",
    execution_timestamp: str = "",
    rollback_route: str = "",
    post_action_validation: dict[str, Any] | None = None,
    post_incident_learning: str = "",
    redacted: bool = True,
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate an observability-to-action receipt.

    Args:
        incident_id: Incident identifier.
        telemetry_source: Source of telemetry.
        query_path: Query or path used to retrieve telemetry.
        time_window: Dict with 'start' and 'end' ISO 8601 timestamps.
        agent_hypothesis: Agent's hypothesis about the incident.
        confidence: Agent's confidence (none/weak/moderate/strong/unknown).
        proposed_action: Action proposed by the agent.
        authority_required: Whether human authority is required (default True).
        human_approval_status: Approval status (default 'pending').
        mode: Receipt mode — advisory_only or human_approved_execution.
        incident_context: Optional context description.
        evidence_refs: Optional list of evidence references.
        human_approval_by: Who approved/rejected (if applicable).
        human_approval_timestamp: When approval was given.
        executed_action: Action that was executed (if any).
        execution_actor: Who/what executed the action.
        execution_timestamp: When the action was executed.
        rollback_route: Rollback route (required if executed).
        post_action_validation: Post-action validation result.
        post_incident_learning: Lessons learned.
        redacted: Whether sensitive data has been redacted (default True).

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        ObservabilityReceiptError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "incident_id": incident_id,
        "telemetry_source": telemetry_source,
        "query_path": query_path,
        "time_window": time_window,
        "agent_hypothesis": agent_hypothesis,
        "confidence": confidence,
        "proposed_action": proposed_action,
        "authority_required": authority_required,
        "human_approval_status": human_approval_status,
        "mode": mode,
        "redacted": redacted,
    }

    if incident_context:
        receipt["incident_context"] = incident_context
    if evidence_refs:
        receipt["evidence_refs"] = list(evidence_refs)
    if human_approval_by:
        receipt["human_approval_by"] = human_approval_by
    if human_approval_timestamp:
        receipt["human_approval_timestamp"] = human_approval_timestamp
    if executed_action:
        receipt["executed_action"] = executed_action
        receipt["execution_actor"] = execution_actor
        receipt["execution_timestamp"] = execution_timestamp
        receipt["rollback_route"] = rollback_route
    if post_action_validation:
        receipt["post_action_validation"] = post_action_validation
    if post_incident_learning:
        receipt["post_incident_learning"] = post_incident_learning

    # Compute hash before validation
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    # Validate
    is_valid, errors = validate_obs_action_receipt(receipt)
    if not is_valid:
        raise ObservabilityReceiptError(
            "receipt failed validation: " + "; ".join(errors)
        )

    return receipt
