"""IMAP poller adapter — email -> envelopes.

Polls a mailbox (e.g. a dedicated bus mailbox behind a local
IMAP/SMTP bridge such as Proton Mail Bridge) for UNSEEN mail and
emits one envelope per message.

Body contract: the Subject line is parsed as bus intent first
(`TYPE [to] ...`); if it doesn't parse to a canonical type, the
plain-text body is used instead. Message-ID is the dedup anchor,
falling back to the IMAP UID when missing.

Google Voice forwards (SMS->email, voicemail->email) are handled by
``gv_parse`` which rewrites sender/body before envelope construction.
"""

from __future__ import annotations

import email
import email.utils
import imaplib
import logging
from dataclasses import dataclass
from email.message import Message

from .envelope import InboundEnvelope
from .gv_parse import parse_gv_forward

log = logging.getLogger("bus-ingress-email")

_U32 = "utf-8"


@dataclass(slots=True)
class IMAPConfig:
    host: str = "127.0.0.1"
    port: int = 1143  # Proton Mail Bridge default IMAP port
    user: str = ""
    password_env: str = "BUS_INGRESS_IMAP_PASSWORD"
    mailbox: str = "INBOX"
    starttls: bool = False  # Bridge is plaintext-localhost by default
    mark_seen: bool = True
    poll_seconds: int = 30


def _first_text(msg: Message) -> str:
    """First text/plain part, else stripped text/html, else empty."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(
                        part.get_content_charset() or _U32, errors="replace"
                    )
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    import re

                    text = payload.decode(
                        part.get_content_charset() or _U32, errors="replace"
                    )
                    return re.sub(r"<[^>]+>", " ", text)
        return ""
    payload = msg.get_payload(decode=True)
    if payload is None:
        return str(msg.get_payload() or "")
    return payload.decode(msg.get_content_charset() or _U32, errors="replace")


def msg_to_envelope(
    raw: bytes, *, channel: str = "email", fallback_id: str = ""
) -> InboundEnvelope:
    msg = email.message_from_bytes(raw)
    msg_id = (msg.get("Message-ID") or fallback_id or "").strip()
    sender = email.utils.parseaddr(msg.get("From", ""))[1].strip()
    subject = str(msg.get("Subject", "")).strip()
    body = _first_text(msg).strip()
    date = email.utils.parsedate_to_datetime(msg.get("Date"))
    received = (
        date.astimezone().strftime("%Y-%m-%dT%H:%M:%SZ")
        if date
        else "1970-01-01T00:00:00Z"
    )

    gv = parse_gv_forward(msg)
    if gv is not None:
        sender, body = gv
        channel = "gv-" + channel  # keep provenance distinct

    # Subject carries the intent if it looks typed; body otherwise.
    intent_src = subject if subject else body
    return InboundEnvelope(
        channel=channel,
        channel_msg_id=msg_id,
        sender_addr=sender,
        received_at=received,
        body=intent_src + ("\n" + body if body and body != intent_src else ""),
        meta={"subject": subject, "message_id": msg_id},
    )


def poll_once(conn: imaplib.IMAP4, cfg: IMAPConfig) -> list[InboundEnvelope]:
    conn.select(cfg.mailbox)
    _, data = conn.search(None, "UNSEEN")
    out: list[InboundEnvelope] = []
    for num in (data[0] or b"").split():
        _, fetched = conn.fetch(num, "(RFC822)")
        raw = next((p[1] for p in fetched if isinstance(p, tuple) and p[1]), b"")
        if raw:
            env = msg_to_envelope(raw, fallback_id=f"uid:{num.decode()}")
            out.append(env)
        if cfg.mark_seen:
            conn.store(num, "+FLAGS", "\\Seen")
    return out


def run_poller(cfg: IMAPConfig, normalizer, *, password: str) -> None:
    """Blocking poll loop; passwords arrive from the caller's secret store."""
    import time

    while True:
        try:
            cls = imaplib.IMAP4 if not cfg.starttls else _starttls_client()
            conn = cls(cfg.host, cfg.port)
            conn.login(cfg.user, password)
            try:
                for env in poll_once(conn, cfg):
                    result = normalizer.handle(env)
                    log.info("email %s -> %s", env.channel_msg_id, result.status)
            finally:
                conn.logout()
        except Exception as e:
            log.warning("imap poll failed: %s", e)
        time.sleep(cfg.poll_seconds)


def _starttls_client():
    class _C(imaplib.IMAP4):
        def open(self, host="", port=imaplib.IMAP4_PORT, timeout=None):
            super().open(host, port)
            self.starttls()

    return _C
