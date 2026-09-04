"""Tests for the External Runtime Verification Monitor (E3 enhancement)."""

from __future__ import annotations

from hummbl_governance.external_monitor import (
    ExternalMonitor,
    TraceEvent,
    Verdict,
)


class TestExternalMonitor:
    """Core monitor functionality."""

    def test_empty_trace_is_inconclusive(self):
        monitor = ExternalMonitor()
        assert monitor.check_temporal_property("monotonic_sequence") == Verdict.INCONCLUSIVE

    def test_monotonic_sequence_satisfied(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:01Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 2},
        ))
        assert monitor.check_temporal_property("monotonic_sequence") == Verdict.SATISFIED

    def test_monotonic_sequence_violated(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 5},
        ))
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:01Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 3},
        ))
        assert monitor.check_temporal_property("monotonic_sequence") == Verdict.VIOLATED

    def test_no_receipt_gaps_satisfied(self):
        monitor = ExternalMonitor()
        for i in range(1, 5):
            monitor.ingest(TraceEvent(
                timestamp=f"2026-09-02T12:00:0{i}Z",
                event_type="RECEIPT_CREATED",
                agent_id="devin",
                payload={"sequence_id": i},
            ))
        assert monitor.check_temporal_property("no_receipt_gaps") == Verdict.SATISFIED

    def test_no_receipt_gaps_violated(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:01Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 5},
        ))
        assert monitor.check_temporal_property("no_receipt_gaps") == Verdict.VIOLATED

    def test_authority_scoped_satisfied(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="AUTHORITY_EXERCISED",
            agent_id="devin",
            payload={"scope": "read", "expiry": "2026-09-02T13:00:00Z"},
        ))
        assert monitor.check_temporal_property("authority_always_scoped") == Verdict.SATISFIED

    def test_authority_scoped_violated(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="AUTHORITY_EXERCISED",
            agent_id="devin",
            payload={"scope": "read"},  # missing expiry
        ))
        assert monitor.check_temporal_property("authority_always_scoped") == Verdict.VIOLATED

    def test_unknown_property_is_not_applicable(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        assert monitor.check_temporal_property("unknown_property") == Verdict.NOT_APPLICABLE

    def test_ingest_batch(self):
        monitor = ExternalMonitor()
        events = [
            TraceEvent(
                timestamp=f"2026-09-02T12:00:0{i}Z",
                event_type="RECEIPT_CREATED",
                agent_id="devin",
                payload={"sequence_id": i},
            )
            for i in range(1, 4)
        ]
        monitor.ingest_batch(events)
        assert monitor.trace_length == 3

    def test_clear(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        assert monitor.trace_length == 1
        monitor.clear()
        assert monitor.trace_length == 0

    def test_export_trace(self):
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        exported = monitor.export_trace()
        assert len(exported) == 1
        assert exported[0]["event_type"] == "RECEIPT_CREATED"
        assert exported[0]["agent_id"] == "devin"

    def test_per_agent_isolation(self):
        """Sequence checks are per-agent — different agents can have
        overlapping sequences without violating monotonicity."""
        monitor = ExternalMonitor()
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:00Z",
            event_type="RECEIPT_CREATED",
            agent_id="devin",
            payload={"sequence_id": 1},
        ))
        monitor.ingest(TraceEvent(
            timestamp="2026-09-02T12:00:01Z",
            event_type="RECEIPT_CREATED",
            agent_id="codex",
            payload={"sequence_id": 1},
        ))
        assert monitor.check_temporal_property("monotonic_sequence") == Verdict.SATISFIED
