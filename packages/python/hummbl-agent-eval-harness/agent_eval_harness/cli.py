"""CLI interface for agent-eval-harness.

Modified by HUMMBL on 2026-09-08: return failures to callers and validate rules.
"""

from __future__ import annotations

import argparse
import re
from .eval import AgentEvalHarness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regex constraint checks for agent output")
    parser.add_argument("text", help="Agent text response to evaluate")
    parser.add_argument("--forbid", nargs="+", help="Forbidden terms/regexes (negative constraints)")
    parser.add_argument("--require", nargs="+", help="Required terms/regexes (positive constraints)")
    args = parser.parse_args(argv)
    if not args.forbid and not args.require:
        parser.error("supply at least one --require or --forbid rule")
    for pattern in [*(args.forbid or []), *(args.require or [])]:
        try:
            re.compile(pattern)
        except re.error as exc:
            parser.error(f"invalid regular expression: {exc}")

    harness = AgentEvalHarness()
    if args.forbid:
        for i, term in enumerate(args.forbid):
            harness.add_regex_constraint(f"FORBID_{i+1}", term, f"Must not contain '{term}'", must_not_match=True)
    if args.require:
        for i, term in enumerate(args.require):
            harness.add_regex_constraint(f"REQUIRE_{i+1}", term, f"Must contain '{term}'", must_not_match=False)

    res = harness.evaluate(args.text)
    print(f"Eval Score: {res.score}% ({res.passed_rules}/{res.total_rules} constraints passed)")
    if res.violations:
        print("Violations:")
        for v in res.violations:
            print(f"  * {v}")
    return 1 if res.failed_rules else 0


if __name__ == "__main__":
    raise SystemExit(main())
