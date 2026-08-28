# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_lattice CLI."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_lattice.cli import main
from hummbl_lattice.models import (
    FAMILIES,
    CompositionMatrix,
    Lattice,
    LatticeOperator,
)


def _make_valid_lattice() -> Lattice:
    lattice = Lattice(domain="Test Engineering")
    for fam in FAMILIES:
        for j in range(4):
            lattice.add_operator(LatticeOperator(
                code=f"{fam}{j+1:02d}",
                name=f"Seismic {fam} Operator {j+1}",
                family=fam,
                definition=f"Domain-specific reasoning for structural engineering seismic load path analysis with material properties.",
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


class TestCLI:
    def test_no_args(self):
        assert main([]) == 0

    def test_info(self, capsys):
        lattice = _make_valid_lattice()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            lattice.to_json(path)
            ret = main(["info", path])
            assert ret == 0
            captured = capsys.readouterr()
            assert "Test Engineering" in captured.out
            assert "Operators:" in captured.out
        finally:
            Path(path).unlink(missing_ok=True)

    def test_validate_pass(self, capsys):
        lattice = _make_valid_lattice()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            lattice.to_json(path)
            ret = main(["validate", path])
            assert ret == 0
            captured = capsys.readouterr()
            assert "Ratification: READY" in captured.out
        finally:
            Path(path).unlink(missing_ok=True)

    def test_validate_fail(self, capsys):
        lattice = _make_valid_lattice()
        lattice.operators = lattice.operators[:5]  # too few
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            lattice.to_json(path)
            ret = main(["validate", path])
            assert ret == 1
        finally:
            Path(path).unlink(missing_ok=True)

    def test_unknown_command(self, capsys):
        ret = main(["bogus"])
        assert ret == 1
