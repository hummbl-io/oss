"""Generic inbound webhook receiver (stdlib http.server).

One endpoint per channel: POST /i/<channel> with a JSON body:

    {"id": "<provider msg id>", "from": "<sender>", "body": "<text>",
     "ts": "<UTC ISO>"}          # ts optional; server stamps if absent

Auth: per-channel bearer token -- ``Authorization: Bearer <token>``.
Header-less senders (Android SMS gateways, IFTTT-style GET webhooks)
authenticate via ``?token=`` or ``?secret=`` query params instead.
Tokens come from env var names in the channel token map, never files.

Any provider that can POST lands here: Twilio SMS (form-encoded +
X-Twilio-Signature verified when BUS_INGRESS_TWILIO_TOKEN is set),
Telegram bot webhooks, Vapi tool calls, SMSGate (android-sms-gateway)
events, iOS Shortcuts, Tasker, IFTTT, n8n, GitHub Actions, CI relays --
one build, N options. GET senders: LibreSMS query-param webhooks.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .normalizer import Normalizer
from .providers import (
    detect_provider,
    detect_provider_params,
    params_to_envelope,
    to_envelope,
    verify_slack_signature,
    verify_twilio_signature,
)

log = logging.getLogger("bus-ingress-webhook")


def _now_z() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_handler(normalizer: Normalizer, channel_tokens: dict[str, str]):
    """channel_tokens: channel name -> env var holding its bearer token."""

    class _Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, body: dict) -> None:
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _authorized(self, channel: str, params: dict[str, str]) -> bool:
            env_name = channel_tokens.get(channel)
            if env_name is None:
                return False  # channel not configured at all
            expected = os.environ.get(env_name, "")
            if not expected:
                return False  # token env unset -> fail closed
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer ") and hmac.compare_digest(auth[7:], expected):
                return True
            # Header-less senders: token rides a query param.
            given = params.get("token") or params.get("secret") or ""
            return bool(given) and hmac.compare_digest(given, expected)

        def _handle_envs(self, channel: str, envs) -> None:
            """Run normalizer over 1..N envelopes and answer."""
            if envs is None:
                self._json(400, {"detail": "unparseable payload"})
                return
            if not isinstance(envs, list):
                envs = [envs]
            results = []
            for env in envs:
                r = normalizer.handle(env)
                results.append(
                    {
                        "status": r.status,
                        "request_id": r.request_id,
                        "type": r.msg_type,
                        "detail": r.detail,
                    }
                )
            overall = results[0]["status"] if len(results) == 1 else "batch"
            ok = all(r["status"] in ("posted", "spooled", "duplicate") for r in results)
            self._json(
                200 if ok else 422,
                {"status": overall, "count": len(results), "results": results},
            )

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json(200, {"status": "healthy"})
                return
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) != 2 or parts[0] != "i":
                self._json(404, {"detail": "not found"})
                return
            channel = parts[1]
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            if not self._authorized(channel, params):
                self._json(401, {"detail": "unauthorized"})
                return
            provider = detect_provider_params(params)
            envs = params_to_envelope(channel, provider, params)
            if envs is None:
                if provider != "generic" and params:
                    self._json(200, {"status": "ignored"})
                else:
                    self._json(400, {"detail": "unparseable payload"})
                return
            self._handle_envs(channel, envs)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) != 2 or parts[0] != "i":
                self._json(404, {"detail": "use POST /i/<channel>"})
                return
            channel = parts[1]
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

            if not self._authorized(channel, params):
                self._json(401, {"detail": "unauthorized"})
                return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""

            provider = detect_provider(self.headers, raw)
            if provider == "twilio" and os.environ.get("BUS_INGRESS_TWILIO_TOKEN"):
                sig = self.headers.get("X-Twilio-Signature", "")
                # Behind TLS termination Twilio signs the https URL it posted.
                proto = self.headers.get("X-Forwarded-Proto", "http")
                proto = proto.split(",")[0].strip() or "http"
                url = f"{proto}://{self.headers.get('Host', '')}{self.path}"
                if not verify_twilio_signature(url, raw, sig):
                    self._json(401, {"detail": "bad twilio signature"})
                    return
            if (
                provider == "slack"
                and os.environ.get("BUS_INGRESS_SLACK_SECRET")
                and not verify_slack_signature(
                    raw,
                    self.headers.get("X-Slack-Request-Timestamp", ""),
                    self.headers.get("X-Slack-Signature", ""),
                )
            ):
                self._json(401, {"detail": "bad slack signature"})
                return

            # Slack app handshake: answer the challenge, nothing to post.
            if provider == "slack":
                try:
                    probe = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    probe = {}
                if probe.get("type") == "url_verification":
                    self._json(200, {"challenge": probe.get("challenge", "")})
                    return

            envs = to_envelope(channel, provider, self.headers, raw)
            if envs is None:
                # Parsed provider event we don't post (message edits,
                # call-end reports, bot echoes, smsgate lifecycle events)
                # -> 200 so the provider doesn't retry/disable the
                # endpoint. True garbage -> 400.
                if provider != "generic" and _looks_structured(raw):
                    self._json(200, {"status": "ignored"})
                else:
                    self._json(400, {"detail": "unparseable payload"})
                return
            self._handle_envs(channel, envs)

        def log_message(self, fmt, *args) -> None:  # quiet -> logging
            log.info("%s %s", self.address_string(), fmt % args)

    return _Handler


def _looks_structured(raw: bytes) -> bool:
    try:
        json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return False
    return True


def serve(
    normalizer: Normalizer,
    channel_tokens: dict[str, str],
    host: str = "127.0.0.1",
    port: int = 18796,
) -> None:
    handler = make_handler(normalizer, channel_tokens)
    srv = ThreadingHTTPServer((host, port), handler)
    log.info("bus-ingress webhook on %s:%d", host, port)
    srv.serve_forever()
