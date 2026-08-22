"""HUMMBL CLI -- analyze and visualize reasoning traces from the command line.

Usage:
    python -m hummbl analyze <traces.json>                -- full analysis report
    python -m hummbl suggest <traces.json>                -- next experiment suggestions
    python -m hummbl stats <traces.json>                  -- summary statistics only
    python -m hummbl plan <traces.json> [--n 5] [--combinatorial] [--exploration] [--strategy-md <path>]
                                                          -- generate experiment plan
    python -m hummbl view <traces.json> [--trace-id ID]   -- single trace view
    python -m hummbl view <traces.json> [--index N]       -- single trace by index
    python -m hummbl timeline <traces.json>               -- timeline view
    python -m hummbl categories <traces.json>             -- category performance
    python -m hummbl diff <traces.json> --ids ID1 ID2     -- compare two traces
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hummbl.analyzer import TraceAnalyzer


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]

    if len(args) < 2:
        print(__doc__)
        return 1

    command = args[0]

    # --- Visualization commands (delegated to visualize module) ---
    if command in ("view", "timeline", "categories", "diff"):
        from hummbl.visualize import cli_view, cli_timeline, cli_categories, cli_diff

        dispatch = {
            "view": cli_view,
            "timeline": cli_timeline,
            "categories": cli_categories,
            "diff": cli_diff,
        }
        return dispatch[command](args[1:])

    # --- Analysis commands ---
    trace_path = Path(args[1])

    if not trace_path.exists():
        print(f"Error: file not found: {trace_path}")
        return 1

    analyzer = TraceAnalyzer()
    analyzer.load_traces_json(trace_path)
    result = analyzer.analyze()

    if command == "analyze":
        print(analyzer.format_stats(result))
        print()
        print(analyzer.format_suggestions(result))

    elif command == "suggest":
        print(analyzer.format_suggestions(result))

    elif command == "stats":
        print(analyzer.format_stats(result))

    elif command == "plan":
        return _handle_plan(analyzer, args[2:])

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1

    return 0


def _handle_plan(analyzer: TraceAnalyzer, extra_args: list[str]) -> int:
    """Handle the 'plan' subcommand."""
    from hummbl.planner import TracePlanner

    planner = TracePlanner(analyzer)

    # Parse flags
    n = 5
    mode = "next"
    strategy_md_path: str | None = None
    transfer_path: str | None = None

    i = 0
    while i < len(extra_args):
        arg = extra_args[i]
        if arg == "--n" and i + 1 < len(extra_args):
            n = int(extra_args[i + 1])
            i += 2
        elif arg == "--combinatorial":
            mode = "combinatorial"
            i += 1
        elif arg == "--exploration":
            mode = "exploration"
            i += 1
        elif arg == "--transfer" and i + 1 < len(extra_args):
            mode = "transfer"
            transfer_path = extra_args[i + 1]
            i += 2
        elif arg == "--strategy-md" and i + 1 < len(extra_args):
            strategy_md_path = extra_args[i + 1]
            i += 2
        else:
            print(f"Unknown plan option: {arg}")
            return 1

    # Generate the plan
    if mode == "next":
        plan = planner.plan_next(n=n)
    elif mode == "combinatorial":
        plan = planner.plan_combinatorial()
    elif mode == "exploration":
        plan = planner.plan_exploration()
    elif mode == "transfer":
        if transfer_path is None:
            print("Error: --transfer requires a path to transfer_hypotheses.json")
            return 1
        tp = Path(transfer_path)
        if not tp.exists():
            print(f"Error: file not found: {tp}")
            return 1
        with open(tp, "r", encoding="utf-8") as f:
            hypotheses = json.load(f)
        plan = planner.plan_from_transfer(hypotheses)
    else:
        print(f"Unknown plan mode: {mode}")
        return 1

    # Display
    print(planner.format_plan(plan))

    # Optionally write strategy.md
    if strategy_md_path:
        md = planner.to_strategy_md(plan)
        Path(strategy_md_path).write_text(md, encoding="utf-8")
        print(f"\nStrategy written to: {strategy_md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
