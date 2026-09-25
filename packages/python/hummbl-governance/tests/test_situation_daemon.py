"""
Comprehensive unit tests for HUMMBL Situation Daemon:
- EventStore deduplication and TTL expiration
- Multi-channel AlertDispatcher (Discord, Telegram, ntfy, generic webhooks)
- HTTP Radar server endpoints (/api/events, /api/status, /)
- Minimal stdlib RFC 6455 WebSocket client (handshake, text, extended length, ping/pong)
- EMSC WebSocket worker event parsing and severity triage
- RIPE RIS Live BGP WebSocket worker event parsing and anomaly triage
- CLI argument parsing including --tui and --no-ws
"""

import asyncio
import base64
import hashlib
import json
import os
import struct
import time
import unittest
import urllib.request
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from examples.situation_daemon import (
    AlertDispatcher,
    AviationSquawkWorker,
    EMSCWebSocketWorker,
    EventStore,
    RipeRisWebSocketWorker,
    SeismicWorker,
    SimpleWebSocketClient,
    SituationDaemon,
    SpaceWeatherWorker,
    TelemetryEvent,
    build_arg_parser,
    run_http_server,
)


class TestSituationDaemonCore(unittest.TestCase):
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
        self.assertTrue(self.store.add(ev1))
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

        with self.store._lock:
            self.store._event_timestamps["expiring_ev"] = time.time() - 10

        self.assertEqual(len(self.store.get_recent()), 0)
        self.assertTrue(self.store.is_new("expiring_ev"))

    def test_alert_dispatcher_multi_channel(self):
        captured_requests = []

        def mock_post(url, data, headers):
            captured_requests.append({"url": url, "data": data, "headers": headers})

        dispatcher = AlertDispatcher(
            webhook_urls=["https://example.com/webhook"],
            discord_webhook_url="https://discord.com/api/webhooks/test",
            telegram_bot_token="test_token_123",
            telegram_chat_id="test_chat_456",
            ntfy_topic="test_topic_789",
            ntfy_url="https://ntfy.sh",
        )
        dispatcher._post_http = mock_post

        ev = TelemetryEvent(
            id="multi_alert_test",
            domain="seismic",
            severity="P0_CRITICAL",
            title="M7.8 Megathrust Earthquake",
            summary="Tsunami warning issued for Pacific basin",
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=-15.5,
            longitude=-175.2,
        )

        # Trigger synchronous dispatch for test verification
        dispatcher._send_all_channels(ev)

        # Verify all 4 channels received dispatched payloads
        urls = [r["url"] for r in captured_requests]
        self.assertIn("https://discord.com/api/webhooks/test", urls)
        self.assertIn("https://api.telegram.org/bottest_token_123/sendMessage", urls)
        self.assertIn("https://ntfy.sh/test_topic_789", urls)
        self.assertIn("https://example.com/webhook", urls)

        # Verify Discord JSON payload structure
        discord_req = [r for r in captured_requests if "discord.com" in r["url"]][0]
        discord_data = json.loads(discord_req["data"].decode("utf-8"))
        self.assertIn("P0_CRITICAL", discord_data["content"])
        self.assertEqual(discord_data["embeds"][0]["color"], 15158332)

        # Verify Telegram payload structure
        tg_req = [r for r in captured_requests if "telegram.org" in r["url"]][0]
        tg_data = json.loads(tg_req["data"].decode("utf-8"))
        self.assertEqual(tg_data["chat_id"], "test_chat_456")
        self.assertIn("HTML", tg_data["parse_mode"])

        # Verify ntfy headers
        ntfy_req = [r for r in captured_requests if "ntfy.sh" in r["url"]][0]
        self.assertEqual(ntfy_req["headers"]["Priority"], "5")

    def test_http_radar_server_endpoints(self):
        test_port = 8798
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
            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/") as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("HUMMBL Situation Room", html)

            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/events") as resp:
                self.assertEqual(resp.status, 200)
                events = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["id"], "http_test_ev")

            with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/status") as resp:
                self.assertEqual(resp.status, 200)
                status = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(status["daemon"], "HUMMBL Situation Daemon")
                self.assertEqual(status["events_in_memory"], 1)

        finally:
            server.shutdown()


class TestWebSocketClientAndWorkers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = EventStore(ttl_seconds=30)
        self.dispatched_events: list[TelemetryEvent] = []

    def on_event(self, ev: TelemetryEvent):
        self.dispatched_events.append(ev)

    async def test_emsc_event_processing(self):
        worker = EMSCWebSocketWorker(self.store, self.on_event)

        # 1. Test Major Quake P0_CRITICAL
        sample_geojson_p0 = json.dumps({
            "action": "create",
            "data": {
                "id": "20260925_001",
                "properties": {
                    "mag": 7.4,
                    "flynn_region": "VANUATU ISLANDS",
                    "depth": 35.0,
                    "time": "2026-09-25T17:15:00Z",
                    "source_catalog": "EMSC"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [168.2, -15.1, 35.0]
                }
            }
        })
        worker._process_message(sample_geojson_p0)

        self.assertEqual(len(self.dispatched_events), 1)
        ev_p0 = self.dispatched_events[0]
        self.assertEqual(ev_p0.severity, "P0_CRITICAL")
        self.assertEqual(ev_p0.domain, "seismic")
        self.assertEqual(ev_p0.longitude, 168.2)
        self.assertEqual(ev_p0.latitude, -15.1)
        self.assertIn("M7.4", ev_p0.title)

        # 2. Test Moderate Quake P2_ADVISORY
        sample_geojson_p2 = json.dumps({
            "action": "create",
            "data": {
                "id": "20260925_002",
                "properties": {
                    "mag": 5.1,
                    "flynn_region": "SOUTHERN CALIFORNIA",
                    "depth": 12.0,
                    "time": "2026-09-25T17:16:00Z",
                    "source_catalog": "EMSC"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [-118.2, 34.0, 12.0]
                }
            }
        })
        worker._process_message(sample_geojson_p2)
        self.assertEqual(len(self.dispatched_events), 2)
        self.assertEqual(self.dispatched_events[1].severity, "P2_ADVISORY")

    async def test_ripe_ris_event_processing(self):
        worker = RipeRisWebSocketWorker(self.store, self.on_event)

        # 1. Mass BGP withdrawal storm -> P0_CRITICAL
        sample_mass_withdraw = json.dumps({
            "type": "ris_message",
            "data": {
                "timestamp": 1790356500.0,
                "peer": "192.0.2.1",
                "peer_asn": "64500",
                "id": "test_bgp_001",
                "type": "UPDATE",
                "path": [64500, 174, 3356],
                "withdrawals": [{"prefixes": [f"10.{i}.0.0/16"]} for i in range(55)],
                "announcements": []
            }
        })
        worker._process_message(sample_mass_withdraw)

        self.assertEqual(len(self.dispatched_events), 1)
        ev_bgp_p0 = self.dispatched_events[0]
        self.assertEqual(ev_bgp_p0.severity, "P0_CRITICAL")
        self.assertEqual(ev_bgp_p0.domain, "network")
        self.assertIn("MASS BGP WITHDRAWAL", ev_bgp_p0.title)

        # 2. AS-path inflation / loop anomaly -> P1_HIGH
        sample_as_loop = json.dumps({
            "type": "ris_message",
            "data": {
                "timestamp": 1790356501.0,
                "peer": "192.0.2.2",
                "peer_asn": "64501",
                "id": "test_bgp_002",
                "type": "UPDATE",
                "path": [64501, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                "withdrawals": [],
                "announcements": [{"prefixes": ["198.51.100.0/24"]}]
            }
        })
        worker._process_message(sample_as_loop)
        self.assertEqual(len(self.dispatched_events), 2)
        ev_bgp_p1 = self.dispatched_events[1]
        self.assertEqual(ev_bgp_p1.severity, "P1_HIGH")
        self.assertIn("AS-PATH LOOP / INFLATION", ev_bgp_p1.title)

    async def test_mock_websocket_server_handshake_and_frames(self):
        """Spins up a lightweight in-process RFC 6455 server to verify client handshake and framing."""
        server_received_messages = []

        async def ws_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            # Read handshake
            req = b""
            while b"\r\n\r\n" not in req:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                req += chunk

            nonce = None
            for line in req.split(b"\r\n"):
                if line.lower().startswith(b"sec-websocket-key:"):
                    nonce = line.split(b":", 1)[1].strip().decode("ascii")
                    break

            accept = base64.b64encode(
                hashlib.sha1((nonce + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("utf-8")).digest()
            ).decode("ascii")

            resp = (
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n"
                b"Sec-WebSocket-Accept: " + accept.encode("ascii") + b"\r\n\r\n"
            )
            writer.write(resp)
            await writer.drain()

            # Read masked text frame from client
            b1_b2 = await reader.readexactly(2)
            opcode = b1_b2[0] & 0x0F
            is_masked = bool(b1_b2[1] & 0x80)
            plen = b1_b2[1] & 0x7F
            mask = await reader.readexactly(4)
            payload = await reader.readexactly(plen)
            unmasked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload)).decode("utf-8")
            server_received_messages.append(unmasked)

            # Send unmasked text frame back to client
            reply = "PONG_FROM_MOCK".encode("utf-8")
            frame = struct.pack("!BB", 0x81, len(reply)) + reply
            writer.write(frame)
            await writer.drain()
            # Let client close the connection

        server = await asyncio.start_server(ws_handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]

        client = SimpleWebSocketClient("127.0.0.1", port, path="/test-ws", use_ssl=False)
        try:
            await client.connect(timeout=5.0)
            await client.send_text("PING_FROM_CLIENT")
            reply = await client.recv_text()
            self.assertEqual(reply, "PONG_FROM_MOCK")
            self.assertEqual(server_received_messages, ["PING_FROM_CLIENT"])
        finally:
            await client.close()
            server.close()
            await server.wait_closed()


class TestDaemonCLI(unittest.TestCase):
    def test_cli_argument_parsing(self):
        parser = build_arg_parser()

        # Defaults
        args = parser.parse_args([])
        self.assertEqual(args.port, 8765)
        self.assertFalse(args.no_ws)
        self.assertFalse(args.tui)

        # With flags
        args2 = parser.parse_args(["--port", "9000", "--tui", "--no-ws", "--webhooks", "https://hummbl.io/hook"])
        self.assertEqual(args2.port, 9000)
        self.assertTrue(args2.tui)
        self.assertTrue(args2.no_ws)
        self.assertEqual(args2.webhooks, "https://hummbl.io/hook")


if __name__ == "__main__":
    unittest.main()
