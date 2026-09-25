"""
HUMMBL Global Situation Daemon — Lightweight Multi-Domain Telemetry Aggregator

A zero-third-party-dependency, asyncio-powered background daemon for real-time global
situational monitoring. Ingests live telemetry streams:
  1. Aviation Emergency Squawks (ADSB.lol: 7700 emergency, 7600 lost comms, 7500 hijack)
  2. USGS Seismic Activity (M4.5+ and significant earthquakes)
  3. NOAA SWPC Space Weather Alerts (Geomagnetic storms, solar radiation)
  4. EMSC Real-Time Seismic Stream (Sub-second native WebSocket stream)
  5. RIPE RIS Live Global BGP Stream (Sub-second native WebSocket stream)

Features:
- Native stdlib RFC 6455 WebSocket client (zero third-party packages)
- Multi-channel alert dispatching (Console SITREP, Discord, Telegram, ntfy, Webhooks)
- In-memory EventStore with time-to-live deduplication
- Embedded HTTP Tactical Radar map & REST API (/api/events, /api/status)
- Headless Terminal TUI mode (--tui) via standard ANSI escapes

Standard library only: Python 3.11+ (asyncio, ssl, struct, base64, hashlib, urllib, http.server).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import http.server
import json
import logging
import os
import socket
import socketserver
import ssl
import struct
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("situation_daemon")

# ---------------------------------------------------------------------------
# Data Models & Triage Schema
# ---------------------------------------------------------------------------


@dataclass
class TelemetryEvent:
    id: str
    domain: str  # "aviation", "seismic", "space_weather", "tsunami", "network"
    severity: str  # "P0_CRITICAL", "P1_HIGH", "P2_ADVISORY"
    title: str
    summary: str
    timestamp: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Deduplication & State Store (Memory + Lock)
# ---------------------------------------------------------------------------


class EventStore:
    def __init__(self, db_path: str = ":memory:", ttl_seconds: int = 7200):
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._events: Dict[str, TelemetryEvent] = {}
        self._event_timestamps: Dict[str, float] = {}

    def is_new(self, event_id: str) -> bool:
        with self._lock:
            self._purge_expired()
            return event_id not in self._events

    def add(self, event: TelemetryEvent) -> bool:
        with self._lock:
            self._purge_expired()
            if event.id in self._events:
                return False
            self._events[event.id] = event
            self._event_timestamps[event.id] = time.time()
            return True

    def get_recent(self, limit: int = 50) -> List[TelemetryEvent]:
        with self._lock:
            self._purge_expired()
            sorted_events = sorted(
                self._events.values(),
                key=lambda e: e.timestamp,
                reverse=True,
            )
            return sorted_events[:limit]

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [eid for eid, t in self._event_timestamps.items() if (now - t) > self.ttl_seconds]
        for eid in expired:
            self._events.pop(eid, None)
            self._event_timestamps.pop(eid, None)


# ---------------------------------------------------------------------------
# HTTP Helpers (Zero Third-Party Dependencies)
# ---------------------------------------------------------------------------


def fetch_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 8.0) -> Optional[Any]:
    req_headers = {
        "User-Agent": "HUMMBL-SituationDaemon/1.0 (Governance; Open-Telemetry-Monitor)",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
    except Exception as exc:
        logger.debug("Fetch error for %s: %s", url, exc)
    return None


# ---------------------------------------------------------------------------
# Minimal Native RFC 6455 Asyncio WebSocket Client (Stdlib Only)
# ---------------------------------------------------------------------------

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class SimpleWebSocketClient:
    """Zero-dependency RFC 6455 WebSocket client using asyncio and ssl."""

    def __init__(
        self,
        host: str,
        port: int = 443,
        path: str = "/",
        use_ssl: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        self.host = host
        self.port = port
        self.path = path
        self.use_ssl = use_ssl
        self.extra_headers = extra_headers or {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.closed: bool = True

    async def connect(self, timeout: float = 10.0) -> None:
        ssl_ctx = ssl.create_default_context() if self.use_ssl else None
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port, ssl=ssl_ctx),
            timeout=timeout,
        )

        nonce = base64.b64encode(os.urandom(16)).decode("ascii")
        expected_accept = base64.b64encode(
            hashlib.sha1((nonce + WS_GUID).encode("utf-8")).digest()
        ).decode("ascii")

        req_lines = [
            f"GET {self.path} HTTP/1.1",
            f"Host: {self.host}:{self.port}" if self.port not in (80, 443) else f"Host: {self.host}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {nonce}",
            "Sec-WebSocket-Version: 13",
            "User-Agent: HUMMBL-SituationDaemon/1.0",
        ]
        for k, v in self.extra_headers.items():
            req_lines.append(f"{k}: {v}")
        req_lines.extend(["", ""])
        req_data = "\r\n".join(req_lines).encode("ascii")

        self.writer.write(req_data)
        await self.writer.drain()

        # Read HTTP handshake response headers
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = await asyncio.wait_for(self.reader.read(1024), timeout=timeout)
            if not chunk:
                raise ConnectionError("Connection closed during WebSocket handshake")
            header_data += chunk

        lines = header_data.split(b"\r\n")
        status_line = lines[0].decode("latin-1", errors="replace")
        if "101" not in status_line:
            raise ConnectionError(f"WebSocket upgrade rejected: {status_line}")

        accept_header = None
        for line in lines[1:]:
            if line.lower().startswith(b"sec-websocket-accept:"):
                accept_header = line.split(b":", 1)[1].strip().decode("ascii")
                break

        if accept_header != expected_accept:
            raise ConnectionError("Sec-WebSocket-Accept handshake validation mismatch")

        self.closed = False

    async def send_text(self, text: str) -> None:
        if self.closed or not self.writer:
            raise ConnectionError("WebSocket is not connected")
        data = text.encode("utf-8")
        mask_key = os.urandom(4)
        masked_data = bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))

        length = len(data)
        if length <= 125:
            header = struct.pack("!BB", 0x81, 0x80 | length)
        elif length <= 65535:
            header = struct.pack("!BBH", 0x81, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", 0x81, 0x80 | 127, length)

        self.writer.write(header + mask_key + masked_data)
        await self.writer.drain()

    async def recv_frame(self) -> Tuple[int, bytes]:
        if self.closed or not self.reader:
            raise ConnectionError("WebSocket is not connected")

        b1_b2 = await self.reader.readexactly(2)
        b1, b2 = b1_b2[0], b1_b2[1]
        opcode = b1 & 0x0F
        is_masked = bool(b2 & 0x80)
        payload_len = b2 & 0x7F

        if payload_len == 126:
            ext_len = await self.reader.readexactly(2)
            payload_len = struct.unpack("!H", ext_len)[0]
        elif payload_len == 127:
            ext_len = await self.reader.readexactly(8)
            payload_len = struct.unpack("!Q", ext_len)[0]

        mask_key = b""
        if is_masked:
            mask_key = await self.reader.readexactly(4)

        payload = await self.reader.readexactly(payload_len)
        if is_masked:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

        if opcode == 0x9:  # Ping -> reply with Pong (0x8A)
            if self.writer and not self.closed:
                pong_mask = os.urandom(4)
                masked_pong = bytes(b ^ pong_mask[i % 4] for i, b in enumerate(payload))
                pong_header = struct.pack("!BB", 0x8A, 0x80 | len(payload))
                self.writer.write(pong_header + pong_mask + masked_pong)
                await self.writer.drain()
            return await self.recv_frame()
        elif opcode == 0x8:  # Close
            await self.close()
            return 0x8, b""

        return opcode, payload

    async def recv_text(self) -> Optional[str]:
        opcode, data = await self.recv_frame()
        if opcode == 0x8:
            return None
        return data.decode("utf-8", errors="replace")

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        if self.writer:
            try:
                mask = os.urandom(4)
                header = struct.pack("!BB", 0x88, 0x80)
                self.writer.write(header + mask)
                await self.writer.drain()
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Feed Ingestion Workers
# ---------------------------------------------------------------------------


class BaseWorker:
    name: str = "base"
    interval_seconds: float = 30.0

    def __init__(self, store: EventStore, on_event: Callable[[TelemetryEvent], None]):
        self.store = store
        self.on_event = on_event
        self.last_run: float = 0.0
        self.last_status: str = "initialized"
        self.error_count: int = 0

    async def run_loop(self) -> None:
        while True:
            try:
                self.last_run = time.time()
                await self.poll()
                self.last_status = "healthy"
            except Exception as e:
                self.error_count += 1
                self.last_status = f"error: {str(e)}"
                logger.error("[%s worker] Polling failure: %s", self.name, e)
            await asyncio.sleep(self.interval_seconds)

    async def poll(self) -> None:
        raise NotImplementedError


class AviationSquawkWorker(BaseWorker):
    """Monitors live emergency transponder squawks (7700 emergency, 7600 lost comms, 7500 hijack)."""

    name = "aviation_squawk"
    interval_seconds = 15.0

    async def poll(self) -> None:
        squawk_endpoints = {
            "7700": ("P1_HIGH", "🚨 General Emergency"),
            "7600": ("P2_ADVISORY", "📻 Radio Failure / Lost Comms"),
            "7500": ("P0_CRITICAL", "⛔ Aircraft Hijacking / Unlawful Interference"),
        }

        loop = asyncio.get_running_loop()
        for code, (severity, label) in squawk_endpoints.items():
            url = f"https://api.adsb.lol/v2/squawk/{code}"
            data = await loop.run_in_executor(None, fetch_json, url)
            if not data or not isinstance(data, dict):
                continue

            for ac in data.get("ac", []):
                hex_id = ac.get("hex", "").strip().upper()
                if not hex_id:
                    continue

                event_id = f"squawk_{code}_{hex_id}"
                callsign = ac.get("flight", "UNKNOWN").strip()
                alt = ac.get("alt_baro", "N/A")
                lat = ac.get("lat")
                lon = ac.get("lon")
                track = ac.get("track")
                spd = ac.get("gs")

                event = TelemetryEvent(
                    id=event_id,
                    domain="aviation",
                    severity=severity,
                    title=f"{label}: Flight {callsign} ({hex_id})",
                    summary=f"Transponder Squawk {code} detected. Altitude: {alt} ft, Speed: {spd} kts, Heading: {track}°",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    latitude=lat if isinstance(lat, (int, float)) else None,
                    longitude=lon if isinstance(lon, (int, float)) else None,
                    metadata={"hex": hex_id, "flight": callsign, "altitude": alt, "speed": spd, "squawk": code},
                    source_url=url,
                )

                if self.store.add(event):
                    self.on_event(event)


class SeismicWorker(BaseWorker):
    """Monitors USGS real-time global earthquake feeds (M4.5+ and significant events)."""

    name = "seismic_usgs"
    interval_seconds = 45.0

    async def poll(self) -> None:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_hour.geojson"
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, fetch_json, url)
        if not data or "features" not in data:
            return

        for feature in data.get("features", []):
            eid = feature.get("id")
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])

            if not eid:
                continue

            mag = props.get("mag", 0.0)
            place = props.get("place", "Unknown location")
            tsunami = props.get("tsunami", 0)
            time_ms = props.get("time", 0)
            ts = datetime.fromtimestamp(time_ms / 1000.0, timezone.utc).isoformat()

            if mag >= 7.0 or tsunami == 1:
                severity = "P0_CRITICAL"
                icon = "🌋 TSUNAMI/MAJOR QUAKE"
            elif mag >= 6.0:
                severity = "P1_HIGH"
                icon = "🌍 STRONG EARTHQUAKE"
            else:
                severity = "P2_ADVISORY"
                icon = "🌐 MODERATE EARTHQUAKE"

            event = TelemetryEvent(
                id=f"usgs_{eid}",
                domain="seismic",
                severity=severity,
                title=f"{icon}: M{mag:.1f} — {place}",
                summary=f"Depth: {coords[2]} km | Tsunami Warning: {'YES' if tsunami else 'No'} | Felt: {props.get('felt', 'N/A')}",
                timestamp=ts,
                longitude=coords[0] if len(coords) > 0 else None,
                latitude=coords[1] if len(coords) > 1 else None,
                metadata={"mag": mag, "place": place, "tsunami": tsunami, "depth_km": coords[2]},
                source_url=props.get("url", url),
            )

            if self.store.add(event):
                self.on_event(event)


class SpaceWeatherWorker(BaseWorker):
    """Monitors NOAA Space Weather Prediction Center planetary geomagnetic storm and solar flare alerts."""

    name = "space_weather"
    interval_seconds = 60.0

    async def poll(self) -> None:
        url = "https://services.swpc.noaa.gov/products/alerts.json"
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, fetch_json, url)
        if not data or not isinstance(data, list):
            return

        for entry in data[:5]:
            issue_time = entry.get("issue_datetime", "")
            msg_id = entry.get("message_id", "")
            msg = entry.get("message", "")
            if not msg_id or not issue_time:
                continue

            event_id = f"swpc_{msg_id}"

            if "WARNING: Geomagnetic Storm Category G5" in msg or "WARNING: Solar Radiation Storm Category S5" in msg:
                severity = "P0_CRITICAL"
                title = "☀️ EXTREME SPACE WEATHER (G5/S5)"
            elif "WARNING: Geomagnetic Storm Category G4" in msg or "G3" in msg or "R4" in msg or "R5" in msg:
                severity = "P1_HIGH"
                title = "⚡ HIGH SPACE WEATHER ALERT (G3/G4/R4)"
            elif "WARNING" in msg or "WATCH" in msg:
                severity = "P2_ADVISORY"
                title = "📡 SPACE WEATHER WATCH/ADVISORY"
            else:
                continue

            summary_snippet = msg.replace("\r", " ").replace("\n", " ").strip()[:200]

            event = TelemetryEvent(
                id=event_id,
                domain="space_weather",
                severity=severity,
                title=title,
                summary=summary_snippet,
                timestamp=issue_time,
                metadata={"message_id": msg_id, "raw_message": msg},
                source_url="https://www.swpc.noaa.gov/",
            )

            if self.store.add(event):
                self.on_event(event)


class EMSCWebSocketWorker(BaseWorker):
    """Native WebSocket stream consumer for EMSC global seismic events."""

    name = "emsc_ws"

    def __init__(
        self,
        store: EventStore,
        on_event: Callable[[TelemetryEvent], None],
        host: str = "www.seismicportal.eu",
        port: int = 443,
        path: str = "/standing_order/websocket",
        use_ssl: bool = True,
    ):
        super().__init__(store, on_event)
        self.host = host
        self.port = port
        self.path = path
        self.use_ssl = use_ssl
        self._client: Optional[SimpleWebSocketClient] = None

    async def run_loop(self) -> None:
        backoff = 2.0
        while True:
            try:
                self.last_status = "connecting"
                self._client = SimpleWebSocketClient(
                    host=self.host,
                    port=self.port,
                    path=self.path,
                    use_ssl=self.use_ssl,
                )
                await self._client.connect(timeout=10.0)
                self.last_status = "streaming"
                backoff = 2.0
                logger.info("[emsc_ws] Connected to EMSC Seismic WebSocket stream")

                while not self._client.closed:
                    self.last_run = time.time()
                    raw = await self._client.recv_text()
                    if raw is None:
                        break
                    self._process_message(raw)

            except asyncio.CancelledError:
                if self._client:
                    await self._client.close()
                break
            except Exception as e:
                self.error_count += 1
                self.last_status = f"error: {e}"
                logger.warning("[emsc_ws] Connection dropped: %s. Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, 60.0)

    def _process_message(self, raw: str) -> None:
        try:
            doc = json.loads(raw)
        except Exception:
            return

        # EMSC can send GeoJSON Feature or enveloped payload
        data = doc.get("data", doc)
        props = data.get("properties", {})
        geom = data.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])

        unid = data.get("unid") or data.get("id") or props.get("unid")
        if not unid:
            return

        mag = float(props.get("mag", 0.0) or 0.0)
        place = props.get("flynn_region") or props.get("region") or "Unknown Region"
        depth = coords[2] if len(coords) > 2 else props.get("depth")
        ts = props.get("time") or datetime.now(timezone.utc).isoformat()

        if mag >= 7.0:
            severity = "P0_CRITICAL"
            icon = "🌋 MAJOR EARTHQUAKE"
        elif mag >= 6.0:
            severity = "P1_HIGH"
            icon = "🌍 STRONG EARTHQUAKE"
        else:
            severity = "P2_ADVISORY"
            icon = "🌐 MODERATE EARTHQUAKE"

        event = TelemetryEvent(
            id=f"emsc_{unid}",
            domain="seismic",
            severity=severity,
            title=f"{icon}: M{mag:.1f} — {place}",
            summary=f"Depth: {depth} km | Real-Time WebSocket EMSC Feed | Source: {props.get('source_catalog', 'EMSC')}",
            timestamp=ts,
            longitude=coords[0] if len(coords) > 0 and coords[0] is not None else None,
            latitude=coords[1] if len(coords) > 1 and coords[1] is not None else None,
            metadata={"mag": mag, "region": place, "depth": depth, "raw": props},
            source_url="https://www.seismicportal.eu/",
        )

        if self.store.add(event):
            self.on_event(event)


class RipeRisWebSocketWorker(BaseWorker):
    """Native WebSocket stream consumer for RIPE RIS Live global BGP updates and anomalies."""

    name = "ripe_ris_ws"

    def __init__(
        self,
        store: EventStore,
        on_event: Callable[[TelemetryEvent], None],
        host: str = "ris-live.ripe.net",
        port: int = 443,
        path: str = "/v1/ws?client=hummbl-situation",
        use_ssl: bool = True,
    ):
        super().__init__(store, on_event)
        self.host = host
        self.port = port
        self.path = path
        self.use_ssl = use_ssl
        self._client: Optional[SimpleWebSocketClient] = None

    async def run_loop(self) -> None:
        backoff = 2.0
        while True:
            try:
                self.last_status = "connecting"
                self._client = SimpleWebSocketClient(
                    host=self.host,
                    port=self.port,
                    path=self.path,
                    use_ssl=self.use_ssl,
                )
                await self._client.connect(timeout=10.0)
                # Subscribe to BGP updates
                sub_payload = json.dumps({"type": "ris_subscribe", "data": {"moreSpecific": True, "type": "UPDATE"}})
                await self._client.send_text(sub_payload)
                self.last_status = "streaming"
                backoff = 2.0
                logger.info("[ripe_ris_ws] Connected to RIPE RIS Live BGP stream")

                while not self._client.closed:
                    self.last_run = time.time()
                    raw = await self._client.recv_text()
                    if raw is None:
                        break
                    self._process_message(raw)

            except asyncio.CancelledError:
                if self._client:
                    await self._client.close()
                break
            except Exception as e:
                self.error_count += 1
                self.last_status = f"error: {e}"
                logger.warning("[ripe_ris_ws] BGP Stream dropped: %s. Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, 60.0)

    def _process_message(self, raw: str) -> None:
        try:
            doc = json.loads(raw)
        except Exception:
            return

        if doc.get("type") != "ris_message":
            return

        data = doc.get("data", {})
        peer = data.get("peer", "unknown")
        peer_asn = data.get("peer_asn", "unknown")
        msg_id = data.get("id") or f"{peer}_{time.time()}"
        path = data.get("path", [])
        withdrawals = data.get("withdrawals", [])
        announcements = data.get("announcements", [])

        # Detect BGP route anomalies
        num_withdrawn = len(withdrawals)
        is_large_withdrawal = num_withdrawn >= 10
        is_path_anomaly = len(path) >= 12

        if num_withdrawn >= 50:
            severity = "P0_CRITICAL"
            title = f"⚡ MASS BGP WITHDRAWAL: {num_withdrawn} prefixes (AS{peer_asn})"
        elif is_large_withdrawal:
            severity = "P1_HIGH"
            title = f"⚠️ BGP ROUTE FLAP: {num_withdrawn} withdrawals via AS{peer_asn}"
        elif is_path_anomaly:
            severity = "P1_HIGH"
            title = f"🔁 AS-PATH LOOP / INFLATION: {len(path)} hops (AS{peer_asn})"
        else:
            severity = "P2_ADVISORY"
            title = f"🌐 BGP ROUTE UPDATE: AS{peer_asn} via {peer}"

        total_prefixes = num_withdrawn + sum(len(a.get("prefixes", [])) for a in announcements)
        summary = (
            f"Peer: {peer} (AS{peer_asn}) | Path: {path[:6]}{'...' if len(path) > 6 else ''} | "
            f"Withdrawals: {num_withdrawn} | Announcements: {len(announcements)} | Total Prefixes: {total_prefixes}"
        )

        event = TelemetryEvent(
            id=f"bgp_{msg_id}",
            domain="network",
            severity=severity,
            title=title,
            summary=summary,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "peer": peer,
                "peer_asn": peer_asn,
                "path": path,
                "withdrawals_count": num_withdrawn,
                "announcements_count": len(announcements),
            },
            source_url="https://ris-live.ripe.net/",
        )

        if self.store.add(event):
            self.on_event(event)


# ---------------------------------------------------------------------------
# Multi-Channel Alert Dispatcher (Discord, Telegram, ntfy, Webhooks)
# ---------------------------------------------------------------------------


class AlertDispatcher:
    def __init__(
        self,
        webhook_urls: Optional[List[str]] = None,
        discord_webhook_url: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        ntfy_topic: Optional[str] = None,
        ntfy_url: str = "https://ntfy.sh",
    ):
        self.webhook_urls = webhook_urls or []
        self.discord_webhook_url = discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "").strip() or None
        self.telegram_bot_token = telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip() or None
        self.ntfy_topic = ntfy_topic or os.getenv("NTFY_TOPIC", "").strip() or None
        self.ntfy_url = (ntfy_url or os.getenv("NTFY_URL", "https://ntfy.sh")).rstrip("/")

    def dispatch(self, event: TelemetryEvent) -> None:
        # 1. Console / Terminal SITREP output
        colors = {
            "P0_CRITICAL": "\033[91;1m",  # Bold Red
            "P1_HIGH": "\033[93;1m",  # Bold Yellow
            "P2_ADVISORY": "\033[94m",  # Blue
        }
        reset = "\033[0m"
        color = colors.get(event.severity, "")
        print(f"\n{color}[SITREP ALERT | {event.severity}] {event.title}{reset}")
        print(f"  Domain:    {event.domain.upper()}")
        print(f"  Summary:   {event.summary}")
        if event.latitude is not None and event.longitude is not None:
            print(f"  Location:  {event.latitude:.4f}, {event.longitude:.4f}")
        print(f"  Timestamp: {event.timestamp}\n")

        # 2. Dispatch to external channels asynchronously in background thread
        threading.Thread(target=self._send_all_channels, args=(event,), daemon=True).start()

    def _send_all_channels(self, event: TelemetryEvent) -> None:
        # Discord Dispatch
        if self.discord_webhook_url:
            self._send_discord(event, self.discord_webhook_url)

        # Telegram Dispatch
        if self.telegram_bot_token and self.telegram_chat_id:
            self._send_telegram(event, self.telegram_bot_token, self.telegram_chat_id)

        # ntfy Dispatch
        if self.ntfy_topic:
            self._send_ntfy(event, self.ntfy_url, self.ntfy_topic)

        # Generic Webhooks
        for url in self.webhook_urls:
            self._send_generic_webhook(event, url)

    def _send_discord(self, event: TelemetryEvent, url: str) -> None:
        payload = json.dumps(
            {
                "content": f"**[{event.severity}] {event.title}**\n{event.summary}\n`Timestamp: {event.timestamp}`",
                "embeds": [
                    {
                        "title": event.title,
                        "description": event.summary,
                        "color": 15158332 if "P0" in event.severity else (15105570 if "P1" in event.severity else 3447003),
                        "fields": [
                            {"name": "Domain", "value": event.domain.upper(), "inline": True},
                            {
                                "name": "Coordinates",
                                "value": f"{event.latitude:.4f},{event.longitude:.4f}" if event.latitude else "N/A",
                                "inline": True,
                            },
                        ],
                    }
                ],
            }
        ).encode("utf-8")
        self._post_http(url, payload, {"Content-Type": "application/json"})

    def _send_telegram(self, event: TelemetryEvent, token: str, chat_id: str) -> None:
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = (
            f"<b>[{event.severity}] {event.title}</b>\n\n"
            f"<b>Domain:</b> {event.domain.upper()}\n"
            f"<b>Summary:</b> {event.summary}\n"
            f"<b>Timestamp:</b> <code>{event.timestamp}</code>"
        )
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        self._post_http(api_url, payload, {"Content-Type": "application/json"})

    def _send_ntfy(self, event: TelemetryEvent, base_url: str, topic: str) -> None:
        target_url = f"{base_url}/{topic}"
        priority_map = {"P0_CRITICAL": "5", "P1_HIGH": "4", "P2_ADVISORY": "3"}
        headers = {
            "Title": event.title,
            "Priority": priority_map.get(event.severity, "3"),
            "Tags": f"{event.domain},warning",
        }
        payload = event.summary.encode("utf-8")
        self._post_http(target_url, payload, headers)

    def _send_generic_webhook(self, event: TelemetryEvent, url: str) -> None:
        payload = json.dumps(event.to_dict()).encode("utf-8")
        self._post_http(url, payload, {"Content-Type": "application/json"})

    def _post_http(self, url: str, data: bytes, headers: Dict[str, str]) -> None:
        req_headers = {"User-Agent": "HUMMBL-SituationDaemon/1.0"}
        req_headers.update(headers)
        req = urllib.request.Request(url, data=data, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=5.0):
                pass
        except Exception as e:
            logger.debug("Dispatch failure to %s: %s", url, e)


# ---------------------------------------------------------------------------
# Embedded Tactical Web Radar & REST API Server
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HUMMBL Situation Room — Tactical Global Radar</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    :root {
      --bg-dark: #0a0c10;
      --card-bg: #12161f;
      --border: #212936;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
      --accent-red: #ef4444;
      --accent-amber: #f59e0b;
      --accent-blue: #3b82f6;
      --accent-green: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg-dark); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    header { background: var(--card-bg); border-bottom: 1px solid var(--border); padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    header h1 { font-size: 16px; letter-spacing: 1.5px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; font-weight: 700; color: #fff; }
    .pulse-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent-green); box-shadow: 0 0 10px var(--accent-green); animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .status-badges { display: flex; gap: 10px; font-size: 12px; }
    .badge { background: #1e293b; padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border); }
    main { display: flex; flex: 1; height: calc(100vh - 50px); }
    #map { flex: 2; height: 100%; background: #05070a; }
    #feed-panel { flex: 1; max-width: 450px; background: var(--card-bg); border-left: 1px solid var(--border); display: flex; flex-direction: column; }
    .panel-header { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; font-weight: 600; text-transform: uppercase; color: var(--text-dim); }
    #events-list { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
    .event-card { background: #1a202c; border: 1px solid var(--border); border-radius: 6px; padding: 12px; transition: transform 0.1s; }
    .event-card:hover { transform: translateY(-2px); border-color: #3b82f6; }
    .event-card.P0_CRITICAL { border-left: 4px solid var(--accent-red); }
    .event-card.P1_HIGH { border-left: 4px solid var(--accent-amber); }
    .event-card.P2_ADVISORY { border-left: 4px solid var(--accent-blue); }
    .card-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #fff; }
    .card-summary { font-size: 12px; color: var(--text-dim); line-height: 1.4; margin-bottom: 6px; }
    .card-meta { font-size: 11px; color: #64748b; display: flex; justify-content: space-between; }
  </style>
</head>
<body>
  <header>
    <h1><span class="pulse-dot"></span> HUMMBL Situation Room // Tactical Radar</h1>
    <div class="status-badges">
      <span class="badge" id="stat-events">0 Active Telemetries</span>
      <span class="badge" id="stat-uptime">Uptime: 0s</span>
    </div>
  </header>
  <main>
    <div id="map"></div>
    <div id="feed-panel">
      <div class="panel-header">Live Telemetry Feed (Auto-Refreshed)</div>
      <div id="events-list"></div>
    </div>
  </main>

  <script>
    const map = L.map('map', { zoomControl: true }).setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap, CartoDB',
      maxZoom: 18
    }).addTo(map);

    const markers = [];

    async function refreshData() {
      try {
        const [evResp, stResp] = await Promise.all([
          fetch('/api/events'),
          fetch('/api/status')
        ]);
        const events = await evResp.json();
        const status = await stResp.json();

        document.getElementById('stat-events').innerText = `${status.events_in_memory} Active Telemetries`;
        document.getElementById('stat-uptime').innerText = `Uptime: ${status.uptime_seconds}s`;

        const listContainer = document.getElementById('events-list');
        listContainer.innerHTML = '';
        markers.forEach(m => map.removeLayer(m));
        markers.length = 0;

        events.forEach(ev => {
          const card = document.createElement('div');
          card.className = `event-card ${ev.severity}`;
          card.innerHTML = `
            <div class="card-title">${ev.title}</div>
            <div class="card-summary">${ev.summary}</div>
            <div class="card-meta">
              <span><b>${ev.domain.toUpperCase()}</b></span>
              <span>${new Date(ev.timestamp).toLocaleTimeString()}</span>
            </div>
          `;
          listContainer.appendChild(card);

          if (ev.latitude != null && ev.longitude != null) {
            const color = ev.severity === 'P0_CRITICAL' ? '#ef4444' : (ev.severity === 'P1_HIGH' ? '#f59e0b' : '#3b82f6');
            const marker = L.circleMarker([ev.latitude, ev.longitude], {
              radius: ev.severity === 'P0_CRITICAL' ? 9 : 6,
              color: color,
              fillColor: color,
              fillOpacity: 0.6,
              weight: 2
            }).bindPopup(`<b>${ev.title}</b><br/>${ev.summary}<br/><small>${ev.timestamp}</small>`);

            marker.addTo(map);
            markers.push(marker);
          }
        });
      } catch (err) {
        console.error("Telemetry sync error:", err);
      }
    }

    setInterval(refreshData, 5000);
    refreshData();
  </script>
</body>
</html>
"""


class SituationHTTPHandler(http.server.BaseHTTPRequestHandler):
    store: Optional[EventStore] = None
    start_time: float = time.time()

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        elif self.path == "/api/events":
            events = self.store.get_recent(100) if self.store else []
            body = json.dumps([e.to_dict() for e in events]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            status = {
                "daemon": "HUMMBL Situation Daemon",
                "uptime_seconds": int(time.time() - self.start_time),
                "events_in_memory": len(self.store.get_recent(500)) if self.store else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            body = json.dumps(status).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_http_server(store: EventStore, port: int = 8765) -> socketserver.TCPServer:
    handler = SituationHTTPHandler
    handler.store = store
    handler.start_time = time.time()

    class ReusableServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    httpd = ReusableServer(("127.0.0.1", port), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    logger.info("Tactical Situation Radar live at http://127.0.0.1:%d/", port)
    return httpd


# ---------------------------------------------------------------------------
# Terminal TUI Mode (ANSI Escapes)
# ---------------------------------------------------------------------------


async def run_tui_dashboard(daemon: SituationDaemon) -> None:
    """Headless Terminal TUI monitoring loop displaying real-time ASCII war room metrics."""
    CLEAR_SCREEN = "\033[2J\033[H"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"

    while True:
        try:
            uptime = int(time.time() - daemon.start_time)
            recent_events = daemon.store.get_recent(15)

            lines = [
                CLEAR_SCREEN,
                f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗{RESET}",
                f"{BOLD}{CYAN}║             HUMMBL GLOBAL SITUATION RADAR // TACTICAL HEADLESS TUI               ║{RESET}",
                f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝{RESET}",
                f" Uptime: {GREEN}{uptime}s{RESET} | Radar Web: {GREEN}http://127.0.0.1:{daemon.port}/{RESET} | Total Cached Events: {BOLD}{len(daemon.store.get_recent(500))}{RESET}",
                "-" * 84,
                f"{BOLD}ACTIVE TELEMETRY WORKERS:{RESET}",
            ]

            for w in daemon.workers:
                status_color = GREEN if "stream" in w.last_status or "health" in w.last_status else (RED if "error" in w.last_status else YELLOW)
                lines.append(f"  • {w.name:<18} Status: {status_color}{w.last_status:<12}{RESET} Errors: {w.error_count:<4}")

            lines.extend([
                "-" * 84,
                f"{BOLD}RECENT TELEMETRY EVENTS:{RESET}",
                f" {'TIME':<10} {'SEV':<12} {'DOMAIN':<14} {'TITLE'}",
                f" {'-'*8} {'-'*10} {'-'*12} {'-'*48}",
            ])

            for ev in recent_events[:10]:
                sev_color = RED if "P0" in ev.severity else (YELLOW if "P1" in ev.severity else CYAN)
                t_str = ev.timestamp[11:19] if len(ev.timestamp) >= 19 else ev.timestamp
                title_snip = ev.title[:48]
                lines.append(f" {t_str:<10} {sev_color}{ev.severity:<12}{RESET} {ev.domain.upper():<14} {title_snip}")

            lines.append("\n[Press Ctrl+C to terminate Situation Daemon]\n")
            print("\n".join(lines), end="", flush=True)

        except Exception as e:
            logger.debug("TUI render error: %s", e)

        await asyncio.sleep(2.0)


# ---------------------------------------------------------------------------
# Daemon Core Orchestrator
# ---------------------------------------------------------------------------


class SituationDaemon:
    def __init__(
        self,
        port: int = 8765,
        webhook_urls: Optional[List[str]] = None,
        enable_ws: bool = True,
        enable_tui: bool = False,
    ):
        self.port = port
        self.enable_ws = enable_ws
        self.enable_tui = enable_tui
        self.start_time = time.time()
        self.store = EventStore(ttl_seconds=7200)
        self.dispatcher = AlertDispatcher(webhook_urls=webhook_urls)

        # Standard polling workers
        self.workers: List[BaseWorker] = [
            AviationSquawkWorker(self.store, self.dispatcher.dispatch),
            SeismicWorker(self.store, self.dispatcher.dispatch),
            SpaceWeatherWorker(self.store, self.dispatcher.dispatch),
        ]

        # Native WebSocket streaming workers
        if self.enable_ws:
            self.workers.append(EMSCWebSocketWorker(self.store, self.dispatcher.dispatch))
            self.workers.append(RipeRisWebSocketWorker(self.store, self.dispatcher.dispatch))

        self.http_server: Optional[socketserver.TCPServer] = None

    async def start(self) -> None:
        logger.info("Initializing HUMMBL Situation Monitoring Daemon (WS enabled: %s)...", self.enable_ws)
        self.http_server = run_http_server(self.store, port=self.port)

        worker_tasks = [asyncio.create_task(w.run_loop()) for w in self.workers]
        logger.info("All telemetry workers engaged (%d workers active).", len(self.workers))

        if self.enable_tui:
            tui_task = asyncio.create_task(run_tui_dashboard(self))
            worker_tasks.append(tui_task)

        try:
            await asyncio.gather(*worker_tasks)
        except asyncio.CancelledError:
            logger.info("Shutting down Situation Daemon...")
        finally:
            if self.http_server:
                self.http_server.shutdown()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HUMMBL Tactical Global Situation Monitoring Daemon")
    parser.add_argument("--port", type=int, default=int(os.getenv("SITUATION_PORT", "8765")), help="HTTP Radar port")
    parser.add_argument("--webhooks", type=str, default=os.getenv("SITUATION_WEBHOOKS", ""), help="Comma-separated webhooks")
    parser.add_argument("--no-ws", action="store_true", help="Disable WebSocket stream workers (polling only)")
    parser.add_argument("--tui", action="store_true", help="Enable terminal TUI monitoring dashboard")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    webhooks_list = [u.strip() for u in args.webhooks.split(",") if u.strip()]
    daemon = SituationDaemon(
        port=args.port,
        webhook_urls=webhooks_list,
        enable_ws=not args.no_ws,
        enable_tui=args.tui,
    )
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        print("\n[Situation Daemon terminated by user]")
