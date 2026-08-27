from __future__ import annotations

from hummbl_cognition.hibp_receipt import (
    compute_hibp_receipt_hash,
    create_hibp_receipt,
    validate_hibp_receipt,
)


def test_hibp_receipt_accepts_safe_public_query():
    receipt = create_hibp_receipt(
        query_type="breaches",
        query_subject="all",
        operator_approval="not_required",
        findings_count=1,
        findings_summary=[{"breach_name": "Example", "breach_date": "2026-01-01"}],
    )

    valid, errors = validate_hibp_receipt(receipt)

    assert valid, errors


def test_hibp_receipt_rejects_unexpected_top_level_field():
    receipt = create_hibp_receipt(
        query_type="breaches",
        query_subject="all",
        operator_approval="not_required",
    )
    receipt["api_key"] = "hibp-secret"
    receipt["receipt_hash"] = compute_hibp_receipt_hash(receipt)

    valid, errors = validate_hibp_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in error for error in errors)


def test_hibp_receipt_rejects_findings_summary_extra_keys():
    receipt = create_hibp_receipt(
        query_type="breaches",
        query_subject="all",
        operator_approval="not_required",
        findings_summary=[{"breach_name": "Example"}],
    )
    receipt["findings_summary"][0]["email"] = "person@example.com"
    receipt["receipt_hash"] = compute_hibp_receipt_hash(receipt)

    valid, errors = validate_hibp_receipt(receipt)

    assert not valid
    assert any(
        "findings_summary" in error and "unexpected fields" in error for error in errors
    )


def test_hibp_password_range_requires_approval_for_lookup():
    receipt = create_hibp_receipt(
        query_type="pwnedpasswordsrange",
        query_subject="ABCDE",
        mode="advisory_only",
        operator_approval="not_required",
    )
    receipt["mode"] = "approved_lookup"
    receipt["receipt_hash"] = compute_hibp_receipt_hash(receipt)

    valid, errors = validate_hibp_receipt(receipt)

    assert not valid
    assert any("requires operator_approval" in error for error in errors)
