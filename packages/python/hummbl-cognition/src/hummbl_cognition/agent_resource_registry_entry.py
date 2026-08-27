"""Agent resource registry entry schema and validator.

Provides a registry entry for an agent-discoverable resource (tool, MCP
server, skill, agent, canvas, connector, script, Vertex AI Extension,
or other). Governs discovery, installation, invocation, and publication
authority. Sensitive resources are disabled by default unless explicitly
admitted.

Motivation: issue #1116 — as the agent fleet gains more MCP servers,
skills, tools, and connectors, discovery becomes an authority surface.
Agents need to know what they may discover, install, invoke, and cite
without ambient expansion of authority. The Vertex AI Extensions
inventory is one resource class tracked by this registry.

Key invariants:
  - namespace_status=admitted requires install_authority and
    invoke_authority to NOT be 'disabled' (an admitted resource must be
    usable by at least one authority class).
  - namespace_status=candidate requires install_authority and
    invoke_authority to be 'disabled' AND publish_authority to be
    'disabled' or 'operator_only' (no ambient authority — candidates
    are not usable or citable until admitted).
  - namespace_status=rejected or retired requires rejection_reason AND
    install_authority='disabled' AND invoke_authority='disabled' (a
    rejected/retired resource must not remain usable — no ambient
    authority persists after rejection).
  - risk_class=critical requires publish_authority=disabled or
    operator_only (critical-risk resources must not appear in external
    artifacts without operator gate).
  - privacy_class=restricted requires publish_authority=disabled or
    operator_only.
  - secrets_required=true requires risk_class >= medium (a resource
    using credentials is at least medium risk).
  - migration_decision=migrate requires migration_target to be present.
  - allowed_contexts and blocked_contexts must not overlap (a context
    cannot be both allowed and blocked).
  - resource_id must match ^res-[a-z0-9-]+$ (validator matches schema).
  - last_reviewed_at must be a valid ISO 8601 date-time (validator
    matches schema).
  - SHA-256 entry hash for tamper detection.

Reference: Agent Resource Registry.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from hummbl_cognition._json_utils import canonical_json as _canonical_json

__all__ = [
    "AgentResourceRegistryError",
    "create_registry_entry",
    "validate_registry_entry",
    "validate_registry_batch",
    "validate_discovery_receipt",
    "create_discovery_receipt",
    "compute_entry_hash",
    "compute_receipt_hash",
]


VALID_RESOURCE_TYPE = {
    "tool",
    "mcp_server",
    "skill",
    "agent",
    "canvas",
    "connector",
    "script",
    "vertex-extension",
    "other",
}
VALID_NAMESPACE_STATUS = {"candidate", "admitted", "rejected", "retired"}
VALID_AUTHORITY = {
    "operator_only",
    "steward",
    "trusted",
    "active",
    "probationary",
    "disabled",
}
VALID_CONTEXT = {
    "development",
    "testing",
    "production",
    "research",
    "briefing",
    "governance",
    "external_facing",
}
VALID_RISK_CLASS = {"low", "medium", "high", "critical"}
VALID_PRIVACY_CLASS = {"public", "internal", "confidential", "restricted"}
VALID_MIGRATION_DECISION = {
    "none",
    "inventory_only",
    "migrate",
    "hold",
    "reject_migration",
}

# Risk ordering for comparison
_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# resource_id must match the schema pattern ^res-[a-z0-9-]+$
_RESOURCE_ID_RE = re.compile(r"^res-[a-z0-9-]+$")

ALLOWED_FIELDS = {
    "resource_id",
    "resource_type",
    "resource_name",
    "resource_owner",
    "source_registry",
    "namespace_status",
    "install_authority",
    "invoke_authority",
    "publish_authority",
    "allowed_contexts",
    "blocked_contexts",
    "secrets_required",
    "network_required",
    "risk_class",
    "privacy_class",
    "receipt_required",
    "discovery_receipts",
    "rejection_reason",
    "admission_conditions",
    "migration_decision",
    "migration_target",
    "last_reviewed_at",
    "reviewed_by",
    "notes",
    "entry_hash",
}


class AgentResourceRegistryError(Exception):
    """Raised when agent resource registry entry validation fails."""


def _is_valid_iso8601(value: str) -> bool:
    """Check if a string is a valid RFC3339-style date-time.

    Accepts forms like '2026-07-04T00:00:00Z' and '2026-07-04T00:00:00+00:00'.
    Rejects 'not-a-date', empty strings, date-only strings, and timezone-less
    date-times (the schema requires format: date-time, which is RFC3339 —
    a timezone offset or Z suffix is mandatory).
    """
    if not value or not isinstance(value, str):
        return False
    # Must contain a time component (T separator) — date-only is not a date-time.
    if "T" not in value:
        return False
    # RFC3339 requires a timezone: either a trailing 'Z' or an explicit
    # offset like '+00:00' or '-05:00'. A timezone-less date-time like
    # '2026-07-04T00:00:00' is NOT valid RFC3339.
    if not (value.endswith("Z") or _has_offset_suffix(value)):
        return False
    # Accept trailing 'Z' (common in our receipts) by replacing with +00:00
    # so fromisoformat can parse it (Python 3.11+ accepts 'Z' directly, but
    # this keeps the helper robust on 3.10).
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
    # Offset is [+-]HH:MM at the end (5 chars), preceded by 'T...'.
    tail = value[-6:]
    if tail[0] not in "+-":
        return False
    if tail[3] != ":":
        return False
    return tail[1:3].isdigit() and tail[4:6].isdigit()


def compute_entry_hash(entry: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical entry (excluding the hash field)."""
    stripped = {k: v for k, v in entry.items() if k != "entry_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_registry_entry(entry: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a registry entry dict against the schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    required = [
        "resource_id",
        "resource_type",
        "resource_owner",
        "namespace_status",
        "install_authority",
        "invoke_authority",
        "risk_class",
        "privacy_class",
        "receipt_required",
        "last_reviewed_at",
        "entry_hash",
    ]
    for field in required:
        if field not in entry or entry[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(entry) - ALLOWED_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    if errors:
        return False, errors

    # Type checks
    if not isinstance(entry.get("resource_id"), str):
        errors.append("resource_id must be a string")
    elif not _RESOURCE_ID_RE.match(entry["resource_id"]):
        errors.append(
            "resource_id must match pattern ^res-[a-z0-9-]+$ "
            f"(lowercase alphanumeric and hyphens only after 'res-' prefix — got {entry['resource_id']!r})"
        )
    if (
        not isinstance(entry.get("resource_owner"), str)
        or not entry["resource_owner"].strip()
    ):
        errors.append("resource_owner must be a non-empty string")
    if not isinstance(entry.get("last_reviewed_at"), str):
        errors.append("last_reviewed_at must be a string")
    elif not _is_valid_iso8601(entry["last_reviewed_at"]):
        errors.append(
            f"last_reviewed_at must be an ISO 8601 date-time string (got {entry['last_reviewed_at']!r})"
        )
    if not isinstance(entry.get("entry_hash"), str):
        errors.append("entry_hash must be a string")
    if not isinstance(entry.get("receipt_required"), bool):
        errors.append("receipt_required must be a boolean")

    # Optional string fields
    for field in (
        "resource_name",
        "source_registry",
        "rejection_reason",
        "migration_target",
        "reviewed_by",
        "notes",
    ):
        if (
            field in entry
            and entry[field] is not None
            and not isinstance(entry[field], str)
        ):
            errors.append(f"{field} must be a string if present")

    # Optional boolean fields
    for field in ("secrets_required", "network_required"):
        if (
            field in entry
            and entry[field] is not None
            and not isinstance(entry[field], bool)
        ):
            errors.append(f"{field} must be a boolean if present")

    # Optional list fields
    for field in (
        "allowed_contexts",
        "blocked_contexts",
        "discovery_receipts",
        "admission_conditions",
    ):
        if field in entry and entry[field] is not None:
            if not isinstance(entry[field], list):
                errors.append(f"{field} must be a list if present")
            elif not all(isinstance(x, str) for x in entry[field]):
                errors.append(f"{field} must be a list of strings if present")

    # Enum checks
    rt = entry.get("resource_type")
    if rt not in VALID_RESOURCE_TYPE:
        errors.append(f"resource_type: {rt!r} not in {sorted(VALID_RESOURCE_TYPE)}")

    ns = entry.get("namespace_status")
    if ns not in VALID_NAMESPACE_STATUS:
        errors.append(
            f"namespace_status: {ns!r} not in {sorted(VALID_NAMESPACE_STATUS)}"
        )

    for field in ("install_authority", "invoke_authority", "publish_authority"):
        v = entry.get(field)
        if v is not None and v not in VALID_AUTHORITY:
            errors.append(f"{field}: {v!r} not in {sorted(VALID_AUTHORITY)}")

    rc = entry.get("risk_class")
    if rc not in VALID_RISK_CLASS:
        errors.append(f"risk_class: {rc!r} not in {sorted(VALID_RISK_CLASS)}")

    pc = entry.get("privacy_class")
    if pc not in VALID_PRIVACY_CLASS:
        errors.append(f"privacy_class: {pc!r} not in {sorted(VALID_PRIVACY_CLASS)}")

    md = entry.get("migration_decision")
    if md is not None and md not in VALID_MIGRATION_DECISION:
        errors.append(
            f"migration_decision: {md!r} not in {sorted(VALID_MIGRATION_DECISION)}"
        )

    # Context enum checks
    for field in ("allowed_contexts", "blocked_contexts"):
        ctxs = entry.get(field)
        if isinstance(ctxs, list):
            for ctx in ctxs:
                if ctx not in VALID_CONTEXT:
                    errors.append(
                        f"{field} item: {ctx!r} not in {sorted(VALID_CONTEXT)}"
                    )

    if errors:
        return False, errors

    # Cross-field invariants

    # namespace_status=admitted requires install/invoke authority NOT disabled
    if ns == "admitted":
        if entry.get("install_authority") == "disabled":
            errors.append(
                "namespace_status=admitted requires install_authority != 'disabled' "
                "(an admitted resource must be installable by at least one authority class)"
            )
        if entry.get("invoke_authority") == "disabled":
            errors.append(
                "namespace_status=admitted requires invoke_authority != 'disabled' "
                "(an admitted resource must be invocable by at least one authority class)"
            )

    # namespace_status=candidate requires install/invoke authority = disabled
    # AND publish_authority in (disabled, operator_only) — no ambient authority
    # for candidates. A candidate must not be installable, invocable, or
    # publishable/citable in external artifacts until explicitly admitted.
    if ns == "candidate":
        if entry.get("install_authority") != "disabled":
            errors.append(
                "namespace_status=candidate requires install_authority='disabled' "
                "(no ambient authority — candidates are not usable until admitted)"
            )
        if entry.get("invoke_authority") != "disabled":
            errors.append(
                "namespace_status=candidate requires invoke_authority='disabled' "
                "(no ambient authority — candidates are not usable until admitted)"
            )
        pa = entry.get("publish_authority")
        if pa not in ("disabled", "operator_only"):
            errors.append(
                "namespace_status=candidate requires publish_authority in ('disabled', 'operator_only') "
                f"(candidates must not be publishable/cited in external artifacts until admitted — got {pa!r})"
            )

    # namespace_status=rejected or retired requires rejection_reason AND
    # disabled install/invoke authority (a rejected/retired resource must not
    # remain usable — no ambient authority persists after rejection).
    if ns in ("rejected", "retired"):
        rr = entry.get("rejection_reason")
        if not isinstance(rr, str) or not rr.strip():
            errors.append(
                f"namespace_status={ns} requires a non-empty rejection_reason"
            )
        if entry.get("install_authority") != "disabled":
            errors.append(
                f"namespace_status={ns} requires install_authority='disabled' "
                f"(a rejected/retired resource must not remain installable — got {entry.get('install_authority')!r})"
            )
        if entry.get("invoke_authority") != "disabled":
            errors.append(
                f"namespace_status={ns} requires invoke_authority='disabled' "
                f"(a rejected/retired resource must not remain invocable — got {entry.get('invoke_authority')!r})"
            )

    # risk_class=critical requires publish_authority in (disabled, operator_only)
    if rc == "critical":
        pa = entry.get("publish_authority")
        if pa not in (None, "disabled", "operator_only"):
            errors.append(
                "risk_class=critical requires publish_authority in ('disabled', 'operator_only') "
                f"(critical-risk resources must not appear in external artifacts — got {pa!r})"
            )

    # privacy_class=restricted requires publish_authority in (disabled, operator_only)
    if pc == "restricted":
        pa = entry.get("publish_authority")
        if pa not in (None, "disabled", "operator_only"):
            errors.append(
                "privacy_class=restricted requires publish_authority in ('disabled', 'operator_only') "
                f"(restricted resources must not appear in external artifacts — got {pa!r})"
            )

    # secrets_required=true requires risk_class >= medium
    if entry.get("secrets_required") is True:
        if rc in VALID_RISK_CLASS and _RISK_ORDER.get(rc, 0) < _RISK_ORDER["medium"]:
            errors.append(
                "secrets_required=true requires risk_class >= 'medium' "
                f"(a resource using credentials is at least medium risk — got {rc!r})"
            )

    # migration_decision=migrate requires migration_target
    if md == "migrate":
        mt = entry.get("migration_target")
        if not isinstance(mt, str) or not mt.strip():
            errors.append(
                "migration_decision=migrate requires a non-empty migration_target"
            )

    # allowed_contexts and blocked_contexts must not overlap
    allowed = set(entry.get("allowed_contexts") or [])
    blocked = set(entry.get("blocked_contexts") or [])
    overlap = allowed & blocked
    if overlap:
        errors.append(
            f"allowed_contexts and blocked_contexts must not overlap (overlap: {sorted(overlap)})"
        )

    # Hash verification
    expected_hash = compute_entry_hash(entry)
    if entry.get("entry_hash") != expected_hash:
        errors.append("entry_hash does not match computed hash — entry may be tampered")

    return len(errors) == 0, errors


def create_registry_entry(
    *,
    resource_id: str,
    resource_type: str,
    resource_owner: str,
    namespace_status: str,
    install_authority: str,
    invoke_authority: str,
    risk_class: str,
    privacy_class: str,
    receipt_required: bool,
    last_reviewed_at: str,
    resource_name: str = "",
    source_registry: str = "",
    publish_authority: str = "disabled",
    allowed_contexts: list[str] | None = None,
    blocked_contexts: list[str] | None = None,
    secrets_required: bool = False,
    network_required: bool = False,
    discovery_receipts: list[str] | None = None,
    rejection_reason: str = "",
    admission_conditions: list[str] | None = None,
    migration_decision: str = "none",
    migration_target: str = "",
    reviewed_by: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Construct and validate an agent resource registry entry.

    Args:
        resource_id: Unique resource identifier (must start with 'res-').
        resource_type: Category of resource.
        resource_owner: Owner identity.
        namespace_status: candidate / admitted / rejected / retired.
        install_authority: Who may install.
        invoke_authority: Who may invoke.
        risk_class: Risk classification.
        privacy_class: Privacy classification.
        receipt_required: Whether discovery receipts are required.
        last_reviewed_at: ISO 8601 UTC timestamp of last review.
        resource_name: Human-readable name.
        source_registry: Where the resource was discovered.
        publish_authority: Who may publish/cite this resource.
        allowed_contexts: Contexts where the resource may be used.
        blocked_contexts: Contexts where the resource must NOT be used.
        secrets_required: Whether credentials are required.
        network_required: Whether network access is required.
        discovery_receipts: References to discovery receipts.
        rejection_reason: Reason for rejection/retirement.
        admission_conditions: Conditions before a candidate can be admitted.
        migration_decision: Migration decision for prompt-packed resources.
        migration_target: Target registry entry ID for migration.
        reviewed_by: Who performed the last review.
        notes: Additional context.

    Returns:
        A validated entry dict (with entry_hash appended).

    Raises:
        AgentResourceRegistryError: if validation fails.
    """
    entry: dict[str, Any] = {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "resource_owner": resource_owner,
        "namespace_status": namespace_status,
        "install_authority": install_authority,
        "invoke_authority": invoke_authority,
        "risk_class": risk_class,
        "privacy_class": privacy_class,
        "receipt_required": receipt_required,
        "last_reviewed_at": last_reviewed_at,
        "publish_authority": publish_authority,
        "secrets_required": secrets_required,
        "network_required": network_required,
        "migration_decision": migration_decision,
    }

    if resource_name:
        entry["resource_name"] = resource_name
    if source_registry:
        entry["source_registry"] = source_registry
    if allowed_contexts:
        entry["allowed_contexts"] = list(allowed_contexts)
    if blocked_contexts:
        entry["blocked_contexts"] = list(blocked_contexts)
    if discovery_receipts:
        entry["discovery_receipts"] = list(discovery_receipts)
    if rejection_reason:
        entry["rejection_reason"] = rejection_reason
    if admission_conditions:
        entry["admission_conditions"] = list(admission_conditions)
    if migration_target:
        entry["migration_target"] = migration_target
    if reviewed_by:
        entry["reviewed_by"] = reviewed_by
    if notes:
        entry["notes"] = notes

    entry["entry_hash"] = compute_entry_hash(entry)

    is_valid, errors = validate_registry_entry(entry)
    if not is_valid:
        raise AgentResourceRegistryError(
            "agent resource registry entry failed validation: " + "; ".join(errors)
        )

    return entry


def validate_registry_batch(
    entries: list[dict[str, Any]],
    *,
    known_agent_ids: set[str] | None = None,
    known_skill_names: set[str] | None = None,
    known_mcp_server_names: set[str] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a batch of registry entries for cross-entry and cross-registry collisions.

    #1687: Namespace audit — checks that resource_ids are unique within the
    batch and do not collide with existing agent IDs, skill names, or MCP
    server names. The ``res-`` prefix makes collisions unlikely, but this
    automates the check for admission workflows.

    Args:
        entries: List of registry entry dicts.
        known_agent_ids: Set of canonical agent IDs (from agent_identity.py).
        known_skill_names: Set of skill names (from .agents/skills/).
        known_mcp_server_names: Set of MCP server names (from session config).

    Returns:
        (is_valid, errors) — errors is empty if valid.
    """
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, entry in enumerate(entries):
        rid = entry.get("resource_id", "")

        # Cross-entry duplicate check
        if rid in seen_ids:
            errors.append(f"entry {i}: duplicate resource_id {rid!r}")
        seen_ids.add(rid)

        # Cross-registry collision checks (resource_id without 'res-' prefix
        # vs bare names in other registries — defensive, catches prefix-stripping
        # mistakes or future schema changes)
        bare = rid.removeprefix("res-") if rid.startswith("res-") else rid
        if known_agent_ids and bare in known_agent_ids:
            errors.append(
                f"entry {i}: resource_id {rid!r} collides with agent ID {bare!r}"
            )
        if known_skill_names and bare in known_skill_names:
            errors.append(
                f"entry {i}: resource_id {rid!r} collides with skill name {bare!r}"
            )
        if known_mcp_server_names and bare in known_mcp_server_names:
            errors.append(
                f"entry {i}: resource_id {rid!r} collides with MCP server name {bare!r}"
            )

    return len(errors) == 0, errors


# --- #1686: Discovery receipt schema ---

# Discovery receipt field validation sets (mirror the JSON Schema).
VALID_DISCOVERY_SOURCE = {
    "mcp-server-registry",
    "internal",
    "vertex-ai-extensions-catalog",
    "skill-registry",
    "tool-discovery",
    "manual",
    "other",
}
VALID_ADMISSION_DECISION = {"admit", "reject", "hold", "retire"}
VALID_REVIEWER = {"operator", "steward", "trusted", "active"}
VALID_EVIDENCE_KIND = {
    "url",
    "commit",
    "pr",
    "issue",
    "doc",
    "test",
    "log",
    "other",
}

ALLOWED_RECEIPT_FIELDS = {
    "receipt_id",
    "resource_id",
    "discovery_source",
    "evidence",
    "admission_decision",
    "reviewer",
    "timestamp",
    "notes",
    "rejection_reason",
    "receipt_hash",
}

# receipt_id must match ^dr-[a-z0-9-]+$
_RECEIPT_ID_RE = re.compile(r"^dr-[a-z0-9-]+$")


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_discovery_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a discovery receipt dict against the schema (#1686).

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    required = [
        "receipt_id",
        "resource_id",
        "discovery_source",
        "evidence",
        "admission_decision",
        "reviewer",
        "timestamp",
        "receipt_hash",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(receipt) - ALLOWED_RECEIPT_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    if errors:
        return False, errors

    rid = receipt["receipt_id"]
    if not _RECEIPT_ID_RE.match(rid):
        errors.append(f"receipt_id must match ^dr-[a-z0-9-]+$ (got {rid!r})")

    resource_id = receipt["resource_id"]
    if not _RESOURCE_ID_RE.match(resource_id):
        errors.append(f"resource_id must match ^res-[a-z0-9-]+$ (got {resource_id!r})")

    ds = receipt["discovery_source"]
    if ds not in VALID_DISCOVERY_SOURCE:
        errors.append(
            f"discovery_source must be one of {sorted(VALID_DISCOVERY_SOURCE)} (got {ds!r})"
        )

    decision = receipt["admission_decision"]
    if decision not in VALID_ADMISSION_DECISION:
        errors.append(
            f"admission_decision must be one of {sorted(VALID_ADMISSION_DECISION)} (got {decision!r})"
        )

    reviewer = receipt["reviewer"]
    if reviewer not in VALID_REVIEWER:
        errors.append(
            f"reviewer must be one of {sorted(VALID_REVIEWER)} (got {reviewer!r})"
        )

    # evidence must be a non-empty array of valid evidence objects
    evidence = receipt.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 1:
        errors.append("evidence must be a non-empty array")
    elif isinstance(evidence, list):
        for i, ev in enumerate(evidence):
            if not isinstance(ev, dict):
                errors.append(f"evidence[{i}] must be an object")
                continue
            ev_kind = ev.get("kind")
            if ev_kind not in VALID_EVIDENCE_KIND:
                errors.append(
                    f"evidence[{i}].kind must be one of {sorted(VALID_EVIDENCE_KIND)} (got {ev_kind!r})"
                )
            ev_ref = ev.get("ref")
            if not isinstance(ev_ref, str) or not ev_ref.strip():
                errors.append(f"evidence[{i}].ref must be a non-empty string")

    # rejection_reason required when decision is reject or retire
    if decision in ("reject", "retire"):
        rr = receipt.get("rejection_reason")
        if not isinstance(rr, str) or not rr.strip():
            errors.append(
                f"admission_decision={decision} requires a non-empty rejection_reason"
            )

    # timestamp must be valid ISO 8601
    ts = receipt["timestamp"]
    if not _is_valid_iso8601(ts):
        errors.append(f"timestamp must be a valid RFC3339 date-time (got {ts!r})")

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append(
            "receipt_hash does not match computed hash — receipt may be tampered"
        )

    return len(errors) == 0, errors


def create_discovery_receipt(
    *,
    receipt_id: str,
    resource_id: str,
    discovery_source: str,
    evidence: list[dict[str, str]],
    admission_decision: str,
    reviewer: str,
    timestamp: str,
    notes: str = "",
    rejection_reason: str = "",
) -> dict[str, Any]:
    """Construct and validate a discovery receipt (#1686).

    Args:
        receipt_id: Unique receipt identifier (must start with 'dr-').
        resource_id: The registry entry this receipt applies to.
        discovery_source: Where the resource was discovered.
        evidence: List of evidence objects ({kind, ref, note?}).
        admission_decision: admit / reject / hold / retire.
        reviewer: Who made the decision.
        timestamp: ISO 8601 UTC timestamp.
        notes: Optional context.
        rejection_reason: Required if decision is reject or retire.

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        AgentResourceRegistryError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id,
        "resource_id": resource_id,
        "discovery_source": discovery_source,
        "evidence": list(evidence),
        "admission_decision": admission_decision,
        "reviewer": reviewer,
        "timestamp": timestamp,
    }
    if notes:
        receipt["notes"] = notes
    if rejection_reason:
        receipt["rejection_reason"] = rejection_reason

    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    is_valid, errors = validate_discovery_receipt(receipt)
    if not is_valid:
        raise AgentResourceRegistryError(
            "discovery receipt failed validation: " + "; ".join(errors)
        )

    return receipt
