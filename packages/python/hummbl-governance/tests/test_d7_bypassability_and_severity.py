"""Tests for D7 bypassability fix — multi-signal invariant amendment detection."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.doctrine_engine import DoctrineEngine, Stage
from hummbl_governance.kernel.invariants import KernelPanic
from pathlib import Path


@pytest.fixture
def engine(tmp_path: Path) -> DoctrineEngine:
    return DoctrineEngine(state_dir=tmp_path)


def _valid_operator_receipt() -> dict:
    return {
        "action_type": "PROMOTE",
        "receipt_id": "rc-001",
        "signature": "test-sig",
    }


class TestD7BypassabilityFix:
    """D7 should detect invariant amendments via multiple signals, not just
    the amendment_type field."""

    def test_amendment_type_still_detected(self, engine: DoctrineEngine, tmp_path: Path):
        """Original signal: amendment_type field present."""
        artifact = {
            "amendment_type": "modify",
            "target_invariant": "K1",
            "authority": {"operator_approval": False, "approver_id": ""},
            "evidence": {"evidence_refs": []},
            "receipt": {},
        }
        with pytest.raises(KernelPanic, match="D7"):
            engine.promote(
                Stage.INNOVATIONS, Stage.FLEET, artifact,
                operator_receipt=_valid_operator_receipt(),
            )

    def test_target_invariant_field_detected(self, engine: DoctrineEngine, tmp_path: Path):
        """Content-based signal: target_invariant field present, no amendment_type."""
        artifact = {
            "target_invariant": "K1",
            "authority": {"operator_approval": False, "approver_id": ""},
            "evidence": {"evidence_refs": []},
            "receipt": {},
        }
        with pytest.raises(KernelPanic, match="D7"):
            engine.promote(
                Stage.INNOVATIONS, Stage.FLEET, artifact,
                operator_receipt=_valid_operator_receipt(),
            )

    def test_invariant_change_field_detected(self, engine: DoctrineEngine, tmp_path: Path):
        """Content-based signal: invariant_change field."""
        artifact = {
            "invariant_change": "K1 modification",
            "authority": {"operator_approval": False, "approver_id": ""},
            "evidence": {"evidence_refs": []},
            "receipt": {},
        }
        with pytest.raises(KernelPanic, match="D7"):
            engine.promote(
                Stage.INNOVATIONS, Stage.FLEET, artifact,
                operator_receipt=_valid_operator_receipt(),
            )

    def test_path_based_detection_invariants_py(self, engine: DoctrineEngine, tmp_path: Path):
        """Path-based signal: target_path contains invariants.py."""
        artifact = {
            "target_path": "hummbl_governance/kernel/invariants.py",
            "authority": {"operator_approval": False, "approver_id": ""},
            "evidence": {"evidence_refs": []},
            "receipt": {},
        }
        with pytest.raises(KernelPanic, match="D7"):
            engine.promote(
                Stage.INNOVATIONS, Stage.FLEET, artifact,
                operator_receipt=_valid_operator_receipt(),
            )

    def test_path_based_detection_doctrine_engine(self, engine: DoctrineEngine, tmp_path: Path):
        """Path-based signal: file_path contains doctrine_engine.py."""
        artifact = {
            "file_path": "kernel/doctrine_engine.py",
            "authority": {"operator_approval": False, "approver_id": ""},
            "evidence": {"evidence_refs": []},
            "receipt": {},
        }
        with pytest.raises(KernelPanic, match="D7"):
            engine.promote(
                Stage.INNOVATIONS, Stage.FLEET, artifact,
                operator_receipt=_valid_operator_receipt(),
            )

    def test_non_invariant_artifact_not_flagged(self, engine: DoctrineEngine, tmp_path: Path):
        """A regular artifact without invariant markers should not trigger D7."""
        artifact = {"name": "regular feature", "description": "not an amendment"}
        result = engine.promote(
            Stage.INNOVATIONS, Stage.FLEET, artifact,
            operator_receipt=_valid_operator_receipt(),
        )
        assert "promotion" in result

    def test_is_invariant_amendment_amendment_type(self, engine: DoctrineEngine):
        assert engine._is_invariant_amendment({"amendment_type": "modify"})

    def test_is_invariant_amendment_target_invariant(self, engine: DoctrineEngine):
        assert engine._is_invariant_amendment({"target_invariant": "K1"})

    def test_is_invariant_amendment_path(self, engine: DoctrineEngine):
        assert engine._is_invariant_amendment({"path": "kernel/invariants.py"})

    def test_is_invariant_amendment_negative(self, engine: DoctrineEngine):
        assert not engine._is_invariant_amendment({"name": "regular"})
        assert not engine._is_invariant_amendment("not a dict")
        assert not engine._is_invariant_amendment({})

    def test_is_invariant_amendment_doctrine_change(self, engine: DoctrineEngine):
        assert engine._is_invariant_amendment({"doctrine_change": "D2 modification"})


class TestSeverityTiers:
    """Graduated severity tiering for KernelPanic."""

    def test_default_severity_used_when_none_specified(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity, default_severity,
        )
        panic = KernelPanic(KernelInvariant.RECEIPT, "test")
        # K1 default is CRITICAL
        assert panic.severity == "CRITICAL"
        assert panic.severity_enum == Severity.CRITICAL

    def test_k4_default_is_medium(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity,
        )
        panic = KernelPanic(KernelInvariant.TEMPORAL, "test")
        assert panic.severity == "MEDIUM"
        assert panic.severity_enum == Severity.MEDIUM

    def test_k13_default_is_low(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity,
        )
        panic = KernelPanic(KernelInvariant.CONVERGENCE, "test")
        assert panic.severity == "LOW"
        assert panic.severity_enum == Severity.LOW

    def test_explicit_severity_string_overrides_default(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity,
        )
        panic = KernelPanic(KernelInvariant.RECEIPT, "test", severity="LOW")
        assert panic.severity == "LOW"
        assert panic.severity_enum == Severity.LOW

    def test_explicit_severity_enum_overrides_default(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity,
        )
        panic = KernelPanic(KernelInvariant.RECEIPT, "test", severity=Severity.MEDIUM)
        assert panic.severity == "MEDIUM"
        assert panic.severity_enum == Severity.MEDIUM

    def test_invalid_severity_string_falls_back_to_high(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, KernelPanic, Severity,
        )
        panic = KernelPanic(KernelInvariant.RECEIPT, "test", severity="BOGUS")
        assert panic.severity_enum == Severity.HIGH

    def test_default_severity_function(self):
        from hummbl_governance.kernel.invariants import (
            KernelInvariant, Severity, default_severity,
        )
        assert default_severity(KernelInvariant.RECEIPT) == Severity.CRITICAL
        assert default_severity(KernelInvariant.TEMPORAL) == Severity.MEDIUM
        assert default_severity(KernelInvariant.CONVERGENCE) == Severity.LOW
        assert default_severity(KernelInvariant.PHYSICAL_SAFETY) == Severity.CRITICAL

    def test_k12_safety_invariant_exists(self):
        from hummbl_governance.kernel.invariants import KernelInvariant
        assert KernelInvariant.SAFETY.value == "K12"

    def test_k13_convergence_invariant_exists(self):
        from hummbl_governance.kernel.invariants import KernelInvariant
        assert KernelInvariant.CONVERGENCE.value == "K13"

    def test_k14_physical_safety_invariant_exists(self):
        from hummbl_governance.kernel.invariants import KernelInvariant
        assert KernelInvariant.PHYSICAL_SAFETY.value == "K14"
