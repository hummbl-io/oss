"""Telegram bot poller — Bot API getUpdates -> envelopes.

Long-poll mode (no public URL needed): the daemon calls getUpdates and
Telegram holds the request open. Message-id anchor: ``update_id`` is
strictly increasing per bot — used as dedup + offset watermark.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request

from .envelope import InboundEnvelope

log = logging.getLogger("bus-ingress-telegram")

_API = "https://api.telegram.org/bot{token}/getUpdates"


def fetch_updates(token: str, *, offset: int = 0, timeout: int = 30) -> list[dict]:
    url = _API.format(token=token)
    payload = json.dumps(
        {"offset": offset, "timeout": timeout, "allowed_updates": ["message"]}
    ).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout + 15) as r:
        data = json.loads(r.read())
    return data.get("result", []) if data.get("ok") else []


def update_to_envelope(upd: dict) -> InboundEnvelope | None:
    msg = upd.get("message") or {}
    text = (msg.get("text") or "").strip()
    if not text:
        return None  # stickers, photos w/o caption, service messages
    sender = msg.get("from", {})
    # Immutable numeric id preferred; username is editable (OQ-016).
    ident = str(sender.get("id") or sender.get("username") or "unknown")
    date = msg.get("date")
    return InboundEnvelope(
        channel="telegram",
        channel_msg_id=str(upd.get("update_id", "")),
        sender_addr=ident,
        received_at=(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(date))
            if date
            else "1970-01-01T00:00:00Z"
        ),
        body=text,
        meta={
            "chat_id": msg.get("chat", {}).get("id"),
            "username": sender.get("username"),
        },
    )


def run_poller(token: str, normalizer, *, poll_seconds: int = 2) -> None:
    offset = 0
    while True:
        try:
            for upd in fetch_updates(token, offset=offset):
                offset = int(upd["update_id"]) + 1
                env = update_to_envelope(upd)
                if env is not None:
                    result = normalizer.handle(env)
                    log.info("telegram %s -> %s", env.channel_msg_id, result.status)
        except Exception as e:
            log.warning("telegram poll failed: %s", e)
        time.sleep(poll_seconds)
