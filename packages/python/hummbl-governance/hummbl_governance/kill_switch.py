# Copyright 2024-2026 HUMMBL
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
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, ClassVar
from uuid import uuid4

from hummbl_governance._file_lock import acquire_file_lock, release_file_lock

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
    event_id: str = field(default_factory=lambda: uuid4().hex)
    requested_by: str | None = None


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


class KillSwitchConfigurationError(RuntimeError):
    """Required signing credentials are unavailable."""


class KillSwitchPersistenceError(RuntimeError):
    """A state transition could not be committed to authoritative storage."""


class KillSwitchAuthorizationError(PermissionError):
    """Release was not authenticated, confirmed, or bound to the current halt."""


@dataclass(frozen=True)
class OperatorReleaseAuthority:
    """Trusted startup configuration for a separate operator control process.

    ``credential_verifier`` is a salted, versioned PBKDF2 verifier for a separate
    operator credential, NOT the state-signing secret or general API token.
    ``operator_id`` is the identity associated with that credential by the
    deployer. Never construct this authority from agent input or expose its
    credential to agents. This is not a same-process sandbox.
    """

    operator_id: str
    credential_verifier: str = field(repr=False)
    _FORMAT: ClassVar[str] = "pbkdf2-sha256-v1"
    _ITERATIONS: ClassVar[int] = 600_000
    _MAX_CREDENTIAL_BYTES: ClassVar[int] = 1024

    def __post_init__(self) -> None:
        if not isinstance(self.operator_id, str) or not self.operator_id.strip():
            raise ValueError("A configured operator identity is required")
        self._parse_verifier()

    def _parse_verifier(self) -> tuple[bytes, bytes]:
        verifier = self.credential_verifier
        # Bound parsing before splitting; no caller-selected KDF or work factor.
        if not isinstance(verifier, str) or len(verifier) != 121:
            raise ValueError("A supported operator credential verifier is required")
        parts = verifier.split("$")
        if (len(parts) != 4 or parts[:2] != [self._FORMAT, str(self._ITERATIONS)]
                or len(parts[2]) != 32 or len(parts[3]) != 64
                or any(c not in "0123456789abcdef" for c in parts[2] + parts[3])):
            raise ValueError("Invalid operator credential verifier")
        return bytes.fromhex(parts[2]), bytes.fromhex(parts[3])

    @classmethod
    def _credential_bytes(cls, credential: str) -> bytes:
        if not isinstance(credential, str) or not credential or len(credential) > cls._MAX_CREDENTIAL_BYTES:
            raise ValueError("Operator credential must contain 1 to 1024 UTF-8 bytes")
        try:
            encoded = credential.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("Invalid operator credential encoding") from exc
        if len(encoded) > cls._MAX_CREDENTIAL_BYTES:
            raise ValueError("Operator credential must contain 1 to 1024 UTF-8 bytes")
        return encoded

    @classmethod
    def create_verifier(cls, credential: str) -> str:
        """Provision in a trusted operator process; protect the returned config.

        Use a long random credential from the operator's secret store. The
        salted KDF additionally slows offline guessing of weaker supplied values.
        """
        encoded = cls._credential_bytes(credential)
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", encoded, salt, cls._ITERATIONS, dklen=32)
        return f"{cls._FORMAT}${cls._ITERATIONS}${salt.hex()}${digest.hex()}"

    def authenticate(self, credential: str | None) -> str:
        try:
            encoded = self._credential_bytes(credential)
        except ValueError as exc:
            raise KillSwitchAuthorizationError("Operator authentication required") from exc
        salt, expected = self._parse_verifier()
        digest = hashlib.pbkdf2_hmac("sha256", encoded, salt, self._ITERATIONS, dklen=32)
        if not hmac.compare_digest(digest, expected):
            raise KillSwitchAuthorizationError("Operator authentication failed")
        return self.operator_id


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
        require_hmac: If True, HMAC verification is mandatory for loading state.
        signing_secret: HMAC secret bytes. If None, reads from HUMMBL_SIGNING_SECRET
            or DCT_SECRET env vars.
        critical_tasks: Set of task types that are always allowed in HALT_NONCRITICAL
            and HALT_ALL modes. Defaults to common safety tasks.
        release_authority: Trusted operator verifier; None denies every release.
            Configure only in a separate protected operator control process.

    Examples:
        >>> ks = KillSwitch()
        >>> ks.mode
        <KillSwitchMode.DISENGAGED: 1>
        >>> ks.engaged
        False

        With persistent state and a custom critical-tasks set:

        >>> from pathlib import Path
        >>> ks = KillSwitch(state_dir=Path("/tmp/ks"), require_hmac=False)
        >>> ks.mode
        <KillSwitchMode.DISENGAGED: 1>
    """

    # Facades use this capability to reject unsafe installed legacy cores.
    RELEASE_AUTHORIZATION_VERSION = 1
    AUTHORITATIVE_READS_VERSION = 1

    DEFAULT_CRITICAL_TASKS: frozenset[str] = frozenset([
        "safety_monitoring",
        "data_persistence",
        "audit_logging",
        "kill_switch_itself",
        "cost_tracking",
    ])

    def __init__(
        self,
        state_dir: Path | None = None,
        require_hmac: bool = True,
        signing_secret: bytes | None = None,
        critical_tasks: frozenset[str] | None = None,
        *,
        release_authority: OperatorReleaseAuthority | None = None,
    ):
        self._mode = KillSwitchMode.DISENGAGED
        self._history: list[KillSwitchEvent] = []
        self._subscribers: list[Callable[[KillSwitchEvent], None]] = []
        self._state_dir = state_dir
        self._require_hmac = require_hmac
        self._signing_secret = signing_secret
        self._release_authority = release_authority
        self._critical_tasks = critical_tasks or self.DEFAULT_CRITICAL_TASKS
        self._lock = threading.RLock()
        self._authoritative_reads = False
        self._persistence_failed = False

    @property
    def mode(self) -> KillSwitchMode:
        """Current kill switch mode (thread-safe read)."""
        with self._lock:
            self._prepare_read()
            return self._mode

    @property
    def engaged(self) -> bool:
        """True if kill switch is engaged (not DISENGAGED)."""
        return self.mode != KillSwitchMode.DISENGAGED

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

    def _require_signing_secret(self) -> bytes:
        """Resolve credentials without generating, caching, or weakening them."""
        secret = self._get_signing_secret()
        if not secret:
            raise KillSwitchConfigurationError(
                "Signing secret required: configure HUMMBL_SIGNING_SECRET or DCT_SECRET"
            )
        return secret

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

    @classmethod
    def load_from_file(
        cls,
        state_dir: Path,
        require_hmac: bool = True,
        signing_secret: bytes | None = None,
        critical_tasks: frozenset[str] | None = None,
        *,
        require_existing: bool = False,
        authoritative_reads: bool = False,
        release_authority: OperatorReleaseAuthority | None = None,
    ) -> KillSwitch:
        """Load kill switch state from persistent storage.

        Missing files return a fresh instance only when require_existing=False.
        Strict readers use require_existing=True: absence cannot clear a halt.
        Corrupt files raise when require_hmac=True. ``authoritative_reads=True``
        requires HMAC and existing state, then re-verifies before every mode,
        status, history and task decision, including through retained references.

        Raises:
            KillSwitchTamperError: If require_hmac=True and signature is invalid/missing.
        """
        if authoritative_reads and not require_hmac:
            raise ValueError("Authoritative reads require HMAC verification")
        state_file = state_dir / "kill_switch_state.json"
        ks = cls(
            state_dir=state_dir,
            require_hmac=require_hmac,
            signing_secret=signing_secret,
            critical_tasks=critical_tasks,
            release_authority=release_authority,
        )
        ks._authoritative_reads = authoritative_reads
        if authoritative_reads:
            ks._require_signing_secret()

        try:
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("State must be a JSON object")

            secret = ks._get_signing_secret()
            signature = data.pop("signature", None)

            if signature is not None and not isinstance(signature, str):
                raise ValueError("State signature must be a string")

            if secret and signature:
                if not cls._verify_signature(data, signature, secret):
                    logger.error("Kill switch state has INVALID HMAC signature")
                    if require_hmac:
                        raise KillSwitchTamperError(
                            "Kill switch state verification failed"
                        )
                    return ks
            elif require_hmac:
                logger.error("Kill switch state lacks required HMAC signature")
                raise KillSwitchTamperError(
                    "Kill switch state missing mandatory HMAC signature"
                )
            else:
                logger.warning("Kill switch state has no signature (legacy mode)")

            mode_str = data["mode"] if require_hmac else data.get("mode", "DISENGAGED")
            ks._mode = KillSwitchMode[mode_str]

            # Restore failure_class if present (Phase 1 — backward compatible)
            failure_class = None
            fc_str = data.get("failure_class")
            if fc_str:
                try:
                    failure_class = KillSwitchReason[fc_str]
                except KeyError:
                    logger.warning("Unknown failure_class in state file: %s", fc_str)

            if ks._mode != KillSwitchMode.DISENGAGED or data.get("engaged_at"):
                event = KillSwitchEvent(
                    timestamp=data.get("engaged_at", datetime.now(timezone.utc).isoformat()),
                    mode=ks._mode,
                    reason=data.get("reason", "Restored from file"),
                    triggered_by=data.get("triggered_by", "system"),
                    affected_tasks=0,
                    failure_class=failure_class,
                    event_id=data.get("event_id") or hashlib.sha256(
                        json.dumps(data, sort_keys=True).encode("utf-8")
                    ).hexdigest(),
                    requested_by=data.get("requested_by"),
                )
                ks._history.append(event)
        except FileNotFoundError as e:
            if require_existing or authoritative_reads:
                raise KillSwitchTamperError("Authoritative kill switch state is missing") from e
        except (KeyError, TypeError, ValueError, OSError) as e:
            logger.error("Kill switch state file corrupt: %s", e)
            if require_hmac:
                raise KillSwitchTamperError(f"Kill switch state file corrupt: {e}")

        return ks

    def _check_write_failure(self) -> None:
        """Keep a failed transition closed until an explicit emergency is saved."""
        if self._persistence_failed:
            raise KillSwitchPersistenceError(
                "Previous state write failed; explicitly persist EMERGENCY before recovery"
            )

    def refresh(self) -> None:
        """Read and verify authoritative state without writing or releasing it.

        Preserve local history and append newly observed transitions. The state
        file contains only the latest event, not a complete cross-process log.
        Callers hold the same lock through refresh and their decision.
        """
        with self._lock:
            self._check_write_failure()
            if self._state_dir is None:
                return
            if self._require_hmac:
                self._require_signing_secret()
            restored = self.load_from_file(
                self._state_dir, require_hmac=self._require_hmac,
                signing_secret=self._signing_secret, critical_tasks=self._critical_tasks,
                require_existing=True,
            )
            self._mode = restored._mode
            if restored._history:
                event = restored._history[-1]
                last = self._history[-1] if self._history else None
                # affected_tasks is not persisted; do not duplicate local events.
                fields = ("event_id", "timestamp", "mode", "reason", "triggered_by", "failure_class", "requested_by")
                if last is None or any(getattr(last, f) != getattr(event, f) for f in fields):
                    self._history.append(event)

    def _prepare_read(self) -> None:
        """Enforce the failure latch and refresh shared-core reads under the lock."""
        self._check_write_failure()
        if self._authoritative_reads:
            self.refresh()

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
            "event_id": last_event.event_id if last_event else None,
        }
        if last_event and last_event.requested_by is not None:
            data["requested_by"] = last_event.requested_by
        if last_event and last_event.failure_class is not None:
            data["failure_class"] = last_event.failure_class.name
        secret = self._require_signing_secret() if self._require_hmac else self._get_signing_secret()
        if secret:
            data["signature"] = self._compute_signature(
                {k: v for k, v in data.items() if k != "signature"}, secret
            )
        return data

    def _persist(self) -> None:
        """Persist current state to file if state_dir is configured."""
        if self._state_dir is None:
            return

        # Build/sign before creating or truncating anything. Readers see either
        # the previous complete state or the newly committed complete state.
        data = self._build_state_data()
        state_file = self._state_dir / "kill_switch_state.json"
        temporary = None
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self._state_dir,
                prefix=".kill-switch-", delete=False,
            ) as f:
                temporary = Path(f.name)
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, state_file)
        except OSError as e:
            raise KillSwitchPersistenceError("Failed to persist kill switch state") from e
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _commit_event(self, event: KillSwitchEvent) -> None:
        """Publish a transition only after persistence succeeds; latch failures."""
        previous_mode = self._mode
        self._mode = event.mode
        self._history.append(event)
        try:
            self._persist()
        except Exception:
            self._mode = previous_mode
            self._history.pop()
            self._persistence_failed = True
            raise
        self._persistence_failed = False

    @contextmanager
    def _state_write_lock(self, *, latch_failure: bool = False):
        """Serialize cooperating processes across refresh, check and replace.

        The stable lock file must not be deleted while any writer is running.
        All writers must use this version; filesystem ACLs remain the boundary
        against writers bypassing the library.
        """
        if self._state_dir is None:
            yield
            return
        if self._require_hmac:
            try:
                self._require_signing_secret()
            except KillSwitchConfigurationError:
                if latch_failure:
                    self._persistence_failed = True
                raise
        lock_file = None
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            lock_file = (self._state_dir / ".kill-switch.lock").open("a+b")
            acquire_file_lock(lock_file)
        except OSError as exc:
            if latch_failure:
                self._persistence_failed = True
            if lock_file is not None:
                try:
                    lock_file.close()
                except OSError:
                    pass  # Preserve the original setup failure and its latch.
            raise KillSwitchPersistenceError("Failed to prepare kill switch state lock") from exc
        # Do not catch errors from the yielded authorization/refresh/commit body
        # as setup failures: those paths preserve their own exception semantics.
        with lock_file:
            try:
                yield
            finally:
                release_file_lock(lock_file)

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
        if not isinstance(mode, KillSwitchMode):
            raise ValueError("Invalid kill switch mode")
        if mode == KillSwitchMode.DISENGAGED:
            raise ValueError("Use disengage() to clear kill switch, not engage()")

        with self._lock, self._state_write_lock(latch_failure=True):
            if mode != KillSwitchMode.EMERGENCY:
                self._check_write_failure()
                # Fresh/stale instances must not overwrite another process's halt.
                if self._state_dir is not None and (
                    self._history or (self._state_dir / "kill_switch_state.json").exists()
                    or self._authoritative_reads
                ):
                    self.refresh()
                if mode.value < self._mode.value:
                    raise KillSwitchAuthorizationError(
                        "Engagement cannot weaken a halt; use the operator release path"
                    )
            event = KillSwitchEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                mode=mode,
                reason=reason,
                triggered_by=triggered_by,
                affected_tasks=affected_tasks,
                failure_class=failure_class,
            )
            self._commit_event(event)
        self._notify(event)
        return event

    def disengage(
        self,
        triggered_by: str | None = None,
        reason: str | None = None,
        *,
        credential: str | None = None,
        confirm: bool = False,
        expected_event_id: str | None = None,
    ) -> KillSwitchEvent:
        """Release only through an authenticated, separately configured operator.

        Defaults deny. ``triggered_by`` is untrusted attribution, recorded only
        as ``requested_by``; the authenticated configured identity is recorded
        as ``triggered_by``. Consent must name the current halt's ``event_id``
        (from ``get_status``), and ``confirm`` must be the boolean True.
        A different/new halt invalidates that consent. Never pass these inputs
        through an agent-facing tool. See docs/OPERATOR_RELEASE.md.
        """
        with self._lock:
            self._check_write_failure()
            if self._release_authority is None:
                raise KillSwitchAuthorizationError("Operator release authority is not configured")
            if confirm is not True:
                raise KillSwitchAuthorizationError("Explicit confirm=True is required")
            operator_id = self._release_authority.authenticate(credential)
            if not isinstance(reason, str) or not reason.strip():
                raise KillSwitchAuthorizationError("A release reason is required")
            if triggered_by is not None and not isinstance(triggered_by, str):
                raise KillSwitchAuthorizationError("Invalid caller attribution")
            with self._state_write_lock():
                if self._state_dir is not None:
                    self.refresh()
                if self._mode == KillSwitchMode.DISENGAGED or not self._history:
                    raise KillSwitchAuthorizationError("There is no current halt to release")
                if (not isinstance(expected_event_id, str)
                        or expected_event_id != self._history[-1].event_id):
                    raise KillSwitchAuthorizationError("Current halt changed; review and confirm again")
                event = KillSwitchEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    mode=KillSwitchMode.DISENGAGED,
                    reason=reason,
                    triggered_by=operator_id,
                    requested_by=triggered_by,
                    affected_tasks=0,
                )
                self._commit_event(event)
        self._notify(event)
        return event

    def check_task_allowed(self, task_type: str) -> dict[str, Any]:
        """Check if a task is allowed under current kill switch mode.

        Returns:
            Dict with 'allowed' (bool), 'action' (str), and optionally
            'reason' or 'note'.
        """
        with self._lock:
            self._prepare_read()
            is_critical = task_type in self._critical_tasks
            current_mode = self._mode

            if current_mode == KillSwitchMode.DISENGAGED:
                return {"allowed": True, "action": "allow", "mode": current_mode.name}

            if current_mode == KillSwitchMode.HALT_NONCRITICAL:
                if is_critical:
                    return {
                        "allowed": True,
                        "action": "allow",
                        "note": "critical task exempted",
                        "mode": current_mode.name,
                    }
                return {
                    "allowed": False,
                    "action": "queue",
                    "reason": f"Kill switch engaged ({current_mode.name}): {task_type} queued",
                    "mode": current_mode.name,
                }

            if current_mode in (KillSwitchMode.HALT_ALL, KillSwitchMode.EMERGENCY):
                if is_critical and current_mode == KillSwitchMode.HALT_ALL:
                    return {"allowed": True, "action": "allow", "note": "critical only", "mode": current_mode.name}
                return {
                    "allowed": False,
                    "action": "block",
                    "reason": f"Kill switch engaged ({current_mode.name}): {task_type} blocked",
                    "mode": current_mode.name,
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
        with self._lock:
            self._prepare_read()
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
                "event_id": self._history[-1].event_id if self._history else None,
                "engaged": self._mode != KillSwitchMode.DISENGAGED,
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
        with self._lock:
            self._prepare_read()
            events = self._history.copy()
            if engaged_only:
                events = [e for e in events if e.mode != KillSwitchMode.DISENGAGED]
            if limit:
                events = events[-limit:]
            return events


# ---------------------------------------------------------------------------
# Process-wide shared instance
# ---------------------------------------------------------------------------

_core_instance: KillSwitch | None = None
_core_lock = threading.Lock()


def get_kill_switch_core() -> KillSwitch:
    """Return the shared core after verifying authoritative persisted state.

    Every status, history, mode and task read refreshes under the instance lock,
    including reads through a retained reference. State must already exist and
    verify with HUMMBL_SIGNING_SECRET or DCT_SECRET. Reads never initialize,
    delete, re-sign, or release state. Missing credentials/state fail closed.

    An operator provisions signed state through an explicit EMERGENCY engagement
    and separately authorizes release. Restoring credentials alone cannot clear
    an emergency. The dedicated MCP server remains read-only.
    """
    global _core_instance
    with _core_lock:
        if _core_instance is None:
            state_dir = Path(
                os.environ.get("GOVERNANCE_STATE_DIR")
                or Path(tempfile.gettempdir()) / "governance"
            )
            core = KillSwitch(state_dir=state_dir)
            core._authoritative_reads = True
            core.refresh()
            _core_instance = core
        core = _core_instance
    # Do not hold the singleton lock while taking the instance lock: subscriber
    # callbacks may themselves call this accessor while holding the latter.
    core.refresh()
    return core
