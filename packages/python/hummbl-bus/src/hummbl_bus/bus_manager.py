"""SecureBusManager - Centralized bus management with security.

Provides identity registration, message signing/verification,
replay attack prevention, timestamp validation, and audit logging.

Extracted from hummbl-governance. The following external import was removed:
    - hummbl_governance.security.key_management (KeyManager, KeyNotFoundError)
KeyManager integration must be provided by the consumer if needed.
"""

from __future__ import annotations

import logging

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None  # type: ignore[assignment]
from datetime import datetime
from pathlib import Path
from typing import Any

from .bus_security import (
    BusIdentity,
    BusMessage,
    IdentityError,
    ReplayAttackError,
    SecurityError,
    TimestampError,
    VerificationError,
)


class SecureBusManager:
    """Centralized manager for secure coordination bus access.

    Handles identity registration, message signing/verification,
    and maintains security audit logs.

    NOTE: KeyManager integration was removed during extraction from
    hummbl-governance. If you need persistent key storage, subclass this
    and override register_identity/rotate_identity_key.

    Attributes:
    ----------
    bus_path : Path
        Path to the coordination bus TSV file
    identities : dict[str, BusIdentity]
        Registered identities by ID
    security_logger : logging.Logger
        Logger for security events

    Example:
    -------
    >>> manager = SecureBusManager(
    ...     bus_path="_state/coordination/messages.tsv",
    ...     secret_key=b'...'
    ... )
    >>> manager.register_identity("agent-001")
    >>> manager.write_message("agent-001", "all", "STATUS", {"status": "ready"})
    >>> messages = manager.read_messages(since=datetime.now() - timedelta(minutes=5))
    """

    DEFAULT_TIMESTAMP_TOLERANCE = 300  # 5 minutes

    def __init__(
        self,
        bus_path: str | Path,
        secret_key: bytes | None = None,
        audit_log_path: str | Path | None = None,
    ):
        """Initialize the secure bus manager.

        Parameters
        ----------
        bus_path : str | Path
            Path to the coordination bus TSV file
        secret_key : bytes, optional
            Master secret for deriving identity keys
        audit_log_path : str | Path, optional
            Path for security audit log (defaults to bus_path.parent / security.log)
        """
        self.bus_path = Path(bus_path).expanduser()
        self.identities: dict[str, BusIdentity] = {}
        self._master_secret = secret_key

        # Setup audit logging
        if audit_log_path is None:
            audit_log_path = self.bus_path.parent / "security.log"
        self.audit_log_path = Path(audit_log_path).expanduser()

        self.security_logger = logging.getLogger("bus_security")
        self.security_logger.setLevel(logging.INFO)

        # Clear any existing handlers and add file handler
        self.security_logger.handlers.clear()
        handler = logging.FileHandler(self.audit_log_path)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)

        # Ensure bus file exists with header
        self._ensure_bus_exists()

    def _ensure_bus_exists(self) -> None:
        """Ensure the bus file exists with proper header."""
        self.bus_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.bus_path.exists():
            # Create new bus with header
            header = "timestamp\tfrom\tto\ttype\tmessage\tnonce\tsignature\tsigner\n"
            self.bus_path.write_text(header, encoding="utf-8")
            self.security_logger.info(f"Created new bus at {self.bus_path}")

    def _derive_key(self, identity_id: str) -> bytes:
        """Derive a key from master secret and identity ID.

        Uses HMAC-based key derivation for deterministic key generation.
        """
        import hashlib
        import hmac

        if not self._master_secret:
            raise IdentityError("No master secret configured for key derivation")

        return hmac.new(
            self._master_secret,
            identity_id.encode("utf-8"),
            hashlib.sha256,
        ).digest()

    def register_identity(
        self,
        identity_id: str,
        secret: bytes | None = None,
    ) -> BusIdentity:
        """Register a new bus participant.

        Parameters
        ----------
        identity_id : str
            Unique identifier for the identity
        secret : bytes, optional
            Secret key (if None, derives from master or generates new)

        Returns:
        -------
        BusIdentity
            The registered identity
        """
        if identity_id in self.identities:
            raise IdentityError(f"Identity {identity_id} already registered")

        # Derive from master secret
        if secret is None and self._master_secret is not None:
            secret = self._derive_key(identity_id)

        # Create identity (will generate random key if secret still None)
        identity = BusIdentity(identity_id, secret)
        self.identities[identity_id] = identity

        self.security_logger.info(f"Registered identity: {identity_id}")
        return identity

    def get_identity(self, identity_id: str) -> BusIdentity | None:
        """Get a registered identity.

        Parameters
        ----------
        identity_id : str
            Identity ID to look up

        Returns:
        -------
        BusIdentity | None
            The identity if registered, None otherwise
        """
        return self.identities.get(identity_id)

    def rotate_identity_key(self, identity_id: str) -> BusIdentity:
        """Rotate an identity's key.

        Parameters
        ----------
        identity_id : str
            Identity to rotate

        Returns:
        -------
        BusIdentity
            Identity with new key
        """
        if identity_id not in self.identities:
            raise IdentityError(f"Identity {identity_id} not registered")

        # Generate new random key
        identity = BusIdentity(identity_id)

        self.identities[identity_id] = identity
        self.security_logger.warning(f"Rotated key for identity: {identity_id}")
        return identity

    def write_message(
        self,
        from_id: str,
        to_id: str,
        msg_type: str,
        payload: dict[str, Any],
    ) -> BusMessage:
        """Write a signed message to the bus.

        Parameters
        ----------
        from_id : str
            Sender identity ID (must be registered)
        to_id : str
            Recipient identity ID or "all"
        msg_type : str
            Message type (STATUS, PROPOSAL, etc.)
        payload : dict
            Message payload

        Returns:
        -------
        BusMessage
            The signed message that was written

        Raises:
        ------
        IdentityError
            If sender identity not registered
        """
        identity = self.identities.get(from_id)
        if identity is None:
            raise IdentityError(f"Identity not registered: {from_id}")

        # Create and sign message
        msg = identity.create_signed_message(to_id, msg_type, payload)

        # Append to bus under exclusive advisory lock
        with open(self.bus_path, "a", encoding="utf-8") as f:
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_EX)
            elif msvcrt is not None:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.write(msg.to_tsv_line() + "\n")
            f.flush()
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_UN)
            elif msvcrt is not None:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

        self.security_logger.info(
            f"Message written: {from_id} -> {to_id}, type={msg_type}"
        )
        return msg

    def read_messages(
        self,
        since: datetime | None = None,
        verify: bool = True,
        sender_filter: str | None = None,
        track_nonces: bool = False,
    ) -> list[BusMessage]:
        """Read and verify messages from the bus.

        Parameters
        ----------
        since : datetime, optional
            Only return messages after this time
        verify : bool
            Whether to verify signatures (raises on failure)
        sender_filter : str, optional
            Only return messages from this sender
        track_nonces : bool
            Whether to track nonces for replay detection.
            Default False to allow re-reading messages.

        Returns:
        -------
        list[BusMessage]
            Verified messages

        Raises:
        ------
        SecurityError
            If verification fails and verify=True
        """
        if not self.bus_path.exists():
            return []

        messages: list[BusMessage] = []
        seen_nonces: set[str] = set() if not track_nonces else None

        with open(self.bus_path, "r", encoding="utf-8") as f:
            # Skip header
            header = f.readline()
            if not header.startswith("timestamp"):
                f.seek(0)  # No header, reset

            for line_num, line in enumerate(f, start=2):
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = BusMessage.from_tsv_line(line)
                except Exception as e:
                    self.security_logger.warning(
                        f"Failed to parse line {line_num}: {e}"
                    )
                    continue

                # Apply filters
                if sender_filter and msg.sender != sender_filter:
                    continue

                if since is not None:
                    try:
                        msg_time = datetime.fromisoformat(
                            msg.timestamp.replace("Z", "+00:00")
                        )
                        if msg_time < since:
                            continue
                    except ValueError:
                        continue

                # Verify signature if present
                if verify and msg.signature:
                    identity = self.identities.get(msg.sender)
                    if identity is None:
                        self.security_logger.warning(
                            f"Unknown sender (cannot verify): {msg.sender}"
                        )
                        # Continue with unverified message
                        messages.append(msg)
                        continue

                    # Check for duplicate nonces within this read if not tracking
                    if not track_nonces and msg.nonce in seen_nonces:
                        self.security_logger.warning(
                            f"Duplicate nonce in read: {msg.nonce}"
                        )
                        continue

                    try:
                        # Only check replay if track_nonces is True
                        identity.verify_message(msg, check_replay=track_nonces)
                        if not track_nonces:
                            seen_nonces.add(msg.nonce)
                        messages.append(msg)
                    except ReplayAttackError as e:
                        self.security_logger.error(
                            f"REPLAY ATTACK from {msg.sender}: {e}"
                        )
                        if track_nonces:
                            raise
                        # Skip duplicate when not tracking
                        continue
                    except (VerificationError, TimestampError) as e:
                        self.security_logger.error(
                            f"Verification failed for {msg.sender}: {e}"
                        )
                        if verify:
                            raise
                        messages.append(msg)
                else:
                    messages.append(msg)

        return messages

    def verify_all_since(
        self,
        sender: str,
        since: datetime,
    ) -> tuple[list[BusMessage], list[SecurityError]]:
        """Verify all messages from a sender since a given time.

        Returns both valid messages and any verification errors found.

        Parameters
        ----------
        sender : str
            Sender identity to verify
        since : datetime
            Start time for verification

        Returns:
        -------
        tuple[list[BusMessage], list[SecurityError]]
            (valid_messages, errors)
        """
        identity = self.identities.get(sender)
        if identity is None:
            raise IdentityError(f"Identity not registered: {sender}")

        valid: list[BusMessage] = []
        errors: list[SecurityError] = []

        with open(self.bus_path, "r", encoding="utf-8") as f:
            f.readline()  # Skip header

            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = BusMessage.from_tsv_line(line)
                except Exception:
                    continue  # Skip unparseable

                if msg.sender != sender:
                    continue

                if since is not None:
                    try:
                        msg_time = datetime.fromisoformat(
                            msg.timestamp.replace("Z", "+00:00")
                        )
                        if msg_time < since:
                            continue
                    except ValueError:
                        continue

                if not msg.signature:
                    errors.append(
                        VerificationError(
                            f"Message at {msg.timestamp} has no signature"
                        )
                    )
                    continue

                try:
                    identity.verify_message(msg)
                    valid.append(msg)
                except SecurityError as e:
                    errors.append(e)

        return valid, errors

    def list_registered_identities(self) -> list[str]:
        """List all registered identity IDs.

        Returns:
        -------
        list[str]
            List of identity IDs
        """
        return list(self.identities.keys())

    def get_audit_log(self, lines: int = 100) -> list[str]:
        """Get recent audit log entries.

        Parameters
        ----------
        lines : int
            Number of lines to return

        Returns:
        -------
        list[str]
            Audit log entries
        """
        if not self.audit_log_path.exists():
            return []

        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        return [line.strip() for line in all_lines[-lines:]]
