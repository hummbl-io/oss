from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hummbl_cognition.postcondition_probe_receipt import (
    PostconditionProbeError,
    compute_receipt_hash,
    create_postcondition_probe,
    validate_postcondition_probe,
)

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker


def _verified_receipt() -> dict:
    return create_postcondition_probe(
        claimed_action="append bus message",
        declared_side_effect="bus file grew by one line with expected marker",
        expected_artifact={
            "kind": "bus-message",
            "locator": "_state/coordination/messages.tsv",
            "content_marker": "postcond-test-marker",
        },
        evidence_locator="_state/coordination/messages.tsv:last-line",
        verification_command="tail -1 _state/coordination/messages.tsv | grep postcond-test-marker",
        verification_result={
            "status": "verified",
            "observed_state": "last line contains postcond-test-marker",
            "exit_code": 0,
            "latency_ms": 12,
        },
        before_state={"snapshot": "wc -l = 412", "captured_at": "2026-07-04T20:00:00Z"},
        after_state={"snapshot": "wc -l = 413", "captured_at": "2026-07-04T20:00:05Z"},
        negative_check={
            "checked": True,
            "result": "passed",
            "description": "no duplicate bus message appended",
        },
        failure_class="none",
    )


_SCHEMA_PATH = (
    Path(__file__).parents[2]
    / "src"
    / "hummbl_cognition"
    / "schemas"
    / "postcondition_probe_receipt.schema.json"
)


def _schema_errors(receipt: dict) -> list:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return list(validator.iter_errors(receipt))


def test_validate_accepts_verified_receipt():
    valid, errors = validate_postcondition_probe(_verified_receipt())

    assert valid, errors


def test_validate_rejects_extra_field():
    receipt = _verified_receipt()
    receipt["raw_secret"] = "sk-leaked"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("unexpected fields" in e for e in errors)


def test_validate_rejects_missing_required_field():
    receipt = _verified_receipt()
    del receipt["verification_command"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("missing required field: verification_command" in e for e in errors)


def test_validate_rejects_bad_receipt_id_prefix():
    receipt = _verified_receipt()
    receipt["receipt_id"] = "wrong-prefix-123"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_receipt_id_with_uppercase():
    """receipt_id must be lowercase hex only after 'postcond-' prefix."""
    receipt = _verified_receipt()
    receipt["receipt_id"] = "postcond-INVALID-ID"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_schema_and_runtime_reject_degenerate_receipt_id():
    receipt = _verified_receipt()
    receipt["receipt_id"] = "postcond-----"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, _ = validate_postcondition_probe(receipt)

    assert not valid
    assert _schema_errors(receipt)


def test_schema_and_runtime_accept_same_valid_receipt():
    receipt = _verified_receipt()

    valid, errors = validate_postcondition_probe(receipt)

    assert valid, errors
    assert not _schema_errors(receipt)


def test_schema_matches_runtime_nonempty_and_cross_field_invariants():
    mutations = []

    for field in ("claimed_action", "declared_side_effect", "verification_command"):
        mutations.append(lambda receipt, field=field: receipt.__setitem__(field, "   "))

    def verified_with_failure(receipt):
        receipt["failure_class"] = "partial"
        receipt["operator_override_ref"] = "approval-1"

    def contradicted_without_failure(receipt):
        receipt["verification_result"]["status"] = "contradicted"

    def failed_negative_wrong_class(receipt):
        receipt["verification_result"]["status"] = "contradicted"
        receipt["negative_check"]["result"] = "failed"
        receipt["failure_class"] = "false_green"
        receipt["operator_override_ref"] = "approval-2"

    def failure_without_override(receipt):
        receipt["verification_result"]["status"] = "contradicted"
        receipt["failure_class"] = "partial"

    def not_verified_without_failure(receipt):
        receipt["verification_result"]["status"] = "not_verified"
        receipt["verification_result"]["observed_state"] = (
            "verification command timed out"
        )
        receipt["failure_class"] = "none"

    mutations.extend(
        [
            verified_with_failure,
            contradicted_without_failure,
            failed_negative_wrong_class,
            failure_without_override,
            not_verified_without_failure,
        ]
    )

    for mutate in mutations:
        receipt = _verified_receipt()
        mutate(receipt)
        receipt["receipt_hash"] = compute_receipt_hash(receipt)

        valid, _ = validate_postcondition_probe(receipt)

        assert not valid
        assert _schema_errors(receipt)


def test_validate_rejects_bad_timestamp():
    """Timestamp must be a valid RFC3339 date-time, not just a string."""
    receipt = _verified_receipt()
    receipt["timestamp"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_timezoneless_timestamp():
    """RFC3339 requires a timezone — '2026-07-04T00:00:00' is invalid."""
    receipt = _verified_receipt()
    receipt["timestamp"] = "2026-07-04T00:00:00"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_bad_nested_captured_at():
    """Nested captured_at fields must also be valid RFC3339 date-times."""
    receipt = _verified_receipt()
    receipt["before_state"]["captured_at"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any(
        "before_state.captured_at must be an RFC3339 date-time" in e for e in errors
    )


def test_validate_rejects_timezoneless_nested_captured_at():
    receipt = _verified_receipt()
    receipt["after_state"]["captured_at"] = "2026-07-04T00:00:00"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any(
        "after_state.captured_at must be an RFC3339 date-time" in e for e in errors
    )


def test_validate_accepts_valid_nested_captured_at():
    """Valid RFC3339 captured_at with Z suffix should pass."""
    receipt = _verified_receipt()
    receipt["before_state"]["captured_at"] = "2026-07-04T12:00:00Z"
    receipt["after_state"]["captured_at"] = "2026-07-04T12:01:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert valid, errors


def test_validate_rejects_bad_artifact_kind():
    receipt = _verified_receipt()
    receipt["expected_artifact"]["kind"] = "rocket-ship"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("expected_artifact.kind" in e for e in errors)


def test_validate_rejects_bad_verification_status():
    receipt = _verified_receipt()
    receipt["verification_result"]["status"] = "maybe"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("verification_result.status" in e for e in errors)


def test_verified_status_requires_failure_class_none():
    receipt = _verified_receipt()
    receipt["failure_class"] = "false_green"
    receipt["operator_override_ref"] = "risk-acceptance-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("requires failure_class='none'" in e for e in errors)


def test_contradicted_status_requires_non_none_failure_class():
    receipt = _verified_receipt()
    receipt["verification_result"]["status"] = "contradicted"
    receipt["verification_result"]["observed_state"] = "PR does not exist"
    receipt["failure_class"] = "none"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("requires failure_class != 'none'" in e for e in errors)


def test_negative_check_failed_requires_negative_violation():
    receipt = _verified_receipt()
    receipt["negative_check"]["result"] = "failed"
    receipt["negative_check"]["description"] = "duplicate PR opened"
    receipt["failure_class"] = "false_green"
    receipt["operator_override_ref"] = "risk-acceptance-002"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("negative_violation" in e for e in errors)


def test_not_verified_status_requires_non_none_failure_class():
    receipt = _verified_receipt()
    receipt["verification_result"]["status"] = "not_verified"
    receipt["verification_result"]["observed_state"] = "verification command timed out"
    receipt["failure_class"] = "none"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("requires failure_class != 'none'" in e for e in errors)


def test_negative_check_failed_requires_checked_true():
    receipt = _verified_receipt()
    receipt["negative_check"]["result"] = "failed"
    receipt["negative_check"]["checked"] = False
    receipt["negative_check"]["description"] = "duplicate bus message appended"
    receipt["failure_class"] = "negative_violation"
    receipt["operator_override_ref"] = "risk-acceptance-004"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any(
        "negative_check.result='failed' requires negative_check.checked=True" in e
        for e in errors
    )


def test_non_none_failure_class_requires_operator_override_ref():
    receipt = _verified_receipt()
    receipt["verification_result"]["status"] = "contradicted"
    receipt["verification_result"]["observed_state"] = "file does not exist"
    receipt["failure_class"] = "false_green"
    # no operator_override_ref
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("operator_override_ref is required" in e for e in errors)


def test_false_green_with_override_is_valid():
    receipt = _verified_receipt()
    receipt["verification_result"]["status"] = "contradicted"
    receipt["verification_result"]["observed_state"] = "PR does not exist"
    receipt["failure_class"] = "false_green"
    receipt["operator_override_ref"] = "risk-acceptance-003"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_postcondition_probe(receipt)

    assert valid, errors


def test_tampered_hash_rejected():
    receipt = _verified_receipt()
    receipt["receipt_hash"] = "0" * 64

    valid, errors = validate_postcondition_probe(receipt)

    assert not valid
    assert any("receipt_hash does not match" in e for e in errors)


def test_create_postcondition_probe_raises_on_invalid():
    try:
        create_postcondition_probe(
            claimed_action="",
            declared_side_effect="x",
            expected_artifact={"kind": "file", "locator": "/tmp/x"},
            evidence_locator="/tmp/x",
            verification_command="ls /tmp/x",
            verification_result={"status": "verified", "observed_state": "exists"},
        )
        raise AssertionError("should have raised")
    except PostconditionProbeError as exc:
        assert "claimed_action" in str(exc)


def test_create_postcondition_probe_default_negative_check():
    receipt = create_postcondition_probe(
        claimed_action="write file",
        declared_side_effect="file exists",
        expected_artifact={"kind": "file", "locator": "/tmp/x"},
        evidence_locator="/tmp/x",
        verification_command="ls /tmp/x",
        verification_result={"status": "verified", "observed_state": "exists"},
    )

    assert receipt["negative_check"] == {"checked": False, "result": "not_applicable"}
    assert receipt["failure_class"] == "none"


def test_receipt_hash_excludes_hash_field():
    receipt = _verified_receipt()
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    expected = hashlib.sha256(
        json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    assert receipt["receipt_hash"] == expected
