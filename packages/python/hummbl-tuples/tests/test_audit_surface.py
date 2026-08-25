#!/usr/bin/env python3
"""Tests for audit surface minimization (issue #41)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from audit_surface import audit_tuple, audit_trace, MINIMUM_FIELDS, RECOMMENDED_FIELDS, FULL_FIELDS


def test_minimum_fields_count():
    """Minimum field set should have 8 fields (7 required + tuple_data)."""
    assert len(MINIMUM_FIELDS) == 8


def test_recommended_fields_count():
    """Recommended field set should have 10 fields."""
    assert len(RECOMMENDED_FIELDS) == 10


def test_full_fields_count():
    """Full field set should have 14 fields."""
    assert len(FULL_FIELDS) == 14


def test_audit_tuple_pass():
    """A tuple with all required fields should pass."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-001",
        "time": "2026-07-01T00:00:00Z",
        "state": "ok",
        "agent": "test-agent",
        "intent_id": "intent-001",
        "task_id": "task-001",
        "tuple_data": {},
    }
    result = audit_tuple(t, "minimum")
    assert result["verdict"] == "pass"
    assert len(result["critical_missing"]) == 0


def test_audit_tuple_fail_missing_critical():
    """A tuple missing critical fields should fail."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-002",
        "tuple_data": {},
    }
    result = audit_tuple(t, "minimum")
    assert result["verdict"] == "fail"
    assert "time" in result["critical_missing"]
    assert "state" in result["critical_missing"]
    assert "agent" in result["critical_missing"]


def test_audit_tuple_defaulted_fields():
    """Missing defaultable fields should be defaulted, not critical."""
    t = {
        "tuple_type": "CONTRACT",
        "id": "test-003",
        "time": "2026-07-01T00:00:00Z",
        "state": "ok",
        "agent": "test-agent",
        "intent_id": "intent-001",
        "task_id": "task-001",
        "tuple_data": {},
    }
    result = audit_tuple(t, "recommended")
    # drift and tier are missing but defaultable
    assert "drift" in result["defaulted"]
    assert "tier" in result["defaulted"]
    assert result["verdict"] == "pass"


def test_audit_trace():
    """audit_trace should aggregate results correctly."""
    trace = [
        {"tuple_type": "CONTRACT", "id": "1", "time": "t1", "state": "ok",
         "agent": "a", "intent_id": "i", "task_id": "t", "tuple_data": {}},
        {"tuple_type": "EVIDENCE", "id": "2", "time": "t2", "state": "ok",
         "agent": "a", "intent_id": "i", "task_id": "t", "tuple_data": {}},
    ]
    report = audit_trace(trace, "minimum")
    assert report["total_tuples"] == 2
    assert report["passed"] == 2
    assert report["failed"] == 0


def test_audit_trace_with_failure():
    """audit_trace should count failures correctly."""
    trace = [
        {"tuple_type": "CONTRACT", "id": "1", "time": "t1", "state": "ok",
         "agent": "a", "intent_id": "i", "task_id": "t", "tuple_data": {}},
        {"tuple_type": "EVIDENCE", "id": "2", "tuple_data": {}},
    ]
    report = audit_trace(trace, "minimum")
    assert report["passed"] == 1
    assert report["failed"] == 1


def test_field_set_hierarchy():
    """Field sets should be hierarchical: minimum ⊂ recommended ⊂ full."""
    assert MINIMUM_FIELDS.issubset(RECOMMENDED_FIELDS)
    assert RECOMMENDED_FIELDS.issubset(FULL_FIELDS)


if __name__ == "__main__":
    test_minimum_fields_count()
    test_recommended_fields_count()
    test_full_fields_count()
    test_audit_tuple_pass()
    test_audit_tuple_fail_missing_critical()
    test_audit_tuple_defaulted_fields()
    test_audit_trace()
    test_audit_trace_with_failure()
    test_field_set_hierarchy()
    print("All audit surface tests passed")
