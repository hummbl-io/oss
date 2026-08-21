"""Tests for D6/D7 wiring into the DoctrineEngine promotion gate.

D6 (CONTESTABILITY): open contests block stage promotion.
D7 (DOCTRINE_AMENDMENT): invariant changes require gated amendment record.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel.doctrine_engine import (
    DoctrineEngine,
    DoctrineInvariant,
    Stage,
)
from hummbl_governance.kernel.invariants import KernelPanic


def _make_engine() -> DoctrineEngine:
    return DoctrineEngine(state_dir=Path(tempfile.mkdtemp(prefix="doctrine_d6d7_")))


def _valid_receipt():
    return {
        "action_type": "PROMOTE",
        "receipt_id": "rc-001",
        "signature": "sig-001",
    }


def _valid_amendment():
    return {
        "schema_version": "1.0.0",
        "amendment_id": "am-001",
        "target_invariant": "K9",
        "amendment_type": "modify",
        "change_description": "Expand K9 scope",
        "amendment_status": "ratified",
        "authority": {
            "operator_approval": True,
            "approver_id": "operator-001",
        },
        "evidence": {
            "evidence_refs": ["incident-001"],
            "rationale": "K9 scope too narrow",
        },
        "receipt": {"receipt_hash": "am-hash-001"},
        "review": {
            "reviewer_id": "operator-001",
            "review_outcome": "approved",
        },
    }


# ===========================================================================
# D6: Open contests block promotion
# ===========================================================================


class TestD6OpenContestBlocksPromotion:
    """D6 CONTESTABILITY: open contests (flagged/under_review) block promotion."""

    def test_flagged_contest_blocks_promotion(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-001", "contest_status": "flagged"},
            ],
        )
        assert not result.valid
        assert result.invariant == DoctrineInvariant.CONTESTABILITY
        assert "ct-001" in result.detail

    def test_under_review_contest_blocks_promotion(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-002", "contest_status": "under_review"},
            ],
        )
        assert not result.valid
        assert result.invariant == DoctrineInvariant.CONTESTABILITY

    def test_upheld_contest_does_not_block(self):
        """Resolved contests (upheld/overturned/withdrawn) do not block."""
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-003", "contest_status": "upheld"},
            ],
        )
        assert result.valid

    def test_overturned_contest_does_not_block(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-004", "contest_status": "overturned"},
            ],
        )
        assert result.valid

    def test_withdrawn_contest_does_not_block(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-005", "contest_status": "withdrawn"},
            ],
        )
        assert result.valid

    def test_no_contests_allows_promotion(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=None,
        )
        assert result.valid

    def test_empty_contest_list_allows_promotion(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[],
        )
        assert result.valid

    def test_mixed_contests_with_one_open_blocks(self):
        """Even one open contest among resolved ones blocks promotion."""
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-006", "contest_status": "upheld"},
                {"contest_id": "ct-007", "contest_status": "flagged"},
                {"contest_id": "ct-008", "contest_status": "withdrawn"},
            ],
        )
        assert not result.valid
        assert "ct-007" in result.detail

    def test_multiple_open_contests_all_listed(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-a", "contest_status": "flagged"},
                {"contest_id": "ct-b", "contest_status": "under_review"},
            ],
        )
        assert not result.valid
        assert "ct-a" in result.detail
        assert "ct-b" in result.detail
        assert "2 open contest(s)" in result.detail


class TestD6AssertPromotionPanicsOnOpenContest:
    """assert_promotion_valid raises KernelPanic when open contests block."""

    def test_assert_panics_on_flagged_contest(self):
        engine = _make_engine()
        with pytest.raises(KernelPanic) as exc:
            engine.assert_promotion_valid(
                Stage.SANDBOX,
                Stage.INNOVATIONS,
                _valid_receipt(),
                open_contests=[
                    {"contest_id": "ct-001", "contest_status": "flagged"},
                ],
            )
        assert "D6" in str(exc.value)
        assert "CONTESTABILITY" in str(exc.value)

    def test_assert_does_not_panic_with_resolved_contests(self):
        engine = _make_engine()
        # Should not raise
        engine.assert_promotion_valid(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
            open_contests=[
                {"contest_id": "ct-001", "contest_status": "upheld"},
            ],
        )


class TestD6PromoteWithContests:
    """promote() passes open_contests through to validation."""

    def test_promote_blocked_by_open_contest(self):
        engine = _make_engine()
        with pytest.raises(KernelPanic):
            engine.promote(
                Stage.SANDBOX,
                Stage.INNOVATIONS,
                artifact={"id": "art-001"},
                operator_receipt=_valid_receipt(),
                open_contests=[
                    {"contest_id": "ct-001", "contest_status": "flagged"},
                ],
            )

    def test_promote_succeeds_with_resolved_contests(self):
        engine = _make_engine()
        result = engine.promote(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            artifact={"id": "art-001"},
            operator_receipt=_valid_receipt(),
            open_contests=[
                {"contest_id": "ct-001", "contest_status": "overturned"},
            ],
        )
        assert "promotion" in result


# ===========================================================================
# D7: Invariant changes require gated amendment record
# ===========================================================================


class TestD7ValidateInvariantChange:
    """D7 DOCTRINE_AMENDMENT: invariant changes require gated amendment."""

    def test_valid_amendment_passes(self):
        engine = _make_engine()
        result = engine.validate_invariant_change(_valid_amendment())
        assert result.valid

    def test_no_amendment_record_fails(self):
        """Ungated amendments are blocked — core D7 enforcement."""
        engine = _make_engine()
        result = engine.validate_invariant_change(None)
        assert not result.valid
        assert result.invariant == DoctrineInvariant.DOCTRINE_AMENDMENT
        assert "without an amendment record" in result.detail

    def test_no_operator_approval_fails(self):
        engine = _make_engine()
        a = _valid_amendment()
        a["authority"]["operator_approval"] = False
        result = engine.validate_invariant_change(a)
        assert not result.valid
        assert result.invariant == DoctrineInvariant.DOCTRINE_AMENDMENT
        assert "operator_approval must be True" in result.detail

    def test_empty_approver_id_fails(self):
        engine = _make_engine()
        a = _valid_amendment()
        a["authority"]["approver_id"] = ""
        result = engine.validate_invariant_change(a)
        assert not result.valid
        assert "approver_id" in result.detail

    def test_no_evidence_refs_fails(self):
        engine = _make_engine()
        a = _valid_amendment()
        a["evidence"]["evidence_refs"] = []
        result = engine.validate_invariant_change(a)
        assert not result.valid
        assert "evidence_refs" in result.detail

    def test_no_receipt_hash_fails(self):
        engine = _make_engine()
        a = _valid_amendment()
        a["receipt"] = {}
        result = engine.validate_invariant_change(a)
        assert not result.valid
        assert "receipt" in result.detail

    def test_missing_authority_fails(self):
        engine = _make_engine()
        a = _valid_amendment()
        del a["authority"]
        result = engine.validate_invariant_change(a)
        assert not result.valid
        assert "authority" in result.detail


class TestD7AssertInvariantChangeGated:
    """assert_invariant_change_gated raises KernelPanic on ungated amendment."""

    def test_assert_panics_on_no_record(self):
        engine = _make_engine()
        with pytest.raises(KernelPanic) as exc:
            engine.assert_invariant_change_gated(None)
        assert "D7" in str(exc.value)
        assert "DOCTRINE_AMENDMENT" in str(exc.value)

    def test_assert_panics_on_no_approval(self):
        engine = _make_engine()
        a = _valid_amendment()
        a["authority"]["operator_approval"] = False
        with pytest.raises(KernelPanic) as exc:
            engine.assert_invariant_change_gated(a)
        assert "D7" in str(exc.value)

    def test_assert_passes_on_valid_amendment(self):
        engine = _make_engine()
        # Should not raise
        engine.assert_invariant_change_gated(_valid_amendment())


class TestD7BackwardCompatibility:
    """Existing promote() calls without open_contests still work."""

    def test_promote_without_contests_arg_works(self):
        engine = _make_engine()
        result = engine.promote(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            artifact={"id": "art-001"},
            operator_receipt=_valid_receipt(),
        )
        assert "promotion" in result

    def test_validate_promotion_without_contests_works(self):
        engine = _make_engine()
        result = engine.validate_promotion(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
        )
        assert result.valid

    def test_assert_promotion_without_contests_works(self):
        engine = _make_engine()
        engine.assert_promotion_valid(
            Stage.SANDBOX,
            Stage.INNOVATIONS,
            _valid_receipt(),
        )
