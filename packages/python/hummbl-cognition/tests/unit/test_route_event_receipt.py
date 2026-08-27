from __future__ import annotations

from hummbl_cognition.route_event_receipt import (
    RouteEventError,
    compute_receipt_hash,
    create_route_event_receipt,
    validate_route_event_receipt,
)


def _incident_529_receipt() -> dict:
    """A 529 overloaded_error incident — the Claude Opus 4.8 recurrence pattern."""
    return create_route_event_receipt(
        vendor="anthropic",
        model="claude-opus-4-8",
        surface="api",
        event_class="incident",
        status_code=529,
        error_type="overloaded_error",
        retry_policy="retry_with_backoff",
        failover_policy="switch_model",
        occurrence_count=11,
        first_seen_at="2026-06-02T00:00:00Z",
        last_seen_at="2026-07-04T00:20:00Z",
        incident_ref="https://status.claude.com/incidents/jul-3-4-2026",
        evidence_refs=[
            "https://status.claude.com",
            "https://platform.claude.com/docs/en/api/errors",
        ],
        notes="Part of recurring capacity-saturation pattern Jun 2 - Jul 4 2026.",
    )


def _healthy_check_receipt() -> dict:
    return create_route_event_receipt(
        vendor="openai",
        model="gpt-5",
        surface="api",
        event_class="health_check",
        status_code=200,
        error_type="none",
        retry_policy="none",
        failover_policy="none",
    )


def test_validate_accepts_529_incident():
    valid, errors = validate_route_event_receipt(_incident_529_receipt())

    assert valid, errors


def test_validate_accepts_healthy_check():
    valid, errors = validate_route_event_receipt(_healthy_check_receipt())

    assert valid, errors


def test_validate_rejects_extra_field():
    receipt = _incident_529_receipt()
    receipt["raw_secret"] = "sk-leaked"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in e for e in errors)


def test_validate_rejects_missing_required_field():
    receipt = _incident_529_receipt()
    del receipt["retry_policy"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("missing required field: retry_policy" in e for e in errors)


def test_validate_rejects_bad_receipt_id_prefix():
    receipt = _incident_529_receipt()
    receipt["receipt_id"] = "wrong-prefix-123"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_receipt_id_with_uppercase():
    receipt = _incident_529_receipt()
    receipt["receipt_id"] = "route-evt-INVALID-ID"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_bad_timestamp():
    receipt = _incident_529_receipt()
    receipt["timestamp"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_timezoneless_timestamp():
    receipt = _incident_529_receipt()
    receipt["timestamp"] = "2026-07-04T00:00:00"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_bad_vendor():
    receipt = _incident_529_receipt()
    receipt["vendor"] = "deepseek"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("vendor:" in e for e in errors)


def test_validate_rejects_empty_model():
    receipt = _incident_529_receipt()
    receipt["model"] = ""
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("model must be a non-empty string" in e for e in errors)


def test_validate_rejects_negative_status_code():
    receipt = _incident_529_receipt()
    receipt["status_code"] = -1
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("status_code must be a non-negative integer" in e for e in errors)


def test_validate_rejects_zero_occurrence_count():
    receipt = _incident_529_receipt()
    receipt["occurrence_count"] = 0
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("occurrence_count must be an integer >= 1" in e for e in errors)


def test_incident_requires_error_or_high_status():
    receipt = _healthy_check_receipt()
    receipt["event_class"] = "incident"
    # status_code=200, error_type=none — not a valid incident
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("event_class=incident requires" in e for e in errors)


def test_recovery_requires_healthy_state_and_incident_ref():
    receipt = _incident_529_receipt()
    receipt["event_class"] = "recovery"
    receipt["status_code"] = 200
    receipt["error_type"] = "none"
    receipt["retry_policy"] = "none"
    receipt["failover_policy"] = "none"
    # no incident_ref
    del receipt["incident_ref"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("event_class=recovery requires incident_ref" in e for e in errors)


def test_recovery_with_incident_ref_is_valid():
    receipt = _incident_529_receipt()
    receipt["event_class"] = "recovery"
    receipt["status_code"] = 200
    receipt["error_type"] = "none"
    receipt["retry_policy"] = "none"
    receipt["failover_policy"] = "none"
    receipt["incident_ref"] = "https://status.claude.com/incidents/jul-3-4-2026"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_degradation_requires_incident_ref():
    receipt = _incident_529_receipt()
    receipt["event_class"] = "degradation"
    del receipt["incident_ref"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("event_class=degradation requires incident_ref" in e for e in errors)


def test_health_check_must_not_have_error():
    receipt = _healthy_check_receipt()
    receipt["error_type"] = "api_error"
    receipt["status_code"] = 500
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any(
        "event_class=health_check requires error_type='none'" in e for e in errors
    )


def test_health_check_with_500_status_rejected_even_with_no_error():
    """A health_check with status_code=500 and error_type=none is a failed probe
    masquerading as healthy — must be rejected (use 'incident' instead)."""
    receipt = _healthy_check_receipt()
    receipt["error_type"] = "none"
    receipt["status_code"] = 500
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any(
        "event_class=health_check requires status_code < 400" in e for e in errors
    )


def test_health_check_with_403_status_rejected():
    """Any 4xx/5xx status code is a failed health check, not a healthy one."""
    receipt = _healthy_check_receipt()
    receipt["status_code"] = 403
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any(
        "event_class=health_check requires status_code < 400" in e for e in errors
    )


def test_health_check_with_200_status_accepted():
    """A 200 status health check with no error is valid."""
    receipt = _healthy_check_receipt()
    receipt["status_code"] = 200
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_overloaded_error_rejects_fail_fast():
    """529 overloaded_error must NOT use fail_fast — capacity is transient."""
    receipt = _incident_529_receipt()
    receipt["retry_policy"] = "fail_fast"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("overloaded_error requires retry_policy" in e for e in errors)


def test_overloaded_error_allows_circuit_breaker_open():
    receipt = _incident_529_receipt()
    receipt["retry_policy"] = "circuit_breaker_open"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_rate_limit_error_rejects_retry_with_backoff():
    """429 rate_limit_error must NOT use retry_with_backoff — burns quota."""
    receipt = _incident_529_receipt()
    receipt["status_code"] = 429
    receipt["error_type"] = "rate_limit_error"
    receipt["retry_policy"] = "retry_with_backoff"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("rate_limit_error requires retry_policy" in e for e in errors)


def test_rate_limit_error_allows_retry_once():
    receipt = _incident_529_receipt()
    receipt["status_code"] = 429
    receipt["error_type"] = "rate_limit_error"
    receipt["retry_policy"] = "retry_once"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_silent_drop_requires_circuit_breaker_open():
    """silent_drop (false-green) must use circuit_breaker_open — fundamental breakage."""
    receipt = _incident_529_receipt()
    receipt["status_code"] = 0
    receipt["error_type"] = "silent_drop"
    receipt["retry_policy"] = "retry_with_backoff"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("silent_drop requires retry_policy" in e for e in errors)


def test_silent_drop_with_circuit_breaker_is_valid():
    receipt = _incident_529_receipt()
    receipt["status_code"] = 0
    receipt["error_type"] = "silent_drop"
    receipt["retry_policy"] = "circuit_breaker_open"
    receipt["failover_policy"] = "escalate"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_occurrence_count_gt_1_requires_first_and_last_seen():
    receipt = _incident_529_receipt()
    del receipt["first_seen_at"]
    del receipt["last_seen_at"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("occurrence_count > 1 requires first_seen_at" in e for e in errors)
    assert any("occurrence_count > 1 requires last_seen_at" in e for e in errors)


def test_first_seen_must_precede_last_seen():
    receipt = _incident_529_receipt()
    receipt["first_seen_at"] = "2026-07-04T00:00:00Z"
    receipt["last_seen_at"] = "2026-06-02T00:00:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("first_seen_at must be <= last_seen_at" in e for e in errors)


def test_last_seen_must_precede_timestamp():
    receipt = _incident_529_receipt()
    receipt["last_seen_at"] = "2026-07-05T00:00:00Z"
    receipt["timestamp"] = "2026-07-04T00:00:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("last_seen_at must be <= timestamp" in e for e in errors)


def test_validate_rejects_invalid_first_seen_at():
    """An invalid first_seen_at must not silently bypass the temporal ordering check."""
    receipt = _incident_529_receipt()
    receipt["occurrence_count"] = 3
    receipt["first_seen_at"] = "not-a-date"
    receipt["last_seen_at"] = "2026-07-04T00:00:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("first_seen_at must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_invalid_last_seen_at():
    receipt = _incident_529_receipt()
    receipt["occurrence_count"] = 3
    receipt["first_seen_at"] = "2026-07-01T00:00:00Z"
    receipt["last_seen_at"] = "also-not-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("last_seen_at must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_timezoneless_first_seen_at():
    receipt = _incident_529_receipt()
    receipt["occurrence_count"] = 2
    receipt["first_seen_at"] = "2026-07-01T00:00:00"
    receipt["last_seen_at"] = "2026-07-04T00:00:00Z"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("first_seen_at must be an RFC3339 date-time" in e for e in errors)


def test_tampered_hash_rejected():
    receipt = _incident_529_receipt()
    receipt["receipt_hash"] = "0" * 64

    valid, errors = validate_route_event_receipt(receipt)

    assert not valid
    assert any("receipt_hash does not match" in e for e in errors)


def test_create_raises_on_invalid():
    try:
        create_route_event_receipt(
            vendor="anthropic",
            model="",
            surface="api",
            event_class="incident",
            status_code=529,
            error_type="overloaded_error",
            retry_policy="retry_with_backoff",
            failover_policy="switch_model",
        )
        assert False, "should have raised"
    except RouteEventError as exc:
        assert "model" in str(exc)


def test_create_omits_empty_optional_fields():
    receipt = create_route_event_receipt(
        vendor="openai",
        model="gpt-5",
        surface="api",
        event_class="health_check",
        status_code=200,
        error_type="none",
        retry_policy="none",
        failover_policy="none",
    )

    assert "incident_ref" not in receipt
    assert "first_seen_at" not in receipt
    assert "last_seen_at" not in receipt
    assert "evidence_refs" not in receipt
    assert "notes" not in receipt


def test_github_copilot_silent_drop_scenario():
    """The GitHub Copilot Cloud Agent silent-failure incident (Jun 26-28 2026)."""
    receipt = create_route_event_receipt(
        vendor="github",
        model="copilot-cloud-agent",
        surface="github-agent",
        event_class="degradation",
        status_code=0,
        error_type="silent_drop",
        retry_policy="circuit_breaker_open",
        failover_policy="escalate",
        occurrence_count=1,
        incident_ref="https://www.githubstatus.com/history",
        notes="Built-in tools unavailable with silent failures Jun 26-28 2026.",
    )

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors


def test_sonnet_5_tokenizer_cost_event():
    """A Sonnet 5 tokenizer cost-delta event — feeds route admission registry."""
    receipt = create_route_event_receipt(
        vendor="anthropic",
        model="claude-sonnet-5",
        surface="api",
        event_class="health_check",
        status_code=200,
        error_type="none",
        retry_policy="none",
        failover_policy="none",
        notes="Tokenizer produces ~30% more tokens. Cost delta confirmed. Route admission pending replay receipt.",
    )

    valid, errors = validate_route_event_receipt(receipt)

    assert valid, errors
