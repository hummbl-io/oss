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

"""Causal ordering for distributed agent events via Lamport logical clock."""

from __future__ import annotations

import threading
from typing import NamedTuple


class LamportTimestamp(NamedTuple):
    """Timestamp + Agent ID for total ordering."""
    time: int
    agent_id: str


class LamportClock:
    """A Lamport logical clock for causal ordering of distributed events.

    This implementation is thread-safe.
    v0.5.0 adds hardening against "forward-jump" attacks via `max_delta`.
    """

    def __init__(self, initial: int = 0, agent_id: str = "", max_delta: int = 1000):
        if initial < 0:
            raise ValueError("Initial clock value cannot be negative.")
        self._time = initial
        self._agent_id = agent_id
        self._max_delta = max_delta
        self._lock = threading.Lock()

    @property
    def value(self) -> int:
        """Return the current clock value without advancing it."""
        with self._lock:
            return self._time

    @property
    def agent_id(self) -> str:
        """Return the agent ID associated with this clock."""
        return self._agent_id

    def tick(self) -> int:
        """Advance the clock and return the new value.

        Used when an internal event occurs.
        """
        with self._lock:
            self._time += 1
            return self._time

    def receive(self, remote_timestamp: int) -> int:
        """Advance the clock based on a received timestamp.

        Used when receiving a message from another agent.
        Hardened to prevent massive clock jumps.
        """
        if remote_timestamp < 0:
            raise ValueError("Remote timestamp cannot be negative.")

        with self._lock:
            # v0.5.0 hardening: cap the delta
            if remote_timestamp > self._time + self._max_delta:
                # Malicious or out-of-sync timestamp; increment locally instead of jumping
                self._time += 1
            else:
                self._time = max(self._time, remote_timestamp) + 1
            return self._time

    def stamp(self) -> LamportTimestamp:
        """Create a new timestamp for an event to be sent."""
        new_time = self.tick()
        return LamportTimestamp(new_time, self.agent_id)

    @staticmethod
    def happened_before(ts1: LamportTimestamp, ts2: LamportTimestamp) -> bool | None:
        """Determine if ts1 happened before ts2.

        Returns:
            True if ts1 happened before ts2.
            False if ts2 happened before ts1.
            None if they are concurrent (or identical).
        """
        if ts1.time < ts2.time:
            return True
        if ts1.time > ts2.time:
            return False
        # Timestamps are equal, use agent ID as tie-breaker
        if ts1.agent_id < ts2.agent_id:
            return True
        if ts1.agent_id > ts2.agent_id:
            return False
        # Identical timestamps from the same agent
        return None
