"""Foreground / background lane classifier for the coordination bus.

Component 2 of PROPOSAL-012: Autonomous Agent Orchestration.
Maps bus lanes and message types to foreground (operator-present, P0/P1)
or background (autonomous, P2/P3) work classes.
"""

from __future__ import annotations

import logging
import re

from hummbl_bus.message_types import CANONICAL_MESSAGE_TYPES

logger = logging.getLogger(__name__)

# Message types that are inherently foreground (review-gate, binding decisions)
_FOREGROUND_MESSAGE_TYPES = frozenset({
    "PROPOSAL",
    "REVIEW",
    "ACK",
    "VETO",
    "DECISION",
    "DIRECTIVE",
    "APPROVE",
    "REJECT",
    "HANDOFF",
    "WIP_START",
    "WIP_END",
    "QUESTION",
    "BLOCKED",
})

# Message types that are inherently background (reporting, monitoring, receipts)
_BACKGROUND_MESSAGE_TYPES = frozenset({
    "STATUS",
    "TASK_COMPLETE",
    "HEARTBEAT",
    "ALERT",
    "RECEIPT",
    "COMPLETE",
    "MILESTONE",
    "SITREP",
    "VERIFY",
    "HRSI_CHECKIN",
    "SKILL_INVOKE",
})

if _FOREGROUND_MESSAGE_TYPES | _BACKGROUND_MESSAGE_TYPES != CANONICAL_MESSAGE_TYPES:
    raise RuntimeError("lane classifier must classify every canonical bus type")

# Lane prefixes that default to background (unless overridden by priority)
_BACKGROUND_LANE_PREFIXES = (
    "audit/",
    "health/",
    "metrics/",
    "chore/",
    "auto-merge-gate/",
)

# Lane prefixes that default to foreground
_FOREGROUND_LANE_PREFIXES = (
    "adr/",
    "security/",
    "incident/",
    "review/",
    "merge/",
)

# Priority values that force foreground regardless of type
_FOREGROUND_PRIORITIES = frozenset({"P0", "P1"})
# Priority values that force background regardless of type
_BACKGROUND_PRIORITIES = frozenset({"P2", "P3"})

# Model tiers per PROPOSAL-012 Component 5
_TIER_FREE_LOCAL = frozenset({"T0", "T0-FREE", "T3-FREE", "ollama", "local"})
_TIER_LOW_COST = frozenset({"T1", "T1-LOW", "openrouter", "agy"})
_TIER_HIGH_STAKES = frozenset({"T2", "T2-ZEN", "T1-BYOK", "anthropic", "gpt-4", "opus", "haiku"})


def classify_message(msg_type: str, priority: str | None = None) -> str:
    """Classify a bus message as foreground or background.

    Args:
        msg_type: The bus message type (e.g. ``STATUS``, ``PROPOSAL``).
        priority: Optional priority tag (``P0``, ``P1``, ``P2``, ``P3``).

    Returns:
        ``"foreground"`` or ``"background"``.
    """
    mtype = msg_type.strip().upper()

    # Priority override takes precedence
    if priority is not None:
        p = priority.strip().upper()
        if p in _FOREGROUND_PRIORITIES:
            return "foreground"
        if p in _BACKGROUND_PRIORITIES:
            return "background"

    # Message type classification
    if mtype in _FOREGROUND_MESSAGE_TYPES:
        return "foreground"
    if mtype in _BACKGROUND_MESSAGE_TYPES:
        return "background"

    # Default: unknown types treated as foreground (safe default)
    logger.debug(
        "Unknown message type %r for lane classification; defaulting to foreground",
        mtype,
    )
    return "foreground"


def classify_lane(lane: str, msg_type: str, priority: str | None = None) -> str:
    """Classify a lane as foreground or background.

    Lane prefixes can bias the classification when priority is ambiguous
    (e.g. ``STATUS`` without explicit priority).

    Args:
        lane: The lane name (e.g. ``ops/codex/steward-watcher``).
        msg_type: The bus message type.
        priority: Optional priority tag.

    Returns:
        ``"foreground"`` or ``"background"``.
    """
    lane_clean = lane.strip().lower()

    # Priority is still the strongest signal
    if priority is not None:
        p = priority.strip().upper()
        if p in _FOREGROUND_PRIORITIES:
            return "foreground"
        if p in _BACKGROUND_PRIORITIES:
            return "background"

    # Lane prefix bias
    if lane_clean.startswith(_BACKGROUND_LANE_PREFIXES):
        return "background"
    if lane_clean.startswith(_FOREGROUND_LANE_PREFIXES):
        return "foreground"

    # Fall through to message-type classification
    return classify_message(msg_type, priority=None)


def is_foreground(msg_type: str, priority: str | None = None) -> bool:
    """Return True if the message/lane is foreground work."""
    return classify_message(msg_type, priority) == "foreground"


def is_background(msg_type: str, priority: str | None = None) -> bool:
    """Return True if the message/lane is background work."""
    return classify_message(msg_type, priority) == "background"


def _extract_tag(body: str, tag: str) -> str | None:
    """Extract ``tag=value`` from a bus message body."""
    pattern = rf"\b{re.escape(tag)}=([^;,\s]+)"
    match = re.search(pattern, body)
    if match:
        return match.group(1)
    return None


def classify_message_from_body(msg_type: str, body: str) -> str:
    """Classify using the raw message body (extracts lane= and priority=)."""
    priority = _extract_tag(body, "priority")
    lane = _extract_tag(body, "lane") or ""
    return classify_lane(lane, msg_type, priority)


def expected_model_tier(
    msg_type: str,
    priority: str | None = None,
    lane: str | None = None,
) -> str:
    """Return the expected model tier for a task.

    Per PROPOSAL-012 Component 5:
    - Background (P2/P3) → T0 (free/local)
    - Foreground non-review → T1 (low-cost)
    - Foreground review-gate or P0 → T2 (high-stakes)

    Returns:
        ``"T0"``, ``"T1"``, or ``"T2"``.
    """
    cls = classify_lane(lane or "", msg_type, priority)
    mtype = msg_type.strip().upper()

    if cls == "background":
        return "T0"

    # Foreground
    if mtype in {"PROPOSAL", "REVIEW", "ACK", "VETO", "DECISION", "APPROVE", "REJECT", "BLOCKED"}:
        return "T2"

    if priority is not None and priority.strip().upper() in _FOREGROUND_PRIORITIES:
        return "T2"

    return "T1"


def validate_model_tier_for_task(
    *,
    msg_type: str,
    body: str,
    enforce: bool = False,
) -> None:
    """Warn or raise if a task uses a model tier mismatched to its classification.

    Background tasks should use T0. Foreground review-gate tasks should use T2.
    """
    priority = _extract_tag(body, "priority")
    lane = _extract_tag(body, "lane") or ""
    declared_tier = _extract_tag(body, "model_tier") or _extract_tag(body, "tier")

    expected = expected_model_tier(msg_type, priority, lane)

    if declared_tier is None:
        # No tier declared — advisory only
        logger.debug(
            "No model_tier declared for %s (lane=%s); expected %s",
            msg_type,
            lane or "<none>",
            expected,
        )
        return

    dt = declared_tier.strip().upper()
    exp = expected.upper()

    # Allow T1 and T0 for background (T1 is acceptable escalation)
    if exp == "T0" and dt in _TIER_HIGH_STAKES:
        msg = (
            f"Background task {msg_type!r} (lane={lane or '<none>'}) "
            f"declares high-stakes model tier {dt!r}. Expected T0/T1. "
            f"Background work should use free/local models per PROPOSAL-012."
        )
        if enforce or _is_enforced("BUS_ENFORCE_TIER_ROUTING"):
            raise ValueError(msg)
        logger.warning(msg)
        return

    # Foreground review-gate should be T2 or at least T1
    if exp == "T2" and dt in _TIER_FREE_LOCAL:
        msg = (
            f"Foreground review-gate task {msg_type!r} (lane={lane or '<none>'}) "
            f"declares free/local tier {dt!r}. Expected T2 for binding verdicts."
        )
        if enforce or _is_enforced("BUS_ENFORCE_TIER_ROUTING"):
            raise ValueError(msg)
        logger.warning(msg)
        return

    logger.debug(
        "Model tier %s accepted for %s (expected %s)",
        dt,
        msg_type,
        exp,
    )


def _is_enforced(env_var: str) -> bool:
    import os

    return os.environ.get(env_var, "").strip().lower() in {"1", "true", "yes", "on"}
