"""BaseN tier classifier — governance policy as code.

Classifies every BaseN tool call into a governance tier:
  Tier 0: reads — no tuple emitted
  Tier 1: writes — EVIDENCE tuple only
  Tier 2: governed decisions — full (CONTRACT, DCT, EVIDENCE) tuple
  Tier 3: chains — hash-linked sequential tuples (IDP delegation flows)

This is hard-coded, not config. The classification IS the policy.
Every tier change goes through a PR with CI checks.

Reference: BASEN_DESIGN.md §3, decision_basen_architecture.md §Q8
Stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tier 0: reads — no governance tuple
# ---------------------------------------------------------------------------

_TIER_0_TOOLS: frozenset[str] = frozenset(
    {
        # Bus reads
        "bus_read",
        "bus_search",
        "bus_stats",
        "bus_agents",
        # Cognition reads
        "ledger_search",
        "ledger_query",
        "ledger_stats",
        "boot_context",
        "reindex",
        "memory_get",
        "memory_list",
        "memory_stats",
        "state_read",
        "state_summary",
        # Base120 reads
        "base120_get",
        "base120_list",
        "base120_families",
        "base120_select",
        # Service reads
        "fleet_status",
        "fleet_server_health",
        "fleet_report",
        "gateway_policy",
        "tracer_status",
        "tracer_recent",
        "tracer_stats",
        "idp_query_governance",
        # Observability reads
        "fleet_status",
        "agent_timeline",
        "bus_anomalies",
        "coordination_health",
        "session_summary",
        # Cost/health/trust reads
        "cost_budget",
        "cost_spend",
        "cost_decisions",
        "health_check",
        "health_probes",
        "health_history",
        "trust_score",
        "trust_history",
        "kill_switch_status",
        # Research/skills reads
        "research_query",
        "research_recent",
        "skill_list",
        "skill_get",
        "skill_search",
    }
)

# ---------------------------------------------------------------------------
# Tier 2: governed decisions — full (CONTRACT, DCT, EVIDENCE) tuple
# ---------------------------------------------------------------------------

_TIER_2_TOOLS: frozenset[str] = frozenset(
    {
        # IDP delegation lifecycle
        "idp_create_delegation",
        "idp_transition",
        "idp_submit_evidence",
        "idp_attest",
        # Gateway verdicts
        "gateway_evaluate",
        # Kill switch state changes
        "kill_switch_engage",
        "kill_switch_disengage",
        "kill_switch_set_mode",
        # Trust score mutations that cross thresholds
        "trust_update_score",
        # Server enable/disable (fleet management)
        "fleet_disable_server",
        "fleet_enable_server",
    }
)

# ---------------------------------------------------------------------------
# Tier 3: chain-linked (IDP delegation flows only)
# IDP tools where previous_hash should link to the prior tuple
# ---------------------------------------------------------------------------

_TIER_3_TOOLS: frozenset[str] = frozenset(
    {
        # These are Tier 2 tools that participate in chains.
        # A chain starts with idp_create_delegation and continues through
        # transition → submit_evidence → attest. The chain classifier
        # checks whether a previous tuple exists for the same task_id.
        # If so, it promotes from Tier 2 to Tier 3 automatically.
    }
)
# Note: Tier 3 promotion is contextual, not tool-based. See classify() below.


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


def classify(tool_name: str) -> int:
    """Classify a tool call into a governance tier.

    Args:
        tool_name: The MCP tool name (e.g., "bus_post", "idp_create_delegation")

    Returns:
        0, 1, 2, or 3

    Tier 3 is contextual — the same tool can be Tier 2 (first call) or Tier 3
    (subsequent call in a chain). This function returns 2 for potential chain
    tools; the caller promotes to 3 if a previous_hash is available.
    """
    if tool_name in _TIER_0_TOOLS:
        return 0
    if tool_name in _TIER_2_TOOLS:
        return 2
    # Everything else is Tier 1 (write with EVIDENCE only)
    return 1


def classify_with_context(
    tool_name: str,
    previous_hash: str | None = None,
) -> int:
    """Classify with chain context — promotes Tier 2 to Tier 3 if chained."""
    tier = classify(tool_name)
    if tier == 2 and previous_hash is not None:
        return 3
    return tier


def is_read(tool_name: str) -> bool:
    """Return True if the tool is a read-only operation (Tier 0)."""
    return tool_name in _TIER_0_TOOLS


def is_governed(tool_name: str) -> bool:
    """Return True if the tool requires full governance (Tier 2+)."""
    return tool_name in _TIER_2_TOOLS
