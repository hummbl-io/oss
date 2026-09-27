"""Inbound channel adapters for the HUMMBL coordination bus.

Every transport (email, SMS, Signal, voice, webhooks, Meshtastic, ...)
normalizes inbound messages into :class:`InboundEnvelope`, then the
:class:`Normalizer` maps the sender through the allowlist, applies the
type policy, and posts to the canonical bus via the authenticated
``remote_write`` bridge (with spool fallback for offline links).

Adapters never talk to the bus directly; they only produce envelopes.
"""

from .envelope import InboundEnvelope, parse_bus_intent
from .normalizer import IngressResult, Normalizer

__all__ = [
    "InboundEnvelope",
    "IngressResult",
    "Normalizer",
    "parse_bus_intent",
]
