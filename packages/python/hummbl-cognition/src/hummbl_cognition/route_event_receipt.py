"""Route event receipt schema and validator.

Provides a telemetry receipt for a single route health event, tracked
by vendor × model × surface × error code. Feeds the route admission
registry (hummbl-admission-controlled-state#5) by making recurrence
patterns visible at the model × surface granularity that vendor-level
status pages hide.

Motivation:
  - Claude elevated-error recurrence (10+ incidents Jun 2 - Jul 4 2026)
    where Opus 4.8 was disproportionately affected but the pattern was
    invisible at vendor-level status granularity.
  - Anthropic error docs distinguish 529 overloaded_error (capacity,
    retry with backoff) from 429 rate_limit_error (quota, do not retry
    aggressively). The retry/failover policy must treat them differently.

Key invariants:
  - event_class=incident requires status_code >= 400 OR error_type != none
  - event_class=recovery requires status_code == 200 OR error_type == none,
    AND incident_ref must be present (recovery links back to the incident)
  - event_class=degradation requires incident_ref (vendor-acknowledged)
  - error_type=overloaded_error requires retry_policy in
    (retry_with_backoff, circuit_breaker_open) — capacity is transient
  - error_type=rate_limit_error requires retry_policy in
    (retry_once, fail_fast, none) — aggressive retry burns quota
  - error_type=silent_drop requires retry_policy=circuit_breaker_open
    (silent drops indicate fundamental breakage)
  - occurrence_count > 1 requires first_seen_at and last_seen_at
  - first_seen_at <= last_seen_at <= timestamp (temporal ordering)
  - SHA-256 receipt hash for tamper detection

Reference: CI postcondition probes / route telemetry
and hummbl-admission-controlled-state#5 (route admission registry).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "RouteEventError",
    "create_route_event_receipt",
    "validate_route_event_receipt",
    "compute_receipt_hash",
]


VALID_VENDORS = {"openai", "anthropic", "google", "aws", "azure", "github", "other"}
VALID_SURFACES = {
    "api", "chat", "code", "cowork", "github-agent",
    "bedrock", "vertex", "foundry", "other",
}
VALID_EVENT_CLASS = {"incident", "health_check", "degradation", "recovery"}
VALID_ERROR_TYPE = {
    "none", "overloaded_error", "rate_limit_error", "api_error",
    "timeout", "silent_drop", "auth_error", "not_found", "other",
}
VALID_RETRY_POLICY = {
    "none", "retry_with_backoff", "retry_once", "fail_fast", "circuit_breaker_open",
}
VALID_FAILOVER_POLICY = {
    "none", "switch_model", "switch_vendor", "queue_and_wait", "escalate",
}

# Error-type → allowed retry policies. Enforces the 529-vs-429 distinction.
_OVERLOADED_RETRY = {"retry_with_backoff", "circuit_breaker_open"}
_RATE_LIMIT_RETRY = {"retry_once", "fail_fast", "none"}
_SILENT_DROP_RETRY = {"circuit_breaker_open"}

# receipt_id must match the schema pattern ^route-evt-[a-f0-9-]+$
_RECEIPT_ID_RE = re.compile(r"^route-evt-[a-f0-9-]+$")

ALLOWED_FIELDS = {
    "receipt_id", "timestamp", "vendor", "model", "surface", "event_class",
    "status_code", "error_type", "retry_policy", "failover_policy",
    "incident_ref", "first_seen_at", "last_seen_at", "occurrence_count",
    "evidence_refs", "notes", "receipt_hash",
}


class RouteEventError(Exception):
    """Raised when route event receipt validation fails."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_receipt_id() -> str:
    return f"route-evt-{uuid.uuid4()}"


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def _parse_iso(ts: str) -> datetime | None:
    if not ts or not isinstance(ts, str):
        return None
    try:
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


def validate_route_event_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the route event schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    required = [
        "receipt_id", "timestamp", "vendor", "model", "surface",
        "event_class", "status_code", "error_type", "retry_policy",
        "failover_policy", "occurrence_count", "receipt_hash",
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
            "receipt_id must match pattern ^route-evt-[a-f0-9-]+$ "
            f"(lowercase hex and hyphens only after 'route-evt-' prefix — got {receipt['receipt_id']!r})"
        )
    if not isinstance(receipt.get("timestamp"), str):
        errors.append("timestamp must be a string")
    elif not _is_valid_iso8601(receipt["timestamp"]):
        errors.append(
            f"timestamp must be an RFC3339 date-time string (got {receipt['timestamp']!r})"
        )
    if not isinstance(receipt.get("model"), str) or not receipt["model"].strip():
        errors.append("model must be a non-empty string")
    if not isinstance(receipt.get("status_code"), int) or receipt["status_code"] < 0:
        errors.append("status_code must be a non-negative integer")
    if not isinstance(receipt.get("occurrence_count"), int) or receipt["occurrence_count"] < 1:
        errors.append("occurrence_count must be an integer >= 1")
    if not isinstance(receipt.get("receipt_hash"), str):
        errors.append("receipt_hash must be a string")
    if "incident_ref" in receipt and not isinstance(receipt["incident_ref"], str):
        errors.append("incident_ref must be a string if present")
    if "notes" in receipt and not isinstance(receipt["notes"], str):
        errors.append("notes must be a string if present")
    if "evidence_refs" in receipt:
        er = receipt["evidence_refs"]
        if not isinstance(er, list) or not all(isinstance(x, str) for x in er):
            errors.append("evidence_refs must be a list of strings if present")

    # Enum checks
    vendor = receipt.get("vendor")
    if vendor not in VALID_VENDORS:
        errors.append(f"vendor: {vendor!r} not in {sorted(VALID_VENDORS)}")

    surface = receipt.get("surface")
    if surface not in VALID_SURFACES:
        errors.append(f"surface: {surface!r} not in {sorted(VALID_SURFACES)}")

    ec = receipt.get("event_class")
    if ec not in VALID_EVENT_CLASS:
        errors.append(f"event_class: {ec!r} not in {sorted(VALID_EVENT_CLASS)}")

    et = receipt.get("error_type")
    if et not in VALID_ERROR_TYPE:
        errors.append(f"error_type: {et!r} not in {sorted(VALID_ERROR_TYPE)}")

    rp = receipt.get("retry_policy")
    if rp not in VALID_RETRY_POLICY:
        errors.append(f"retry_policy: {rp!r} not in {sorted(VALID_RETRY_POLICY)}")

    fp = receipt.get("failover_policy")
    if fp not in VALID_FAILOVER_POLICY:
        errors.append(f"failover_policy: {fp!r} not in {sorted(VALID_FAILOVER_POLICY)}")

    if errors:
        return False, errors

    # Cross-field invariants
    sc = receipt.get("status_code")
    ec_value = receipt.get("event_class")
    et_value = receipt.get("error_type")
    rp_value = receipt.get("retry_policy")
    oc = receipt.get("occurrence_count")

    # event_class=incident requires status_code >= 400 OR error_type != none
    if ec_value == "incident":
        if not ((isinstance(sc, int) and sc >= 400) or et_value != "none"):
            errors.append(
                "event_class=incident requires status_code >= 400 or error_type != 'none'"
            )

    # event_class=recovery requires (status_code == 200 OR error_type == none)
    # AND incident_ref must be present
    if ec_value == "recovery":
        if not ((isinstance(sc, int) and sc == 200) or et_value == "none"):
            errors.append(
                "event_class=recovery requires status_code == 200 or error_type == 'none'"
            )
        iref = receipt.get("incident_ref")
        if not isinstance(iref, str) or not iref.strip():
            errors.append(
                "event_class=recovery requires incident_ref (recovery links back to the incident)"
            )

    # event_class=degradation requires incident_ref (vendor-acknowledged)
    if ec_value == "degradation":
        iref = receipt.get("incident_ref")
        if not isinstance(iref, str) or not iref.strip():
            errors.append(
                "event_class=degradation requires incident_ref (vendor-acknowledged degradation)"
            )

    # event_class=health_check should not have an error AND must report a
    # healthy HTTP status code. A health_check with status_code >= 400 is
    # a failed probe — it must be classified as 'incident' instead.
    if ec_value == "health_check":
        if et_value != "none":
            errors.append(
                "event_class=health_check requires error_type='none' (use 'incident' for failed probes)"
            )
        if isinstance(sc, int) and sc >= 400:
            errors.append(
                f"event_class=health_check requires status_code < 400 (got {sc}) — "
                "a failed HTTP health probe must be classified as 'incident', not 'health_check'"
            )

    # Error-type → retry_policy invariants (the 529-vs-429 distinction)
    if et_value == "overloaded_error" and rp_value not in _OVERLOADED_RETRY:
        errors.append(
            f"error_type=overloaded_error requires retry_policy in {sorted(_OVERLOADED_RETRY)} "
            f"(capacity is transient — got {rp_value!r})"
        )
    if et_value == "rate_limit_error" and rp_value not in _RATE_LIMIT_RETRY:
        errors.append(
            f"error_type=rate_limit_error requires retry_policy in {sorted(_RATE_LIMIT_RETRY)} "
            f"(aggressive retry burns quota — got {rp_value!r})"
        )
    if et_value == "silent_drop" and rp_value not in _SILENT_DROP_RETRY:
        errors.append(
            f"error_type=silent_drop requires retry_policy={sorted(_SILENT_DROP_RETRY)} "
            f"(silent drops indicate fundamental breakage — got {rp_value!r})"
        )

    # occurrence_count > 1 requires first_seen_at and last_seen_at
    if isinstance(oc, int) and oc > 1:
        if not receipt.get("first_seen_at"):
            errors.append("occurrence_count > 1 requires first_seen_at")
        if not receipt.get("last_seen_at"):
            errors.append("occurrence_count > 1 requires last_seen_at")

    # first_seen_at / last_seen_at must be valid RFC3339 date-times when present.
    # An invalid timestamp must not silently bypass the temporal ordering check.
    fsa_raw = receipt.get("first_seen_at")
    lsa_raw = receipt.get("last_seen_at")
    if fsa_raw is not None and fsa_raw != "":
        if not isinstance(fsa_raw, str):
            errors.append("first_seen_at must be a string if present")
        elif not _is_valid_iso8601(fsa_raw):
            errors.append(
                f"first_seen_at must be an RFC3339 date-time string (got {fsa_raw!r})"
            )
    if lsa_raw is not None and lsa_raw != "":
        if not isinstance(lsa_raw, str):
            errors.append("last_seen_at must be a string if present")
        elif not _is_valid_iso8601(lsa_raw):
            errors.append(
                f"last_seen_at must be an RFC3339 date-time string (got {lsa_raw!r})"
            )

    # Temporal ordering: first_seen_at <= last_seen_at <= timestamp
    # (only checked when all three are valid — invalid timestamps are
    # already reported above and would produce spurious ordering errors)
    ts = _parse_iso(receipt.get("timestamp", ""))
    fsa = _parse_iso(receipt.get("first_seen_at", ""))
    lsa = _parse_iso(receipt.get("last_seen_at", ""))
    if fsa and lsa and fsa > lsa:
        errors.append("first_seen_at must be <= last_seen_at")
    if lsa and ts and lsa > ts:
        errors.append("last_seen_at must be <= timestamp")

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_route_event_receipt(
    *,
    vendor: str,
    model: str,
    surface: str,
    event_class: str,
    status_code: int,
    error_type: str,
    retry_policy: str,
    failover_policy: str,
    occurrence_count: int = 1,
    incident_ref: str = "",
    first_seen_at: str = "",
    last_seen_at: str = "",
    evidence_refs: list[str] | None = None,
    notes: str = "",
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate a route event receipt.

    Args:
        vendor: Vendor providing the route.
        model: Model identifier (free string).
        surface: Product surface where the event was observed.
        event_class: incident / health_check / degradation / recovery.
        status_code: HTTP status code (0 for non-HTTP).
        error_type: Error type (none for healthy events).
        retry_policy: Retry policy for this error type.
        failover_policy: Failover policy for this error type.
        occurrence_count: How many times this error signature has been
            observed (default 1).
        incident_ref: Upstream incident reference (required for
            degradation and recovery).
        first_seen_at: When this error signature was first observed
            (required when occurrence_count > 1).
        last_seen_at: When this error signature was last observed
            (required when occurrence_count > 1).
        evidence_refs: Evidence references.
        notes: Additional context.
        receipt_id: Override auto-generated ID (testing/determinism).
        timestamp: Override auto-generated timestamp (testing/determinism).

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        RouteEventError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "vendor": vendor,
        "model": model,
        "surface": surface,
        "event_class": event_class,
        "status_code": status_code,
        "error_type": error_type,
        "retry_policy": retry_policy,
        "failover_policy": failover_policy,
        "occurrence_count": occurrence_count,
    }

    if incident_ref:
        receipt["incident_ref"] = incident_ref
    if first_seen_at:
        receipt["first_seen_at"] = first_seen_at
    if last_seen_at:
        receipt["last_seen_at"] = last_seen_at
    if evidence_refs:
        receipt["evidence_refs"] = list(evidence_refs)
    if notes:
        receipt["notes"] = notes

    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    is_valid, errors = validate_route_event_receipt(receipt)
    if not is_valid:
        raise RouteEventError(
            "route event receipt failed validation: " + "; ".join(errors)
        )

    return receipt
