"""Provider payload shims — native webhook shapes -> InboundEnvelope.

Providers don't send our generic ``{id,from,body,ts}`` shape. These
detectors let each vendor's webhook land on ``/i/<channel>`` directly:

- **Twilio SMS** — ``application/x-www-form-urlencoded`` with
  ``MessageSid``/``From``/``Body`` + ``X-Twilio-Signature`` validation
- **Telegram** — ``update.message`` JSON from Bot API webhook mode
- **Slack** — Events API ``event_callback`` payloads (plus the
  ``url_verification`` handshake the endpoint must answer), with
  ``X-Slack-Signature`` v0 validation
- **Vapi** — server ``tool-calls`` envelope (same shape as the
  omnichannel escalation parser)
- **SMSGate (android-sms-gateway)** — POST JSON ``{event, payload}``
  events; ``sms:received``/``mms:downloaded`` post, ``*:batch:*`` events
  yield multiple envelopes, lifecycle events are ignored
- **LibreSMS** — GET query-string webhooks ``?id=&from=&message=&type=``
  (header-less device); auth rides the ``?secret=`` param
- **Generic JSON** — the native contract (fallback)

Signature checks are opt-in per deployment: when
``BUS_INGRESS_TWILIO_TOKEN`` / ``BUS_INGRESS_SLACK_SECRET`` is set the
matching signature header is verified; when unset, bearer-token auth
remains the gate.

Sender binding: ``sender_addr`` prefers immutable provider IDs
(telegram ``from.id``, slack ``event.user``) over display names —
usernames are user-editable and must never carry allowlist trust.
Display names ride in ``meta`` for humans.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from urllib.parse import parse_qs

from .envelope import InboundEnvelope


def detect_provider(headers, raw: bytes) -> str:
    ctype = (headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if "twilio" in (headers.get("User-Agent") or "").lower() or headers.get(
        "X-Twilio-Signature"
    ):
        return "twilio"
    if ctype == "application/x-www-form-urlencoded" and b"MessageSid=" in raw:
        return "twilio"
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return "generic"
    if isinstance(data, dict):
        if data.get("type") in ("event_callback", "url_verification") or headers.get(
            "X-Slack-Signature"
        ):
            return "slack"
        if "message" in data and isinstance(data["message"], dict):
            if data["message"].get("type") == "tool-calls":
                return "vapi"
            if "from" in data["message"] and "text" in data["message"]:
                return "telegram"
        if "update_id" in data and "message" in data:
            return "telegram"
        if data.get("event") and isinstance(data.get("payload"), dict):
            return "smsgate"
    return "generic"


def detect_provider_params(params: dict[str, str]) -> str:
    """Detect provider from a header-less request (GET query params)."""
    if params.get("from") and params.get("type", "").upper() in ("SMS", "MMS"):
        return "libresms"
    return "generic"


def params_to_envelope(
    channel: str, provider: str, params: dict[str, str]
) -> InboundEnvelope | None:
    """Translate a query-param payload into an InboundEnvelope."""
    if provider == "libresms":
        return _libresms(params, channel)
    if not params.get("body") and not params.get("message"):
        return None
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=str(params.get("id", "")),
        sender_addr=str(params.get("from", "")),
        received_at=str(params.get("timestamp") or _now_z()),
        body=str(params.get("body") or params.get("message") or ""),
        meta={"provider": "generic-params"},
    )


def _libresms(params: dict[str, str], channel: str) -> InboundEnvelope | None:
    body = params.get("message") or ""
    if not body and params.get("type", "").upper() != "MMS":
        return None
    # Attachment *metadata* only — base64 blobs stay off the bus.
    attachments = [
        {
            "name": params.get(f"attachment_{i}_name"),
            "type": params.get(f"attachment_{i}_type"),
            "size": params.get(f"attachment_{i}_size"),
        }
        for i in range(int(params.get("attachment_count") or 0))
    ]
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=str(params.get("id", "")),
        sender_addr=str(params.get("from", "")),
        received_at=str(params.get("timestamp") or _now_z()),
        body=body or f"[MMS: {len(attachments)} attachment(s)]",
        meta={
            "provider": "libresms",
            "kind": params.get("type"),
            "to": params.get("to"),
            "attachments": attachments,
        },
    )


def to_envelope(
    channel: str, provider: str, headers, raw: bytes, *, default_sender: str = ""
) -> InboundEnvelope | list[InboundEnvelope] | None:
    """Translate a provider-native request into envelope(s).

    Batch events (smsgate ``*:batch:*``) return a list; non-postable
    provider events return None.
    """
    if provider == "twilio":
        return _twilio(headers, raw, channel)
    if provider == "telegram":
        return _telegram(raw, channel)
    if provider == "slack":
        return _slack(raw, channel)
    if provider == "vapi":
        return _vapi(raw, channel)
    if provider == "smsgate":
        return _smsgate(raw, channel)
    return _generic(raw, channel, default_sender)


_SMSGATE_POSTABLE = frozenset(
    {
        "sms:received",
        "sms:batch:received",
        "sms:data-received",
        "sms:batch:data-received",
        "mms:downloaded",
        "mms:batch:downloaded",
    }
)


def _smsgate(
    raw: bytes, channel: str
) -> InboundEnvelope | list[InboundEnvelope] | None:
    """android-sms-gateway (capcom6) events -> envelopes.

    ``mms:received`` is notice-only (body arrives on mms:downloaded);
    sms:sent/delivered/failed, system:ping, app:started are lifecycle
    events and get ignored.
    """
    data = json.loads(raw)
    event = data.get("event", "")
    if event not in _SMSGATE_POSTABLE:
        return None
    payload = data.get("payload") or {}
    if ":batch:" in event:
        envs = [
            _smsgate_item(item, channel, event=event, device=data.get("deviceId"))
            for item in payload.get("messages") or []
        ]
        return [e for e in envs if e is not None] or None
    return _smsgate_item(payload, channel, event=event, device=data.get("deviceId"))


def _smsgate_item(
    item: dict, channel: str, *, event: str, device: str | None
) -> InboundEnvelope | None:
    if "data-received" in event:
        blob = item.get("data") or ""
        try:
            body = base64.b64decode(blob).decode("utf-8")
        except Exception:
            body = f"[data SMS: {len(blob)} b64 chars]"
    elif event.startswith("mms:"):
        parts = [p for p in (item.get("subject"), item.get("body")) if p]
        body = "\n".join(parts) or "[MMS]"
    else:
        body = item.get("message") or ""
    if not body:
        return None
    attachments = [
        {"name": a.get("name"), "type": a.get("contentType"), "size": a.get("size")}
        for a in item.get("attachments") or []
    ]
    ts = item.get("receivedAt") or ""
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=str(item.get("messageId") or item.get("transactionId") or ""),
        sender_addr=str(item.get("sender") or "unknown"),
        received_at=(ts[:19] + "Z") if ts else _now_z(),
        body=body,
        meta={
            "provider": "smsgate",
            "event": event,
            "device": device,
            "recipient": item.get("recipient"),
            "sim": item.get("simNumber"),
            "attachments": attachments,
        },
    )


def _twilio(headers, raw: bytes, channel: str) -> InboundEnvelope | None:
    form = {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace")).items()}
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=form.get("MessageSid", ""),
        sender_addr=form.get("From", ""),
        received_at=_now_z(),
        body=form.get("Body", ""),
        meta={"to": form.get("To"), "provider": "twilio"},
    )


def _telegram(raw: bytes, channel: str) -> InboundEnvelope | None:
    data = json.loads(raw)
    msg = data.get("message") or {}
    text = msg.get("text") or ""
    sender = msg.get("from", {})
    # Prefer immutable numeric id; username is user-editable (OQ-016).
    ident = str(sender.get("id") or sender.get("username") or "unknown")
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=f"{msg.get('chat', {}).get('id', '')}:{msg.get('message_id', '')}",
        sender_addr=ident,
        received_at=_z(msg.get("date")) if msg.get("date") else _now_z(),
        body=text,
        meta={
            "provider": "telegram",
            "chat_id": msg.get("chat", {}).get("id"),
            "username": sender.get("username"),
        },
    )


def _slack(raw: bytes, channel: str) -> InboundEnvelope | None:
    data = json.loads(raw)
    if data.get("type") == "url_verification":
        return None  # handshake — caller answers it, not a bus message
    ev = data.get("event") or {}
    if ev.get("type") != "message" or ev.get("subtype"):
        return None  # edits, joins, bot posts — not ingress traffic
    if ev.get("bot_id"):
        return None
    text = (ev.get("text") or "").strip()
    if not text:
        return None
    ts = ev.get("ts") or ""
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=ev.get("client_msg_id") or f"{ev.get('channel', '')}:{ts}",
        sender_addr=str(ev.get("user") or "slack-user"),
        received_at=_z(ts.split(".")[0]) if ts else _now_z(),
        body=text,
        meta={
            "provider": "slack",
            "slack_channel": ev.get("channel"),
            "team": data.get("team_id"),
        },
    )


def _vapi(raw: bytes, channel: str) -> InboundEnvelope | None:
    data = json.loads(raw)
    if (
        data.get("type") == "tool-calls"
        or data.get("message", {}).get("type") == "tool-calls"
    ):
        msg = data.get("message", data)
        for item in msg.get("toolWithToolCallList", []):
            fn = item.get("toolCall", {}).get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"body": args}
            if args:
                body = args.get("body") or args.get("message") or json.dumps(args)
                return InboundEnvelope(
                    channel=channel,
                    channel_msg_id=item.get("toolCall", {}).get("id", "")
                    or msg.get("id", "vapi"),
                    sender_addr=str(
                        args.get("from") or args.get("caller") or "voice-caller"
                    ),
                    received_at=_now_z(),
                    body=str(body),
                    meta={"provider": "vapi", "function": fn.get("name")},
                )
    return None


def _generic(raw: bytes, channel: str, default_sender: str) -> InboundEnvelope | None:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=str(data.get("id", "")),
        sender_addr=str(data.get("from", default_sender)),
        received_at=str(data.get("ts") or _now_z()),
        body=str(data.get("body", "")),
        meta={"provider": "generic"},
    )


def verify_twilio_signature(url: str, raw: bytes, signature_b64: str) -> bool:
    """Validate X-Twilio-Signature per Twilio docs.

    Needs ``BUS_INGRESS_TWILIO_TOKEN``; when unset, verification is not
    performed (the caller should keep bearer-token auth enabled).
    """
    token = os.environ.get("BUS_INGRESS_TWILIO_TOKEN", "")
    if not token or not signature_b64:
        return False
    params = {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace")).items()}
    data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    expected = base64.b64encode(
        hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()
    ).decode()
    return hmac.compare_digest(expected, signature_b64)


def verify_slack_signature(
    raw: bytes, timestamp: str, signature: str, *, max_age_seconds: int = 300
) -> bool:
    """Validate X-Slack-Signature (v0 HMAC-SHA256) + freshness window.

    Needs ``BUS_INGRESS_SLACK_SECRET``; the request timestamp guard
    rejects replays older than ``max_age_seconds``.
    """
    secret = os.environ.get("BUS_INGRESS_SLACK_SECRET", "")
    if not secret or not timestamp or not signature.startswith("v0="):
        return False
    try:
        import time

        if abs(time.time() - int(timestamp)) > max_age_seconds:
            return False
    except ValueError:
        return False
    base = f"v0:{timestamp}:{raw.decode('utf-8', 'replace')}".encode()
    expected = "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _now_z() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _z(epoch) -> str:
    from datetime import UTC, datetime

    return datetime.fromtimestamp(int(epoch), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
