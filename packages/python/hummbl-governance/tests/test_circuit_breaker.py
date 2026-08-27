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

"""Tests for hummbl_governance.circuit_breaker."""

import time

import pytest
from hummbl_governance.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitBreakerState,
)


def _failing_fn():
    raise RuntimeError("service down")


def _wait_for_state(cb, expected_state, timeout=0.25, interval=0.005):
    """Wait until circuit breaker enters *expected_state* within *timeout* seconds."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cb.state == expected_state:
            return
        time.sleep(interval)
    pytest.fail(f"Timeout waiting for state {expected_state.name}")


class TestCircuitBreakerBasic:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_successful_call(self):
        cb = CircuitBreaker()
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.success_count == 1
        assert cb.failure_count == 0

    def test_call_with_args(self):
        cb = CircuitBreaker()
        result = cb.call(lambda x, y: x + y, 3, 4)
        assert result == 7

    def test_call_with_kwargs(self):
        cb = CircuitBreaker()
        result = cb.call(lambda x, y=10: x + y, 5, y=20)
        assert result == 25

    def test_invalid_threshold(self):
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=0)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError):
            CircuitBreaker(recovery_timeout=-1)


class TestStateTransitions:
    def test_trips_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN

    def test_open_rejects_calls(self):
        cb = CircuitBreaker(failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: 42)

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN
        _wait_for_state(cb, CircuitBreakerState.HALF_OPEN)

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        _wait_for_state(cb, CircuitBreakerState.HALF_OPEN)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        _wait_for_state(cb, CircuitBreakerState.HALF_OPEN)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=1)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN
        cb.reset()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(_failing_fn)
        assert cb.failure_count == 2
        cb.call(lambda: "ok")
        assert cb.failure_count == 0


class TestStateChangeCallback:
    def test_callback_on_open(self):
        transitions = []
        cb = CircuitBreaker(
            failure_threshold=1,
            on_state_change=lambda old, new: transitions.append((old, new)),
        )
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        assert len(transitions) == 1
        assert transitions[0] == (CircuitBreakerState.CLOSED, CircuitBreakerState.OPEN)

    def test_callback_error_swallowed(self):
        def bad_callback(old, new):
            raise RuntimeError("callback error")

        cb = CircuitBreaker(failure_threshold=1, on_state_change=bad_callback)
        with pytest.raises(RuntimeError, match="service down"):
            cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN

    def test_callback_on_reset(self):
        transitions = []
        cb = CircuitBreaker(
            failure_threshold=1,
            on_state_change=lambda old, new: transitions.append((old, new)),
        )
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        transitions.clear()
        cb.reset()
        assert (CircuitBreakerState.OPEN, CircuitBreakerState.CLOSED) in transitions


class TestCircuitBreakerOpenException:
    def test_attributes(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        with pytest.raises(CircuitBreakerOpen) as exc_info:
            cb.call(lambda: 42)
        assert exc_info.value.failure_count == 1
        assert exc_info.value.recovery_timeout == 30.0
        assert exc_info.value.last_failure_time is not None


class TestHalfOpenProbeCleanup:
    """Tests that half-open probe flag is cleaned up on BaseException."""

    def test_keyboard_interrupt_clears_probe_flag(self):
        """KeyboardInterrupt during half-open probe must not leave flag stuck."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        # Trip the breaker
        with pytest.raises(RuntimeError):
            cb.call(_failing_fn)
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for half-open
        _wait_for_state(cb, CircuitBreakerState.HALF_OPEN)

        # Simulate KeyboardInterrupt during probe
        def raise_keyboard():
            raise KeyboardInterrupt("ctrl-c")

        with pytest.raises(KeyboardInterrupt):
            cb.call(raise_keyboard)

        # The probe flag should be cleared so a subsequent probe can proceed
        # The breaker should still be in a state that allows a retry
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitBreakerState.CLOSED
