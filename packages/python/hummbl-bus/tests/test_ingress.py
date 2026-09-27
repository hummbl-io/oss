"""Tests for hummbl_bus.ingress — envelope, normalizer, adapters."""

from __future__ import annotations

import email
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from hummbl_bus.ingress import InboundEnvelope, Normalizer, parse_bus_intent
from hummbl_bus.ingress.allowlist import Allowlist
from hummbl_bus.ingress.fanout import (
    Route,
    parse_tsv_line,
    route_row,
)
from hummbl_bus.ingress.gv_parse import parse_gv_forward
from hummbl_bus.ingress.meshtastic import Reassembler, packet_to_envelope
from hummbl_bus.ingress.normalizer import MAX_MESSAGE_CHARS
from hummbl_bus.ingress.signal_cli import line_to_envelope
from hummbl_bus.ingress.webhook import make_handler

# ---------- envelope ----------


def _env(**kw):
    base = {
        "channel": "sms",
        "channel_msg_id": "m1",
        "sender_addr": "+15550001111",
        "received_at": "2026-09-27T00:00:00Z",
        "body": "STATUS hello",
    }
    base.update(kw)
    return InboundEnvelope(**base)


class TestEnvelope:
    def test_request_id_deterministic(self):
        assert _env().request_id == _env().request_id
        assert _env(channel_msg_id="m2").request_id != _env().request_id
        assert _env(channel="signal").request_id != _env().request_id

    def test_validate(self):
        assert _env().validate() == []
        assert "received_at" in _env(received_at="no-z").validate()[0]
        assert _env(body="  ").validate()

    def test_parse_typed(self):
        i = parse_bus_intent("QUESTION operator: eta?")
        assert i.msg_type == "QUESTION" and i.to == "operator"
        assert i.message == "eta?"

    def test_parse_untyped_defaults_status(self):
        i = parse_bus_intent("just a note")
        assert i.msg_type == "STATUS" and i.to == "all"
        assert i.message == "just a note"

    def test_parse_at_to(self):
        i = parse_bus_intent("ALERT @devin: disk full")
        assert i.msg_type == "ALERT" and i.to == "devin"
        i = parse_bus_intent("ALERT @devin disk full")  # no colon needed
        assert i.to == "devin" and i.message == "disk full"

    def test_bare_word_is_not_recipient(self):
        """'STATUS fleet sync green' is a message, not to='fleet'."""
        i = parse_bus_intent("STATUS fleet sync green")
        assert i.to == "all" and i.message == "fleet sync green"

    def test_parse_pin_extracted(self):
        i = parse_bus_intent("VETO pin=s3cret: don't ship")
        assert i.pin == "s3cret" and i.msg_type == "VETO"
        assert "pin=" not in i.message


# ---------- allowlist ----------


def _allow(**kw):
    senders = {
        "+15550001111": {
            "from": "operator",
            "channels": ["sms", "signal"],
            "pin_env": "TEST_PIN",
        },
        "me@x.com": {"from": "operator", "channels": ["email"], "pin_env": "TEST_PIN"},
        "default": {"from": "channel-ingress", "channels": ["*"]},
    }
    return Allowlist(senders, **kw)


class TestAllowlist:
    def test_known_sender_right_channel(self):
        p = _allow().lookup("+15550001111", "sms")
        assert p.bus_from == "operator" and not p.quarantine

    def test_known_sender_wrong_channel_quarantined(self):
        p = _allow().lookup("+15550001111", "email")
        assert p.quarantine and p.bus_from == "email-ingress"

    def test_unknown_sender_quarantine(self):
        # "default" entry's configured name wins over <channel>-ingress
        p = _allow().lookup("+1999", "sms")
        assert p.quarantine and p.bus_from == "channel-ingress"
        # no default configured -> generic per-channel name
        p = Allowlist({}).lookup("+1999", "sms")
        assert p.bus_from == "sms-ingress"

    def test_unknown_sender_drop(self):
        assert _allow(unknown_sender="drop").lookup("+1999", "sms") is None

    def test_pin_match(self, monkeypatch):
        monkeypatch.setenv("TEST_PIN", "s3cret")
        p = _allow().lookup("+15550001111", "sms")
        assert p.pin_matches("s3cret")
        assert not p.pin_matches("wrong")
        assert not p.pin_matches(None)


# ---------- normalizer ----------


class _FakeBridge:
    def __init__(self, ok=True, fail_transient=False, permanent=False):
        self.calls = []
        self.ok = ok
        self.fail_transient = fail_transient
        self.permanent = permanent

    def __call__(self, host, from_agent, to_agent, msg_type, message, **kw):
        self.calls.append((from_agent, to_agent, msg_type, message, kw))
        if self.permanent:
            return {"ok": False, "permanent_error": True, "error": "nope"}
        if self.fail_transient:
            return {"ok": False, "permanent_error": False, "error": "down"}
        return {"ok": self.ok, "duplicate": False}


def _norm(bridge, tmp_path, **kw):
    return Normalizer(_allow(), post_fn=bridge, spool_dir=tmp_path / "spool", **kw)


class TestNormalizer:
    def test_posts_typed_message(self, tmp_path):
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(body="ALERT ops: fire"))
        assert r.status == "posted" and r.msg_type == "ALERT"
        frm, to, typ, msg, kw = b.calls[0]
        assert frm == "operator" and to == "ops" and typ == "ALERT"
        assert "via=sms" in msg and "fire" in msg
        assert kw["request_id"] == _env(body="ALERT ops: fire").request_id

    def test_elevated_downgrades_without_pin(self, tmp_path):
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(body="VETO: stop"))
        assert r.status == "posted" and r.msg_type == "STATUS"
        assert r.requested_type == "VETO"
        assert "attempted_type=VETO" in b.calls[0][3]

    def test_elevated_allowed_with_pin(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_PIN", "s3cret")
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(body="VETO pin=s3cret: stop"))
        assert r.msg_type == "VETO" and r.status == "posted"

    def test_decision_always_downgrades(self, tmp_path):
        """DECISION/DIRECTIVE are privileged — channels can't prove them."""
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(body="DECISION: ship it"))
        assert r.msg_type == "STATUS" and "attempted_type=DECISION" in b.calls[0][3]

    def test_unknown_sender_quarantine_posts(self, tmp_path):
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(sender_addr="+1999"))
        assert r.status == "posted" and b.calls[0][0] == "channel-ingress"

    def test_transient_spools(self, tmp_path):
        b = _FakeBridge(fail_transient=True)
        r = _norm(b, tmp_path).handle(_env())
        assert r.status == "spooled"
        spooled = list((tmp_path / "spool").glob("*.json"))
        assert len(spooled) == 1
        rec = json.loads(spooled[0].read_text())
        assert rec["request_id"] == r.request_id

    def test_permanent_rejects(self, tmp_path):
        b = _FakeBridge(permanent=True)
        r = _norm(b, tmp_path).handle(_env())
        assert r.status == "rejected"

    def test_message_truncated(self, tmp_path):
        b = _FakeBridge()
        _norm(b, tmp_path).handle(_env(body="STATUS " + "x" * 5000))
        assert len(b.calls[0][3]) <= MAX_MESSAGE_CHARS

    def test_invalid_envelope_rejected(self, tmp_path):
        b = _FakeBridge()
        r = _norm(b, tmp_path).handle(_env(body="  "))
        assert r.status == "rejected" and not b.calls


# ---------- webhook ----------


class TestWebhook:
    @pytest.fixture()
    def server(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_HOOK_TOKEN", "tok123")
        b = _FakeBridge()
        norm = _norm(b, tmp_path)
        srv = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(norm, {"sms": "TEST_HOOK_TOKEN"})
        )
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield srv, b
        srv.shutdown()

    def _post(self, port, channel, payload, token="tok123"):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/i/{channel}",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_post_flow(self, server):
        srv, b = server
        code, body = self._post(
            srv.server_port,
            "sms",
            {"id": "abc", "from": "+15550001111", "body": "STATUS hi"},
        )
        assert code == 200 and body["status"] == "posted"
        assert b.calls[0][2] == "STATUS"

    def test_unauthorized(self, server):
        srv, _ = server
        code, _ = self._post(srv.server_port, "sms", {"id": "x"}, token="bad")
        assert code == 401

    def test_unconfigured_channel_closed(self, server):
        srv, _ = server
        code, _ = self._post(srv.server_port, "fax", {"id": "x"})
        assert code == 401


# ---------- adapters ----------


class TestGVParse:
    def test_sms_forward(self):
        msg = email.message_from_string(
            "From: voice-noreply@google.com\r\n"
            "Subject: New text from +1 555-000-1111\r\n\r\n"
            "STATUS build green\nReply to this email to respond"
        )
        out = parse_gv_forward(msg)
        assert out is not None
        num, body = out
        assert num == "+15550001111"
        assert "STATUS build green" in body
        assert "Reply to this email" not in body

    def test_non_gv_passthrough(self):
        msg = email.message_from_string("From: a@b.com\r\nSubject: hi\r\n\r\nhello")
        assert parse_gv_forward(msg) is None


class TestSignalCLI:
    def test_dm_line(self):
        line = json.dumps(
            {
                "envelope": {
                    "source": "+15550001111",
                    "timestamp": 1727440000000,
                    "dataMessage": {"timestamp": 1727440000000, "message": "STATUS ok"},
                }
            }
        )
        env = line_to_envelope(line)
        assert env and env.sender_addr == "+15550001111"
        assert env.body == "STATUS ok"
        assert env.channel_msg_id == "+15550001111:1727440000000"

    def test_non_dm_skipped(self):
        line = json.dumps(
            {
                "envelope": {
                    "source": "+1",
                    "timestamp": 1,
                    "dataMessage": {"timestamp": 1, "message": ""},
                }
            }
        )
        assert line_to_envelope(line) is None


class TestMeshtastic:
    def test_text_packet(self):
        env = packet_to_envelope(
            {
                "text": "STATUS node alive",
                "sender": "!abc123",
                "id": 42,
                "rx_time": 1727440000,
            }
        )
        assert env and env.sender_addr == "!abc123"
        assert env.channel == "meshtastic"

    def test_non_text_skipped(self):
        assert packet_to_envelope({"sender": "!a", "id": 1}) is None

    def test_multipart_reassembly(self):
        asm = Reassembler()
        e1 = _env(
            channel="meshtastic",
            sender_addr="!a",
            channel_msg_id="!a:1",
            body="[1/2] STATUS fir",
        )
        e2 = _env(
            channel="meshtastic",
            sender_addr="!a",
            channel_msg_id="!a:1",
            body="[2/2] st part",
        )
        assert asm.feed(e1) is None
        out = asm.feed(e2)
        assert out and out.body == "STATUS first part"
        assert out.meta["multipart"] == 2


# ---------- fanout ----------


class TestFanout:
    def test_row_parse(self):
        row = parse_tsv_line("2026-09-27T00:00:00Z\tdevin\tall\tSTATUS\thello")
        assert row and row.sender == "devin" and row.message == "hello"

    def test_routes_to_matching_recipient(self):
        sent = []
        r = Route(
            recipients=frozenset({"operator"}),
            channel="signal",
            backend=lambda to, msg: sent.append(msg) or True,
        )
        row = parse_tsv_line("2026-09-27T00:00:00Z\tagy\toperator\tALERT\tdisk full")
        assert route_row(row, [r]) == 1
        assert "[ALERT] agy: disk full" in sent[0]

    def test_skips_ingress_rows(self):
        sent = []
        r = Route(
            recipients=frozenset({"operator"}),
            channel="signal",
            backend=lambda to, msg: sent.append(msg) or True,
        )
        row = parse_tsv_line(
            "2026-09-27T00:00:00Z\toperator\tall\tSTATUS\tvia=sms hello"
        )
        assert route_row(row, [r]) == 0 and not sent

    def test_urgency_filter(self):
        sent = []
        r = Route(
            recipients=frozenset({"operator"}),
            channel="signal",
            urgency=frozenset({"ALERT"}),
            backend=lambda to, msg: sent.append(msg) or True,
        )
        row = parse_tsv_line("2026-09-27T00:00:00Z\tx\toperator\tSTATUS\tnormal")
        assert route_row(row, [r]) == 0

    def test_nonmatching_recipient(self):
        r = Route(
            recipients=frozenset({"operator"}),
            channel="signal",
            backend=lambda t, m: True,
        )
        row = parse_tsv_line("2026-09-27T00:00:00Z\tx\tdevin\tSTATUS\thi")
        assert route_row(row, [r]) == 0


# ---------- provider shims ----------

from hummbl_bus.ingress.discord_poller import msg_to_envelope as dc_msg
from hummbl_bus.ingress.ntfy_sub import event_to_envelope as ntfy_ev
from hummbl_bus.ingress.providers import (
    detect_provider,
    to_envelope,
    verify_slack_signature,
    verify_twilio_signature,
)
from hummbl_bus.ingress.telegram_poller import update_to_envelope as tg_upd


class _Hdr:
    def __init__(self, **kw):
        self._d = {k.lower().replace("_", "-"): v for k, v in kw.items()}

    def get(self, k, default=None):
        return self._d.get(k.lower(), default)


class TestProviders:
    def test_detect_twilio(self):
        raw = b"MessageSid=SM1&From=%2B15550001111&Body=STATUS+hi"
        h = _Hdr(content_type="application/x-www-form-urlencoded")
        assert detect_provider(h, raw) == "twilio"

    def test_detect_telegram(self):
        raw = json.dumps(
            {
                "update_id": 1,
                "message": {
                    "message_id": 5,
                    "from": {"id": 9},
                    "text": "STATUS hi",
                    "chat": {"id": 9},
                    "date": 1727440000,
                },
            }
        ).encode()
        assert detect_provider(_Hdr(content_type="application/json"), raw) == "telegram"

    def test_detect_vapi(self):
        raw = json.dumps(
            {"message": {"type": "tool-calls", "toolWithToolCallList": []}}
        ).encode()
        assert detect_provider(_Hdr(content_type="application/json"), raw) == "vapi"

    def test_twilio_envelope(self):
        raw = b"MessageSid=SM1&From=%2B15550001111&Body=STATUS+hi&To=%2B15550002222"
        env = to_envelope("sms", "twilio", _Hdr(), raw)
        assert env.sender_addr == "+15550001111"
        assert env.channel_msg_id == "SM1" and "STATUS hi" in env.body

    def test_telegram_envelope(self):
        raw = json.dumps(
            {
                "update_id": 42,
                "message": {
                    "message_id": 5,
                    "from": {"id": 9, "username": "reuben"},
                    "text": "STATUS hi",
                    "chat": {"id": 9},
                    "date": 1727440000,
                },
            }
        ).encode()
        env = to_envelope("telegram", "telegram", _Hdr(), raw)
        assert env.sender_addr == "9"  # immutable id, not editable username
        assert env.meta["username"] == "reuben"
        assert env.channel_msg_id == "9:5"
        assert env.received_at.endswith("Z")

    def test_vapi_envelope(self):
        raw = json.dumps(
            {
                "message": {
                    "type": "tool-calls",
                    "toolWithToolCallList": [
                        {
                            "toolCall": {
                                "id": "call1",
                                "function": {
                                    "name": "post_bus",
                                    "arguments": {
                                        "from": "+1555",
                                        "body": "STATUS spoken",
                                    },
                                },
                            }
                        }
                    ],
                }
            }
        ).encode()
        env = to_envelope("voice", "vapi", _Hdr(), raw)
        assert env.body == "STATUS spoken"
        assert env.channel_msg_id == "call1"

    def test_generic_envelope(self):
        raw = json.dumps({"id": "x", "from": "me", "body": "STATUS ok"}).encode()
        env = to_envelope("misc", "generic", _Hdr(), raw)
        assert env.channel_msg_id == "x" and env.body == "STATUS ok"

    def test_twilio_signature(self, monkeypatch):
        token = "authtoken123"
        monkeypatch.setenv("BUS_INGRESS_TWILIO_TOKEN", token)
        url = "https://x.example.com/i/sms"
        # Signature over url + sorted params
        params = {"Body": "STATUS hi", "From": "+15550001111", "MessageSid": "SM1"}
        data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
        import base64
        import hashlib
        import hmac as _h

        sig = base64.b64encode(
            _h.new(token.encode(), data.encode(), hashlib.sha1).digest()
        ).decode()
        import urllib.parse

        raw = "&".join(
            f"{k}={urllib.parse.quote(v, safe='')}" for k, v in params.items()
        ).encode()
        assert verify_twilio_signature(url, raw, sig)
        assert not verify_twilio_signature(url, raw, "badsig")


class TestNewAdapters:
    def test_discord_msg(self):
        env = dc_msg(
            {
                "id": "123",
                "content": "STATUS hi",
                "timestamp": "2026-09-27T00:00:00Z",
                "author": {"id": "u1", "username": "reuben"},
            }
        )
        assert env.channel_msg_id == "123" and env.sender_addr == "u1"
        assert env.meta["username"] == "reuben"
        assert (
            dc_msg({"id": "9", "content": "x", "author": {"id": "me"}}, bot_id="me")
            is None
        )

    def test_telegram_update(self):
        env = tg_upd(
            {
                "update_id": 42,
                "message": {
                    "message_id": 5,
                    "from": {"id": 9},
                    "text": "STATUS hi",
                    "chat": {"id": 9},
                    "date": 1727440000,
                },
            }
        )
        assert env.channel_msg_id == "42" and env.sender_addr == "9"

    def test_ntfy_event(self):
        env = ntfy_ev(
            {
                "event": "message",
                "id": "n1",
                "time": 1727440000,
                "message": "STATUS hi",
                "topic": "bus",
            }
        )
        assert env and env.body == "STATUS hi"
        assert ntfy_ev({"event": "open"}) is None


class TestSlack:
    def test_detect_slack_events(self):
        raw = json.dumps(
            {
                "type": "event_callback",
                "team_id": "T1",
                "event": {
                    "type": "message",
                    "user": "U123",
                    "ts": "1727440000.000100",
                    "text": "STATUS from slack",
                    "client_msg_id": "cm-1",
                    "channel": "C1",
                },
            }
        ).encode()
        assert detect_provider(_Hdr(content_type="application/json"), raw) == "slack"

    def test_detect_slack_by_header(self):
        raw = json.dumps({"type": "url_verification", "challenge": "abc"}).encode()
        h = _Hdr(content_type="application/json", x_slack_signature="v0=x")
        assert detect_provider(h, raw) == "slack"

    def test_slack_message_envelope(self):
        raw = json.dumps(
            {
                "type": "event_callback",
                "team_id": "T1",
                "event": {
                    "type": "message",
                    "user": "U123",
                    "ts": "1727440000.000100",
                    "text": "STATUS from slack",
                    "client_msg_id": "cm-1",
                    "channel": "C1",
                },
            }
        ).encode()
        env = to_envelope("slack", "slack", _Hdr(), raw)
        assert env.sender_addr == "U123"
        assert env.channel_msg_id == "cm-1"
        assert env.body == "STATUS from slack"
        assert env.meta["team"] == "T1"

    def test_slack_ignores_non_message(self):
        for ev in (
            {"type": "message", "subtype": "message_changed", "ts": "1"},
            {"type": "channel_created", "channel": {}},
            {"type": "message", "bot_id": "B1", "ts": "1", "text": "x"},
        ):
            raw = json.dumps({"type": "event_callback", "event": ev}).encode()
            assert to_envelope("slack", "slack", _Hdr(), raw) is None

    def test_slack_signature(self, monkeypatch):
        import hashlib
        import hmac as _h
        import time

        monkeypatch.setenv("BUS_INGRESS_SLACK_SECRET", "slacksecret")
        raw = b'{"type":"event_callback"}'
        ts = str(int(time.time()))
        base = f"v0:{ts}:{raw.decode()}".encode()
        sig = "v0=" + _h.new(b"slacksecret", base, hashlib.sha256).hexdigest()
        assert verify_slack_signature(raw, ts, sig)
        assert not verify_slack_signature(raw, ts, "v0=bad")
        assert not verify_slack_signature(raw, "12345", sig)  # stale replay


class TestWebhookProviderFlow:
    """Webhook-level: slack url_verification + ignored events return
    200 not 400 (providers disable endpoints on repeated errors)."""

    def _serve(self):
        from http.server import ThreadingHTTPServer

        from hummbl_bus.ingress.webhook import make_handler

        srv = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(
                Normalizer(
                    Allowlist(
                        {"senders": {"U1": {"from": "operator", "channels": ["slack"]}}}
                    ),
                    post_fn=lambda *a, **k: {"ok": True},
                ),
                {"slack": "BUS_INGRESS_TOKEN_SLACK"},
            ),
        )
        import threading

        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv

    def _post(self, port, body, headers=None):
        import urllib.error
        import urllib.request

        hdrs = {"Authorization": "Bearer slk", "Content-Type": "application/json"}
        hdrs.update(headers or {})
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/i/slack", data=body.encode(), headers=hdrs
        )
        try:
            resp = urllib.request.urlopen(req)
            return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_url_verification_echo(self, monkeypatch):
        monkeypatch.setenv("BUS_INGRESS_TOKEN_SLACK", "slk")
        srv = self._serve()
        try:
            code, body = self._post(
                srv.server_address[1],
                json.dumps({"type": "url_verification", "challenge": "ch3ck"}),
            )
            assert code == 200 and body["challenge"] == "ch3ck"
        finally:
            srv.shutdown()

    def test_ignored_event_200(self, monkeypatch):
        monkeypatch.setenv("BUS_INGRESS_TOKEN_SLACK", "slk")
        srv = self._serve()
        try:
            code, body = self._post(
                srv.server_address[1],
                json.dumps(
                    {
                        "type": "event_callback",
                        "event": {"type": "message", "subtype": "message_changed"},
                    }
                ),
            )
            assert code == 200 and body["status"] == "ignored"
        finally:
            srv.shutdown()

    def test_slack_message_posts(self, monkeypatch):
        monkeypatch.setenv("BUS_INGRESS_TOKEN_SLACK", "slk")
        srv = self._serve()
        try:
            code, body = self._post(
                srv.server_address[1],
                json.dumps(
                    {
                        "type": "event_callback",
                        "event": {
                            "type": "message",
                            "user": "U1",
                            "ts": "1727440000.1",
                            "text": "STATUS ok",
                            "channel": "C1",
                        },
                    }
                ),
            )
            assert code == 200 and body["status"] == "posted"
        finally:
            srv.shutdown()


# ---------- android gateways + jmp ----------


class TestLibreSMS:
    def test_detect_params(self):
        from hummbl_bus.ingress.providers import detect_provider_params

        p = {"from": "+15551112222", "message": "hi", "type": "SMS", "id": "x1"}
        assert detect_provider_params(p) == "libresms"
        assert detect_provider_params({"from": "+1", "type": "SMS"}) == "libresms"
        assert detect_provider_params({"foo": "bar"}) == "generic"

    def test_sms_envelope(self):
        from hummbl_bus.ingress.providers import params_to_envelope

        env = params_to_envelope(
            "android",
            "libresms",
            {
                "id": "abc123",
                "from": "+15551112222",
                "to": "self",
                "message": "STATUS gateway up",
                "type": "SMS",
                "timestamp": "2026-09-28T10:00:00Z",
            },
        )
        assert env.sender_addr == "+15551112222"
        assert env.channel_msg_id == "abc123"
        assert env.body == "STATUS gateway up"
        assert env.meta["provider"] == "libresms"

    def test_mms_attachment_metadata_only(self):
        from hummbl_bus.ingress.providers import params_to_envelope

        env = params_to_envelope(
            "android",
            "libresms",
            {
                "id": "m1",
                "from": "+15551112222",
                "message": "look",
                "type": "MMS",
                "attachment_count": "1",
                "attachment_0_name": "pic.jpg",
                "attachment_0_type": "image/jpeg",
                "attachment_0_size": "42000",
                "attachment_0_data": "AAAABBBB" * 10000,  # never carried
            },
        )
        assert env.meta["attachments"][0]["name"] == "pic.jpg"
        assert "AAAABBBB" not in json.dumps(env.meta)

    def test_empty_sms_returns_none(self):
        from hummbl_bus.ingress.providers import params_to_envelope

        assert params_to_envelope("android", "libresms", {"type": "SMS"}) is None


class TestSMSGate:
    def _raw(self, event, payload):
        return json.dumps(
            {"deviceId": "dev1", "event": event, "id": "w1", "payload": payload}
        ).encode()

    def test_detect(self):
        assert (
            detect_provider(
                _Hdr(content_type="application/json"),
                self._raw("sms:received", {"sender": "+1", "message": "x"}),
            )
            == "smsgate"
        )

    def test_sms_received(self):
        env = to_envelope(
            "android",
            "smsgate",
            _Hdr(),
            self._raw(
                "sms:received",
                {
                    "messageId": "mid1",
                    "message": "STATUS phone rail live",
                    "sender": "+15551112222",
                    "recipient": "+15553334444",
                    "simNumber": 1,
                    "receivedAt": "2026-09-28T10:00:00.000Z",
                },
            ),
        )
        assert env.sender_addr == "+15551112222"
        assert env.channel_msg_id == "mid1"
        assert env.body == "STATUS phone rail live"
        assert env.meta["device"] == "dev1"

    def test_batch_returns_list(self):
        envs = to_envelope(
            "android",
            "smsgate",
            _Hdr(),
            self._raw(
                "sms:batch:received",
                {
                    "messages": [
                        {"messageId": "a", "message": "one", "sender": "+1555"},
                        {"messageId": "b", "message": "two", "sender": "+1555"},
                    ]
                },
            ),
        )
        assert isinstance(envs, list) and len(envs) == 2
        assert envs[0].body == "one" and envs[1].body == "two"

    def test_mms_downloaded(self):
        env = to_envelope(
            "android",
            "smsgate",
            _Hdr(),
            self._raw(
                "mms:downloaded",
                {
                    "messageId": "mm1",
                    "subject": "pic",
                    "body": "see attached",
                    "sender": "+15551112222",
                    "attachments": [{"name": "a.jpg", "contentType": "image/jpeg"}],
                },
            ),
        )
        assert "pic" in env.body and "see attached" in env.body
        assert env.meta["attachments"][0]["type"] == "image/jpeg"

    def test_lifecycle_events_ignored(self):
        for ev, payload in (
            ("sms:sent", {"messageId": "x", "sender": "+1"}),
            ("sms:delivered", {"messageId": "x"}),
            ("system:ping", {"health": {}}),
            ("app:started", {"simCards": []}),
            ("mms:received", {"messageId": "x", "sender": "+1"}),
        ):
            assert (
                to_envelope("android", "smsgate", _Hdr(), self._raw(ev, payload))
                is None
            )


class TestJMP:
    def test_stanza_to_envelope(self):
        from hummbl_bus.ingress.xmpp_jmp import jmp_to_envelope

        env = jmp_to_envelope(
            "+15551112222@cheogram.com",
            "STATUS jmp rail",
            "stz-42",
        )
        assert env.sender_addr == "+15551112222"
        assert env.channel_msg_id == "stz-42"
        assert env.body == "STATUS jmp rail"
        assert env.channel == "jmp"

    def test_non_phone_jid_ignored(self):
        from hummbl_bus.ingress.xmpp_jmp import jmp_to_envelope

        assert jmp_to_envelope("alice@example.org", "hi", "s1") is None
        assert jmp_to_envelope("room@conference.cheogram.com", "hi", "s2") is None

    def test_wrong_gateway_ignored(self):
        from hummbl_bus.ingress.xmpp_jmp import jmp_to_envelope

        assert (
            jmp_to_envelope("+1555@evil.example", "hi", "s3", gateway="cheogram.com")
            is None
        )

    def test_media_urls_collected(self):
        from hummbl_bus.ingress.xmpp_jmp import jmp_to_envelope

        env = jmp_to_envelope(
            "+15551112222@cheogram.com",
            "pic https://dl.cheogram.com/abc.jpg",
            "",
            oob_urls=["https://dl.cheogram.com/oob.m4a"],
        )
        assert len(env.meta["media"]) == 2
        assert env.channel_msg_id  # hash fallback for empty stanza id

    def test_empty_message_none(self):
        from hummbl_bus.ingress.xmpp_jmp import jmp_to_envelope

        assert jmp_to_envelope("+1555@cheogram.com", "", "s9") is None


class TestWebhookGetAndParams:
    """GET webhooks (LibreSMS) + ?token=/?secret= auth + smsgate batch."""

    def _serve(self):
        norm = Normalizer(
            Allowlist(
                {
                    "senders": {
                        "+15551112222": {
                            "from": "operator",
                            "channels": ["android", "jmp"],
                        }
                    }
                }
            ),
            post_fn=lambda *a, **k: {"ok": True},
        )
        srv = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(norm, {"android": "AND_TOKEN"})
        )
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv

    def _get(self, port, path):
        import urllib.error

        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_libresms_get_posts(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            code, body = self._get(
                srv.server_port,
                "/i/android?id=g1&from=%2B15551112222&message=STATUS%20get"
                "&type=SMS&secret=andtok",
            )
            assert code == 200 and body["status"] == "posted"
            assert body["results"][0]["request_id"]
        finally:
            srv.shutdown()

    def test_get_bad_secret_401(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            code, _ = self._get(
                srv.server_port,
                "/i/android?id=g1&from=%2B1555&message=x&type=SMS&secret=wrong",
            )
            assert code == 401
        finally:
            srv.shutdown()

    def test_get_no_token_401(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            code, _ = self._get(
                srv.server_port, "/i/android?id=g1&from=%2B1555&message=x&type=SMS"
            )
            assert code == 401
        finally:
            srv.shutdown()

    def test_post_token_param_auth(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{srv.server_port}/i/android?token=andtok",
                data=json.dumps(
                    {"id": "p1", "from": "+15551112222", "body": "STATUS hi"}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req) as r:
                    body = json.loads(r.read())
                    assert body["status"] == "posted"
            except urllib.error.HTTPError as e:
                raise AssertionError(e.read())
        finally:
            srv.shutdown()

    def test_smsgate_batch_posts_both(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{srv.server_port}/i/android",
                data=json.dumps(
                    {
                        "deviceId": "d1",
                        "event": "sms:batch:received",
                        "payload": {
                            "messages": [
                                {
                                    "messageId": "b1",
                                    "message": "STATUS one",
                                    "sender": "+15551112222",
                                },
                                {
                                    "messageId": "b2",
                                    "message": "STATUS two",
                                    "sender": "+15551112222",
                                },
                            ]
                        },
                    }
                ).encode(),
                headers={
                    "Authorization": "Bearer andtok",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req) as r:
                body = json.loads(r.read())
            assert body["status"] == "batch" and body["count"] == 2
            assert all(i["status"] == "posted" for i in body["results"])
        finally:
            srv.shutdown()

    def test_smsgate_ping_ignored_200(self, monkeypatch):
        monkeypatch.setenv("AND_TOKEN", "andtok")
        srv = self._serve()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{srv.server_port}/i/android",
                data=json.dumps(
                    {"deviceId": "d1", "event": "system:ping", "payload": {}}
                ).encode(),
                headers={
                    "Authorization": "Bearer andtok",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req) as r:
                body = json.loads(r.read())
            assert body["status"] == "ignored"
        finally:
            srv.shutdown()
