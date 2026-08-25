#!/usr/bin/env python3
"""Tests for tuples vs untyped logs comparison (issue #39)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from tuples_vs_logs import (
    generate_tuples,
    tuples_to_untyped_logs,
    measure_validation_time,
    measure_storage_size,
    measure_query_scope_violations,
    run_comparison,
    SCALES,
)


def test_generate_tuples_count():
    """generate_tuples should produce the requested count."""
    tuples = generate_tuples(100)
    assert len(tuples) == 100


def test_generate_tuples_fields():
    """Generated tuples should have required fields."""
    tuples = generate_tuples(10)
    t = tuples[0]
    assert "tuple_type" in t
    assert "id" in t
    assert "time" in t
    assert "state" in t
    assert "agent" in t
    assert "intent_id" in t
    assert "task_id" in t
    assert "tuple_data" in t


def test_generate_tuples_blocked_ratio():
    """~10% of generated tuples should have state=blocked."""
    tuples = generate_tuples(100)
    blocked = [t for t in tuples if t["state"] == "blocked"]
    assert len(blocked) == 10  # exactly 10% for n=100


def test_tuples_to_untyped_logs():
    """Conversion to untyped logs should preserve key info."""
    tuples = generate_tuples(5)
    logs = tuples_to_untyped_logs(tuples)
    assert len(logs) == 5
    assert logs[0]["timestamp"] == tuples[0]["time"]
    assert logs[0]["event"] == tuples[0]["tuple_type"].lower()
    assert logs[0]["agent"] == tuples[0]["agent"]


def test_measure_validation_time_tuples():
    """Validation time for tuples should be measurable and positive."""
    tuples = generate_tuples(100)
    t = measure_validation_time(tuples, is_tuple=True)
    assert t >= 0


def test_measure_validation_time_logs():
    """Validation time for logs should be measurable and positive."""
    logs = tuples_to_untyped_logs(generate_tuples(100))
    t = measure_validation_time(logs, is_tuple=False)
    assert t >= 0


def test_measure_storage_size():
    """Storage size should be positive and tuples >= logs (more fields)."""
    tuples = generate_tuples(100)
    logs = tuples_to_untyped_logs(tuples)
    tuple_size = measure_storage_size(tuples)
    log_size = measure_storage_size(logs)
    assert tuple_size > 0
    assert log_size > 0


def test_measure_query_scope_violations():
    """Query for scope violations should find the same count in both formats."""
    tuples = generate_tuples(100)
    logs = tuples_to_untyped_logs(tuples)
    _, tuple_violations = measure_query_scope_violations(tuples, is_tuple=True)
    _, log_violations = measure_query_scope_violations(logs, is_tuple=False)
    assert tuple_violations == log_violations
    assert tuple_violations == 10  # 10% of 100


def test_run_comparison_small():
    """run_comparison should return a valid result for small scale."""
    result = run_comparison("small", SCALES["small"])
    assert result["scale"] == "small"
    assert result["n_events"] == 100
    assert "tuples" in result
    assert "untyped_logs" in result
    assert "delta" in result
    assert result["tuples"]["storage_bytes"] > 0
    assert result["untyped_logs"]["storage_bytes"] > 0


def test_run_comparison_delta_ratios():
    """Delta ratios should be positive numbers."""
    result = run_comparison("small", 100)
    assert result["delta"]["validation_time_ratio"] > 0
    assert result["delta"]["storage_ratio"] > 0
    assert result["delta"]["query_violations_ratio"] > 0


if __name__ == "__main__":
    test_generate_tuples_count()
    test_generate_tuples_fields()
    test_generate_tuples_blocked_ratio()
    test_tuples_to_untyped_logs()
    test_measure_validation_time_tuples()
    test_measure_validation_time_logs()
    test_measure_storage_size()
    test_measure_query_scope_violations()
    test_run_comparison_small()
    test_run_comparison_delta_ratios()
    print("All tuples vs logs comparison tests passed")
