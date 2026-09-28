"""Google Voice forward parser.

When Google Voice forwards SMS or voicemail to email, the carrier- and
voice-side metadata lands in an email whose true semantic is:

    SMS fwd:      "text from +1555...: <the sms body>"
    Voicemail:    "voicemail from +1555...: <transcript>"

GV's exact templates drift; this parser is deliberately tolerant —
extract the originating phone number, then treat the largest free-text
chunk as the message body. Returns (sender_e164, body) or None when the
message doesn't look like a GV forward.
"""

from __future__ import annotations

import re
from email.message import Message

_E164_RE = re.compile(r"\+?\d[\d\s().-]{6,18}\d")
_GV_SENDERS = (
    "voice-noreply@google.com",
    "txt.voice.google.com",
    "@voice.google.com",
)
_GV_SUBJECT_HINTS = ("new text", "new voicemail", "voicemail from", "text from")


def _looks_gv(msg: Message) -> bool:
    frm = (msg.get("From") or "").lower()
    subj = (msg.get("Subject") or "").lower()
    return any(s in frm for s in _GV_SENDERS) or any(
        h in subj for h in _GV_SUBJECT_HINTS
    )


def _extract_number(*texts: str) -> str | None:
    for t in texts:
        m = _E164_RE.search(t)
        if m:
            digits = re.sub(r"\D", "", m.group(0))
            if 7 <= len(digits) <= 15:
                return "+" + digits.lstrip("0")
    return None


def _extract_body(text: str) -> str:
    """Heuristic: drop GV boilerplate lines, keep the substance."""
    drop = (
        "reply to this email to respond",
        "to stop receiving these emails",
        "play voicemail",
        "google voice",
        "https://voice.google.com",
    )
    keep = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not any(d in ln.lower() for d in drop)
    ]
    return "\n".join(keep)


def parse_gv_forward(msg: Message) -> tuple[str, str] | None:
    if not _looks_gv(msg):
        return None
    subject = str(msg.get("Subject") or "")
    from_hdr = str(msg.get("From") or "")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        else:
            body = str(msg.get_payload() or "")

    number = _extract_number(subject, from_hdr, body) or "unknown-gv-sender"
    return number, _extract_body(body) or subject
