"""INT taxonomy — canonical intelligence discipline definitions.

Maps the US DoD / ODNI collection discipline framework (JP 2-0)
to an agent-operational type system. Each INT is a first-class
enum member carrying: steward role, collection surface, and
reliability grading defaults.

Source: ODNI "What is Intelligence" (dni.gov) and JP 2-0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


class IntelligenceDiscipline(Enum):
    """Canonical DoD/ODNI intelligence collection disciplines."""

    SIGINT = "signals_intelligence"
    """Intercepted signals: COMINT, ELINT, FISINT. In agent terms: bus messages, SITREP loops, heartbeats, API telemetry."""

    HUMINT = "human_intelligence"
    """Human sources: DECISION posts, HRSI checkins, meeting captures, CRM pipeline. Highest-authority source."""

    OSINT = "open_source_intelligence"
    """Open/public information: web research, industry watch, evidence sweeps, documentation."""

    GEOINT = "geospatial_intelligence"
    """Activity on infrastructure: fleet mesh health, disk watcher, SSH monitoring, machine state."""

    MASINT = "measurement_and_signature_intelligence"
    """Physical/quantitative signatures: circuit breaker states, kill switch modes, test trends, mutation scores, performance baselines."""

    FININT = "financial_intelligence"
    """Monetary transactions: API spend, cost tracking, budget caps, runway forecasts."""

    TECHINT = "technical_intelligence"
    """Adversary tooling analysis: security scans, dependency audits, license checks, supply chain."""

    IMINT = "imagery_intelligence"
    """Visual representation: dashboards, charts, architecture diagrams, session renders."""

    ALL_SOURCE = "all_source_intelligence"
    """Fusion of multiple INTs: morning briefing, cognitive ledger synthesis, cross-session consolidation."""


# Human-readable labels for reporting
INT_LABELS: dict[IntelligenceDiscipline, str] = {
    IntelligenceDiscipline.SIGINT: "Signals Intelligence",
    IntelligenceDiscipline.HUMINT: "Human Intelligence",
    IntelligenceDiscipline.OSINT: "Open-Source Intelligence",
    IntelligenceDiscipline.GEOINT: "Geospatial Intelligence",
    IntelligenceDiscipline.MASINT: "Measurement & Signature Intelligence",
    IntelligenceDiscipline.FININT: "Financial Intelligence",
    IntelligenceDiscipline.TECHINT: "Technical Intelligence",
    IntelligenceDiscipline.IMINT: "Imagery Intelligence",
    IntelligenceDiscipline.ALL_SOURCE: "All-Source Intelligence",
}


@dataclass(frozen=True)
class CollectionSurface:
    """Describes what an INT discipline collects FROM.

    Maps the INT to concrete collection surfaces in an agent
    operating environment. Used by posture tracking to verify
    that each INT has active collection.
    """

    discipline: IntelligenceDiscipline
    surfaces: list[str] = field(default_factory=list)
    """Named collection surfaces (e.g., 'coordination_bus', 'github_api', 'ollama_telemetry')."""

    lead_agency: str = ""
    """DoD-equivalent lead for this INT (e.g., 'NSA' for SIGINT). In agent terms: the steward agent."""

    collection_frequency: str = "continuous"
    """Expected collection cadence: 'continuous', 'daily', 'on_demand'."""


# Canonical collection surfaces — the concrete sources mapped per INT.
CANONICAL_SURFACES: dict[IntelligenceDiscipline, CollectionSurface] = {
    IntelligenceDiscipline.SIGINT: CollectionSurface(
        discipline=IntelligenceDiscipline.SIGINT,
        surfaces=[
            "coordination_bus",
            "codex_steward_loop",
            "bus_auditor",
            "spoke_heartbeat",
            "agent_sitreps",
        ],
        lead_agency="bus-auditor",
        collection_frequency="continuous",
    ),
    IntelligenceDiscipline.HUMINT: CollectionSurface(
        discipline=IntelligenceDiscipline.HUMINT,
        surfaces=[
            "human_decisions",
            "hrsi_checkins",
            "meeting_captures",
            "crm_pipeline",
            "stakeholder_updates",
        ],
        lead_agency="human",
        collection_frequency="on_demand",
    ),
    IntelligenceDiscipline.OSINT: CollectionSurface(
        discipline=IntelligenceDiscipline.OSINT,
        surfaces=[
            "daily_research",
            "industry_watch",
            "overnight_research",
            "web_research",
            "evidence_sweeps",
        ],
        lead_agency="research-pipeline",
        collection_frequency="daily",
    ),
    IntelligenceDiscipline.GEOINT: CollectionSurface(
        discipline=IntelligenceDiscipline.GEOINT,
        surfaces=[
            "fleet_mesh_sitreps",
            "disk_watcher",
            "ssh_fleet_monitoring",
            "tailscale_status",
            "process_check",
        ],
        lead_agency="codex",
        collection_frequency="continuous",
    ),
    IntelligenceDiscipline.MASINT: CollectionSurface(
        discipline=IntelligenceDiscipline.MASINT,
        surfaces=[
            "circuit_breaker_states",
            "kill_switch_mode",
            "test_trends",
            "mutation_scores",
            "flake_hunter",
        ],
        lead_agency="devin",
        collection_frequency="continuous",
    ),
    IntelligenceDiscipline.FININT: CollectionSurface(
        discipline=IntelligenceDiscipline.FININT,
        surfaces=[
            "cost_tracker",
            "cost_governor_bridge",
            "budget_status",
            "runway_analysis",
            "api_usage_records",
        ],
        lead_agency="cost_governor",
        collection_frequency="daily",
    ),
    IntelligenceDiscipline.TECHINT: CollectionSurface(
        discipline=IntelligenceDiscipline.TECHINT,
        surfaces=[
            "bandit_scan",
            "semgrep_scan",
            "dependency_audit",
            "license_check",
            "supply_chain",
        ],
        lead_agency="security-adapter",
        collection_frequency="on_demand",
    ),
    IntelligenceDiscipline.IMINT: CollectionSurface(
        discipline=IntelligenceDiscipline.IMINT,
        surfaces=[
            "mission_control_dashboard",
            "session_render",
            "arch_diagrams",
            "state_briefings",
            "charts",
        ],
        lead_agency="dashboard-api",
        collection_frequency="on_demand",
    ),
    IntelligenceDiscipline.ALL_SOURCE: CollectionSurface(
        discipline=IntelligenceDiscipline.ALL_SOURCE,
        surfaces=[
            "morning_briefing",
            "cognitive_ledger",
            "memory_city_architecture",
            "cross_session_consolidation",
        ],
        lead_agency="claude-code",
        collection_frequency="daily",
    ),
}


def from_bus_prefix(tag: str) -> IntelligenceDiscipline | None:
    """Parse an INT tag from a bus message prefix.

    Expected format: [int=sigint] or [int=humint]

    Returns None if the tag is not recognized.
    """
    if not tag.startswith("[int=") or not tag.endswith("]"):
        return None
    key = tag[5:-1].upper()
    try:
        return IntelligenceDiscipline[key]
    except KeyError:
        return None


def get_surface(discipline: IntelligenceDiscipline) -> CollectionSurface:
    """Return the canonical collection surface definition for a discipline."""
    return CANONICAL_SURFACES.get(
        discipline,
        CollectionSurface(discipline=discipline),
    )


def list_disciplines() -> list[IntelligenceDiscipline]:
    """Return all intelligence disciplines in canonical order."""
    return list(IntelligenceDiscipline)
