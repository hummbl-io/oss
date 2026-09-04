"""Tests for the Primitive Registry (O7 — Registry-Based Organization)."""

from __future__ import annotations

import pytest

from hummbl_governance.primitive_registry import (
    PrimitiveRegistry,
    PrimitiveEntry,
    PrimitiveStatus,
    PrimitiveLayer,
)


class TestPrimitiveRegistry:
    """Core registry functionality."""

    def test_registry_has_primitives(self):
        reg = PrimitiveRegistry()
        assert len(reg) > 0

    def test_get_by_pid(self):
        reg = PrimitiveRegistry()
        p1 = reg.get("P1")
        assert p1 is not None
        assert p1.name == "KillSwitch"
        assert p1.category == "Safety"

    def test_get_by_family_code(self):
        reg = PrimitiveRegistry()
        sf1 = reg.get_by_family_code("SF-1")
        assert sf1 is not None
        assert sf1.pid == "P1"

    def test_primitives_for_invariant(self):
        reg = PrimitiveRegistry()
        k1_enforcers = reg.primitives_for_invariant("K1")
        assert len(k1_enforcers) > 0
        for p in k1_enforcers:
            assert "K1" in p.enforced_invariants

    def test_primitives_in_category(self):
        reg = PrimitiveRegistry()
        safety = reg.primitives_in_category("Safety")
        assert len(safety) > 0
        for p in safety:
            assert p.category == "Safety"

    def test_primitives_in_layer(self):
        reg = PrimitiveRegistry()
        authority = reg.primitives_in_layer(PrimitiveLayer.AUTHORITY)
        assert len(authority) > 0
        for p in authority:
            assert p.layer == PrimitiveLayer.AUTHORITY

    def test_governance_vs_infrastructure(self):
        reg = PrimitiveRegistry()
        gov = reg.governance_primitives()
        infra = reg.infrastructure_primitives()
        assert len(gov) > 0
        assert len(infra) > 0
        assert len(gov) + len(infra) == len(reg)
        for p in gov:
            assert p.is_governance_primitive
            assert not p.is_infrastructure
        for p in infra:
            assert p.is_infrastructure
            assert not p.is_governance_primitive

    def test_implemented_primitives(self):
        reg = PrimitiveRegistry()
        implemented = reg.implemented_primitives()
        assert len(implemented) > 0
        for p in implemented:
            assert p.status == PrimitiveStatus.IMPLEMENTED

    def test_proposed_primitives(self):
        reg = PrimitiveRegistry()
        proposed = reg.proposed_primitives()
        # There should be some not-started primitives
        for p in proposed:
            assert p.status == PrimitiveStatus.NOT_STARTED

    def test_coverage_report(self):
        reg = PrimitiveRegistry()
        report = reg.coverage_report()
        assert "total_primitives" in report
        assert "governance_primitives" in report
        assert "infrastructure_primitives" in report
        assert "pairing_coverage" in report
        assert "uncovered_invariants" in report
        assert report["total_primitives"] == len(reg)
        assert (
            report["governance_primitives"] + report["infrastructure_primitives"]
            == report["total_primitives"]
        )
        # K12-K14 should now be covered
        assert "K12" not in report["uncovered_invariants"]
        assert "K13" not in report["uncovered_invariants"]
        assert "K14" not in report["uncovered_invariants"]

    def test_categories(self):
        reg = PrimitiveRegistry()
        cats = reg.categories()
        assert "Safety" in cats
        assert "Governance Kernel" in cats
        assert all(count > 0 for count in cats.values())

    def test_family_codes(self):
        reg = PrimitiveRegistry()
        codes = reg.family_codes()
        assert "Safety" in codes
        assert codes["Safety"] == "SF"
        assert "Governance Kernel" in codes
        assert codes["Governance Kernel"] == "GK"

    def test_contains(self):
        reg = PrimitiveRegistry()
        assert "P1" in reg
        assert "P999" not in reg

    def test_k12_safety_invariant_covered(self):
        """K12 (SAFETY) should be covered by P1 and P2."""
        reg = PrimitiveRegistry()
        k12_enforcers = reg.primitives_for_invariant("K12")
        pids = {p.pid for p in k12_enforcers}
        assert "P1" in pids
        assert "P2" in pids

    def test_k13_convergence_invariant_covered(self):
        """K13 (CONVERGENCE) should be covered by P16."""
        reg = PrimitiveRegistry()
        k13_enforcers = reg.primitives_for_invariant("K13")
        pids = {p.pid for p in k13_enforcers}
        assert "P16" in pids

    def test_k14_physical_safety_invariant_covered(self):
        """K14 (PHYSICAL_SAFETY) should be covered by P20."""
        reg = PrimitiveRegistry()
        k14_enforcers = reg.primitives_for_invariant("K14")
        pids = {p.pid for p in k14_enforcers}
        assert "P20" in pids


class TestPrimitiveEntry:
    """PrimitiveEntry dataclass tests."""

    def test_is_governance_primitive(self):
        entry = PrimitiveEntry(
            pid="P1", family_code="SF-1", name="Test", category="Safety",
            module="test", enforced_invariants=("K1",),
        )
        assert entry.is_governance_primitive
        assert not entry.is_infrastructure

    def test_is_infrastructure(self):
        entry = PrimitiveEntry(
            pid="P99", family_code="XX-1", name="Test", category="Test",
            module="test", enforced_invariants=(),
        )
        assert entry.is_infrastructure
        assert not entry.is_governance_primitive

    def test_frozen(self):
        entry = PrimitiveEntry(
            pid="P1", family_code="SF-1", name="Test", category="Safety",
            module="test",
        )
        with pytest.raises(AttributeError):
            entry.pid = "P2"  # type: ignore[misc]
