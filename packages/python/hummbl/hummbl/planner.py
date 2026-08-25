"""Trace-guided experiment planner — turns analyzer insights into structured plans.

Given a TraceAnalyzer with loaded traces, the planner generates concrete
ExperimentPlans that tell the autoresearch agent what to try next. Plans
are grounded in historical performance data, not vibes.

Planning strategies:
- plan_next():           Best N experiments across all viable categories
- plan_combinatorial():  Combine near-miss changes that individually almost won
- plan_exploration():    Probe underexplored categories with nonzero potential
- plan_from_transfer():  Adapt hypotheses from another machine's trace analysis
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from hummbl.analyzer import (
    AnalysisResult,
    CategoryStats,
    ExperimentRecord,
    TraceAnalyzer,
    get_top_category,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PlannedExperiment:
    """A single experiment proposed by the planner."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    hypothesis: str = ""
    category: str = ""
    change_description: str = ""
    confidence: float = 0.0
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hypothesis": self.hypothesis,
            "category": self.category,
            "change_description": self.change_description,
            "confidence": self.confidence,
            "dependencies": self.dependencies,
        }


@dataclass
class ExperimentPlan:
    """A structured plan for the next N experiments."""
    rationale: str = ""
    experiments: list[PlannedExperiment] = field(default_factory=list)
    estimated_keep_rate: float = 0.0
    priority: str = "medium"  # high, medium, low

    def to_dict(self) -> dict:
        return {
            "rationale": self.rationale,
            "experiments": [e.to_dict() for e in self.experiments],
            "estimated_keep_rate": self.estimated_keep_rate,
            "priority": self.priority,
        }


# ---------------------------------------------------------------------------
# Concrete change templates — keyed by category
# ---------------------------------------------------------------------------

# Each entry: (hypothesis_template, change_template, base_confidence)
# Templates use {placeholders} filled from trace analysis context.
CATEGORY_TEMPLATES: dict[str, list[tuple[str, str, float]]] = {
    "architecture/depth": [
        (
            "Increasing depth to {depth} may capture longer-range dependencies",
            "Set depth={depth} in train.py model config",
            0.3,
        ),
    ],
    "architecture/attention_heads": [
        (
            "Changing n_head={n_head} with head_dim={head_dim} may improve attention quality",
            "Set n_head={n_head}, HEAD_DIM={head_dim} in train.py",
            0.4,
        ),
        (
            "GQA with n_kv_head={n_kv_head} reduces memory while preserving quality",
            "Set n_kv_head={n_kv_head} (GQA) in train.py",
            0.35,
        ),
    ],
    "architecture/width": [
        (
            "Wider model (n_embd={n_embd}) trades compute for capacity",
            "Set n_embd={n_embd} in train.py",
            0.3,
        ),
    ],
    "architecture/mlp": [
        (
            "MLP expansion factor {factor}x may better match the compute budget",
            "Set MLP expansion to {factor}x in train.py",
            0.35,
        ),
    ],
    "architecture/activation": [
        (
            "SwiGLU activation improves over GELU in recent transformer work",
            "Replace activation function with SwiGLU in train.py",
            0.4,
        ),
    ],
    "architecture/token_mixing": [
        (
            "Token mixing with blend factor {blend} may improve cross-position flow",
            "Add token mixing: x = {blend}*x + (1-{blend})*prev_x before attention",
            0.4,
        ),
    ],
    "architecture/value_embed": [
        (
            "Value embedding with resid_lambda={lam} may stabilize deep networks",
            "Enable value embedding with resid_lambda={lam}",
            0.35,
        ),
    ],
    "architecture/normalization": [
        (
            "QK normalization may stabilize attention logits at this scale",
            "Add QK RMSNorm before attention dot products",
            0.3,
        ),
    ],
    "attention/window": [
        (
            "Window pattern {pattern} may balance local and global attention",
            "Set WINDOW_PATTERN='{pattern}' (near window={window})",
            0.4,
        ),
    ],
    "attention/rope": [
        (
            "RoPE base frequency {base} may improve position encoding",
            "Set RoPE theta={base} in train.py",
            0.3,
        ),
    ],
    "attention/softcap": [
        (
            "Softcap at {cap} stabilizes attention without clipping",
            "Set attention softcap={cap} in train.py",
            0.35,
        ),
    ],
    "lr/matrix": [
        (
            "Matrix LR={lr} may be closer to optimal for weight matrices",
            "Set MATRIX_LR={lr} in train.py",
            0.35,
        ),
    ],
    "lr/embedding": [
        (
            "Embedding LR={lr} should differ from matrix LR for embeddings",
            "Set EMBEDDING_LR={lr} in train.py",
            0.3,
        ),
    ],
    "lr/scalar": [
        (
            "Scalar LR={lr} tuning for bias and norm parameters",
            "Set SCALAR_LR={lr} in train.py",
            0.3,
        ),
    ],
    "lr/final_frac": [
        (
            "Final LR fraction {frac} controls endpoint of LR schedule",
            "Set FINAL_LR_FRAC={frac} in train.py",
            0.3,
        ),
    ],
    "optimizer/weight_decay": [
        (
            "Weight decay {wd} may regularize better at this model scale",
            "Set WEIGHT_DECAY={wd} in train.py",
            0.3,
        ),
    ],
    "optimizer/adam": [
        (
            "Adam betas ({b1}, {b2}) tuning for training stability",
            "Set ADAM_BETAS=({b1}, {b2}) in train.py",
            0.3,
        ),
    ],
    "schedule/warmup": [
        (
            "Warmup of {steps} steps may improve early training dynamics",
            "Set WARMUP_STEPS={steps} in train.py",
            0.25,
        ),
    ],
    "schedule/warmdown": [
        (
            "Warmdown fraction {frac} for a smoother LR tail",
            "Set WARMDOWN_FRAC={frac} in train.py",
            0.25,
        ),
    ],
    "training/batch_size": [
        (
            "Batch size {bs} changes the noise/signal tradeoff in gradients",
            "Set TOTAL_BATCH_SIZE=2**{bs_exp} in train.py",
            0.3,
        ),
    ],
    "training/label_smoothing": [
        (
            "Label smoothing {eps} may regularize the output distribution",
            "Set label_smoothing={eps} in loss function",
            0.3,
        ),
    ],
    "training/regularization": [
        (
            "Z-loss coefficient {coeff} penalizes extreme logits",
            "Add z_loss with coefficient={coeff} to the loss computation",
            0.3,
        ),
    ],
}


# ---------------------------------------------------------------------------
# Value extraction from historical experiments
# ---------------------------------------------------------------------------

def _extract_numeric_values(descriptions: list[str], pattern_keyword: str) -> list[float]:
    """Pull numeric values from experiment descriptions matching a keyword.

    Filters out values that are clearly not parameter values (experiment
    indices, very large numbers, etc.).
    """
    import re
    values = []
    for desc in descriptions:
        if pattern_keyword.lower() in desc.lower():
            # Look for patterns like "keyword value" or "keyword=value"
            param_pattern = rf"{re.escape(pattern_keyword)}\s*[=:]?\s*([-+]?\d*\.?\d+(?:e[-+]?\d+)?)"
            matches = re.findall(param_pattern, desc, re.IGNORECASE)
            for m in matches:
                v = float(m)
                # Filter out experiment indices and unreasonable values
                if 1e-8 < abs(v) < 1000:
                    values.append(v)
    return values


def _suggest_perturbation(values: list[float], direction: str = "both") -> list[float]:
    """Given observed values, suggest nearby perturbations to try."""
    if not values:
        return []
    unique = sorted(set(values))
    suggestions = []
    for v in unique:
        if v == 0:
            continue
        if direction in ("both", "lower"):
            suggestions.append(round(v * 0.8, 6))
        if direction in ("both", "higher"):
            suggestions.append(round(v * 1.2, 6))
        # Also try halfway between consecutive values
    if len(unique) >= 2:
        for i in range(len(unique) - 1):
            mid = round((unique[i] + unique[i + 1]) / 2, 6)
            suggestions.append(mid)
    return sorted(set(suggestions))


# ---------------------------------------------------------------------------
# Core planner
# ---------------------------------------------------------------------------

class TracePlanner:
    """Generates experiment plans from trace analysis."""

    def __init__(self, analyzer: TraceAnalyzer):
        self.analyzer = analyzer
        self._result: Optional[AnalysisResult] = None

    @property
    def result(self) -> AnalysisResult:
        if self._result is None:
            self._result = self.analyzer.analyze()
        return self._result

    def _category_confidence(self, category: str) -> float:
        """Compute a confidence score for a category based on history."""
        stats = self.result.category_stats.get(category)
        if stats is None:
            return 0.2  # Unknown category — moderate prior
        if category in self.result.exhausted_categories:
            return 0.05  # Exhausted — very low
        if stats.total == 0:
            return 0.2
        # Base: keep rate, but boost underexplored categories
        base = stats.keep_rate
        if stats.total <= 2 and stats.keeps > 0:
            base = max(base, 0.4)  # Underexplored boost
        return round(min(base, 0.95), 3)

    def _get_near_misses(self, threshold: float = 0.003) -> list[ExperimentRecord]:
        """Find discarded experiments within threshold of the best bpb."""
        if self.result.best_bpb is None:
            return []
        best = self.result.best_bpb
        return [
            r for r in self.analyzer.records
            if r.outcome == "discard"
            and r.val_bpb > 0
            and (r.val_bpb - best) <= threshold
        ]

    def _get_kept_experiments(self) -> list[ExperimentRecord]:
        """Return all kept experiments."""
        return [r for r in self.analyzer.records if r.outcome == "keep"]

    def _descriptions_for_category(self, category: str) -> list[str]:
        """Get all experiment descriptions in a category."""
        return [
            r.description for r in self.analyzer.records
            if r.category == category
        ]

    # -------------------------------------------------------------------
    # Planning strategies
    # -------------------------------------------------------------------

    def plan_next(self, n: int = 5) -> ExperimentPlan:
        """Generate the next N experiments based on trace analysis.

        Strategy:
        1. Rank categories by keep rate (skip exhausted ones)
        2. For promising categories, propose perturbations of kept values
        3. For underexplored categories, propose initial explorations
        4. Mix in one wild-card from a zero-trial category if any exist
        """
        experiments: list[PlannedExperiment] = []

        # Sort categories: promising first, then underexplored, skip exhausted
        ranked = self._rank_categories()

        for cat, stats in ranked:
            if len(experiments) >= n:
                break

            conf = self._category_confidence(cat)
            descs = self._descriptions_for_category(cat)
            kept_descs = [
                r.description for r in self.analyzer.records
                if r.category == cat and r.outcome == "keep"
            ]

            templates = CATEGORY_TEMPLATES.get(cat, [])

            if templates:
                # Use the first template and fill with reasonable values
                hyp_tmpl, change_tmpl, base_conf = templates[0]
                adjusted_conf = round(min(conf * 1.2, 0.9) if stats.keeps > 0 else conf, 3)
                exp = PlannedExperiment(
                    hypothesis=self._fill_template(hyp_tmpl, cat, descs),
                    category=cat,
                    change_description=self._fill_template(change_tmpl, cat, descs),
                    confidence=adjusted_conf,
                )
                experiments.append(exp)
            else:
                # No template — generate a generic proposal from description patterns
                if kept_descs:
                    reference = kept_descs[-1]
                    exp = PlannedExperiment(
                        hypothesis=f"Variant of successful '{cat}' experiment: refine the parameters from '{reference}'",
                        category=cat,
                        change_description=f"Take the kept change '{reference}' and try a +/- 20% perturbation of its key parameter",
                        confidence=conf,
                    )
                elif descs:
                    reference = descs[-1]
                    exp = PlannedExperiment(
                        hypothesis=f"Revisit '{cat}' with a different parameter range than '{reference}'",
                        category=cat,
                        change_description=f"Try a value outside the previously tested range in '{reference}'",
                        confidence=conf,
                    )
                else:
                    exp = PlannedExperiment(
                        hypothesis=f"Initial exploration of '{cat}' category",
                        category=cat,
                        change_description=f"Start with a moderate change in the '{cat}' space",
                        confidence=0.2,
                    )
                experiments.append(exp)

        # Estimate keep rate from the confidences
        avg_conf = sum(e.confidence for e in experiments) / len(experiments) if experiments else 0.0
        priority = "high" if avg_conf > 0.35 else ("medium" if avg_conf > 0.2 else "low")

        return ExperimentPlan(
            rationale=self._build_rationale("next-n", experiments),
            experiments=experiments,
            estimated_keep_rate=round(avg_conf, 3),
            priority=priority,
        )

    def plan_combinatorial(self) -> ExperimentPlan:
        """Generate experiments that combine near-miss changes.

        Near-misses are discarded experiments within 0.003 bpb of the best.
        The idea: each individually didn't beat the best, but combining
        two near-miss changes from different categories might.
        """
        near_misses = self._get_near_misses(threshold=0.003)
        experiments: list[PlannedExperiment] = []

        if len(near_misses) < 2:
            return ExperimentPlan(
                rationale="Not enough near-miss experiments to generate combinations (need at least 2 discards within 0.003 of best)",
                experiments=[],
                estimated_keep_rate=0.0,
                priority="low",
            )

        # Group near-misses by top-level category to find cross-category combos
        by_top_cat: dict[str, list[ExperimentRecord]] = {}
        for r in near_misses:
            top = get_top_category(r.category)
            by_top_cat.setdefault(top, []).append(r)

        top_cats = list(by_top_cat.keys())

        # Generate pairwise combinations across top-level categories
        seen_pairs: set[tuple[str, str]] = set()
        for i, cat_a in enumerate(top_cats):
            for cat_b in top_cats[i + 1:]:
                if len(experiments) >= 5:
                    break
                pair = (cat_a, cat_b)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                rec_a = by_top_cat[cat_a][0]
                rec_b = by_top_cat[cat_b][0]

                delta_a = abs(rec_a.delta_bpb) if rec_a.delta_bpb is not None else 0
                delta_b = abs(rec_b.delta_bpb) if rec_b.delta_bpb is not None else 0

                exp = PlannedExperiment(
                    hypothesis=(
                        f"Combining near-miss '{rec_a.description}' "
                        f"(delta={rec_a.delta_bpb:+.6f}) with '{rec_b.description}' "
                        f"(delta={rec_b.delta_bpb:+.6f}) may yield a joint improvement"
                    ),
                    category=f"combo/{cat_a}+{cat_b}",
                    change_description=(
                        f"Apply both changes simultaneously: "
                        f"(1) {rec_a.description}, (2) {rec_b.description}"
                    ),
                    confidence=round(min(0.3 + delta_a * 100 + delta_b * 100, 0.6), 3),
                )
                experiments.append(exp)

        # Also combine near-misses within the same category (different subcategories)
        for top_cat, recs in by_top_cat.items():
            if len(experiments) >= 8:
                break
            subcats = set(r.category for r in recs)
            if len(subcats) >= 2:
                sub_recs = []
                for sc in subcats:
                    sub_recs.append(next(r for r in recs if r.category == sc))
                if len(sub_recs) >= 2:
                    r1, r2 = sub_recs[0], sub_recs[1]
                    exp = PlannedExperiment(
                        hypothesis=(
                            f"Joint tuning within '{top_cat}': "
                            f"'{r1.description}' + '{r2.description}'"
                        ),
                        category=f"combo/{r1.category}+{r2.category}",
                        change_description=(
                            f"Apply both {top_cat} changes: "
                            f"(1) {r1.description}, (2) {r2.description}"
                        ),
                        confidence=0.35,
                    )
                    experiments.append(exp)

        avg_conf = sum(e.confidence for e in experiments) / len(experiments) if experiments else 0.0

        return ExperimentPlan(
            rationale=(
                f"Found {len(near_misses)} near-miss experiments (within 0.003 bpb of best). "
                f"These changes individually weren't enough, but combinations may "
                f"push past the current best of {self.result.best_bpb:.6f}"
            ),
            experiments=experiments,
            estimated_keep_rate=round(avg_conf, 3),
            priority="high" if len(experiments) >= 3 else "medium",
        )

    def plan_exploration(self) -> ExperimentPlan:
        """Generate experiments in underexplored categories.

        Targets:
        - Categories with 1-2 experiments and at least one keep
        - Categories with 0 experiments (from the template list)
        - Subcategories of successful top-level categories
        """
        experiments: list[PlannedExperiment] = []

        # 1. Categories with few experiments but nonzero keep rate
        for cat, stats in self.result.category_stats.items():
            if cat == "baseline" or cat in self.result.exhausted_categories:
                continue
            if stats.total <= 2 and stats.keeps > 0:
                descs = self._descriptions_for_category(cat)
                templates = CATEGORY_TEMPLATES.get(cat, [])
                if templates:
                    hyp_tmpl, change_tmpl, base_conf = templates[0]
                    exp = PlannedExperiment(
                        hypothesis=f"[UNDEREXPLORED] {self._fill_template(hyp_tmpl, cat, descs)}",
                        category=cat,
                        change_description=self._fill_template(change_tmpl, cat, descs),
                        confidence=round(stats.keep_rate * 0.8, 3),
                    )
                else:
                    exp = PlannedExperiment(
                        hypothesis=f"[UNDEREXPLORED] Further explore '{cat}' — {stats.keeps}/{stats.total} kept so far",
                        category=cat,
                        change_description=f"Try a finer-grained sweep around the kept value in '{descs[-1] if descs else cat}'",
                        confidence=round(stats.keep_rate * 0.8, 3),
                    )
                experiments.append(exp)

        # 2. Template categories never tried
        tried_cats = set(self.result.category_stats.keys())
        for cat in CATEGORY_TEMPLATES:
            if cat not in tried_cats and len(experiments) < 8:
                templates = CATEGORY_TEMPLATES[cat]
                hyp_tmpl, change_tmpl, base_conf = templates[0]
                exp = PlannedExperiment(
                    hypothesis=f"[UNTRIED] {self._fill_template(hyp_tmpl, cat, [])}",
                    category=cat,
                    change_description=self._fill_template(change_tmpl, cat, []),
                    confidence=round(base_conf * 0.5, 3),  # Low confidence for untried
                )
                experiments.append(exp)

        # 3. Subcategory expansion: if "architecture/attention_heads" worked,
        #    try other "architecture/*" subcategories
        successful_tops = set()
        for cat, stats in self.result.category_stats.items():
            if stats.keeps > 0:
                successful_tops.add(get_top_category(cat))

        for cat in CATEGORY_TEMPLATES:
            top = get_top_category(cat)
            if top in successful_tops and cat not in tried_cats and len(experiments) < 10:
                templates = CATEGORY_TEMPLATES[cat]
                hyp_tmpl, change_tmpl, base_conf = templates[0]
                exp = PlannedExperiment(
                    hypothesis=f"[SIBLING] '{top}' category has wins — try subcategory '{cat}'",
                    category=cat,
                    change_description=self._fill_template(change_tmpl, cat, []),
                    confidence=round(base_conf * 0.7, 3),
                )
                # Check not already added
                if not any(e.category == cat for e in experiments):
                    experiments.append(exp)

        avg_conf = sum(e.confidence for e in experiments) / len(experiments) if experiments else 0.0

        return ExperimentPlan(
            rationale=(
                f"Exploration plan targeting {len(experiments)} underexplored or "
                f"untried categories. Successful top-level categories: "
                f"{', '.join(sorted(successful_tops)) if successful_tops else 'none'}"
            ),
            experiments=experiments,
            estimated_keep_rate=round(avg_conf, 3),
            priority="medium",
        )

    def plan_from_transfer(self, transfer_hypotheses: list[dict]) -> ExperimentPlan:
        """Generate experiments from cross-machine transfer hypotheses.

        Each hypothesis dict should have:
            - hypothesis: str
            - category: str
            - change_description: str
            - source_machine: str
            - source_delta_bpb: float (optional)
        """
        experiments: list[PlannedExperiment] = []

        for th in transfer_hypotheses:
            cat = th.get("category", "other")
            source = th.get("source_machine", "unknown")
            source_delta = th.get("source_delta_bpb")

            # Check if this category is exhausted on our machine
            if cat in self.result.exhausted_categories:
                conf = 0.1  # Very low — exhausted here even if it worked elsewhere
            else:
                local_stats = self.result.category_stats.get(cat)
                if local_stats and local_stats.total > 0:
                    # We have data — weight by local keep rate
                    conf = round(local_stats.keep_rate * 0.7 + 0.15, 3)
                else:
                    # Never tried locally — moderate confidence from transfer
                    conf = 0.3

            # Boost if the source saw a large improvement
            if source_delta is not None and source_delta < -0.002:
                conf = round(min(conf + 0.15, 0.7), 3)

            exp = PlannedExperiment(
                hypothesis=f"[TRANSFER from {source}] {th.get('hypothesis', '')}",
                category=cat,
                change_description=th.get("change_description", ""),
                confidence=conf,
            )
            experiments.append(exp)

        avg_conf = sum(e.confidence for e in experiments) / len(experiments) if experiments else 0.0

        return ExperimentPlan(
            rationale=(
                f"Transfer plan: {len(experiments)} hypotheses adapted from "
                f"other machines. Confidence adjusted for local category performance."
            ),
            experiments=experiments,
            estimated_keep_rate=round(avg_conf, 3),
            priority="medium" if avg_conf > 0.2 else "low",
        )

    # -------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------

    def to_strategy_md(self, plan: ExperimentPlan) -> str:
        """Export plan as strategy.md for the autoresearch agent.

        Format follows the program.md strategy checkpointing convention:
        a numbered list of experiments with rationale and parameters.
        """
        lines = []
        lines.append("# Experiment Strategy")
        lines.append("")
        lines.append(f"**Priority:** {plan.priority}")
        lines.append(f"**Estimated keep rate:** {plan.estimated_keep_rate:.0%}")
        lines.append("")
        lines.append("## Rationale")
        lines.append("")
        lines.append(plan.rationale)
        lines.append("")
        lines.append("## Planned Experiments")
        lines.append("")

        for i, exp in enumerate(plan.experiments, 1):
            lines.append(f"### Experiment {i}: {exp.category}")
            lines.append("")
            lines.append(f"- **Hypothesis:** {exp.hypothesis}")
            lines.append(f"- **Change:** {exp.change_description}")
            lines.append(f"- **Confidence:** {exp.confidence:.0%}")
            if exp.dependencies:
                lines.append(f"- **Depends on:** {', '.join(exp.dependencies)}")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated by HUMMBL TracePlanner — {len(plan.experiments)} experiments queued*")
        return "\n".join(lines)

    def format_plan(self, plan: ExperimentPlan) -> str:
        """Format a plan for terminal display."""
        lines = []
        lines.append("=" * 70)
        lines.append("HUMMBL EXPERIMENT PLAN")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"  Priority:            {plan.priority}")
        lines.append(f"  Estimated keep rate: {plan.estimated_keep_rate:.0%}")
        lines.append(f"  Experiments:         {len(plan.experiments)}")
        lines.append("")
        lines.append("RATIONALE")
        lines.append("-" * 40)
        lines.append(f"  {plan.rationale}")
        lines.append("")
        lines.append("EXPERIMENTS")
        lines.append("-" * 70)

        for i, exp in enumerate(plan.experiments, 1):
            lines.append("")
            lines.append(f"  {i}. [{exp.category}] (confidence: {exp.confidence:.0%})")
            lines.append(f"     Hypothesis:  {exp.hypothesis}")
            lines.append(f"     Change:      {exp.change_description}")
            if exp.dependencies:
                lines.append(f"     Depends on:  {', '.join(exp.dependencies)}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _rank_categories(self) -> list[tuple[str, CategoryStats]]:
        """Rank categories by planning priority.

        Order: promising > underexplored > low-volume > exhausted (excluded).
        """
        items = []
        for cat, stats in self.result.category_stats.items():
            if cat == "baseline":
                continue
            if cat in self.result.exhausted_categories:
                continue
            # Score: keep_rate * sqrt(total) — rewards both success and coverage
            import math
            score = stats.keep_rate * math.sqrt(stats.total + 1)
            # Boost underexplored
            if stats.total <= 2 and stats.keeps > 0:
                score += 0.5
            items.append((cat, stats, score))

        items.sort(key=lambda x: -x[2])
        return [(cat, stats) for cat, stats, _ in items]

    def _fill_template(self, template: str, category: str, descriptions: list[str]) -> str:
        """Fill a template string with reasonable values from history.

        If no history exists, use sensible defaults.
        """
        # Extract numeric values from descriptions for this category
        values = _extract_numeric_values(descriptions, category.split("/")[-1])
        suggestions = _suggest_perturbation(values) if values else []

        # Build a context dict with defaults and perturbations
        ctx: dict[str, str] = {}

        # Category-specific defaults
        defaults: dict[str, dict[str, str]] = {
            "architecture/depth": {"depth": "10"},
            "architecture/attention_heads": {"n_head": "8", "head_dim": "64", "n_kv_head": "4"},
            "architecture/width": {"n_embd": "768"},
            "architecture/mlp": {"factor": "4"},
            "architecture/token_mixing": {"blend": "0.1"},
            "architecture/value_embed": {"lam": "0.5"},
            "attention/window": {"pattern": "NNSSL", "window": "256"},
            "attention/rope": {"base": "10000"},
            "attention/softcap": {"cap": "50.0"},
            "lr/matrix": {"lr": "0.001"},
            "lr/embedding": {"lr": "0.01"},
            "lr/scalar": {"lr": "0.01"},
            "lr/final_frac": {"frac": "0.1"},
            "optimizer/weight_decay": {"wd": "0.1"},
            "optimizer/adam": {"b1": "0.9", "b2": "0.95"},
            "schedule/warmup": {"steps": "100"},
            "schedule/warmdown": {"frac": "0.3"},
            "training/batch_size": {"bs": "65536", "bs_exp": "16"},
            "training/label_smoothing": {"eps": "0.1"},
            "training/regularization": {"coeff": "1e-4"},
        }

        if category in defaults:
            ctx.update(defaults[category])

        # Override with perturbations from history
        if suggestions and category in defaults:
            keys = list(defaults[category].keys())
            if keys and suggestions:
                ctx[keys[0]] = str(suggestions[len(suggestions) // 2])

        # Safe format — ignore missing keys
        try:
            return template.format(**ctx)
        except KeyError:
            return template

    def _build_rationale(self, strategy: str, experiments: list[PlannedExperiment]) -> str:
        """Build a rationale string from context."""
        cats = [e.category for e in experiments]
        cat_counts: dict[str, int] = {}
        for c in cats:
            top = get_top_category(c)
            cat_counts[top] = cat_counts.get(top, 0) + 1

        parts = []
        if strategy == "next-n":
            parts.append(
                f"Plan {len(experiments)} experiments based on category performance analysis."
            )
            if self.result.best_bpb is not None:
                parts.append(f"Current best: {self.result.best_bpb:.6f} bpb.")
            if self.result.diminishing_returns:
                parts.append("Note: diminishing returns detected — prioritizing novel categories.")
            if self.result.current_discard_streak >= 5:
                parts.append(
                    f"Currently on a {self.result.current_discard_streak}-experiment "
                    "discard streak — mixing in exploratory experiments."
                )
            focus = ", ".join(f"{k}({v})" for k, v in sorted(cat_counts.items(), key=lambda x: -x[1]))
            parts.append(f"Focus areas: {focus}.")

        return " ".join(parts)
