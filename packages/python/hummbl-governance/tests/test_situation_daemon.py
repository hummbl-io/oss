"""
Tests for HUMMBL Situation Daemon (EventStore, Deduplication, Workers, and HTTP Radar endpoints).
"""

import json
import threading
import time
import unittest
import urllib.request
from datetime import datetime, timezone

from examples.situation_daemon import (
    AlertDispatcher,
    EventStore,
    SituationDaemon,
    SituationHTTPHandler,
    TelemetryEvent,
    run_http_server,
)


class TestSituationDaemon(unittest.TestCase):
    def setUp(self):
        self.store = EventStore(ttl_seconds=5)

    def test_event_store_deduplication(self):
        ev1 = TelemetryEvent(
            id="test_ev_1",
            domain="seismic",
            severity="P1_HIGH",
            title="M6.2 Earthquake - Japan",
            summary="Depth: 10km",
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=35.6762,
            longitude=139.6503,
        )
        # First insertion succeeds
        self.assertTrue(self.store.add(ev1))
        # Second insertion with same ID is rejected (deduplicated)
        self.assertFalse(self.store.add(ev1))
        
        recent = self.store.get_recent()
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].id, "test_ev_1")

    def test_event_store_ttl_expiration(self):
        ev = TelemetryEvent(
            id="expiring_ev",
            domain="aviation",
            severity="P2_ADVISORY",
            title="Squawk 7600",
            summary="Lost comms",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.store.add(ev)
        self.assertEqual(len(self.store.get_recent()), 1)
        
        # Artificially age the event timestamp
        with self.store._lock:
            self.store._event_timestamps["expiring_ev"] = time.time() - 10
            
        # Purge triggers on next query
        self.assertEqual(len(self.store.get_recent()), 0)
        self.assertTrue(self.store.is_new("expiring_ev"))

    def test_alert_dispatcher_formatting(self):
        dispatched_events = []
        dispatcher = AlertDispatcher(webhook_urls=[])
        
        ev = TelemetryEvent(
            id="alert_test",
            domain="space_weather",
            severity="P0_CRITICAL",
            title="G5 Solar Storm Warning",
            summary="Severe geomagnetic storm in progress",
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=0.0,
            longitude=0.0,
        )
        # Should not raise
        dispatcher.dispatch(ev)

    def test_http_radar_server_endpoints(self):
        test_port = 8799
        ev = TelemetryEvent(
            id="http_test_ev",
            domain="aviation",
            severity="P1_HIGH",
            title="Squawk 7700: Flight TEST123",
            summary="Emergency transponder active",
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=51.5074,
            longitude=-0.1278,
        )
        self.store.add(ev)
        
        server = run_http_server(self.store, port=test_port)
        time.sleep(0.1)

        try:
            # 1. Test HTML dashboard GET /
            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/") as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("HUMMBL Situation Room", html)

            # 2. Test JSON API GET /api/events
            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/events") as resp:
                self.assertEqual(resp.status, 200)
                events = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["id"], "http_test_ev")
                self.assertEqual(events[0]["domain"], "aviation")

            # 3. Test Status API GET /api/status
            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/status") as resp:
                self.assertEqual(resp.status, 200)
                status = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(status["daemon"], "HUMMBL Situation Daemon")
                self.assertEqual(status["events_in_memory"], 1)

        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
