"""Regression coverage for the runnable registry smoke-check example."""

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

import pytest


@pytest.fixture
def smoke_check(monkeypatch):
    """Load the example without retaining its command-line path bootstrap."""
    monkeypatch.setattr(sys, "path", sys.path.copy())
    path = Path(__file__).resolve().parents[1] / "examples" / "registry_smoke_check.py"
    spec = importlib.util.spec_from_file_location("registry_smoke_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_registry_passes(smoke_check, capsys):
    assert smoke_check.main() == 0
    assert capsys.readouterr().out.splitlines() == [
        "P: 20",
        "IN: 20",
        "CO: 20",
        "DE: 20",
        "RE: 20",
        "SY: 20",
        "TOTAL: 120",
        "OK",
    ]


def test_mismatched_code_and_family_fails(smoke_check, monkeypatch, capsys):
    operators = smoke_check.Engine().list()
    assert operators[0].family == "P"
    # Keep all 120 codes unchanged: prefix counting would incorrectly pass.
    operators[0] = replace(operators[0], transformation="IN")
    monkeypatch.setattr(smoke_check.Engine, "list", lambda self: operators)

    assert smoke_check.main() == 1
    lines = capsys.readouterr().out.splitlines()
    assert "P: 19" in lines
    assert "IN: 21" in lines
    assert lines[-2:] == ["TOTAL: 120", "MISMATCH"]


@pytest.mark.parametrize("extra", [False, True], ids=["missing", "extra"])
def test_wrong_total_fails(smoke_check, monkeypatch, capsys, extra):
    operators = smoke_check.Engine().list()
    operators = operators + [operators[0]] if extra else operators[:-1]
    monkeypatch.setattr(smoke_check.Engine, "list", lambda self: operators)

    assert smoke_check.main() == 1
    assert capsys.readouterr().out.splitlines()[-2:] == [
        f"TOTAL: {len(operators)}",
        "MISMATCH",
    ]
