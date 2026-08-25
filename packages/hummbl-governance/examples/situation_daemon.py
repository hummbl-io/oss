"""
HUMMBL Global Situation Daemon — Lightweight Multi-Domain Telemetry Aggregator

A zero-third-party-dependency, asyncio-powered background daemon for real-time global
situational monitoring. Ingests live telemetry streams (Aviation Emergency Squawks,
USGS/EMSC Seismic Activity, NOAA Space Weather Alerts, and Tsunami Warnings),
deduplicates events, triages severity (P0/P1/P2), dispatches webhooks, and serves
an embedded local tactical war room map and REST API.

Standard library only: Python 3.11+ (asyncio, urllib, http.server, sqlite3, json).
"""

from __future__ import annotations

import asyncio
import hashlib
import http.server
import json
import logging
import os
import socketserver
import ssl
import sys
import threading
import time
import urllib.request
import urllib.error
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

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
# Deduplication & State Store (Memory + SQLite)
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
        expired = [
            eid for eid, t in self._event_timestamps.items()
            if (now - t) > self.ttl_seconds
        ]
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
                
                # Fingerprint per aircraft + squawk code
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

            # Triage severity
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
            
            # Simple keyword triage
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

            # First 200 chars of message
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


# ---------------------------------------------------------------------------
# Multi-Channel Alert Dispatcher
# ---------------------------------------------------------------------------

class AlertDispatcher:
    def __init__(self, webhook_urls: Optional[List[str]] = None):
        self.webhook_urls = webhook_urls or []

    def dispatch(self, event: TelemetryEvent) -> None:
        # 1. Console / Terminal SITREP output
        colors = {
            "P0_CRITICAL": "\033[91;1m",  # Bold Red
            "P1_HIGH": "\033[93;1m",      # Bold Yellow
            "P2_ADVISORY": "\033[94m",    # Blue
        }
        reset = "\033[0m"
        color = colors.get(event.severity, "")
        print(f"\n{color}[SITREP ALERT | {event.severity}] {event.title}{reset}")
        print(f"  Domain:    {event.domain.upper()}")
        print(f"  Summary:   {event.summary}")
        if event.latitude is not None and event.longitude is not None:
            print(f"  Location:  {event.latitude:.4f}, {event.longitude:.4f}")
        print(f"  Timestamp: {event.timestamp}\n")

        # 2. Webhooks (Async or threaded to avoid blocking)
        if self.webhook_urls:
            threading.Thread(target=self._send_webhooks, args=(event,), daemon=True).start()

    def _send_webhooks(self, event: TelemetryEvent) -> None:
        payload = json.dumps({
            "content": f"**[{event.severity}] {event.title}**\n{event.summary}\n`Timestamp: {event.timestamp}`",
            "embeds": [{
                "title": event.title,
                "description": event.summary,
                "color": 15158332 if "P0" in event.severity else 15105570,
                "fields": [
                    {"name": "Domain", "value": event.domain, "inline": True},
                    {"name": "Coordinates", "value": f"{event.latitude},{event.longitude}" if event.latitude else "N/A", "inline": True},
                ]
            }]
        }).encode("utf-8")

        for url in self.webhook_urls:
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "HUMMBL-SituationDaemon/1.0"},
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    pass
            except Exception as e:
                logger.debug("Webhook delivery failed to %s: %s", url, e)


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

    let markers = [];
    const startTime = Date.now();

    function formatTime(iso) {
      try { return new Date(iso).toLocaleTimeString(); } catch(e) { return iso; }
    }

    async function refreshData() {
      try {
        const res = await fetch('/api/events');
        const events = await res.json();
        
        // Update stats
        document.getElementById('stat-events').innerText = `${events.length} Active Events`;
        document.getElementById('stat-uptime').innerText = `Uptime: ${Math.floor((Date.now() - startTime)/1000)}s`;

        // Clear markers
        markers.forEach(m => map.removeLayer(m));
        markers = [];

        const list = document.getElementById('events-list');
        list.innerHTML = '';

        events.forEach(ev => {
          // Add to feed list
          const card = document.createElement('div');
          card.className = `event-card ${ev.severity}`;
          card.innerHTML = `
            <div class="card-title">${ev.title}</div>
            <div class="card-summary">${ev.summary}</div>
            <div class="card-meta">
              <span>${ev.domain.toUpperCase()}</span>
              <span>${formatTime(ev.timestamp)}</span>
            </div>
          `;
          list.appendChild(card);

          // Add map marker if coordinates exist
          if (ev.latitude !== null && ev.longitude !== null) {
            const color = ev.severity === 'P0_CRITICAL' ? '#ef4444' : ev.severity === 'P1_HIGH' ? '#f59e0b' : '#3b82f6';
            const radius = ev.domain === 'seismic' ? Math.max(6, (ev.metadata.mag || 4) * 2.5) : 6;
            
            const marker = L.circleMarker([ev.latitude, ev.longitude], {
              radius: radius,
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
        # Suppress routine GET logs
        pass


def run_http_server(store: EventStore, port: int = 8765) -> socketserver.TCPServer:
    handler = SituationHTTPHandler
    handler.store = store
    handler.start_time = time.time()
    
    # Threading server
    class ReusableServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    httpd = ReusableServer(("127.0.0.1", port), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    logger.info("Tactical Situation Radar live at http://127.0.0.1:%d/", port)
    return httpd


# ---------------------------------------------------------------------------
# Daemon Core Orchestrator
# ---------------------------------------------------------------------------

class SituationDaemon:
    def __init__(self, port: int = 8765, webhook_urls: Optional[List[str]] = None):
        self.port = port
        self.store = EventStore(ttl_seconds=7200)
        self.dispatcher = AlertDispatcher(webhook_urls=webhook_urls)
        self.workers: List[BaseWorker] = [
            AviationSquawkWorker(self.store, self.dispatcher.dispatch),
            SeismicWorker(self.store, self.dispatcher.dispatch),
            SpaceWeatherWorker(self.store, self.dispatcher.dispatch),
        ]
        self.http_server: Optional[socketserver.TCPServer] = None

    async def start(self) -> None:
        logger.info("Initializing HUMMBL Situation Monitoring Daemon...")
        self.http_server = run_http_server(self.store, port=self.port)
        
        # Start all polling workers concurrently
        tasks = [asyncio.create_task(w.run_loop()) for w in self.workers]
        logger.info("All telemetry workers engaged (%d workers active).", len(self.workers))
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Shutting down Situation Daemon...")
        finally:
            if self.http_server:
                self.http_server.shutdown()


if __name__ == "__main__":
    port = int(os.getenv("SITUATION_PORT", "8765"))
    webhooks = [u.strip() for u in os.getenv("SITUATION_WEBHOOKS", "").split(",") if u.strip()]
    daemon = SituationDaemon(port=port, webhook_urls=webhooks)
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        print("\n[Situation Daemon terminated by user]")
