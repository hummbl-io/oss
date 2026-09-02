"""CLI for HUMMBL design token generation.

Usage:
  python -m hummbl_design_tokens generate --all --outdir ./output
  python -m hummbl_design_tokens generate --base24 --css --outdir ./output
  python -m hummbl_design_tokens info
  python -m hummbl_design_tokens validate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hummbl_design_tokens.loader import TokenSystem
from hummbl_design_tokens.color import contrast_ratio, delta_e2000
from hummbl_design_tokens.generators import (
    generate_base24,
    generate_css,
    generate_python_module,
    generate_typescript_module,
    generate_livery,
    generate_swatches_html,
)


def cmd_generate(args: argparse.Namespace) -> int:
    ts = TokenSystem(args.tokens)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    written = []

    if args.all or args.base24:
        p = outdir / "base24-hummbl.yml"
        p.write_text(generate_base24(ts))
        written.append(str(p))

    if args.all or args.css:
        p = outdir / "hummbl-tokens.css"
        p.write_text(generate_css(ts))
        written.append(str(p))

    if args.all or args.python:
        p = outdir / "colors.py"
        p.write_text(generate_python_module(ts))
        written.append(str(p))

    if args.all or args.typescript:
        p = outdir / "colors.ts"
        p.write_text(generate_typescript_module(ts))
        written.append(str(p))

    if args.all or args.liveries:
        ldir = outdir / "liveries"
        ldir.mkdir(exist_ok=True)
        for agent in ts.agent_names():
            p = ldir / f"{agent}.json"
            p.write_text(generate_livery(ts, agent))
            written.append(str(p))

    if args.all or args.swatches:
        p = outdir / "swatches.html"
        p.write_text(generate_swatches_html(ts))
        written.append(str(p))

    if not written:
        print("No outputs selected. Use --all or specify individual formats.")
        return 1

    for p in written:
        print(f"  wrote {p}")
    print(f"\n{len(written)} file(s) written to {outdir}/")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    ts = TokenSystem(args.tokens)
    print(f"HUMMBL Design Token System v{ts.version}")
    print(f"  Color space: {ts.meta.get('color_space', 'OKLCH')}")
    print(f"  Dark mode: {ts.meta.get('dark_mode', 'primary')}")
    print(f"  Canonical surface: {ts.canonical_surface}")
    print(f"  Agents: {len(ts.agents)} ({', '.join(ts.agent_names())})")
    print(f"  Trust tiers: {len(ts.trust_tiers)}")
    print(f"  Bus types: {len(ts.bus_types)}")
    print(f"  Status colors: {len(ts.status)}")
    print(f"  Heraldry combinations: {ts.heraldry.get('total_combinations', 'N/A')}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ts = TokenSystem(args.tokens)
    errors = []
    warnings = []
    base = ts.surfaces["base"]

    # Check contrast ratios for status colors (text indicators — need AAA 7:1)
    min_safety = float(ts.accessibility.get("min_contrast_safety_critical", "7.0").rstrip(":1"))

    for sname, st in ts.status.items():
        cr = contrast_ratio(st["hex"], base)
        if cr < min_safety:
            errors.append(f"status:{sname} contrast {cr:.2f}:1 < {min_safety}:1 (AAA required for safety-critical)")
        else:
            print(f"  ✓ status:{sname} {cr:.2f}:1 (AAA)")

    # Trust tier colors are badge/background colors, not text — they need
    # to be distinguishable from each other and from the base surface, but
    # don't need to meet text contrast ratios. Flag only if < 1.5:1 (invisible)
    for tier_name, tier in ts.trust_tiers.items():
        cr = contrast_ratio(tier["hex"], base)
        if cr < 1.5:
            warnings.append(f"trust:{tier_name} contrast {cr:.2f}:1 < 1.5:1 (nearly invisible on base)")
        else:
            print(f"  ✓ trust:{tier_name} {cr:.2f}:1 (badge/background — not text)")

    # Check agent color separation (dE2000 > 10 ideal, > 5 minimum)
    min_de_ideal = ts.accessibility.get("min_de2000_agent_colors", 10)
    agents = ts.agent_names()
    for i, a1 in enumerate(agents):
        for a2 in agents[i + 1:]:
            de = delta_e2000(ts.agents[a1]["hex_dark"], ts.agents[a2]["hex_dark"])
            if de < 5.0:
                errors.append(f"agent:{a1} vs agent:{a2} dE2000={de:.1f} < 5.0 (too similar)")
            elif de < min_de_ideal:
                warnings.append(f"agent:{a1} vs agent:{a2} dE2000={de:.1f} < {min_de_ideal} (ideal)")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\n✓ All checks passed ({len(warnings)} warning(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hummbl-design-tokens", description="HUMMBL design token system")
    parser.add_argument("--tokens", default=None, help="Path to tokens.json (default: bundled)")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate output formats")
    gen.add_argument("--all", action="store_true", help="Generate all formats")
    gen.add_argument("--base24", action="store_true")
    gen.add_argument("--css", action="store_true")
    gen.add_argument("--python", action="store_true")
    gen.add_argument("--typescript", action="store_true")
    gen.add_argument("--liveries", action="store_true")
    gen.add_argument("--swatches", action="store_true")
    gen.add_argument("--outdir", default="./output", help="Output directory")
    gen.set_defaults(func=cmd_generate)

    info = sub.add_parser("info", help="Show token system info")
    info.set_defaults(func=cmd_info)

    val = sub.add_parser("validate", help="Validate tokens (contrast, dE2000)")
    val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
