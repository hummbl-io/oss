"""Runner CLI for the governance simulation prototype.

Usage::

    python -m hummbl_tuples.simulation                         # print trace JSON
    python -m hummbl_tuples.simulation --summary                # print scalar summary
    python -m hummbl_tuples.simulation --out trace.json         # write trace to file

The CLI is intentionally minimal: no external deps, no colored output, no
config files. It exists so that a prospect demo can be run from a fresh
checkout with ``make simulate``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import Environment, trace_summary
from .scenarios import gemini_probation_scenario

_SCENARIOS = {
    "gemini-probation": gemini_probation_scenario,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_tuples.simulation",
        description=(
            "Run the rule-based governance simulation prototype and emit a "
            "schema-valid tuple trace."
        ),
    )
    parser.add_argument(
        "--scenario",
        default="gemini-probation",
        choices=sorted(_SCENARIOS),
        help="Scenario to run (default: gemini-probation).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="RNG seed (default: 0).",
    )
    parser.add_argument(
        "--out",
        default="-",
        help="Output path for trace JSON ('-' = stdout).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print scalar trace summary instead of the full trace.",
    )
    args = parser.parse_args(argv)

    scenario = _SCENARIOS[args.scenario]()
    env = Environment(scenario, seed=args.seed)
    trace = env.run()

    if args.summary:
        payload = json.dumps(trace_summary(trace), indent=2, sort_keys=True)
    else:
        payload = json.dumps(trace, indent=2, sort_keys=True)

    if args.out == "-":
        print(payload)
    else:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(
            f"wrote {len(trace)} events to {args.out}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
