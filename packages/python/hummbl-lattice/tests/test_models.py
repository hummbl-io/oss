# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_lattice.models."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_lattice.models import (
    BASE120_ANCESTORS,
    FAMILIES,
    CompositionMatrix,
    Lattice,
    LatticeOperator,
)


class TestLatticeOperator:
    def test_valid_operator(self):
        op = LatticeOperator(
            code="IN01",
            name="Seismic Load Path Inversion",
            family="IN",
            definition="Instead of designing for expected loads, trace the failure path backward.",
            base120_ancestor="IN3",
        )
        assert op.code == "IN01"
        assert op.family == "IN"
        assert op.family_name == "Inversion"
        assert op.status == "draft"

    def test_invalid_family(self):
        with pytest.raises(ValueError, match="Invalid family"):
            LatticeOperator(
                code="X01", name="Test", family="X",
                definition="Test", base120_ancestor="P1",
            )

    def test_invalid_ancestor(self):
        with pytest.raises(ValueError, match="Invalid base120_ancestor"):
            LatticeOperator(
                code="P01", name="Test", family="P",
                definition="Test", base120_ancestor="ZZ99",
            )

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="Invalid status"):
            LatticeOperator(
                code="P01", name="Test", family="P",
                definition="Test", base120_ancestor="P1",
                status="bogus",
            )

    def test_serialization(self):
        op = LatticeOperator(
            code="DE01", name="Recursive Decomposition",
            family="DE", definition="Break into subsystems recursively.",
            base120_ancestor="DE5", status="ratified",
        )
        d = op.to_dict()
        assert d["code"] == "DE01"
        assert d["status"] == "ratified"
        op2 = LatticeOperator.from_dict(d)
        assert op2 == op


class TestCompositionMatrix:
    def test_default_undefined(self):
        m = CompositionMatrix()
        assert m.get("P", "IN") == "undefined"

    def test_set_and_get(self):
        m = CompositionMatrix()
        m.set("P", "IN", "admissible")
        assert m.get("P", "IN") == "admissible"
        assert m.admissible_count == 1

    def test_invalid_state(self):
        m = CompositionMatrix()
        with pytest.raises(ValueError):
            m.set("P", "IN", "bogus")

    def test_invalid_family(self):
        m = CompositionMatrix()
        with pytest.raises(ValueError):
            m.set("X", "IN", "admissible")

    def test_serialization(self):
        m = CompositionMatrix()
        m.set("P", "IN", "admissible")
        m.set("CO", "DE", "admissible")
        m.set("RE", "SY", "inadmissible")
        d = m.to_dict()
        assert d["P"]["IN"] == "admissible"
        m2 = CompositionMatrix.from_dict(d)
        assert m2.get("P", "IN") == "admissible"
        assert m2.admissible_count == 2


class TestLattice:
    def _make_test_lattice(self) -> Lattice:
        lattice = Lattice(domain="Test Domain", version="0.1.0")
        for i, fam in enumerate(FAMILIES):
            for j in range(4):
                lattice.add_operator(LatticeOperator(
                    code=f"{fam}{j+1:02d}",
                    name=f"Test Operator {fam}{j+1}",
                    family=fam,
                    definition=f"A domain-specific reasoning operator for structural engineering seismic analysis with load path inversion.",
                    base120_ancestor=f"{fam}{j+1}",
                ))
        lattice.composition_matrix.set("P", "IN", "admissible")
        lattice.composition_matrix.set("CO", "DE", "admissible")
        lattice.composition_matrix.set("RE", "SY", "admissible")
        lattice.cross_maps = [
            {"to": "Architecture", "operator": "IN01", "cousin": "IN03"},
            {"to": "DevTools", "operator": "DE01", "cousin": "DE02"},
            {"to": "News", "operator": "P01", "cousin": "P05"},
        ]
        return lattice

    def test_basic_properties(self):
        lattice = self._make_test_lattice()
        assert lattice.domain == "Test Domain"
        assert lattice.operator_count == 24
        assert lattice.missing_families == []

    def test_family_counts(self):
        lattice = self._make_test_lattice()
        counts = lattice.family_counts
        for fam in FAMILIES:
            assert counts[fam] == 4

    def test_get_operator(self):
        lattice = self._make_test_lattice()
        op = lattice.get_operator("P01")
        assert op is not None
        assert op.name == "Test Operator P1"
        assert lattice.get_operator("ZZZ") is None

    def test_list_by_family(self):
        lattice = self._make_test_lattice()
        p_ops = lattice.list_by_family("P")
        assert len(p_ops) == 4

    def test_hash(self):
        lattice = self._make_test_lattice()
        h = lattice.lattice_hash
        assert len(h) == 64  # SHA-256 hex
        # Same lattice → same hash
        assert lattice.lattice_hash == h

    def test_json_roundtrip(self):
        lattice = self._make_test_lattice()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            lattice.to_json(path)
            lattice2 = Lattice.from_json(path)
            assert lattice2.domain == lattice.domain
            assert lattice2.operator_count == lattice.operator_count
            assert lattice2.lattice_hash == lattice.lattice_hash
        finally:
            Path(path).unlink(missing_ok=True)

    def test_missing_families(self):
        lattice = Lattice(domain="Incomplete")
        lattice.add_operator(LatticeOperator(
            code="P01", name="Only P", family="P",
            definition="Test operator for structural engineering analysis.",
            base120_ancestor="P1",
        ))
        assert "P" not in lattice.missing_families
        assert "IN" in lattice.missing_families
