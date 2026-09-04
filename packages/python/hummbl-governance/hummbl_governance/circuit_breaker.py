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

"""Circuit Breaker -- Automatic failure detection and recovery.

Three states:
    CLOSED: Normal operation. Failures are counted.
    OPEN: Failure threshold exceeded. All calls rejected immediately.
    HALF_OPEN: Recovery timeout elapsed. One probe call allowed.

Usage:
    from hummbl_governance import CircuitBreaker, CircuitBreakerState

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

    try:
        result = cb.call(some_external_service, arg1, arg2)
    except CircuitBreakerOpen:
        result = fallback_value

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Optional

from hummbl_governance._types import CircuitBreakerState

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when a call is attempted on an open circuit breaker.

    Attributes:
        failure_count: Number of failures that tripped the breaker.
        last_failure_time: Timestamp (monotonic) of the last failure.
        recovery_timeout: Seconds until the breaker enters HALF_OPEN.
    """

    def __init__(
        self,
        message: str = "Circuit breaker is open",
        *,
        failure_count: int = 0,
        last_failure_time: float | None = None,
        recovery_timeout: float = 0.0,
    ):
        self.failure_count = failure_count
        self.last_failure_time = last_failure_time
        self.recovery_timeout = recovery_timeout
        super().__init__(message)


class CircuitBreaker:
    """Automatic failure detection and recovery for callable wrappers.

    Thread-safe: all state mutations are protected by a threading.Lock.

    Args:
        failure_threshold: Number of consecutive failures before tripping.
        recovery_timeout: Seconds to wait in OPEN before allowing a probe.
        on_state_change: Optional callback(old_state, new_state) invoked
            on every state transition.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        on_state_change: Optional[Callable[[CircuitBreakerState, CircuitBreakerState], None]] = None,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout < 0:
            raise ValueError("recovery_timeout must be >= 0")

        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._on_state_change = on_state_change

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_probe_in_flight = False
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        """Current breaker state."""
        with self._lock:
            return self._effective_state()

    @property
    def failure_count(self) -> int:
        """Consecutive failure count since last reset."""
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """Total successful calls since last reset."""
        with self._lock:
            return self._success_count

    @property
    def last_failure_time(self) -> float | None:
        """Monotonic timestamp of the most recent failure, or None."""
        with self._lock:
            return self._last_failure_time

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute *fn* through the circuit breaker.

        Returns whatever *fn* returns.

        Raises:
            CircuitBreakerOpen: If the breaker is OPEN.
            Exception: Any exception raised by *fn*.
        """
        with self._lock:
            effective = self._effective_state()

            if effective == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is open (failures={self._failure_count}, "
                    f"recovery_timeout={self._recovery_timeout}s)",
                    failure_count=self._failure_count,
                    last_failure_time=self._last_failure_time,
                    recovery_timeout=self._recovery_timeout,
                )

            if effective == CircuitBreakerState.HALF_OPEN:
                if self._state == CircuitBreakerState.OPEN:
                    self._transition(CircuitBreakerState.HALF_OPEN)
                if self._half_open_probe_in_flight:
                    raise CircuitBreakerOpen(
                        "Circuit breaker half-open probe already in progress",
                        failure_count=self._failure_count,
                        last_failure_time=self._last_failure_time,
                        recovery_timeout=self._recovery_timeout,
                    )
                self._half_open_probe_in_flight = True

        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self._lock:
                self._record_failure()
            raise
        except BaseException:
            # ponytail: KeyboardInterrupt/SystemExit are not failures, but the
            # half-open probe flag must be cleared so the breaker is not stuck.
            with self._lock:
                self._half_open_probe_in_flight = False
            raise

        with self._lock:
            self._record_success()

        return result

    def reset(self) -> None:
        """Manually reset the breaker to CLOSED state."""
        with self._lock:
            old_state = self._effective_state()
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_probe_in_flight = False
            if self._state != CircuitBreakerState.CLOSED:
                self._state = CircuitBreakerState.CLOSED
                self._fire_callback(old_state, CircuitBreakerState.CLOSED)

    def _effective_state(self) -> CircuitBreakerState:
        """Compute effective state, accounting for recovery timeout."""
        if self._state == CircuitBreakerState.OPEN and self._last_failure_time is not None:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                return CircuitBreakerState.HALF_OPEN
        return self._state

    def _record_failure(self) -> None:
        """Record a failure. Trip the breaker if threshold is reached."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_probe_in_flight = False
            self._transition(CircuitBreakerState.OPEN)
        elif (
            self._state == CircuitBreakerState.CLOSED
            and self._failure_count >= self._failure_threshold
        ):
            self._transition(CircuitBreakerState.OPEN)

    def _record_success(self) -> None:
        """Record a success. Reset if in HALF_OPEN."""
        self._success_count += 1

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_probe_in_flight = False
            self._failure_count = 0
            self._last_failure_time = None
            self._transition(CircuitBreakerState.CLOSED)
        elif self._state == CircuitBreakerState.CLOSED:
            self._failure_count = 0

    def _transition(self, new_state: CircuitBreakerState) -> None:
        """Transition to a new state and fire the callback."""
        old_state = self._state
        if old_state == new_state:
            return
        self._state = new_state
        self._fire_callback(old_state, new_state)

    def _fire_callback(
        self, old_state: CircuitBreakerState, new_state: CircuitBreakerState
    ) -> None:
        """Fire the on_state_change callback, swallowing errors."""
        if self._on_state_change is None:
            return
        try:
            self._on_state_change(old_state, new_state)
        except Exception:
            logger.debug("Circuit breaker state change callback failed", exc_info=True)
