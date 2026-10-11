"""Meshtastic adapter skeleton — mesh text -> envelopes.

Two transports, one parser:

1. Serial line mode: a helper process (meshtastic CLI, python
   ``meshtastic`` lib, or a serial-forwarder) emits one JSON record per
   received text on stdout; this adapter consumes lines.

2. MQTT mode: a tiny stdlib MQTT-subscribe reader consuming
   ``msh/*/2/e/<channel>/+`` JSON service envelopes. Meshtastic's MQTT
   JSON payload carries ``{from, payload, id, sender}``; packet bodies
   are protobuf-encoded in the real protocol — deployments typically
   run a local json-emitting relay (``meshtastic --host ...`` or a
   gateway script), so this adapter consumes the *already-decoded*
   shape: a JSON object with ``text`` + ``sender`` + ``id`` fields.

Packet budget: LongFast ~230 bytes. Multi-part messages arrive as
separate packets — fragments tagged ``part i/n`` are reassembled in
``Reassembler`` before envelope emission.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from collections import OrderedDict
from collections.abc import Iterator

from .envelope import InboundEnvelope

MAX_PACKET = 230  # bytes, LongFast preset practical text budget


def packet_to_envelope(rec: dict) -> InboundEnvelope | None:
    """One decoded mesh record -> envelope; None for non-text packets."""
    text = rec.get("text") or rec.get("payload_text")
    if not isinstance(text, str) or not text.strip():
        return None
    sender = str(rec.get("sender") or rec.get("from") or "mesh-unknown")
    pkt_id = str(rec.get("id") or rec.get("packet_id") or "")
    ts = rec.get("rx_time") or rec.get("timestamp")
    if ts:
        received = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(ts)))
    else:
        received = "1970-01-01T00:00:00Z"
    return InboundEnvelope(
        channel="meshtastic",
        channel_msg_id=f"{sender}:{pkt_id}",
        sender_addr=sender,
        received_at=received,
        body=text.strip(),
        meta={"rssi": rec.get("rssi"), "hops": rec.get("hops_away")},
    )


class Reassembler:
    """Multi-part text reassembly for 'part i/n' tagged fragments."""

    _PART_RE = re.compile(r"^\[(\d+)/(\d+)\]\s*(.*)$", re.DOTALL)

    def __init__(self, ttl_s: int = 300):
        self._buf: OrderedDict[str, dict] = OrderedDict()
        self.ttl = ttl_s

    def feed(self, env: InboundEnvelope) -> InboundEnvelope | None:
        m = self._PART_RE.match(env.body)
        if not m:
            return env
        i, n, chunk = int(m.group(1)), int(m.group(2)), m.group(3)
        key = f"{env.sender_addr}:{env.channel_msg_id.rsplit(':', 1)[0]}"
        now = time.time()
        # expiry sweep
        for k in [k for k, v in self._buf.items() if now - v["ts"] > self.ttl]:
            del self._buf[k]
        slot = self._buf.setdefault(key, {"ts": now, "n": n, "parts": {}})
        slot["parts"][i] = chunk
        slot["ts"] = now
        if len(slot["parts"]) < n:
            return None
        body = "".join(slot["parts"][j] for j in range(1, n + 1))
        del self._buf[key]
        return InboundEnvelope(
            channel=env.channel,
            channel_msg_id=env.channel_msg_id,
            sender_addr=env.sender_addr,
            received_at=env.received_at,
            body=body,
            meta={**env.meta, "multipart": n},
        )


def iter_json_lines(fd) -> Iterator[InboundEnvelope]:
    """Consume JSON-per-line records (serial relay or mqtt2json)."""
    for line in fd:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        env = packet_to_envelope(rec)
        if env is not None:
            yield env


def run_serial_relay(
    cmd: list[str], normalizer, *, reassembler: Reassembler | None = None
) -> None:
    """Launch a relay command and feed every decoded envelope onward."""
    import logging

    log = logging.getLogger("bus-ingress-meshtastic")
    asm = reassembler or Reassembler()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    for env in iter_json_lines(proc.stdout):
        out = asm.feed(env)
        if out is None:
            continue
        result = normalizer.handle(out)
        log.info("mesh %s -> %s", out.channel_msg_id, result.status)
