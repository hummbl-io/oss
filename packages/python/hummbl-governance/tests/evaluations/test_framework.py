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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_governance.evaluations.framework."""

from __future__ import annotations

import pytest

from hummbl_governance.evaluations.framework import (
    EvaluationFramework,
    ScoreLevel,
    DimensionResult,
)


class TestScoreLevel:
    """Tests for the ScoreLevel enum."""

    def test_from_score_0(self):
        assert ScoreLevel.from_score(0) == ScoreLevel.NONE

    def test_from_score_1(self):
        assert ScoreLevel.from_score(1) == ScoreLevel.MINIMAL

    def test_from_score_5(self):
        assert ScoreLevel.from_score(5) == ScoreLevel.EXEMPLARY

    def test_from_score_invalid(self):
        with pytest.raises(ValueError):
            ScoreLevel.from_score(-1)
        with pytest.raises(ValueError):
            ScoreLevel.from_score(6)


class TestEvaluationFramework:
    """Tests for the EvaluationFramework class."""

    def test_framework_has_8_dimensions(self):
        """Framework should have all 8 dimensions."""
        framework = EvaluationFramework()
        assert framework.dimension_count == 8

    def test_total_weight_is_1(self):
        """Sum of all dimension weights should be 1.0."""
        framework = EvaluationFramework()
        assert abs(framework.total_weight - 1.0) < 0.001

    def test_list_dimensions(self):
        """list_dimensions() should return all dimensions."""
        framework = EvaluationFramework()
        dims = framework.list_dimensions()
        assert len(dims) == 8
        expected_slugs = {
            "governance_maturity", "runtime_governance", "compliance_posture",
            "agent_governance", "transparency", "open_weight_governance",
            "safety_behaviors", "agent_capability",
        }
        assert {d.slug for d in dims} == expected_slugs

    def test_get_dimension(self):
        """get_dimension() should return the correct dimension."""
        framework = EvaluationFramework()
        gm = framework.get_dimension("governance_maturity")
        assert gm is not None
        assert gm.name == "Governance Maturity"
        assert gm.weight == 0.20

    def test_get_dimension_unknown(self):
        """get_dimension() should return None for unknown slugs."""
        framework = EvaluationFramework()
        assert framework.get_dimension("nonexistent") is None

    def test_score_criterion_valid(self):
        """score_criterion() should return a valid result for 0-5 scores."""
        framework = EvaluationFramework()
        result = framework.score_criterion(
            "governance_maturity", "safety_framework_published", 4,
        )
        assert result.score == 4
        assert result.level == ScoreLevel.ADVANCED

    def test_score_criterion_na(self):
        """score_criterion() should handle -1 as N/A."""
        framework = EvaluationFramework()
        result = framework.score_criterion(
            "governance_maturity", "safety_framework_published", -1,
        )
        assert result.score is None
        assert result.level is None

    def test_score_criterion_invalid_score(self):
        """score_criterion() should reject scores outside 0-5."""
        framework = EvaluationFramework()
        with pytest.raises(ValueError):
            framework.score_criterion(
                "governance_maturity", "safety_framework_published", 6,
            )

    def test_score_criterion_unknown_dimension(self):
        """score_criterion() should raise KeyError for unknown dimension."""
        framework = EvaluationFramework()
        with pytest.raises(KeyError):
            framework.score_criterion("nonexistent", "criterion", 3)

    def test_score_criterion_unknown_criterion(self):
        """score_criterion() should raise KeyError for unknown criterion."""
        framework = EvaluationFramework()
        with pytest.raises(KeyError):
            framework.score_criterion("governance_maturity", "nonexistent", 3)

    def test_score_dimension_all_scored(self):
        """score_dimension() should correctly weight all criteria."""
        framework = EvaluationFramework()
        scores = {
            "safety_framework_published": 5,
            "framework_bindingness": 4,
            "pause_commitment": 3,
            "external_review": 2,
            "academic_eval_score": 1,
        }
        result = framework.score_dimension("governance_maturity", scores)
        assert result.applicable
        assert 0 < result.weighted_score <= 5
        assert len(result.criterion_results) == 5

    def test_score_dimension_with_na(self):
        """score_dimension() should handle N/A criteria (None scores)."""
        framework = EvaluationFramework()
        scores = {
            "safety_framework_published": 5,
            "framework_bindingness": 4,
            "pause_commitment": None,  # N/A
            "external_review": 2,
            "academic_eval_score": 1,
        }
        result = framework.score_dimension("governance_maturity", scores)
        assert result.applicable
        # N/A criterion should be excluded from weighting
        na_criteria = [cr for cr in result.criterion_results if cr.score is None]
        assert len(na_criteria) == 1

    def test_score_dimension_all_na(self):
        """score_dimension() should mark dimension as not applicable if all N/A."""
        framework = EvaluationFramework()
        scores = {
            "safety_framework_published": None,
            "framework_bindingness": None,
            "pause_commitment": None,
            "external_review": None,
            "academic_eval_score": None,
        }
        result = framework.score_dimension("governance_maturity", scores)
        assert not result.applicable

    def test_aggregate(self):
        """aggregate() should produce a valid overall score."""
        framework = EvaluationFramework()
        dim_results = [
            framework.score_dimension("governance_maturity", {
                "safety_framework_published": 5,
                "framework_bindingness": 4,
                "pause_commitment": 3,
                "external_review": 2,
                "academic_eval_score": 4,
            }),
            framework.score_dimension("runtime_governance", {
                "kill_switch": 3,
                "circuit_breaker": 2,
                "cost_governance": 3,
                "audit_logging": 4,
                "output_validation": 3,
                "capability_fencing": 2,
            }),
        ]
        scorecard = framework.aggregate("test-lab", dim_results)
        assert scorecard.lab_slug == "test-lab"
        assert 0 < scorecard.overall_score <= 5
        assert 0 < scorecard.overall_percentage <= 100

    def test_aggregate_with_not_applicable(self):
        """aggregate() should skip not-applicable dimensions."""
        framework = EvaluationFramework()
        dim_results = [
            framework.score_dimension("governance_maturity", {
                "safety_framework_published": 5,
                "framework_bindingness": 4,
                "pause_commitment": 3,
                "external_review": 2,
                "academic_eval_score": 4,
            }),
            DimensionResult(
                dimension_slug="open_weight_governance",
                weighted_score=0.0,
                applicable=False,
            ),
        ]
        scorecard = framework.aggregate("test-lab", dim_results)
        assert scorecard.overall_score > 0

    def test_dimension_criteria_weights_sum_to_1(self):
        """Each dimension's criteria weights should sum to approximately 1.0."""
        framework = EvaluationFramework()
        for dim in framework.list_dimensions():
            assert abs(dim.total_criterion_weight - 1.0) < 0.01, \
                f"Dimension {dim.slug} criteria weights sum to {dim.total_criterion_weight}, not 1.0"

    def test_all_criteria_have_6_level_rubrics(self):
        """Each criterion should have exactly 6 rubric levels (0-5)."""
        framework = EvaluationFramework()
        for dim in framework.list_dimensions():
            for crit in dim.criteria:
                assert len(crit.rubric) == 6, \
                    f"Criterion {crit.slug} has {len(crit.rubric)} rubric levels, expected 6"

    def test_scorecard_result_to_json(self):
        """ScorecardResult.to_json() should produce valid JSON."""
        framework = EvaluationFramework()
        dim_results = [
            framework.score_dimension("governance_maturity", {
                "safety_framework_published": 5,
                "framework_bindingness": 4,
                "pause_commitment": 3,
                "external_review": 2,
                "academic_eval_score": 4,
            }),
        ]
        scorecard = framework.aggregate("test-lab", dim_results)
        json_str = scorecard.to_json()
        import json
        parsed = json.loads(json_str)
        assert parsed["lab"] == "test-lab"
        assert "dimensions" in parsed
