"""External Runtime Verification Monitor (E3 enhancement).

Stub implementation of an external trace monitor for temporal invariant
verification. This module provides the interface for a TeSSLa-style
external monitor that runs in parallel with the governed system and
checks temporal properties over event traces.

Unlike inline monitors (P30 ReceiptIntegrityMonitor), an external monitor
provides stronger isolation — the monitor cannot be corrupted by the
monitored system. This is important for adversarial deployment environments.

This is a stub. Full implementation would require:
  - A trace ingestion protocol (file-based, socket, or shared memory)
  - A temporal specification language (TeSSLa, QEA, or LTL)
  - A monitor process that runs independently
  - A verdict emission protocol (satisfied, violated, inconclusive)

Usage (stub):
    from hummbl_governance.external_monitor import ExternalMonitor, TraceEvent

    monitor = ExternalMonitor()
    monitor.ingest(TraceEvent(timestamp="2026-09-02T12:00:00Z",
                               event_type="RECEIPT_CREATED",
                               agent_id="devin",
                               payload={"sequence_id": 42}))
    verdict = monitor.check_temporal_property("monotonic_sequence")
    print(verdict)  # Verdict.SATISFIED, Verdict.VIOLATED, or Verdict.INCONCLUSIVE

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(Enum):
    """Four-valued verdict domain (from QEA formalism)."""

    SATISFIED = "satisfied"
    """The property holds for the observed trace so far."""

    VIOLATED = "violated"
    """The property has been violated by the observed trace."""

    INCONCLUSIVE = "inconclusive"
    """The verdict cannot be determined from the observed trace so far."""

    NOT_APPLICABLE = "not_applicable"
    """The property does not apply to the observed events."""


@dataclass
class TraceEvent:
    """A single event in a trace submitted to the monitor.

    Attributes:
        timestamp: ISO 8601 timestamp with Z suffix.
        event_type: Event type (e.g., "RECEIPT_CREATED", "AUTHORITY_EXERCISED").
        agent_id: Agent that generated the event.
        payload: Event-specific data.
    """

    timestamp: str
    event_type: str
    agent_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class ExternalMonitor:
    """External runtime verification monitor (stub).

    Ingests trace events and checks temporal properties. This stub
    implements basic monotonicity checks. A full implementation would
    support TeSSLa-style temporal stream specifications.

    The monitor is designed to run in a separate process from the
    governed system, providing isolation against corruption.
    """

    def __init__(self) -> None:
        self._trace: list[TraceEvent] = []
        self._property_checks: dict[str, Any] = {}

    def ingest(self, event: TraceEvent) -> None:
        """Ingest a trace event into the monitor."""
        self._trace.append(event)

    def ingest_batch(self, events: list[TraceEvent]) -> None:
        """Ingest a batch of trace events."""
        self._trace.extend(events)

    def check_temporal_property(self, property_name: str) -> Verdict:
        """Check a temporal property against the ingested trace.

        Currently supported properties (stub):
        - monotonic_sequence: receipt sequence_ids must be monotonic
          within each agent context (K4 TEMPORAL).
        - no_receipt_gaps: receipt sequence_ids must have no gaps
          within each agent context (K11 INTEGRITY).
        - authority_always_scoped: every AUTHORITY_EXERCISED event
          must have a scope and expiry in its payload (K6 AUTHORITY).

        Args:
            property_name: Name of the temporal property to check.

        Returns:
            Verdict indicating whether the property holds.
        """
        if not self._trace:
            return Verdict.INCONCLUSIVE

        if property_name == "monotonic_sequence":
            return self._check_monotonic_sequence()
        elif property_name == "no_receipt_gaps":
            return self._check_no_receipt_gaps()
        elif property_name == "authority_always_scoped":
            return self._check_authority_scoped()
        else:
            return Verdict.NOT_APPLICABLE

    def _check_monotonic_sequence(self) -> Verdict:
        """Check that receipt sequence_ids are monotonic per agent (K4)."""
        agent_sequences: dict[str, list[int]] = {}
        for event in self._trace:
            if event.event_type != "RECEIPT_CREATED":
                continue
            seq = event.payload.get("sequence_id")
            if seq is None:
                continue
            agent_sequences.setdefault(event.agent_id, []).append(seq)

        for agent_id, sequences in agent_sequences.items():
            for i in range(1, len(sequences)):
                if sequences[i] <= sequences[i - 1]:
                    return Verdict.VIOLATED

        return Verdict.SATISFIED if agent_sequences else Verdict.INCONCLUSIVE

    def _check_no_receipt_gaps(self) -> Verdict:
        """Check that receipt sequence_ids have no gaps per agent (K11)."""
        agent_sequences: dict[str, list[int]] = {}
        for event in self._trace:
            if event.event_type != "RECEIPT_CREATED":
                continue
            seq = event.payload.get("sequence_id")
            if seq is None:
                continue
            agent_sequences.setdefault(event.agent_id, []).append(seq)

        for agent_id, sequences in agent_sequences.items():
            sequences.sort()
            for i in range(1, len(sequences)):
                if sequences[i] != sequences[i - 1] + 1:
                    return Verdict.VIOLATED

        return Verdict.SATISFIED if agent_sequences else Verdict.INCONCLUSIVE

    def _check_authority_scoped(self) -> Verdict:
        """Check that every AUTHORITY_EXERCISED event has scope and expiry (K6)."""
        authority_events = [
            e for e in self._trace
            if e.event_type == "AUTHORITY_EXERCISED"
        ]
        if not authority_events:
            return Verdict.INCONCLUSIVE

        for event in authority_events:
            if "scope" not in event.payload or "expiry" not in event.payload:
                return Verdict.VIOLATED

        return Verdict.SATISFIED

    def clear(self) -> None:
        """Clear the ingested trace."""
        self._trace.clear()
        self._property_checks.clear()

    @property
    def trace_length(self) -> int:
        """Number of events in the trace."""
        return len(self._trace)

    def export_trace(self) -> list[dict[str, Any]]:
        """Export the trace as a list of dicts (for serialization)."""
        return [
            {
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "agent_id": e.agent_id,
                "payload": e.payload,
            }
            for e in self._trace
        ]


__all__ = [
    "ExternalMonitor",
    "TraceEvent",
    "Verdict",
]
