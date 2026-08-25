"""Cost-optimized inference tier router and cost estimator.

Component 4 of PROPOSAL-012: Autonomous Agent Orchestration.

Enforces the tier policy:
- **T0** (Free/Local): default for all background tasks.
- **T1** (Low-cost): escalate only for tasks requiring >7B parameters.
- **T2** (High-stakes): escalate only for review-gate verdicts or P0 analysis.

Every escalation above the baseline tier MUST include a justification.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Approximate cost per 1K tokens (input + output blended) in USD
_COST_PER_1K_TOKENS: dict[str, float] = {
    "T0": 0.0,
    "T1": 0.001,  # OpenRouter paid / GCP ~$0.001/1K
    "T2": 0.05,   # Anthropic Haiku/GPT-4 blended ~$0.01–$0.10/1K
}

# Baseline tier for any task without explicit justification
_BASELINE_TIER = "T0"

# Escalation rules
_TIER_ESCALATION_RULES: dict[str, dict[str, str]] = {
    "T1": {
        "trigger": "task_requires_7b_plus",
        "description": "Task requires model >7B parameters",
    },
    "T2": {
        "trigger": "review_gate_or_p0",
        "description": "Review-gate verdict or P0 analysis",
    },
}

# Keywords that indicate a task likely needs >7B parameters
_7B_TRIGGER_KEYWORDS = (
    "deep reasoning",
    "code generation",
    "complex analysis",
    "architecture design",
    "security review",
    "threat model",
    "formal verification",
    "mathematical proof",
    "long context",
    "128k",
    "200k",
)


def baseline_tier() -> str:
    """Return the default tier for all tasks."""
    return _BASELINE_TIER


def recommended_tier(
    *,
    msg_type: str,
    priority: str | None = None,
    description: str = "",
    requires_large_model: bool = False,
) -> str:
    """Recommend the cheapest viable tier for a task.

    Args:
        msg_type: Bus message type (e.g. ``STATUS``, ``REVIEW``).
        priority: Optional ``P0``/``P1``/``P2``/``P3``.
        description: Task description text scanned for complexity signals.
        requires_large_model: Explicit flag from caller.

    Returns:
        ``"T0"``, ``"T1"``, or ``"T2"``.
    """
    mtype = msg_type.strip().upper()
    desc_lower = description.lower()

    # T2: review-gate types or P0
    if mtype in {"PROPOSAL", "REVIEW", "ACK", "VETO", "DECISION", "APPROVE", "REJECT", "BLOCKED"}:
        return "T2"
    if priority is not None and priority.strip().upper() in {"P0", "P1"}:
        return "T2"

    # T1: large model required or complexity signals
    if requires_large_model:
        return "T1"
    if any(kw in desc_lower for kw in _7B_TRIGGER_KEYWORDS):
        return "T1"

    # T0: default
    return "T0"


def escalate_tier(
    current_tier: str,
    target_tier: str,
    justification: str,
) -> str:
    """Escalate a task to a higher tier with mandatory justification.

    Args:
        current_tier: The task's currently assigned tier.
        target_tier: The desired higher tier.
        justification: One-line reason for escalation.

    Returns:
        The target tier if justification is non-empty.

    Raises:
        ValueError: If trying to escalate without justification, or if
            target_tier is not higher than current_tier.
    """
    order = {"T0": 0, "T1": 1, "T2": 2}
    cur = order.get(current_tier.upper(), -1)
    tgt = order.get(target_tier.upper(), -1)

    if tgt <= cur:
        raise ValueError(
            f"Escalation requires target tier > current tier. "
            f"Got {target_tier!r} <= {current_tier!r}."
        )

    if not justification or not justification.strip():
        raise ValueError(
            f"Escalation from {current_tier!r} to {target_tier!r} requires "
            f"a non-empty justification per PROPOSAL-012 Component 4."
        )

    logger.info(
        "Tier escalation: %s → %s | justification: %s",
        current_tier,
        target_tier,
        justification,
    )
    return target_tier


def estimate_cost(
    tier: str,
    input_tokens: int = 1000,
    output_tokens: int = 500,
) -> float:
    """Estimate cost in USD for a single inference call.

    Args:
        tier: ``T0``/``T1``/``T2``.
        input_tokens: Estimated prompt size.
        output_tokens: Estimated response size.

    Returns:
        Estimated USD cost.
    """
    t = tier.strip().upper()
    rate = _COST_PER_1K_TOKENS.get(t, 0.0)
    total_tokens = input_tokens + output_tokens
    return (total_tokens / 1000.0) * rate


def validate_tier_escalation(
    *,
    msg_type: str,
    body: str,
    enforce: bool = False,
) -> None:
    """Warn or raise when a bus post uses a tier above the recommended baseline.

    Looks for ``model_tier=`` and ``tier_justification=`` in the message body.
    """
    declared_tier = _extract_tag(body, "model_tier") or _extract_tag(body, "tier")
    if declared_tier is None:
        # No tier declared — nothing to validate
        return

    priority = _extract_tag(body, "priority")
    desc = _extract_tag(body, "desc") or body

    recommended = recommended_tier(
        msg_type=msg_type,
        priority=priority,
        description=desc,
    )

    dt = declared_tier.strip().upper()
    rec = recommended.upper()

    order = {"T0": 0, "T1": 1, "T2": 2}
    declared_ord = order.get(dt, 99)
    rec_ord = order.get(rec, 99)

    if declared_ord <= rec_ord:
        # Tier is at or below recommendation — acceptable
        return

    # Tier is above recommendation — check for justification
    justification = _extract_tag(body, "tier_justification") or _extract_tag(body, "justification")
    if justification and justification.strip():
        logger.info(
            "Tier escalation accepted for %s: %s → %s | justification: %s",
            msg_type,
            rec,
            dt,
            justification,
        )
        return

    msg = (
        f"Tier {dt!r} for {msg_type!r} exceeds recommended {rec!r}. "
        f"Escalation requires tier_justification= in message body per PROPOSAL-012 Component 4."
    )
    if enforce or _is_enforced("BUS_ENFORCE_TIER_JUSTIFICATION"):
        raise ValueError(msg)
    logger.warning(msg)


def _extract_tag(body: str, tag: str) -> str | None:
    """Extract ``tag=value`` from a bus message body."""
    pattern = rf"\b{re.escape(tag)}=([^;,\s]+)"
    match = re.search(pattern, body)
    if match:
        return match.group(1)
    return None


def _is_enforced(env_var: str) -> bool:
    import os

    return os.environ.get(env_var, "").strip().lower() in {"1", "true", "yes", "on"}
