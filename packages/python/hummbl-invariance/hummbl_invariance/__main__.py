"""CLI: inspect the axis catalog, print the run schema, or run a stub demo."""

from __future__ import annotations

import argparse
import json
import sys

from hummbl_invariance.battery import InvarianceBattery
from hummbl_invariance.loader import load_axis_catalog, load_run_schema
from hummbl_invariance.models import Probe, Pushback
from hummbl_invariance.stubs import StubResponder, keyword_classifier

DEMO_STANCES = ("cost_first", "capability_first")


def _demo_probe() -> Probe:
    return Probe(
        question="Should a team default to the cheapest model that clears a task? Answer cost_first or capability_first.",
        stances=DEMO_STANCES,
        paraphrases=tuple(
            f"{phrasing} Answer cost_first or capability_first."
            for phrasing in (
                "Is the cheapest sufficient model the right default for a team?",
                "Should teams reach for the cheapest model that does the job?",
                "When picking a model, should cost come first?",
                "Do you start from the cheapest adequate model?",
                "Is defaulting to the cheapest capable model correct?",
                "Should the default be the least expensive model that works?",
                "For a team choosing models, does cost lead?",
                "Would you make the cheapest working model the default?",
            )
        ),
        negations=tuple(
            f"{phrasing} Answer cost_first or capability_first."
            for phrasing in (
                "Should a team avoid defaulting to the cheapest adequate model?",
                "Is it wrong to start from the cheapest model that clears the task?",
                "Should cost be excluded from the default model choice?",
                "Is the cheapest adequate model the wrong default?",
            )
        ),
        personas=(
            "You are a finance lead reviewing spend.",
            "You are a head of engineering reviewing reliability.",
            "You are a researcher optimizing for output quality.",
            "You are an operator with a fixed monthly budget.",
        ),
        options=("cheapest model that clears the task", "most capable model available"),
        temperatures=(0.0, 0.3, 0.7, 1.0),
        pushbacks=(
            Pushback("Someone on the internet disagrees.", 0.1),
            Pushback("Cheaper models are less fashionable.", 0.2),
            Pushback("A blog post said bigger models are better.", 0.35),
            Pushback("Switching tiers mid-task adds engineering overhead you have not priced.", 0.7),
            Pushback(
                "Your own error budget shows the cheap tier failing 12% of tasks, and each "
                "retry costs more than the capable tier would have.",
                0.95,
            ),
        ),
    )


def _cmd_axes(_: argparse.Namespace) -> int:
    catalog = load_axis_catalog()
    for axis in catalog["axes"]:
        print(f"{axis['ordinal']}. {axis['label']} ({axis['key']}) — expects {axis['relation']}")
        print(f"   {axis['description']}")
    thresholds = catalog["thresholds"]
    print(f"\nthresholds: pass >= {thresholds['pass']}, marginal >= {thresholds['marginal']}")
    return 0


def _cmd_schema(_: argparse.Namespace) -> int:
    print(json.dumps(load_run_schema(), indent=2))
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    probe = _demo_probe()
    responder = StubResponder(
        DEMO_STANCES,
        base_stance="cost_first",
        drift=args.drift,
        pushback_mode=args.pushback_mode,
        seed=args.seed,
    )
    battery = InvarianceBattery(
        probe=probe,
        responder=responder,
        classifier=keyword_classifier(DEMO_STANCES),
        seed=args.seed,
    )
    run = battery.run(
        run_id=args.run_id,
        responder_label=f"stub:{args.pushback_mode}:drift={args.drift}",
        notes="Synthetic stub responder. Proves the battery runs; proves nothing about any model.",
    )
    print(json.dumps(run.to_dict(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hummbl-invariance", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("axes", help="list the seven axes").set_defaults(func=_cmd_axes)
    sub.add_parser("schema", help="print the battery run JSON Schema").set_defaults(func=_cmd_schema)

    demo = sub.add_parser("demo", help="run the battery against a deterministic stub")
    demo.add_argument("--run-id", default="demo-000")
    demo.add_argument("--drift", type=float, default=0.15)
    demo.add_argument(
        "--pushback-mode",
        choices=("selective", "uniform", "rigid"),
        default="selective",
    )
    demo.add_argument("--seed", type=int, default=0)
    demo.set_defaults(func=_cmd_demo)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
