"""Tests for hummbl_evidence.approval.

Ported from hummbl-observatory's intake approval tests to verify the
shared primitive preserves the P2 constraint: authorship and approval
must be separated, and decisions are typo-safe.
"""

from dataclasses import dataclass

import pytest

from hummbl_evidence.approval import (
    Decision,
    ApprovalRecord,
    Proposable,
    enforce_two_party,
    approve,
)
from hummbl_evidence.evidence_state import EvidenceState


@dataclass(frozen=True)
class _StubProposal:
    """Minimal Proposable for testing — satisfies the Protocol structurally."""
    proposed_by: str


class TestDecision:
    def test_two_values(self):
        assert Decision.APPROVED.value == "approved"
        assert Decision.REJECTED.value == "rejected"

    def test_is_str_enum(self):
        assert isinstance(Decision.APPROVED, str)
        assert Decision.APPROVED == "approved"


class TestApprovalRecord:
    def test_defaults(self):
        record = ApprovalRecord(
            approved_by="bob",
            approver_identity="sigstore:bob@example.com",
        )
        assert record.approved_by == "bob"
        assert record.decision is Decision.APPROVED
        assert record.evidence_state is EvidenceState.SUFFICIENT
        assert record.approved_at  # auto-generated

    def test_frozen(self):
        record = ApprovalRecord(
            approved_by="bob",
            approver_identity="sigstore:bob@example.com",
        )
        with pytest.raises(Exception):
            record.approved_by = "eve"  # type: ignore[misc]


class TestEnforceTwoParty:
    def test_different_parties_passes(self):
        enforce_two_party("alice", "bob")  # no exception

    def test_same_party_raises(self):
        with pytest.raises(ValueError, match="Two-party approval violated"):
            enforce_two_party("alice", "alice")

    def test_error_message_names_both_parties(self):
        with pytest.raises(ValueError, match="alice"):
            enforce_two_party("alice", "alice")


class TestApprove:
    def test_approve_returns_approval_record(self):
        proposal = _StubProposal(proposed_by="alice")
        approval = approve(proposal, approved_by="bob",
                           approver_identity="sigstore:bob@example.com")
        assert isinstance(approval, ApprovalRecord)
        assert approval.approved_by == "bob"
        assert approval.decision is Decision.APPROVED

    def test_two_party_approval_enforced(self):
        """The approver must not be the same person as the proposer."""
        proposal = _StubProposal(proposed_by="devin-agent")
        with pytest.raises(ValueError, match="Two-party approval violated"):
            approve(proposal, approved_by="devin-agent", approver_identity="stub")

    def test_decision_typo_rejected(self):
        """A free-form decision string (e.g. a typo) must not silently land."""
        proposal = _StubProposal(proposed_by="devin-agent")
        with pytest.raises(TypeError, match="expected Decision"):
            approve(proposal, approved_by="operator", approver_identity="stub",
                    decision="apporved")  # type: ignore[arg-type]

    def test_rejected_decision_lands(self):
        """Decision.REJECTED is a valid decision and lands on the record."""
        proposal = _StubProposal(proposed_by="devin-agent")
        approval = approve(proposal, approved_by="operator",
                           approver_identity="stub", decision=Decision.REJECTED)
        assert approval.decision is Decision.REJECTED
        assert approval.decision.value == "rejected"

    def test_proposable_protocol_satisfied_structurally(self):
        """_StubProposal satisfies Proposable without inheriting from it."""
        proposal = _StubProposal(proposed_by="alice")
        assert isinstance(proposal, Proposable)
