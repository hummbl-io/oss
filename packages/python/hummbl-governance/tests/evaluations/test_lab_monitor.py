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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_governance.evaluations.lab_monitor."""

from __future__ import annotations

import json
import pytest

from hummbl_governance.evaluations.lab_monitor import (
    LabMonitor,
    LabEvent,
    LabSnapshot,
    EventTimeline,
    EventType,
    AlertLevel,
    create_seeded_monitor,
)


class TestEventType:
    """Tests for the EventType enum."""

    def test_event_type_values(self):
        assert EventType.MODEL_RELEASE.value == "model_release"
        assert EventType.SAFETY_FRAMEWORK_RESCINDED.value == "safety_framework_rescinded"
        assert EventType.INCIDENT_REPORT.value == "incident_report"
        assert EventType.REGULATORY_ACTION.value == "regulatory_action"

    def test_event_type_count(self):
        """Should have at least 19 event types."""
        assert len(list(EventType)) >= 19


class TestAlertLevel:
    """Tests for the AlertLevel enum."""

    def test_alert_level_values(self):
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.POSITIVE.value == "positive"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"
        assert AlertLevel.EMERGENCY.value == "emergency"

    def test_alert_level_ordering(self):
        """Alert levels should be ordered by severity."""
        assert AlertLevel.INFO.value != AlertLevel.CRITICAL.value


class TestLabEvent:
    """Tests for the LabEvent dataclass."""

    def test_create_event(self):
        event = LabEvent(
            event_id="evt-001",
            lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z",
            title="Test event",
            description="Test description",
        )
        assert event.event_id == "evt-001"
        assert event.lab_slug == "anthropic"
        assert event.event_type == EventType.MODEL_RELEASE
        assert event.alert_level == AlertLevel.INFO

    def test_to_dict(self):
        event = LabEvent(
            event_id="evt-001",
            lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z",
            title="Test",
            description="Test desc",
        )
        d = event.to_dict()
        assert d["event_id"] == "evt-001"
        assert d["event_type"] == "model_release"
        assert d["alert_level"] == "info"

    def test_frozen(self):
        """LabEvent should be frozen (immutable)."""
        event = LabEvent(
            event_id="evt-001", lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z",
            title="Test", description="Test",
        )
        with pytest.raises(AttributeError):
            event.title = "Changed"


class TestEventTimeline:
    """Tests for the EventTimeline class."""

    def test_add_and_get_all(self):
        timeline = EventTimeline()
        event = LabEvent(
            event_id="evt-001", lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z",
            title="Test", description="Test",
        )
        timeline.add(event)
        assert timeline.count == 1
        assert timeline.get_all() == [event]

    def test_sorted_by_timestamp(self):
        timeline = EventTimeline()
        e1 = LabEvent(
            event_id="evt-1", lab_slug="lab", event_type=EventType.MODEL_RELEASE,
            timestamp="2026-03-01T00:00:00Z", title="T1", description="D1",
        )
        e2 = LabEvent(
            event_id="evt-2", lab_slug="lab", event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="T2", description="D2",
        )
        timeline.add(e1)
        timeline.add(e2)
        events = timeline.get_all()
        assert events[0].timestamp < events[1].timestamp

    def test_get_for_lab(self):
        timeline = EventTimeline()
        for slug in ["anthropic", "openai", "anthropic"]:
            timeline.add(LabEvent(
                event_id=f"evt-{slug}", lab_slug=slug,
                event_type=EventType.MODEL_RELEASE,
                timestamp="2026-01-01T00:00:00Z",
                title="T", description="D",
            ))
        assert len(timeline.get_for_lab("anthropic")) == 2
        assert len(timeline.get_for_lab("openai")) == 1

    def test_get_by_type(self):
        timeline = EventTimeline()
        timeline.add(LabEvent(
            event_id="e1", lab_slug="lab",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="T", description="D",
        ))
        timeline.add(LabEvent(
            event_id="e2", lab_slug="lab",
            event_type=EventType.INCIDENT_REPORT,
            timestamp="2026-01-02T00:00:00Z", title="T", description="D",
        ))
        assert len(timeline.get_by_type(EventType.MODEL_RELEASE)) == 1
        assert len(timeline.get_by_type(EventType.INCIDENT_REPORT)) == 1

    def test_get_since(self):
        timeline = EventTimeline()
        timeline.add(LabEvent(
            event_id="e1", lab_slug="lab", event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="T", description="D",
        ))
        timeline.add(LabEvent(
            event_id="e2", lab_slug="lab", event_type=EventType.MODEL_RELEASE,
            timestamp="2026-06-01T00:00:00Z", title="T", description="D",
        ))
        assert len(timeline.get_since("2026-03-01T00:00:00Z")) == 1

    def test_filter_multiple_criteria(self):
        timeline = EventTimeline()
        timeline.add(LabEvent(
            event_id="e1", lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="T", description="D",
            alert_level=AlertLevel.INFO,
        ))
        timeline.add(LabEvent(
            event_id="e2", lab_slug="openai",
            event_type=EventType.INCIDENT_REPORT,
            timestamp="2026-06-01T00:00:00Z", title="T", description="D",
            alert_level=AlertLevel.CRITICAL,
        ))
        results = timeline.filter(
            lab_slug="openai",
            alert_level=AlertLevel.CRITICAL,
        )
        assert len(results) == 1
        assert results[0].lab_slug == "openai"

    def test_to_json(self):
        timeline = EventTimeline()
        timeline.add(LabEvent(
            event_id="e1", lab_slug="lab", event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="T", description="D",
        ))
        parsed = json.loads(timeline.to_json())
        assert parsed["count"] == 1

    def test_to_markdown(self):
        timeline = EventTimeline()
        timeline.add(LabEvent(
            event_id="e1", lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z", title="Test Event", description="D",
        ))
        md = timeline.to_markdown()
        assert "anthropic" in md
        assert "Test Event" in md
        assert "|" in md


class TestLabMonitor:
    """Tests for the LabMonitor class."""

    def test_record_event(self):
        monitor = LabMonitor()
        event = monitor.record_event(
            lab_slug="anthropic",
            event_type=EventType.MODEL_RELEASE,
            timestamp="2026-01-01T00:00:00Z",
            title="Test",
            description="Test desc",
        )
        assert event.event_id.startswith("evt-")
        assert event.lab_slug == "anthropic"
        assert monitor.event_count == 1

    def test_record_event_auto_increment_ids(self):
        monitor = LabMonitor()
        e1 = monitor.record_event(
            "lab", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "T", "D",
        )
        e2 = monitor.record_event(
            "lab", EventType.MODEL_RELEASE, "2026-01-02T00:00:00Z", "T", "D",
        )
        assert e1.event_id != e2.event_id

    def test_get_timeline_for_lab(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "T", "D",
        )
        monitor.record_event(
            "openai", EventType.MODEL_RELEASE, "2026-01-02T00:00:00Z", "T", "D",
        )
        timeline = monitor.get_timeline("anthropic")
        assert timeline.count == 1

    def test_get_events_filtered(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "T", "D",
            alert_level=AlertLevel.INFO,
        )
        monitor.record_event(
            "anthropic", EventType.INCIDENT_REPORT, "2026-06-01T00:00:00Z", "T", "D",
            alert_level=AlertLevel.CRITICAL,
        )
        results = monitor.get_events(
            lab_slug="anthropic",
            alert_level=AlertLevel.CRITICAL,
        )
        assert len(results) == 1
        assert results[0].event_type == EventType.INCIDENT_REPORT

    def test_record_and_get_snapshot(self):
        monitor = LabMonitor()
        snap = LabSnapshot(
            lab_slug="anthropic",
            timestamp="2026-01-01T00:00:00Z",
            safety_framework="RSP v3",
            governance_score=3.1,
        )
        monitor.record_snapshot(snap)
        snaps = monitor.get_snapshots("anthropic")
        assert len(snaps) == 1
        assert snaps[0].safety_framework == "RSP v3"

    def test_get_latest_snapshot(self):
        monitor = LabMonitor()
        for ts in ["2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z"]:
            monitor.record_snapshot(LabSnapshot(
                lab_slug="lab", timestamp=ts,
            ))
        latest = monitor.get_latest_snapshot("lab")
        assert latest is not None
        assert latest.timestamp == "2026-06-01T00:00:00Z"

    def test_get_latest_snapshot_none(self):
        monitor = LabMonitor()
        assert monitor.get_latest_snapshot("nonexistent") is None

    def test_diff_snapshots(self):
        monitor = LabMonitor()
        monitor.record_snapshot(LabSnapshot(
            lab_slug="lab", timestamp="2026-01-01T00:00:00Z",
            safety_framework="None published",
            governance_score=0.0,
        ))
        monitor.record_snapshot(LabSnapshot(
            lab_slug="lab", timestamp="2026-06-01T00:00:00Z",
            safety_framework="RSP v1",
            governance_score=2.5,
        ))
        diff = monitor.diff_snapshots("lab", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")
        assert "safety_framework" in diff
        assert diff["safety_framework"]["previous"] == "None published"
        assert diff["safety_framework"]["new"] == "RSP v1"
        assert "governance_score" in diff

    def test_diff_snapshots_no_change(self):
        monitor = LabMonitor()
        monitor.record_snapshot(LabSnapshot(
            lab_slug="lab", timestamp="2026-01-01T00:00:00Z",
        ))
        monitor.record_snapshot(LabSnapshot(
            lab_slug="lab", timestamp="2026-06-01T00:00:00Z",
        ))
        diff = monitor.diff_snapshots("lab", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")
        assert diff == {}

    def test_check_for_alerts_safety_rescinded(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.SAFETY_FRAMEWORK_RESCINDED,
            "2026-01-01T00:00:00Z", "RSP rescinded", "Description",
        )
        alerts = monitor.check_for_alerts("anthropic")
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL

    def test_check_for_alerts_safety_new(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.SAFETY_FRAMEWORK_NEW,
            "2026-01-01T00:00:00Z", "New framework", "Description",
        )
        alerts = monitor.check_for_alerts("anthropic")
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.POSITIVE

    def test_check_for_alerts_incident(self):
        monitor = LabMonitor()
        monitor.record_event(
            "openai", EventType.INCIDENT_REPORT,
            "2026-01-01T00:00:00Z", "Data leak", "Description",
            metadata={"severity": "moderate"},
        )
        alerts = monitor.check_for_alerts("openai")
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL

    def test_check_for_alerts_severe_incident(self):
        monitor = LabMonitor()
        monitor.record_event(
            "openai", EventType.INCIDENT_REPORT,
            "2026-01-01T00:00:00Z", "Severe incident", "Description",
            metadata={"severity": "severe"},
        )
        alerts = monitor.check_for_alerts("openai")
        assert alerts[0].level == AlertLevel.EMERGENCY

    def test_check_for_alerts_regulatory_action(self):
        monitor = LabMonitor()
        monitor.record_event(
            "openai", EventType.REGULATORY_ACTION,
            "2026-01-01T00:00:00Z", "EU AI Act enforcement", "Description",
        )
        alerts = monitor.check_for_alerts("openai")
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL

    def test_check_for_alerts_leadership_departure(self):
        monitor = LabMonitor()
        monitor.record_event(
            "openai", EventType.LEADERSHIP_CHANGE,
            "2026-01-01T00:00:00Z", "CEO departed", "Description",
            metadata={"departure": True},
        )
        alerts = monitor.check_for_alerts("openai")
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING

    def test_check_all_alerts(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.SAFETY_FRAMEWORK_NEW,
            "2026-01-01T00:00:00Z", "New", "D",
        )
        monitor.record_event(
            "openai", EventType.INCIDENT_REPORT,
            "2026-01-02T00:00:00Z", "Incident", "D",
        )
        all_alerts = monitor.check_all_alerts()
        assert len(all_alerts) >= 2

    def test_activity_summary(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.MODEL_RELEASE,
            "2026-01-01T00:00:00Z", "T", "D",
        )
        monitor.record_event(
            "anthropic", EventType.INCIDENT_REPORT,
            "2026-06-01T00:00:00Z", "T", "D",
        )
        monitor.record_event(
            "openai", EventType.MODEL_RELEASE,
            "2026-03-01T00:00:00Z", "T", "D",
        )
        summary = monitor.get_activity_summary()
        assert "anthropic" in summary
        assert summary["anthropic"]["event_count"] == 2
        assert "openai" in summary
        assert summary["openai"]["event_count"] == 1

    def test_most_active_labs(self):
        monitor = LabMonitor()
        for i in range(5):
            monitor.record_event(
                "anthropic", EventType.MODEL_RELEASE,
                f"2026-01-0{i+1}T00:00:00Z", "T", "D",
            )
        for i in range(2):
            monitor.record_event(
                "openai", EventType.MODEL_RELEASE,
                f"2026-01-0{i+1}T00:00:00Z", "T", "D",
            )
        ranked = monitor.get_most_active_labs(n=10)
        assert ranked[0][0] == "anthropic"
        assert ranked[0][1] == 5
        assert ranked[1][0] == "openai"
        assert ranked[1][1] == 2

    def test_export_timeline_json(self):
        monitor = LabMonitor()
        monitor.record_event(
            "lab", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "T", "D",
        )
        result = json.loads(monitor.export_timeline_json())
        assert result["count"] == 1

    def test_export_timeline_markdown(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "Test", "D",
        )
        md = monitor.export_timeline_markdown()
        assert "anthropic" in md

    def test_export_alerts_json(self):
        monitor = LabMonitor()
        monitor.record_event(
            "anthropic", EventType.SAFETY_FRAMEWORK_RESCINDED,
            "2026-01-01T00:00:00Z", "T", "D",
        )
        result = json.loads(monitor.export_alerts_json())
        assert result["count"] >= 1

    def test_lab_count(self):
        monitor = LabMonitor()
        monitor.record_event("anthropic", EventType.MODEL_RELEASE, "2026-01-01T00:00:00Z", "T", "D")
        monitor.record_event("openai", EventType.MODEL_RELEASE, "2026-01-02T00:00:00Z", "T", "D")
        assert monitor.lab_count == 2


class TestSeededMonitor:
    """Tests for the create_seeded_monitor function."""

    def test_seeded_monitor_has_events(self):
        monitor = create_seeded_monitor()
        assert monitor.event_count > 0

    def test_seeded_monitor_has_multiple_labs(self):
        monitor = create_seeded_monitor()
        assert monitor.lab_count >= 5

    def test_seeded_anthropic_has_events(self):
        monitor = create_seeded_monitor()
        timeline = monitor.get_timeline("anthropic")
        assert timeline.count >= 3

    def test_seeded_anthropic_has_alerts(self):
        monitor = create_seeded_monitor()
        alerts = monitor.check_for_alerts("anthropic")
        # Anthropic has RSP rescinded event -> CRITICAL alert
        critical = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        assert len(critical) >= 1

    def test_seeded_openai_has_alerts(self):
        monitor = create_seeded_monitor()
        alerts = monitor.check_for_alerts("openai")
        # OpenAI has incident + regulatory action
        assert len(alerts) >= 2

    def test_seeded_activity_summary(self):
        monitor = create_seeded_monitor()
        summary = monitor.get_activity_summary()
        assert len(summary) >= 5

    def test_seeded_most_active(self):
        monitor = create_seeded_monitor()
        ranked = monitor.get_most_active_labs(n=5)
        assert len(ranked) <= 5
        assert all(count > 0 for _, count in ranked)
