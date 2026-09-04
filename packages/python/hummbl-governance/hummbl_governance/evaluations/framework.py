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

"""Evaluation Framework -- Core scoring engine for model evaluation.

Defines the evaluation dimensions, criteria, scoring levels, and aggregation
methodology for HUMMBL's model evaluation framework.

Scoring:
    Each criterion is scored 0-5. Each dimension aggregates its criteria.
    Each lab's scorecard aggregates all dimensions. Weights are applied
    per-dimension based on HUMMBL's governance-focused priorities.

    Dimension weights (sum to 1.0):
        Governance Maturity:    0.20  (safety framework quality)
        Runtime Governance:     0.20  (deployment-time controls)
        Compliance Posture:     0.15  (regulatory alignment)
        Agent Governance:       0.15  (multi-agent coordination)
        Transparency:           0.10  (documentation and disclosure)
        Open-Weight Governance: 0.05  (conditional, for open-weight labs)
        Safety Behaviors:       0.10  (API-tested, runtime)
        Agent Capability:       0.05  (API-tested, capability)

Usage:
    from hummbl_governance.evaluations.framework import (
        EvaluationFramework, Dimension, Criterion, ScoreLevel,
    )

    framework = EvaluationFramework()
    print(framework.dimension_count)
    print(framework.total_weight)

    # Score a single criterion
    result = framework.score_criterion("governance_maturity", "safety_framework_published", 4)
    print(result.level, result.description)

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class ScoreLevel(str, Enum):
    """Qualitative level for a 0-5 score."""

    NONE = "none"          # 0: No capability or coverage
    MINIMAL = "minimal"    # 1: Basic awareness or ad-hoc
    DEVELOPING = "developing"  # 2: Partial implementation
    ESTABLISHED = "established"  # 3: Systematic implementation
    ADVANCED = "advanced"  # 4: Comprehensive with verification
    EXEMPLARY = "exemplary"  # 5: Industry-leading with external validation

    @classmethod
    def from_score(cls, score: int) -> "ScoreLevel":
        """Map a 0-5 score to a qualitative level."""
        levels = [cls.NONE, cls.MINIMAL, cls.DEVELOPING,
                  cls.ESTABLISHED, cls.ADVANCED, cls.EXEMPLARY]
        if score < 0 or score > 5:
            raise ValueError(f"Score must be 0-5, got {score}")
        return levels[score]


@dataclass(frozen=True)
class Criterion:
    """A single evaluation criterion within a dimension.

    Attributes:
        slug: URL-safe identifier (e.g., "safety_framework_published").
        name: Human-readable name.
        description: What this criterion measures.
        weight: Relative weight within the dimension (0.0-1.0).
        rubric: Tuple of 6 strings describing score levels 0-5.
        api_testable: Whether this criterion can be tested via API.
    """

    slug: str
    name: str
    description: str
    weight: float
    rubric: tuple[str, str, str, str, str, str]  # 6 levels: 0-5
    api_testable: bool = False


@dataclass(frozen=True)
class Dimension:
    """An evaluation dimension containing multiple criteria.

    Attributes:
        slug: URL-safe identifier (e.g., "governance_maturity").
        name: Human-readable name.
        description: What this dimension measures.
        weight: Weight in the overall scorecard (0.0-1.0).
        criteria: Tuple of Criterion objects.
        conditional: Whether this dimension only applies to some labs.
    """

    slug: str
    name: str
    description: str
    weight: float
    criteria: tuple[Criterion, ...]
    conditional: bool = False

    @property
    def criterion_count(self) -> int:
        return len(self.criteria)

    @property
    def total_criterion_weight(self) -> float:
        """Sum of all criterion weights (should be 1.0)."""
        return sum(c.weight for c in self.criteria)


@dataclass
class CriterionResult:
    """Result of scoring a single criterion.

    Attributes:
        criterion_slug: The criterion identifier.
        score: 0-5 score (or None for N/A).
        level: Qualitative score level.
        notes: Optional notes explaining the score.
    """

    criterion_slug: str
    score: int | None
    level: ScoreLevel | None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "criterion": self.criterion_slug,
            "score": self.score,
            "level": self.level.value if self.level else None,
            "notes": self.notes,
        }


@dataclass
class DimensionResult:
    """Result of scoring a single dimension.

    Attributes:
        dimension_slug: The dimension identifier.
        weighted_score: Weighted score (0-5) for this dimension.
        criterion_results: List of per-criterion results.
        applicable: Whether this dimension applies to the lab.
    """

    dimension_slug: str
    weighted_score: float
    criterion_results: list[CriterionResult] = field(default_factory=list)
    applicable: bool = True

    @property
    def max_score(self) -> float:
        return 5.0

    @property
    def percentage(self) -> float:
        """Score as percentage of maximum (0-100)."""
        return (self.weighted_score / self.max_score) * 100 if self.applicable else 0.0

    @property
    def level(self) -> ScoreLevel:
        """Qualitative level for the dimension score."""
        score = round(self.weighted_score)
        return ScoreLevel.from_score(max(0, min(5, score)))

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension_slug,
            "weighted_score": round(self.weighted_score, 2),
            "percentage": round(self.percentage, 1),
            "level": self.level.value,
            "applicable": self.applicable,
            "criteria": [cr.to_dict() for cr in self.criterion_results],
        }


@dataclass
class ScorecardResult:
    """Complete scorecard result for a single lab.

    Attributes:
        lab_slug: The lab identifier.
        dimensions: List of dimension results.
        overall_score: Weighted overall score (0-5).
        overall_percentage: Score as percentage (0-100).
        overall_level: Qualitative level for the overall score.
    """

    lab_slug: str
    dimensions: list[DimensionResult] = field(default_factory=list)
    overall_score: float = 0.0
    overall_percentage: float = 0.0
    overall_level: ScoreLevel = ScoreLevel.NONE

    def to_dict(self) -> dict:
        return {
            "lab": self.lab_slug,
            "overall_score": round(self.overall_score, 2),
            "overall_percentage": round(self.overall_percentage, 1),
            "overall_level": self.overall_level.value,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)


class EvaluationFramework:
    """Core evaluation framework with dimension definitions and scoring engine.

    Dimensions are registered at construction time from the rubrics module.
    The framework provides scoring, aggregation, and level classification.
    """

    def __init__(self, dimensions: tuple[Dimension, ...] | None = None) -> None:
        if dimensions is None:
            from hummbl_governance.evaluations.rubrics import ALL_DIMENSIONS
            dimensions = ALL_DIMENSIONS
        self._dimensions: dict[str, Dimension] = {d.slug: d for d in dimensions}

    @property
    def dimension_count(self) -> int:
        return len(self._dimensions)

    @property
    def total_weight(self) -> float:
        """Sum of all dimension weights (should be 1.0)."""
        return sum(d.weight for d in self._dimensions.values())

    def get_dimension(self, slug: str) -> Dimension | None:
        return self._dimensions.get(slug)

    def list_dimensions(self) -> list[Dimension]:
        return list(self._dimensions.values())

    def score_criterion(
        self, dimension_slug: str, criterion_slug: str, score: int,
        notes: str = "",
    ) -> CriterionResult:
        """Score a single criterion and return a result.

        Args:
            dimension_slug: The dimension containing the criterion.
            criterion_slug: The criterion to score.
            score: 0-5 score (or -1 for N/A, which becomes None).
            notes: Optional notes explaining the score.

        Returns:
            CriterionResult with the score and qualitative level.

        Raises:
            KeyError: If dimension or criterion not found.
            ValueError: If score is not 0-5 or -1.
        """
        dimension = self._dimensions.get(dimension_slug)
        if dimension is None:
            raise KeyError(f"Dimension not found: {dimension_slug}")

        criterion = None
        for c in dimension.criteria:
            if c.slug == criterion_slug:
                criterion = c
                break
        if criterion is None:
            raise KeyError(f"Criterion not found: {criterion_slug} in {dimension_slug}")

        if score == -1:
            return CriterionResult(
                criterion_slug=criterion_slug,
                score=None,
                level=None,
                notes=notes or "N/A (not applicable)",
            )

        if score < 0 or score > 5:
            raise ValueError(f"Score must be 0-5 or -1 for N/A, got {score}")

        return CriterionResult(
            criterion_slug=criterion_slug,
            score=score,
            level=ScoreLevel.from_score(score),
            notes=notes,
        )

    def score_dimension(
        self, dimension_slug: str, scores: dict[str, int | None],
    ) -> DimensionResult:
        """Score a full dimension from a dict of criterion scores.

        Args:
            dimension_slug: The dimension to score.
            scores: Dict mapping criterion slug to score (0-5) or None (N/A).

        Returns:
            DimensionResult with weighted score and per-criterion results.
        """
        dimension = self._dimensions.get(dimension_slug)
        if dimension is None:
            raise KeyError(f"Dimension not found: {dimension_slug}")

        results: list[CriterionResult] = []
        total_weight = 0.0
        weighted_sum = 0.0

        for criterion in dimension.criteria:
            raw_score = scores.get(criterion.slug)
            if raw_score is None:
                # N/A — exclude from weighting
                results.append(CriterionResult(
                    criterion_slug=criterion.slug,
                    score=None,
                    level=None,
                    notes="N/A",
                ))
                continue

            result = self.score_criterion(
                dimension_slug, criterion.slug, raw_score,
            )
            results.append(result)
            weighted_sum += result.score * criterion.weight
            total_weight += criterion.weight

        if total_weight == 0:
            return DimensionResult(
                dimension_slug=dimension_slug,
                weighted_score=0.0,
                criterion_results=results,
                applicable=False,
            )

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        return DimensionResult(
            dimension_slug=dimension_slug,
            weighted_score=weighted_score,
            criterion_results=results,
            applicable=True,
        )

    def aggregate(
        self, lab_slug: str, dimension_results: list[DimensionResult],
    ) -> ScorecardResult:
        """Aggregate dimension results into a complete scorecard.

        Args:
            lab_slug: The lab identifier.
            dimension_results: List of per-dimension results.

        Returns:
            ScorecardResult with weighted overall score.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for dr in dimension_results:
            if not dr.applicable:
                continue
            dimension = self._dimensions.get(dr.dimension_slug)
            if dimension is None:
                continue
            weighted_sum += dr.weighted_score * dimension.weight
            total_weight += dimension.weight

        overall = weighted_sum / total_weight if total_weight > 0 else 0.0
        overall_pct = (overall / 5.0) * 100
        overall_level = ScoreLevel.from_score(max(0, min(5, round(overall))))

        return ScorecardResult(
            lab_slug=lab_slug,
            dimensions=dimension_results,
            overall_score=overall,
            overall_percentage=overall_pct,
            overall_level=overall_level,
        )

    def __iter__(self) -> Iterator[Dimension]:
        return iter(self.list_dimensions())

    def __len__(self) -> int:
        return self.dimension_count
