"""Normalized inbound envelope + bus-intent parsing.

Every channel adapter produces exactly this shape. The normalizer
consumes it; adapters never see bus internals.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from ..message_types import CANONICAL_MESSAGE_TYPES

# Channels are free-form but lowercase; keep the set open so a new
# transport only needs an adapter, not a schema change.
# Recipient must be explicit: `@name` or `name:` -- an un-prefixed word
# with no colon stays part of the message ("STATUS fleet sync green"
# is a message about the fleet, not a post to "fleet").
_INTENT_RE = re.compile(
    r"^\s*(?P<type>[A-Za-z_]+)(?:\s+(?P<to>@[A-Za-z0-9._-]+|[A-Za-z0-9._-]+(?=:)))?\s*:?\s*(?P<body>.*)$",
    re.DOTALL,
)
_PIN_RE = re.compile(r"\bpin=([A-Za-z0-9._:-]{4,64})\b")


@dataclass(frozen=True, slots=True)
class InboundEnvelope:
    """One inbound channel message, normalized."""

    channel: str  # e.g. "email", "signal", "sms", "voice", "meshtastic"
    channel_msg_id: str  # provider-unique id; dedup anchor
    sender_addr: str  # +E.164, email, discord id, mesh node id...
    received_at: str  # UTC ISO-8601 with Z
    body: str  # raw text the sender wrote
    meta: dict = field(default_factory=dict)  # adapter extras (subj, urls)

    @property
    def request_id(self) -> str:
        """Deterministic dedup id: identical deliveries collapse."""
        key = f"{self.channel}|{self.channel_msg_id}".encode()
        return hashlib.sha256(key).hexdigest()[:32]

    def validate(self) -> list[str]:
        errs = []
        if not self.channel or not self.channel.strip():
            errs.append("channel is required")
        if not self.channel_msg_id or not self.channel_msg_id.strip():
            errs.append("channel_msg_id is required")
        if not self.sender_addr or not self.sender_addr.strip():
            errs.append("sender_addr is required")
        if not self.received_at.endswith("Z"):
            errs.append("received_at must be UTC with Z suffix")
        if not self.body.strip():
            errs.append("body is empty")
        return errs


@dataclass(frozen=True, slots=True)
class BusIntent:
    """Parsed intent: what the sender wants posted."""

    msg_type: str
    to: str
    message: str
    requested_type: str  # what they asked for before policy
    pin: str | None = None  # in-body privilege proof, if present


def parse_bus_intent(
    body: str, *, default_type: str = "STATUS", default_to: str = "all"
) -> BusIntent:
    """Parse `TYPE [to] body` syntax from a free-text channel message.

    Examples:
        "STATUS fleet sync green"          -> STATUS to=all
        "QUESTION operator: eta on #551"   -> QUESTION to=operator
        "ALERT all: disk at 92%"           -> ALERT to=all
        "blocker is real"                  -> STATUS to=all (type inferred)
        "DIRECTIVE devin pin=abc123: ship" -> DIRECTIVE w/ pin (elevated)

    The first token is treated as a type ONLY if it is a canonical bus
    type; otherwise the whole body is the message and type falls back to
    ``default_type``. A ``pin=`` token is extracted wherever it appears.
    """
    pin: str | None = None
    m = _PIN_RE.search(body)
    if m:
        pin = m.group(1)
        body = _PIN_RE.sub("", body).strip()

    m = _INTENT_RE.match(body)
    if not m:
        return BusIntent(default_type, default_to, body.strip(), default_type, pin)

    raw_type = m.group("type").upper()
    to = (m.group("to") or "").lstrip("@") or default_to
    text = m.group("body").strip()

    if raw_type in CANONICAL_MESSAGE_TYPES:
        return BusIntent(raw_type, to, text or raw_type, raw_type, pin)

    # First word wasn't a type -> entire body is the message.
    return BusIntent(default_type, default_to, body.strip(), default_type, pin)
