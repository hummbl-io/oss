"""Compliance log gap receipt schema and validator.

Provides a receipt structure for tracking compliance-log export
availability and gaps for regulated workspaces. Captures provider,
workspace class, endpoint health, retention window, last successful
export, and any detected gap with its fallback capture path or risk
acceptance.

Motivated by the OpenAI FedRAMP incident (2026-06-30 onward) where the
Compliance Log Platform download endpoint was degraded in FedRAMP
workspaces with 30-day retention, risking unrecoverable audit-trail
gaps for regulated customers.

Decision rule:
  - If HUMMBL has no regulated dependency on this provider workspace,
    monitoring_mode=monitor_only is acceptable.
  - If HUMMBL has any regulated/FedRAMP workspace automation depending
    on this endpoint, monitoring_mode must be fallback_required with an
    active fallback_capture_path, OR risk_accepted with an explicit
    risk_acceptance_ref.
  - If a gap is detected and the gap_start is older than
    (now - retention_days), monitoring_mode MUST be escalate — the gap
    has crossed the retention window and is at risk of being
    unrecoverable. The receipt cannot silently age out a gap.

Key invariants:
  - gap_detected=true requires gap_start and gap_end.
  - monitoring_mode=fallback_required requires a non-empty
    fallback_capture_path with fallback_capture_status=active.
  - monitoring_mode=risk_accepted requires a non-empty
    risk_acceptance_ref.
  - monitoring_mode=escalate is required when a detected gap's start is
    older than the retention window (gap_start < now - retention_days).
  - SHA-256 receipt hash for tamper detection.

Reference: issue #1118 (compliance-log health + fallback gap model).
Also strengthens #1391 (observability-to-action receipt) by providing
the upstream compliance-log telemetry that feeds the obs-action chain.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "ComplianceLogGapError",
    "create_compliance_log_gap_receipt",
    "validate_compliance_log_gap_receipt",
    "compute_receipt_hash",
    "gap_exceeds_retention",
]


VALID_PROVIDERS = {"openai", "anthropic", "google", "aws", "azure", "github", "other"}
VALID_WORKSPACE_CLASS = {"fedramp", "commercial", "enterprise", "team", "individual", "other"}
VALID_ENDPOINT_STATUS = {"healthy", "degraded", "down", "unknown"}
VALID_FALLBACK_STATUS = {"active", "inactive", "not_configured", "failed"}
VALID_MONITORING_MODE = {"monitor_only", "fallback_required", "risk_accepted", "escalate"}

# receipt_id must match the schema pattern ^compliance-gap-[a-f0-9-]+$
_RECEIPT_ID_RE = re.compile(r"^compliance-gap-[a-f0-9-]+$")

ALLOWED_FIELDS = {
    "receipt_id",
    "timestamp",
    "provider",
    "workspace_class",
    "endpoint",
    "endpoint_status",
    "retention_days",
    "export_window_start",
    "export_window_end",
    "last_successful_export_at",
    "oldest_required_timestamp",
    "gap_detected",
    "gap_start",
    "gap_end",
    "fallback_capture_path",
    "fallback_capture_status",
    "risk_acceptance_ref",
    "monitoring_mode",
    "owner",
    "incident_ref",
    "receipt_hash",
}


class ComplianceLogGapError(Exception):
    """Raised when compliance log gap receipt validation fails."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_receipt_id() -> str:
    return f"compliance-gap-{uuid.uuid4()}"


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def _parse_iso(ts: str) -> datetime | None:
    """Parse an ISO 8601 timestamp; return None if blank or unparseable."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        # Accept Z suffix
        cleaned = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


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


def gap_exceeds_retention(
    gap_start: str,
    retention_days: int,
    now: datetime | None = None,
) -> bool:
    """Return True if gap_start is older than (now - retention_days).

    A gap whose start is older than the retention window is at risk of
    being unrecoverable — the provider may have already aged out those
    logs.
    """
    start = _parse_iso(gap_start)
    if start is None:
        return False
    now = now or datetime.now(timezone.utc)
    return (now - start).days > retention_days


def validate_compliance_log_gap_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the compliance log gap schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    required = [
        "receipt_id",
        "timestamp",
        "provider",
        "workspace_class",
        "endpoint",
        "endpoint_status",
        "retention_days",
        "last_successful_export_at",
        "oldest_required_timestamp",
        "gap_detected",
        "monitoring_mode",
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

    # Type checks
    if not isinstance(receipt.get("receipt_id"), str):
        errors.append("receipt_id must be a string")
    elif not _RECEIPT_ID_RE.match(receipt["receipt_id"]):
        errors.append(
            "receipt_id must match pattern ^compliance-gap-[a-f0-9-]+$ "
            f"(lowercase hex and hyphens only after 'compliance-gap-' prefix — got {receipt['receipt_id']!r})"
        )
    if not isinstance(receipt.get("timestamp"), str):
        errors.append("timestamp must be a string")
    elif not _is_valid_iso8601(receipt["timestamp"]):
        errors.append(
            f"timestamp must be an RFC3339 date-time string (got {receipt['timestamp']!r})"
        )
    if not isinstance(receipt.get("endpoint"), str) or not receipt["endpoint"].strip():
        errors.append("endpoint must be a non-empty string")
    if not isinstance(receipt.get("last_successful_export_at"), str):
        errors.append("last_successful_export_at must be a string (may be empty)")
    elif receipt["last_successful_export_at"] and not _is_valid_iso8601(receipt["last_successful_export_at"]):
        errors.append(
            f"last_successful_export_at must be an RFC3339 date-time string when non-empty (got {receipt['last_successful_export_at']!r})"
        )
    if not isinstance(receipt.get("oldest_required_timestamp"), str):
        errors.append("oldest_required_timestamp must be a string")
    elif not _is_valid_iso8601(receipt["oldest_required_timestamp"]):
        errors.append(
            f"oldest_required_timestamp must be an RFC3339 date-time string (got {receipt['oldest_required_timestamp']!r})"
        )
    if not isinstance(receipt.get("receipt_hash"), str):
        errors.append("receipt_hash must be a string")
    if not isinstance(receipt.get("gap_detected"), bool):
        errors.append("gap_detected must be a boolean")

    # retention_days
    rd = receipt.get("retention_days")
    if not isinstance(rd, int) or rd < 1:
        errors.append("retention_days must be a positive integer")

    # Enum checks
    provider = receipt.get("provider")
    if provider not in VALID_PROVIDERS:
        errors.append(f"provider: {provider!r} not in {sorted(VALID_PROVIDERS)}")

    wc = receipt.get("workspace_class")
    if wc not in VALID_WORKSPACE_CLASS:
        errors.append(f"workspace_class: {wc!r} not in {sorted(VALID_WORKSPACE_CLASS)}")

    es = receipt.get("endpoint_status")
    if es not in VALID_ENDPOINT_STATUS:
        errors.append(f"endpoint_status: {es!r} not in {sorted(VALID_ENDPOINT_STATUS)}")

    mm = receipt.get("monitoring_mode")
    if mm not in VALID_MONITORING_MODE:
        errors.append(f"monitoring_mode: {mm!r} not in {sorted(VALID_MONITORING_MODE)}")

    fcs = receipt.get("fallback_capture_status")
    if fcs is not None and fcs not in VALID_FALLBACK_STATUS:
        errors.append(f"fallback_capture_status: {fcs!r} not in {sorted(VALID_FALLBACK_STATUS)}")

    # gap_detected=true requires gap_start and gap_end (both must be valid RFC3339)
    if receipt.get("gap_detected") is True:
        gs = receipt.get("gap_start")
        if not gs:
            errors.append("gap_start is required when gap_detected=true")
        elif not _is_valid_iso8601(gs):
            errors.append(
                f"gap_start must be an RFC3339 date-time string (got {gs!r}) — "
                "an invalid gap_start cannot be used to bypass retention escalation"
            )
        ge = receipt.get("gap_end")
        if not ge:
            errors.append("gap_end is required when gap_detected=true")
        elif not _is_valid_iso8601(ge):
            errors.append(
                f"gap_end must be an RFC3339 date-time string (got {ge!r})"
            )
    elif receipt.get("gap_detected") is False:
        if receipt.get("gap_start"):
            errors.append("gap_start must be empty when gap_detected=false")
        if receipt.get("gap_end"):
            errors.append("gap_end must be empty when gap_detected=false")

    # monitoring_mode=fallback_required requires active fallback_capture_path
    if mm == "fallback_required":
        fcp = receipt.get("fallback_capture_path")
        if not isinstance(fcp, str) or not fcp.strip():
            errors.append(
                "monitoring_mode=fallback_required requires a non-empty fallback_capture_path"
            )
        if receipt.get("fallback_capture_status") != "active":
            errors.append(
                "monitoring_mode=fallback_required requires fallback_capture_status=active"
            )

    # monitoring_mode=risk_accepted requires risk_acceptance_ref
    if mm == "risk_accepted":
        rar = receipt.get("risk_acceptance_ref")
        if not isinstance(rar, str) or not rar.strip():
            errors.append(
                "monitoring_mode=risk_accepted requires a non-empty risk_acceptance_ref"
            )

    # monitoring_mode=escalate is required when a detected gap exceeds retention
    if receipt.get("gap_detected") is True and isinstance(rd, int) and rd >= 1:
        gs = receipt.get("gap_start")
        if isinstance(gs, str) and gs.strip():
            if gap_exceeds_retention(gs, rd):
                if mm != "escalate":
                    errors.append(
                        "monitoring_mode must be 'escalate' when a detected gap's start "
                        f"is older than the {rd}-day retention window (gap_start={gs})"
                    )

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_compliance_log_gap_receipt(
    *,
    provider: str,
    workspace_class: str,
    endpoint: str,
    endpoint_status: str,
    retention_days: int,
    last_successful_export_at: str,
    oldest_required_timestamp: str,
    gap_detected: bool,
    monitoring_mode: str,
    export_window_start: str = "",
    export_window_end: str = "",
    gap_start: str = "",
    gap_end: str = "",
    fallback_capture_path: str = "",
    fallback_capture_status: str = "not_configured",
    risk_acceptance_ref: str = "",
    owner: str = "",
    incident_ref: str = "",
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate a compliance log gap receipt.

    Args:
        provider: Compliance log provider.
        workspace_class: Workspace class (fedramp/commercial/etc).
        endpoint: Compliance log export endpoint URL or identifier.
        endpoint_status: Health of the endpoint.
        retention_days: Provider-stated retention window in days.
        last_successful_export_at: ISO 8601 timestamp of last successful
            export (empty string if never).
        oldest_required_timestamp: ISO 8601 timestamp of the oldest
            compliance-relevant event HUMMBL still needs.
        gap_detected: Whether an audit-trail gap has been detected.
        monitoring_mode: Tracking mode (monitor_only/fallback_required/
            risk_accepted/escalate).
        export_window_start: Start of export window being attempted.
        export_window_end: End of export window being attempted.
        gap_start: Start of detected gap (required if gap_detected).
        gap_end: End of detected gap (required if gap_detected).
        fallback_capture_path: Fallback capture path or method.
        fallback_capture_status: Status of fallback capture.
        risk_acceptance_ref: Risk acceptance reference (required if
            monitoring_mode=risk_accepted).
        owner: Owner of this tracking.
        incident_ref: Upstream provider incident reference.
        receipt_id: Override auto-generated ID (testing/determinism).
        timestamp: Override auto-generated timestamp (testing/determinism).

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        ComplianceLogGapError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "provider": provider,
        "workspace_class": workspace_class,
        "endpoint": endpoint,
        "endpoint_status": endpoint_status,
        "retention_days": retention_days,
        "last_successful_export_at": last_successful_export_at,
        "oldest_required_timestamp": oldest_required_timestamp,
        "gap_detected": gap_detected,
        "monitoring_mode": monitoring_mode,
    }

    if export_window_start:
        receipt["export_window_start"] = export_window_start
    if export_window_end:
        receipt["export_window_end"] = export_window_end
    if gap_detected:
        receipt["gap_start"] = gap_start
        receipt["gap_end"] = gap_end
    if fallback_capture_path:
        receipt["fallback_capture_path"] = fallback_capture_path
    if fallback_capture_status != "not_configured":
        receipt["fallback_capture_status"] = fallback_capture_status
    if risk_acceptance_ref:
        receipt["risk_acceptance_ref"] = risk_acceptance_ref
    if owner:
        receipt["owner"] = owner
    if incident_ref:
        receipt["incident_ref"] = incident_ref

    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    is_valid, errors = validate_compliance_log_gap_receipt(receipt)
    if not is_valid:
        raise ComplianceLogGapError(
            "compliance log gap receipt failed validation: " + "; ".join(errors)
        )

    return receipt
