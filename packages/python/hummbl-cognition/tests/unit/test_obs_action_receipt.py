from __future__ import annotations

from hummbl_cognition.obs_action_receipt import (
    compute_receipt_hash,
    create_obs_action_receipt,
    validate_obs_action_receipt,
)


def _valid_receipt() -> dict:
    return create_obs_action_receipt(
        incident_id="inc-1",
        telemetry_source="local-logs",
        query_path="logs/app.log",
        time_window={"start": "2026-07-04T00:00:00Z", "end": "2026-07-04T00:05:00Z"},
        agent_hypothesis="worker stalled",
        confidence="moderate",
        proposed_action="restart worker after approval",
    )


def test_validate_obs_action_receipt_accepts_valid_receipt():
    valid, errors = validate_obs_action_receipt(_valid_receipt())

    assert valid, errors


def test_validate_obs_action_receipt_rejects_extra_field():
    receipt = _valid_receipt()
    receipt["raw_secret_log"] = "token"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_obs_action_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in error for error in errors)


def test_validate_obs_action_receipt_rejects_empty_enum_field():
    receipt = _valid_receipt()
    receipt["confidence"] = ""
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_obs_action_receipt(receipt)

    assert not valid
    assert "confidence must be a non-empty string" in errors


def test_human_approved_execution_requires_approved_status():
    receipt = _valid_receipt()
    receipt["mode"] = "human_approved_execution"
    receipt["human_approval_status"] = "pending"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_obs_action_receipt(receipt)

    assert not valid
    assert any("requires human_approval_status" in error for error in errors)