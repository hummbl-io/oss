"""Trace analysis engine — turns passive reasoning traces into active insights.

Analyzes autoresearch experiment traces to find:
- Win/loss patterns and streaks
- Category-level performance (what types of changes succeed?)
- Diminishing returns detection
- Dead ends and unexplored combinations
- Suggestions for next experiments

This is the intelligence layer on top of HUMMBL's data model.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Category extraction — the key to pattern analysis
# ---------------------------------------------------------------------------

# Maps regex patterns to semantic categories. Order matters: first match wins.
CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"baseline", "baseline"),
    (r"DEPTH|depth", "architecture/depth"),
    (r"HEAD_DIM|head_dim|n_head|n_kv_head|GQA", "architecture/attention_heads"),
    (r"ASPECT_RATIO|n_embd", "architecture/width"),
    (r"MLP.*(expansion|[0-9]+x)|MLP dropout", "architecture/mlp"),
    (r"SwiGLU|GELU|ReLU|activation", "architecture/activation"),
    (r"parallel attn|sequential", "architecture/layout"),
    (r"MoE|expert", "architecture/moe"),
    (r"differential attention", "architecture/diff_attn"),
    (r"token.?mixing|blend|prev", "architecture/token_mixing"),
    (r"multi.?token prediction", "architecture/mtp"),
    (r"WINDOW_PATTERN|window|NSSL|NNSL|TTSL|near", "attention/window"),
    (r"RoPE|rope|rotary", "attention/rope"),
    (r"softcap", "attention/softcap"),
    (r"QK.?norm|remove QK", "attention/qk_norm"),
    (r"shared QKV", "attention/shared_qkv"),
    (r"MATRIX_LR|matrix_lr", "lr/matrix"),
    (r"EMBEDDING_LR|embedding_lr", "lr/embedding"),
    (r"UNEMBEDDING_LR|unembedding_lr", "lr/unembedding"),
    (r"SCALAR_LR|scalar_lr", "lr/scalar"),
    (r"FINAL_LR_FRAC|final_lr", "lr/final_frac"),
    (r"LR|lr|learning.?rate", "lr/general"),
    (r"ADAM_BETAS|adam|betas", "optimizer/adam"),
    (r"Muon|muon|momentum", "optimizer/muon"),
    (r"WEIGHT_DECAY|weight_decay", "optimizer/weight_decay"),
    (r"WARMUP|warmup", "schedule/warmup"),
    (r"WARMDOWN|warmdown", "schedule/warmdown"),
    (r"cosine|schedule", "schedule/shape"),
    (r"TOTAL_BATCH_SIZE|batch", "training/batch_size"),
    (r"label.?smooth", "training/label_smoothing"),
    (r"z.?loss|regulariz", "training/regularization"),
    (r"dropout", "training/dropout"),
    (r"init|lm_head.*init", "training/initialization"),
    (r"checkpoint|autotune", "training/infrastructure"),
    (r"value embed|VE|resid_lambda", "architecture/value_embed"),
    (r"RMSNorm|norm", "architecture/normalization"),
]


def categorize_experiment(description: str) -> str:
    """Assign a semantic category to an experiment description."""
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            return category
    return "other"


def get_top_category(category: str) -> str:
    """Get the top-level category (before the slash)."""
    return category.split("/")[0]


# ---------------------------------------------------------------------------
# Data structures for analysis results
# ---------------------------------------------------------------------------

@dataclass
class ExperimentRecord:
    """Flattened record from a trace, optimized for analysis."""
    index: int
    description: str
    outcome: str  # keep / discard / crash
    val_bpb: float
    peak_vram_gb: float
    delta_bpb: Optional[float]
    category: str
    top_category: str


@dataclass
class CategoryStats:
    """Aggregated statistics for an experiment category."""
    category: str
    total: int = 0
    keeps: int = 0
    discards: int = 0
    crashes: int = 0
    best_bpb: Optional[float] = None
    worst_bpb: Optional[float] = None
    avg_bpb: float = 0.0
    best_delta: Optional[float] = None

    @property
    def keep_rate(self) -> float:
        return self.keeps / self.total if self.total > 0 else 0.0

    @property
    def is_exhausted(self) -> bool:
        """A category is likely exhausted if it has 3+ experiments, all recent ones discard."""
        return self.total >= 3 and self.keeps == 0

    @property
    def is_promising(self) -> bool:
        """A category is promising if it has a decent keep rate."""
        return self.total >= 2 and self.keep_rate >= 0.3


@dataclass
class StreakInfo:
    """Information about consecutive outcome streaks."""
    outcome: str
    length: int
    start_index: int
    end_index: int


@dataclass
class AnalysisResult:
    """Complete analysis of a trace set."""
    # Basic stats
    total_experiments: int = 0
    total_keeps: int = 0
    total_discards: int = 0
    total_crashes: int = 0
    keep_rate: float = 0.0
    best_bpb: Optional[float] = None
    best_experiment: Optional[str] = None

    # Trajectory
    bpb_trajectory: list[float] = field(default_factory=list)
    keep_indices: list[int] = field(default_factory=list)
    avg_distance_between_keeps: float = 0.0

    # Transition patterns
    keep_after_keep: int = 0
    keep_after_discard: int = 0
    discard_after_keep: int = 0
    discard_after_discard: int = 0

    # Category analysis
    category_stats: dict[str, CategoryStats] = field(default_factory=dict)

    # Streaks
    longest_discard_streak: int = 0
    current_discard_streak: int = 0
    streaks: list[StreakInfo] = field(default_factory=list)

    # Diminishing returns
    recent_improvement_rate: float = 0.0
    total_improvement: float = 0.0
    last_10_improvement: float = 0.0
    diminishing_returns: bool = False

    # Dead ends and opportunities
    exhausted_categories: list[str] = field(default_factory=list)
    promising_categories: list[str] = field(default_factory=list)
    untried_combinations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core analyzer
# ---------------------------------------------------------------------------

class TraceAnalyzer:
    """Analyzes reasoning traces for patterns, dead ends, and opportunities."""

    def __init__(self):
        self.records: list[ExperimentRecord] = []

    def load_traces_json(self, path: str | Path) -> list[ExperimentRecord]:
        """Load traces from a JSON file exported by HUMMBL capture."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        traces = data.get("traces", [])
        self.records = []

        for i, trace in enumerate(traces):
            steps = trace.get("steps", [])
            if not steps:
                continue

            # Extract fields from the trace structure
            hyp_content = steps[0].get("content", "")
            # Strip "Experiment N: " prefix
            prefix = f"Experiment {i}: "
            desc = hyp_content[len(prefix):] if hyp_content.startswith(prefix) else hyp_content

            obs_meta = steps[2].get("metadata", {}) if len(steps) > 2 else {}
            eval_meta = steps[3].get("metadata", {}) if len(steps) > 3 else {}

            category = categorize_experiment(desc)
            record = ExperimentRecord(
                index=i,
                description=desc,
                outcome=trace.get("outcome", "unknown"),
                val_bpb=obs_meta.get("val_bpb", 0.0),
                peak_vram_gb=obs_meta.get("peak_vram_gb", 0.0),
                delta_bpb=eval_meta.get("delta_bpb"),
                category=category,
                top_category=get_top_category(category),
            )
            self.records.append(record)

        return self.records

    def analyze(self) -> AnalysisResult:
        """Run full analysis on loaded records."""
        if not self.records:
            return AnalysisResult()

        result = AnalysisResult()
        result.total_experiments = len(self.records)

        # --- Basic counts ---
        outcomes = [r.outcome for r in self.records]
        result.total_keeps = outcomes.count("keep")
        result.total_discards = outcomes.count("discard")
        result.total_crashes = outcomes.count("crash")
        result.keep_rate = result.total_keeps / result.total_experiments

        # --- Best result ---
        keeps_with_bpb = [r for r in self.records if r.outcome == "keep" and r.val_bpb > 0]
        if keeps_with_bpb:
            best = min(keeps_with_bpb, key=lambda r: r.val_bpb)
            result.best_bpb = best.val_bpb
            result.best_experiment = best.description

        # --- BPB trajectory (running best) ---
        running_best = None
        for r in self.records:
            if r.outcome == "keep" and r.val_bpb > 0:
                if running_best is None or r.val_bpb < running_best:
                    running_best = r.val_bpb
            result.bpb_trajectory.append(running_best if running_best else r.val_bpb)

        # --- Keep indices and distance ---
        result.keep_indices = [r.index for r in self.records if r.outcome == "keep"]
        if len(result.keep_indices) >= 2:
            distances = [
                result.keep_indices[i + 1] - result.keep_indices[i]
                for i in range(len(result.keep_indices) - 1)
            ]
            result.avg_distance_between_keeps = sum(distances) / len(distances)

        # --- Transition matrix ---
        for i in range(1, len(self.records)):
            prev = self.records[i - 1].outcome
            curr = self.records[i].outcome
            if prev == "keep" and curr == "keep":
                result.keep_after_keep += 1
            elif prev == "discard" and curr == "keep":
                result.keep_after_discard += 1
            elif prev == "keep" and curr == "discard":
                result.discard_after_keep += 1
            elif prev == "discard" and curr == "discard":
                result.discard_after_discard += 1

        # --- Streaks ---
        streaks = self._compute_streaks(outcomes)
        result.streaks = streaks
        discard_streaks = [s for s in streaks if s.outcome == "discard"]
        if discard_streaks:
            result.longest_discard_streak = max(s.length for s in discard_streaks)

        # Current streak at the end
        if outcomes:
            current_streak = 1
            for i in range(len(outcomes) - 1, 0, -1):
                if outcomes[i] == outcomes[i - 1]:
                    current_streak += 1
                else:
                    break
            if outcomes[-1] == "discard":
                result.current_discard_streak = current_streak

        # --- Category analysis ---
        cat_records: dict[str, list[ExperimentRecord]] = defaultdict(list)
        for r in self.records:
            cat_records[r.category].append(r)

        for cat, recs in cat_records.items():
            stats = CategoryStats(category=cat)
            stats.total = len(recs)
            stats.keeps = sum(1 for r in recs if r.outcome == "keep")
            stats.discards = sum(1 for r in recs if r.outcome == "discard")
            stats.crashes = sum(1 for r in recs if r.outcome == "crash")

            valid_bpbs = [r.val_bpb for r in recs if r.val_bpb > 0]
            if valid_bpbs:
                stats.best_bpb = min(valid_bpbs)
                stats.worst_bpb = max(valid_bpbs)
                stats.avg_bpb = sum(valid_bpbs) / len(valid_bpbs)

            deltas = [r.delta_bpb for r in recs if r.delta_bpb is not None]
            if deltas:
                stats.best_delta = min(deltas)

            result.category_stats[cat] = stats

        # --- Diminishing returns ---
        if result.best_bpb is not None and result.bpb_trajectory:
            first_best = result.bpb_trajectory[0]
            result.total_improvement = first_best - result.best_bpb

            # Compare first half vs second half improvement
            mid = len(result.bpb_trajectory) // 2
            first_half_best = min(result.bpb_trajectory[:mid])
            second_half_best = min(result.bpb_trajectory[mid:])
            first_half_improvement = first_best - first_half_best
            second_half_improvement = first_half_best - second_half_best

            if first_half_improvement > 0:
                result.recent_improvement_rate = (
                    second_half_improvement / first_half_improvement
                )
            result.diminishing_returns = (
                result.recent_improvement_rate < 0.25 and result.total_experiments > 20
            )

            # Last 10 experiments improvement
            last_10_best = min(result.bpb_trajectory[-10:])
            prior_best = min(result.bpb_trajectory[:-10]) if len(result.bpb_trajectory) > 10 else first_best
            result.last_10_improvement = prior_best - last_10_best

        # --- Exhausted and promising categories ---
        for cat, stats in result.category_stats.items():
            if cat == "baseline":
                continue
            # Exhausted: many tries, low or zero keep rate, no recent keeps
            cat_recs = cat_records[cat]
            recent_keeps = sum(1 for r in cat_recs[-3:] if r.outcome == "keep")
            if stats.total >= 3 and stats.keep_rate < 0.15 and recent_keeps == 0:
                result.exhausted_categories.append(cat)
            elif stats.is_promising:
                result.promising_categories.append(cat)

        # --- Suggestions ---
        result.suggestions = self._generate_suggestions(result, cat_records)

        return result

    def _compute_streaks(self, outcomes: list[str]) -> list[StreakInfo]:
        """Find all consecutive outcome streaks."""
        if not outcomes:
            return []

        streaks = []
        current_outcome = outcomes[0]
        start = 0

        for i in range(1, len(outcomes)):
            if outcomes[i] != current_outcome:
                streaks.append(StreakInfo(
                    outcome=current_outcome,
                    length=i - start,
                    start_index=start,
                    end_index=i - 1,
                ))
                current_outcome = outcomes[i]
                start = i

        streaks.append(StreakInfo(
            outcome=current_outcome,
            length=len(outcomes) - start,
            start_index=start,
            end_index=len(outcomes) - 1,
        ))
        return streaks

    def _generate_suggestions(
        self,
        result: AnalysisResult,
        cat_records: dict[str, list[ExperimentRecord]],
    ) -> list[str]:
        """Generate actionable suggestions based on analysis."""
        suggestions = []

        # 1. Diminishing returns warning
        if result.diminishing_returns:
            suggestions.append(
                "DIMINISHING RETURNS detected: second-half improvement is "
                f"{result.recent_improvement_rate:.0%} of first-half. "
                "Consider architectural changes rather than hyperparameter tuning."
            )

        # 2. Current discard streak warning
        if result.current_discard_streak >= 8:
            suggestions.append(
                f"Currently on a {result.current_discard_streak}-experiment "
                "discard streak. The search space around the current config "
                "may be locally optimal. Try a larger perturbation."
            )

        # 3. Promising categories to explore further
        for cat in result.promising_categories:
            stats = result.category_stats[cat]
            suggestions.append(
                f"PROMISING: '{cat}' has {stats.keep_rate:.0%} keep rate "
                f"({stats.keeps}/{stats.total}). Consider more experiments here."
            )

        # 4. Categories with single successful experiment (worth revisiting)
        for cat, stats in result.category_stats.items():
            if stats.keeps == 1 and stats.total <= 2:
                suggestions.append(
                    f"UNDEREXPLORED: '{cat}' had 1 keep in {stats.total} tries. "
                    "Might benefit from finer-grained sweeps."
                )

        # 5. Combination suggestions based on successful categories
        successful_cats = [
            cat for cat, stats in result.category_stats.items()
            if stats.keeps > 0 and cat != "baseline"
        ]
        top_cats = set(get_top_category(c) for c in successful_cats)

        # Check for cross-category combinations
        if "architecture" in top_cats and "lr" in top_cats:
            arch_keeps = [c for c in successful_cats if c.startswith("architecture/")]
            lr_keeps = [c for c in successful_cats if c.startswith("lr/")]
            if arch_keeps and lr_keeps:
                suggestions.append(
                    f"COMBINATION: Architecture changes ({', '.join(arch_keeps)}) "
                    f"and LR changes ({', '.join(lr_keeps)}) both produced wins. "
                    "Joint re-tuning of LR after architecture changes may yield gains."
                )

        # 6. Specific untried ideas based on what worked
        if "architecture/token_mixing" in successful_cats:
            suggestions.append(
                "Token mixing improved results. Consider other forms of "
                "cross-token communication: convolution-based mixing, "
                "or learned position-dependent blending weights."
            )

        if "attention/window" in successful_cats:
            suggestions.append(
                "Window attention patterns helped. Try varying near_window "
                "sizes (128, 384) or asymmetric patterns (NSSSL)."
            )

        # 7. Exhausted categories to avoid
        if result.exhausted_categories:
            suggestions.append(
                f"EXHAUSTED categories (avoid unless new approach): "
                f"{', '.join(result.exhausted_categories)}"
            )

        return suggestions

    def format_stats(self, result: AnalysisResult) -> str:
        """Format analysis result as a human-readable summary."""
        lines = []
        lines.append("=" * 70)
        lines.append("HUMMBL TRACE ANALYSIS")
        lines.append("=" * 70)

        # --- Overview ---
        lines.append("")
        lines.append("OVERVIEW")
        lines.append("-" * 40)
        lines.append(f"  Total experiments:   {result.total_experiments}")
        lines.append(f"  Keeps:               {result.total_keeps} ({result.keep_rate:.1%})")
        lines.append(f"  Discards:            {result.total_discards}")
        lines.append(f"  Crashes:             {result.total_crashes}")
        if result.best_bpb is not None:
            lines.append(f"  Best val_bpb:        {result.best_bpb:.6f}")
            lines.append(f"  Best experiment:     {result.best_experiment}")
        lines.append(f"  Total improvement:   {result.total_improvement:.6f} bpb")

        # --- Keep/discard patterns ---
        lines.append("")
        lines.append("OUTCOME PATTERNS")
        lines.append("-" * 40)
        if result.keep_indices:
            lines.append(f"  Avg experiments between keeps: {result.avg_distance_between_keeps:.1f}")
        lines.append(f"  Longest discard streak:        {result.longest_discard_streak}")
        lines.append(f"  Current discard streak:        {result.current_discard_streak}")
        lines.append("")
        lines.append("  Transition matrix:")
        lines.append(f"    keep->keep:       {result.keep_after_keep:3d}")
        lines.append(f"    keep->discard:    {result.discard_after_keep:3d}")
        lines.append(f"    discard->keep:    {result.keep_after_discard:3d}")
        lines.append(f"    discard->discard: {result.discard_after_discard:3d}")

        # Cluster analysis: keeps tend to cluster?
        if result.keep_after_keep + result.keep_after_discard > 0:
            cluster_ratio = result.keep_after_keep / (result.keep_after_keep + result.keep_after_discard)
            lines.append(f"  P(keep|prev=keep):  {cluster_ratio:.2f}")
        if result.discard_after_keep + result.discard_after_discard > 0:
            persist_ratio = result.discard_after_discard / (result.discard_after_keep + result.discard_after_discard)
            lines.append(f"  P(disc|prev=disc):  {persist_ratio:.2f}")

        # --- Diminishing returns ---
        lines.append("")
        lines.append("DIMINISHING RETURNS")
        lines.append("-" * 40)
        lines.append(f"  First-half vs second-half ratio: {result.recent_improvement_rate:.2f}")
        lines.append(f"  Last 10 experiments improvement:  {result.last_10_improvement:.6f} bpb")
        lines.append(f"  Diminishing returns detected:     {'YES' if result.diminishing_returns else 'No'}")

        # --- Category breakdown ---
        lines.append("")
        lines.append("CATEGORY PERFORMANCE")
        lines.append("-" * 70)
        lines.append(f"  {'Category':<30s} {'Total':>5s} {'Keep':>4s} {'Rate':>6s} {'Best BPB':>10s}")
        lines.append(f"  {'-'*30} {'-'*5} {'-'*4} {'-'*6} {'-'*10}")

        sorted_cats = sorted(
            result.category_stats.items(),
            key=lambda x: (-x[1].keep_rate, -x[1].total),
        )
        for cat, stats in sorted_cats:
            best = f"{stats.best_bpb:.6f}" if stats.best_bpb else "N/A"
            lines.append(
                f"  {cat:<30s} {stats.total:>5d} {stats.keeps:>4d} "
                f"{stats.keep_rate:>5.0%} {best:>10s}"
            )

        # --- Winning patterns ---
        lines.append("")
        lines.append("WINNING PATTERNS (categories with keeps)")
        lines.append("-" * 40)
        winners = [
            (cat, stats) for cat, stats in sorted_cats
            if stats.keeps > 0 and cat != "baseline"
        ]
        for cat, stats in winners:
            lines.append(f"  {cat}: {stats.keeps}/{stats.total} kept")

        # --- Dead ends ---
        if result.exhausted_categories:
            lines.append("")
            lines.append("DEAD ENDS (exhausted categories)")
            lines.append("-" * 40)
            for cat in result.exhausted_categories:
                stats = result.category_stats[cat]
                lines.append(f"  {cat}: {stats.keeps}/{stats.total} kept")

        return "\n".join(lines)

    def format_suggestions(self, result: AnalysisResult) -> str:
        """Format suggestions as a readable list."""
        lines = []
        lines.append("=" * 70)
        lines.append("HUMMBL EXPERIMENT SUGGESTIONS")
        lines.append("=" * 70)

        if not result.suggestions:
            lines.append("")
            lines.append("  No specific suggestions — analysis looks healthy.")
            return "\n".join(lines)

        for i, suggestion in enumerate(result.suggestions, 1):
            lines.append("")
            # Word-wrap long suggestions
            words = suggestion.split()
            current_line = f"  {i}. "
            for word in words:
                if len(current_line) + len(word) + 1 > 72:
                    lines.append(current_line)
                    current_line = "     " + word
                else:
                    current_line += (" " if not current_line.endswith(". ") else "") + word
            if current_line.strip():
                lines.append(current_line)

        return "\n".join(lines)
