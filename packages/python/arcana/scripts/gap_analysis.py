"""Compute target-vs-actual PAIDEIA-9 gaps and attribute root causes.

Reads:
- paideia/plans/*.json  (target vectors)
- paideia/history.tsv   (actual scored vectors)

Produces a ranked list of (axis, mean_gap, root_cause, proposed_fix, confidence).

Pure stdlib. No Ollama.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecosystem_contracts as ec

HERE = Path(__file__).resolve().parent
PLANS_DIR = HERE / "paideia" / "plans"
HISTORY_PATH = HERE / "paideia" / "history.tsv"
AXES = list(ec.PAIDEIA_AXES)


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        return list(reader)


def load_plans(plans_dir: Path) -> list[dict]:
    plans: list[dict] = []
    if not plans_dir.exists():
        return plans
    for p in sorted(plans_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            plans.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: skipping corrupt {p}: {e}", file=sys.stderr)
            continue
    return plans


def parse_signature(sig: str) -> dict[str, int] | None:
    """Parse a PAIDEIA signature into {axis: score}.

    Version-aware (docs/paideia-9-v0.2-draft.md): accepts v0.2 10-element
    signatures (M-D-E-V-C-L-S-P-A-Em) and v0.1 9-element signatures
    (M-D-E-V-C-L-S-P-A). v0.1 results lack the Em key; callers must treat
    Em as absent/None for those. Returns None for any other length or
    non-integer parts.
    """
    parts = sig.split("-")
    try:
        values = [int(v) for v in parts]
    except ValueError:
        return None
    if len(values) == len(AXES):  # v0.2: 10 axes
        return dict(zip(AXES, values))
    if len(values) == len(ec.PAIDEIA_AXES_V0_1):  # v0.1: 9 axes
        return dict(zip(ec.PAIDEIA_AXES_V0_1, values))
    return None


def compute_axis_gaps(
    plans: list[dict],
    history: list[dict],
) -> dict[str, list[float]]:
    """Return {axis: [gap1, gap2, ...]} for all matched plan+score pairs."""
    # Index history by slug for matching
    history_by_slug: dict[str, list[dict]] = defaultdict(list)
    for row in history:
        slug = row.get("slug", "")
        if slug:
            history_by_slug[slug].append(row)

    gaps: dict[str, list[float]] = {a: [] for a in AXES}

    for plan in plans:
        target = plan.get("target_vector", {})
        # Match by topic slugification
        topic = plan.get("_provenance", {}).get("topic", "")
        slug = _slugify(topic)
        if not slug:
            continue
        # Find history rows with matching slug prefix
        matched = []
        for hslug, rows in history_by_slug.items():
            if hslug.startswith(slug) or slug.startswith(hslug):
                matched.extend(rows)

        for row in matched:
            actual = parse_signature(row.get("signature", ""))
            if actual is None:
                continue
            for axis in AXES:
                t = target.get(axis)
                a = actual.get(axis)
                if t is not None and a is not None:
                    # gap = target - actual (positive = underperforming)
                    gaps[axis].append(float(t - a))

    return gaps


def attribute_root_cause(
    axis: str,
    mean_gap: float,
    sample_size: int,
    plan_targets: list[float],
    actual_scores: list[float],
) -> tuple[str, str, float]:
    """Return (root_cause, proposed_fix, confidence)."""
    # Attribution heuristics
    mean_target = statistics.mean(plan_targets) if plan_targets else 0.0
    mean_actual = statistics.mean(actual_scores) if actual_scores else 0.0

    # Case: target is high but actual is consistently low → prompt weakness
    if mean_target >= 3 and mean_actual <= 1.5:
        cause = "prompt_weakness"
        fix = (
            f"Strengthen {axis} ({ec.PAIDEIA_AXIS_NAMES[axis]}) instruction "
            f"in paideia_plan_v2.txt: add explicit 'must score >= {int(mean_target)}' "
            f"constraint and worked-example requirement."
        )
        confidence = min(0.95, 0.5 + sample_size * 0.05)
        return cause, fix, confidence

    # Case: target and actual both moderate → detector underestimation
    if mean_target >= 2 and mean_actual >= 1.5 and mean_gap < 1.0:
        cause = "detector_underestimation"
        fix = (
            f"Recalibrate {axis} detector in score_paideia.py: "
            f"lower threshold or add more signal patterns."
        )
        confidence = 0.6
        return cause, fix, confidence

    # Case: gap is huge but sample small → need more data
    if abs(mean_gap) >= 2 and sample_size < 3:
        cause = "insufficient_data"
        fix = (
            f"Generate more articles on this topic type to validate "
            f"{axis} gap before proposing fix."
        )
        confidence = 0.3
        return cause, fix, confidence

    # Default: detector limitation
    cause = "detector_limitation"
    fix = (
        f"For {axis} ({ec.PAIDEIA_AXIS_NAMES[axis]}): improve heuristic "
        f"or switch to LLM-based detector. Current mean actual={mean_actual:.1f}, "
        f"target={mean_target:.1f}."
    )
    confidence = 0.5
    return cause, fix, confidence


def analyze(plans_dir: Path = PLANS_DIR, history_path: Path = HISTORY_PATH) -> dict:
    plans = load_plans(plans_dir)
    history = load_history(history_path)
    gaps = compute_axis_gaps(plans, history)

    # Also collect per-axis target/actual distributions for attribution
    axis_targets: dict[str, list[float]] = {a: [] for a in AXES}
    axis_actuals: dict[str, list[float]] = {a: [] for a in AXES}

    history_by_slug: dict[str, list[dict]] = defaultdict(list)
    for row in history:
        slug = row.get("slug", "")
        if slug:
            history_by_slug[slug].append(row)

    for plan in plans:
        target = plan.get("target_vector", {})
        topic = plan.get("_provenance", {}).get("topic", "")
        slug = _slugify(topic)
        if not slug:
            continue
        for hslug, rows in history_by_slug.items():
            if hslug.startswith(slug) or slug.startswith(hslug):
                for row in rows:
                    actual = parse_signature(row.get("signature", ""))
                    if actual:
                        for axis in AXES:
                            t = target.get(axis)
                            a = actual.get(axis)
                            if t is not None and a is not None:
                                axis_targets[axis].append(float(t))
                                axis_actuals[axis].append(float(a))

    results = []
    for axis in AXES:
        gap_list = gaps[axis]
        if not gap_list:
            continue
        mean_gap = statistics.mean(gap_list)
        sample_size = len(gap_list)
        cause, fix, confidence = attribute_root_cause(
            axis, mean_gap, sample_size,
            axis_targets[axis], axis_actuals[axis],
        )
        results.append({
            "axis": axis,
            "axis_name": ec.PAIDEIA_AXIS_NAMES[axis],
            "mean_gap": round(mean_gap, 2),
            "sample_size": sample_size,
            "root_cause": cause,
            "proposed_fix": fix,
            "confidence": round(confidence, 2),
            "priority_score": round(abs(mean_gap) * confidence, 2),
        })

    # Sort by priority_score descending
    results.sort(key=lambda r: r["priority_score"], reverse=True)
    return {
        "plans_loaded": len(plans),
        "history_rows_loaded": len(history),
        # ponytail: max (not average) so version-mixed data stays correct.
        # v0.1 scores lack Em, so Em has fewer entries than the 9 shared axes;
        # sum//len would undercount (9//10 == 0). max reflects the true number
        # of plan+score pairs that matched on at least one comparable axis.
        "matched_pairs": max((len(gaps[a]) for a in AXES), default=0),
        "axis_gaps": results,
        "overall_mean_gap": round(statistics.mean(
            r["mean_gap"] for r in results
        ), 2) if results else 0.0,
    }


def render_report(report: dict) -> str:
    lines = [
        "# ARCANA PAIDEIA-9 Gap Analysis",
        "",
        f"- **Plans loaded:** {report['plans_loaded']}",
        f"- **History rows:** {report['history_rows_loaded']}",
        f"- **Matched plan→score pairs:** {report['matched_pairs']}",
        f"- **Overall mean gap:** {report['overall_mean_gap']}",
        "",
        "## Axis Gaps (ranked by priority = |gap| × confidence)",
        "",
    ]
    for r in report["axis_gaps"]:
        lines.append(f"### {r['axis']} — {r['axis_name']}")
        lines.append(f"- **Mean gap:** {r['mean_gap']} (target - actual)")
        lines.append(f"- **Sample size:** {r['sample_size']}")
        lines.append(f"- **Root cause:** {r['root_cause']}")
        lines.append(f"- **Proposed fix:** {r['proposed_fix']}")
        lines.append(f"- **Confidence:** {r['confidence']}")
        lines.append(f"- **Priority score:** {r['priority_score']}")
        lines.append("")
    return "\n".join(lines)


def _slugify(s: str, max_len: int = 60) -> str:
    s = s.lower().strip()
    s = __import__("re").sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or "untitled"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plans-dir", type=Path, default=PLANS_DIR)
    p.add_argument("--history", type=Path, default=HISTORY_PATH)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = p.parse_args(argv)

    report = analyze(args.plans_dir, args.history)

    if args.format == "json":
        out = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        out = render_report(report)

    if args.output:
        args.output.write_text(out + "\n", encoding="utf-8")
        print(f"wrote gap report to {args.output}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
