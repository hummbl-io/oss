"""Two-party approval primitives — the P2 constraint from the ARCANA peer review.

Authorship and approval must be separated. The human who drafts a provenance
record must not sign the approval. Two-party review with independent signing.

This module provides the shared enforcement logic so that any domain record
(OSS intake, feed admission, warrant approval) can reuse the same governance
primitive without duplicating the author!=approver check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol, runtime_checkable

from hummbl_evidence.evidence_state import EvidenceState


class Decision(str, Enum):
    """Approval decision — constrained so a typo cannot silently land."""
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ApprovalRecord:
    """Provenance record for a two-party approval event.

    Frozen so the approval cannot be mutated after signing — the record is
    the artifact that proves the governance step was completed.
    """
    approved_by: str
    approver_identity: str  # stub for Sigstore identity
    approved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: Decision = Decision.APPROVED
    evidence_state: EvidenceState = EvidenceState.SUFFICIENT


@runtime_checkable
class Proposable(Protocol):
    """Structural protocol: anything with a ``proposed_by`` attribute.

    Domain records (IntakeProposal, FeedSource, etc.) satisfy this
    implicitly via structural typing — no import or inheritance required.
    """

    proposed_by: str


def enforce_two_party(proposed_by: str, approved_by: str) -> None:
    """Raise ValueError if the approver is the same person as the proposer.

    This is the core governance invariant: authorship and approval must be
    separated. Call this directly when the domain record's proposer field
    has a non-standard name (e.g. ``admission_proposed_by``).
    """
    if approved_by == proposed_by:
        raise ValueError(
            f"Two-party approval violated: approver '{approved_by}' is the same "
            f"person as proposer '{proposed_by}'. "
            f"Authorship and approval must be separated."
        )


def approve(
    proposable: Proposable,
    approved_by: str,
    approver_identity: str,
    decision: Decision = Decision.APPROVED,
) -> ApprovalRecord:
    """Two-party approval — the approver must differ from the proposer.

    Returns an :class:`ApprovalRecord`. The caller is responsible for
    assigning it to the appropriate field on their domain record.

    Raises :class:`TypeError` if ``decision`` is not a :class:`Decision`
    (guards against typos like ``"apporved"`` silently landing as a
    free-form string).

    Raises :class:`ValueError` if the approver is the same person as the
    proposer (two-party violation).
    """
    if not isinstance(decision, Decision):
        raise TypeError(f"expected Decision, got {type(decision).__name__}")
    enforce_two_party(proposable.proposed_by, approved_by)
    return ApprovalRecord(
        approved_by=approved_by,
        approver_identity=approver_identity,
        decision=decision,
    )
