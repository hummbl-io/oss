"""Tests for K9-K11 enforcement wiring in the Kernel.

K9 (REVERSIBILITY): Kernel.validate_rollback() raises KernelPanic on invalid declaration.
K10 (RECOVERY): Kernel.validate_recovery() raises KernelPanic on invalid verification.
K11 (INTEGRITY): Kernel.check_receipt_integrity() raises KernelPanic on sequence gaps / hash chain breaks.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel import Kernel
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


def _make_kernel() -> Kernel:
    """Create a booted Kernel with a temporary state directory."""
    tmpdir = tempfile.mkdtemp(prefix="kernel_k9k11_")
    return Kernel.boot(state_dir=Path(tmpdir))


def _valid_rollback_declaration():
    return {
        "schema_version": "1.0.0",
        "action_id": "act-001",
        "reversibility": "reversible",
        "rollback_plan": {
            "rollback_steps": [
                {
                    "step_id": "step-1",
                    "description": "Revert config file",
                    "estimated_duration_minutes": 5,
                    "data_loss": False,
                }
            ],
            "checkpoint_ref": "ckpt-001",
        },
        "authority": {"declared_by": "operator-001"},
        "receipt": {"receipt_hash": "abc123"},
    }


def _valid_recovery_verification():
    return {
        "schema_version": "1.0.0",
        "halt_event_id": "halt-001",
        "halt_source": "kill_switch",
        "root_cause_analysis": {
            "identified": True,
            "analysis_summary": "Memory exhaustion from unbounded queue",
            "root_cause_category": "resource_exhaustion",
            "fix_applied": True,
            "fix_description": "Added queue size limit and backpressure",
        },
        "evidence": {
            "evidence_refs": ["ref-001", "ref-002"],
            "test_results_ref": "tests/run-001",
            "health_check_ref": "health/probe-001",
        },
        "operator_approval": {
            "approved": True,
            "approver_id": "operator-001",
            "approval_timestamp": "2026-06-26T12:00:00Z",
            "conditions": ["monitor for 30 minutes"],
        },
        "receipt": {"receipt_hash": "abc123", "receipt_sequence": 42},
        "re_engagement_plan": {
            "strategy": "gradual",
            "monitoring_duration_minutes": 30,
            "rollback_on_failure": True,
        },
    }


class TestK9RollbackWiring:
    """K9 REVERSIBILITY: Kernel.validate_rollback() enforces rollback declarations."""

    def test_valid_rollback_passes(self):
        kernel = _make_kernel()
        # Should not raise
        kernel.validate_rollback(_valid_rollback_declaration())

    def test_invalid_rollback_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_rollback_declaration()
        bad["reversibility"] = "irreversible"
        bad.pop("rollback_plan", None)  # remove plan
        bad.pop("irreversibility_acceptance", None)  # missing acceptance
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_rollback(bad)
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY
        assert "K9" in str(exc.value)

    def test_schema_invalid_raises_kernel_panic(self):
        kernel = _make_kernel()
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_rollback({"schema_version": "1.0.0"})
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY

    def test_empty_declaration_raises_kernel_panic(self):
        kernel = _make_kernel()
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_rollback({})
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY


class TestK10RecoveryWiring:
    """K10 RECOVERY: Kernel.validate_recovery() enforces recovery verification."""

    def test_valid_recovery_passes(self):
        kernel = _make_kernel()
        # Should not raise
        kernel.validate_recovery(_valid_recovery_verification())

    def test_no_root_cause_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_recovery_verification()
        bad["root_cause_analysis"]["identified"] = False
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_recovery(bad)
        assert exc.value.invariant == KernelInvariant.RECOVERY
        assert "K10" in str(exc.value)

    def test_no_operator_approval_raises_kernel_panic(self):
        kernel = _make_kernel()
        bad = _valid_recovery_verification()
        bad["operator_approval"]["approved"] = False
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_recovery(bad)
        assert exc.value.invariant == KernelInvariant.RECOVERY

    def test_schema_invalid_raises_kernel_panic(self):
        kernel = _make_kernel()
        with pytest.raises(KernelPanic) as exc:
            kernel.validate_recovery({"schema_version": "1.0.0"})
        assert exc.value.invariant == KernelInvariant.RECOVERY


class TestK11IntegrityWiring:
    """K11 INTEGRITY: Kernel.check_receipt_integrity() enforces receipt integrity."""

    def test_no_receipts_returns_clean_report(self):
        """Agent with no receipts returns a clean report (no panic)."""
        kernel = _make_kernel()
        report = kernel.check_receipt_integrity("agent-001")
        assert report["panic_triggered"] is False
        assert report["check_results"]["sequence_check"]["passed"] is True
        assert report["check_results"]["hash_chain_check"]["passed"] is True

    def test_valid_receipts_no_panic(self):
        """A clean receipt chain does not raise KernelPanic.

        Note: SequenceEngine starts at 1, but the integrity monitor's
        check_sequence expects 0-based. The Kernel.check_receipt_integrity()
        method handles this by detecting the 1-based start and adjusting.
        """
        kernel = _make_kernel()

        # Create a few receipts (seq 1, 2, ...)
        r1 = kernel.create_receipt("test-agent", "TEST_ACTION_1")
        kernel.store_receipt(r1)
        r2 = kernel.create_receipt("test-agent", "TEST_ACTION_2")
        kernel.store_receipt(r2)

        # Should not raise — the Kernel method handles 1-based sequences
        report = kernel.check_receipt_integrity("test-agent")
        assert report["panic_triggered"] is False

    def test_sequence_gap_raises_kernel_panic(self):
        """A sequence gap in receipts triggers KernelPanic(K11)."""
        kernel = _make_kernel()

        # Create receipt with sequence 1 (boot creates seq 0)
        r1 = kernel.create_receipt("test-agent", "TEST_ACTION_1")
        kernel.store_receipt(r1)

        # Manually append a receipt with a sequence gap (skip seq 2, use seq 5)
        receipt_file = kernel.receipt.receipts_dir / "test-agent.jsonl"
        gap_receipt = {
            "receipt_id": "r-gap001",
            "agent_id": "test-agent",
            "sequence_id": 5,  # gap: 1 -> 5, missing 2-4
            "prev_receipt_hash": r1.compute_hash(),
            "timestamp": "2026-06-26T12:00:00Z",
            "action_type": "TEST_ACTION_2",
            "payload": {},
            "law_checks": [],
            "evidence_grade": "UNGRADED",
            "signature": "fake-sig",
        }
        with open(receipt_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(gap_receipt, sort_keys=True) + "\n")

        with pytest.raises(KernelPanic) as exc:
            kernel.check_receipt_integrity("test-agent")
        assert exc.value.invariant == KernelInvariant.INTEGRITY
        assert "K11" in str(exc.value)

    def test_hash_chain_break_raises_kernel_panic(self):
        """A broken hash chain triggers KernelPanic(K11)."""
        kernel = _make_kernel()

        r1 = kernel.create_receipt("test-agent", "TEST_ACTION_1")
        kernel.store_receipt(r1)

        # Append a receipt with wrong prev_receipt_hash
        receipt_file = kernel.receipt.receipts_dir / "test-agent.jsonl"
        broken_receipt = {
            "receipt_id": "r-broken001",
            "agent_id": "test-agent",
            "sequence_id": 2,  # correct sequence
            "prev_receipt_hash": "wrong-hash-value",
            "timestamp": "2026-06-26T12:00:01Z",
            "action_type": "TEST_ACTION_2",
            "payload": {},
            "law_checks": [],
            "evidence_grade": "UNGRADED",
            "signature": "fake-sig",
        }
        with open(receipt_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(broken_receipt, sort_keys=True) + "\n")

        with pytest.raises(KernelPanic) as exc:
            kernel.check_receipt_integrity("test-agent")
        assert exc.value.invariant == KernelInvariant.INTEGRITY
        assert "K11" in str(exc.value)


class TestK9K11BackwardCompatibility:
    """Existing Kernel methods still work after K9-K11 wiring."""

    def test_create_receipt_still_works(self):
        kernel = _make_kernel()
        receipt = kernel.create_receipt("test-agent", "TEST_ACTION")
        assert receipt is not None
        assert receipt.agent_id == "test-agent"

    def test_store_receipt_still_works(self):
        kernel = _make_kernel()
        receipt = kernel.create_receipt("test-agent", "TEST_ACTION")
        receipt_id = kernel.store_receipt(receipt)
        assert receipt_id is not None

    def test_check_authority_still_works(self):
        kernel = _make_kernel()
        # Should not raise even if authority check returns False
        check = kernel.check_authority("test-agent", "role-1", "some-authority")
        assert check is not None

    def test_health_still_works(self):
        kernel = _make_kernel()
        health = kernel.health()
        assert health["booted"] is True
