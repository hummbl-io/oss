"""INT Manager role definitions.

In the DoD framework, each INT has a functional manager (e.g., NSA owns SIGINT,
NGA owns GEOINT). In the agent system, each INT is assigned a steward agent
responsible for collection posture, source reliability grading, and gap
reporting within their discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hummbl_intel.taxonomy import CANONICAL_SURFACES, IntelligenceDiscipline


@dataclass(frozen=True)
class INTManager:
    """Definition of a steward role for one intelligence discipline."""

    discipline: IntelligenceDiscipline
    """The INT this manager owns."""

    steward_agent: str
    """Canonical agent identity responsible for this INT."""

    duties: list[str] = field(default_factory=list)
    """Specific responsibilities of this steward."""

    reporting_cadence: str = "daily"
    """How often this steward reports posture."""

    escalation_agent: str = "claude-code"
    """Agent to escalate gaps to if steward cannot resolve."""


# Canonical INT Manager assignments per the Tier C build.
# These map agent identities to intelligence disciplines based on
# their existing operational scope and surface access.
CANONICAL_MANAGERS: tuple[INTManager, ...] = (
    INTManager(
        discipline=IntelligenceDiscipline.SIGINT,
        steward_agent="bus-auditor",
        duties=[
            "Monitor bus message health (parse errors, unknown senders)",
            "Track SITREP loop frequency and completeness",
            "Detect signal gaps (agent silence > threshold)",
            "Report SIGINT posture in daily steward SITREP",
        ],
        reporting_cadence="continuous",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.HUMINT,
        steward_agent="human",
        duties=[
            "Post DECISION messages for consequential choices",
            "Log HRSI checkins (belonging baseline)",
            "Capture meeting outcomes via meeting-capture skill",
            "Maintain CRM pipeline as HUMINT collection surface",
        ],
        reporting_cadence="on_demand",
        escalation_agent="human",  # Self-owned
    ),
    INTManager(
        discipline=IntelligenceDiscipline.OSINT,
        steward_agent="research-pipeline",
        duties=[
            "Run daily-research and overnight-research sweeps",
            "Grade ingested findings for source reliability",
            "Maintain evidence doc freshness",
            "Flag OSINT collection gaps (stale > 24h)",
        ],
        reporting_cadence="daily",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.GEOINT,
        steward_agent="codex",
        duties=[
            "Monitor fleet mesh health via steward loop",
            "Track disk watcher and SSH fleet monitoring",
            "Report fleet host status in SITREPs",
            "Escalate degraded machine status to ops",
        ],
        reporting_cadence="continuous",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.MASINT,
        steward_agent="devin",
        duties=[
            "Track circuit breaker state transitions",
            "Monitor kill switch engagement history",
            "Report test trends (pass rate, duration, flake rate)",
            "Maintain performance baselines for mutation scores",
        ],
        reporting_cadence="daily",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.FININT,
        steward_agent="cost-governor",
        duties=[
            "Track API spend vs budget via cost tracker",
            "Monitor runway projections",
            "Report budget DENY events and kill switch engagements",
            "Maintain cost records for audit trail",
        ],
        reporting_cadence="daily",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.TECHINT,
        steward_agent="security-adapter",
        duties=[
            "Run Bandit + Semgrep security scans on schedule",
            "Audit dependency health and license compliance",
            "Monitor supply chain for CVEs",
            "Report TECHINT posture (scan freshness, finding counts)",
        ],
        reporting_cadence="daily",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.IMINT,
        steward_agent="dashboard-api",
        duties=[
            "Maintain Mission Control dashboard health",
            "Ensure session-render and arch-diagram availability",
            "Report dashboard API + frontend status",
            "Maintain state briefing dual-format (MD + JSON)",
        ],
        reporting_cadence="daily",
    ),
    INTManager(
        discipline=IntelligenceDiscipline.ALL_SOURCE,
        steward_agent="claude-code",
        duties=[
            "Produce morning briefing as all-source fusion product",
            "Cross-correlate multi-INT findings",
            "Maintain cognitive ledger as all-source memory",
            "Host Memory City architecture as fusion framework",
            "Apply estimative probability language to key judgments",
        ],
        reporting_cadence="daily",
    ),
)


def get_manager(discipline: IntelligenceDiscipline) -> INTManager | None:
    """Return the canonical INT manager for a discipline."""
    for manager in CANONICAL_MANAGERS:
        if manager.discipline == discipline:
            return manager
    return None


def get_disciplines_for_agent(agent_id: str) -> list[IntelligenceDiscipline]:
    """Return all INT disciplines stewarded by a given agent."""
    return [
        m.discipline
        for m in CANONICAL_MANAGERS
        if m.steward_agent == agent_id
    ]


def manager_summary_table() -> str:
    """Produce a human-readable table of all INT manager assignments."""
    lines = [
        "| INT | Steward | Cadence | Escalation |",
        "|-----|---------|---------|------------|",
    ]
    for manager in CANONICAL_MANAGERS:
        int_name = manager.discipline.name
        lines.append(
            f"| {int_name} | {manager.steward_agent} | "
            f"{manager.reporting_cadence} | {manager.escalation_agent} |"
        )
    return "\n".join(lines)


def to_dict() -> list[dict[str, Any]]:
    """Export all manager definitions as dicts for JSON serialization."""
    return [
        {
            "discipline": m.discipline.value,
            "int_code": m.discipline.name,
            "steward_agent": m.steward_agent,
            "duties": m.duties,
            "reporting_cadence": m.reporting_cadence,
            "escalation_agent": m.escalation_agent,
        }
        for m in CANONICAL_MANAGERS
    ]
