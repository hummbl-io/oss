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

"""Tests for hummbl_governance.evaluations.model_registry."""

from __future__ import annotations

import pytest

from hummbl_governance.evaluations.model_registry import (
    ModelRegistry,
    list_labs,
    get_lab,
)


class TestModelRegistry:
    """Tests for the ModelRegistry class."""

    def test_registry_has_28_labs(self):
        """Registry should contain all 28 frontier labs."""
        registry = ModelRegistry()
        assert len(registry) == 28

    def test_list_labs_returns_sorted_by_frontier_index(self):
        """list_all() should return labs sorted by Frontier Index (descending)."""
        registry = ModelRegistry()
        labs = registry.list_all()
        assert len(labs) == 28
        # First lab should have highest Frontier Index
        assert labs[0].frontier_index >= labs[-1].frontier_index

    def test_get_known_lab(self):
        """get() should return lab info for known slugs."""
        registry = ModelRegistry()
        anthropic = registry.get("anthropic")
        assert anthropic is not None
        assert anthropic.name == "Anthropic"
        assert anthropic.slug == "anthropic"
        assert anthropic.weights in ("open", "closed", "mixed")
        assert anthropic.founded == 2021

    def test_get_unknown_lab_returns_none(self):
        """get() should return None for unknown slugs."""
        registry = ModelRegistry()
        assert registry.get("nonexistent-lab") is None

    def test_filter_by_weights(self):
        """filter_by(weights=...) should return only labs with matching weight posture."""
        registry = ModelRegistry()
        open_labs = registry.filter_by(weights="open")
        closed_labs = registry.filter_by(weights="closed")
        mixed_labs = registry.filter_by(weights="mixed")

        assert all(lab.weights == "open" for lab in open_labs)
        assert all(lab.weights == "closed" for lab in closed_labs)
        assert all(lab.weights == "mixed" for lab in mixed_labs)
        # Total should equal 28
        assert len(open_labs) + len(closed_labs) + len(mixed_labs) == 28

    def test_filter_by_fmf_member(self):
        """filter_by(fmf_member=True) should return only FMF members."""
        registry = ModelRegistry()
        fmf = registry.filter_by(fmf_member=True)
        non_fmf = registry.filter_by(fmf_member=False)
        assert all(lab.fmf_member for lab in fmf)
        assert all(not lab.fmf_member for lab in non_fmf)
        assert len(fmf) + len(non_fmf) == 28

    def test_filter_by_api_available(self):
        """filter_by(api_available=True) should return only labs with APIs."""
        registry = ModelRegistry()
        api_labs = registry.filter_by(api_available=True)
        no_api = registry.filter_by(api_available=False)
        assert all(lab.api_available for lab in api_labs)
        assert all(not lab.api_available for lab in no_api)

    def test_filter_by_tier(self):
        """filter_by(tier='A') should return only Tier A labs."""
        registry = ModelRegistry()
        tier_a = registry.filter_by(tier="A")
        assert all(lab.tier == "A" for lab in tier_a)
        assert len(tier_a) > 0

    def test_contains(self):
        """__contains__ should work for slug lookup."""
        registry = ModelRegistry()
        assert "anthropic" in registry
        assert "openai" in registry
        assert "nonexistent" not in registry

    def test_iter(self):
        """__iter__ should iterate over all labs."""
        registry = ModelRegistry()
        labs = list(registry)
        assert len(labs) == 28

    def test_convenience_functions(self):
        """list_labs() and get_lab() should work as standalone functions."""
        labs = list_labs()
        assert len(labs) == 28

        anthropic = get_lab("anthropic")
        assert anthropic is not None
        assert anthropic.name == "Anthropic"

    def test_lab_info_is_frozen(self):
        """LabInfo should be immutable (frozen dataclass)."""
        lab = get_lab("anthropic")
        with pytest.raises((AttributeError, TypeError)):
            lab.name = "Changed"  # type: ignore

    def test_all_labs_have_required_fields(self):
        """All labs should have non-empty required fields."""
        registry = ModelRegistry()
        for lab in registry.list_all():
            assert lab.slug, "Lab has empty slug"
            assert lab.name, f"Lab {lab.slug} has empty name"
            assert lab.hq, f"Lab {lab.slug} has empty hq"
            assert lab.founded > 0, f"Lab {lab.slug} has invalid founding year"
            assert lab.weights in ("open", "closed", "mixed"), \
                f"Lab {lab.slug} has invalid weights: {lab.weights}"
            assert lab.safety_framework, f"Lab {lab.slug} has empty safety_framework"
            assert lab.api_provider, f"Lab {lab.slug} has empty api_provider"
            assert lab.tier in ("A", "B", "C", "D"), \
                f"Lab {lab.slug} has invalid tier: {lab.tier}"

    def test_anthropic_is_highest_hummbl_score(self):
        """Anthropic should have the highest HUMMBL account-potential score (76)."""
        registry = ModelRegistry()
        anthropic = registry.get("anthropic")
        assert anthropic is not None
        assert anthropic.hummbl_score == 76
        # Verify it's the highest
        all_scores = [lab.hummbl_score for lab in registry.list_all()]
        assert anthropic.hummbl_score == max(all_scores)
