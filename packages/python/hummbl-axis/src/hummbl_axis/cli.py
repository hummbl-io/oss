"""Axis CLI — the ladder that selects which contradiction to act on.

Usage:
  axis scan --atlas-dir ~/docs --inventory path/to/inventory.json
  axis scan --atlas-dir ~/docs --cycle-state .axis-state.json
  axis report --cycle-state .axis-state.json
  axis contradictions --atlas-dir ~/docs

The scan command:
  1. Reads Atlas markdown evidence cuts (contradictions)
  2. Reads JSON inventory (claimed state)
  3. Diffs claimed vs observed (if both provided)
  4. Prioritizes by severity
  5. Updates cycle state
  6. Prints contradiction rows
  7. Exits when stuck (3 unchanged cycles) or healthy (0 new for 3 cycles)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output — Atlas evidence cuts contain Unicode that cp1252 can't encode
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .atlas_reader import (
    diff_counts,
    extract_claimed_counts,
    load_json_inventory,
    scan_freshness,
    scan_ledger_directory,
)
from .contradiction import CycleState, Contradiction, prioritize


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_row(c: Contradiction, unchanged: int = 0) -> str:
    """Format a contradiction as a single-line row for human reading."""
    flag = " [STUCK]" if unchanged >= 3 else ""
    return (
        f"[{c.severity}] {c.id} | {c.scope} | "
        f"claim={c.claim} | obs={c.observation} | "
        f"conf={c.confidence:.0%} vol={c.volatility} "
        f"unchanged={unchanged}{flag}"
    )


def cmd_scan(args: argparse.Namespace) -> int:
    """Run one Axis cycle: read Atlas, diff, prioritize, update state, report."""
    contradictions: list[Contradiction] = []

    # 1. Read Atlas markdown evidence cuts
    atlas_dir = Path(args.atlas_dir).expanduser()
    if atlas_dir.is_dir():
        md_contradictions = scan_ledger_directory(atlas_dir, args.atlas_pattern)
        contradictions.extend(md_contradictions)
        print(f"# Atlas markdown: {len(md_contradictions)} contradictions from {atlas_dir}", file=sys.stderr)

        # 1a. Check freshness if requested
        if args.check_freshness:
            freshness_results = scan_freshness(atlas_dir, args.atlas_pattern, args.freshness_category)
            stale = [r for r in freshness_results if r.is_stale]
            if stale:
                print(f"# FRESHNESS WARNING: {len(stale)}/{len(freshness_results)} evidence cuts are stale ({args.freshness_category} window: {stale[0].max_age_days}d)", file=sys.stderr)
                for r in stale[:5]:
                    print(f"#   STALE: {r.path} ({r.age_days:.0f}d old, max {r.max_age_days}d)", file=sys.stderr)
                if len(stale) > 5:
                    print(f"#   ... and {len(stale) - 5} more stale", file=sys.stderr)
            else:
                print(f"# Freshness OK: all {len(freshness_results)} evidence cuts within {args.freshness_category} window", file=sys.stderr)
    else:
        print(f"# Atlas dir not found: {atlas_dir}", file=sys.stderr)

    # 2. Read JSON inventory and diff against observed counts
    if args.inventory:
        inv_path = Path(args.inventory).expanduser()
        if inv_path.exists():
            inventory = load_json_inventory(inv_path)
            claimed = extract_claimed_counts(inventory)
            # If we have an observed-counts file, diff against it
            if args.observed_counts:
                obs_path = Path(args.observed_counts).expanduser()
                if obs_path.exists():
                    observed = json.loads(obs_path.read_text(encoding="utf-8"))
                    count_contradictions = diff_counts(
                        claimed, observed,
                        evidence_source=str(inv_path),
                        claim_source=str(obs_path),
                    )
                    contradictions.extend(count_contradictions)
                    print(f"# Count diff: {len(count_contradictions)} contradictions", file=sys.stderr)
                else:
                    print(f"# Observed counts file not found: {obs_path}", file=sys.stderr)
            else:
                print(f"# No --observed-counts provided; skipping count diff", file=sys.stderr)
        else:
            print(f"# Inventory file not found: {inv_path}", file=sys.stderr)

    # 3. Prioritize
    prioritized = prioritize(contradictions)

    # 4. Update cycle state
    state_path = Path(args.cycle_state).expanduser() if args.cycle_state else Path(".axis-state.json")
    state = CycleState.load(state_path)
    results = state.update(prioritized)
    state.save(state_path)

    # 5. Print contradiction rows
    print(f"# Axis cycle {state.cycle} | {_utc_now()}")
    print(f"# Total contradictions: {len(prioritized)}")
    print(f"# State: {state_path}")
    print()

    for c, unchanged in results:
        print(_format_row(c, unchanged))

    # 6. Check exit condition
    should_exit, reason = state.should_exit()
    if should_exit:
        print()
        print(f"# EXIT: {reason}")
        if "stuck" in reason:
            print("# -> Escalate to human. Stop looping on these contradictions.")
            return 2  # exit code 2 = stuck, needs human
        else:
            print("# -> System healthy. Reduce cadence.")
            return 0

    # 7. Route to human if requested
    if args.bus_post and results:
        host = args.host or os.environ.get("AXIS_HOST", "unknown")
        _bus_post(
            results,
            bus_identity=args.bus_post,
            cycle=state.cycle,
            host=host,
            bus_path=Path(args.bus_path).expanduser() if args.bus_path else None,
            dry_run=args.bus_dry_run,
        )

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print cycle state history without running a new cycle."""
    state_path = Path(args.cycle_state).expanduser() if args.cycle_state else Path(".axis-state.json")
    state = CycleState.load(state_path)
    print(json.dumps(state.to_dict(), indent=2))
    return 0


def cmd_contradictions(args: argparse.Namespace) -> int:
    """List contradictions without cycle tracking (one-shot mode)."""
    atlas_dir = Path(args.atlas_dir).expanduser()
    if not atlas_dir.is_dir():
        print(f"Atlas dir not found: {atlas_dir}", file=sys.stderr)
        return 1

    contradictions = scan_ledger_directory(atlas_dir, args.atlas_pattern)
    prioritized = prioritize(contradictions)

    print(f"# {len(prioritized)} contradictions from {atlas_dir}")
    print()
    for c in prioritized:
        print(_format_row(c))

    return 0


def _format_bus_message(results: list, cycle: int, host: str) -> str:
    """Format the bus SITREP message from scan results."""
    # Severity counts
    counts: dict[str, int] = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for c, _ in results:
        counts[c.severity] = counts.get(c.severity, 0) + 1

    total = len(results)
    summary = f"host={host} Axis cycle {cycle}: {total} contradictions (P0: {counts['P0']}, P1: {counts['P1']}, P2: {counts['P2']}, P3: {counts['P3']})"

    if results:
        top_c, top_unchanged = results[0]
        summary += f". Top: [{top_c.severity}] {top_c.scope}: {top_c.claim} vs {top_c.observation}"
        if top_unchanged >= 3:
            summary += f" [STUCK {top_unchanged}c]"

    return summary


def _bus_post(
    results: list,
    bus_identity: str,
    cycle: int,
    host: str,
    bus_path: Path | None = None,
    dry_run: bool = False,
) -> bool:
    """Post a SITREP summary to the coordination bus.

    Uses bus-global.py if available, falls back to direct TSV append.
    Returns True if posted, False if failed.
    """
    message = _format_bus_message(results, cycle, host)

    if dry_run:
        print(f"# Bus dry-run: {message}", file=sys.stderr)
        return True

    # Try bus-global.py first
    if bus_path is None:
        bus_path = Path.home() / "bin" / "bus-global.py"

    if bus_path.exists():
        try:
            proc = subprocess.run(
                [sys.executable, str(bus_path), "post", "axis", "all", "SITREP", message],
                capture_output=True, text=True, timeout=15,
            )
            if proc.returncode == 0:
                print(f"# Bus posted: {message}", file=sys.stderr)
                return True
            else:
                print(f"# Bus post failed (exit {proc.returncode}): {proc.stderr.strip()}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"# Bus post timed out", file=sys.stderr)
        except Exception as exc:
            print(f"# Bus post error: {exc}", file=sys.stderr)

    # Fallback: direct TSV append to local mirror
    fallback_paths = [
        Path.home() / "Projects" / "hummbl-governance" / "_state" / "coordination" / "messages.tsv",
        Path.home() / ".agents" / "bus" / "messages.tsv",
    ]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\taxis\tall\tSITREP\t{message}"

    for fb_path in fallback_paths:
        try:
            fb_path.parent.mkdir(parents=True, exist_ok=True)
            with open(fb_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            print(f"# Bus posted (fallback TSV): {fb_path}", file=sys.stderr)
            return True
        except Exception as exc:
            print(f"# Bus fallback failed ({fb_path}): {exc}", file=sys.stderr)
            continue

    print(f"# Bus post failed — no delivery path available", file=sys.stderr)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="axis",
        description="Axis — the ladder that selects which Atlas contradiction to act on.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    scan = sub.add_parser("scan", help="Run one Axis cycle")
    scan.add_argument("--atlas-dir", default="~/docs", help="Directory of Atlas markdown evidence cuts")
    scan.add_argument("--atlas-pattern", default="hummbl-atlas-*.md", help="Glob pattern for ledger files")
    scan.add_argument("--inventory", help="JSON inventory file (claimed state)")
    scan.add_argument("--observed-counts", help="JSON file of observed counts to diff against inventory")
    scan.add_argument("--cycle-state", default=".axis-state.json", help="Cycle state file path")
    scan.add_argument("--bus-post", help="Post SITREP summary to coordination bus (any value enables)")
    scan.add_argument("--bus-path", help="Path to bus-global.py (default: ~/bin/bus-global.py)")
    scan.add_argument("--bus-dry-run", action="store_true", help="Format bus message without posting")
    scan.add_argument("--host", help="Host tag for bus messages (default: $AXIS_HOST or 'unknown')")
    scan.add_argument("--check-freshness", action="store_true", help="Check Atlas evidence cut freshness per scoring standard")
    scan.add_argument("--freshness-category", default="metadata", choices=["metadata", "dependency", "security"], help="Freshness window category (default: metadata=30d)")
    scan.set_defaults(func=cmd_scan)

    # report
    report = sub.add_parser("report", help="Print cycle state history")
    report.add_argument("--cycle-state", default=".axis-state.json", help="Cycle state file path")
    report.set_defaults(func=cmd_report)

    # contradictions
    con = sub.add_parser("contradictions", help="List contradictions (one-shot, no cycle tracking)")
    con.add_argument("--atlas-dir", default="~/docs", help="Directory of Atlas markdown evidence cuts")
    con.add_argument("--atlas-pattern", default="hummbl-atlas-*.md", help="Glob pattern for ledger files")
    con.set_defaults(func=cmd_contradictions)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
