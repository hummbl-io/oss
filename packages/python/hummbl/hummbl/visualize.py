"""Terminal trace visualizer — renders reasoning traces as Unicode diagrams.

Provides four views:
- Single trace view: step chain/tree for one trace
- Timeline view: experiment progression with bar chart
- Category summary: keep rates by category
- Trace diff: side-by-side comparison of two traces

Uses only stdlib. Falls back to ASCII on terminals that don't support Unicode.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from hummbl.analyzer import TraceAnalyzer, categorize_experiment, get_top_category


# ---------------------------------------------------------------------------
# Unicode vs ASCII glyph sets
# ---------------------------------------------------------------------------

def _can_unicode() -> bool:
    """Check if the terminal can render Unicode box-drawing characters."""
    try:
        # Try encoding a representative set of glyphs
        test = "\u2500\u2502\u250c\u2514\u251c\u2588\u2591\u2713\u2717\u25bc"
        test.encode(sys.stdout.encoding or "utf-8")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


class _Glyphs:
    """Character set for rendering."""
    def __init__(self, unicode: bool = True):
        if unicode:
            self.h_line = "\u2500"      # horizontal line
            self.v_line = "\u2502"      # vertical line
            self.top_left = "\u250c"    # top-left corner
            self.bot_left = "\u2514"    # bottom-left corner
            self.tee = "\u251c"         # tee (left side)
            self.block_full = "\u2588"  # full block
            self.block_light = "\u2591" # light shade
            self.check = "\u2713"       # checkmark
            self.cross = "\u2717"       # cross
            self.down_arrow = "\u25bc"  # down-pointing triangle
            self.dash = "\u2500"
        else:
            self.h_line = "-"
            self.v_line = "|"
            self.top_left = "+"
            self.bot_left = "+"
            self.tee = "+"
            self.block_full = "#"
            self.block_light = "."
            self.check = "+"
            self.cross = "x"
            self.down_arrow = "v"
            self.dash = "-"


# Singleton, initialized lazily
_glyphs: Optional[_Glyphs] = None


def _g() -> _Glyphs:
    global _glyphs
    if _glyphs is None:
        _glyphs = _Glyphs(unicode=_can_unicode())
    return _glyphs


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_raw_traces(path: str | Path) -> list[dict]:
    """Load raw trace dicts from a HUMMBL JSON file."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("traces", [])


def _extract_trace_info(trace: dict, index: int) -> dict:
    """Extract display-relevant fields from a raw trace dict."""
    steps = trace.get("steps", [])
    info = {
        "id": trace.get("id", "?"),
        "index": index,
        "outcome": trace.get("outcome", "unknown"),
        "steps": steps,
    }

    # Hypothesis
    if steps:
        hyp = steps[0].get("content", "")
        prefix = f"Experiment {index}: "
        info["description"] = hyp[len(prefix):] if hyp.startswith(prefix) else hyp

    # Action
    if len(steps) > 1:
        info["action"] = steps[1].get("content", "")
        info["commit"] = steps[1].get("metadata", {}).get("commit_hash", "")

    # Observation
    if len(steps) > 2:
        obs_meta = steps[2].get("metadata", {})
        info["val_bpb"] = obs_meta.get("val_bpb", 0.0)
        info["peak_vram_gb"] = obs_meta.get("peak_vram_gb", 0.0)
        info["observation"] = steps[2].get("content", "")

    # Evaluation
    if len(steps) > 3:
        eval_meta = steps[3].get("metadata", {})
        info["delta_bpb"] = eval_meta.get("delta_bpb")
        info["baseline_bpb"] = eval_meta.get("baseline_bpb")
        info["evaluation"] = steps[3].get("content", "")

    # Decision
    if len(steps) > 4:
        info["decision"] = steps[4].get("content", "")

    return info


# ---------------------------------------------------------------------------
# View 1: Single trace view
# ---------------------------------------------------------------------------

def render_single_trace(path: str | Path, trace_id: Optional[str] = None,
                        trace_index: Optional[int] = None) -> str:
    """Render a single trace as a step chain diagram."""
    g = _g()
    traces = _load_raw_traces(path)

    if not traces:
        return "No traces found."

    # Find the requested trace
    target = None
    idx = 0
    if trace_id is not None:
        for i, t in enumerate(traces):
            if t.get("id", "") == trace_id:
                target = t
                idx = i
                break
        if target is None:
            return f"Trace ID '{trace_id}' not found."
    elif trace_index is not None:
        if 0 <= trace_index < len(traces):
            target = traces[trace_index]
            idx = trace_index
        else:
            return f"Trace index {trace_index} out of range (0-{len(traces)-1})."
    else:
        # Default to first trace
        target = traces[0]
        idx = 0

    info = _extract_trace_info(target, idx)
    lines: list[str] = []

    lines.append(f"Trace: {info['id']}  (experiment #{idx:02d})")
    lines.append(g.dash * 50)
    lines.append("")

    step_types = ["hypothesis", "action", "observation", "evaluation", "decision"]
    step_labels = {
        "hypothesis": "HYPOTHESIS",
        "action": "ACTION",
        "observation": "OBSERVATION",
        "evaluation": "EVALUATION",
        "decision": "DECISION",
    }

    steps = info["steps"]
    for i, step in enumerate(steps):
        stype = step.get("type", "unknown")
        content = step.get("content", "")
        label = step_labels.get(stype, stype.upper())

        is_first = (i == 0)
        is_last = (i == len(steps) - 1)

        if is_first:
            connector = g.top_left + g.h_line
        elif is_last:
            connector = g.bot_left + g.h_line
        else:
            connector = g.tee + g.h_line

        # Add status symbol to decision line
        if stype == "decision":
            outcome = info.get("outcome", "")
            if outcome == "keep":
                content = f"{g.check} KEEP"
                # Check if it was a new best
                delta = info.get("delta_bpb")
                if delta is not None and delta < 0:
                    content += " (new best)"
            elif outcome == "discard":
                content = f"{g.cross} DISCARD"
            else:
                content = outcome.upper()

        lines.append(f"{connector} {label}: {content}")

        # Add blank connector between steps (except after last)
        if not is_last:
            lines.append(f"{g.v_line}")

    # Append summary metadata
    lines.append("")
    val_bpb = info.get("val_bpb")
    if val_bpb:
        lines.append(f"  val_bpb:   {val_bpb:.6f}")
    delta = info.get("delta_bpb")
    if delta is not None:
        direction = "better" if delta < 0 else "worse"
        lines.append(f"  delta:     {delta:+.6f} ({direction})")
    vram = info.get("peak_vram_gb")
    if vram:
        lines.append(f"  peak_vram: {vram:.1f} GB")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# View 2: Timeline view
# ---------------------------------------------------------------------------

def render_timeline(path: str | Path, max_width: int = 80) -> str:
    """Render experiment timeline with progress bars."""
    g = _g()
    traces = _load_raw_traces(path)

    if not traces:
        return "No traces found."

    records = []
    running_best = None
    for i, t in enumerate(traces):
        info = _extract_trace_info(t, i)
        val_bpb = info.get("val_bpb", 0.0)
        outcome = info.get("outcome", "unknown")

        is_new_best = False
        if outcome == "keep" and val_bpb > 0:
            if running_best is None or val_bpb < running_best:
                is_new_best = True
                running_best = val_bpb

        records.append({
            "index": i,
            "description": info.get("description", "?"),
            "outcome": outcome,
            "val_bpb": val_bpb,
            "is_new_best": is_new_best,
        })

    # Find bpb range for bar scaling
    bpb_values = [r["val_bpb"] for r in records if r["val_bpb"] > 0]
    if not bpb_values:
        return "No valid bpb values found."

    bpb_min = min(bpb_values)
    bpb_max = max(bpb_values)
    bpb_range = bpb_max - bpb_min if bpb_max > bpb_min else 0.01

    lines: list[str] = []
    lines.append(f"Experiment Timeline ({len(records)} traces)")
    lines.append(g.dash * min(max_width, 70))

    # Truncate description to fit
    desc_width = 28
    bar_max = 20

    for r in records:
        idx = r["index"]
        outcome = r["outcome"]
        val_bpb = r["val_bpb"]
        desc = r["description"]

        # Status symbol
        if r["is_new_best"]:
            symbol = g.down_arrow
        elif outcome == "keep":
            symbol = g.check
        elif outcome == "discard":
            symbol = g.cross
        else:
            symbol = "?"

        # Truncate description
        if len(desc) > desc_width:
            desc = desc[:desc_width - 2] + ".."

        # Bar length: proportional to bpb (lower = shorter bar = better)
        if val_bpb > 0:
            normalized = (val_bpb - bpb_min) / bpb_range
            bar_len = max(1, int(normalized * bar_max))
            bar = g.block_full * bar_len
        else:
            bar = ""

        lines.append(
            f" #{idx:02d} {symbol} {desc:<{desc_width}s} {val_bpb:.3f} {bar}"
        )

    # Summary line
    lines.append(g.dash * min(max_width, 70))
    if running_best is not None:
        lines.append(f" Best: {running_best:.6f}")
    lines.append(f" Keep rate: {sum(1 for r in records if r['outcome'] == 'keep')}/{len(records)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# View 3: Category summary
# ---------------------------------------------------------------------------

def render_categories(path: str | Path) -> str:
    """Render category performance summary with bar chart."""
    g = _g()
    analyzer = TraceAnalyzer()
    analyzer.load_traces_json(path)
    result = analyzer.analyze()

    if not result.category_stats:
        return "No category data found."

    lines: list[str] = []
    lines.append("Category Performance")
    lines.append(g.dash * 60)

    bar_width = 8

    # Sort by keep rate descending, then total descending
    sorted_cats = sorted(
        result.category_stats.items(),
        key=lambda x: (-x[1].keep_rate, -x[1].total),
    )

    # Find max total for scale
    max_total = max(s.total for _, s in sorted_cats) if sorted_cats else 1

    # Header
    cat_col = 25
    lines.append(
        f"  {'Category':<{cat_col}s} {'Bar':<{bar_width + 2}s} "
        f"{'Keep':>8s}  {'Rate':>6s}  {'Best BPB':>10s}"
    )
    lines.append(f"  {g.dash * cat_col} {g.dash * (bar_width + 2)} "
                 f"{g.dash * 8}  {g.dash * 6}  {g.dash * 10}")

    for cat, stats in sorted_cats:
        # Bar: filled portion = keep rate
        filled = max(0, int(stats.keep_rate * bar_width))
        empty = bar_width - filled
        bar = g.block_full * filled + g.block_light * empty

        keep_str = f"{stats.keeps}/{stats.total}"
        rate_str = f"{stats.keep_rate:.1%}"
        best_str = f"{stats.best_bpb:.6f}" if stats.best_bpb else "N/A"

        # Truncate category name
        cat_display = cat if len(cat) <= cat_col else cat[:cat_col - 2] + ".."
        lines.append(
            f"  {cat_display:<{cat_col}s} {bar}  {keep_str:>8s}  {rate_str:>6s}  {best_str:>10s}"
        )

    # Summary
    lines.append(f"  {g.dash * cat_col}")
    total_keeps = result.total_keeps
    total = result.total_experiments
    lines.append(f"  {'TOTAL':<{cat_col}s}           {total_keeps}/{total:>4d}  {result.keep_rate:.1%}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# View 4: Trace diff
# ---------------------------------------------------------------------------

def render_diff(path: str | Path, id_a: str, id_b: str) -> str:
    """Render side-by-side comparison of two traces."""
    g = _g()
    traces = _load_raw_traces(path)

    # Resolve IDs -- accept either trace ID or numeric index
    def find_trace(identifier: str) -> tuple[Optional[dict], int]:
        # Try numeric index first
        try:
            idx = int(identifier)
            if 0 <= idx < len(traces):
                return traces[idx], idx
        except ValueError:
            pass
        # Try trace ID
        for i, t in enumerate(traces):
            if t.get("id", "") == identifier:
                return t, i
        return None, -1

    trace_a, idx_a = find_trace(id_a)
    trace_b, idx_b = find_trace(id_b)

    if trace_a is None:
        return f"Trace A '{id_a}' not found."
    if trace_b is None:
        return f"Trace B '{id_b}' not found."

    info_a = _extract_trace_info(trace_a, idx_a)
    info_b = _extract_trace_info(trace_b, idx_b)

    col_width = 35
    sep = "  "

    lines: list[str] = []

    # Header
    header_a = f"Trace A: #{idx_a:02d}"
    header_b = f"Trace B: #{idx_b:02d}"
    lines.append(f"{header_a:<{col_width}s}{sep}{header_b:<{col_width}s}")
    lines.append(f"{g.dash * col_width}{sep}{g.dash * col_width}")

    # Description
    desc_a = info_a.get("description", "?")
    desc_b = info_b.get("description", "?")
    if len(desc_a) > col_width:
        desc_a = desc_a[:col_width - 2] + ".."
    if len(desc_b) > col_width:
        desc_b = desc_b[:col_width - 2] + ".."
    lines.append(f"{desc_a:<{col_width}s}{sep}{desc_b:<{col_width}s}")
    lines.append("")

    # Metrics
    def row(label: str, val_a: str, val_b: str) -> str:
        cell_a = f"{label}: {val_a}"
        cell_b = f"{label}: {val_b}"
        return f"{cell_a:<{col_width}s}{sep}{cell_b:<{col_width}s}"

    bpb_a = info_a.get("val_bpb", 0.0)
    bpb_b = info_b.get("val_bpb", 0.0)
    lines.append(row("val_bpb", f"{bpb_a:.6f}" if bpb_a else "N/A",
                      f"{bpb_b:.6f}" if bpb_b else "N/A"))

    delta_a = info_a.get("delta_bpb")
    delta_b = info_b.get("delta_bpb")

    def fmt_delta(d: Optional[float], bpb: float, baseline: Optional[float]) -> str:
        if d is None:
            return "N/A (baseline)"
        pct = abs(d / baseline * 100) if baseline else 0
        return f"{d:+.6f} ({pct:.1f}%)"

    lines.append(row(
        "delta",
        fmt_delta(delta_a, bpb_a, info_a.get("baseline_bpb")),
        fmt_delta(delta_b, bpb_b, info_b.get("baseline_bpb")),
    ))

    vram_a = info_a.get("peak_vram_gb", 0.0)
    vram_b = info_b.get("peak_vram_gb", 0.0)
    lines.append(row("peak_vram", f"{vram_a:.1f} GB" if vram_a else "N/A",
                      f"{vram_b:.1f} GB" if vram_b else "N/A"))

    outcome_a = info_a.get("outcome", "?")
    outcome_b = info_b.get("outcome", "?")
    status_a = f"{g.check} KEEP" if outcome_a == "keep" else f"{g.cross} DISCARD" if outcome_a == "discard" else outcome_a.upper()
    status_b = f"{g.check} KEEP" if outcome_b == "keep" else f"{g.cross} DISCARD" if outcome_b == "discard" else outcome_b.upper()
    lines.append(row("status", status_a, status_b))

    cat_a = categorize_experiment(info_a.get("description", ""))
    cat_b = categorize_experiment(info_b.get("description", ""))
    lines.append(row("category", cat_a, cat_b))

    # Direct comparison
    lines.append("")
    lines.append(g.dash * (col_width * 2 + len(sep)))
    if bpb_a and bpb_b and bpb_a > 0 and bpb_b > 0:
        diff = bpb_a - bpb_b
        if abs(diff) < 1e-8:
            lines.append("Result: identical val_bpb")
        else:
            winner = "A" if bpb_a < bpb_b else "B"
            lines.append(f"Result: Trace {winner} is better by {abs(diff):.6f} bpb")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI dispatch (called from cli.py)
# ---------------------------------------------------------------------------

def cli_view(args: list[str]) -> int:
    """Handle 'view' command."""
    if not args:
        print("Usage: python -m hummbl view <traces.json> [--trace-id ID | --index N]")
        return 1

    path = args[0]
    trace_id = None
    trace_index = None

    i = 1
    while i < len(args):
        if args[i] == "--trace-id" and i + 1 < len(args):
            trace_id = args[i + 1]
            i += 2
        elif args[i] == "--index" and i + 1 < len(args):
            trace_index = int(args[i + 1])
            i += 2
        else:
            i += 1

    print(render_single_trace(path, trace_id=trace_id, trace_index=trace_index))
    return 0


def cli_timeline(args: list[str]) -> int:
    """Handle 'timeline' command."""
    if not args:
        print("Usage: python -m hummbl timeline <traces.json>")
        return 1
    print(render_timeline(args[0]))
    return 0


def cli_categories(args: list[str]) -> int:
    """Handle 'categories' command."""
    if not args:
        print("Usage: python -m hummbl categories <traces.json>")
        return 1
    print(render_categories(args[0]))
    return 0


def cli_diff(args: list[str]) -> int:
    """Handle 'diff' command."""
    if not args:
        print("Usage: python -m hummbl diff <traces.json> --ids ID1 ID2")
        return 1

    path = args[0]
    id_a = None
    id_b = None

    i = 1
    while i < len(args):
        if args[i] == "--ids" and i + 2 < len(args):
            id_a = args[i + 1]
            id_b = args[i + 2]
            i += 3
        else:
            i += 1

    if id_a is None or id_b is None:
        print("Usage: python -m hummbl diff <traces.json> --ids ID1 ID2")
        print("  IDs can be trace IDs or numeric indices (e.g. --ids 0 21)")
        return 1

    print(render_diff(path, id_a, id_b))
    return 0
