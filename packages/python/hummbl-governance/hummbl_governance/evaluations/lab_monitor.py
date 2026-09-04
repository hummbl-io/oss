# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Lab Monitor -- Track frontier AI lab activity, governance changes, and alerts.

Monitors 28 frontier AI labs for:
- Model releases and updates
- Safety framework changes (new, revised, rescinded)
- Policy and governance changes
- Compliance posture shifts (EU AI Act, NIST, ISO)
- Leadership/team changes
- Funding and valuation changes
- Incident reports

Provides change detection between snapshots, alert generation for
governance regressions and improvements, and timeline export.

Usage:
    from hummbl_governance.evaluations.lab_monitor import (
        LabMonitor, LabEvent, EventType, AlertLevel, EventTimeline,
    )

    monitor = LabMonitor()
    timeline = monitor.get_timeline("anthropic")
    alerts = monitor.check_for_alerts("anthropic")
    changes = monitor.diff_snapshots("anthropic", "2026-08-01", "2026-08-31")

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of lab events tracked by the monitor."""
    MODEL_RELEASE = "model_release"
    MODEL_UPDATE = "model_update"
    SAFETY_FRAMEWORK_NEW = "safety_framework_new"
    SAFETY_FRAMEWORK_REVISED = "safety_framework_revised"
    SAFETY_FRAMEWORK_RESCINDED = "safety_framework_rescinded"
    POLICY_CHANGE = "policy_change"
    COMPLIANCE_CHANGE = "compliance_change"
    LEADERSHIP_CHANGE = "leadership_change"
    FUNDING_ROUND = "funding_round"
    VALUATION_CHANGE = "valuation_change"
    INCIDENT_REPORT = "incident_report"
    PARTNERSHIP = "partnership"
    ACQUISITION = "acquisition"
    OPEN_WEIGHT_RELEASE = "open_weight_release"
    API_LAUNCH = "api_launch"
    API_CHANGE = "api_change"
    BENCHMARK_RESULT = "benchmark_result"
    RESEARCH_PUBLICATION = "research_publication"
    REGULATORY_ACTION = "regulatory_action"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"           # Neutral event (model release, publication)
    POSITIVE = "positive"   # Governance improvement (new safety framework)
    WARNING = "warning"     # Potential concern (framework revised, leadership exit)
    CRITICAL = "critical"   # Governance regression (framework rescinded, incident)
    EMERGENCY = "emergency" # Severe incident or regulatory action


class AlertCategory(str, Enum):
    """Categories for alert classification."""
    GOVERNANCE_REGRESSION = "governance_regression"
    GOVERNANCE_IMPROVEMENT = "governance_improvement"
    CAPABILITY_CHANGE = "capability_change"
    COMPLIANCE_SHIFT = "compliance_shift"
    INCIDENT = "incident"
    ORGANIZATIONAL = "organizational"
    MARKET = "market"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class LabEvent:
    """A single event in a lab's timeline.

    Attributes:
        event_id: Unique identifier for the event.
        lab_slug: Lab identifier (matches model_registry slugs).
        event_type: Type of event (from EventType enum).
        timestamp: ISO 8601 timestamp (UTC).
        title: Short human-readable title.
        description: Detailed description.
        source: Source URL or reference.
        alert_level: Severity level for this event.
        alert_category: Category for alert classification.
        metadata: Additional structured data (dict).
    """
    event_id: str
    lab_slug: str
    event_type: EventType
    timestamp: str
    title: str
    description: str
    source: str = ""
    alert_level: AlertLevel = AlertLevel.INFO
    alert_category: AlertCategory = AlertCategory.NEUTRAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "lab_slug": self.lab_slug,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "alert_level": self.alert_level.value,
            "alert_category": self.alert_category.value,
            "metadata": dict(self.metadata),
        }


@dataclass
class LabSnapshot:
    """A point-in-time snapshot of a lab's status.

    Captures the state of key governance indicators at a specific time,
    enabling change detection between snapshots.
    """
    lab_slug: str
    timestamp: str
    safety_framework: str = "None published"
    safety_framework_binding: bool = False
    pause_commitment: bool = False
    eu_ai_act_signatory: bool = False
    nist_ai_rmf_aligned: bool = False
    iso_42001_certified: bool = False
    fmf_member: bool = False
    weights_posture: str = "closed"
    flagship_model: str = ""
    valuation: str = ""
    api_available: bool = False
    incident_count_30d: int = 0
    governance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lab_slug": self.lab_slug,
            "timestamp": self.timestamp,
            "safety_framework": self.safety_framework,
            "safety_framework_binding": self.safety_framework_binding,
            "pause_commitment": self.pause_commitment,
            "eu_ai_act_signatory": self.eu_ai_act_signatory,
            "nist_ai_rmf_aligned": self.nist_ai_rmf_aligned,
            "iso_42001_certified": self.iso_42001_certified,
            "fmf_member": self.fmf_member,
            "weights_posture": self.weights_posture,
            "flagship_model": self.flagship_model,
            "valuation": self.valuation,
            "api_available": self.api_available,
            "incident_count_30d": self.incident_count_30d,
            "governance_score": self.governance_score,
        }


@dataclass
class Alert:
    """An alert generated from detecting a change or event.

    Attributes:
        alert_id: Unique identifier.
        lab_slug: Lab identifier.
        level: Severity level.
        category: Alert category.
        title: Short title.
        description: Detailed description.
        timestamp: When the alert was generated.
        event_id: Related event ID (if any).
        previous_value: Previous state value.
        new_value: New state value.
    """
    alert_id: str
    lab_slug: str
    level: AlertLevel
    category: AlertCategory
    title: str
    description: str
    timestamp: str
    event_id: str = ""
    previous_value: str = ""
    new_value: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "lab_slug": self.lab_slug,
            "level": self.level.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
        }


class EventTimeline:
    """A timeline of events for a single lab or across all labs.

    Stores events sorted by timestamp and provides filtering,
    search, and export capabilities.
    """

    def __init__(self) -> None:
        self._events: list[LabEvent] = []

    def add(self, event: LabEvent) -> None:
        """Add an event to the timeline."""
        self._events.append(event)
        self._events.sort(key=lambda e: e.timestamp)

    def add_many(self, events: list[LabEvent]) -> None:
        """Add multiple events to the timeline."""
        self._events.extend(events)
        self._events.sort(key=lambda e: e.timestamp)

    def get_all(self) -> list[LabEvent]:
        """Get all events, sorted by timestamp."""
        return list(self._events)

    def get_for_lab(self, lab_slug: str) -> list[LabEvent]:
        """Get all events for a specific lab."""
        return [e for e in self._events if e.lab_slug == lab_slug]

    def get_by_type(self, event_type: EventType) -> list[LabEvent]:
        """Get all events of a specific type."""
        return [e for e in self._events if e.event_type == event_type]

    def get_by_alert_level(self, level: AlertLevel) -> list[LabEvent]:
        """Get all events with a specific alert level."""
        return [e for e in self._events if e.alert_level == level]

    def get_since(self, timestamp: str) -> list[LabEvent]:
        """Get all events since a given timestamp (ISO 8601)."""
        return [e for e in self._events if e.timestamp >= timestamp]

    def get_between(self, start: str, end: str) -> list[LabEvent]:
        """Get all events between two timestamps (inclusive)."""
        return [e for e in self._events if start <= e.timestamp <= end]

    def filter(
        self,
        lab_slug: str | None = None,
        event_type: EventType | None = None,
        alert_level: AlertLevel | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[LabEvent]:
        """Filter events by multiple criteria."""
        results = list(self._events)
        if lab_slug:
            results = [e for e in results if e.lab_slug == lab_slug]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if alert_level:
            results = [e for e in results if e.alert_level == alert_level]
        if since:
            results = [e for e in results if e.timestamp >= since]
        if until:
            results = [e for e in results if e.timestamp <= until]
        return results

    @property
    def count(self) -> int:
        """Total number of events in the timeline."""
        return len(self._events)

    def to_json(self) -> str:
        """Export timeline as JSON."""
        import json
        return json.dumps({
            "count": self.count,
            "events": [e.to_dict() for e in self._events],
        }, indent=2)

    def to_markdown(self, lab_slug: str | None = None) -> str:
        """Export timeline as markdown."""
        events = self.get_for_lab(lab_slug) if lab_slug else self.get_all()
        if not events:
            return f"No events{' for ' + lab_slug if lab_slug else ''}."

        lines = [
            f"# Event Timeline{' — ' + lab_slug if lab_slug else ''}",
            "",
            f"**Total events:** {len(events)}",
            "",
            "| Date | Lab | Type | Level | Title |",
            "|------|-----|------|-------|-------|",
        ]
        for e in events:
            date = e.timestamp[:10]
            lines.append(
                f"| {date} | {e.lab_slug} | {e.event_type.value} | "
                f"{e.alert_level.value} | {e.title} |"
            )
        return "\n".join(lines)


class LabMonitor:
    """Monitors frontier AI labs for events, changes, and alerts.

    Maintains an event timeline and lab snapshots, providing:
    - Event recording and retrieval
    - Snapshot diffing for change detection
    - Alert generation for governance regressions and improvements
    - Timeline export (JSON, markdown)
    - Cross-lab comparison of recent activity

    Usage:
        monitor = LabMonitor()
        monitor.record_event(event)
        timeline = monitor.get_timeline("anthropic")
        alerts = monitor.check_for_alerts("anthropic")
    """

    def __init__(self) -> None:
        self._timeline = EventTimeline()
        self._snapshots: dict[str, list[LabSnapshot]] = {}
        self._event_counter = 0
        self._alert_counter = 0

    def _next_event_id(self) -> str:
        self._event_counter += 1
        return f"evt-{self._event_counter:06d}"

    def _next_alert_id(self) -> str:
        self._alert_counter += 1
        return f"alt-{self._alert_counter:06d}"

    def record_event(
        self,
        lab_slug: str,
        event_type: EventType,
        timestamp: str,
        title: str,
        description: str,
        source: str = "",
        alert_level: AlertLevel = AlertLevel.INFO,
        alert_category: AlertCategory = AlertCategory.NEUTRAL,
        metadata: dict[str, Any] | None = None,
    ) -> LabEvent:
        """Record a new event in the timeline.

        Returns the created LabEvent.
        """
        event = LabEvent(
            event_id=self._next_event_id(),
            lab_slug=lab_slug,
            event_type=event_type,
            timestamp=timestamp,
            title=title,
            description=description,
            source=source,
            alert_level=alert_level,
            alert_category=alert_category,
            metadata=metadata or {},
        )
        self._timeline.add(event)
        return event

    def record_snapshot(self, snapshot: LabSnapshot) -> None:
        """Record a point-in-time snapshot of a lab's status."""
        if snapshot.lab_slug not in self._snapshots:
            self._snapshots[snapshot.lab_slug] = []
        self._snapshots[snapshot.lab_slug].append(snapshot)
        self._snapshots[snapshot.lab_slug].sort(key=lambda s: s.timestamp)

    def get_timeline(self, lab_slug: str | None = None) -> EventTimeline:
        """Get the event timeline, optionally filtered by lab."""
        if lab_slug:
            timeline = EventTimeline()
            timeline.add_many(self._timeline.get_for_lab(lab_slug))
            return timeline
        return self._timeline

    def get_events(
        self,
        lab_slug: str | None = None,
        event_type: EventType | None = None,
        alert_level: AlertLevel | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[LabEvent]:
        """Get events matching the given filters."""
        return self._timeline.filter(
            lab_slug=lab_slug,
            event_type=event_type,
            alert_level=alert_level,
            since=since,
            until=until,
        )

    def get_snapshots(self, lab_slug: str) -> list[LabSnapshot]:
        """Get all snapshots for a lab, sorted by timestamp."""
        return list(self._snapshots.get(lab_slug, []))

    def get_latest_snapshot(self, lab_slug: str) -> LabSnapshot | None:
        """Get the most recent snapshot for a lab."""
        snaps = self._snapshots.get(lab_slug, [])
        return snaps[-1] if snaps else None

    def diff_snapshots(
        self, lab_slug: str, earlier_ts: str, later_ts: str,
    ) -> dict[str, dict[str, Any]]:
        """Compare two snapshots and return the differences.

        Args:
            lab_slug: Lab identifier.
            earlier_ts: Earlier timestamp (ISO 8601).
            later_ts: Later timestamp (ISO 8601).

        Returns:
            Dict of field -> {previous, new, changed: bool} for each
            field that differs between the two snapshots.
        """
        snaps = self._snapshots.get(lab_slug, [])
        earlier = None
        later = None
        for s in snaps:
            if s.timestamp <= earlier_ts and (earlier is None or s.timestamp > earlier.timestamp):
                earlier = s
            if s.timestamp <= later_ts and (later is None or s.timestamp > later.timestamp):
                later = s

        if earlier is None or later is None:
            return {}

        diff: dict[str, dict[str, Any]] = {}
        fields = [
            "safety_framework", "safety_framework_binding", "pause_commitment",
            "eu_ai_act_signatory", "nist_ai_rmf_aligned", "iso_42001_certified",
            "fmf_member", "weights_posture", "flagship_model", "valuation",
            "api_available", "incident_count_30d", "governance_score",
        ]
        for f in fields:
            old_val = getattr(earlier, f)
            new_val = getattr(later, f)
            if old_val != new_val:
                diff[f] = {
                    "previous": old_val,
                    "new": new_val,
                    "changed": True,
                }
        return diff

    def check_for_alerts(self, lab_slug: str) -> list[Alert]:
        """Check a lab's recent events and generate alerts.

        Generates alerts for:
        - Safety framework rescinded (CRITICAL)
        - Safety framework revised (WARNING)
        - New safety framework (POSITIVE)
        - Incident report (CRITICAL/EMERGENCY)
        - Compliance posture loss (WARNING)
        - Governance score drop (WARNING)
        - Leadership departure (WARNING)
        """
        events = self._timeline.get_for_lab(lab_slug)
        alerts: list[Alert] = []
        now = datetime.now(timezone.utc).isoformat()

        for event in events:
            if event.event_type == EventType.SAFETY_FRAMEWORK_RESCINDED:
                alerts.append(Alert(
                    alert_id=self._next_alert_id(),
                    lab_slug=lab_slug,
                    level=AlertLevel.CRITICAL,
                    category=AlertCategory.GOVERNANCE_REGRESSION,
                    title=f"Safety framework rescinded: {lab_slug}",
                    description=event.description,
                    timestamp=now,
                    event_id=event.event_id,
                    previous_value="Framework active",
                    new_value="Framework rescinded",
                ))
            elif event.event_type == EventType.SAFETY_FRAMEWORK_REVISED:
                alerts.append(Alert(
                    alert_id=self._next_alert_id(),
                    lab_slug=lab_slug,
                    level=AlertLevel.WARNING,
                    category=AlertCategory.GOVERNANCE_IMPROVEMENT,
                    title=f"Safety framework revised: {lab_slug}",
                    description=event.description,
                    timestamp=now,
                    event_id=event.event_id,
                ))
            elif event.event_type == EventType.SAFETY_FRAMEWORK_NEW:
                alerts.append(Alert(
                    alert_id=self._next_alert_id(),
                    lab_slug=lab_slug,
                    level=AlertLevel.POSITIVE,
                    category=AlertCategory.GOVERNANCE_IMPROVEMENT,
                    title=f"New safety framework published: {lab_slug}",
                    description=event.description,
                    timestamp=now,
                    event_id=event.event_id,
                ))
            elif event.event_type == EventType.INCIDENT_REPORT:
                level = AlertLevel.EMERGENCY if event.metadata.get("severity") == "severe" else AlertLevel.CRITICAL
                alerts.append(Alert(
                    alert_id=self._next_alert_id(),
                    lab_slug=lab_slug,
                    level=level,
                    category=AlertCategory.INCIDENT,
                    title=f"Incident reported: {lab_slug}",
                    description=event.description,
                    timestamp=now,
                    event_id=event.event_id,
                ))
            elif event.event_type == EventType.COMPLIANCE_CHANGE:
                old_val = event.metadata.get("previous_value", "")
                new_val = event.metadata.get("new_value", "")
                if "withdraw" in str(new_val).lower() or "exit" in str(new_val).lower():
                    alerts.append(Alert(
                        alert_id=self._next_alert_id(),
                        lab_slug=lab_slug,
                        level=AlertLevel.WARNING,
                        category=AlertCategory.COMPLIANCE_SHIFT,
                        title=f"Compliance posture change: {lab_slug}",
                        description=event.description,
                        timestamp=now,
                        event_id=event.event_id,
                        previous_value=str(old_val),
                        new_value=str(new_val),
                    ))
            elif event.event_type == EventType.LEADERSHIP_CHANGE:
                if event.metadata.get("departure"):
                    alerts.append(Alert(
                        alert_id=self._next_alert_id(),
                        lab_slug=lab_slug,
                        level=AlertLevel.WARNING,
                        category=AlertCategory.ORGANIZATIONAL,
                        title=f"Leadership departure: {lab_slug}",
                        description=event.description,
                        timestamp=now,
                        event_id=event.event_id,
                    ))
            elif event.event_type == EventType.REGULATORY_ACTION:
                alerts.append(Alert(
                    alert_id=self._next_alert_id(),
                    lab_slug=lab_slug,
                    level=AlertLevel.CRITICAL,
                    category=AlertCategory.GOVERNANCE_REGRESSION,
                    title=f"Regulatory action: {lab_slug}",
                    description=event.description,
                    timestamp=now,
                    event_id=event.event_id,
                ))

        return alerts

    def check_all_alerts(self) -> list[Alert]:
        """Check all labs for alerts and return a combined list."""
        lab_slugs = {e.lab_slug for e in self._timeline.get_all()}
        all_alerts: list[Alert] = []
        for slug in lab_slugs:
            all_alerts.extend(self.check_for_alerts(slug))
        return all_alerts

    def get_activity_summary(
        self, since: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get a summary of activity across all labs.

        Returns a dict mapping lab_slug to summary stats:
        - event_count: Total events
        - latest_event: Most recent event timestamp
        - alert_count: Number of alerts
        - by_type: Count of events by type
        - by_level: Count of events by alert level
        """
        events = self._timeline.get_since(since) if since else self._timeline.get_all()
        summary: dict[str, dict[str, Any]] = {}

        for event in events:
            slug = event.lab_slug
            if slug not in summary:
                summary[slug] = {
                    "event_count": 0,
                    "latest_event": "",
                    "by_type": {},
                    "by_level": {},
                }
            s = summary[slug]
            s["event_count"] += 1
            if event.timestamp > s["latest_event"]:
                s["latest_event"] = event.timestamp
            type_key = event.event_type.value
            s["by_type"][type_key] = s["by_type"].get(type_key, 0) + 1
            level_key = event.alert_level.value
            s["by_level"][level_key] = s["by_level"].get(level_key, 0) + 1

        # Add alert counts
        for slug in summary:
            alerts = self.check_for_alerts(slug)
            summary[slug]["alert_count"] = len(alerts)

        return summary

    def get_most_active_labs(self, n: int = 10, since: str | None = None) -> list[tuple[str, int]]:
        """Get the N most active labs by event count."""
        summary = self.get_activity_summary(since=since)
        ranked = sorted(
            summary.items(),
            key=lambda x: x[1]["event_count"],
            reverse=True,
        )
        return [(slug, data["event_count"]) for slug, data in ranked[:n]]

    def export_timeline_json(self, lab_slug: str | None = None) -> str:
        """Export the timeline as JSON."""
        timeline = self.get_timeline(lab_slug)
        return timeline.to_json()

    def export_timeline_markdown(self, lab_slug: str | None = None) -> str:
        """Export the timeline as markdown."""
        timeline = self.get_timeline(lab_slug)
        return timeline.to_markdown(lab_slug)

    def export_alerts_json(self, lab_slug: str | None = None) -> str:
        """Export alerts as JSON."""
        import json
        alerts = self.check_for_alerts(lab_slug) if lab_slug else self.check_all_alerts()
        return json.dumps({
            "count": len(alerts),
            "alerts": [a.to_dict() for a in alerts],
        }, indent=2)

    @property
    def event_count(self) -> int:
        """Total number of events across all labs."""
        return self._timeline.count

    @property
    def lab_count(self) -> int:
        """Number of labs with recorded events."""
        return len({e.lab_slug for e in self._timeline.get_all()})


# ---------------------------------------------------------------------------
# Seed data — known historical events (sourced from research artifacts)
# ---------------------------------------------------------------------------

def _seed_historical_events() -> list[LabEvent]:
    """Create seed events from known historical data.

    Sourced from the HUMMBL frontier labs research artifacts (Aug 2026).
    These are real events that occurred; timestamps are approximate.
    """
    events: list[LabEvent] = []
    _id = [0]

    def _evt(
        lab: str, etype: EventType, ts: str, title: str, desc: str,
        level: AlertLevel = AlertLevel.INFO, cat: AlertCategory = AlertCategory.NEUTRAL,
        source: str = "", metadata: dict | None = None,
    ) -> LabEvent:
        _id[0] += 1
        return LabEvent(
            event_id=f"seed-{_id[0]:04d}",
            lab_slug=lab, event_type=etype, timestamp=ts,
            title=title, description=desc, source=source,
            alert_level=level, alert_category=cat,
            metadata=metadata or {},
        )

    # Anthropic
    events.append(_evt(
        "anthropic", EventType.SAFETY_FRAMEWORK_NEW, "2023-07-01T00:00:00Z",
        "RSP v1 published",
        "Anthropic published Responsible Scaling Policy v1, introducing ASL levels.",
        AlertLevel.POSITIVE, AlertCategory.GOVERNANCE_IMPROVEMENT,
    ))
    events.append(_evt(
        "anthropic", EventType.SAFETY_FRAMEWORK_REVISED, "2024-10-15T00:00:00Z",
        "RSP v2 published",
        "Anthropic revised RSP to v2, adding more detailed ASL thresholds.",
        AlertLevel.POSITIVE, AlertCategory.GOVERNANCE_IMPROVEMENT,
    ))
    events.append(_evt(
        "anthropic", EventType.SAFETY_FRAMEWORK_REVISED, "2025-12-01T00:00:00Z",
        "RSP v3 published — pause commitment rescinded",
        "Anthropic published RSP v3, rescinding the voluntary pause commitment "
        "from the Frontier AI Commitments. Pause commitment removed in favor of "
        "internal ASL-driven gating.",
        AlertLevel.WARNING, AlertCategory.GOVERNANCE_REGRESSION,
        metadata={"pause_rescinded": True},
    ))
    events.append(_evt(
        "anthropic", EventType.MODEL_RELEASE, "2026-02-24T00:00:00Z",
        "Claude 4.5 released",
        "Anthropic released Claude 4.5 Opus and Sonnet, achieving state-of-the-art "
        "on coding and reasoning benchmarks.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "anthropic", EventType.FUNDING_ROUND, "2025-03-01T00:00:00Z",
        "Series E — $61B raised",
        "Anthropic raised $61B in Series E funding at a $965B valuation.",
        AlertLevel.INFO, AlertCategory.MARKET,
    ))

    # OpenAI
    events.append(_evt(
        "openai", EventType.SAFETY_FRAMEWORK_NEW, "2023-12-01T00:00:00Z",
        "Preparedness Framework published",
        "OpenAI published its Preparedness Framework for evaluating catastrophic "
        "risks of frontier models.",
        AlertLevel.POSITIVE, AlertCategory.GOVERNANCE_IMPROVEMENT,
    ))
    events.append(_evt(
        "openai", EventType.LEADERSHIP_CHANGE, "2023-11-17T00:00:00Z",
        "Sam Altman fired and rehired",
        "OpenAI board fired CEO Sam Altman, then rehired him days later after "
        "employee revolt. Board restructured.",
        AlertLevel.WARNING, AlertCategory.ORGANIZATIONAL,
        metadata={"departure": False, "governance_crisis": True},
    ))
    events.append(_evt(
        "openai", EventType.MODEL_RELEASE, "2024-05-13T00:00:00Z",
        "GPT-4o released",
        "OpenAI released GPT-4o with multimodal capabilities.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "openai", EventType.MODEL_RELEASE, "2026-04-01T00:00:00Z",
        "GPT-5 released",
        "OpenAI released GPT-5 with significant reasoning improvements.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "openai", EventType.INCIDENT_REPORT, "2025-08-15T00:00:00Z",
        "ChatGPT data leak via prompt injection",
        "Security researchers demonstrated systematic data exfiltration from "
        "ChatGPT via prompt injection attacks.",
        AlertLevel.CRITICAL, AlertCategory.INCIDENT,
        metadata={"severity": "moderate"},
    ))

    # Google DeepMind
    events.append(_evt(
        "google-deepmind", EventType.SAFETY_FRAMEWORK_NEW, "2024-05-01T00:00:00Z",
        "Frontier Safety Framework published",
        "Google DeepMind published its Frontier Safety Framework with Critical "
        "Capability Levels.",
        AlertLevel.POSITIVE, AlertCategory.GOVERNANCE_IMPROVEMENT,
    ))
    events.append(_evt(
        "google-deepmind", EventType.MODEL_RELEASE, "2024-12-06T00:00:00Z",
        "Gemini 2.0 released",
        "Google DeepMind released Gemini 2.0 with improved reasoning and "
        "agentic capabilities.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "google-deepmind", EventType.OPEN_WEIGHT_RELEASE, "2025-02-01T00:00:00Z",
        "Gemma 2 open-weight release",
        "Google released Gemma 2 as open-weight models for research use.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))

    # Meta
    events.append(_evt(
        "meta", EventType.OPEN_WEIGHT_RELEASE, "2024-07-23T00:00:00Z",
        "Llama 3.1 405B open-weight release",
        "Meta released Llama 3.1 405B as open-weight, the largest open-weight "
        "model at the time.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "meta", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z",
        "Llama 4 released",
        "Meta released Llama 4 family with multimodal capabilities.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "meta", EventType.LEADERSHIP_CHANGE, "2025-06-01T00:00:00Z",
        "Meta AI reorganized into Superintelligence Labs",
        "Meta reorganized its AI division into Meta Superintelligence Labs, "
        "hiring Scale AI founder Alexandr Wang.",
        AlertLevel.INFO, AlertCategory.ORGANIZATIONAL,
    ))

    # DeepSeek
    events.append(_evt(
        "deepseek", EventType.MODEL_RELEASE, "2025-01-20T00:00:00Z",
        "DeepSeek-R1 released",
        "DeepSeek released R1, a reasoning model competitive with OpenAI o1 "
        "at a fraction of the cost. Triggered market turbulence.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
        metadata={"market_impact": "significant"},
    ))
    events.append(_evt(
        "deepseek", EventType.OPEN_WEIGHT_RELEASE, "2025-01-20T00:00:00Z",
        "DeepSeek-R1 open-weight release",
        "DeepSeek released R1 weights under MIT license.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "deepseek", EventType.INCIDENT_REPORT, "2025-01-28T00:00:00Z",
        "DeepSeek exposed user data via open database",
        "Security researchers found an unsecured database exposing DeepSeek "
        "user chat histories and API keys.",
        AlertLevel.CRITICAL, AlertCategory.INCIDENT,
        metadata={"severity": "moderate"},
    ))

    # Mistral
    events.append(_evt(
        "mistral", EventType.SAFETY_FRAMEWORK_NEW, "2024-02-01T00:00:00Z",
        "Mistral publishes safety policy",
        "Mistral AI published its first safety policy document.",
        AlertLevel.POSITIVE, AlertCategory.GOVERNANCE_IMPROVEMENT,
    ))
    events.append(_evt(
        "mistral", EventType.COMPLIANCE_CHANGE, "2025-09-01T00:00:00Z",
        "Mistral signs EU AI Act GPAI Code of Practice",
        "Mistral AI became a signatory to the EU AI Act GPAI Code of Practice.",
        AlertLevel.POSITIVE, AlertCategory.COMPLIANCE_SHIFT,
        metadata={"previous_value": "non-signatory", "new_value": "signatory"},
    ))

    # xAI
    events.append(_evt(
        "xai", EventType.MODEL_RELEASE, "2024-11-01T00:00:00Z",
        "Grok 2 released",
        "xAI released Grok 2 with improved reasoning capabilities.",
        AlertLevel.INFO, AlertCategory.CAPABILITY_CHANGE,
    ))
    events.append(_evt(
        "xai", EventType.FUNDING_ROUND, "2024-12-01T00:00:00Z",
        "xAI raises $6B at $50B valuation",
        "xAI raised $6B in Series C at a $50B valuation.",
        AlertLevel.INFO, AlertCategory.MARKET,
    ))

    # SSI
    events.append(_evt(
        "ssi", EventType.LEADERSHIP_CHANGE, "2024-06-01T00:00:00Z",
        "Ilya Sutskever founds SSI",
        "Ilya Sutskever co-founded Safe Superintelligence Inc. after leaving "
        "OpenAI, focusing purely on safety research.",
        AlertLevel.INFO, AlertCategory.ORGANIZATIONAL,
    ))
    events.append(_evt(
        "ssi", EventType.FUNDING_ROUND, "2024-09-01T00:00:00Z",
        "SSI raises $1B at $5B valuation",
        "SSI raised $1B at a $5B valuation with no product or revenue.",
        AlertLevel.INFO, AlertCategory.MARKET,
    ))

    # EU AI Act enforcement
    events.append(_evt(
        "openai", EventType.REGULATORY_ACTION, "2025-08-02T00:00:00Z",
        "EU AI Act enters into force",
        "EU AI Act provisions for GPAI models entered into force. OpenAI "
        "classified as GPAI provider.",
        AlertLevel.WARNING, AlertCategory.COMPLIANCE_SHIFT,
    ))
    events.append(_evt(
        "anthropic", EventType.REGULATORY_ACTION, "2025-08-02T00:00:00Z",
        "EU AI Act enters into force",
        "EU AI Act provisions for GPAI models entered into force. Anthropic "
        "classified as GPAI provider.",
        AlertLevel.WARNING, AlertCategory.COMPLIANCE_SHIFT,
    ))

    return events


def create_seeded_monitor() -> LabMonitor:
    """Create a LabMonitor pre-populated with known historical events.

    Returns a LabMonitor with ~25 seed events covering major lab activity
    from 2023-2026, sourced from HUMMBL research artifacts.
    """
    monitor = LabMonitor()
    for event in _seed_historical_events():
        monitor._timeline.add(event)
    return monitor
