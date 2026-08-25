"""Bus integration mixin for adapters.

Provides coordination bus publishing capabilities for all adapters,
enabling health monitoring, status updates, and participation in
the multi-agent ecosystem.

All writes go through the canonical bus_writer.post_message() path,
ensuring consistent 5-column TSV format with fcntl locking.

ASI07 Hardening (2026-03-01):
    Safety-critical reads (_check_kill_switch, _check_circuit_breaker)
    now verify message signatures when BUS_SIGNING_SECRET is set and
    BUS_SAFETY_VERIFY_SIGNATURES is true.

Extracted from hummbl-governance. The following external import was removed:
    - hummbl_governance.integrations.base (HealthCheckResult, HealthStatus)
Health monitoring features (BusHealthMonitor, _publish_health_check)
require HealthCheckResult/HealthStatus to be provided by the consumer.

Usage:
    from hummbl_bus.bus_integration import BusIntegrationMixin

    class MyAdapter(BusIntegrationMixin):
        def __init__(self):
            super().__init__()
            self._init_bus_integration("my_adapter")
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .bus_writer import (
    post_message,
    read_verified_messages,
)

logger = logging.getLogger(__name__)


def _read_recent_bus_entries(
    bus_path: str | Path,
    since_minutes: int = 5,
) -> list[dict[str, str]]:
    """Read recent bus entries from the canonical 5-column TSV bus.

    Args:
        bus_path: Path to messages.tsv file
        since_minutes: How far back to look

    Returns:
        List of dicts with keys: timestamp, sender, recipient, msg_type, message
    """
    path = Path(bus_path)
    if not path.exists():
        return []

    cutoff = datetime.now(UTC) - timedelta(minutes=since_minutes)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 5:
                    continue
                ts, sender, recipient, msg_type, message = parts
                if ts >= cutoff_str:
                    entries.append(
                        {
                            "timestamp": ts,
                            "sender": sender,
                            "recipient": recipient,
                            "msg_type": msg_type,
                            "message": message,
                        }
                    )
    except OSError:
        pass

    return entries


class BusIntegrationMixin:
    """Mixin providing coordination bus integration for adapters.

    All writes go through bus_writer.post_message() for consistent
    5-column TSV format with fcntl locking.

    Attributes:
    ----------
    bus_identity : str
        Identity string for bus messages
    bus_enabled : bool
        Whether bus integration is active
    """

    def __init__(self):
        """Initialize the mixin."""
        self._bus_path: str = ""
        self.bus_identity: str = ""
        self.bus_enabled: bool = False
        self._circuit_breakers: dict[str, bool] = {}  # service -> is_open
        self._kill_switch_status: str | None = None

    def _init_bus_integration(
        self,
        identity: str,
        bus_path: str = "_state/coordination/messages.tsv",
    ) -> bool:
        """Initialize bus integration.

        Parameters
        ----------
        identity : str
            Identity string for this adapter (e.g., "llm_adapter")
        bus_path : str
            Path to the coordination bus TSV file

        Returns:
        -------
        bool
            True if bus integration initialized successfully
        """
        try:
            self._bus_path = bus_path
            self.bus_identity = identity
            self.bus_enabled = True

            # Publish initial status
            self._publish_status("initialized", {})

            logger.info(f"Bus integration initialized for {identity}")
            return True

        except Exception as e:
            logger.warning(f"Could not initialize bus integration: {e}")
            self.bus_enabled = False
            return False

    def _publish_status(
        self,
        status: str,
        details: dict[str, Any],
    ) -> bool:
        """Publish status update to the bus.

        Parameters
        ----------
        status : str
            Status string (e.g., "ready", "busy", "error")
        details : dict
            Additional status details

        Returns:
        -------
        bool
            True if published successfully
        """
        if not self.bus_enabled:
            return False

        try:
            payload = json.dumps(
                {
                    "status": status,
                    **details,
                },
                separators=(",", ":"),
                sort_keys=True,
            )

            post_message(
                bus_path=self._bus_path,
                from_id=self.bus_identity,
                to_id="all",
                msg_type="STATUS",
                message=payload,
            )

            return True

        except Exception as e:
            logger.warning(f"Could not publish status: {e}")
            return False

    def _publish_task_complete(
        self,
        task_name: str,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Publish task completion to the bus.

        Parameters
        ----------
        task_name : str
            Name of the completed task
        success : bool
            Whether the task succeeded
        details : dict, optional
            Additional completion details

        Returns:
        -------
        bool
            True if published successfully
        """
        if not self.bus_enabled:
            return False

        try:
            payload = json.dumps(
                {
                    "task": task_name,
                    "success": success,
                    **(details or {}),
                },
                separators=(",", ":"),
                sort_keys=True,
            )

            msg_type = "COMPLETE" if success else "ERROR"

            post_message(
                bus_path=self._bus_path,
                from_id=self.bus_identity,
                to_id="all",
                msg_type=msg_type,
                message=payload,
            )

            return True

        except Exception as e:
            logger.warning(f"Could not publish task completion: {e}")
            return False

    def _check_circuit_breaker(self, service: str) -> bool:
        """Check if circuit breaker allows operation.

        ASI07 Hardening: When ``BUS_SAFETY_VERIFY_SIGNATURES=true`` is set
        and a signing secret is available, only signature-verified SAFETY
        messages are trusted for circuit breaker state.

        Parameters
        ----------
        service : str
            Service name (e.g., "github", "calendar", "signal")

        Returns:
        -------
        bool
            True if circuit is closed (operation allowed)
        """
        if not self.bus_enabled:
            return True  # Default to allowing if bus unavailable

        try:
            verify_safety = os.environ.get(
                "BUS_SAFETY_VERIFY_SIGNATURES", ""
            ).lower() in ("true", "1", "yes")

            if verify_safety:
                entries = read_verified_messages(
                    self._bus_path,
                    msg_type_filter="SAFETY",
                    since_minutes=5,
                    require_signature=True,
                )
            else:
                entries = _read_recent_bus_entries(
                    self._bus_path,
                    since_minutes=5,
                )

            for entry in entries:
                if (
                    entry["msg_type"] == "SAFETY"
                    and "CircuitBreaker" in entry["message"]
                ):
                    payload_str = entry["message"]
                    if f"CircuitBreaker {service}" in payload_str:
                        if "OPEN" in payload_str:
                            self._circuit_breakers[service] = True
                            return False
                        elif "CLOSED" in payload_str:
                            self._circuit_breakers[service] = False

            return not self._circuit_breakers.get(service, False)

        except Exception as e:
            logger.warning(f"Could not check circuit breaker: {e}")
            return True  # Default to allowing on error

    def _check_kill_switch(self) -> str | None:
        """Check kill switch status from the coordination bus.

        ASI07 Hardening: When ``BUS_SAFETY_VERIFY_SIGNATURES=true`` is set
        and a signing secret is available, only signature-verified SAFETY
        messages are trusted.

        Returns:
        -------
        str | None
            Kill switch status string (e.g., "HALT_NONCRITICAL", "HALT_ALL")
            or None if no kill switch active
        """
        if not self.bus_enabled:
            return None

        try:
            # ASI07: Use verified reads for safety-critical messages
            verify_safety = os.environ.get(
                "BUS_SAFETY_VERIFY_SIGNATURES", ""
            ).lower() in ("true", "1", "yes")

            if verify_safety:
                entries = read_verified_messages(
                    self._bus_path,
                    msg_type_filter="SAFETY",
                    since_minutes=5,
                    require_signature=True,
                )
            else:
                entries = _read_recent_bus_entries(
                    self._bus_path,
                    since_minutes=5,
                )
                entries = [e for e in entries if e["msg_type"] == "SAFETY"]

            latest_kill_switch = None

            for entry in reversed(entries):  # Check newest first
                msg = entry["message"]

                if "Kill switch engaged" in msg:
                    if "HALT_ALL" in msg:
                        return "HALT_ALL"
                    elif "HALT_NONCRITICAL" in msg:
                        latest_kill_switch = "HALT_NONCRITICAL"
                elif "Kill switch disengaged" in msg:
                    # Kill switch was turned off
                    return None

            return latest_kill_switch

        except Exception as e:
            logger.warning(f"Could not check kill switch: {e}")
            return None

    def _is_operation_allowed(
        self, service: str = "default"
    ) -> tuple[bool, str | None]:
        """Check if operation is allowed (circuit breaker + kill switch).

        Parameters
        ----------
        service : str
            Service to check circuit breaker for

        Returns:
        -------
        tuple[bool, str | None]
            (allowed, reason) - reason is None if allowed, otherwise explains why not
        """
        # Check kill switch first
        kill_switch = self._check_kill_switch()
        if kill_switch == "HALT_ALL":
            return False, f"Kill switch {kill_switch} is active"

        # Check circuit breaker
        if not self._check_circuit_breaker(service):
            return False, f"Circuit breaker OPEN for {service}"

        return True, None

    def _enforce_safety(self, service: str = "default") -> None:
        """Enforce safety checks, raising exception if operation not allowed.

        Parameters
        ----------
        service : str
            Service to check

        Raises:
        ------
        BusSafetyError
            If operation is not allowed
        """
        allowed, reason = self._is_operation_allowed(service)
        if not allowed:
            raise BusSafetyError(f"Operation blocked: {reason}")


class BusSafetyError(Exception):
    """Raised when bus safety checks prevent operation."""
