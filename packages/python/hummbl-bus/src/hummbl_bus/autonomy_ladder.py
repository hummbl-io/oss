"""Autonomy escalation ladder — Component 5 of PROPOSAL-012.

Maps agent actions to minimum autonomy tiers and enforces the ladder:

- **Tier 0** — Human Override: every action requires operator command.
- **Tier 1** — Shadow Mode: agent may read, query, and propose; waits for ACK.
- **Tier 2** — Supervised Autonomy: agent may write, edit, commit within scope;
  exceptions escalate to operator.
- **Tier 3** — Full Autonomy: agent may deploy, merge, and execute within mission
  parameters; operator reviews async.

All tier checks are advisory by default; set ``BUS_ENFORCE_AUTONOMY_TIER=1``
to raise on violations.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

TIER_LABELS = {
    0: "Human Override",
    1: "Shadow Mode",
    2: "Supervised Autonomy",
    3: "Full Autonomy",
}

# Action categories mapped to minimum required tier
_ACTION_TIER_MAP: dict[str, int] = {
    # Tier 0 only — human-only actions
    "kill_switch": 0,
    "emergency_stop": 0,
    "privileged_directive": 0,
    # Tier 1 — read/query/propose
    "read": 1,
    "query": 1,
    "status_check": 1,
    "propose": 1,
    "suggest": 1,
    "analyze": 1,
    "review": 1,
    # Tier 2 — write within scope
    "write": 2,
    "edit": 2,
    "commit": 2,
    "push": 2,
    "create_branch": 2,
    "test": 2,
    "lint": 2,
    "format": 2,
    "task_claim": 2,
    "task_complete": 2,
    # Tier 3 — execute autonomously
    "deploy": 3,
    "merge": 3,
    "delete": 3,
    "release": 3,
    "rollback": 3,
    "provision": 3,
    "destroy": 3,
}

# Wildcard patterns for actions not explicitly listed
_TIER_PATTERN_FALLBACK: list[tuple[str, int]] = [
    ("read_", 1),
    ("query_", 1),
    ("propose_", 1),
    ("write_", 2),
    ("edit_", 2),
    ("create_", 2),
    ("deploy_", 3),
    ("destroy_", 3),
]


def tier_label(tier: int) -> str:
    """Return human-readable label for a tier."""
    return TIER_LABELS.get(tier, f"Unknown({tier})")


def required_tier_for_action(action: str) -> int:
    """Return the minimum autonomy tier required to execute *action*.

    Args:
        action: Canonical action name (e.g. ``"commit"``, ``"deploy"``).

    Returns:
        Minimum tier (0–3). Unknown actions default to tier 3 (safest).
    """
    normalized = action.strip().lower()
    exact = _ACTION_TIER_MAP.get(normalized)
    if exact is not None:
        return exact
    for prefix, tier in _TIER_PATTERN_FALLBACK:
        if normalized.startswith(prefix):
            return tier
    return 3  # unknown = safest = full autonomy required


def can_execute(
    *,
    current_tier: int,
    action: str,
    from_id: str | None = None,
) -> bool:
    """Check whether *current_tier* permits *action*.

    Args:
        current_tier: Agent's current autonomy tier (0–3).
        action: Canonical action name.
        from_id: Optional sender identity for logging.

    Returns:
        ``True`` if permitted, ``False`` otherwise.
    """
    required = required_tier_for_action(action)
    permitted = current_tier >= required
    if not permitted:
        logger.warning(
            "Autonomy violation: %s (tier %d) attempted %r (requires tier %d)",
            from_id or "unknown",
            current_tier,
            action,
            required,
        )
    return permitted


def validate_action_tier(
    *,
    current_tier: int,
    action: str,
    from_id: str | None = None,
    enforce: bool = False,
) -> None:
    """Raise or warn when an action exceeds the current autonomy tier.

    Args:
        current_tier: Agent's current autonomy tier.
        action: Canonical action name.
        from_id: Optional sender identity for logging.
        enforce: If ``True``, raise ``PermissionError`` on violation.
    """
    required = required_tier_for_action(action)
    if current_tier >= required:
        return

    msg = (
        f"Action {action!r} requires autonomy tier {required} "
        f"({tier_label(required)}); current tier is {current_tier} "
        f"({tier_label(current_tier)})."
    )
    if enforce or _is_enforced("BUS_ENFORCE_AUTONOMY_TIER"):
        raise PermissionError(msg)
    logger.warning(msg)


def tier_transition_allowed(
    *,
    current_tier: int,
    target_tier: int,
    justification: str = "",
) -> bool:
    """Check whether a tier transition is allowed.

    Rules:
    - Promotion: always allowed with non-empty justification.
    - Demotion: always allowed (safety measure).
    - Same tier: always allowed.

    Args:
        current_tier: Current autonomy tier.
        target_tier: Desired autonomy tier.
        justification: Required for promotion; ignored for demotion.

    Returns:
        ``True`` if transition is allowed.
    """
    if target_tier <= current_tier:
        return True
    # Promotion requires justification
    if not justification or not justification.strip():
        logger.warning(
            "Tier promotion %d → %d rejected: missing justification",
            current_tier,
            target_tier,
        )
        return False
    return True


def actions_permitted_at_tier(tier: int) -> list[str]:
    """Return all actions permitted at or below *tier*.

    Args:
        tier: Autonomy tier (0–3).

    Returns:
        Sorted list of action names.
    """
    return sorted([a for a, t in _ACTION_TIER_MAP.items() if t <= tier])


def _is_enforced(env_var: str) -> bool:
    return os.environ.get(env_var, "").strip().lower() in {"1", "true", "yes", "on"}
