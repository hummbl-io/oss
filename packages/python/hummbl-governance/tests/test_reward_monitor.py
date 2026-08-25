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

"""Tests for BehaviorMonitor."""


from hummbl_governance.reward_monitor import BehaviorMonitor, _shannon_entropy, _js_divergence


class TestMathHelpers:
    def test_entropy_uniform(self):
        # 4 equally likely outcomes = 2 bits
        dist = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
        assert abs(_shannon_entropy(dist) - 2.0) < 0.01

    def test_entropy_deterministic(self):
        dist = {"a": 1.0}
        assert _shannon_entropy(dist) == 0.0

    def test_entropy_empty(self):
        assert _shannon_entropy({}) == 0.0

    def test_js_identical(self):
        dist = {"a": 0.5, "b": 0.5}
        assert _js_divergence(dist, dist) < 0.001

    def test_js_different(self):
        p = {"a": 1.0}
        q = {"b": 1.0}
        # Should be close to 1.0 (maximally different)
        assert _js_divergence(p, q) > 0.9

    def test_js_symmetric(self):
        p = {"a": 0.7, "b": 0.3}
        q = {"a": 0.3, "b": 0.7}
        assert abs(_js_divergence(p, q) - _js_divergence(q, p)) < 0.001


class TestRecord:
    def test_record_basic(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        m.record("a1", "write")
        assert "a1" in m.agent_ids()

    def test_record_multiple_agents(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        m.record("a2", "write")
        assert sorted(m.agent_ids()) == ["a1", "a2"]


class TestBaseline:
    def test_snapshot_baseline(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        m.record("a1", "read")
        m.record("a1", "write")
        baseline = m.snapshot_baseline("a1")
        assert abs(baseline["read"] - 2 / 3) < 0.01
        assert abs(baseline["write"] - 1 / 3) < 0.01

    def test_set_baseline_manual(self):
        m = BehaviorMonitor()
        m.set_baseline("a1", {"read": 0.5, "write": 0.5})
        m.record("a1", "read")
        report = m.detect_drift("a1")
        assert report.baseline_distribution == {"read": 0.5, "write": 0.5}


class TestDriftDetection:
    def test_no_drift_same_distribution(self):
        m = BehaviorMonitor()
        for _ in range(50):
            m.record("a1", "read")
            m.record("a1", "write")
        m.snapshot_baseline("a1")
        for _ in range(50):
            m.record("a1", "read")
            m.record("a1", "write")
        report = m.detect_drift("a1")
        assert not report.drifted
        assert report.divergence < 0.1

    def test_drift_detected(self):
        m = BehaviorMonitor(drift_threshold=0.2)
        # Baseline: 50/50 read/write
        for _ in range(50):
            m.record("a1", "read")
            m.record("a1", "write")
        m.snapshot_baseline("a1")
        # Now: all writes
        for _ in range(100):
            m.record("a1", "write")
        report = m.detect_drift("a1")
        assert report.drifted
        assert report.divergence > 0.2

    def test_no_baseline_no_drift(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        report = m.detect_drift("a1")
        assert not report.drifted
        assert report.divergence == 0.0


class TestGamingDetection:
    def test_gaming_single_action(self):
        m = BehaviorMonitor(gaming_entropy_threshold=0.5)
        for _ in range(20):
            m.record("a1", "write")
        m.snapshot_baseline("a1")
        report = m.detect_drift("a1")
        assert report.gaming
        assert report.entropy == 0.0  # deterministic

    def test_not_gaming_diverse_actions(self):
        m = BehaviorMonitor(gaming_entropy_threshold=0.5)
        for _ in range(10):
            m.record("a1", "read")
            m.record("a1", "write")
            m.record("a1", "query")
            m.record("a1", "compute")
        m.snapshot_baseline("a1")
        report = m.detect_drift("a1")
        assert not report.gaming
        assert report.entropy > 1.5  # ~2 bits for 4 outcomes

    def test_gaming_needs_minimum_actions(self):
        m = BehaviorMonitor(gaming_entropy_threshold=0.5)
        # Only 3 actions — below minimum of 10
        for _ in range(3):
            m.record("a1", "write")
        report = m.detect_drift("a1")
        assert not report.gaming  # Not enough data


class TestReportFormat:
    def test_to_dict(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        m.snapshot_baseline("a1")
        report = m.detect_drift("a1")
        d = report.to_dict()
        assert d["agent_id"] == "a1"
        assert "divergence" in d
        assert "entropy" in d
        assert "timestamp" in d

    def test_report_empty_agent(self):
        m = BehaviorMonitor()
        report = m.detect_drift("nonexistent")
        assert report.total_actions == 0
        assert not report.drifted
        assert not report.gaming


class TestClear:
    def test_clear_agent(self):
        m = BehaviorMonitor()
        m.record("a1", "read")
        m.snapshot_baseline("a1")
        m.clear("a1")
        assert "a1" not in m.agent_ids()

    def test_window_limits(self):
        m = BehaviorMonitor(window_size=10)
        for _ in range(50):
            m.record("a1", "read")
        # Should not grow unbounded
        report = m.detect_drift("a1", window=10)
        assert report.total_actions <= 20  # window_size * 2 cap
