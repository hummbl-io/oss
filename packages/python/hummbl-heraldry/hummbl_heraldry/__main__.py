"""HUMMBL Heraldry CLI.

Usage:
  hummbl-heraldry generate <agent_name> [--trust TIER] [--role ROLE] [--host HOST]
  hummbl-heraldry generate-all [--outdir DIR]
  hummbl-heraldry fleet-arms [--outdir DIR]
  hummbl-heraldry ics-flags [--outdir DIR]
  hummbl-heraldry blazon <agent_name>
  hummbl-heraldry info
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ArmsGenerator, Grammar, generate_all_arms
from .svg import render_arms_svg, render_fleet_arms_svg, render_ics_flag_svg


def cmd_generate(args: argparse.Namespace) -> int:
    gen = ArmsGenerator()
    arms = gen.generate(
        agent_name=args.agent_name,
        trust_tier=args.trust,
        role=args.role,
        host=args.host,
    )

    if args.json:
        print(json.dumps(arms.to_dict(), indent=2))
    else:
        print(f"Agent: {arms.agent_name}")
        print(f"Hash:  {arms.hash[:16]}...")
        print(f"Shield: {arms.shield.name}")
        print(f"Field:  {arms.field_tincture.name} ({arms.field_tincture.hex})")
        if arms.division_tincture:
            print(f"Division: {arms.division.name} — {arms.field_tincture.name} and {arms.division_tincture.name}")
        else:
            print(f"Division: {arms.division.name}")
        if arms.ordinary_tincture:
            print(f"Ordinary: {arms.ordinary.name} in {arms.ordinary_tincture.name}")
        else:
            print(f"Ordinary: {arms.ordinary.name}")
        if arms.charge_tincture:
            print(f"Charge: {arms.charge.name} in {arms.charge_tincture.name}")
        else:
            print(f"Charge: {arms.charge.name}")
        if arms.cadency:
            print(f"Cadency: {arms.cadency.id} ({arms.cadency.trust_tier})")
        if arms.role_badge:
            print(f"Role:   {arms.role_badge.role} {arms.role_badge.icon}")
        if arms.host_patch:
            print(f"Host:   {arms.host_patch.name}")
        print()
        print(f"Blazon: {arms.blazon}")

    if args.svg:
        svg_path = Path(args.svg)
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(render_arms_svg(arms))
        print(f"\nSVG written to {svg_path}")

    return 0


def cmd_generate_all(args: argparse.Namespace) -> int:
    all_arms = generate_all_arms()
    outdir = Path(args.outdir) if args.outdir else None

    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    for name, arms in sorted(all_arms.items()):
        if args.json:
            print(json.dumps(arms.to_dict(), indent=2))
        else:
            print(f"{name:15s}  {arms.blazon}")

        if outdir:
            svg_path = outdir / f"{name}.svg"
            svg_path.write_text(render_arms_svg(arms))

    if outdir:
        # Write JSON manifest
        manifest = {name: arms.to_dict() for name, arms in sorted(all_arms.items())}
        (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"\n{len(all_arms)} arms + manifest written to {outdir}")

    return 0


def cmd_fleet_arms(args: argparse.Namespace) -> int:
    grammar = Grammar()
    fleet = grammar.fleet_arms()
    print(f"Fleet: {fleet['name']}")
    print(f"Blazon: {fleet['blazon']}")
    print(f"Description: {fleet['description']}")

    if args.outdir:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        svg_path = outdir / "fleet-arms.svg"
        svg_path.write_text(render_fleet_arms_svg())
        print(f"\nSVG written to {svg_path}")

    return 0


def cmd_ics_flags(args: argparse.Namespace) -> int:
    grammar = Grammar()
    flags = grammar.ics_flags()

    if args.outdir:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        for flag in flags:
            svg = render_ics_flag_svg(flag.bus_type, flag.color_scheme)
            fname = f"{flag.bus_type.lower()}.svg"
            (outdir / fname).write_text(svg)
            ics_info = f" ({flag.ics_letter} — {flag.ics_name})" if flag.ics_letter else ""
            print(f"  {flag.bus_type:15s}  {flag.color_scheme}{ics_info}  → {fname}")
        print(f"\n{len(flags)} ICS flags written to {outdir}")
    else:
        for flag in flags:
            ics_info = f" ({flag.ics_letter} — {flag.ics_name})" if flag.ics_letter else ""
            print(f"  {flag.bus_type:15s}  {flag.color_scheme}{ics_info}")

    return 0


def cmd_blazon(args: argparse.Namespace) -> int:
    gen = ArmsGenerator()
    arms = gen.generate(args.agent_name)
    print(arms.blazon)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    grammar = Grammar()
    print(f"HUMMBL Heraldric Identity System v0.1.0")
    print(f"  Shield shapes: {len(grammar.shield_shapes())}")
    print(f"  Tinctures: {len(grammar.tinctures())}")
    print(f"  Divisions: {len(grammar.divisions())}")
    print(f"  Ordinaries: {len(grammar.ordinaries())}")
    print(f"  Charges: {len(grammar.charges())}")
    print(f"  Cadency marks: {len(grammar.cadency_marks())}")
    print(f"  Role badges: {len(grammar.role_badges())}")
    print(f"  Host patches: {len(grammar.host_patches())}")
    print(f"  ICS flags: {len(grammar.ics_flags())}")
    combos = (
        len(grammar.shield_shapes())
        * len(grammar.tinctures())
        * len(grammar.divisions())
        * len(grammar.ordinaries())
        * len(grammar.charges())
    )
    print(f"  Combinations: {combos:,}")
    fleet = grammar.fleet_arms()
    print(f"  Fleet arms: {fleet['name']}")
    print(f"  Fleet blazon: {fleet['blazon']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hummbl-heraldry",
        description="HUMMBL Procedural Heraldic Identity System",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = sub.add_parser("generate", help="Generate arms for a single agent")
    p_gen.add_argument("agent_name", help="Agent name (e.g. devin)")
    p_gen.add_argument("--trust", help="Trust tier (OWNER, TRUSTED, MEDIUM-HIGH, MEDIUM, PROBATIONARY)")
    p_gen.add_argument("--role", help="Agent role (coordinator, engineer, memory, scanner, research, ops)")
    p_gen.add_argument("--host", help="Host ID (delta, anvil, hummbl-vps, beachhead, slate)")
    p_gen.add_argument("--json", action="store_true", help="Output as JSON")
    p_gen.add_argument("--svg", help="Write SVG to this path")
    p_gen.set_defaults(func=cmd_generate)

    # generate-all
    p_all = sub.add_parser("generate-all", help="Generate arms for all 11 fleet agents")
    p_all.add_argument("--outdir", help="Output directory for SVGs + manifest")
    p_all.add_argument("--json", action="store_true", help="Output as JSON")
    p_all.set_defaults(func=cmd_generate_all)

    # fleet-arms
    p_fleet = sub.add_parser("fleet-arms", help="Show HUMMBL LLC fleet arms")
    p_fleet.add_argument("--outdir", help="Output directory for SVG")
    p_fleet.set_defaults(func=cmd_fleet_arms)

    # ics-flags
    p_ics = sub.add_parser("ics-flags", help="Generate ICS signal flags for bus message types")
    p_ics.add_argument("--outdir", help="Output directory for SVGs")
    p_ics.set_defaults(func=cmd_ics_flags)

    # blazon
    p_blazon = sub.add_parser("blazon", help="Print the blazon for an agent")
    p_blazon.add_argument("agent_name", help="Agent name")
    p_blazon.set_defaults(func=cmd_blazon)

    # info
    p_info = sub.add_parser("info", help="Show grammar statistics")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
