#!/usr/bin/env python3
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

"""Demo: Circuit breaker failure injection and recovery.

Demonstrates the full lifecycle: CLOSED -> OPEN -> HALF_OPEN -> CLOSED.

Usage:
    python examples/failure_injection.py
"""

import time

from hummbl_governance import CircuitBreaker, CircuitBreakerState
from hummbl_governance.circuit_breaker import CircuitBreakerOpen

call_count = 0


def unreliable_service(should_fail: bool = True) -> str:
    global call_count
    call_count += 1
    if should_fail:
        raise ConnectionError(f"Call #{call_count} failed")
    return f"Call #{call_count} succeeded"


def main():
    transitions: list[str] = []

    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0,  # Short timeout for demo
        on_state_change=lambda old, new: transitions.append(f"{old.name} -> {new.name}"),
    )

    print("=== Phase 1: Inducing failures until breaker trips ===")
    for i in range(5):
        try:
            breaker.call(unreliable_service, True)
        except CircuitBreakerOpen:
            print(f"  Call {i+1}: REJECTED (breaker open)")
        except ConnectionError:
            print(f"  Call {i+1}: FAILED (state={breaker.state.name}, failures={breaker.failure_count})")

    print(f"\nBreaker state: {breaker.state.name}")
    assert breaker.state == CircuitBreakerState.OPEN

    print("\n=== Phase 2: Waiting for recovery timeout ===")
    time.sleep(1.1)
    print(f"Breaker state after wait: {breaker.state.name}")
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    print("\n=== Phase 3: Recovery probe succeeds ===")
    result = breaker.call(unreliable_service, False)
    print(f"  Probe: {result}")
    print(f"Breaker state after recovery: {breaker.state.name}")
    assert breaker.state == CircuitBreakerState.CLOSED

    print("\n=== State transitions ===")
    for t in transitions:
        print(f"  {t}")

    print(f"\nTotal calls: {call_count}")
    print(f"Final state: {breaker.state.name}")
    print(f"Success count: {breaker.success_count}")


if __name__ == "__main__":
    main()
