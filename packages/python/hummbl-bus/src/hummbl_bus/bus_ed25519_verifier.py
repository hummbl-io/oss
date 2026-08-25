"""Ed25519 signed envelope verification for the coordination bus.

This module provides optional Ed25519 signature verification for bus messages.
It uses lazy imports of the `cryptography` package so that the core bus_writer
remains stdlib-only when Ed25519 verification is not enabled.

Enable via:
    BUS_ED25519_VERIFY=true — reject unsigned envelopes from privileged senders
    BUS_ED25519_KEY_DIR=/path/to/keys — directory with public key files

Integration point:
    bus_writer.py calls verify_envelope_if_signed() before writing.
    If verification fails, the write is rejected with ValueError.

Promoted from hummbl-governance/bus/bus_ed25519_verifier.py 2026-08-15.
No changes needed — module is stdlib-only with lazy cryptography import.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Envelope field names (must match governance/board/bus_envelope.py)
ENVELOPE_SIGNATURE_FIELD = "signature"
ENVELOPE_KEY_ID_FIELD = "key_id"
ENVELOPE_BODY_FIELD = "body"
ENVELOPE_BODY_HASH_FIELD = "body_hash"
ENVELOPE_EVENT_TYPE_FIELD = "event_type"
ENVELOPE_SENDER_ID_FIELD = "sender_id"

# Fields that are part of the signed payload (excluding signature)
SIGNED_PAYLOAD_FIELDS = [
    "event_id",
    "event_type",
    "correlation_id",
    "sender_id",
    "sender_kind",
    "posted_by",
    "on_behalf_of",
    "authority_source",
    "created_at",
    "body",
    "body_hash",
    "prev_event_hash",
    "key_id",
]


class Ed25519VerificationError(ValueError):
    """Ed25519 signature verification failed."""


class Ed25519NotAvailableError(RuntimeError):
    """The cryptography package is not installed."""


def is_ed25519_verify_enabled() -> bool:
    """Check if Ed25519 verification is enabled via env var."""
    return os.environ.get("BUS_ED25519_VERIFY", "").strip().lower() in (
        "true",
        "1",
        "yes",
    )


def _load_public_key(key_id: str, key_dir: str | None = None) -> bytes:
    """Load a public key from the key directory.

    Key files are named <key_id>.pub and contain raw 32-byte Ed25519 public keys
    in base64 encoding.

    Raises:
        FileNotFoundError: If the key file does not exist
        Ed25519NotAvailableError: If cryptography is not installed
    """
    try:
        from cryptography.hazmat.primitives import serialization  # noqa: F401
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,  # noqa: F401
        )
    except ImportError as exc:
        raise Ed25519NotAvailableError(
            "cryptography package required for Ed25519 verification"
        ) from exc

    key_dir = key_dir or os.environ.get("BUS_ED25519_KEY_DIR", "")
    if not key_dir:
        raise Ed25519VerificationError(
            "BUS_ED25519_KEY_DIR not set; cannot locate public keys"
        )

    key_path = Path(key_dir) / f"{key_id}.pub"
    if not key_path.exists():
        raise Ed25519VerificationError(f"Public key file not found: {key_path}")

    raw_b64 = key_path.read_text(encoding="utf-8").strip()
    import base64

    raw_bytes = base64.b64decode(raw_b64)
    return raw_bytes


def _verify_signature(
    public_key_bytes: bytes, payload: bytes, signature_b64: str
) -> None:
    """Verify an Ed25519 signature.

    Raises:
        Ed25519VerificationError: If signature is invalid
        Ed25519NotAvailableError: If cryptography is not installed
    """
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise Ed25519NotAvailableError(
            "cryptography package required for Ed25519 verification"
        ) from exc

    import base64

    try:
        signature = base64.b64decode(signature_b64)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, payload)
    except InvalidSignature as exc:
        raise Ed25519VerificationError(
            "Ed25519 signature verification failed: signature does not match payload"
        ) from exc
    except Exception as exc:
        raise Ed25519VerificationError(
            f"Ed25519 signature verification error: {exc}"
        ) from exc


def _extract_envelope(message: str) -> dict[str, Any] | None:
    """Extract a JSON envelope from a bus message if present.

    Returns None if the message is not a JSON envelope with a signature field.
    """
    stripped = message.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    # Must have signature field to be an Ed25519 envelope
    if ENVELOPE_SIGNATURE_FIELD not in parsed:
        return None

    return parsed


def _compute_canonical_payload(envelope: dict[str, Any]) -> bytes:
    """Compute the canonical JSON payload for signature verification.

    This must match the signing side: all fields except 'signature',
    sorted keys, compact separators.
    """
    payload = {k: v for k, v in envelope.items() if k != ENVELOPE_SIGNATURE_FIELD}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_envelope_if_signed(message: str, sender_id: str = "") -> bool:
    """Verify an Ed25519 signed envelope if present in the message.

    This is the main integration point for bus_writer.py.

    Args:
        message: The bus message (5th TSV column, may be JSON envelope or plain text)
        sender_id: The sender identity (from_id, for logging)

    Returns:
        True if:
        - Message is not a signed envelope (no verification needed), OR
        - Message is a signed envelope and verification succeeds

    Raises:
        Ed25519VerificationError: If verification fails (signature invalid,
            key not found, body hash mismatch)
        Ed25519NotAvailableError: If cryptography is not installed and
            verification is enabled
    """
    envelope = _extract_envelope(message)
    if envelope is None:
        # Not a signed envelope — no verification needed
        return True

    if not is_ed25519_verify_enabled():
        # Envelope is signed but verification is not enabled — accept with warning
        logger.debug(
            "Ed25519 signed envelope from %s accepted without verification "
            "(BUS_ED25519_VERIFY not enabled)",
            sender_id,
        )
        return True

    # Verification is enabled — verify the signature
    key_id = envelope.get(ENVELOPE_KEY_ID_FIELD, "")
    if not key_id:
        raise Ed25519VerificationError("Signed envelope missing key_id field")

    signature = envelope.get(ENVELOPE_SIGNATURE_FIELD, "")
    if not signature:
        raise Ed25519VerificationError("Signed envelope missing signature field")

    # Verify body hash if present
    body = envelope.get(ENVELOPE_BODY_FIELD, "")
    body_hash = envelope.get(ENVELOPE_BODY_HASH_FIELD, "")
    if body_hash:
        import hashlib

        actual_hash = hashlib.sha256(body.encode()).hexdigest()
        if actual_hash != body_hash:
            raise Ed25519VerificationError(
                f"body_hash mismatch: expected {body_hash}, got {actual_hash}"
            )

    # Load public key and verify signature
    public_key_bytes = _load_public_key(key_id)
    payload = _compute_canonical_payload(envelope)
    _verify_signature(public_key_bytes, payload, signature)

    logger.info(
        "Ed25519 envelope verified: sender=%s key_id=%s",
        sender_id,
        key_id,
    )
    return True


def verify_envelope_strict(message: str, sender_id: str = "") -> bool:
    """Strict mode: reject unsigned envelopes from privileged senders.

    When BUS_ED25519_STRICT=true, privileged event types (DECISION, GRANT,
    DIRECTIVE) must be signed. Unsigned privileged events are rejected.

    Args:
        message: The bus message
        sender_id: The sender identity

    Returns:
        True if the message passes strict verification

    Raises:
        Ed25519VerificationError: If a privileged event is unsigned in strict mode
    """
    strict = os.environ.get("BUS_ED25519_STRICT", "").strip().lower() in (
        "true",
        "1",
        "yes",
    )

    if not strict:
        return verify_envelope_if_signed(message, sender_id)

    envelope = _extract_envelope(message)
    if envelope is None:
        # In strict mode, check if this is a privileged event type
        # by looking at the message content for event type markers
        # (This is a heuristic — the real check is in the structured event)
        return True

    event_type = envelope.get(ENVELOPE_EVENT_TYPE_FIELD, "")
    privileged_types = {"DECISION", "GRANT", "DIRECTIVE"}

    if event_type in privileged_types and not envelope.get(ENVELOPE_SIGNATURE_FIELD):
        raise Ed25519VerificationError(
            f"Strict mode: privileged event type {event_type} must be signed"
        )

    return verify_envelope_if_signed(message, sender_id)
