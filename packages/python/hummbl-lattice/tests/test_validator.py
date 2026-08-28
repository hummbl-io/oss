# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_lattice.validator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from hummbl_lattice.models import (
    FAMILIES,
    CompositionMatrix,
    Lattice,
    LatticeOperator,
)
from hummbl_lattice.validator import LatticeValidator


def _make_valid_lattice() -> Lattice:
    """A lattice that passes all validation checks."""
    lattice = Lattice(domain="Structural Engineering", version="0.1.0")
    for fam in FAMILIES:
        for j in range(4):
            lattice.add_operator(LatticeOperator(
                code=f"{fam}{j+1:02d}",
                name=f"Seismic {fam} Operator {j+1}",
                family=fam,
                definition=f"Domain-specific reasoning for structural engineering seismic load path analysis with material properties.",
                base120_ancestor=f"{fam}{j+1}",
                status="draft",
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


class TestLatticeValidator:
    def test_valid_lattice_passes(self):
        lattice = _make_valid_lattice()
        validator = LatticeValidator()
        report = validator.validate(lattice)
        assert report.failed_count == 0
        assert report.ratification_ready

    def test_too_few_operators(self):
        lattice = _make_valid_lattice()
        lattice.operators = lattice.operators[:10]
        validator = LatticeValidator()
        report = validator.validate(lattice)
        check = next(c for c in report.checks if c.name == "operator_count")
        assert check.failed

    def test_missing_family(self):
        lattice = _make_valid_lattice()
        lattice.operators = [op for op in lattice.operators if op.family != "SY"]
        validator = LatticeValidator()
        report = validator.validate(lattice)
        check = next(c for c in report.checks if c.name == "family_coverage")
        assert check.failed

    def test_no_composition_matrix(self):
        lattice = _make_valid_lattice()
        lattice.composition_matrix = CompositionMatrix()
        validator = LatticeValidator()
        report = validator.validate(lattice)
        check = next(c for c in report.checks if c.name == "composition_matrix")
        assert check.failed

    def test_no_cross_maps(self):
        lattice = _make_valid_lattice()
        lattice.cross_maps = []
        validator = LatticeValidator()
        report = validator.validate(lattice)
        check = next(c for c in report.checks if c.name == "cross_maps")
        assert check.failed

    def test_low_domain_specificity(self):
        lattice = _make_valid_lattice()
        for op in lattice.operators[:5]:
            object.__setattr__(op, "definition", "Think about the problem.")
        validator = LatticeValidator()
        report = validator.validate(lattice)
        check = next(c for c in report.checks if c.name == "domain_specificity")
        assert check.failed or check.is_warning

    def test_hash_computed(self):
        lattice = _make_valid_lattice()
        validator = LatticeValidator()
        report = validator.validate(lattice)
        assert len(report.lattice_hash) == 64

    def test_file_not_found(self):
        validator = LatticeValidator()
        report = validator.validate("nonexistent.json")
        check = next(c for c in report.checks if c.name == "file_load")
        assert check.failed

    def test_json_file_validation(self):
        lattice = _make_valid_lattice()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            lattice.to_json(path)
            validator = LatticeValidator()
            report = validator.validate(path)
            assert report.ratification_ready
        finally:
            Path(path).unlink(missing_ok=True)

    def test_report_text(self):
        lattice = _make_valid_lattice()
        validator = LatticeValidator()
        report = validator.validate(lattice)
        text = report.to_text()
        assert "Domain120 Lattice Validation Report" in text
        assert "Ratification" in text
