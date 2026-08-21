"""Tests for the Receipt Integrity Monitor primitive (P30)."""

from __future__ import annotations

import pytest

from hummbl_governance.kernel.receipt_integrity_monitor import (
    check_sequence,
    check_hash_chain,
    check_timestamps,
    run_integrity_check,
    validate_receipt_integrity_monitor,
    validate_monitor_report,
)
from hummbl_governance.schema_validator import ValidationError


def _receipt(seq, hash_val, prev_hash="", ts="", rid=""):
    return {
        "sequence_id": seq,
        "receipt_hash": hash_val,
        "prev_receipt_hash": prev_hash,
        "timestamp": ts,
        "receipt_id": rid or f"r-{seq}",
    }


class TestCheckSequence:
    def test_empty_list_passes(self):
        passed, gaps = check_sequence([])
        assert passed is True
        assert gaps == []

    def test_contiguous_passes(self):
        receipts = [_receipt(i, f"h{i}") for i in range(5)]
        passed, gaps = check_sequence(receipts)
        assert passed is True
        assert gaps == []

    def test_single_receipt_passes(self):
        receipts = [_receipt(0, "h0")]
        passed, gaps = check_sequence(receipts)
        assert passed is True

    def test_gap_detected(self):
        receipts = [_receipt(0, "h0"), _receipt(1, "h1"), _receipt(5, "h5")]
        passed, gaps = check_sequence(receipts)
        assert passed is False
        assert len(gaps) == 1
        assert gaps[0]["expected_sequence"] == 2
        assert gaps[0]["found_sequence"] == 5
        assert gaps[0]["missing_count"] == 3

    def test_multiple_gaps_detected(self):
        receipts = [
            _receipt(0, "h0"),
            _receipt(3, "h3"),
            _receipt(7, "h7"),
        ]
        passed, gaps = check_sequence(receipts)
        assert passed is False
        assert len(gaps) == 2


class TestCheckHashChain:
    def test_empty_list_passes(self):
        passed, broken = check_hash_chain([])
        assert passed is True
        assert broken == []

    def test_valid_chain_passes(self):
        passed, broken = check_hash_chain([])
        assert passed is True

    def test_first_receipt_empty_prev_ok(self):
        receipts = [_receipt(0, "aaa", prev_hash="")]
        passed, broken = check_hash_chain(receipts)
        assert passed is True

    def test_broken_link_detected(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(1, "bbb", prev_hash="WRONG"),
            _receipt(2, "ccc", prev_hash="bbb"),
        ]
        passed, broken = check_hash_chain(receipts)
        assert passed is False
        assert len(broken) == 1
        assert broken[0]["expected_prev_hash"] == "aaa"
        assert broken[0]["actual_prev_hash"] == "WRONG"

    def test_none_prev_hash_treated_as_empty(self):
        receipts = [_receipt(0, "aaa", prev_hash=None)]
        passed, broken = check_hash_chain(receipts)
        assert passed is True


class TestCheckTimestamps:
    def test_empty_list_passes(self):
        passed, anomalies = check_timestamps([])
        assert passed is True

    def test_in_order_passes(self):
        receipts = [
            _receipt(0, "h0", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "h1", ts="2026-01-01T11:00:00Z"),
            _receipt(2, "h2", ts="2026-01-01T12:00:00Z"),
        ]
        passed, anomalies = check_timestamps(receipts)
        assert passed is True

    def test_retroactive_insertion_detected(self):
        receipts = [
            _receipt(0, "h0", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "h1", ts="2026-01-01T09:00:00Z"),
        ]
        passed, anomalies = check_timestamps(receipts)
        assert passed is False
        assert len(anomalies) == 1
        assert anomalies[0]["anomaly_type"] == "retroactive_insertion"

    def test_no_timestamps_passes(self):
        receipts = [_receipt(0, "h0"), _receipt(1, "h1")]
        passed, anomalies = check_timestamps(receipts)
        assert passed is True


class TestRunIntegrityCheck:
    def test_all_pass(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T11:00:00Z"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is False
        assert report["panic_details"] is None
        assert report["check_results"]["sequence_check"]["passed"] is True
        assert report["check_results"]["hash_chain_check"]["passed"] is True
        assert report["check_results"]["timestamp_check"]["passed"] is True

    def test_sequence_gap_triggers_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(5, "bbb", prev_hash="aaa"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is True
        assert report["panic_details"]["invariant_violated"] == "K4"

    def test_hash_break_triggers_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(1, "bbb", prev_hash="WRONG"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        assert report["panic_triggered"] is True
        assert report["panic_details"]["invariant_violated"] == "K1"

    def test_empty_receipts(self):
        report = run_integrity_check([], "agent-001")
        assert report["panic_triggered"] is False
        assert report["check_results"]["sequence_check"]["receipts_scanned"] == 0


class TestSchemaValidation:
    def test_valid_report_passes(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T11:00:00Z"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        validate_receipt_integrity_monitor(report)

    def test_missing_required_fails(self):
        with pytest.raises(ValidationError):
            validate_receipt_integrity_monitor({"schema_version": "1.0.0"})

    def test_invalid_invariant_enum_fails(self):
        report = run_integrity_check(
            [_receipt(0, "aaa"), _receipt(5, "bbb", prev_hash="aaa")], "agent-001"
        )
        report["panic_details"]["invariant_violated"] = "K99"
        with pytest.raises(ValidationError):
            validate_receipt_integrity_monitor(report)


class TestValidateMonitorReport:
    def test_consistent_pass_report(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T11:00:00Z"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        validate_monitor_report(report)

    def test_consistent_fail_report(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(5, "bbb", prev_hash="aaa"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        validate_monitor_report(report)

    def test_inconsistent_pass_with_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash="", ts="2026-01-01T10:00:00Z"),
            _receipt(1, "bbb", prev_hash="aaa", ts="2026-01-01T11:00:00Z"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        report["panic_triggered"] = True
        report["panic_details"] = {
            "invariant_violated": "K1",
            "severity": "CRITICAL",
            "description": "fake panic",
        }
        with pytest.raises(ValueError, match="passed but panic_triggered is True"):
            validate_monitor_report(report)

    def test_inconsistent_fail_without_panic(self):
        receipts = [
            _receipt(0, "aaa", prev_hash=""),
            _receipt(5, "bbb", prev_hash="aaa"),
        ]
        report = run_integrity_check(receipts, "agent-001")
        report["panic_triggered"] = False
        report["panic_details"] = None
        with pytest.raises(ValueError, match="failed but panic_triggered is False"):
            validate_monitor_report(report)
