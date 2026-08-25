from __future__ import annotations

from datetime import datetime, timedelta, timezone

from hummbl_cognition.compliance_log_gap_receipt import (
    ComplianceLogGapError,
    compute_receipt_hash,
    create_compliance_log_gap_receipt,
    gap_exceeds_retention,
    validate_compliance_log_gap_receipt,
)


def _healthy_receipt() -> dict:
    return create_compliance_log_gap_receipt(
        provider="openai",
        workspace_class="fedramp",
        endpoint="https://api.chatgpt.com/v1/compliance/logs/download",
        endpoint_status="healthy",
        retention_days=30,
        last_successful_export_at="2026-07-04T00:00:00Z",
        oldest_required_timestamp="2026-06-04T00:00:00Z",
        gap_detected=False,
        monitoring_mode="monitor_only",
    )


def test_validate_accepts_healthy_receipt():
    valid, errors = validate_compliance_log_gap_receipt(_healthy_receipt())

    assert valid, errors


def test_validate_rejects_extra_field():
    receipt = _healthy_receipt()
    receipt["raw_secret"] = "sk-leaked"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in e for e in errors)


def test_validate_rejects_missing_required_field():
    receipt = _healthy_receipt()
    del receipt["retention_days"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("missing required field: retention_days" in e for e in errors)


def test_validate_rejects_bad_receipt_id_prefix():
    receipt = _healthy_receipt()
    receipt["receipt_id"] = "wrong-prefix-123"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_bad_provider():
    receipt = _healthy_receipt()
    receipt["provider"] = "deepseek"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("provider:" in e for e in errors)


def test_validate_rejects_zero_retention_days():
    receipt = _healthy_receipt()
    receipt["retention_days"] = 0
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("retention_days must be a positive integer" in e for e in errors)


def test_gap_detected_requires_gap_start_and_end():
    receipt = _healthy_receipt()
    receipt["gap_detected"] = True
    receipt["monitoring_mode"] = "escalate"
    # no gap_start / gap_end
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("gap_start is required" in e for e in errors)
    assert any("gap_end is required" in e for e in errors)


def test_gap_false_rejects_stray_gap_fields():
    receipt = _healthy_receipt()
    receipt["gap_start"] = "2026-06-30T00:00:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("gap_start must be empty" in e for e in errors)


def test_fallback_required_requires_active_fallback():
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "degraded"
    receipt["monitoring_mode"] = "fallback_required"
    # no fallback_capture_path, fallback_capture_status defaults to not_configured
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("fallback_capture_path" in e for e in errors)
    assert any("fallback_capture_status=active" in e for e in errors)


def test_fallback_required_with_active_fallback_is_valid():
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "degraded"
    receipt["monitoring_mode"] = "fallback_required"
    receipt["fallback_capture_path"] = "s3://hummbl-compliance-fallback/openai-fedramp/"
    receipt["fallback_capture_status"] = "active"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert valid, errors


def test_risk_accepted_requires_risk_acceptance_ref():
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "degraded"
    receipt["gap_detected"] = True
    receipt["gap_start"] = "2026-07-01T00:00:00Z"
    receipt["gap_end"] = "present"
    receipt["monitoring_mode"] = "risk_accepted"
    # no risk_acceptance_ref
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("risk_acceptance_ref" in e for e in errors)


def test_risk_accepted_with_ref_is_valid():
    now = datetime.now(timezone.utc)
    gap_start = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    gap_end = (now - timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "degraded"
    receipt["gap_detected"] = True
    receipt["gap_start"] = gap_start
    receipt["gap_end"] = gap_end
    receipt["monitoring_mode"] = "risk_accepted"
    receipt["risk_acceptance_ref"] = "risk-acceptance-2026-07-04-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert valid, errors


def test_gap_exceeds_retention_requires_escalate():
    # gap_start 40 days ago, retention 30 days -> exceeds
    now = datetime.now(timezone.utc)
    gap_start = (now - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
    gap_end = (now - timedelta(days=39)).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "down"
    receipt["gap_detected"] = True
    receipt["gap_start"] = gap_start
    receipt["gap_end"] = gap_end
    receipt["monitoring_mode"] = "risk_accepted"
    receipt["risk_acceptance_ref"] = "risk-acceptance-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("must be 'escalate'" in e for e in errors)


def test_gap_within_retention_allows_risk_accepted():
    # gap_start 5 days ago, retention 30 days -> within
    now = datetime.now(timezone.utc)
    gap_start = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    gap_end = (now - timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "degraded"
    receipt["gap_detected"] = True
    receipt["gap_start"] = gap_start
    receipt["gap_end"] = gap_end
    receipt["monitoring_mode"] = "risk_accepted"
    receipt["risk_acceptance_ref"] = "risk-acceptance-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert valid, errors


def test_gap_exceeds_retention_helper():
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)
    old_start = "2026-05-15T00:00:00Z"  # 50 days before
    recent_start = "2026-07-01T00:00:00Z"  # 3 days before

    assert gap_exceeds_retention(old_start, retention_days=30, now=now) is True
    assert gap_exceeds_retention(recent_start, retention_days=30, now=now) is False


def test_validate_rejects_invalid_gap_start_bypasses_retention_escalation():
    """An invalid gap_start must not silently bypass the retention escalation check."""
    receipt = _healthy_receipt()
    receipt["endpoint_status"] = "down"
    receipt["gap_detected"] = True
    receipt["gap_start"] = "not-a-date"
    receipt["gap_end"] = "2026-07-04T00:00:00Z"
    receipt["monitoring_mode"] = "risk_accepted"  # should be escalate if gap exceeds
    receipt["risk_acceptance_ref"] = "risk-acceptance-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("gap_start must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_invalid_gap_end():
    receipt = _healthy_receipt()
    receipt["gap_detected"] = True
    receipt["gap_start"] = "2026-07-01T00:00:00Z"
    receipt["gap_end"] = "also-not-date"
    receipt["monitoring_mode"] = "risk_accepted"
    receipt["risk_acceptance_ref"] = "risk-acceptance-001"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("gap_end must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_bad_timestamp():
    receipt = _healthy_receipt()
    receipt["timestamp"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_timezoneless_timestamp():
    receipt = _healthy_receipt()
    receipt["timestamp"] = "2026-07-04T00:00:00"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_bad_oldest_required_timestamp():
    receipt = _healthy_receipt()
    receipt["oldest_required_timestamp"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("oldest_required_timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_bad_last_successful_export_at():
    receipt = _healthy_receipt()
    receipt["last_successful_export_at"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("last_successful_export_at must be an RFC3339 date-time" in e for e in errors)


def test_validate_accepts_empty_last_successful_export_at():
    """Empty last_successful_export_at is valid (means never successfully exported)."""
    receipt = _healthy_receipt()
    receipt["last_successful_export_at"] = ""
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert valid, errors


def test_validate_rejects_receipt_id_with_uppercase():
    receipt = _healthy_receipt()
    receipt["receipt_id"] = "compliance-gap-INVALID-ID"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_tampered_hash_rejected():
    receipt = _healthy_receipt()
    receipt["receipt_hash"] = "0" * 64

    valid, errors = validate_compliance_log_gap_receipt(receipt)

    assert not valid
    assert any("receipt_hash does not match" in e for e in errors)


def test_create_raises_on_invalid():
    try:
        create_compliance_log_gap_receipt(
            provider="openai",
            workspace_class="fedramp",
            endpoint="",
            endpoint_status="healthy",
            retention_days=30,
            last_successful_export_at="",
            oldest_required_timestamp="2026-06-04T00:00:00Z",
            gap_detected=False,
            monitoring_mode="monitor_only",
        )
        assert False, "should have raised"
    except ComplianceLogGapError as exc:
        assert "endpoint" in str(exc)


def test_create_omits_empty_optional_fields():
    receipt = create_compliance_log_gap_receipt(
        provider="openai",
        workspace_class="fedramp",
        endpoint="https://example.com/logs",
        endpoint_status="healthy",
        retention_days=30,
        last_successful_export_at="2026-07-04T00:00:00Z",
        oldest_required_timestamp="2026-06-04T00:00:00Z",
        gap_detected=False,
        monitoring_mode="monitor_only",
    )

    # Optional fields should not be present when empty/default
    assert "gap_start" not in receipt
    assert "gap_end" not in receipt
    assert "fallback_capture_path" not in receipt
    assert "fallback_capture_status" not in receipt
    assert "risk_acceptance_ref" not in receipt
    assert "owner" not in receipt
    assert "incident_ref" not in receipt
    assert "export_window_start" not in receipt
    assert "export_window_end" not in receipt
