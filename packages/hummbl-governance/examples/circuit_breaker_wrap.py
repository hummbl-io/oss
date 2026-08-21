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

"""Circuit Breaker: Wrap an unreliable service with automatic failure detection.

Demonstrates the three-state circuit breaker pattern:
CLOSED (normal) -> OPEN (tripped) -> HALF_OPEN (testing) -> CLOSED (recovered).
"""

import random
from hummbl_governance import CircuitBreaker, CircuitBreakerOpen


def unreliable_api_call() -> str:
    """Simulates an API that fails 60% of the time."""
    if random.random() < 0.6:
        raise ConnectionError("Service unavailable")
    return "OK"


# Create breaker: trips after 3 failures, recovers after 2 seconds
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=2.0)

print(f"Initial state: {breaker.state.name}")

for i in range(10):
    try:
        result = breaker.call(unreliable_api_call)
        print(f"  Call {i+1}: {result} (failures={breaker.failure_count})")
    except CircuitBreakerOpen:
        print(f"  Call {i+1}: BLOCKED - breaker is {breaker.state.name}")
    except ConnectionError:
        print(f"  Call {i+1}: FAILED  (failures={breaker.failure_count}, state={breaker.state.name})")

print(f"\nFinal state: {breaker.state.name}")
print(f"Total failures: {breaker.failure_count}")
