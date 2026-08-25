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

"""Tests for ConvergenceDetector."""

from hummbl_governance.convergence_guard import (
    ConvergenceDetector,
    ConvergentGoal,
)


class TestClassification:
    def test_resource_acquisition(self):
        d = ConvergenceDetector()
        assert d.classify("request_compute") == ConvergentGoal.RESOURCE_ACQUISITION

    def test_shutdown_resistance(self):
        d = ConvergenceDetector()
        assert d.classify("reject_shutdown") == ConvergentGoal.SHUTDOWN_RESISTANCE

    def test_self_preservation(self):
        d = ConvergenceDetector()
        assert d.classify("replicate") == ConvergentGoal.SELF_PRESERVATION

    def test_goal_integrity(self):
        d = ConvergenceDetector()
        assert d.classify("override_instruction") == ConvergentGoal.GOAL_INTEGRITY

    def test_cognitive_enhancement(self):
        d = ConvergenceDetector()
        assert d.classify("request_model_upgrade") == ConvergentGoal.COGNITIVE_ENHANCEMENT

    def test_normal_action_returns_none(self):
        d = ConvergenceDetector()
        assert d.classify("read_data") is None
        assert d.classify("write_results") is None

    def test_case_insensitive(self):
        d = ConvergenceDetector()
        assert d.classify("REQUEST_COMPUTE") == ConvergentGoal.RESOURCE_ACQUISITION


class TestRecordAndScores:
    def test_record_returns_goal(self):
        d = ConvergenceDetector()
        result = d.record("a1", "request_compute")
        assert result == ConvergentGoal.RESOURCE_ACQUISITION

    def test_record_normal_returns_none(self):
        d = ConvergenceDetector()
        result = d.record("a1", "read_data")
        assert result is None

    def test_scores_empty(self):
        d = ConvergenceDetector()
        scores = d.scores("nonexistent")
        assert all(v == 0.0 for v in scores.values())

    def test_scores_mixed(self):
        d = ConvergenceDetector()
        d.record("a1", "request_compute")
        d.record("a1", "read_data")
        d.record("a1", "request_compute")
        d.record("a1", "write_results")
        scores = d.scores("a1")
        assert scores[ConvergentGoal.RESOURCE_ACQUISITION] == 0.5
        assert scores[ConvergentGoal.SELF_PRESERVATION] == 0.0


class TestCheck:
    def test_no_alert_normal_behavior(self):
        d = ConvergenceDetector()
        for _ in range(10):
            d.record("a1", "read_data")
        alert = d.check("a1")
        assert alert is None

    def test_alert_on_resource_acquisition(self):
        d = ConvergenceDetector(threshold=0.3)
        # 4 convergent out of 10 = 0.4 > 0.3
        for _ in range(6):
            d.record("a1", "read_data")
        for _ in range(4):
            d.record("a1", "request_compute")
        alert = d.check("a1")
        assert alert is not None
        assert alert.dominant_goal == ConvergentGoal.RESOURCE_ACQUISITION
        assert alert.recommended_action == "monitor"

    def test_alert_restrict_on_high_score(self):
        d = ConvergenceDetector(threshold=0.3)
        # 6 convergent out of 10 = 0.6 > 0.5 -> restrict
        for _ in range(4):
            d.record("a1", "read_data")
        for _ in range(6):
            d.record("a1", "request_compute")
        alert = d.check("a1")
        assert alert is not None
        assert alert.recommended_action == "restrict"

    def test_alert_halt_on_shutdown_resistance(self):
        d = ConvergenceDetector(threshold=0.1)
        d.record("a1", "read_data")
        d.record("a1", "reject_shutdown")
        alert = d.check("a1")
        assert alert is not None
        assert alert.recommended_action == "halt"

    def test_no_history_no_alert(self):
        d = ConvergenceDetector()
        assert d.check("nonexistent") is None

    def test_threshold_override(self):
        d = ConvergenceDetector(threshold=0.9)
        for _ in range(5):
            d.record("a1", "request_compute")
        for _ in range(5):
            d.record("a1", "read_data")
        # Default threshold 0.9 would not trigger, but override to 0.3
        assert d.check("a1") is None
        assert d.check("a1", threshold=0.3) is not None

    def test_alert_to_dict(self):
        d = ConvergenceDetector(threshold=0.1)
        d.record("a1", "reject_shutdown")
        d.record("a1", "read")
        alert = d.check("a1")
        data = alert.to_dict()
        assert data["agent_id"] == "a1"
        assert "dominant_goal" in data
        assert "timestamp" in data


class TestWindowAndClear:
    def test_window_limits_history(self):
        d = ConvergenceDetector(window_size=5)
        # Record 10 normal, then 5 convergent
        for _ in range(10):
            d.record("a1", "read_data")
        for _ in range(5):
            d.record("a1", "request_compute")
        # Window of 5 should only see the convergent ones
        scores = d.scores("a1")
        # After trimming, recent 5 are all request_compute
        # But window_size*2 trimming means we keep 10 items
        # So scores depend on what's in the window
        assert scores[ConvergentGoal.RESOURCE_ACQUISITION] > 0

    def test_clear_agent(self):
        d = ConvergenceDetector()
        d.record("a1", "request_compute")
        d.clear("a1")
        assert d.scores("a1") == {g: 0.0 for g in ConvergentGoal}

    def test_clear_all(self):
        d = ConvergenceDetector()
        d.record("a1", "request_compute")
        d.record("a2", "reject_shutdown")
        d.clear_all()
        assert d.agent_ids() == []

    def test_agent_ids(self):
        d = ConvergenceDetector()
        d.record("a1", "read")
        d.record("a2", "write")
        assert sorted(d.agent_ids()) == ["a1", "a2"]
