from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from hummbl_bus.bus_auditor import (
    AuditReport,
    run_audit,
    scan_format_drift,
    scan_format_drift_details,
    scan_unreviewed_proposals,
)


def _write_bus(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_scan_format_drift_empty_when_bus_missing(tmp_path: Path) -> None:
    report = scan_format_drift_details(tmp_path / "nonexistent.tsv")
    assert report.physical_rows == 0
    assert report.valid_rows == 0


def test_scan_format_drift_counts_valid_rows(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(
        bus,
        [
            "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello",
            "2026-08-15T12:01:00Z\tcodex\tall\tSITREP\tworld",
        ],
    )
    report = scan_format_drift_details(bus)
    assert report.physical_rows == 2
    assert report.valid_rows == 2
    assert report.malformed_rows == 0
    assert report.invalid_timestamps == 0
    assert report.unknown_types == ()


def test_scan_format_drift_detects_malformed(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(
        bus,
        [
            "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello",
            "only\tthree\tfields",
        ],
    )
    report = scan_format_drift_details(bus)
    assert report.physical_rows == 2
    assert report.valid_rows == 1
    assert report.malformed_rows == 1


def test_scan_format_drift_detects_bad_timestamps(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(
        bus,
        [
            "not-a-timestamp\tcodex\tall\tSTATUS\thello",
            "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tworld",
        ],
    )
    report = scan_format_drift_details(bus)
    assert report.valid_rows == 2
    assert report.invalid_timestamps == 1


def test_scan_format_drift_detects_unknown_types(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(
        bus,
        ["2026-08-15T12:00:00Z\tcodex\tall\tBOGUS_TYPE\thello"],
    )
    report = scan_format_drift_details(bus)
    assert report.unknown_types == ("BOGUS_TYPE",)


def test_scan_format_drift_detects_legacy_types(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(
        bus,
        ["2026-08-15T12:00:00Z\tcodex\tall\tAAR\thistorical review"],
    )
    report = scan_format_drift_details(bus)
    assert report.legacy_types == ("AAR",)
    assert report.unknown_types == ()


def test_scan_format_drift_compat_wrapper(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    _write_bus(bus, ["2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello"])
    physical, malformed, bad_ts, unknown = scan_format_drift(bus)
    assert physical == 1
    assert malformed == 0
    assert bad_ts == 0
    assert unknown == []


def test_scan_unreviewed_proposals_finds_open(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    ts = (now - timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{ts}\tcodex\tall\tPROPOSAL\tlane=feature-x should we do it"])
    results = scan_unreviewed_proposals(bus, window_hours=72.0, now=now)
    assert len(results) == 1
    assert results[0]["lane"] == "feature-x"


def test_scan_unreviewed_proposals_skips_acked(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    prop_ts = (now - timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ack_ts = (now - timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(
        bus,
        [
            f"{prop_ts}\tcodex\tall\tPROPOSAL\tlane=feature-x should we do it",
            f"{ack_ts}\tclaude-code\tall\tACK\tlane=feature-x approved",
        ],
    )
    results = scan_unreviewed_proposals(bus, window_hours=72.0, now=now)
    assert results == []


def test_scan_unreviewed_proposals_skips_old(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    old_ts = (now - timedelta(hours=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{old_ts}\tcodex\tall\tPROPOSAL\tlane=feature-x should we do it"])
    results = scan_unreviewed_proposals(bus, window_hours=72.0, now=now)
    assert results == []


def test_run_audit_passes_on_clean_bus(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    _write_bus(bus, ["2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello"])
    report = run_audit(bus, now=now)
    assert isinstance(report, AuditReport)
    assert report.passed
    assert report.malformed_lines == 0


def test_run_audit_fails_on_malformed(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    _write_bus(
        bus,
        [
            "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello",
            "malformed\trow",
        ],
    )
    report = run_audit(bus, now=now)
    assert not report.passed
    assert report.malformed_lines == 1


def test_run_audit_fails_on_unknown_types(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    _write_bus(bus, ["2026-08-15T12:00:00Z\tcodex\tall\tBOGUS\thello"])
    report = run_audit(bus, now=now)
    assert not report.passed
    assert "BOGUS" in report.unknown_types


def test_run_audit_posts_sitrep(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    _write_bus(bus, ["2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello"])

    posted: list[tuple] = []

    def poster(frm, to, mtype, body, bus_path):
        posted.append((frm, to, mtype, body))

    report = run_audit(bus, now=now, poster=poster)
    assert report.passed
    assert len(posted) == 1
    assert posted[0][0] == "bus-auditor"
    assert posted[0][2] == "SITREP"
    assert "audit_status=PASS" in posted[0][3]


def test_audit_report_summary(tmp_path: Path) -> None:
    report = AuditReport(
        total_lines=10,
        valid_rows=9,
        malformed_lines=1,
        invalid_timestamps=0,
    )
    summary = report.summary()
    assert "physical_rows=10" in summary
    assert "valid_rows=9" in summary
    assert "malformed=1" in summary
