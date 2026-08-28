"""Source reliability and content credibility grading.

Implements the DoD-standard source reliability (A-F) and content
credibility (1-6) grading scales used in intelligence products.
Extended with agent-specific grading dimensions for automated
collection surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar


class SourceReliability(Enum):
    """DoD source reliability scale (A-F).

    Evaluates the TRUSTWORTHINESS of the source itself,
    independent of any single report.

    Source: JP 2-0, Appendix B.
    """

    A = "completely_reliable"
    """No doubt of authenticity, trustworthiness, or competency. History of complete reliability."""

    B = "usually_reliable"
    """Minor doubt. History of valid information most of the time."""

    C = "fairly_reliable"
    """Some doubt. History of valid information but not on all subjects."""

    D = "not_usually_reliable"
    """Significant doubt. History of valid information some of the time."""

    E = "unreliable"
    """Lacking authenticity, trustworthiness, or competency. History of invalid information."""

    F = "cannot_be_judged"
    """No basis exists for evaluating reliability. New or unproven source."""


class ContentCredibility(Enum):
    """DoD content credibility scale (1-6).

    Evaluates the CREDIBILITY of a specific piece of information,
    independent of the source's general reliability.

    Source: JP 2-0, Appendix B.
    """

    ONE = "confirmed"
    """Confirmed by other independent sources. Logical. Consistent with other information."""

    TWO = "probably_true"
    """Not confirmed. Logical. Consistent with other information."""

    THREE = "possibly_true"
    """Not confirmed. Reasonably logical. Agrees with some other information."""

    FOUR = "doubtfully_true"
    """Not confirmed. Possible but not logical. No other information on subject."""

    FIVE = "improbable"
    """Not confirmed. Not logical. Contradicted by other information."""

    SIX = "cannot_be_judged"
    """No basis exists for evaluating credibility. No other information on subject."""


# Human-readable labels
RELIABILITY_LABELS: dict[SourceReliability, str] = {
    SourceReliability.A: "A — Completely Reliable",
    SourceReliability.B: "B — Usually Reliable",
    SourceReliability.C: "C — Fairly Reliable",
    SourceReliability.D: "D — Not Usually Reliable",
    SourceReliability.E: "E — Unreliable",
    SourceReliability.F: "F — Cannot Be Judged",
}

CREDIBILITY_LABELS: dict[ContentCredibility, str] = {
    ContentCredibility.ONE: "1 — Confirmed",
    ContentCredibility.TWO: "2 — Probably True",
    ContentCredibility.THREE: "3 — Possibly True",
    ContentCredibility.FOUR: "4 — Doubtfully True",
    ContentCredibility.FIVE: "5 — Improbable",
    ContentCredibility.SIX: "6 — Cannot Be Judged",
}


@dataclass(frozen=True)
class SourceGrade:
    """A complete source grading pair as used in intelligence products.

    Format: "B/2" = Usually Reliable source, reporting Probably True information.
    """

    reliability: SourceReliability
    credibility: ContentCredibility

    def to_code(self) -> str:
        """Return the grading code string (e.g., 'B/2')."""
        cred_int = {
            ContentCredibility.ONE: 1,
            ContentCredibility.TWO: 2,
            ContentCredibility.THREE: 3,
            ContentCredibility.FOUR: 4,
            ContentCredibility.FIVE: 5,
            ContentCredibility.SIX: 6,
        }[self.credibility]
        return f"{self.reliability.name}/{cred_int}"

    def is_actionable(self) -> bool:
        """Whether this grade is sufficient for operational use.

        Actionable: source is at least C-reliable AND content is
        at least 3 (possibly true).
        """
        reliable = self.reliability in (
            SourceReliability.A,
            SourceReliability.B,
            SourceReliability.C,
        )
        credible = self.credibility in (
            ContentCredibility.ONE,
            ContentCredibility.TWO,
            ContentCredibility.THREE,
        )
        return reliable and credible


@dataclass(frozen=True)
class GradedAssertion:
    """A single piece of information with a source grading.

    Maps to one finding/insight/tclaim in the cognitive ledger.
    """

    content: str
    """The assertion being graded."""

    source: str
    """Identifier for the source (agent name, URL, filename)."""

    grade: SourceGrade
    """The reliability/credibility pair for this assertion."""

    discipline: str = ""
    """INT discipline this assertion originates from."""

    corroboration_count: int = 0
    """Number of independent sources confirming this assertion."""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "reliability": self.grade.reliability.name,
            "credibility": self.grade.credibility.value,
            "code": self.grade.to_code(),
            "discipline": self.discipline,
            "corroboration_count": self.corroboration_count,
            "timestamp": self.timestamp,
        }


def grade_human_source() -> SourceGrade:
    """Human operator sources default to A/2 (usually reliable human, probably true).

    Human DECISION posts are treated as high-reliability but not confirmed
    until corroborated by another source.
    """
    return SourceGrade(SourceReliability.A, ContentCredibility.TWO)


def grade_automated_source() -> SourceGrade:
    """Automated collection defaults to B/3 (usually reliable system, possibly true).

    Bus telemetry, SITREP loops, and automated scans are B-reliable by default
    but content needs confirmation from other sources.
    """
    return SourceGrade(SourceReliability.B, ContentCredibility.THREE)


def grade_research_source(peer_reviewed: bool = False) -> SourceGrade:
    """Research pipeline sources default to C/3 or B/3.

    Args:
        peer_reviewed: If True, upgrade to B/3. Otherwise C/3.
    """
    if peer_reviewed:
        return SourceGrade(SourceReliability.B, ContentCredibility.THREE)
    return SourceGrade(SourceReliability.C, ContentCredibility.THREE)


def grade_uncorroborated() -> SourceGrade:
    """New, unproven source — F/6 (cannot be judged).

    Used for first reports from emerging collection surfaces.
    """
    return SourceGrade(SourceReliability.F, ContentCredibility.SIX)


def upgrade_with_corroboration(
    grade: SourceGrade,
    num_independent: int,
) -> SourceGrade:
    """Upgrade a grading when corroborated by independent sources.

    Rules:
    - 2 independent confirmations: upgrade content one step (e.g., 3->2)
    - 3+ independent confirmations: upgrade reliability one step AND content to 1

    Args:
        grade: Current source grade.
        num_independent: Number of independent corroborating sources.

    Returns:
        Upgraded grade (never downgrades).
    """
    if num_independent < 2:
        return grade

    credibility = grade.credibility
    reliability = grade.reliability

    if num_independent >= 3:
        credibility = ContentCredibility.ONE

        # Upgrade reliability if possible
        reliability_map = {
            SourceReliability.F: SourceReliability.E,
            SourceReliability.E: SourceReliability.D,
            SourceReliability.D: SourceReliability.C,
            SourceReliability.C: SourceReliability.B,
            SourceReliability.B: SourceReliability.A,
            SourceReliability.A: SourceReliability.A,
        }
        reliability = reliability_map.get(reliability, reliability)
    elif num_independent == 2:
        # Upgrade content one step
        cred_map = {
            ContentCredibility.THREE: ContentCredibility.TWO,
            ContentCredibility.TWO: ContentCredibility.ONE,
        }
        credibility = cred_map.get(credibility, credibility)

    return SourceGrade(reliability, credibility)
