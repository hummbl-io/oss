"""Evidence state tracking — the P1 constraint from the ARCANA peer review.

Every health-bearing record must carry an evidence_state field. A project
with zero scanner coverage must render as *unknown*, never *clean*. Absence
is the most exploitable signal: a project with no coverage appears cleaner
than one with full coverage and one real CVE. The system must not produce
the "missing data with safety" confusion the README warns against.
"""

from __future__ import annotations

from enum import Enum


class EvidenceState(str, Enum):
    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    ABSENT = "absent"
    CONTRADICTORY = "contradictory"


# The rendering rule: absent and contradictory never render as a positive
# health signal. This is the non-trivial logic — the rest of the enum is
# trivial. If this mapping is broken, the system produces the exact failure
# mode the README warns against.
_HEALTH_RENDER = {
    EvidenceState.SUFFICIENT: "supported",
    EvidenceState.PARTIAL: "partial",
    EvidenceState.ABSENT: "unknown",
    EvidenceState.CONTRADICTORY: "contested",
}


def render_health(state: EvidenceState) -> str:
    """Render an evidence state as a health label.

    ABSENT always renders as 'unknown', never 'clean' or 'healthy'.
    CONTRADICTORY always renders as 'contested', never 'clean' or 'healthy'.
    """
    if not isinstance(state, EvidenceState):
        raise TypeError(f"expected EvidenceState, got {type(state).__name__}")
    return _HEALTH_RENDER[state]
