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

#!/usr/bin/env python3
"""
Circuit Breaker -- Automatic failure detection and recovery (Phase 2 Pillar 1.1).

Thin wrapper re-exporting from hummbl-governance. The canonical implementation
lives in hummbl_governance.circuit_breaker. This module preserves the
founder_mode.services.circuit_breaker import path for backward compatibility.

Usage:
    from founder_mode.services.circuit_breaker import (
        CircuitBreaker, CircuitBreakerOpen, CircuitBreakerState,
    )

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

    try:
        result = cb.call(some_external_service, arg1, arg2)
    except CircuitBreakerOpen:
        result = fallback_value

Integration with coordination bus:
    def on_change(old_state, new_state):
        bus_write(f"circuit_breaker: {old_state.name} -> {new_state.name}")

    cb = CircuitBreaker(on_state_change=on_change)

Stdlib-only. Zero third-party dependencies.
"""

import logging
import threading
import time  # noqa: F401 -- tests mock this via founder_mode.services.circuit_breaker.time

from hummbl_governance.circuit_breaker import (  # noqa: F401
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitBreakerState,
)

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sekhmet Signal 3 — Circuit Breaker Registry
#
# A module-level registry of named CircuitBreaker instances.  Any service
# that instantiates a breaker should call ``register_circuit_breaker`` so
# ``_probe_circuit_breakers`` (health.py) can count simultaneously OPEN
# breakers.  3+ OPEN breakers simultaneously = Signal 3 active.
# ---------------------------------------------------------------------------

SIGNAL3_THRESHOLD: int = 3  # recommended in sekhmet-activation-metrics.md

_registry_lock = threading.Lock()
_registry: dict[str, "CircuitBreaker"] = {}


def register_circuit_breaker(name: str, cb: "CircuitBreaker") -> None:
    """Register a named circuit breaker for Signal 3 monitoring."""
    with _registry_lock:
        _registry[name] = cb


def deregister_circuit_breaker(name: str) -> None:
    """Remove a circuit breaker from the Signal 3 registry."""
    with _registry_lock:
        _registry.pop(name, None)


def count_open_circuit_breakers() -> int:
    """Return the number of registered circuit breakers currently OPEN."""
    with _registry_lock:
        snapshot = list(_registry.values())
    return sum(
        1 for cb in snapshot if cb._effective_state() == CircuitBreakerState.OPEN
    )


def get_registry_snapshot() -> dict[str, str]:
    """Return {name: state_name} for all registered circuit breakers."""
    with _registry_lock:
        snapshot = dict(_registry.items())
    return {name: cb._effective_state().name for name, cb in snapshot.items()}


def force_open(cb: CircuitBreaker) -> None:
    """Force a circuit breaker into OPEN state.

    Used by the kill switch EMERGENCY subscription to immediately trip all
    breakers, preventing any further outbound calls.
    """
    with cb._lock:
        old = cb._effective_state()
        if old == CircuitBreakerState.OPEN:
            return
        cb._failure_count = cb._failure_threshold
        cb._last_failure_time = time.monotonic()
        cb._half_open_probe_in_flight = False
        cb._state = CircuitBreakerState.OPEN
        cb._fire_callback(old, CircuitBreakerState.OPEN)
    _logger.warning("Circuit breaker forced OPEN by kill switch")


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitBreakerState",
    "force_open",
    "SIGNAL3_THRESHOLD",
    "register_circuit_breaker",
    "deregister_circuit_breaker",
    "count_open_circuit_breakers",
    "get_registry_snapshot",
]
