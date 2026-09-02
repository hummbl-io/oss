"""Collection posture tracking — per-INT health assessment.

Monitors each intelligence discipline's collection status:
freshness (last collection time), volume (message/event count),
and coverage (which surfaces are active vs dormant).

Produces posture reports consumable by the morning briefing
and by INT manager agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from hummbl_intel.taxonomy import CANONICAL_SURFACES, IntelligenceDiscipline


class PostureStatus(Enum):
    """Traffic-light status for a collection discipline."""

    GREEN = "green"
    """Active collection within expected cadence. All surfaces operational."""

    YELLOW = "yellow"
    """Collection active but degraded. Some surfaces stale or missing."""

    RED = "red"
    """Collection significantly degraded or absent. Requires intervention."""

    BLACK = "black"
    """No collection capability exists for this INT. Deliberate gap."""


@dataclass
class SurfaceStatus:
    """Status of a single collection surface."""

    name: str
    """Surface identifier (e.g., 'coordination_bus')."""

    active: bool = True
    """Whether this surface is currently collecting."""

    last_collection: datetime | None = None
    """Timestamp of most recent collection event."""

    event_count: int = 0
    """Number of collection events in the current window."""

    stale_threshold_hours: float = 24.0
    """Hours after which this surface is considered stale."""

    def is_stale(self, now: datetime | None = None) -> bool:
        """Check if this surface has exceeded its stale threshold.

        A surface with no collection data (last_collection=None)
        is NOT considered stale — it represents a surface that
        has never collected, not one that has gone silent.
        Only surfaces with actual collection timestamps age into staleness.
        """
        if self.last_collection is None:
            return False
        now = now or datetime.now(timezone.utc)
        age = now - self.last_collection
        return age > timedelta(hours=self.stale_threshold_hours)


@dataclass
class DisciplinePosture:
    """Complete posture assessment for one INT discipline."""

    discipline: IntelligenceDiscipline
    status: PostureStatus = PostureStatus.BLACK
    surfaces: list[SurfaceStatus] = field(default_factory=list)
    last_full_collection: datetime | None = None
    gap_notes: list[str] = field(default_factory=list)

    def active_surfaces(self) -> int:
        """Count of currently active (non-stale) surfaces."""
        now = datetime.now(timezone.utc)
        return sum(
            1 for s in self.surfaces if s.active and not s.is_stale(now)
        )

    def total_surfaces(self) -> int:
        """Total defined surfaces for this discipline."""
        return len(self.surfaces)

    def compute_status(self) -> PostureStatus:
        """Recompute posture status from surface states.

        Rules:
        - ALL surfaces active and fresh → GREEN
        - >50% surfaces active → YELLOW
        - <=50% surfaces active → RED
        - No surfaces defined → BLACK
        """
        if not self.surfaces:
            self.status = PostureStatus.BLACK
            return self.status

        active = self.active_surfaces()
        total = self.total_surfaces()

        if active == total:
            self.status = PostureStatus.GREEN
        elif active * 2 >= total:
            self.status = PostureStatus.YELLOW
        else:
            self.status = PostureStatus.RED

        return self.status


@dataclass
class CollectionPostureReport:
    """Aggregate posture report across all INT disciplines.

    Consumable by the morning briefing as a "Collection Posture" section.
    """

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    disciplines: dict[str, DisciplinePosture] = field(default_factory=dict)
    overall_status: PostureStatus = PostureStatus.BLACK

    def add_discipline(self, posture: DisciplinePosture) -> None:
        self.disciplines[posture.discipline.value] = posture

    def compute_overall(self) -> PostureStatus:
        """Compute fleet-wide posture from individual disciplines.

        Worst-status-wins rule: if any discipline is RED, overall is RED.
        If any YELLOW, overall YELLOW. Otherwise GREEN.
        """
        statuses = [d.status for d in self.disciplines.values()]
        if not statuses:
            self.overall_status = PostureStatus.BLACK
        elif any(s == PostureStatus.RED for s in statuses):
            self.overall_status = PostureStatus.RED
        elif any(s == PostureStatus.YELLOW for s in statuses):
            self.overall_status = PostureStatus.YELLOW
        else:
            self.overall_status = PostureStatus.GREEN
        return self.overall_status

    def to_summary_lines(self) -> list[str]:
        """Produce human-readable posture summary lines.

        Format: "SIGINT: GREEN (5/5 surfaces active, last: 2m ago)"
        """
        from hummbl_intel.taxonomy import INT_LABELS

        lines = []
        for disc in IntelligenceDiscipline:
            if disc == IntelligenceDiscipline.ALL_SOURCE:
                continue  # Skip all-source — it's fusion output, not collection
            posture = self.disciplines.get(disc.value)
            if posture is None:
                lines.append(
                    f"{INT_LABELS[disc]}: BLACK (no posture data)"
                )
                continue

            status = posture.status.value.upper()
            active = posture.active_surfaces()
            total = posture.total_surfaces()

            last_str = "never"
            if posture.last_full_collection:
                age = datetime.now(timezone.utc) - posture.last_full_collection
                mins = int(age.total_seconds() / 60)
                if mins < 60:
                    last_str = f"{mins}m ago"
                elif mins < 1440:
                    last_str = f"{mins // 60}h ago"
                else:
                    last_str = f"{mins // 1440}d ago"

            lines.append(
                f"{INT_LABELS[disc]}: {status} ({active}/{total} surfaces active, last: {last_str})"
            )

        return lines


def build_default_posture() -> CollectionPostureReport:
    """Build a posture report from canonical surface definitions.

    Initializes all INT disciplines with their canonical surfaces.
    Each surface starts with active=True and no collection data.
    Callers should populate last_collection and event_count from
    actual telemetry.
    """
    report = CollectionPostureReport()

    for discipline, surface_def in CANONICAL_SURFACES.items():
        if discipline == IntelligenceDiscipline.ALL_SOURCE:
            continue

        surfaces = [
            SurfaceStatus(
                name=name,
                active=True,
                stale_threshold_hours=(
                    1.0 if surface_def.collection_frequency == "continuous"
                    else 24.0 if surface_def.collection_frequency == "daily"
                    else 168.0  # weekly for on_demand
                ),
            )
            for name in surface_def.surfaces
        ]

        posture = DisciplinePosture(
            discipline=discipline,
            surfaces=surfaces,
        )
        posture.compute_status()
        report.add_discipline(posture)

    report.compute_overall()
    return report
