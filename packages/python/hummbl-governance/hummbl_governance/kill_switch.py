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

"""Kill Switch -- Emergency halt system with graduated response.

Four modes:
    DISENGAGED: Normal operation.
    HALT_NONCRITICAL: Queue non-critical tasks, continue critical.
    HALT_ALL: Stop all new work, complete in-flight.
    EMERGENCY: Immediate halt, preserve state.

Usage:
    from hummbl_governance import KillSwitch, KillSwitchMode, KillSwitchReason

    ks = KillSwitch()
    ks.engage(
        KillSwitchMode.HALT_ALL,
        reason="Budget exceeded",
        triggered_by="cost_governor",
        failure_class=KillSwitchReason.BUDGET,
    )

    result = ks.check_task_allowed("briefing_generation")
    if not result["allowed"]:
        raise KillSwitchEngagedError(result["reason"])

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from hummbl_governance._types import KillSwitchMode, KillSwitchReason

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KillSwitchEvent:
    """Record of a kill switch state change."""

    timestamp: str
    mode: KillSwitchMode
    reason: str
    triggered_by: str
    affected_tasks: int = 0
    failure_class: KillSwitchReason | None = None


class KillSwitchEngagedError(Exception):
    """Raised when an operation is blocked by an engaged kill switch."""

    def __init__(self, reason: str, mode: KillSwitchMode | None = None):
        self.reason = reason
        self.mode = mode
        super().__init__(f"Kill switch engaged: {reason}")


class KillSwitchTamperError(Exception):
    """Raised when kill switch state file fails integrity verification."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Kill switch tamper detected: {reason}")


class KillSwitch:
    """Emergency halt system with graduated response.

    Features:
        - Four engagement levels (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY)
        - Configurable critical task exemptions
        - Event history with optional persistence
        - Subscriber notifications for state changes
        - Optional HMAC integrity verification for persisted state
        - Thread-safe (RLock)

    Args:
        state_dir: Directory for persistent state. None disables persistence.
            When set, persisted ``kill_switch_state.json`` is restored on
            construction so an engaged halt survives process restart.
        require_hmac: If True, HMAC verification is mandatory for loading state
            when a signing secret is available.
        signing_secret: HMAC secret bytes. If None, reads from HUMMBL_SIGNING_SECRET
            or DCT_SECRET env vars.
        critical_tasks: Set of task types that are always allowed in HALT_NONCRITICAL
            and HALT_ALL modes. Defaults to common safety tasks.

    Examples:
        >>> ks = KillSwitch()
        >>> ks.mode
        <KillSwitchMode.DISENGAGED: 1>
        >>> ks.engaged
        False

        With persistent state and a custom critical-tasks set (empty dir):

        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as d:
        ...     ks = KillSwitch(state_dir=Path(d), require_hmac=False)
        ...     ks.mode
        <KillSwitchMode.DISENGAGED: 1>
    """

    DEFAULT_CRITICAL_TASKS: frozenset[str] = frozenset(
        [
            "safety_monitoring",
            "data_persistence",
            "audit_logging",
            "kill_switch_itself",
            "cost_tracking",
        ]
    )

    def __init__(
        self,
        state_dir: Path | None = None,
        require_hmac: bool = True,
        signing_secret: bytes | None = None,
        critical_tasks: frozenset[str] | None = None,
    ):
        self._mode = KillSwitchMode.DISENGAGED
        self._history: list[KillSwitchEvent] = []
        self._subscribers: list[Callable[[KillSwitchEvent], None]] = []
        self._state_dir = state_dir
        self._require_hmac = require_hmac
        self._signing_secret = signing_secret
        self._critical_tasks = critical_tasks or self.DEFAULT_CRITICAL_TASKS
        self._lock = threading.RLock()
        if self._state_dir is not None:
            self._restore_from_disk()

    @property
    def mode(self) -> KillSwitchMode:
        """Current kill switch mode."""
        return self._mode

    @property
    def engaged(self) -> bool:
        """True if kill switch is engaged (not DISENGAGED)."""
        return self._mode != KillSwitchMode.DISENGAGED

    @property
    def critical_tasks(self) -> frozenset[str]:
        """Set of critical task types that bypass non-emergency modes."""
        return self._critical_tasks

    def _get_signing_secret(self) -> bytes | None:
        """Get HMAC signing secret from instance or environment."""
        if self._signing_secret:
            return self._signing_secret
        for var in ("HUMMBL_SIGNING_SECRET", "DCT_SECRET"):
            secret = os.environ.get(var)
            if secret:
                return secret.encode("utf-8")
        return None

    @staticmethod
    def _compute_signature(data: dict[str, Any], secret: bytes) -> str:
        """Compute HMAC-SHA256 signature over state payload."""
        canonical = json.dumps(data, separators=(",", ":"), sort_keys=True)
        mac = hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256)
        return mac.hexdigest()

    @staticmethod
    def _verify_signature(data: dict[str, Any], signature: str, secret: bytes) -> bool:
        """Verify HMAC-SHA256 signature of persisted state."""
        expected = KillSwitch._compute_signature(data, secret)
        return hmac.compare_digest(expected, signature)

    def _restore_from_disk(self) -> None:
        """Restore mode from ``kill_switch_state.json`` if present.

        Missing file leaves the instance DISENGAGED. Invalid HMAC (when a
        signing secret is configured) raises ``KillSwitchTamperError`` if
        ``require_hmac`` is True, otherwise leaves the instance DISENGAGED.
        Unsigned state is restored when no signing secret is available —
        HMAC cannot be enforced without a key, and refusing to load would
        silently drop an emergency halt across process restart.
        """
        if self._state_dir is None:
            return

        state_file = self._state_dir / "kill_switch_state.json"
        if not state_file.exists():
            return

        try:
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)

            secret = self._get_signing_secret()
            signature = data.pop("signature", None)

            if secret and signature:
                if not self._verify_signature(data, signature, secret):
                    logger.error("Kill switch state has INVALID HMAC signature")
                    if self._require_hmac:
                        raise KillSwitchTamperError("Kill switch state verification failed")
                    return
            elif secret:
                logger.error("Kill switch state lacks required HMAC signature")
                if self._require_hmac:
                    raise KillSwitchTamperError(
                        "Kill switch state missing mandatory HMAC signature"
                    )
                logger.warning("Kill switch state has no signature (legacy mode)")
            elif signature:
                logger.error(
                    "Kill switch state has an HMAC signature but no signing secret "
                    "is configured; cannot verify integrity"
                )
                if self._require_hmac:
                    raise KillSwitchTamperError(
                        "Kill switch state missing mandatory HMAC signature"
                    )
                logger.warning("Kill switch state has no signature (legacy mode)")
            else:
                if self._require_hmac:
                    logger.error(
                        "Kill switch state is unsigned and no signing secret is "
                        "configured; restoring persisted mode without HMAC"
                    )
                else:
                    logger.warning("Kill switch state has no signature (legacy mode)")

            mode_str = data.get("mode", "DISENGAGED")
            self._mode = KillSwitchMode[mode_str]

            failure_class = None
            fc_str = data.get("failure_class")
            if fc_str:
                try:
                    failure_class = KillSwitchReason[fc_str]
                except KeyError:
                    logger.warning("Unknown failure_class in state file: %s", fc_str)

            if self._mode != KillSwitchMode.DISENGAGED:
                event = KillSwitchEvent(
                    timestamp=data.get("engaged_at", datetime.now(timezone.utc).isoformat()),
                    mode=self._mode,
                    reason=data.get("reason", "Restored from file"),
                    triggered_by=data.get("triggered_by", "system"),
                    affected_tasks=0,
                    failure_class=failure_class,
                )
                self._history.append(event)
        except KillSwitchTamperError:
            raise
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.error("Kill switch state file corrupt: %s", e)
            if self._require_hmac:
                raise KillSwitchTamperError(f"Kill switch state file corrupt: {e}") from e

    @classmethod
    def load_from_file(
        cls,
        state_dir: Path,
        require_hmac: bool = True,
        signing_secret: bytes | None = None,
        critical_tasks: frozenset[str] | None = None,
    ) -> KillSwitch:
        """Load kill switch state from persistent storage.

        Returns a fresh DISENGAGED instance if file is missing or corrupt
        (when ``require_hmac`` is False). Construction with ``state_dir``
        also restores persisted state; this classmethod remains the explicit
        production boot API.

        Raises:
            KillSwitchTamperError: If require_hmac=True and signature is invalid,
                or a signing secret is configured but the file is unsigned/corrupt.
        """
        return cls(
            state_dir=state_dir,
            require_hmac=require_hmac,
            signing_secret=signing_secret,
            critical_tasks=critical_tasks,
        )

    def subscribe(self, callback: Callable[[KillSwitchEvent], None]) -> None:
        """Subscribe to kill switch state changes."""
        self._subscribers.append(callback)

    def _build_state_data(self) -> dict[str, Any]:
        """Build state dict from current mode and last event."""
        last_event = self._history[-1] if self._history else None
        data: dict[str, Any] = {
            "mode": self._mode.name,
            "engaged_at": last_event.timestamp if last_event else None,
            "reason": last_event.reason if last_event else None,
            "triggered_by": last_event.triggered_by if last_event else None,
        }
        if last_event and last_event.failure_class is not None:
            data["failure_class"] = last_event.failure_class.name
        secret = self._get_signing_secret()
        if secret:
            data["signature"] = self._compute_signature({k: v for k, v in data.items() if k != "signature"}, secret)
        elif self._require_hmac:
            logger.error("Signing secret not available but require_hmac=True")
        return data

    def _persist(self) -> None:
        """Persist current state to file if state_dir is configured."""
        if self._state_dir is None:
            return

        state_file = self._state_dir / "kill_switch_state.json"
        self._state_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(self._build_state_data(), f, indent=2)
            state_file.chmod(0o600)
        except OSError as e:
            logger.error("Failed to persist kill switch state: %s", e)

    def _notify(self, event: KillSwitchEvent) -> None:
        """Notify subscribers of state change."""
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception:
                logger.debug("Kill switch subscriber callback failed", exc_info=True)
                continue

    def engage(
        self,
        mode: KillSwitchMode,
        reason: str,
        triggered_by: str,
        affected_tasks: int = 0,
        failure_class: KillSwitchReason | None = None,
    ) -> KillSwitchEvent:
        """Engage the kill switch.

        Args:
            mode: Engagement level (must not be DISENGAGED).
            reason: Human-readable explanation.
            triggered_by: Component or user triggering engagement.
            affected_tasks: Estimated number of tasks affected.
            failure_class: Machine-actionable failure classification
                (Phase 1 — optional, defaults to None for backward compatibility).
                See ``KillSwitchReason`` enum for the 15 standard values.

        Returns:
            KillSwitchEvent record.

        Raises:
            ValueError: If mode is DISENGAGED.

        Examples:
            >>> ks = KillSwitch()
            >>> event = ks.engage(
            ...     KillSwitchMode.HALT_ALL,
            ...     reason="Budget exceeded",
            ...     triggered_by="cost_governor",
            ...     failure_class=KillSwitchReason.BUDGET,
            ... )
            >>> event.mode
            <KillSwitchMode.HALT_ALL: 3>
            >>> event.failure_class
            <KillSwitchReason.BUDGET: 'budget'>
            >>> ks.engaged
            True
        """
        if mode == KillSwitchMode.DISENGAGED:
            raise ValueError("Use disengage() to clear kill switch, not engage()")

        with self._lock:
            self._mode = mode
            event = KillSwitchEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                mode=mode,
                reason=reason,
                triggered_by=triggered_by,
                affected_tasks=affected_tasks,
                failure_class=failure_class,
            )
            self._history.append(event)
            self._notify(event)
            self._persist()
            return event

    def disengage(self, triggered_by: str, reason: str | None = None) -> KillSwitchEvent:
        """Disengage the kill switch.

        Returns:
            KillSwitchEvent record.

        Examples:
            >>> ks = KillSwitch()
            >>> _ = ks.engage(KillSwitchMode.HALT_ALL, reason="Over budget", triggered_by="monitor")
            >>> event = ks.disengage(triggered_by="operator", reason="Budget restored")
            >>> ks.engaged
            False
            >>> event.mode
            <KillSwitchMode.DISENGAGED: 1>
        """
        with self._lock:
            previous_mode = self._mode
            self._mode = KillSwitchMode.DISENGAGED

            disengage_reason = reason or f"Disengaged from {previous_mode.name}"
            event = KillSwitchEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                mode=KillSwitchMode.DISENGAGED,
                reason=disengage_reason,
                triggered_by=triggered_by,
                affected_tasks=0,
            )
            self._history.append(event)
            self._notify(event)
            self._persist()
            return event

    def check_task_allowed(self, task_type: str) -> dict[str, Any]:
        """Check if a task is allowed under current kill switch mode.

        Returns:
            Dict with 'allowed' (bool), 'action' (str), and optionally
            'reason' or 'note'.
        """
        with self._lock:
            is_critical = task_type in self._critical_tasks
            current_mode = self._mode

            if current_mode == KillSwitchMode.DISENGAGED:
                return {"allowed": True, "action": "allow"}

            if current_mode == KillSwitchMode.HALT_NONCRITICAL:
                if is_critical:
                    return {"allowed": True, "action": "allow", "note": "critical task exempted"}
                return {
                    "allowed": False,
                    "action": "queue",
                    "reason": f"Kill switch engaged ({current_mode.name}): {task_type} queued",
                }

            if current_mode in (KillSwitchMode.HALT_ALL, KillSwitchMode.EMERGENCY):
                if is_critical and current_mode == KillSwitchMode.HALT_ALL:
                    return {"allowed": True, "action": "allow", "note": "critical only"}
                return {
                    "allowed": False,
                    "action": "block",
                    "reason": f"Kill switch engaged ({current_mode.name}): {task_type} blocked",
                }

            return {"allowed": False, "action": "block", "reason": "Unknown kill switch state"}

    def check_or_raise(self, task_type: str) -> None:
        """Check task and raise KillSwitchEngagedError if not allowed."""
        result = self.check_task_allowed(task_type)
        if not result["allowed"]:
            raise KillSwitchEngagedError(result["reason"], self._mode)

    def get_status(self) -> dict[str, Any]:
        """Get current kill switch status summary.

        Returns:
            Dict with mode, engaged flag, engagement_count, last_engagement, and total_events.

        Examples:
            >>> ks = KillSwitch()
            >>> status = ks.get_status()
            >>> status['mode']
            'DISENGAGED'
            >>> status['engaged']
            False
            >>> status['engagement_count']
            0
        """
        engagement_count = len([e for e in self._history if e.mode != KillSwitchMode.DISENGAGED])

        last_engagement = None
        for event in reversed(self._history):
            if event.mode != KillSwitchMode.DISENGAGED:
                last_engagement = {
                    "timestamp": event.timestamp,
                    "mode": event.mode.name,
                    "reason": event.reason,
                    "triggered_by": event.triggered_by,
                }
                if event.failure_class is not None:
                    last_engagement["failure_class"] = event.failure_class.name
                break

        return {
            "mode": self._mode.name,
            "engaged": self.engaged,
            "engagement_count": engagement_count,
            "last_engagement": last_engagement,
            "total_events": len(self._history),
        }

    def get_history(
        self,
        limit: int | None = None,
        engaged_only: bool = False,
    ) -> list[KillSwitchEvent]:
        """Get kill switch event history."""
        events = self._history.copy()
        if engaged_only:
            events = [e for e in events if e.mode != KillSwitchMode.DISENGAGED]
        if limit:
            events = events[-limit:]
        return events
