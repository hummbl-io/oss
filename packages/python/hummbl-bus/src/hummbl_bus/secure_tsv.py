"""Secure TSV encoding/decoding for the coordination bus.

CRIT-003: TSV Injection Prevention
Implements base64 encoding for message payloads to prevent tab and newline
injection attacks that could corrupt the TSV message bus format.

The format maintains backward compatibility:
    - Old plaintext messages can still be read
    - New messages are base64-encoded in the payload column
    - A version flag indicates encoding type
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TSVInjectionError(Exception):
    """Raised when TSV injection is detected or encoding fails."""


@dataclass(frozen=True)
class BusMessage:
    """A message on the coordination bus.

    Attributes:
        timestamp: ISO format timestamp.
        from_id: Sender identifier (agent name).
        to_id: Recipient identifier (agent name or "all").
        message_type: Type of message (STATUS, PROPOSAL, ACK, etc.).
        payload: Message content (dict, str, or bytes).
        version: Encoding version (1.0 = base64, legacy = plaintext).
    """

    timestamp: str
    from_id: str
    to_id: str
    message_type: str
    payload: dict[str, Any] | str
    version: str = "1.0"

    def __post_init__(self):
        """Validate fields after creation."""
        # Validate timestamp format roughly
        if not self.timestamp or not isinstance(self.timestamp, str):
            object.__setattr__(
                self,
                "timestamp",
                datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

        # Ensure IDs don't contain tabs or newlines
        for field_name, value in [
            ("from_id", self.from_id),
            ("to_id", self.to_id),
            ("message_type", self.message_type),
        ]:
            if not isinstance(value, str):
                raise TSVInjectionError(f"{field_name} must be a string")
            if "\t" in value or "\n" in value or "\r" in value:
                raise TSVInjectionError(
                    f"{field_name} contains tab or newline: {value!r}"
                )
            if "\x00" in value:
                raise TSVInjectionError(f"{field_name} contains null byte: {value!r}")


class SecureTSVEncoder:
    """Encoder for secure TSV bus messages.

    Encodes message payloads using base64 to prevent TSV injection attacks
    where malicious content could fake columns or rows.
    """

    # TSV column headers
    COLUMNS = ["timestamp", "from", "to", "type", "version", "payload"]

    @classmethod
    def encode_message(cls, message: BusMessage) -> str:
        """Encode a BusMessage to a secure TSV line.

        Args:
            message: The message to encode.

        Returns:
            TSV-formatted line string (without newline).

        Raises:
            TSVInjectionError: If encoding fails.
        """
        try:
            # Serialize payload to JSON
            if isinstance(message.payload, dict):
                payload_json = json.dumps(message.payload, separators=(",", ":"))
            elif isinstance(message.payload, str):
                payload_json = message.payload
            else:
                payload_json = json.dumps(message.payload, separators=(",", ":"))

            # Base64 encode to prevent TSV injection
            payload_bytes = payload_json.encode("utf-8")
            encoded_payload = base64.b64encode(payload_bytes).decode("ascii")

            # Build TSV line
            fields = [
                message.timestamp,
                message.from_id,
                message.to_id,
                message.message_type,
                message.version,
                encoded_payload,
            ]

            # Verify no tabs or newlines in metadata fields
            for i, field in enumerate(fields[:-1]):  # Skip payload (already encoded)
                if "\t" in field or "\n" in field or "\r" in field:
                    raise TSVInjectionError(
                        f"Field at index {i} contains tab or newline: {field!r}"
                    )

            return "\t".join(fields)

        except (json.JSONEncodeError, UnicodeEncodeError) as e:
            raise TSVInjectionError(f"Failed to encode message payload: {e}") from e

    @classmethod
    def encode_legacy_message(
        cls,
        timestamp: str,
        from_id: str,
        to_id: str,
        message_type: str,
        message: str,
    ) -> str:
        """Encode a message in legacy (plaintext) format.

        Only use this for backward compatibility or when the message
        content is guaranteed safe.

        Args:
            timestamp: ISO timestamp.
            from_id: Sender ID.
            to_id: Recipient ID.
            message_type: Message type.
            message: Plaintext message.

        Returns:
            TSV-formatted line string (legacy format).
        """
        # Sanitize the message to remove tabs and newlines
        safe_message = message.replace("\t", " ").replace("\n", " ").replace("\r", " ")

        fields = [timestamp, from_id, to_id, message_type, "legacy", safe_message]
        return "\t".join(fields)

    @classmethod
    def create_and_encode(
        cls,
        from_id: str,
        to_id: str,
        message_type: str,
        payload: dict[str, Any] | str,
        timestamp: str | None = None,
    ) -> str:
        """Create a BusMessage and encode it in one step.

        Args:
            from_id: Sender identifier.
            to_id: Recipient identifier.
            message_type: Type of message.
            payload: Message content.
            timestamp: Optional timestamp (default: now).

        Returns:
            Encoded TSV line.
        """
        if timestamp is None:
            timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%Z")

        message = BusMessage(
            timestamp=timestamp,
            from_id=from_id,
            to_id=to_id,
            message_type=message_type,
            payload=payload,
            version="1.0",
        )

        return cls.encode_message(message)


class SecureTSVDecoder:
    """Decoder for secure TSV bus messages.

    Handles both new base64-encoded messages and legacy plaintext messages.
    """

    @classmethod
    def decode_line(cls, line: str) -> BusMessage:
        """Decode a TSV line to a BusMessage.

        Args:
            line: TSV-formatted line (without trailing newline).

        Returns:
            Decoded BusMessage.

        Raises:
            TSVInjectionError: If decoding fails or format is invalid.
        """
        line = line.rstrip("\n\r")

        if not line or line.startswith("#"):
            raise TSVInjectionError("Empty line or comment")

        fields = line.split("\t")

        # Handle both old format (5 columns) and new format (6 columns)
        if len(fields) == 5:
            # Legacy format: timestamp, from, to, type, message
            timestamp, from_id, to_id, message_type, payload = fields
            version = "legacy"
        elif len(fields) == 6:
            # New format: timestamp, from, to, type, version, payload
            timestamp, from_id, to_id, message_type, version, payload = fields
        else:
            raise TSVInjectionError(
                f"Invalid TSV format: expected 5 or 6 columns, got {len(fields)}"
            )

        # Decode payload based on version
        if version == "legacy":
            # Legacy: plaintext payload
            decoded_payload = payload
        elif version == "1.0":
            # New format: base64 encoded
            try:
                decoded_bytes = base64.b64decode(payload)
                decoded_str = decoded_bytes.decode("utf-8")

                # Try to parse as JSON
                try:
                    decoded_payload = json.loads(decoded_str)
                except json.JSONDecodeError:
                    # Not valid JSON, return as string
                    decoded_payload = decoded_str

            except (base64.binascii.Error, UnicodeDecodeError) as e:
                raise TSVInjectionError(f"Failed to decode base64 payload: {e}") from e
        else:
            # Unknown version, treat as plaintext
            decoded_payload = payload

        return BusMessage(
            timestamp=timestamp,
            from_id=from_id,
            to_id=to_id,
            message_type=message_type,
            payload=decoded_payload,
            version=version,
        )

    @classmethod
    def decode_file(cls, file_path: str | Path) -> list[BusMessage]:
        """Decode all messages from a TSV file.

        Args:
            file_path: Path to the TSV file.

        Returns:
            List of decoded BusMessage objects.

        Raises:
            TSVInjectionError: If file cannot be read.
        """
        file_path = Path(file_path)
        messages = []

        if not file_path.exists():
            return messages

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Skip header line
                    if line_num == 1 and "timestamp" in line.lower():
                        continue

                    try:
                        message = cls.decode_line(line)
                        messages.append(message)
                    except TSVInjectionError as e:
                        logger.warning(
                            f"Failed to decode line {line_num} in {file_path}: {e}"
                        )
                        continue

        except OSError as e:
            raise TSVInjectionError(f"Failed to read file {file_path}: {e}") from e

        return messages

    @classmethod
    def is_valid_line(cls, line: str) -> bool:
        """Check if a line is valid TSV format.

        Args:
            line: TSV line to validate.

        Returns:
            True if the line is valid, False otherwise.
        """
        try:
            cls.decode_line(line)
            return True
        except TSVInjectionError:
            return False


def append_message_to_bus(
    file_path: str | Path,
    from_id: str,
    to_id: str,
    message_type: str,
    payload: dict[str, Any] | str,
    timestamp: str | None = None,
    ensure_header: bool = True,
) -> None:
    """Append a message to the TSV bus file.

    .. deprecated::
        Do not use for production bus writes. This function lacks fcntl
        mutual exclusion and HMAC signing. Use
        ``bus_writer.post_message()`` instead, which provides fcntl.LOCK_EX
        locking and optional HMAC-SHA256 signing.

    Args:
        file_path: Path to the TSV bus file.
        from_id: Sender identifier.
        to_id: Recipient identifier.
        message_type: Type of message.
        payload: Message content.
        timestamp: Optional timestamp (default: now).
        ensure_header: If True, write header if file is new.

    Raises:
        TSVInjectionError: If appending fails.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create encoded line
    encoded_line = SecureTSVEncoder.create_and_encode(
        from_id=from_id,
        to_id=to_id,
        message_type=message_type,
        payload=payload,
        timestamp=timestamp,
    )

    try:
        # Check if file exists and needs header
        write_header = ensure_header and (
            not file_path.exists() or file_path.stat().st_size == 0
        )

        with open(file_path, "a", encoding="utf-8", newline="") as f:
            if write_header:
                f.write("\t".join(SecureTSVEncoder.COLUMNS) + "\n")
            f.write(encoded_line + "\n")

    except OSError as e:
        raise TSVInjectionError(f"Failed to append to bus file: {e}") from e


def sanitize_for_tsv(value: str) -> str:
    """Sanitize a string for safe TSV inclusion (legacy mode).

    Replaces tabs and newlines with spaces to prevent column/row injection.

    Args:
        value: String to sanitize.

    Returns:
        Sanitized string safe for TSV.
    """
    if not isinstance(value, str):
        value = str(value)
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
