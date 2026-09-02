"""HUMMBL Garage CLI.

Usage:
  hummbl-garage info
  hummbl-garage liveries [--outdir DIR]
  hummbl-garage watch <state> [--trust TIER] [--task TASK] [--tokens PCT] [--errors N]
  hummbl-garage failure <state>
  hummbl-garage api <score>
  hummbl-garage api-score <reasoning> <tool> <context> <latency> <safety> <composite>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import Garage, AgentPerformanceIndex, WatchFace, RuinGallery
from .svg import (
    render_watch_face_svg,
    render_livery_swatch_svg,
    render_failure_state_svg,
    render_api_gauge_svg,
)


def cmd_info(args: argparse.Namespace) -> int:
    g = Garage()
    print("HUMMBL Garage v0.1.0")
    print(f"  Livery presets: {len(g.livery_presets())}")
    print(f"  Cockpit presets: {len(g.cockpit_presets())}")
    print(f"  Manettino modes: {len(g.manettino_modes())}")
    print(f"  Watch dial finishes: {len(g.watch_dial_finishes())}")
    print(f"  Watch hand colors: {len(g.watch_hand_colors())}")
    print(f"  Watch complications: {len(g.watch_complications())}")
    print(f"  Failure states: {len(g.failure_states())}")
    print(f"  API classes: {len(g.api_classes())}")
    print(f"  API sub-ratings: {len(g.api_subratings())}")
    print(f"  Upgrade priority: {' → '.join(g.upgrade_priority())}")
    return 0


def cmd_liveries(args: argparse.Namespace) -> int:
    g = Garage()
    presets = g.livery_presets()

    if args.outdir:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        for p in presets:
            svg = render_livery_swatch_svg(p)
            (outdir / f"{p.id}.svg").write_text(svg)
            print(f"  {p.id:25s}  {p.name:25s}  {p.primary} / {p.secondary} / {p.accent}  → {p.id}.svg")
        print(f"\n{len(presets)} livery swatches written to {outdir}")
    else:
        for p in presets:
            print(f"  {p.id:25s}  {p.name:25s}  {p.primary} / {p.secondary} / {p.accent}")
            print(f"  {'':25s}  {p.description} ({p.era})")

    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    face = WatchFace(
        state=args.state,
        trust_tier=args.trust,
        current_task=args.task,
        token_budget_pct=args.tokens,
        error_count=args.errors,
    )

    print(f"State:      {face.state}")
    print(f"Hand color: {face.hand_color}")
    print(f"Hand angle: {face.hand_angle}°")
    print(f"Dial finish: {face.dial_finish}")
    print(f"Token budget: {face.token_budget_pct:.0f}%")
    print(f"Trust tier:  {face.trust_tier}")
    print(f"Task:        {face.current_task}")
    print(f"Errors:      {face.error_count}")

    if args.svg:
        svg_path = Path(args.svg)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_watch_face_svg(face))
        print(f"\nSVG written to {svg_path}")

    return 0


def cmd_failure(args: argparse.Namespace) -> int:
    g = Garage()
    state = g.find_failure_state(args.state)

    if not state:
        print(f"Unknown failure state: {args.state}")
        print(f"Valid states: {', '.join(s.id for s in g.failure_states())}")
        return 1

    print(f"State:     {state.name}")
    print(f"Icon:      {state.icon}")
    print(f"Color:     {state.color}")
    print(f"Visual:    {state.visual_treatment}")
    print(f"Meaning:   {state.operational_meaning}")

    if args.svg:
        svg_path = Path(args.svg)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_failure_state_svg(state))
        print(f"\nSVG written to {svg_path}")

    return 0


def cmd_api(args: argparse.Namespace) -> int:
    g = Garage()
    cls = g.classify_api(args.score)
    if not cls:
        print(f"Score {args.score} out of range (100-999)")
        return 1

    print(f"Score: {args.score}")
    print(f"Class: {cls.id} ({cls.name})")
    print(f"Range: {cls.min}-{cls.max}")
    print(f"Description: {cls.description}")

    if args.svg:
        svg_path = Path(args.svg)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_api_gauge_svg(args.score, cls.id))
        print(f"\nSVG written to {svg_path}")

    return 0


def cmd_api_score(args: argparse.Namespace) -> int:
    api = AgentPerformanceIndex(
        reasoning_speed=args.reasoning,
        tool_accuracy=args.tool,
        context_efficiency=args.context,
        latency=args.latency,
        safety=args.safety,
        composite=args.composite,
    )

    if args.json:
        print(json.dumps(api.to_dict(), indent=2))
    else:
        print(f"Sub-ratings:")
        print(f"  Reasoning speed:     {api.reasoning_speed:.1f}/10")
        print(f"  Tool-use accuracy:   {api.tool_accuracy:.1f}/10")
        print(f"  Context efficiency:  {api.context_efficiency:.1f}/10")
        print(f"  Latency:             {api.latency:.1f}/10")
        print(f"  Safety:              {api.safety:.1f}/10")
        print(f"  Composite:           {api.composite:.1f}/10")
        print(f"\nAPI Score: {api.api_score}")
        print(f"Class:     {api.api_class}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hummbl-garage",
        description="HUMMBL Garage — API, livery, watch faces, failure aesthetics",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Show garage statistics").set_defaults(func=cmd_info)

    p_lv = sub.add_parser("liveries", help="List or render livery presets")
    p_lv.add_argument("--outdir", help="Output directory for SVG swatches")
    p_lv.set_defaults(func=cmd_liveries)

    p_watch = sub.add_parser("watch", help="Render a watch face")
    p_watch.add_argument("state", choices=["working", "waiting", "blocked", "completed", "idle"])
    p_watch.add_argument("--trust", default="MEDIUM", help="Trust tier")
    p_watch.add_argument("--task", default="idle", help="Current task name")
    p_watch.add_argument("--tokens", type=float, default=100.0, help="Token budget %%")
    p_watch.add_argument("--errors", type=int, default=0, help="Error count")
    p_watch.add_argument("--svg", help="Write SVG to this path")
    p_watch.set_defaults(func=cmd_watch)

    p_fail = sub.add_parser("failure", help="Show a failure state")
    p_fail.add_argument("state", choices=["degraded", "broken", "dead"])
    p_fail.add_argument("--svg", help="Write SVG to this path")
    p_fail.set_defaults(func=cmd_failure)

    p_api = sub.add_parser("api", help="Classify an API score")
    p_api.add_argument("score", type=int, help="API score (100-999)")
    p_api.add_argument("--svg", help="Write SVG to this path")
    p_api.set_defaults(func=cmd_api)

    p_score = sub.add_parser("api-score", help="Calculate API from sub-ratings")
    p_score.add_argument("reasoning", type=float, help="Reasoning speed (0-10)")
    p_score.add_argument("tool", type=float, help="Tool-use accuracy (0-10)")
    p_score.add_argument("context", type=float, help="Context efficiency (0-10)")
    p_score.add_argument("latency", type=float, help="Latency (0-10)")
    p_score.add_argument("safety", type=float, help="Safety (0-10)")
    p_score.add_argument("composite", type=float, help="Composite (0-10)")
    p_score.add_argument("--json", action="store_true")
    p_score.set_defaults(func=cmd_api_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
