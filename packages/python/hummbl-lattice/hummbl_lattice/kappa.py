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

"""Fleiss' kappa calculator for Domain120 cross-rating (Severe Test 2).

Computes inter-rater reliability for the stopping rule validation.
Designed for the Domain120 Lattice Design Cohort's week 5 cross-rating phase.

Usage::

    from hummbl_lattice import KappaCalculator

    calc = KappaCalculator()
    result = calc.compute("ratings.csv")
    print(result.kappa, result.interpretation)

CSV format::

    item_id,rater_id,classification,confidence,justification,language,item_language
    op-001,rater-01,reasoning_operator,5,"This tells you how to decompose"
    op-002,rater-01,domain_knowledge,3,"This tells you what material to use"
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = ("reasoning_operator", "domain_knowledge")
THRESHOLD = 0.6


def _interpret_kappa(k: float) -> str:
    """Landis & Koch (1977) interpretation."""
    if k < 0:
        return "poor agreement"
    elif k <= 0.20:
        return "slight agreement"
    elif k <= 0.40:
        return "fair agreement"
    elif k <= 0.60:
        return "moderate agreement"
    elif k <= 0.80:
        return "substantial agreement"
    else:
        return "almost perfect agreement"


@dataclass
class ItemAgreement:
    """Per-item agreement breakdown."""
    item_id: str
    n_raters: int
    reasoning_count: int
    knowledge_count: int
    majority: str
    agreement: float
    ambiguous: bool


@dataclass
class RaterAgreement:
    """Per-rater agreement with majority."""
    rater_id: str
    n_items: int
    agreement_with_majority: float
    outlier: bool


@dataclass
class KappaResult:
    """Complete kappa computation result."""
    kappa: float = 0.0
    p_observed: float = 0.0
    p_expected: float = 0.0
    n_items: int = 0
    n_raters_per_item: int = 0
    category_proportions: dict[str, float] = field(default_factory=dict)
    interpretation: str = ""
    threshold_passed: bool = False
    ambiguous_items: list[ItemAgreement] = field(default_factory=list)
    outlier_raters: list[RaterAgreement] = field(default_factory=list)
    same_language_kappa: float | None = None
    cross_language_kappa: float | None = None
    weighted_agreement: float = 0.0

    def summary(self) -> str:
        """One-line summary."""
        status = "PASS" if self.threshold_passed else "FAIL"
        return (
            f"κ={self.kappa:.4f} ({self.interpretation}), "
            f"threshold {THRESHOLD}: {status}, "
            f"ambiguous: {len(self.ambiguous_items)}, "
            f"outliers: {len(self.outlier_raters)}"
        )

    def to_text(self) -> str:
        """Full text report."""
        lines = [
            "=" * 70,
            "Domain120 Severe Test 2 — Fleiss' Kappa Report",
            "=" * 70,
            "",
            "OVERALL FLEISS' KAPPA",
            "-" * 40,
            f"  Kappa:              {self.kappa:.4f}",
            f"  Interpretation:     {self.interpretation}",
            f"  P_o (observed):     {self.p_observed:.4f}",
            f"  P_e (expected):     {self.p_expected:.4f}",
            f"  Items:              {self.n_items}",
            f"  Raters per item:    {self.n_raters_per_item}",
            f"  Category proportions: {self.category_proportions}",
            "",
        ]
        if self.threshold_passed:
            lines.append(f"  THRESHOLD CHECK: PASS (κ >= {THRESHOLD})")
        else:
            lines.append(f"  THRESHOLD CHECK: FAIL (κ < {THRESHOLD})")
        lines.append("")

        if self.same_language_kappa is not None:
            lines.append(f"  Same-language kappa:    {self.same_language_kappa:.4f}")
        if self.cross_language_kappa is not None:
            lines.append(f"  Cross-language kappa:   {self.cross_language_kappa:.4f}")
        if self.weighted_agreement > 0:
            lines.append(f"  Confidence-weighted:    {self.weighted_agreement:.4f}")
        lines.append("")
        lines.append("=" * 70)
        lines.append(self.summary())
        lines.append("")
        return "\n".join(lines)


class KappaCalculator:
    """Computes Fleiss' kappa for Domain120 cross-rating data."""

    def compute(self, filepath: str | Path) -> KappaResult:
        """Compute Fleiss' kappa from a ratings CSV file.

        Args:
            filepath: Path to the ratings CSV.

        Returns:
            KappaResult with kappa, per-item agreement, per-rater agreement,
            and language-split kappa (if language data is present).
        """
        ratings = self._load_ratings(filepath)
        return self._compute(ratings)

    def _load_ratings(self, filepath: str | Path) -> list[dict]:
        """Load ratings from CSV."""
        ratings = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ratings.append({
                    "item_id": row["item_id"],
                    "rater_id": row["rater_id"],
                    "classification": row["classification"].strip().lower(),
                    "confidence": int(row.get("confidence", 3)),
                    "justification": row.get("justification", ""),
                    "language": row.get("language", "en"),
                    "item_language": row.get("item_language", "en"),
                })
        return ratings

    def _compute(self, ratings: list[dict], _skip_lang_split: bool = False) -> KappaResult:
        """Compute kappa from loaded ratings."""
        result = KappaResult()

        # Build rating matrix
        items: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        item_rater_count: dict[str, int] = defaultdict(int)

        for r in ratings:
            items[r["item_id"]][r["classification"]] += 1
            item_rater_count[r["item_id"]] += 1

        n_items = len(items)
        if n_items == 0:
            return result

        n = round(statistics.mean(item_rater_count.values()))

        # Category proportions
        cat_totals: dict[str, int] = defaultdict(int)
        total = 0
        for cats in items.values():
            for cat in CATEGORIES:
                c = cats.get(cat, 0)
                cat_totals[cat] += c
                total += c

        p_j = {cat: cat_totals[cat] / total for cat in CATEGORIES} if total > 0 else {cat: 0 for cat in CATEGORIES}

        # P_o: observed agreement
        p_o = 0.0
        for item_id, cats in items.items():
            n_i = item_rater_count[item_id]
            if n_i <= 1:
                continue
            sum_sq = sum(cats.get(cat, 0) ** 2 for cat in CATEGORIES)
            p_o += (sum_sq - n_i) / (n_i * (n_i - 1))
        p_o /= n_items

        # P_e: expected agreement
        p_e = sum(p_j[cat] ** 2 for cat in CATEGORIES)

        # Kappa
        kappa = (p_o - p_e) / (1 - p_e) if (1 - p_e) != 0 else 1.0

        result.kappa = round(kappa, 4)
        result.p_observed = round(p_o, 4)
        result.p_expected = round(p_e, 4)
        result.n_items = n_items
        result.n_raters_per_item = n
        result.category_proportions = {cat: round(p, 4) for cat, p in p_j.items()}
        result.interpretation = _interpret_kappa(kappa)
        result.threshold_passed = kappa >= THRESHOLD

        # Per-item agreement
        result.ambiguous_items = self._per_item_agreement(ratings)

        # Per-rater agreement
        result.outlier_raters = self._per_rater_agreement(ratings)

        # Language split (only at top level to avoid recursion)
        if not _skip_lang_split:
            has_lang = any(
                r.get("language", "en") != "en" or r.get("item_language", "en") != "en"
                for r in ratings
            )
            if has_lang:
                same = [r for r in ratings if r.get("language", "en") == r.get("item_language", "en")]
                cross = [r for r in ratings if r.get("language", "en") != r.get("item_language", "en")]
                if same:
                    sl = self._compute(same, _skip_lang_split=True)
                    result.same_language_kappa = sl.kappa
                if cross:
                    cl = self._compute(cross, _skip_lang_split=True)
                    result.cross_language_kappa = cl.kappa

        # Confidence-weighted
        result.weighted_agreement = self._weighted_agreement(ratings)

        return result

    def _per_item_agreement(self, ratings: list[dict]) -> list[ItemAgreement]:
        """Compute per-item agreement — identifies ambiguous items."""
        items: dict[str, list[str]] = defaultdict(list)
        for r in ratings:
            items[r["item_id"]].append(r["classification"])

        results = []
        for item_id, classes in items.items():
            n = len(classes)
            reasoning = sum(1 for c in classes if c == "reasoning_operator")
            knowledge = n - reasoning
            majority = "reasoning_operator" if reasoning > knowledge else "domain_knowledge"
            agreement = max(reasoning, knowledge) / n
            results.append(ItemAgreement(
                item_id=item_id,
                n_raters=n,
                reasoning_count=reasoning,
                knowledge_count=knowledge,
                majority=majority,
                agreement=round(agreement, 4),
                ambiguous=agreement < 0.7,
            ))
        results.sort(key=lambda x: x.agreement)
        return results

    def _per_rater_agreement(self, ratings: list[dict]) -> list[RaterAgreement]:
        """Compute per-rater agreement with majority."""
        # Majority per item
        items: dict[str, list[str]] = defaultdict(list)
        for r in ratings:
            items[r["item_id"]].append(r["classification"])

        item_majority: dict[str, str] = {}
        for item_id, classes in items.items():
            reasoning = sum(1 for c in classes if c == "reasoning_operator")
            knowledge = len(classes) - reasoning
            item_majority[item_id] = "reasoning_operator" if reasoning > knowledge else "domain_knowledge"

        # Per-rater
        raters: dict[str, list[dict]] = defaultdict(list)
        for r in ratings:
            raters[r["rater_id"]].append(r)

        results = []
        for rater_id, rater_ratings in raters.items():
            n = len(rater_ratings)
            agree = sum(1 for r in rater_ratings if r["classification"] == item_majority[r["item_id"]])
            results.append(RaterAgreement(
                rater_id=rater_id,
                n_items=n,
                agreement_with_majority=round(agree / n, 4) if n > 0 else 0,
                outlier=(agree / n) < 0.6 if n > 0 else False,
            ))
        results.sort(key=lambda x: x.agreement_with_majority)
        return results

    def _weighted_agreement(self, ratings: list[dict]) -> float:
        """Confidence-weighted agreement score."""
        items: dict[str, list[dict]] = defaultdict(list)
        for r in ratings:
            items[r["item_id"]].append(r)

        agreements = []
        for item_ratings in items.values():
            if len(item_ratings) < 2:
                continue
            reasoning_w = sum(r["confidence"] for r in item_ratings if r["classification"] == "reasoning_operator")
            knowledge_w = sum(r["confidence"] for r in item_ratings if r["classification"] == "domain_knowledge")
            total_w = reasoning_w + knowledge_w
            if total_w == 0:
                continue
            agreements.append(max(reasoning_w, knowledge_w) / total_w)

        return round(statistics.mean(agreements), 4) if agreements else 0.0
