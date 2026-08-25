#!/usr/bin/env python3
"""Tests for ATTEST separate class evaluation (issue #30)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_attest_schema_exists():
    """The ATTEST schema should exist as a separate file."""
    schema = REPO_ROOT / "schemas" / "attest.schema.json"
    assert schema.exists(), "attest.schema.json not found"


def test_evidence_schema_exists():
    """The EVIDENCE schema should exist as a separate file."""
    schema = REPO_ROOT / "schemas" / "evidence.schema.json"
    assert schema.exists(), "evidence.schema.json not found"


def test_attest_schema_has_tuple_data():
    """The ATTEST schema should have a tuple_data field for domain-specific fields."""
    import json
    schema = REPO_ROOT / "schemas" / "attest.schema.json"
    data = json.loads(schema.read_text(encoding="utf-8"))
    props = data.get("properties", {})
    assert "tuple_data" in props or "tuple_data" in data.get("required", [])


def test_attest_schema_has_intent_id():
    """The ATTEST schema should have an intent_id field (governance link)."""
    import json
    schema = REPO_ROOT / "schemas" / "attest.schema.json"
    data = json.loads(schema.read_text(encoding="utf-8"))
    props = data.get("properties", {})
    assert "intent_id" in props or "intent_id" in data.get("required", [])


def test_decision_record_exists():
    """The decision record should exist."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-attest-separate-class-evaluation.md"
    assert note.exists()


def test_decision_record_contains_decision():
    """The decision record should contain a clear decision."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-attest-separate-class-evaluation.md"
    content = note.read_text(encoding="utf-8")
    assert "KEEP ATTEST" in content or "SEPARATE" in content.upper()
    assert "Decision" in content


def test_decision_record_contains_empirical_comparison():
    """The decision record should contain an empirical comparison."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-attest-separate-class-evaluation.md"
    content = note.read_text(encoding="utf-8")
    assert "Empirical" in content or "empirical" in content
    assert "Model 1" in content
    assert "Model 2" in content


def test_decision_record_contains_consequences():
    """The decision record should document consequences."""
    note = REPO_ROOT / "research_notes" / "2026-07-01-attest-separate-class-evaluation.md"
    content = note.read_text(encoding="utf-8")
    assert "Consequences" in content


if __name__ == "__main__":
    test_attest_schema_exists()
    test_evidence_schema_exists()
    test_attest_schema_has_tuple_data()
    test_attest_schema_has_intent_id()
    test_decision_record_exists()
    test_decision_record_contains_decision()
    test_decision_record_contains_empirical_comparison()
    test_decision_record_contains_consequences()
    print("All ATTEST evaluation tests passed")
