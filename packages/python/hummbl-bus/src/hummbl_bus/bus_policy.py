"""Bus security policy enforcement for ASI07 (Insecure Inter-Agent Communication).

Implements configurable enforcement levels for message signing on the
coordination bus, addressing OWASP Agentic Top 10 ASI07.

Policy levels:
    PERMISSIVE  -- Accept unsigned messages silently (backward compat default)
    WARN        -- Accept unsigned but log a warning per message
    STRICT      -- Reject unsigned messages with ValueError

Configure via:
    - Environment variable: BUS_SECURITY_POLICY=permissive|warn|strict
    - Direct instantiation: BusSecurityPolicy(level="strict")

This module is stdlib-only and has no side effects on import.
"""

from __future__ import annotations

import logging
import os
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyLevel(Enum):
    """Bus security enforcement level."""

    PERMISSIVE = "permissive"
    WARN = "warn"
    STRICT = "strict"


class BusSecurityPolicy:
    """Configurable security policy for coordination bus messages.

    Controls whether unsigned messages are accepted, warned about, or
    rejected. Designed to be wired into ``post_message()`` with zero
    behavioral change at the default PERMISSIVE level.

    Parameters
    ----------
    level : str or PolicyLevel
        Enforcement level (permissive, warn, strict).
    allow_unsigned_types : set[str] | None
        Message types exempt from signing requirements even in STRICT mode.
        Defaults to {"HEARTBEAT"} since heartbeats are high-frequency
        and low-sensitivity.

    Example:
    -------
    >>> policy = BusSecurityPolicy(level="warn")
    >>> policy.check_signing(secret=None, from_id="agent-a", msg_type="STATUS")
    # Logs warning: "Unsigned bus message from agent-a (type=STATUS)"
    """

    def __init__(
        self,
        level: str | PolicyLevel | None = None,
        allow_unsigned_types: set[str] | None = None,
    ):
        if level is None:
            level = os.environ.get("BUS_SECURITY_POLICY", "permissive")

        if isinstance(level, str):
            try:
                self.level = PolicyLevel(level.lower())
            except ValueError:
                logger.warning(
                    "Invalid BUS_SECURITY_POLICY=%r, defaulting to permissive",
                    level,
                )
                self.level = PolicyLevel.PERMISSIVE
        else:
            self.level = level

        self.allow_unsigned_types = allow_unsigned_types or {"HEARTBEAT"}

    def check_signing(
        self,
        *,
        secret: bytes | None,
        from_id: str,
        msg_type: str,
    ) -> None:
        """Check whether an unsigned message should be accepted.

        Called by ``post_message()`` before writing. If the message is
        signed (secret is not None), this is a no-op at all levels.

        Parameters
        ----------
        secret : bytes | None
            The signing secret. None means the message is unsigned.
        from_id : str
            Sender identity for logging/error context.
        msg_type : str
            Message type (checked against allow_unsigned_types).

        Raises:
        ------
        ValueError
            In STRICT mode when secret is None and msg_type is not exempt.
        """
        # Signed messages always pass
        if secret is not None:
            return

        # Exempt types always pass
        if msg_type.strip().upper() in self.allow_unsigned_types:
            return

        if self.level == PolicyLevel.PERMISSIVE:
            return

        if self.level == PolicyLevel.WARN:
            logger.warning(
                "Unsigned bus message from %s (type=%s) -- "
                "set BUS_SECURITY_POLICY=strict to enforce signing",
                from_id,
                msg_type,
            )
            return

        if self.level == PolicyLevel.STRICT:
            raise ValueError(
                f"Bus security policy STRICT: unsigned message rejected "
                f"from {from_id} (type={msg_type}). "
                f"Provide a signing secret via --sign or --secret-file."
            )


# Module singleton -- lazy-initialized from env var
_default_policy: BusSecurityPolicy | None = None


def get_bus_policy() -> BusSecurityPolicy:
    """Get the default bus security policy (singleton).

    Reads BUS_SECURITY_POLICY env var on first call. Thread-safe via
    Python's GIL for simple attribute assignment.

    Returns:
    -------
    BusSecurityPolicy
        Shared policy instance.
    """
    global _default_policy
    if _default_policy is None:
        _default_policy = BusSecurityPolicy()
    return _default_policy


def reset_bus_policy() -> None:
    """Reset the singleton policy (for testing)."""
    global _default_policy
    _default_policy = None
