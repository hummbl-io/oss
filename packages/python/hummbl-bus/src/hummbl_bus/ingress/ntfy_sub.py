"""ntfy.sh subscriber — SSE stream -> envelopes.

Subscribes to an ntfy topic's JSON stream (self-hosted or ntfy.sh).
Anyone who can POST to the topic can reach the bus — share the topic
URL as the "bus button" endpoint for arbitrary tools.

Message-id anchor: ntfy message ``id`` + ``time`` composite.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from collections.abc import Iterator

from .envelope import InboundEnvelope

log = logging.getLogger("bus-ingress-ntfy")


def stream_events(
    base_url: str, topic: str, *, token: str | None = None
) -> Iterator[dict]:
    """Yield decoded JSON event lines from the ntfy SSE endpoint."""
    url = f"{base_url.rstrip('/')}/{topic}/json"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=None) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def event_to_envelope(ev: dict) -> InboundEnvelope | None:
    if ev.get("event") != "message":
        return None
    text = (ev.get("message") or "").strip()
    if not text:
        return None
    ts = ev.get("time")
    return InboundEnvelope(
        channel="ntfy",
        channel_msg_id=f"{ev.get('id', '')}:{ev.get('time', '')}",
        sender_addr=str(
            ev.get("extras", {}).get("from") or ev.get("title") or "ntfy-poster"
        ),
        received_at=(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts)))
            if ts
            else "1970-01-01T00:00:00Z"
        ),
        body=text,
        meta={"topic": ev.get("topic")},
    )


def run_subscriber(
    base_url: str,
    topic: str,
    normalizer,
    *,
    token_env: str | None = None,
    reconnect_seconds: int = 10,
) -> None:
    """Resilient SSE loop — reconnects on stream drop."""
    import os

    token = os.environ.get(token_env, "") if token_env else None
    while True:
        try:
            for ev in stream_events(base_url, topic, token=token):
                env = event_to_envelope(ev)
                if env is not None:
                    result = normalizer.handle(env)
                    log.info("ntfy %s -> %s", env.channel_msg_id, result.status)
        except Exception as e:
            log.warning("ntfy stream dropped: %s", e)
        time.sleep(reconnect_seconds)
