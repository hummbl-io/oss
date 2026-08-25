"""Tests for D7 (DOCTRINE_AMENDMENT) wiring into Kernel and DoctrineEngine.promote().

D7 requires that no invariant or doctrine amendment takes effect without
operator approval, evidence, and a recorded receipt. These tests verify:
1. Kernel.validate_doctrine_amendment() raises KernelPanic on ungated amendments.
2. DoctrineEngine.promote() enforces D7 when the artifact is an invariant amendment.
3. Non-amendment artifacts pass through promote() without D7 checks.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel import Kernel
from hummbl_governance.kernel.doctrine_engine import DoctrineEngine, Stage
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


def _make_kernel() -> Kernel:
    tmpdir = tempfile.mkdtemp(prefix="kernel_d7_")
    return Kernel.boot(state_dir=Path(tmpdir))


def _valid_amendment():
    return {
        "schema_version": "1.0.0",
        "amendment_id": "amd-001",
        "amendment_type": "add",
        "target_invariant": "K12",
        "amendment_status": "ratified",
        "description": "Add K12: Every agent action is auditable.",
        "authority": {
            "operator_approval": True,
            "approver_id": "operator-001",
        },
        "evidence": {
            "evidence_refs": ["ref-001", "ref-002"],
        },
        "review": {
            "reviewer_id": "reviewer-001",
            "review_outcome": "approved",
            "review_notes": "Approved with minor concerns.",
        },
        "receipt": {
            "receipt_hash": "abc123",
            "receipt_sequence": 42,
        },
    }


def _valid_operator_receipt():
    return {
        "receipt_id": "r-op-001",
        "receipt_hash": "hash-001",
        "action_type": "PROMOTE",
        "signature": "sig-001",
    }


class TestKernelValidateDoctrineAmendment:
    """Kernel.validate_doctrine_amendment() enforces D7."""

    def test_valid_amendment_passes(self):
        kernel = _make_kernel()
        kernel.validate_doctrine_amendment(_valid_amendment())

    def test_none_amendment_raises_kernel_panic(self):
        kernel = _make_kernel()
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_doctrine_amendment(None)
        assert exc.value.invariant == KernelInvariant.DOCTRINE
        assert "D7" in str(exc.value)

    def test_no_operator_approval_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_amendment()
        bad["authority"]["operator_approval"] = False
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_doctrine_amendment(bad)
        assert exc.value.invariant == KernelInvariant.DOCTRINE
        assert "operator_approval" in str(exc.value)

    def test_empty_approver_id_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_amendment()
        bad["authority"]["approver_id"] = ""
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_doctrine_amendment(bad)
        assert exc.value.invariant == KernelInvariant.DOCTRINE

    def test_no_evidence_refs_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_amendment()
        bad["evidence"]["evidence_refs"] = []
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_doctrine_amendment(bad)
        assert exc.value.invariant == KernelInvariant.DOCTRINE
        assert "evidence" in str(exc.value).lower()

    def test_no_receipt_hash_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_amendment()
        bad["receipt"]["receipt_hash"] = ""
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_doctrine_amendment(bad)
        assert exc.value.invariant == KernelInvariant.DOCTRINE
        assert "receipt" in str(exc.value).lower()


class TestDoctrineEnginePromoteD7Gate:
    """DoctrineEngine.promote() enforces D7 for invariant amendments."""

    def test_non_amendment_artifact_promotes_without_d7_check(self):
        """Regular artifacts (no amendment_type) skip the D7 gate."""
        engine = DoctrineEngine(Path(tempfile.mkdtemp(prefix="d7_")))
        artifact = {"name": "some-policy", "content": "policy text"}
        result = engine.promote(
            from_stage=Stage.PLAYGROUND,
            to_stage=Stage.SANDBOX,
            artifact=artifact,
            operator_receipt=_valid_operator_receipt(),
        )
        assert "promotion" in result

    def test_valid_amendment_artifact_promotes(self):
        """Amendment artifacts with proper gating promote successfully."""
        engine = DoctrineEngine(Path(tempfile.mkdtemp(prefix="d7_")))
        amendment = _valid_amendment()
        result = engine.promote(
            from_stage=Stage.PLAYGROUND,
            to_stage=Stage.SANDBOX,
            artifact=amendment,
            operator_receipt=_valid_operator_receipt(),
        )
        assert "promotion" in result

    def test_ungated_amendment_artifact_raises_kernel_panic(self):
        """Amendment artifacts without operator approval are blocked."""
        engine = DoctrineEngine(Path(tempfile.mkdtemp(prefix="d7_")))
        bad = _valid_amendment()
        bad["authority"]["operator_approval"] = False
        with pytest.raises(KernelPanic) as exc:
            engine.promote(
                from_stage=Stage.PLAYGROUND,
                to_stage=Stage.SANDBOX,
                artifact=bad,
                operator_receipt=_valid_operator_receipt(),
            )
        assert exc.value.invariant == KernelInvariant.DOCTRINE
        assert "D7" in str(exc.value)

    def test_amendment_without_evidence_raises_kernel_panic(self):
        """Amendment artifacts without evidence are blocked."""
        engine = DoctrineEngine(Path(tempfile.mkdtemp(prefix="d7_")))
        bad = _valid_amendment()
        bad["evidence"]["evidence_refs"] = []
        with pytest.raises(KernelPanic) as exc:
            engine.promote(
                from_stage=Stage.PLAYGROUND,
                to_stage=Stage.SANDBOX,
                artifact=bad,
                operator_receipt=_valid_operator_receipt(),
            )
        assert exc.value.invariant == KernelInvariant.DOCTRINE

    def test_amendment_without_receipt_raises_kernel_panic(self):
        """Amendment artifacts without receipt hash are blocked."""
        engine = DoctrineEngine(Path(tempfile.mkdtemp(prefix="d7_")))
        bad = _valid_amendment()
        bad["receipt"]["receipt_hash"] = ""
        with pytest.raises(KernelPanic) as exc:
            engine.promote(
                from_stage=Stage.PLAYGROUND,
                to_stage=Stage.SANDBOX,
                artifact=bad,
                operator_receipt=_valid_operator_receipt(),
            )
        assert exc.value.invariant == KernelInvariant.DOCTRINE


class TestD7BackwardCompatibility:
    """Existing Kernel methods still work after D7 wiring."""

    def test_create_receipt_still_works(self):
        kernel = _make_kernel()
        receipt = kernel.create_receipt("test-agent", "TEST_ACTION")
        assert receipt is not None

    def test_health_still_works(self):
        kernel = _make_kernel()
        health = kernel.health()
        assert health["booted"] is True

    def test_validate_rollback_still_works(self):
        """K9 wiring still works alongside D7 wiring."""
        kernel = _make_kernel()
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_rollback({})
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY
