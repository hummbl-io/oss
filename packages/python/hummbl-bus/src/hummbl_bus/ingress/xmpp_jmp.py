"""JMP.chat adapter — a real phone number over XMPP -> envelopes.

JMP binds a US/CA phone number to a Jabber ID (JID). Inbound SMS/MMS
arrive as XMPP chat messages from ``+<E164>@<gateway>`` (default
``cheogram.com``); voicemail arrives the same way with an OOB media URL.
That makes a plain JID a fully programmable phone identity: no Twilio,
no per-message fees, works over the federated XMPP network.

Requires the optional ``slixmpp`` dependency::

    pip install 'hummbl-bus[xmpp]'

The stanza->envelope conversion is a pure function (``jmp_to_envelope``)
so it is testable without a live XMPP connection or the dependency.

Dedup anchor: stanza ``id`` when present, else a stable hash of
``from|body`` — racing pollers or replayed stanzas collapse to the same
request id downstream.
"""

from __future__ import annotations

import hashlib
import logging
import re

from .envelope import InboundEnvelope

log = logging.getLogger("bus-ingress-jmp")

_PHONE_JID = re.compile(r"^\+?(\d{7,16})@")
_URL_RE = re.compile(r"https?://\S+")


def _now_z() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def jmp_to_envelope(
    from_jid: str,
    body: str,
    stanza_id: str,
    *,
    gateway: str = "cheogram.com",
    channel: str = "jmp",
    oob_urls: list[str] | None = None,
) -> InboundEnvelope | None:
    """Pure conversion: cheogram stanza fields -> InboundEnvelope.

    ``from_jid`` looks like ``+15551234567@cheogram.com`` — the sender's
    real phone number is the localpart, which becomes ``sender_addr``
    (immutable, allowlistable). Non-phone JIDs return None.
    """
    bare = from_jid.split("/", 1)[0]
    match = _PHONE_JID.match(bare)
    domain = bare.split("@", 1)[1] if "@" in bare else ""
    if not match or domain.lower() != gateway.lower():
        return None
    sender = "+" + match.group(1)
    text = (body or "").strip()
    urls = list(oob_urls or [])
    # MMS media often arrives as bare URLs inside the body text.
    for found in _URL_RE.findall(text):
        if found not in urls:
            urls.append(found)
    if not text and not urls:
        return None
    msg_id = (
        stanza_id
        or hashlib.sha1(f"{sender}|{text}".encode("utf-8", "replace")).hexdigest()[:16]
    )
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=msg_id,
        sender_addr=sender,
        received_at=_now_z(),
        body=text,
        meta={"provider": "jmp", "gateway": gateway, "media": urls},
    )


def send_sms(
    client, to_number: str, body: str, *, gateway: str = "cheogram.com"
) -> None:
    """Send an SMS by messaging ``+<to>@<gateway>`` (fanout/replies)."""
    digits = re.sub(r"\D", "", to_number)
    client.send_message(mto=f"+{digits}@{gateway}", mbody=body, mtype="chat")


def run_client(
    jid: str,
    password: str,
    normalizer,
    *,
    gateway: str = "cheogram.com",
    channel: str = "jmp",
    reconnect_seconds: int = 15,
) -> None:
    """Connect the JID and forward inbound phone messages to the bus."""
    try:
        import slixmpp
    except ImportError as e:  # pragma: no cover - env dependent
        raise SystemExit(
            "jmp adapter needs slixmpp: pip install 'hummbl-bus[xmpp]'"
        ) from e

    class _Client(slixmpp.ClientXMPP):
        def __init__(self):
            super().__init__(jid, password)
            self.add_event_handler("session_start", self._start)
            self.add_event_handler("message", self._on_message)
            self.register_plugin("xep_0066")  # OOB URLs (MMS/voicemail media)

        def _start(self, _event):
            self.send_presence()
            log.info("jmp xmpp online as %s (gateway=%s)", jid, gateway)

        def _on_message(self, msg):
            if msg["type"] not in ("chat", "normal"):
                return
            urls = []
            try:
                oob = msg["oob"]
                if oob and oob["url"]:
                    urls.append(str(oob["url"]))
            except Exception:
                pass
            env = jmp_to_envelope(
                str(msg["from"]),
                msg["body"] or "",
                str(msg["id"] or ""),
                gateway=gateway,
                channel=channel,
                oob_urls=urls,
            )
            if env is None:
                return
            result = normalizer.handle(env)
            log.info("jmp %s -> %s", env.channel_msg_id, result.status)

    import time

    while True:
        try:
            client = _Client()
            client.connect()
            client.process(forever=True)
        except Exception as e:  # pragma: no cover - network dependent
            log.warning("jmp xmpp connection failed: %s", e)
        log.info("jmp reconnecting in %ds", reconnect_seconds)
        time.sleep(reconnect_seconds)
