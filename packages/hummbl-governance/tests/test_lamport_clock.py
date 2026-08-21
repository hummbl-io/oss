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

"""Tests for LamportClock."""

import pytest
import threading

from hummbl_governance.lamport_clock import LamportClock, LamportTimestamp


class TestLamportClockBasic:
    """Basic tick/receive operations."""

    def test_initial_value(self):
        clock = LamportClock()
        assert clock.value == 0

    def test_custom_initial_value(self):
        clock = LamportClock(initial=42)
        assert clock.value == 42

    def test_tick_increments(self):
        clock = LamportClock()
        assert clock.tick() == 1
        assert clock.tick() == 2
        assert clock.tick() == 3

    def test_receive_advances_past_remote(self):
        clock = LamportClock()
        clock.tick()  # 1
        result = clock.receive(10)
        assert result == 11  # max(1, 10) + 1

    def test_receive_with_lower_remote(self):
        clock = LamportClock(initial=20)
        result = clock.receive(5)
        assert result == 21  # max(20, 5) + 1

    def test_receive_with_equal_remote(self):
        clock = LamportClock(initial=10)
        result = clock.receive(10)
        assert result == 11  # max(10, 10) + 1

    def test_tick_after_receive(self):
        clock = LamportClock()
        clock.receive(100)  # -> 101
        assert clock.tick() == 102

    def test_value_read_only(self):
        clock = LamportClock()
        _ = clock.value
        _ = clock.value
        assert clock.value == 0  # Reading doesn't advance


class TestLamportClockStamp:
    """Stamp and ordering."""

    def test_stamp_returns_tuple(self):
        clock = LamportClock(agent_id="agent-1")
        ts, aid = clock.stamp()
        assert ts == 1
        assert aid == "agent-1"

    def test_stamp_increments(self):
        clock = LamportClock(agent_id="a")
        s1 = clock.stamp()
        s2 = clock.stamp()
        assert s1[0] < s2[0]

    def test_happened_before_lower_timestamp(self):
        assert LamportClock.happened_before(LamportTimestamp(1, "a"), LamportTimestamp(2, "b")) is True

    def test_happened_before_higher_timestamp(self):
        assert LamportClock.happened_before(LamportTimestamp(5, "a"), LamportTimestamp(3, "b")) is False

    def test_happened_before_same_timestamp_tie_break(self):
        # "a" < "b" lexicographically
        assert LamportClock.happened_before(LamportTimestamp(5, "a"), LamportTimestamp(5, "b")) is True
        assert LamportClock.happened_before(LamportTimestamp(5, "b"), LamportTimestamp(5, "a")) is False

    def test_happened_before_same_agent_same_timestamp(self):
        assert LamportClock.happened_before(LamportTimestamp(5, "a"), LamportTimestamp(5, "a")) is None


class TestLamportClockThreadSafety:
    """Concurrent access."""

    def test_concurrent_ticks(self):
        clock = LamportClock()
        results = []
        barrier = threading.Barrier(10)

        def tick_many():
            barrier.wait()
            for _ in range(100):
                results.append(clock.tick())

        threads = [threading.Thread(target=tick_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 threads * 100 ticks = 1000 unique values
        assert len(set(results)) == 1000
        assert clock.value == 1000

    def test_concurrent_receive(self):
        clock = LamportClock()

        def receive_many(base):
            for i in range(50):
                clock.receive(base + i)

        threads = [threading.Thread(target=receive_many, args=(i * 100,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Clock should be well past 0 (exact value depends on thread interleaving)
        assert clock.value >= 250


class TestLamportClockAgentId:
    """Agent identity."""

    def test_default_empty_agent_id(self):
        clock = LamportClock()
        assert clock.agent_id == ""

    def test_custom_agent_id(self):
        clock = LamportClock(agent_id="orchestrator")
        assert clock.agent_id == "orchestrator"


class TestLamportClockHardening:
    """Vulnerability and hardening tests (v0.5.0)."""

    def test_forward_jump_attack(self):
        """A malicious remote timestamp should not cause a massive clock jump."""
        clock = LamportClock(initial=100)
        # Malicious actor sends a timestamp far in the future
        malicious_timestamp = 100 + 2000
        clock.receive(malicious_timestamp)
        # With hardening, the clock should only increment by 1, not jump to 2001.
        assert clock.value == 101

    def test_negative_timestamp_receive_raises(self):
        clock = LamportClock()
        with pytest.raises(ValueError):
            clock.receive(-1)
