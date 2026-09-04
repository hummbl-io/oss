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

"""Tests for hummbl_governance.evaluations.scorecard."""

from __future__ import annotations

import json
import pytest

from hummbl_governance.evaluations.scorecard import (
    ScorecardGenerator,
)
from hummbl_governance.evaluations.scorecard_data import (
    LAB_SCORECARDS,
    LAB_METADATA,
)


class TestScorecardData:
    """Tests for the scorecard data module."""

    def test_all_28_labs_have_scorecards(self):
        """LAB_SCORECARDS should have entries for all 28 labs."""
        assert len(LAB_SCORECARDS) == 28

    def test_all_28_labs_have_metadata(self):
        """LAB_METADATA should have entries for all 28 labs."""
        assert len(LAB_METADATA) == 28

    def test_scorecard_slugs_match_metadata_slugs(self):
        """LAB_SCORECARDS and LAB_METADATA should have the same keys."""
        assert set(LAB_SCORECARDS.keys()) == set(LAB_METADATA.keys())

    def test_each_lab_has_6_dimensions(self):
        """Each lab should have scores for all 6 rubric dimensions."""
        for slug, scores in LAB_SCORECARDS.items():
            expected_dims = {
                "governance_maturity", "runtime_governance",
                "compliance_posture", "agent_governance",
                "transparency", "open_weight_governance",
            }
            assert set(scores.keys()) == expected_dims, \
                f"Lab {slug} has dimensions: {set(scores.keys())}, expected: {expected_dims}"

    def test_all_scores_are_0_to_5_or_none(self):
        """All criterion scores should be 0-5 or None (for N/A)."""
        for slug, dims in LAB_SCORECARDS.items():
            for dim_name, criteria in dims.items():
                for crit_name, score in criteria.items():
                    if score is not None:
                        assert 0 <= score <= 5, \
                            f"Lab {slug} dim {dim_name} crit {crit_name}: score {score} out of range"

    def test_closed_weight_labs_have_none_open_weight(self):
        """Closed-weight labs should have None for open-weight governance."""
        for slug, meta in LAB_METADATA.items():
            if meta["weights"] == "closed":
                ow_scores = LAB_SCORECARDS[slug].get("open_weight_governance", {})
                for crit, score in ow_scores.items():
                    assert score is None, \
                        f"Closed-weight lab {slug} has non-None open_weight score: {crit}={score}"


class TestScorecardGenerator:
    """Tests for the ScorecardGenerator class."""

    def test_generate_single_lab(self):
        """generate() should produce a scorecard for a known lab."""
        generator = ScorecardGenerator()
        sc = generator.generate("anthropic")
        assert sc.lab_slug == "anthropic"
        assert sc.lab.name == "Anthropic"
        assert 0 < sc.overall_score <= 5
        assert 0 < sc.overall_percentage <= 100

    def test_generate_unknown_lab_raises(self):
        """generate() should raise KeyError for unknown lab."""
        generator = ScorecardGenerator()
        with pytest.raises(KeyError):
            generator.generate("nonexistent-lab")

    def test_generate_all(self):
        """generate_all() should produce scorecards for all 28 labs."""
        generator = ScorecardGenerator()
        scorecards = generator.generate_all()
        assert len(scorecards) == 28

    def test_generate_all_sorted_by_score(self):
        """generate_all() should return scorecards sorted by overall score (desc)."""
        generator = ScorecardGenerator()
        scorecards = generator.generate_all()
        for i in range(len(scorecards) - 1):
            assert scorecards[i].overall_score >= scorecards[i + 1].overall_score

    def test_generate_by_tier(self):
        """generate_by_tier() should return only labs in the specified tier."""
        generator = ScorecardGenerator()
        tier_a = generator.generate_by_tier("A")
        assert all(sc.lab.tier == "A" for sc in tier_a)
        assert len(tier_a) > 0

    def test_closed_weight_lab_excludes_open_weight(self):
        """Closed-weight labs should have open_weight_governance marked not applicable."""
        generator = ScorecardGenerator()
        # SSI is closed-weight
        sc = generator.generate("ssi")
        ow_dim = [d for d in sc.result.dimensions if d.dimension_slug == "open_weight_governance"]
        assert len(ow_dim) == 1
        assert not ow_dim[0].applicable

    def test_open_weight_lab_includes_open_weight(self):
        """Open-weight labs should have open_weight_governance applicable."""
        generator = ScorecardGenerator()
        # DeepSeek is open-weight
        sc = generator.generate("deepseek")
        ow_dim = [d for d in sc.result.dimensions if d.dimension_slug == "open_weight_governance"]
        assert len(ow_dim) == 1
        assert ow_dim[0].applicable

    def test_scorecard_to_json(self):
        """Scorecard.to_json() should produce valid JSON."""
        generator = ScorecardGenerator()
        sc = generator.generate("anthropic")
        json_str = sc.to_json()
        parsed = json.loads(json_str)
        assert parsed["lab"] == "anthropic"
        assert parsed["lab_name"] == "Anthropic"
        assert "dimensions" in parsed

    def test_scorecard_to_markdown_row(self):
        """Scorecard.to_markdown_row() should produce a table row."""
        generator = ScorecardGenerator()
        sc = generator.generate("anthropic")
        row = sc.to_markdown_row()
        assert "Anthropic" in row
        assert "|" in row

    def test_export_markdown_table(self):
        """export_markdown_table() should produce a full markdown table."""
        generator = ScorecardGenerator()
        table = generator.export_markdown_table()
        assert "| Lab |" in table
        assert "Anthropic" in table
        assert "OpenAI" in table
        # Should have 28 data rows + header
        lines = [line for line in table.split("\n") if line.strip()]
        assert len(lines) >= 29  # header + separator + 28 rows

    def test_export_json(self):
        """export_json() should produce valid JSON for all labs."""
        generator = ScorecardGenerator()
        json_str = generator.export_json()
        parsed = json.loads(json_str)
        assert len(parsed) == 28

    def test_anthropic_scores_high_on_governance(self):
        """Anthropic should score relatively high on governance maturity."""
        generator = ScorecardGenerator()
        sc = generator.generate("anthropic")
        gm = [d for d in sc.result.dimensions if d.dimension_slug == "governance_maturity"][0]
        assert gm.weighted_score >= 3.0  # At least "established"

    def test_chinese_labs_score_low_on_governance(self):
        """Chinese labs should score low on governance maturity (no frameworks)."""
        generator = ScorecardGenerator()
        for slug in ["deepseek", "alibaba-qwen", "zai-zhipu", "moonshot"]:
            sc = generator.generate(slug)
            gm = [d for d in sc.result.dimensions
                  if d.dimension_slug == "governance_maturity"][0]
            assert gm.weighted_score < 2.0, \
                f"{slug} governance maturity {gm.weighted_score} should be < 2.0"
