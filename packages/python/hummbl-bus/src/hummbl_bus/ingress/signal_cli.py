"""signal-cli receive adapter.

Runs ``signal-cli -o json receive`` (or consumes its JSON-RPC daemon
stream) and turns incoming DMs into envelopes. The adapter parses the
well-known receive output shapes; it does not send.

Message-id anchor: signal-cli messages lack a transport id, so we
compose ``source + timestamp_ms`` — stable for dedup of redeliveries.
"""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Iterator

from .envelope import InboundEnvelope


def _utc_ms(ms: float) -> str:
    import datetime as dt

    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def line_to_envelope(line: str) -> InboundEnvelope | None:
    """Parse one signal-cli JSON receive line; None if not a text DM."""
    try:
        rec = json.loads(line)
    except json.JSONDecodeError:
        return None

    env = rec.get("envelope", rec)  # -o json wraps in {"envelope": ...}
    data = env.get("dataMessage")
    if not isinstance(data, dict):
        return None
    body = (data.get("message") or "").strip()
    if not body:
        return None  # reactions, receipts, typing, attachments-only
    source = env.get("source") or env.get("sourceNumber") or "unknown"
    ts = data.get("timestamp") or env.get("timestamp") or 0
    return InboundEnvelope(
        channel="signal",
        channel_msg_id=f"{source}:{ts}",
        sender_addr=str(source),
        received_at=_utc_ms(ts) if ts else "1970-01-01T00:00:00Z",
        body=body,
        meta={"group": data.get("groupInfo", {}).get("groupId") is not None},
    )


def receive_once(
    account: str, config_dir: str | None = None, timeout: int = 5
) -> Iterator[InboundEnvelope]:
    """One-shot: drain pending messages. Used in polling loops."""
    cmd = ["signal-cli"]
    if config_dir:
        cmd += ["--config", config_dir]
    cmd += ["-a", account, "-o", "json", "receive", "-t", str(timeout)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    for line in proc.stdout.splitlines():
        env = line_to_envelope(line)
        if env is not None:
            yield env


def run_daemon(
    account: str, normalizer, *, config_dir: str | None = None, poll_seconds: int = 10
) -> None:
    """Polling loop; signal-cli exits between polls (simple + robust)."""
    import logging

    log = logging.getLogger("bus-ingress-signal")
    while True:
        try:
            for env in receive_once(account, config_dir, timeout=5):
                result = normalizer.handle(env)
                log.info("signal %s -> %s", env.channel_msg_id, result.status)
        except Exception as e:
            log.warning("signal receive failed: %s", e)
        time.sleep(poll_seconds)
