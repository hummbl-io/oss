from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

from hummbl_cognition.parallel_gate_receipt import (
    compute_gate_receipt_hash,
    create_parallel_gate_receipt,
    validate_parallel_gate_receipt,
)

_SCHEMA_PATH = (
    Path(__file__).parents[2] / "src" / "hummbl_cognition" / "schemas" / "parallel_gate_receipt.schema.json"
)


def _schema_errors(receipt: dict) -> list:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return list(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(receipt)
    )


def _finding(**overrides) -> dict:
    value = {
        "file": "hummbl_cognition/example.py",
        "line": 1,
        "rule": "R001",
        "severity": "high",
        "message": "example finding",
    }
    value.update(overrides)
    return value


def test_parallel_gate_hash_excludes_timestamp():
    a = create_parallel_gate_receipt(
        gate_name="unit", run_id="run-1", status="pass", duration_ms=1, timestamp="2026-07-04T00:00:00Z"
    )
    b = create_parallel_gate_receipt(
        gate_name="unit", run_id="run-1", status="pass", duration_ms=1, timestamp="2026-07-04T00:01:00Z"
    )

    assert a["receipt_hash"] == b["receipt_hash"]
    assert a["receipt_hash"].startswith("sha256:")


def test_parallel_gate_rejects_unsorted_findings():
    receipt = create_parallel_gate_receipt(
        gate_name="unit",
        run_id="run-1",
        status="fail",
        duration_ms=1,
        findings=[
            {"file": "b.py", "line": 2, "rule": "R", "severity": "high", "message": "b"},
            {"file": "a.py", "line": 1, "rule": "R", "severity": "high", "message": "a"},
        ],
    )
    receipt["findings"] = list(reversed(receipt["findings"]))
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert "findings must be sorted by file, then line" in errors


def test_parallel_gate_rejects_empty_required_string():
    receipt = create_parallel_gate_receipt(
        gate_name="unit", run_id="run-1", status="pass", duration_ms=1
    )
    receipt["gate_name"] = ""
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert "gate_name must be a non-empty string" in errors


def test_parallel_gate_rejects_extra_field():
    receipt = create_parallel_gate_receipt(
        gate_name="unit", run_id="run-1", status="pass", duration_ms=1
    )
    receipt["extra"] = "nope"
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in error for error in errors)


def test_parallel_gate_fail_requires_attributable_finding_in_both_contracts():
    receipt = create_parallel_gate_receipt(
        gate_name="unit", run_id="run-1", status="pass", duration_ms=1
    )
    receipt["status"] = "fail"
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert any("requires at least one" in error for error in errors)
    assert _schema_errors(receipt)


def test_parallel_gate_rejects_retry_on_deterministic_failure():
    receipt = create_parallel_gate_receipt(
        gate_name="unit",
        run_id="run-1",
        status="fail",
        duration_ms=1,
        findings=[_finding()],
    )
    receipt["retry_count"] = 1
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert any("retry_count > 0" in error for error in errors)
    assert _schema_errors(receipt)


def test_parallel_gate_malformed_same_file_findings_return_errors_not_exception():
    receipt = create_parallel_gate_receipt(
        gate_name="unit",
        run_id="run-1",
        status="fail",
        duration_ms=1,
        findings=[_finding(line=1), _finding(line=2, rule="R002")],
    )
    receipt["findings"][1]["line"] = "2"
    receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert not valid
    assert any("positive integer" in error for error in errors)


def test_parallel_gate_rejects_invalid_attribution_values_in_both_contracts():
    for overrides in (
        {"file": "/absolute.py"},
        {"file": "../escape.py"},
        {"file": "windows\\path.py"},
        {"rule": "   "},
        {"line": True},
        {"severity": "unknown"},
        {"message": "   "},
    ):
        receipt = create_parallel_gate_receipt(
            gate_name="unit",
            run_id="run-1",
            status="fail",
            duration_ms=1,
            findings=[_finding()],
        )
        receipt["findings"][0].update(overrides)
        receipt["receipt_hash"] = compute_gate_receipt_hash(receipt)

        valid, _ = validate_parallel_gate_receipt(receipt)

        assert not valid, overrides
        assert _schema_errors(receipt), overrides


def test_parallel_gate_valid_receipt_matches_schema():
    receipt = create_parallel_gate_receipt(
        gate_name="unit",
        run_id="run-1",
        status="fail",
        duration_ms=1,
        findings=[_finding()],
        environment={
            "runner": "ubuntu-latest",
            "python_version": "3.12",
            "dependencies_hash": f"sha256:{'a' * 64}",
        },
    )

    valid, errors = validate_parallel_gate_receipt(receipt)

    assert valid, errors
    assert not _schema_errors(receipt)
