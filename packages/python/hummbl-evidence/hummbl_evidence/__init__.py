"""Shared evidence-state and two-party approval primitives for the HUMMBL fleet.

Extracted from hummbl-observatory so that both observatory (OSS adoption
intelligence) and hummbl-signal (public-signal intelligence) can import the
same governed-belief primitives without duplication.
"""

from hummbl_evidence.evidence_state import EvidenceState, render_health
from hummbl_evidence.approval import (
    Decision,
    ApprovalRecord,
    Proposable,
    enforce_two_party,
    approve,
)

__all__ = [
    "EvidenceState",
    "render_health",
    "Decision",
    "ApprovalRecord",
    "Proposable",
    "enforce_two_party",
    "approve",
]
__version__ = "0.1.0"
