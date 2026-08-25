#!/usr/bin/env python3
"""
Bus Bridge Server - HTTP endpoint for cross-machine bus coordination.

Receives bus messages via HTTP POST and appends to local coordination bus.
Secure by default: binds to Tailscale interface only, requires Bearer token
auth (BUS_BRIDGE_TOKEN env var), and rejects client-supplied bus_path.
"""

import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .bus_writer import _resolve_bus_path, post_message


def _load_bridge_token() -> str | None:
    """Return the expected Bearer token from env var, or None if not configured."""
    env_token = os.environ.get("BUS_BRIDGE_TOKEN", "").strip()
    if env_token:
        return env_token
    token_file = os.environ.get("BUS_BRIDGE_TOKEN_FILE", "").strip()
    if not token_file:
        return None
    try:
        token = Path(token_file).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    return token or None


def _require_auth() -> bool:
    """Return True if POST auth is required (fail-closed when token not configured).

    Default: True (fail-closed). Set BUS_BRIDGE_ALLOW_NO_AUTH=1 to bypass
    (tests/dev only). Closes the prior fail-open default where a missing
    token silently accepted unauthenticated writes.
    """
    allow = os.environ.get("BUS_BRIDGE_ALLOW_NO_AUTH", "").strip().lower()
    return allow not in ("1", "true", "yes", "on")


MAX_TAIL_LINES = 10000  # DoS protection: cap on /bus/tail?n= and /bus/search?n=


class BusBridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving remote bus messages."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default logging - be quiet."""

    def _check_post_auth(self) -> bool:
        """Return True if the POST passes auth, False after sending 401.

        Uses hmac.compare_digest for constant-time comparison.
        """
        token = _load_bridge_token()
        if token is None:
            if _require_auth():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {"error": "Unauthorized: BUS_BRIDGE_TOKEN not configured"}
                    ).encode()
                )
                return False
            return True
        auth_header = self.headers.get("Authorization", "")
        expected = f"Bearer {token}"
        if not hmac.compare_digest(auth_header, expected):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return False
        return True

    def do_POST(self):
        """Handle incoming bus message."""
        if self.path != "/bus":
            self.send_error(404, "Not found")
            return

        if not self._check_post_auth():
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            # Required fields
            from_agent = data.get("from")
            to_agent = data.get("to", "all")
            msg_type = data.get("type", "STATUS")
            message = data.get("message")

            if not from_agent or not message:
                self.send_error(400, "Missing required fields: 'from' and 'message'")
                return

            # P0 fix (S-003): reject client-supplied bus_path — arbitrary file
            # write via path traversal. Always resolve to the canonical local
            # bus path.
            if data.get("bus_path"):
                self.send_error(400, "Client-supplied bus_path is not accepted")
                return

            # Append to local bus. The Bearer token (checked above in
            # _check_post_auth) authenticates the remote HTTP client. The
            # sender identity in the message body is metadata the authenticated
            # client vouches for; enforcing it against the LOCAL agent registry
            # would couple the bridge to whatever registry/agents_v2.json the
            # receiving machine happens to have, and reject legitimate
            # cross-machine posts from fleet agents not in that local registry
            # (e.g. devin, opencode, apex, sov, kai, echo, soma, nexus,
            # auditor, hermes, human). validate=True still emits a warning log
            # for unknown senders (fleet observability) without rejecting.
            # The S-001 default (enforce=True for local callers) is unchanged.
            bus_path = _resolve_bus_path(None)
            post_message(
                bus_path=bus_path,
                from_id=from_agent,
                to_id=to_agent,
                msg_type=msg_type,
                message=message,
                validate_sender_identity=True,
                enforce_sender_identity=False,
            )
            result = True

            if result:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                self.send_error(500, "Failed to append to bus")

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        """Handle GET requests: health, tail, search."""
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self._json_response(
                {"status": "up", "service": "bus-bridge", "version": "1.1"}
            )

        elif path == "/bus/tail":
            try:
                n = min(int(params.get("n", ["50"])[0]), MAX_TAIL_LINES)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid 'n' parameter")
                return
            if n < 0:
                n = 0
            date = params.get("date", [None])[0]
            self._serve_bus_lines(n=n, date=date)

        elif path == "/bus/search":
            pattern = params.get("q", [None])[0]
            if not pattern:
                self.send_error(400, "Missing required param: q")
                return
            try:
                n = min(int(params.get("n", ["200"])[0]), MAX_TAIL_LINES)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid 'n' parameter")
                return
            if n < 0:
                n = 0
            self._serve_bus_lines(n=n, pattern=pattern)

        else:
            self.send_error(404, "Not found")

    def _json_response(self, data: dict[str, object], status: int = 200) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _serve_bus_lines(
        self, n: int = 50, date: str | None = None, pattern: str | None = None
    ) -> None:
        """Read and filter bus lines, return as JSON."""
        try:
            bus_path = _resolve_bus_path(None)
            if not bus_path.exists():
                self._json_response({"error": "Bus file not found"}, 404)
                return

            with open(bus_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Filter by date prefix if provided
            if date:
                lines = [line for line in lines if line.startswith(date)]

            # Filter by pattern (case-insensitive substring match)
            if pattern:
                pat_lower = pattern.lower()
                lines = [line for line in lines if pat_lower in line.lower()]

            # Return last n lines
            lines = lines[-n:]

            messages = []
            for line in lines:
                line = line.rstrip("\n")
                if not line or line.startswith("timestamp_utc"):
                    continue
                parts = line.split("\t", 4)
                if len(parts) >= 5:
                    messages.append(
                        {
                            "timestamp": parts[0],
                            "from": parts[1],
                            "to": parts[2],
                            "type": parts[3],
                            "message": parts[4],
                        }
                    )

            self._json_response({"count": len(messages), "messages": messages})

        except Exception as e:
            self.send_error(500, str(e))


def get_tailscale_ip():
    """Get the Tailscale IP (100.x.x.x)."""
    import subprocess

    try:
        # Try to get from tailscale status
        result = subprocess.run(
            ["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Fallback: try to find 100.x interface
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
        pass

    return None


def run_server(port=18790, bind_all=False):
    """Run the bridge server."""
    if bind_all:
        host = "0.0.0.0"
    else:
        # Bind to Tailscale interface only for security
        tailscale_ip = get_tailscale_ip()
        if tailscale_ip:
            host = tailscale_ip
            print(f"Binding to Tailscale interface: {host}")
        else:
            host = "127.0.0.1"
            print("Warning: No Tailscale IP found, binding to localhost only")

    server = HTTPServer((host, port), BusBridgeHandler)
    print(f"Bus Bridge Server running on http://{host}:{port}")
    print("Endpoints: POST /bus, GET /health, GET /bus/tail, GET /bus/search")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bus Bridge Server for cross-machine coordination"
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=18790,
        help="Port to listen on (default: 18790)",
    )
    parser.add_argument(
        "--bind-all",
        "-a",
        action="store_true",
        help="Bind to all interfaces (default: Tailscale only)",
    )

    args = parser.parse_args()
    run_server(port=args.port, bind_all=args.bind_all)
