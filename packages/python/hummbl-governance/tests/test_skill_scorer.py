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
# See the License for the specific language and permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the SkillScorer usage health scoring service."""

import os
import tempfile
import unittest

from hummbl_governance.services.skill_scorer import (
    SkillScorer,
    _score_frequency,
    _score_success,
    _score_recency,
    _score_exploration,
    _wilson_score_lower,
)


class TestScoringFunctions(unittest.TestCase):
    """Unit tests for individual scoring functions."""

    def test_frequency_zero_invocations(self):
        self.assertEqual(_score_frequency(0), 0.0)

    def test_frequency_one_invocation(self):
        score = _score_frequency(1)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 12.0)

    def test_frequency_ten_invocations(self):
        score = _score_frequency(10)
        self.assertAlmostEqual(score, 12.0, places=1)

    def test_frequency_capped_at_max(self):
        score = _score_frequency(1000)
        self.assertEqual(score, 12.0)

    def test_success_zero_total(self):
        self.assertEqual(_score_success(0, 0), 0.0)

    def test_success_all_successes(self):
        score = _score_success(10, 10)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 8.0)

    def test_success_wilson_penalizes_small_samples(self):
        # 1/1 success should score lower than 10/10 (Wilson lower bound)
        small = _score_success(1, 1)
        large = _score_success(10, 10)
        self.assertLess(small, large)

    def test_recency_no_timestamp(self):
        self.assertEqual(_score_recency(None), 0.0)

    def test_recency_recent(self):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=1)).isoformat()
        score = _score_recency(recent, now=now)
        self.assertGreater(score, 4.0)  # should be > half of max

    def test_recency_old(self):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=60)).isoformat()
        score = _score_recency(old, now=now)
        self.assertLess(score, 1.0)  # should be heavily decayed

    def test_recency_invalid_timestamp(self):
        self.assertEqual(_score_recency("not-a-date"), 0.0)

    def test_exploration_zero_pulls(self):
        self.assertEqual(_score_exploration(0, 0), 6.0)

    def test_exploration_zero_invocations(self):
        self.assertEqual(_score_exploration(0, 100), 6.0)

    def test_exploration_high_invocations_decreases(self):
        low = _score_exploration(1, 100)
        high = _score_exploration(50, 100)
        self.assertGreater(low, high)

    def test_wilson_score_bounds(self):
        self.assertEqual(_wilson_score_lower(0, 0), 0.0)
        self.assertGreater(_wilson_score_lower(5, 10), 0.0)
        self.assertLessEqual(_wilson_score_lower(10, 10), 1.0)


class TestSkillScorer(unittest.TestCase):
    """Tests for the SkillScorer class."""

    def test_no_telemetry_all_zero(self):
        scorer = SkillScorer(telemetry_path=None, skills_dir="/nonexistent")
        scores = scorer.score_all()
        self.assertEqual(scores, {})

    def test_with_telemetry(self):
        # Create a temp TSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", delete=False, encoding="utf-8"
        ) as f:
            f.write("skill_name\tinvocation_count\tlast_invoked\tsession_count\tsuccess_count\n")
            f.write("test-skill\t5\t2026-09-01T00:00:00Z\t3\t5\n")
            tsv_path = f.name

        try:
            scorer = SkillScorer(
                telemetry_path=tsv_path, skills_dir="/nonexistent"
            )
            score = scorer.score_skill("test-skill")
            self.assertEqual(score.invocation_count, 5)
            self.assertGreater(score.frequency, 0)
            self.assertGreater(score.success, 0)
            self.assertGreater(score.recency, 0)
            self.assertGreater(score.total, 0)
        finally:
            os.unlink(tsv_path)

    def test_missing_skill_returns_zero_usage(self):
        scorer = SkillScorer(telemetry_path=None, skills_dir="/nonexistent")
        score = scorer.score_skill("nonexistent-skill")
        self.assertEqual(score.invocation_count, 0)
        self.assertEqual(score.frequency, 0.0)
        self.assertEqual(score.success, 0.0)
        self.assertEqual(score.recency, 0.0)
        # Exploration bonus is max (6.0) for unexplored skills — this is correct
        self.assertEqual(score.exploration, 6.0)

    def test_report_generation(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", delete=False, encoding="utf-8"
        ) as f:
            f.write("skill_name\tinvocation_count\tlast_invoked\tsession_count\tsuccess_count\n")
            f.write("test-skill\t3\t2026-09-01T00:00:00Z\t2\t3\n")
            tsv_path = f.name

        try:
            scorer = SkillScorer(
                telemetry_path=tsv_path, skills_dir="/nonexistent"
            )
            scores = scorer.score_all()
            report = scorer.generate_report(scores)
            self.assertIn("Skill Usage Scorer", report)
            self.assertIn("test-skill", report)
        finally:
            os.unlink(tsv_path)


if __name__ == "__main__":
    unittest.main()
