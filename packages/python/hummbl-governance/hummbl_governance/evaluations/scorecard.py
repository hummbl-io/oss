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

"""Scorecard Generator -- Per-lab scorecard generation from rubric data.

Combines the evaluation framework with per-lab scoring data to produce
complete scorecards for all 28 frontier AI labs.

Usage:
    from hummbl_governance.evaluations.scorecard import ScorecardGenerator

    generator = ScorecardGenerator()
    scorecard = generator.generate("anthropic")
    print(scorecard.to_json())

    # Generate all scorecards
    all_scorecards = generator.generate_all()
    for sc in all_scorecards:
        print(f"{sc.lab_slug}: {sc.overall_percentage:.1f}%")

    # Export as markdown table
    markdown = generator.export_markdown_table()
    print(markdown)

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from hummbl_governance.evaluations.framework import (
    EvaluationFramework,
    ScorecardResult,
    DimensionResult,
    ScoreLevel,
)
from hummbl_governance.evaluations.model_registry import ModelRegistry, LabInfo


@dataclass
class Scorecard:
    """A complete scorecard for a single lab.

    Wraps a ScorecardResult with lab metadata for convenience.
    """

    result: ScorecardResult
    lab: LabInfo

    @property
    def lab_slug(self) -> str:
        return self.result.lab_slug

    @property
    def overall_score(self) -> float:
        return self.result.overall_score

    @property
    def overall_percentage(self) -> float:
        return self.result.overall_percentage

    @property
    def overall_level(self) -> ScoreLevel:
        return self.result.overall_level

    def to_dict(self) -> dict:
        d = self.result.to_dict()
        d["lab_name"] = self.lab.name
        d["lab_hq"] = self.lab.hq
        d["lab_flagship_model"] = self.lab.flagship_model
        d["lab_weights"] = self.lab.weights
        d["lab_safety_framework"] = self.lab.safety_framework
        d["lab_tier"] = self.lab.tier
        d["lab_hummbl_score"] = self.lab.hummbl_score
        return d

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown_row(self) -> str:
        """Render as a markdown table row."""
        dims = {d.dimension_slug: d for d in self.result.dimensions}
        gm = dims.get("governance_maturity")
        rg = dims.get("runtime_governance")
        cp = dims.get("compliance_posture")
        ag = dims.get("agent_governance")
        tr = dims.get("transparency")
        ow = dims.get("open_weight_governance")
        sb = dims.get("safety_behaviors")
        ac = dims.get("agent_capability")

        def fmt(d: DimensionResult | None) -> str:
            if d is None or not d.applicable:
                return "N/A"
            return f"{d.weighted_score:.1f}"

        return (
            f"| {self.lab.name} | {self.lab.weights} | "
            f"{fmt(gm)} | {fmt(rg)} | {fmt(cp)} | {fmt(ag)} | "
            f"{fmt(tr)} | {fmt(ow)} | {fmt(sb)} | {fmt(ac)} | "
            f"{self.overall_score:.2f} | {self.overall_percentage:.1f}% | "
            f"{self.overall_level.value} |"
        )


class ScorecardGenerator:
    """Generates scorecards from the evaluation framework and per-lab data.

    Uses the rubric-based scoring data from scorecard_data.py for the 6
    rubric-based dimensions. API-runnable dimensions (safety_behaviors,
    agent_capability) are left unscored (0) until API tests are run.
    """

    def __init__(
        self,
        framework: EvaluationFramework | None = None,
        registry: ModelRegistry | None = None,
    ) -> None:
        self.framework = framework or EvaluationFramework()
        self.registry = registry or ModelRegistry()

    def generate(self, lab_slug: str) -> Scorecard:
        """Generate a scorecard for a single lab.

        Args:
            lab_slug: The lab identifier (e.g., "anthropic").

        Returns:
            Scorecard with all dimension results.

        Raises:
            KeyError: If lab not found in registry.
        """
        lab = self.registry.get(lab_slug)
        if lab is None:
            raise KeyError(f"Lab not found: {lab_slug}")

        from hummbl_governance.evaluations.scorecard_data import (
            LAB_SCORECARDS,
        )

        lab_scores = LAB_SCORECARDS.get(lab_slug, {})
        dimension_results: list[DimensionResult] = []

        for dimension in self.framework.list_dimensions():
            dim_scores = lab_scores.get(dimension.slug, {})

            # Check if conditional dimension applies
            if dimension.conditional:
                if lab.weights == "closed":
                    # Open-weight governance doesn't apply to closed-weight labs
                    dimension_results.append(DimensionResult(
                        dimension_slug=dimension.slug,
                        weighted_score=0.0,
                        applicable=False,
                    ))
                    continue

            dr = self.framework.score_dimension(dimension.slug, dim_scores)
            dimension_results.append(dr)

        result = self.framework.aggregate(lab_slug, dimension_results)
        return Scorecard(result=result, lab=lab)

    def generate_all(self) -> list[Scorecard]:
        """Generate scorecards for all registered labs, sorted by overall score."""
        scorecards = []
        for lab in self.registry.list_all():
            try:
                sc = self.generate(lab.slug)
                scorecards.append(sc)
            except Exception:
                continue
        return sorted(scorecards, key=lambda s: s.overall_score, reverse=True)

    def generate_by_tier(self, tier: str) -> list[Scorecard]:
        """Generate scorecards for labs in a specific tier."""
        scorecards = self.generate_all()
        return [s for s in scorecards if s.lab.tier == tier]

    def export_markdown_table(self) -> str:
        """Export all scorecards as a markdown table.

        Returns:
            Markdown-formatted table string.
        """
        header = (
            "| Lab | Weights | Gov Maturity | Runtime Gov | Compliance | "
            "Agent Gov | Transparency | Open-Weight | Safety Behaviors | "
            "Agent Capability | Overall | % | Level |\n"
            "|-----|---------|-------------|-------------|------------|"
            "-----------|-------------|-------------|-----------------|"
            "-----------------|---------|---|-------|"
        )

        scorecards = self.generate_all()
        rows = [sc.to_markdown_row() for sc in scorecards]
        return header + "\n".join(rows)

    def export_json(self) -> str:
        """Export all scorecards as JSON."""
        import json
        scorecards = self.generate_all()
        return json.dumps(
            [sc.to_dict() for sc in scorecards],
            indent=2,
        )

    def __iter__(self) -> Iterator[Scorecard]:
        return iter(self.generate_all())

    def __len__(self) -> int:
        return self.registry.count()
