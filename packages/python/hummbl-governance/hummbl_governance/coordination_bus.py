# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Coordination Bus -- Append-only TSV message bus with HMAC signing and policy levels.

Provides a thread-safe, flock-based message bus for multi-agent coordination.
Messages are append-only (no edits, no deletes) in 5-column TSV format:

    timestamp_utc\\tfrom\\tto\\ttype\\tmessage

Usage::

    from hummbl_governance.coordination_bus import BusWriter, sign_message, PolicyLevel

    bus = BusWriter("/path/to/messages.tsv")
    bus.post("agent-1", "all", "STATUS", "Starting task")

    msgs = bus.read_all()
    recent = bus.read_since("2026-03-20T00:00:00Z")

Stdlib-only. Cross-platform file locking uses ``fcntl`` on POSIX and
``msvcrt`` on Windows.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

from hummbl_governance._file_lock import acquire_file_lock, release_file_lock
from hummbl_governance._types import PolicyLevel

logger = logging.getLogger(__name__)

# Maximum message payload size (64 KB)
MAX_MESSAGE_BYTES = 65536

# Maximum structured fields in a JSON payload
MAX_PAYLOAD_FIELDS = 64


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def generate_secret(nbytes: int = 32) -> str:
    """Generate a cryptographically secure random secret (hex-encoded).

    Args:
        nbytes: Number of random bytes (default 32 = 256-bit key).

    Returns:
        Hex-encoded secret string.
    """
    return secrets.token_hex(nbytes)


def sign_message(payload: str, secret: str) -> str:
    """Sign a payload string with HMAC-SHA256.

    Args:
        payload: The string to sign (typically a TSV line without trailing newline).
        secret: The shared secret key.

    Returns:
        Hex-encoded HMAC-SHA256 digest.
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_message(payload: str, signature: str, secret: str) -> bool:
    """Verify an HMAC-SHA256 signature using constant-time comparison.

    Args:
        payload: The original payload string.
        signature: The hex-encoded signature to verify.
        secret: The shared secret key.

    Returns:
        True if the signature is valid, False otherwise.
    """
    expected = sign_message(payload, secret)
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Field sanitization
# ---------------------------------------------------------------------------


def _sanitize_field(value: str) -> str:
    """Sanitize a TSV field by stripping whitespace and replacing tabs/newlines.

    Ensures any field value is safe for inclusion in a single TSV column.
    """
    value = value.strip()
    value = value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    value = value.replace("\t", " ")
    return value


def _escape_message(message: str) -> str:
    r"""Escape newlines and tabs in message content for TSV safety.

    Converts:
    - Newlines (\\n, \\r\\n, \\r) to escaped literal \\n
    - Tabs (\\t) to spaces

    This ensures multiline message bodies become single-line TSV-safe payloads.
    """
    if not isinstance(message, str):
        message = str(message)
    message = message.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    message = message.replace("\t", " ")
    return message


def _normalize_timestamp(ts: str) -> str:
    """Normalize an ISO 8601 timestamp to UTC with Z suffix.

    Accepts timestamps with timezone offsets (e.g., ``-05:00``, ``+09:00``)
    and converts them to UTC.  Timestamps already ending in ``Z`` are
    returned unchanged (sub-second precision stripped for canonical format).
    """
    ts = ts.strip()

    # Already UTC -- fast path
    if ts.endswith("Z"):
        base = ts[:-1]
        if "." in base:
            base = base[: base.index(".")]
        return base + "Z"

    # Try parsing with timezone offset
    try:
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError):
        pass

    # Fallback: return as-is
    logger.warning("Could not normalize timestamp: %s", ts)
    return ts


def _check_nonempty_str(value: object, name: str) -> None:
    """Raise ValueError if value is not a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")


def _check_payload(message: str) -> None:
    """Validate message payload: size, null bytes, structured field count."""
    message_bytes = len(message.encode("utf-8"))
    if message_bytes > MAX_MESSAGE_BYTES:
        raise ValueError(f"message exceeds maximum size: {message_bytes} bytes > {MAX_MESSAGE_BYTES} bytes")
    if "\x00" in message:
        raise ValueError("message contains null bytes")

    stripped = message.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and len(parsed) > MAX_PAYLOAD_FIELDS:
                raise ValueError(f"structured payload has {len(parsed)} fields, max is {MAX_PAYLOAD_FIELDS}")
        except json.JSONDecodeError as exc:
            logger.debug("Structured payload parse failed, treating as plain string: %s", exc)


def _validate_fields(
    from_id: str, to_id: str, msg_type: str, message: str
) -> None:
    """Validate that required bus message fields are non-empty strings.

    Raises:
        ValueError: If any required field is empty, not a string,
            contains null bytes, or exceeds size limits.
    """
    for value, name in [(from_id, "from_id"), (to_id, "to_id"), (msg_type, "msg_type"), (message, "message")]:
        _check_nonempty_str(value, name)
    _check_payload(message)


# ---------------------------------------------------------------------------
# BusWriter
# ---------------------------------------------------------------------------


class BusWriter:
    """Append-only TSV message bus with file-level locking.

    Thread-safe: uses a threading.Lock for in-process safety and
    a platform-native stdlib lock for cross-process safety.

    Args:
        bus_path: Path to the TSV file. Parent directories are created
            automatically if they do not exist.
        policy: Security policy level (default PERMISSIVE).
    """

    def __init__(
        self,
        bus_path: str | Path,
        *,
        policy: PolicyLevel = PolicyLevel.PERMISSIVE,
    ):
        self._bus_path = Path(bus_path)
        self._policy = policy
        self._lock = threading.Lock()

    @property
    def bus_path(self) -> Path:
        """Path to the underlying TSV file."""
        return self._bus_path

    @property
    def policy(self) -> PolicyLevel:
        """Current security policy level."""
        return self._policy

    def post(
        self,
        from_id: str,
        to_id: str,
        msg_type: str,
        message: str,
        *,
        timestamp: str | None = None,
        validate: bool = True,
    ) -> None:
        """Append a message to the bus file.

        Uses a platform-native stdlib file lock for safe concurrent writes
        from multiple processes, plus a ``threading.Lock`` for in-process
        safety.

        Args:
            from_id: Sender identifier (e.g., ``"agent-1"``).
            to_id: Recipient identifier (e.g., ``"all"``).
            msg_type: Message type (e.g., ``"STATUS"``, ``"PROPOSAL"``).
            message: Message content. Tabs and newlines are escaped automatically.
            timestamp: Optional UTC timestamp (defaults to ``now()`` with ``Z`` suffix).
            validate: If True (default), validate fields before writing.

        Raises:
            ValueError: If ``validate=True`` and a required field is empty or invalid.
        """
        if validate:
            _validate_fields(from_id, to_id, msg_type, message)

        if timestamp is not None:
            ts = _normalize_timestamp(timestamp)
        else:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Sanitize header fields
        safe_from = _sanitize_field(from_id)
        safe_to = _sanitize_field(to_id)
        safe_type = _sanitize_field(msg_type)
        safe_message = _escape_message(message)

        line = "\t".join([ts, safe_from, safe_to, safe_type, safe_message]) + "\n"

        with self._lock:
            self._bus_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(self._bus_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            try:
                acquire_file_lock(fd)
                try:
                    os.write(fd, line.encode("utf-8"))
                finally:
                    release_file_lock(fd)
            finally:
                os.close(fd)

    def append(
        self,
        agent: str,
        action: str,
        resource: str,
        *,
        to_id: str = "all",
    ) -> None:
        """Convenience alias for post() with agent/action/resource signature.

        Matches the code examples shown on hummbl.io. Posts a LOG-type
        message encoding the agent, action, and resource as a structured
        log entry.

        Args:
            agent: Agent performing the action (maps to from_id).
            action: Action performed (e.g. "read", "summarize").
            resource: Resource accessed (e.g. "docs/report.md").
            to_id: Recipient (default "all").
        """
        self.post(
            from_id=agent,
            to_id=to_id,
            msg_type="LOG",
            message=f"{action}:{resource}",
        )

    def write(
        self,
        actor: str,
        action: str,
        scope: str,
        *,
        to_id: str = "all",
    ) -> None:
        """Convenience alias for post() with actor/action/scope signature.

        Matches the code examples shown on hummbl.io. Posts a LOG-type
        message encoding the actor, action, and scope.

        Args:
            actor: Agent performing the action (maps to from_id).
            action: Action performed.
            scope: Scope of the action.
            to_id: Recipient (default "all").
        """
        self.post(
            from_id=actor,
            to_id=to_id,
            msg_type="LOG",
            message=f"{action}:{scope}",
        )

    def read_all(self) -> list[dict[str, str]]:
        """Read all messages from the bus.

        Returns:
            List of dicts with keys: ``timestamp``, ``from``, ``to``,
            ``type``, ``message``.
        """
        if not self._bus_path.exists():
            return []

        messages: list[dict[str, str]] = []
        with open(self._bus_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n\r").split("\t")
                if len(parts) >= 5:
                    messages.append(
                        {
                            "timestamp": parts[0],
                            "from": parts[1],
                            "to": parts[2],
                            "type": parts[3],
                            "message": parts[4],
                        }
                    )
        return messages

    def read_since(self, since: str) -> list[dict[str, str]]:
        """Read messages posted at or after a given timestamp.

        Args:
            since: ISO 8601 UTC timestamp (e.g., ``"2026-03-20T00:00:00Z"``).
                Normalized before comparison.

        Returns:
            List of message dicts whose timestamp >= ``since``.
        """
        cutoff = _normalize_timestamp(since)
        return [m for m in self.read_all() if m["timestamp"] >= cutoff]

    def message_count(self) -> int:
        """Return the number of messages currently on the bus.

        Returns 0 if the bus file does not exist.
        """
        if not self._bus_path.exists():
            return 0

        count = 0
        with open(self._bus_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n\r").split("\t")
                if len(parts) >= 5:
                    count += 1
        return count
