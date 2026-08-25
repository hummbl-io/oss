#!/usr/bin/env python3
"""HRSI Bridge Server — HTTP endpoint for cross-machine HRSI check-ins.

Receives HRSI cycle data via HTTP POST and appends to the local cognition
state (hrsi_cycles.jsonl + belonging_baseline.jsonl + CLP ledger).
Mirrors the bus bridge architecture: Tailscale-only binding, Bearer token
auth, default-deny protected operations.

Usage:
    python -m hummbl_cognition.hrsi_bridge_server --port 18791
    python -m hummbl_cognition.hrsi_bridge_server --port 18791 --bind-all
"""

from __future__ import annotations

import argparse
import datetime as dt
import hmac
import json
import logging
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hummbl_cognition.hrsi_checkin import (
    CYCLES_PATH,
    get_status,
    record_cycle,
)
from hummbl_cognition.belonging_check import (
    BASELINE_PATH,
    COGSTATE_VALUES,
    SCORE_RANGE,
)

logger = logging.getLogger(__name__)

DEFAULT_PORT = 18791
MAX_REQUEST_BODY = 1_048_576


# ---------------------------------------------------------------------------
# Credential loading (mirrors bus bridge_server._load_bridge_credentials)
# ---------------------------------------------------------------------------

def _load_bridge_credentials() -> dict[str, str]:
    """Load rotatable client credentials from env or an external file.

    A JSON token file maps client IDs to bearer tokens. A plaintext file or
    HRSI_BRIDGE_TOKEN remains supported as the single-client ``default`` form.
    """
    env_token = os.environ.get("HRSI_BRIDGE_TOKEN", "").strip()
    if env_token:
        return {"default": env_token}

    token_file = os.environ.get("HRSI_BRIDGE_TOKEN_FILE", "").strip()
    if not token_file:
        return {}

    try:
        raw = Path(token_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        logger.exception("Failed to read HRSI_BRIDGE_TOKEN_FILE")
        return {}

    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"default": raw}
    if not isinstance(parsed, dict) or not all(
        isinstance(k, str) and isinstance(v, str) and v.strip()
        for k, v in parsed.items()
    ):
        logger.error("HRSI_BRIDGE_TOKEN_FILE must contain a client-to-token JSON object")
        return {}
    return {k: v.strip() for k, v in parsed.items()}


# ---------------------------------------------------------------------------
# Tailscale IP detection (mirrors bus bridge_server.get_tailscale_ip)
# ---------------------------------------------------------------------------

def get_tailscale_ip() -> str | None:
    """Detect the local Tailscale IPv4 address."""
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    try:
        for line in subprocess.run(
            ["ifconfig"], capture_output=True, text=True
        ).stdout.split("\n"):
            if "inet 100." in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "inet" and i + 1 < len(parts):
                        ip = parts[i + 1]
                        if ip.startswith("100."):
                            return ip
    except Exception:
        logger.exception("Failed to detect Tailscale IP")

    return None


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class HRSIBridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving remote HRSI check-ins."""

    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def _client_ip(self) -> str:
        try:
            return self.client_address[0]
        except Exception:
            return "?"

    def _check_auth(self) -> bool:
        """Default-deny; only /health is unauthenticated.

        Uses hmac.compare_digest for constant-time comparison.
        """
        credentials = _load_bridge_credentials()
        client_id = self.headers.get("X-Bridge-Client-ID", "").strip() or None
        auth_header = self.headers.get("Authorization", "")
        supplied = auth_header.removeprefix("Bearer ").strip()
        matched_id = None
        for candidate_id, token in credentials.items():
            if hmac.compare_digest(supplied, token):
                if client_id is None or client_id == candidate_id:
                    matched_id = candidate_id
                    break
        if matched_id is None:
            status = 503 if not credentials else 401
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "HRSI bridge authentication required"}).encode()
            )
            return False
        return True

    def _json_response(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # ------------------------------------------------------------------
    # POST /hrsi — record a check-in cycle
    # ------------------------------------------------------------------

    def do_POST(self) -> None:
        if self.path not in ("/hrsi", "/hrsi-checkin", "/api/hrsi/checkin"):
            self.send_error(404, "Not found")
            return

        if not self._check_auth():
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > MAX_REQUEST_BODY:
                self.send_error(413, "Payload too large")
                return
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            cogstate = data.get("cogstate")
            safety = data.get("safety")
            mattering = data.get("mattering")
            connection = data.get("connection")
            hule = data.get("hule")
            lens = data.get("lens")
            delta = data.get("delta")
            energy = data.get("energy")
            sleep_hours = data.get("sleep_hours")
            relational_note = data.get("relational_note")
            origin_machine = data.get("origin_machine")
            force = bool(data.get("force", False))

            # Validate required fields
            missing = []
            if cogstate is None:
                missing.append("cogstate")
            if safety is None:
                missing.append("safety")
            if mattering is None:
                missing.append("mattering")
            if connection is None:
                missing.append("connection")
            if not hule:
                missing.append("hule")
            if missing:
                self._json_response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=400,
                )
                return

            # Type coercion (JSON numbers may arrive as int or float)
            safety = int(safety)
            mattering = int(mattering)
            connection = int(connection)
            if energy is not None:
                energy = int(energy)
            if sleep_hours is not None:
                sleep_hours = float(sleep_hours)

            # Validate ranges
            if cogstate not in COGSTATE_VALUES:
                self._json_response(
                    {"error": f"cogstate must be one of {sorted(COGSTATE_VALUES)}, got {cogstate!r}"},
                    status=400,
                )
                return
            for name, val in [("safety", safety), ("mattering", mattering), ("connection", connection)]:
                if val not in SCORE_RANGE:
                    self._json_response(
                        {"error": f"{name} must be 1-5, got {val}"},
                        status=400,
                    )
                    return
            if energy is not None and energy not in SCORE_RANGE:
                self._json_response({"error": f"energy must be 1-5, got {energy}"}, status=400)
                return
            if sleep_hours is not None and not (0 <= sleep_hours <= 24):
                self._json_response(
                    {"error": f"sleep_hours must be 0-24, got {sleep_hours}"},
                    status=400,
                )
                return

            cycle = record_cycle(
                cogstate=cogstate,
                safety=safety,
                mattering=mattering,
                connection=connection,
                hule=hule,
                lens=lens,
                delta=delta,
                energy=energy,
                sleep_hours=sleep_hours,
                relational_note=relational_note,
                force=force,
            )

            logger.info(
                "HRSI cycle recorded via bridge from %s: %s | %s | belonging=%.1f",
                self._client_ip(),
                cycle["date"],
                cycle["cogstate"],
                cycle["belonging_avg"],
            )

            status = get_status()
            self._json_response({
                "status": "ok",
                "cycle": cycle,
                "gap1_qualifying_days": status["gap1_qualifying_days"],
                "gap1_closed": status["gap1_closed"],
                "current_streak": status["current_streak"],
                "total_cycles": status["total_cycles"],
                "origin_machine": origin_machine,
            })

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except ValueError as e:
            self._json_response({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("HRSI bridge POST failed")
            self.send_error(500, str(e))

    # ------------------------------------------------------------------
    # GET endpoints
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/health":
            credentials = _load_bridge_credentials()
            self._json_response({
                "status": "up",
                "service": "hrsi-bridge",
                "version": "1.0",
                "auth_enabled": bool(credentials),
                "cycles_path": str(CYCLES_PATH),
                "baseline_path": str(BASELINE_PATH),
            })
            return

        if path in ("/hrsi/status", "/hrsi-checkin/status"):
            if not self._check_auth():
                return
            status = get_status()
            self._json_response(status)
            return

        if path in ("/hrsi/last", "/hrsi-checkin/last"):
            if not self._check_auth():
                return
            if not CYCLES_PATH.exists():
                self._json_response({"cycle": None, "message": "no cycles logged"})
                return
            lines = [
                l for l in CYCLES_PATH.read_text(encoding="utf-8").splitlines() if l.strip()
            ]
            if not lines:
                self._json_response({"cycle": None, "message": "empty ledger"})
                return
            last = json.loads(lines[-1])
            self._json_response({"cycle": last})
            return

        self.send_error(404, "Not found")


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------

def run_server(port: int = DEFAULT_PORT, bind_all: bool = False) -> None:
    if bind_all:
        host = "0.0.0.0"
    else:
        tailscale_ip = get_tailscale_ip()
        if tailscale_ip:
            host = tailscale_ip
            print(f"Binding to Tailscale interface: {host}")
        else:
            host = "127.0.0.1"
            print("Warning: No Tailscale IP found, binding to localhost only")

    credentials = _load_bridge_credentials()
    server = ThreadingHTTPServer((host, port), HRSIBridgeHandler)
    server.daemon_threads = True
    print(f"HRSI Bridge Server running on http://{host}:{port}")
    print("Endpoints: POST /hrsi, GET /health, GET /hrsi/status, GET /hrsi/last")
    if credentials:
        print("Auth: POST/GET endpoints require Authorization: Bearer <HRSI_BRIDGE_TOKEN>")
    else:
        print("Auth: FAIL-CLOSED — configure HRSI_BRIDGE_TOKEN or HRSI_BRIDGE_TOKEN_FILE")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="HRSI Bridge Server for cross-machine HRSI check-ins"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--bind-all", "-a", action="store_true",
        help="Bind to all interfaces (default: Tailscale only)",
    )
    args = parser.parse_args()
    run_server(port=args.port, bind_all=args.bind_all)
