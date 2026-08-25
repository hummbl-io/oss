"""Core security classes for the coordination bus.

Provides message structures, exceptions, and identity management
with HMAC-SHA256 signing support.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def generate_nonce() -> str:
    """Generate a unique nonce with embedded timestamp.

    The nonce format is: {micros_since_epoch}-{random_hex}
    This provides both uniqueness and temporal information.

    Returns:
    -------
    str
        Unique nonce string
    """
    return f"{int(time.time() * 1000000)}-{secrets.token_hex(8)}"


class SecurityError(Exception):
    """Base exception for bus security errors."""


class VerificationError(SecurityError):
    """Message verification failed."""


class ReplayAttackError(SecurityError):
    """Replay attack detected - nonce already seen."""


class TimestampError(SecurityError):
    """Message timestamp outside acceptable tolerance."""


class IdentityError(SecurityError):
    """Identity-related error."""


@dataclass(frozen=True, slots=True)
class BusMessage:
    """A signed message on the coordination bus.

    Supports both legacy TSV format (without signatures) and
    new signed format with cryptographic verification.

    Attributes:
    ----------
    timestamp : str
        ISO 8601 timestamp (UTC, Z suffix)
    sender : str
        Identity ID of the sender
    recipient : str
        Identity ID of recipient or "all"
    msg_type : str
        Message type (STATUS, PROPOSAL, ACK, etc.)
    payload : dict
        Message payload (will be JSON-encoded for signing)
    nonce : str
        Unique nonce for replay protection
    signature : str | None
        HMAC-SHA256 signature (hex), or None for unsigned messages
    """

    timestamp: str
    sender: str
    recipient: str
    msg_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    nonce: str = ""
    signature: str | None = None

    def __post_init__(self):
        # Generate nonce if not provided
        if not self.nonce:
            object.__setattr__(self, "nonce", generate_nonce())

    @classmethod
    def create(
        cls,
        sender: str,
        recipient: str,
        msg_type: str,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> BusMessage:
        """Factory method to create a new message.

        Parameters
        ----------
        sender : str
            Identity ID of sender
        recipient : str
            Identity ID of recipient or "all"
        msg_type : str
            Message type
        payload : dict, optional
            Message payload
        timestamp : str, optional
            Override timestamp (defaults to now)

        Returns:
        -------
        BusMessage
            New unsigned message (call sign() to add signature)
        """
        ts = timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(
            timestamp=ts,
            sender=sender,
            recipient=recipient,
            msg_type=msg_type,
            payload=payload or {},
        )

    def to_tsv_line(self) -> str:
        r"""Convert to TSV line format (legacy or signed).

        For unsigned messages: timestamp\tsender\trecipient\ttype\tmessage
        For signed messages: adds nonce and signature columns

        Returns:
        -------
        str
            TSV-formatted line
        """
        # Main message body from payload
        if "message" in self.payload:
            message_body = self.payload["message"]
        else:
            message_body = json.dumps(self.payload, separators=(",", ":"))

        # Sanitize to preserve TSV structure
        message_body = message_body.replace("\t", " ").replace("\n", " ")

        if self.signature:
            # Signed format: 8 columns
            return (
                f"{self.timestamp}\t{self.sender}\t{self.recipient}\t"
                f"{self.msg_type}\t{message_body}\t{self.nonce}\t"
                f"{self.signature}\t{self.sender}"
            )
        else:
            # Legacy format: 5 columns
            return (
                f"{self.timestamp}\t{self.sender}\t{self.recipient}\t"
                f"{self.msg_type}\t{message_body}"
            )

    @classmethod
    def from_tsv_line(cls, line: str) -> BusMessage:
        """Parse a TSV line into a BusMessage.

        Handles both legacy 5-column and signed 8-column formats.

        Parameters
        ----------
        line : str
            TSV line from the bus

        Returns:
        -------
        BusMessage
            Parsed message (may be unsigned)
        """
        parts = line.rstrip("\n\r").split("\t")

        if len(parts) >= 8:
            # Signed format with signature
            (
                timestamp,
                sender,
                recipient,
                msg_type,
                message_body,
                nonce,
                signature,
                _,
            ) = parts[:8]
            # Try to parse message_body as JSON, fallback to {"message": body}
            try:
                payload = json.loads(message_body)
            except json.JSONDecodeError:
                payload = {"message": message_body}
            return cls(
                timestamp=timestamp,
                sender=sender,
                recipient=recipient,
                msg_type=msg_type,
                payload=payload,
                nonce=nonce,
                signature=signature,
            )
        elif len(parts) >= 5:
            # Legacy unsigned format
            timestamp, sender, recipient, msg_type, message_body = parts[:5]
            try:
                payload = json.loads(message_body)
            except json.JSONDecodeError:
                payload = {"message": message_body}
            return cls(
                timestamp=timestamp,
                sender=sender,
                recipient=recipient,
                msg_type=msg_type,
                payload=payload,
            )
        else:
            raise VerificationError(f"Invalid TSV format: {len(parts)} columns")

    def _canonicalize(self) -> str:
        """Create canonical string for signing.

        The canonical form includes all fields except the signature itself,
        in a deterministic order with JSON-encoded payload.

        Returns:
        -------
        str
            Canonical string for HMAC signing
        """
        # Sort payload keys for determinism
        canonical_payload = json.dumps(
            self.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )

        return (
            f"{self.timestamp}|{self.sender}|{self.recipient}|"
            f"{self.msg_type}|{canonical_payload}|{self.nonce}"
        )


class BusIdentity:
    """Identity for bus participants with signing/verification capabilities.

    Each identity has a unique ID and a secret key used for HMAC-SHA256
    signing. Supports replay attack prevention through nonce tracking and
    timestamp validation.

    Attributes:
    ----------
    identity_id : str
        Unique identifier for this identity
    secret : bytes
        32-byte secret key for HMAC signing

    Example:
    -------
    >>> identity = BusIdentity("agent-001")
    >>> msg = identity.create_signed_message("agent-002", "PROPOSAL", {"action": "test"})
    >>> assert identity.verify_message(msg)  # Valid
    >>>
    >>> # Tamper detection
    >>> msg.payload["action"] = "hacked"
    >>> assert not identity.verify_message(msg)  # Invalid signature
    """

    # Constants for security parameters
    NONCE_TTL_SECONDS = 300  # 5 minutes
    TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes
    MAX_SEEN_NONCES = 10000  # Prevent memory exhaustion

    def __init__(self, identity_id: str, secret: bytes | None = None):
        """Initialize a bus identity.

        Parameters
        ----------
        identity_id : str
            Unique identifier for this identity
        secret : bytes, optional
            32-byte secret key. If not provided, a random key is generated.
        """
        self.identity_id = identity_id
        self.secret = secret or secrets.token_bytes(32)

        if len(self.secret) < 32:
            raise IdentityError("Secret must be at least 32 bytes")

        # Nonce tracking for replay prevention: {nonce: timestamp}
        self._seen_nonces: dict[str, float] = {}
        self._last_cleanup = time.time()
        self._lock = threading.Lock()  # Add a lock for thread-safety

    def _cleanup_old_nonces(self) -> None:
        """Remove expired nonces to prevent memory exhaustion."""
        with self._lock:  # Acquire lock
            now = time.time()
            if now - self._last_cleanup < 60:  # Cleanup at most once per minute
                return

            cutoff = now - self.NONCE_TTL_SECONDS
            expired = [n for n, ts in self._seen_nonces.items() if ts < cutoff]
            for nonce in expired:
                del self._seen_nonces[nonce]

            self._last_cleanup = now

    def _record_nonce(self, nonce: str) -> None:
        """Record a nonce as seen.

        Parameters
        ----------
        nonce : str
            Nonce to record
        """
        self._cleanup_old_nonces()  # This will acquire the lock internally

        with self._lock:  # Acquire lock
            # Prevent memory exhaustion - remove oldest if at limit
            if len(self._seen_nonces) >= self.MAX_SEEN_NONCES:
                # Remove 10% oldest entries
                sorted_nonces = sorted(self._seen_nonces.items(), key=lambda x: x[1])
                for old_nonce, _ in sorted_nonces[: self.MAX_SEEN_NONCES // 10]:
                    del self._seen_nonces[old_nonce]

            self._seen_nonces[nonce] = time.time()

    def _is_nonce_seen(self, nonce: str) -> bool:
        """Check if a nonce has been seen before.

        Parameters
        ----------
        nonce : str
            Nonce to check

        Returns:
        -------
        bool
            True if nonce was previously seen
        """
        self._cleanup_old_nonces()  # This will acquire the lock internally
        with self._lock:  # Acquire lock
            return nonce in self._seen_nonces

    def sign_message(self, msg: BusMessage) -> str:
        """Sign a message with HMAC-SHA256.

        Parameters
        ----------
        msg : BusMessage
            Message to sign (modified in-place with signature)

        Returns:
        -------
        str
            Hex-encoded signature
        """
        canonical = msg._canonicalize()
        signature = hmac.new(
            self.secret, canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        object.__setattr__(msg, "signature", signature)
        object.__setattr__(msg, "sender", self.identity_id)
        return signature

    def create_signed_message(
        self,
        recipient: str,
        msg_type: str,
        payload: dict[str, Any],
    ) -> BusMessage:
        """Create and sign a new message.

        Parameters
        ----------
        recipient : str
            Identity ID of recipient or "all"
        msg_type : str
            Message type
        payload : dict
            Message payload

        Returns:
        -------
        BusMessage
            Signed message ready for the bus
        """
        msg = BusMessage.create(
            sender=self.identity_id,
            recipient=recipient,
            msg_type=msg_type,
            payload=payload,
        )
        self.sign_message(msg)
        return msg

    def verify_message(
        self,
        msg: BusMessage,
        check_timestamp: bool = True,
        check_replay: bool = True,
    ) -> bool:
        """Verify a message's signature and security properties.

        Parameters
        ----------
        msg : BusMessage
            Message to verify
        check_timestamp : bool
            Whether to validate timestamp freshness
        check_replay : bool
            Whether to check for replay attacks

        Returns:
        -------
        bool
            True if message is valid

        Raises:
        ------
        VerificationError
            If signature verification fails
        ReplayAttackError
            If replay attack detected
        TimestampError
            If timestamp is outside tolerance
        """
        # Must have a signature
        if not msg.signature:
            raise VerificationError("Message has no signature")

        # Check timestamp freshness
        if check_timestamp:
            try:
                msg_time = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                msg_ts = msg_time.timestamp()
                now = time.time()

                if abs(now - msg_ts) > self.TIMESTAMP_TOLERANCE_SECONDS:
                    raise TimestampError(
                        f"Message timestamp {msg.timestamp} is outside "
                        f"acceptable tolerance ({self.TIMESTAMP_TOLERANCE_SECONDS}s)"
                    )
            except ValueError as e:
                raise TimestampError(
                    f"Invalid timestamp format: {msg.timestamp}"
                ) from e

        # Check for replay attack
        if check_replay and self._is_nonce_seen(msg.nonce):
            raise ReplayAttackError(f"Nonce {msg.nonce} has been seen before")

        # Verify HMAC signature
        canonical = msg._canonicalize()
        expected_sig = hmac.new(
            self.secret, canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(msg.signature, expected_sig):
            raise VerificationError("Signature mismatch")

        # Record nonce as seen (after successful verification)
        if check_replay:
            self._record_nonce(msg.nonce)

        return True
