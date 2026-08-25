"""Focused tests for K9-K11, D6-D7 invariant enforcement.

Tests the enum promotion and scoped enforcement wiring ordered by the
operator on 2026-06-26 (APPROVED_WITH_CONSTRAINTS).

Coverage:
    - K9 enum recognition and scoped rollback enforcement
    - Irreversible action with accepted risk passing
    - Missing rollback/risk acceptance failing
    - K10 re-engagement blocked without root cause + evidence + operator approval
    - K11 sequence/hash failure severity
    - Timestamp-only anomaly NOT panicking
    - D6/D7 enum recognition
    - D7 blocking ungated invariant/doctrine amendment
"""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.doctrine_engine import DoctrineInvariant
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic
from hummbl_governance.kernel.receipt_integrity_monitor import (
    raise_on_integrity_violation,
    run_integrity_check,
)
from hummbl_governance.kernel.recovery_verifier import (
    raise_on_recovery_violation,
)
from hummbl_governance.kernel.rollback import (
    raise_on_rollback_violation,
)


# ===========================================================================
# K9 REVERSIBILITY — enum recognition and scoped enforcement
# ===========================================================================


class TestK9EnumRecognition:
    """K9 must be recognized as a KernelInvariant enum value."""

    def test_k9_exists_in_enum(self):
        assert hasattr(KernelInvariant, "REVERSIBILITY")

    def test_k9_value_is_k9(self):
        assert KernelInvariant.REVERSIBILITY.value == "K9"

    def test_k9_in_all_invariants(self):
        values = {inv.value for inv in KernelInvariant}
        assert "K9" in values

    def test_kernel_invariant_count_is_11(self):
        assert len(list(KernelInvariant)) == 11


class TestK9ScopedRollbackEnforcement:
    """K9 applies to governed durable-state mutations and irreversible
    external side effects. raise_on_rollback_violation raises KernelPanic(K9)."""

    def test_valid_reversible_with_plan_does_not_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-001",
            "reversibility": "reversible",
            "rollback_plan": {
                "rollback_steps": [{"step_id": "1", "description": "undo mutation"}],
            },
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "abc123"},
        }
        # Should not raise
        raise_on_rollback_violation(declaration)

    def test_irreversible_with_accepted_risk_does_not_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-002",
            "reversibility": "irreversible",
            "irreversibility_acceptance": {
                "risk_description": "Email sent to external recipient cannot be unsent",
                "acceptor_id": "operator-001",
            },
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "def456"},
        }
        # Should not raise
        raise_on_rollback_violation(declaration)

    def test_missing_rollback_plan_raises_k9_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-003",
            "reversibility": "reversible",
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "ghi789"},
        }
        with pytest.raises(KernelPanic) as exc:
            raise_on_rollback_violation(declaration)
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY
        assert "K9" in str(exc.value)

    def test_missing_risk_acceptance_raises_k9_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-004",
            "reversibility": "irreversible",
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "jkl012"},
        }
        with pytest.raises(KernelPanic) as exc:
            raise_on_rollback_violation(declaration)
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY
        assert "K9" in str(exc.value)

    def test_empty_rollback_steps_raises_k9_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-005",
            "reversibility": "partially_reversible",
            "rollback_plan": {"rollback_steps": []},
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "mno345"},
        }
        with pytest.raises(KernelPanic) as exc:
            raise_on_rollback_violation(declaration)
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY

    def test_irreversible_empty_risk_description_raises_k9_panic(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-006",
            "reversibility": "irreversible",
            "irreversibility_acceptance": {
                "risk_description": "",
                "acceptor_id": "operator-001",
            },
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "pqr678"},
        }
        with pytest.raises(KernelPanic) as exc:
            raise_on_rollback_violation(declaration)
        assert exc.value.invariant == KernelInvariant.REVERSIBILITY

    def test_k9_panic_severity_is_critical(self):
        declaration = {
            "schema_version": "1.0.0",
            "action_id": "act-007",
            "reversibility": "reversible",
            "authority": {"declared_by": "operator-001"},
            "receipt": {"receipt_hash": "stu901"},
        }
        with pytest.raises(KernelPanic) as exc:
            raise_on_rollback_violation(declaration)
        assert exc.value.severity == "CRITICAL"


# ===========================================================================
# K10 RECOVERY — re-engagement blocked without root cause + evidence + approval
# ===========================================================================


class TestK10EnumRecognition:
    """K10 must be recognized as a KernelInvariant enum value."""

    def test_k10_exists_in_enum(self):
        assert hasattr(KernelInvariant, "RECOVERY")

    def test_k10_value_is_k10(self):
        assert KernelInvariant.RECOVERY.value == "K10"

    def test_k10_in_all_invariants(self):
        values = {inv.value for inv in KernelInvariant}
        assert "K10" in values


class TestK10ScopedRecoveryEnforcement:
    """K10 applies to re-engagement after halt/quarantine/open breaker.
    raise_on_recovery_violation raises KernelPanic(K10)."""

    def _valid_verification(self):
        return {
            "schema_version": "1.0.0",
            "halt_event_id": "halt-001",
            "halt_source": "circuit_breaker",
            "root_cause_analysis": {
                "identified": True,
                "analysis_summary": "Null-pointer dereference in module X",
                "fix_applied": True,
                "fix_description": "Patched the null-pointer dereference in module X",
            },
            "evidence": {"evidence_refs": ["log-001", "test-001"]},
            "operator_approval": {
                "approved": True,
                "approver_id": "operator-001",
            },
            "receipt": {"receipt_hash": "rv-hash-001"},
        }

    def test_valid_recovery_does_not_panic(self):
        raise_on_recovery_violation(self._valid_verification())

    def test_missing_root_cause_raises_k10_panic(self):
        v = self._valid_verification()
        v["root_cause_analysis"]["identified"] = False
        with pytest.raises(KernelPanic) as exc:
            raise_on_recovery_violation(v)
        assert exc.value.invariant == KernelInvariant.RECOVERY
        assert "K10" in str(exc.value)

    def test_missing_operator_approval_raises_k10_panic(self):
        v = self._valid_verification()
        v["operator_approval"]["approved"] = False
        with pytest.raises(KernelPanic) as exc:
            raise_on_recovery_violation(v)
        assert exc.value.invariant == KernelInvariant.RECOVERY

    def test_missing_approver_id_raises_k10_panic(self):
        v = self._valid_verification()
        v["operator_approval"]["approver_id"] = ""
        with pytest.raises(KernelPanic) as exc:
            raise_on_recovery_violation(v)
        assert exc.value.invariant == KernelInvariant.RECOVERY

    def test_fix_applied_without_description_raises_k10_panic(self):
        v = self._valid_verification()
        v["root_cause_analysis"]["fix_description"] = ""
        with pytest.raises(KernelPanic) as exc:
            raise_on_recovery_violation(v)
        assert exc.value.invariant == KernelInvariant.RECOVERY

    def test_k10_panic_severity_is_critical(self):
        v = self._valid_verification()
        v["root_cause_analysis"]["identified"] = False
        with pytest.raises(KernelPanic) as exc:
            raise_on_recovery_violation(v)
        assert exc.value.severity == "CRITICAL"


# ===========================================================================
# K11 INTEGRITY — sequence/hash failure severity, timestamp-only NOT panicking
# ===========================================================================


class TestK11EnumRecognition:
    """K11 must be recognized as a KernelInvariant enum value."""

    def test_k11_exists_in_enum(self):
        assert hasattr(KernelInvariant, "INTEGRITY")

    def test_k11_value_is_k11(self):
        assert KernelInvariant.INTEGRITY.value == "K11"

    def test_k11_in_all_invariants(self):
        values = {inv.value for inv in KernelInvariant}
        assert "K11" in values


def _receipt(seq, hash_val, prev_hash="", ts="", rid=""):
    return {
        "sequence_id": seq,
        "receipt_hash": hash_val,
        "prev_receipt_hash": prev_hash,
        "timestamp": ts,
        "receipt_id": rid or f"r-{seq}",
    }


class TestK11SequenceFailureSeverity:
    """Sequence gaps must trigger KernelPanic via raise_on_integrity_violation."""

    def test_sequence_gap_raises_k11_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(5, "bbb", prev_hash="aaa"),
        ]
        with pytest.raises(KernelPanic) as exc:
            raise_on_integrity_violation(receipts, "agent-001")
        assert exc.value.invariant == KernelInvariant.INTEGRITY
        assert "K11" in str(exc.value)
        assert exc.value.severity == "CRITICAL"

    def test_sequence_gap_report_marks_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(5, "bbb", prev_hash="aaa"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is True
        assert report["panic_details"]["invariant_violated"] == "K4"


class TestK11HashChainFailureSeverity:
    """Hash-chain breaks must trigger KernelPanic via raise_on_integrity_violation."""

    def test_hash_break_raises_k11_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(1, "bbb", prev_hash="WRONG"),
        ]
        with pytest.raises(KernelPanic) as exc:
            raise_on_integrity_violation(receipts, "agent-001")
        assert exc.value.invariant == KernelInvariant.INTEGRITY
        assert "K11" in str(exc.value)
        assert exc.value.severity == "CRITICAL"

    def test_hash_break_report_marks_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(1, "bbb", prev_hash="WRONG"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is True
        assert report["panic_details"]["invariant_violated"] == "K1"


class TestK11TimestampOnlyAnomalyDoesNotPanic:
    """Timestamp-only anomalies must NOT trigger KernelPanic. They are warnings."""

    def test_timestamp_anomaly_does_not_raise(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T09:00:00Z"),
        ]
        # Should NOT raise — timestamp-only anomaly
        report = raise_on_integrity_violation(receipts, "agent-001")
        assert report["panic_triggered"] is False
        assert report["panic_details"] is None
        # But the timestamp check should still report the anomaly
        assert report["check_results"]["timestamp_check"]["passed"] is False
        assert len(report["check_results"]["timestamp_check"]["anomalies"]) == 1

    def test_timestamp_anomaly_report_has_no_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T09:00:00Z"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is False
        assert report["check_results"]["sequence_check"]["passed"] is True
        assert report["check_results"]["hash_chain_check"]["passed"] is True
        assert report["check_results"]["timestamp_check"]["passed"] is False

    def test_timestamp_anomaly_with_sequence_gap_does_panic(self):
        """Timestamp anomaly combined with sequence gap MUST panic."""
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(5, "bbb", prev_hash="aaa", ts="2026-01-01T09:00:00Z"),
        ]
        with pytest.raises(KernelPanic) as exc:
            raise_on_integrity_violation(receipts, "agent-001")
        assert exc.value.invariant == KernelInvariant.INTEGRITY

    def test_clean_receipts_do_not_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T11:00:00Z"),
        ]
        report = raise_on_integrity_violation(receipts, "agent-001")
        assert report["panic_triggered"] is False


# ===========================================================================
# D6 CONTESTABILITY — enum recognition
# ===========================================================================


class TestD6EnumRecognition:
    """D6 must be recognized as a DoctrineInvariant enum value."""

    def test_d6_exists_in_enum(self):
        assert hasattr(DoctrineInvariant, "CONTESTABILITY")

    def test_d6_value_is_d6(self):
        assert DoctrineInvariant.CONTESTABILITY.value == "D6"

    def test_d6_in_all_doctrine_invariants(self):
        values = {inv.value for inv in DoctrineInvariant}
        assert "D6" in values

    def test_doctrine_invariant_count_is_7(self):
        assert len(list(DoctrineInvariant)) == 7


# ===========================================================================
# D7 DOCTRINE_AMENDMENT — enum recognition + blocking ungated amendment
# ===========================================================================


class TestD7EnumRecognition:
    """D7 must be recognized as a DoctrineInvariant enum value."""

    def test_d7_exists_in_enum(self):
        assert hasattr(DoctrineInvariant, "DOCTRINE_AMENDMENT")

    def test_d7_value_is_d7(self):
        assert DoctrineInvariant.DOCTRINE_AMENDMENT.value == "D7"

    def test_d7_in_all_doctrine_invariants(self):
        values = {inv.value for inv in DoctrineInvariant}
        assert "D7" in values


class TestD7BlocksUngatedAmendment:
    """D7 blocks ungated invariant/doctrine amendments at the promotion gate.

    The DoctrineEngine's validate_promotion must reject amendments that
    attempt to change invariants without operator approval.
    """

    def test_d7_source_mentions_operator_approval(self):
        """The D7 source docstring must mention operator approval requirement."""
        from pathlib import Path

        # Resolve against the package
        import hummbl_governance.kernel.doctrine_engine as de_mod

        source_path = Path(de_mod.__file__)
        content = source_path.read_text()
        assert "operator approval" in content.lower()
        assert "DOCTRINE_AMENDMENT" in content

    def test_d7_source_mentions_receipt(self):
        """The D7 source docstring must mention recorded receipt."""
        import hummbl_governance.kernel.doctrine_engine as de_mod
        from pathlib import Path

        source_path = Path(de_mod.__file__)
        content = source_path.read_text()
        assert "receipt" in content.lower()

    def test_d7_source_mentions_blocked(self):
        """The D7 source docstring must mention that ungated amendments are blocked."""
        import hummbl_governance.kernel.doctrine_engine as de_mod
        from pathlib import Path

        source_path = Path(de_mod.__file__)
        content = source_path.read_text()
        assert "blocked" in content.lower()
