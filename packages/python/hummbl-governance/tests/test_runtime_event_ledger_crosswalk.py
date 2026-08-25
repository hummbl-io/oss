"""Tests for advisory deterministic runtime and event-ledger fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_governance.schema_validator import SchemaValidator


ROOT = Path(__file__).parent.parent
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "runtime_event_ledger" / "runtime_event_ledger_fixtures.json"
DOC_PATH = ROOT / "docs" / "ecosystem" / "deterministic_agent_runtime_event_ledger_crosswalk_2026-07-03.md"


def _fixture_bundle() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case_name", sorted(_fixture_bundle()))
def test_valid_runtime_event_ledger_fixtures_pass(case_name):
    """Each proposed advisory schema must have one valid fixture."""
    case = _fixture_bundle()[case_name]
    schema = json.loads((ROOT / case["schema"]).read_text(encoding="utf-8"))
    ok, errors = SchemaValidator.validate_dict(case["valid"], schema)
    assert ok, f"{case_name} valid fixture failed: {errors}"


@pytest.mark.parametrize("case_name", sorted(_fixture_bundle()))
def test_negative_runtime_event_ledger_fixtures_fail(case_name):
    """Each proposed advisory schema must have one adversarial fixture."""
    case = _fixture_bundle()[case_name]
    schema = json.loads((ROOT / case["schema"]).read_text(encoding="utf-8"))
    ok, errors = SchemaValidator.validate_dict(case["invalid"], schema)
    assert not ok, f"{case_name} negative fixture unexpectedly passed"
    assert errors


def test_runtime_event_ledger_doc_exists():
    """The issue crosswalk document must exist beside the advisory schemas."""
    assert DOC_PATH.exists()
