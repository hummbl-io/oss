"""Postcondition probe receipt schema and validator.

Provides a receipt structure that proves an agent/CI action's declared
side effect actually occurred, rather than relying on process exit code
alone. Prevents false-green failures where a job exits 0 but the side
effect (file write, PR open, bus append, issue comment) did not happen
or was silently dropped.

Designed to detect false-green execution in which a process reports success
without producing its declared side effect.

Key invariants:
  - Every claimed action must declare its observable side effect.
  - The probe must run a replayable verification command.
  - before_state and after_state must be captured for delta verification.
  - A negative check must confirm no unintended side effect occurred.
  - A non-`none` failure_class requires either pipeline failure or an
    explicit operator_override_ref (risk acceptance / approval).
  - The receipt hash is SHA-256 of canonical JSON (excluding the hash
    field) for tamper detection.

Reference: issue #1117 (CI postcondition probes / false-green prevention)
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "PostconditionProbeError",
    "create_postcondition_probe",
    "validate_postcondition_probe",
    "compute_receipt_hash",
]


VALID_VERIFICATION_STATUS = {"verified", "not_verified", "contradicted"}
VALID_FAILURE_CLASS = {
    "none",
    "false_green",
    "partial",
    "silent_drop",
    "wrong_artifact",
    "negative_violation",
    "probe_error",
}
VALID_ARTIFACT_KIND = {
    "file",
    "pr",
    "issue-comment",
    "bus-message",
    "workflow-run",
    "tag",
    "commit",
    "ledger-entry",
    "other",
}
VALID_NEGATIVE_RESULT = {"passed", "failed", "not_applicable"}

# receipt_id is a canonical lowercase UUIDv4 with a receipt-type prefix.
_RECEIPT_ID_PATTERN = (
    r"^postcond-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_RECEIPT_ID_RE = re.compile(_RECEIPT_ID_PATTERN)

ALLOWED_FIELDS = {
    "receipt_id",
    "timestamp",
    "claimed_action",
    "declared_side_effect",
    "expected_artifact",
    "evidence_locator",
    "verification_command",
    "verification_result",
    "before_state",
    "after_state",
    "negative_check",
    "failure_class",
    "operator_override_ref",
    "receipt_hash",
}


class PostconditionProbeError(Exception):
    """Raised when postcondition probe validation fails."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_receipt_id() -> str:
    return f"postcond-{uuid.uuid4()}"


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _is_valid_iso8601(value: str) -> bool:
    """Check if a string is a valid RFC3339-style date-time.

    Requires a timezone (Z suffix or explicit offset). Rejects date-only
    and timezone-less strings.
    """
    if not value or not isinstance(value, str):
        return False
    if "T" not in value:
        return False
    if not (value.endswith("Z") or _has_offset_suffix(value)):
        return False
    candidate = value.replace("Z", "+00:00") if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def _has_offset_suffix(value: str) -> bool:
    """Check if a string ends with a timezone offset like '+00:00' or '-05:00'."""
    if len(value) < 6:
        return False
    tail = value[-6:]
    if tail[0] not in "+-":
        return False
    if tail[3] != ":":
        return False
    return tail[1:3].isdigit() and tail[4:6].isdigit()


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_postcondition_probe(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the postcondition probe schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    # Required fields
    required = [
        "receipt_id",
        "timestamp",
        "claimed_action",
        "declared_side_effect",
        "expected_artifact",
        "evidence_locator",
        "verification_command",
        "verification_result",
        "before_state",
        "after_state",
        "negative_check",
        "failure_class",
        "receipt_hash",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(receipt) - ALLOWED_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    if errors:
        return False, errors

    # Type checks — top-level scalars
    if not isinstance(receipt.get("receipt_id"), str):
        errors.append("receipt_id must be a string")
    elif not _RECEIPT_ID_RE.match(receipt["receipt_id"]):
        errors.append(
            f"receipt_id must match pattern {_RECEIPT_ID_PATTERN} "
            f"(canonical lowercase UUIDv4 after 'postcond-' — got {receipt['receipt_id']!r})"
        )
    if not isinstance(receipt.get("timestamp"), str):
        errors.append("timestamp must be a string")
    elif not _is_valid_iso8601(receipt["timestamp"]):
        errors.append(
            f"timestamp must be an RFC3339 date-time string (got {receipt['timestamp']!r})"
        )
    if not isinstance(receipt.get("claimed_action"), str) or not receipt["claimed_action"].strip():
        errors.append("claimed_action must be a non-empty string")
    if not isinstance(receipt.get("declared_side_effect"), str) or not receipt["declared_side_effect"].strip():
        errors.append("declared_side_effect must be a non-empty string")
    if not isinstance(receipt.get("evidence_locator"), str):
        errors.append("evidence_locator must be a string")
    if not isinstance(receipt.get("verification_command"), str) or not receipt["verification_command"].strip():
        errors.append("verification_command must be a non-empty string (must be replayable)")
    if not isinstance(receipt.get("receipt_hash"), str):
        errors.append("receipt_hash must be a string")

    # expected_artifact structure
    artifact = receipt.get("expected_artifact")
    if isinstance(artifact, dict):
        if "kind" not in artifact or "locator" not in artifact:
            errors.append("expected_artifact must have 'kind' and 'locator'")
        else:
            kind = artifact.get("kind")
            if kind not in VALID_ARTIFACT_KIND:
                errors.append(
                    f"expected_artifact.kind: {kind!r} not in {sorted(VALID_ARTIFACT_KIND)}"
                )
            if not isinstance(artifact.get("locator"), str) or not artifact["locator"].strip():
                errors.append("expected_artifact.locator must be a non-empty string")
            if "content_marker" in artifact and not isinstance(artifact["content_marker"], str):
                errors.append("expected_artifact.content_marker must be a string if present")
    else:
        errors.append("expected_artifact must be an object")

    # verification_result structure
    vr = receipt.get("verification_result")
    if isinstance(vr, dict):
        if "status" not in vr or "observed_state" not in vr:
            errors.append("verification_result must have 'status' and 'observed_state'")
        else:
            status = vr.get("status")
            if status not in VALID_VERIFICATION_STATUS:
                errors.append(
                    f"verification_result.status: {status!r} not in {sorted(VALID_VERIFICATION_STATUS)}"
                )
            if not isinstance(vr.get("observed_state"), str):
                errors.append("verification_result.observed_state must be a string")
            if "exit_code" in vr and not isinstance(vr["exit_code"], int):
                errors.append("verification_result.exit_code must be an integer if present")
            if "latency_ms" in vr and not isinstance(vr["latency_ms"], int):
                errors.append("verification_result.latency_ms must be an integer if present")
    else:
        errors.append("verification_result must be an object")

    # before_state / after_state (optional inner fields)
    for state_field in ("before_state", "after_state"):
        state = receipt.get(state_field)
        if state is None:
            errors.append(f"{state_field} is required (may be empty object)")
        elif not isinstance(state, dict):
            errors.append(f"{state_field} must be an object")
        else:
            if "snapshot" in state and not isinstance(state["snapshot"], str):
                errors.append(f"{state_field}.snapshot must be a string if present")
            cap = state.get("captured_at")
            if cap is not None:
                if not isinstance(cap, str):
                    errors.append(f"{state_field}.captured_at must be a string if present")
                elif not _is_valid_iso8601(cap):
                    errors.append(
                        f"{state_field}.captured_at must be an RFC3339 date-time string (got {cap!r})"
                    )

    # negative_check structure
    nc = receipt.get("negative_check")
    if isinstance(nc, dict):
        if "checked" not in nc or "result" not in nc:
            errors.append("negative_check must have 'checked' and 'result'")
        else:
            if not isinstance(nc.get("checked"), bool):
                errors.append("negative_check.checked must be a boolean")
            result = nc.get("result")
            if result not in VALID_NEGATIVE_RESULT:
                errors.append(
                    f"negative_check.result: {result!r} not in {sorted(VALID_NEGATIVE_RESULT)}"
                )
            if "description" in nc and not isinstance(nc["description"], str):
                errors.append("negative_check.description must be a string if present")
    else:
        errors.append("negative_check must be an object")

    # failure_class enum
    fc = receipt.get("failure_class")
    if fc not in VALID_FAILURE_CLASS:
        errors.append(
            f"failure_class: {fc!r} not in {sorted(VALID_FAILURE_CLASS)}"
        )

    # Cross-field invariants
    status = receipt.get("verification_result", {}).get("status") if isinstance(receipt.get("verification_result"), dict) else None
    fc_value = receipt.get("failure_class")

    # verified status implies failure_class none
    if status == "verified" and fc_value not in (None, "none"):
        errors.append(
            "verification_result.status='verified' requires failure_class='none'"
        )

    # contradicted status implies a non-none failure_class
    if status == "contradicted" and fc_value in (None, "none"):
        errors.append(
            "verification_result.status='contradicted' requires failure_class != 'none'"
        )

    # not_verified status also requires a non-none failure class
    if status == "not_verified" and fc_value in (None, "none"):
        errors.append(
            "verification_result.status='not_verified' requires failure_class != 'none'"
        )

    # negative_check.failed implies negative_violation
    nc_result = receipt.get("negative_check", {}).get("result") if isinstance(receipt.get("negative_check"), dict) else None
    if nc_result == "failed" and fc_value != "negative_violation":
        errors.append(
            "negative_check.result='failed' requires failure_class='negative_violation'"
        )

    # failed negative check means checked must be true
    if nc_result == "failed" and not receipt.get("negative_check", {}).get("checked"):
        errors.append("negative_check.result='failed' requires negative_check.checked=True")

    # Non-none failure_class requires operator_override_ref OR pipeline must fail.
    # The probe cannot force pipeline failure from inside the receipt, so the
    # invariant is: if failure_class != 'none', operator_override_ref MUST be
    # present OR the consumer must fail the pipeline. We require the override
    # ref to be present so that a silent override is impossible — every
    # false-green that is allowed through must be traceable to an approval.
    if fc_value not in (None, "none"):
        override = receipt.get("operator_override_ref")
        if not isinstance(override, str) or not override.strip():
            errors.append(
                "operator_override_ref is required when failure_class != 'none' "
                "(every allowed-through false-green must be traceable to an approval)"
            )

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_postcondition_probe(
    *,
    claimed_action: str,
    declared_side_effect: str,
    expected_artifact: dict[str, Any],
    evidence_locator: str,
    verification_command: str,
    verification_result: dict[str, Any],
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    negative_check: dict[str, Any] | None = None,
    failure_class: str = "none",
    operator_override_ref: str = "",
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate a postcondition probe receipt.

    Args:
        claimed_action: What the agent/CI job claimed to do.
        declared_side_effect: The observable side effect expected.
        expected_artifact: Dict with 'kind', 'locator', optional 'content_marker'.
        evidence_locator: Where evidence was (or was not) found.
        verification_command: Replayable command used to verify the side effect.
        verification_result: Dict with 'status', 'observed_state', optional
            'exit_code' and 'latency_ms'.
        before_state: State snapshot before the action (may be empty {}).
        after_state: State snapshot after the action (may be empty {}).
        negative_check: Dict with 'checked', 'result', optional 'description'.
        failure_class: Failure classification (default 'none').
        operator_override_ref: Required if failure_class != 'none'.
        receipt_id: Override auto-generated ID (testing/determinism).
        timestamp: Override auto-generated timestamp (testing/determinism).

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        PostconditionProbeError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "claimed_action": claimed_action,
        "declared_side_effect": declared_side_effect,
        "expected_artifact": expected_artifact,
        "evidence_locator": evidence_locator,
        "verification_command": verification_command,
        "verification_result": verification_result,
        "before_state": before_state or {},
        "after_state": after_state or {},
        "negative_check": negative_check or {"checked": False, "result": "not_applicable"},
        "failure_class": failure_class,
    }

    if operator_override_ref:
        receipt["operator_override_ref"] = operator_override_ref

    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    is_valid, errors = validate_postcondition_probe(receipt)
    if not is_valid:
        raise PostconditionProbeError(
            "postcondition probe failed validation: " + "; ".join(errors)
        )

    return receipt
