"""ARSI — Agent Recursive Self-check In.

Session/daily baseline check-in for agents, mirroring the human HRSI
check-in (hrsi_checkin.py) but built for a key asymmetry: a human's
self-report IS the ground truth (only they know felt safety/mattering/
connection), while an agent's self-report is TESTIMONY that must be
verified against external measurement.

Two layers:

1. Self-report — what the agent believes about itself (opstate, scores,
   AUOE: the agent-unique observation only it could surface).
2. Probe — externally measured values for the same dimensions, supplied
   via --probe-json (the fleet's roster/audit tooling emits this file).

The divergence between the layers is itself the signal: an agent that
reports AVAILABLE while measurement shows degraded is more dangerous
than an agent that knows it is degraded. The gate therefore requires
self-report and probe to AGREE (calibrated), not merely look good.

Opstate options: AVAILABLE, EXECUTING, DEGRADED, QUOTA_BOUND,
CONTEXT_STALE, ISOLATED, QUARANTINED, TRANSITION.

arsi_safe = opstate==AVAILABLE AND all gate dimensions >=3
            (probe values dominate when a probe is supplied)
            AND calibrated when a probe is supplied (|self - measured| <= 1)

Usage:
    python -m hummbl_cognition arsi-checkin \\
        --agent my-agent \\
        --opstate AVAILABLE \\
        --integrity 4 --scope 4 --connectivity 5 \\
        --auoe "Noticed drift in X that no other agent could see" \\
        --probe-json /path/to/probe.json

    python -m hummbl_cognition arsi-checkin --status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from hummbl_cognition.belonging_check import SCORE_RANGE
from hummbl_cognition.hrsi_checkin import (
    _append_cycle,
    _cycle_transaction_lock,
    _load_cycles,
    _restore,
    _snapshot,
    resolve_cognition_dir,
)
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPSTATE_VALUES = {
    "AVAILABLE",
    "EXECUTING",
    "DEGRADED",
    "QUOTA_BOUND",
    "CONTEXT_STALE",
    "ISOLATED",
    "QUARANTINED",
    "TRANSITION",
}

GATE_DIMS = ("integrity", "scope", "connectivity")
PROBEABLE_DIMS = GATE_DIMS + ("budget", "freshness_hours")
CALIBRATION_TOLERANCE = 1  # |self - measured| <= 1 counts as agreement

_VENDOR = "local"
_MODEL = "self-report"
_TYPE = "convention"
_SCOPE = "convention"
_BASE_TAGS = ("arsi-cycle",)

COGNITION_DIR = resolve_cognition_dir()
CYCLES_PATH = COGNITION_DIR / "arsi_cycles.jsonl"
LEDGER_PATH = COGNITION_DIR / "ledger.jsonl"
LOCK_PATH = COGNITION_DIR / ".arsi-checkin.lock"


# ---------------------------------------------------------------------------
# Probe loading
# ---------------------------------------------------------------------------


def _load_probe(path: Path) -> dict:
    """Load external measurements for the gate dimensions.

    Expected JSON shape (any subset of PROBEABLE_DIMS):
        {"integrity": 4, "scope": 5, "connectivity": 2,
         "budget": 3, "freshness_hours": 48.0}
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("probe file must contain a JSON object")
    probe = {}
    for dim in PROBEABLE_DIMS:
        if dim in data:
            probe[dim] = data[dim]
    return probe


def _compute_calibration(self_report: dict, probe: dict) -> dict:
    """Per-dimension divergence between self-report and probe.

    Returns {dim: {"self": x, "measured": y, "delta": x - y}} for dims
    present in both layers. A nonzero delta in EITHER direction matters:
    over-reporting hides degradation; under-reporting means the agent's
    self-model has drifted the other way.
    """
    calibration = {}
    for dim in PROBEABLE_DIMS:
        if dim in probe and self_report.get(dim) is not None:
            calibration[dim] = {
                "self": self_report[dim],
                "measured": probe[dim],
                "delta": round(self_report[dim] - probe[dim], 4),
            }
    return calibration


def _is_calibrated(calibration: dict) -> bool:
    """True when every probed dimension agrees within tolerance."""
    return all(
        abs(dim["delta"]) <= CALIBRATION_TOLERANCE for dim in calibration.values()
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def record_cycle(
    agent: str,
    opstate: str,
    integrity: int,
    scope: int,
    connectivity: int,
    auoe: str,
    budget: Optional[int] = None,
    freshness_hours: Optional[float] = None,
    peers: Optional[str] = None,
    probe: Optional[dict] = None,
    share_sensitive_notes: bool = False,
    today: Optional[str] = None,
    cycles_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    lock_path: Optional[Path] = None,
    force: bool = False,
) -> dict:
    """Record one ARSI check-in cycle.

    Writes to:
    - arsi_cycles.jsonl (full cycle record, append-only)
    - CLP ledger (cycle summary; raw AUOE/peers hashed unless
      share_sensitive_notes)

    Returns the cycle dict.
    """
    if cycles_path is None:
        cycles_path = CYCLES_PATH
    if lock_path is None:
        lock_path = LOCK_PATH
    if not agent or not agent.strip():
        raise ValueError("--agent is required: ARSI records which agent checked in")
    if opstate not in OPSTATE_VALUES:
        raise ValueError(
            f"opstate must be one of {sorted(OPSTATE_VALUES)}, got {opstate!r}"
        )
    for name, val in [
        ("integrity", integrity),
        ("scope", scope),
        ("connectivity", connectivity),
    ]:
        if val not in SCORE_RANGE:
            raise ValueError(f"{name} must be 1-5, got {val}")
    if not auoe or not auoe.strip():
        raise ValueError(
            "--auoe is required: record the observation only this agent could make"
        )
    if budget is not None and budget not in SCORE_RANGE:
        raise ValueError(f"budget must be 1-5, got {budget}")
    if freshness_hours is not None and freshness_hours < 0:
        raise ValueError(f"freshness_hours must be >= 0, got {freshness_hours}")

    d = today or date.today().isoformat()
    ts = datetime.now(timezone.utc).isoformat()

    self_report = {
        "integrity": integrity,
        "scope": scope,
        "connectivity": connectivity,
    }
    if budget is not None:
        self_report["budget"] = budget
    if freshness_hours is not None:
        self_report["freshness_hours"] = freshness_hours

    probe = probe or {}
    calibration = _compute_calibration(self_report, probe)
    calibrated = _is_calibrated(calibration) if calibration else None

    # Probe dominates the gate when present; without a probe the gate is
    # self-reported and flagged unverified.
    gate_values = {
        dim: probe.get(dim, self_report[dim]) for dim in GATE_DIMS
    }
    arsi_safe = (
        opstate == "AVAILABLE"
        and all(v >= 3 for v in gate_values.values())
        and calibrated is not False
    )

    gate_avg = round(sum(gate_values.values()) / len(GATE_DIMS), 2)

    cycle: dict = {
        "date": d,
        "timestamp": ts,
        "agent": agent.strip(),
        "opstate": opstate,
        "integrity": integrity,
        "scope": scope,
        "connectivity": connectivity,
        "gate_avg": gate_avg,
        "arsi_safe": arsi_safe,
        "verified": bool(probe),
        "auoe": auoe.strip(),
    }
    if budget is not None:
        cycle["budget"] = budget
    if freshness_hours is not None:
        cycle["freshness_hours"] = freshness_hours
    if peers:
        cycle["peers"] = peers.strip()
    if probe:
        cycle["probe"] = probe
        cycle["calibration"] = calibration
        cycle["calibrated"] = calibrated

    # CLP ledger entry — cycle summary; AUOE/peers hashed by default.
    tags = list(_BASE_TAGS)
    if arsi_safe:
        tags.append("arsi-safe")
    if probe and calibrated is False:
        tags.append("arsi-uncalibrated")

    content_parts = [
        f"ARSI cycle {d}: agent={agent.strip()} opstate={opstate}",
        f"gate_avg={gate_avg:.1f} (i={integrity}/s={scope}/c={connectivity})",
        f"verified={bool(probe)}",
    ]
    if calibrated is not None:
        content_parts.append(f"calibrated={calibrated}")
    auoe_value = auoe.strip()
    if share_sensitive_notes:
        content_parts.append(f"AUOE: {auoe_value}")
    else:
        auoe_hash = hashlib.sha256(auoe_value.encode("utf-8")).hexdigest()
        content_parts.append(f"AUOE recorded locally; auoe_sha256={auoe_hash}")
    if budget is not None:
        content_parts.append(f"budget: {budget}/5")
    if freshness_hours is not None:
        content_parts.append(f"freshness: {freshness_hours}h")
    if peers:
        peers_value = peers.strip()
        if share_sensitive_notes:
            content_parts.append(f"peers: {peers_value}")
        else:
            peers_hash = hashlib.sha256(peers_value.encode("utf-8")).hexdigest()
            content_parts.append(f"peers recorded locally; peers_sha256={peers_hash}")

    content = " | ".join(content_parts)
    if len(content) > 4096:
        content = content[:4096]

    entry = LedgerEntry.create(
        agent=agent.strip(),
        vendor=_VENDOR,
        model=_MODEL,
        entry_type=_TYPE,
        scope=_SCOPE,
        content=content,
        confidence=1.0,
        tags=tuple(tags),
    )
    effective_ledger_path = ledger_path or LEDGER_PATH
    cycle["ledger_id"] = entry.id
    with _cycle_transaction_lock(lock_path):
        cycles_before = _snapshot(cycles_path)
        ledger_before = _snapshot(effective_ledger_path)
        try:
            _append_arsi_cycle(cycle, cycles_path, force=force)
            post_entry(entry, ledger_path=effective_ledger_path)
        except Exception:
            _restore(cycles_path, cycles_before)
            _restore(effective_ledger_path, ledger_before)
            raise

    return cycle


def _append_arsi_cycle(cycle: dict, path: Path, force: bool = False) -> None:
    """Append or, with force, overwrite the entry for the SAME (agent, date).

    Unlike hrsi (one human per day), many agents share arsi_cycles.jsonl
    on the same date — dedup must match agent AND date.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if force and path.exists():
        existing = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        same_slot = (
                            entry.get("date") == cycle.get("date")
                            and entry.get("agent") == cycle.get("agent")
                        )
                        if not same_slot:
                            existing.append(line)
                    except json.JSONDecodeError:
                        existing.append(line)
        with open(path, "w", encoding="utf-8") as f:
            for line in existing:
                f.write(line + "\n")
            f.write(json.dumps(cycle, ensure_ascii=False) + "\n")
        return
    _append_cycle(cycle, path, force=False)


def get_status(cycles_path: Optional[Path] = None) -> dict:
    """Return ARSI status summary across all agents."""
    if cycles_path is None:
        cycles_path = CYCLES_PATH
    cycles = _load_cycles(cycles_path)
    agents = sorted({c.get("agent", "?") for c in cycles})
    dates = sorted({c.get("date", "") for c in cycles if c.get("date")})
    streak = _day_streak(dates)
    probed = [c for c in cycles if c.get("verified")]
    calibrated = [c for c in probed if c.get("calibrated")]
    last = cycles[-1] if cycles else {}
    return {
        "total_cycles": len(cycles),
        "agents_seen": agents,
        "days_with_cycles": len(dates),
        "current_streak": streak,
        "probed_cycles": len(probed),
        "calibrated_cycles": len(calibrated),
        "last_agent": last.get("agent"),
        "last_date": last.get("date"),
        "last_opstate": last.get("opstate"),
        "last_arsi_safe": last.get("arsi_safe"),
    }


def _day_streak(dates: list[str]) -> int:
    """Consecutive-day streak ending today, over days with >=1 cycle."""
    if not dates:
        return 0
    unique = sorted({date.fromisoformat(d) for d in dates}, reverse=True)
    streak = 0
    expected = date.today()
    for day in unique:
        if day == expected:
            streak += 1
            expected = date.fromordinal(expected.toordinal() - 1)
        elif day < expected:
            break
    return streak


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition arsi-checkin",
        description="ARSI — agent self-check-in (self-report + probe layers)",
    )
    parser.add_argument("--agent", help="Agent identifier (required)")
    parser.add_argument(
        "--opstate",
        choices=sorted(OPSTATE_VALUES),
        help="Current operational state",
    )
    parser.add_argument("--integrity", type=int, choices=SCORE_RANGE, metavar="1-5")
    parser.add_argument("--scope", type=int, choices=SCORE_RANGE, metavar="1-5")
    parser.add_argument("--connectivity", type=int, choices=SCORE_RANGE, metavar="1-5")
    parser.add_argument(
        "--auoe",
        help="Agent-unique observation — what only this agent could see (required)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        choices=SCORE_RANGE,
        metavar="1-5",
        help="Remaining quota/compute headroom (1=exhausted, 5=full)",
    )
    parser.add_argument(
        "--freshness",
        type=float,
        metavar="HOURS",
        help="Hours since last state sync / context age",
    )
    parser.add_argument(
        "--peers", help="Peers interacted with or delegations (free text, optional)"
    )
    parser.add_argument(
        "--probe-json",
        help="Path to external probe measurements JSON (verified layer)",
    )
    parser.add_argument(
        "--share-sensitive-notes",
        action="store_true",
        help="Opt in to copying raw AUOE and peers text into the shared CLP ledger",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show ARSI status summary without recording",
    )
    parser.add_argument("--ledger", help="Override ledger path")
    parser.add_argument(
        "--cycles", help="Override arsi_cycles.jsonl path (for testing)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite this agent's entry for today if it already exists",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    cycles_path = Path(args.cycles) if getattr(args, "cycles", None) else CYCLES_PATH

    if args.status:
        status = get_status(cycles_path=cycles_path)
        print(f"Total ARSI cycles:    {status['total_cycles']}")
        print(
            f"Days with cycles:     {status['days_with_cycles']} "
            f"| streak={status['current_streak']}"
        )
        print(f"Agents seen:          {', '.join(status['agents_seen']) or 'none'}")
        print(
            f"Probe coverage:       {status['probed_cycles']} verified "
            f"({status['calibrated_cycles']} calibrated)"
        )
        if status["total_cycles"]:
            safe = "arsi-safe" if status["last_arsi_safe"] else "NOT arsi-safe"
            print(
                f"Last cycle:           {status['last_agent']} "
                f"{status['last_date']} {status['last_opstate']} ({safe})"
            )
        return 0

    missing = []
    for field in ("agent", "opstate", "integrity", "scope", "connectivity", "auoe"):
        if getattr(args, field) is None:
            missing.append(f"--{field}")
    if missing:
        print(
            f"ERROR: full cycle requires {', '.join(missing)}",
            file=sys.stderr,
        )
        print("  Use --status to see current summary without recording.", file=sys.stderr)
        parser.print_usage(sys.stderr)
        return 1

    probe = None
    if args.probe_json:
        try:
            probe = _load_probe(Path(args.probe_json))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"ERROR: could not load probe file: {exc}", file=sys.stderr)
            return 1

    ledger_path = Path(args.ledger) if args.ledger else None
    try:
        cycle = record_cycle(
            agent=args.agent,
            opstate=args.opstate,
            integrity=args.integrity,
            scope=args.scope,
            connectivity=args.connectivity,
            auoe=args.auoe,
            budget=args.budget,
            freshness_hours=args.freshness,
            peers=getattr(args, "peers", None),
            probe=probe,
            share_sensitive_notes=args.share_sensitive_notes,
            cycles_path=cycles_path,
            ledger_path=ledger_path,
            force=getattr(args, "force", False),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    safe_str = "ARSI-safe" if cycle["arsi_safe"] else "NOT ARSI-safe"
    verified_str = "verified" if cycle["verified"] else "self-report only (unverified)"
    print(f"Cycle recorded: {cycle['date']} | {cycle['agent']} | {cycle['opstate']} | {safe_str}")
    print(f"Gate avg:       {cycle['gate_avg']:.1f}/5.0 ({verified_str})")
    if cycle.get("calibrated") is not None:
        print(f"Calibrated:     {cycle['calibrated']}")
        for dim, cal in cycle["calibration"].items():
            if cal["delta"]:
                print(f"  {dim}: self={cal['self']} measured={cal['measured']} (delta {cal['delta']:+.4g})")
    if cycle.get("budget") is not None:
        print(f"Budget:         {cycle['budget']}/5")
    if cycle.get("freshness_hours") is not None:
        print(f"Freshness:      {cycle['freshness_hours']}h")
    if cycle.get("peers"):
        print(f"Peers:          {cycle['peers']}")
    print(f"Ledger entry:   {cycle.get('ledger_id', 'n/a')}")
    return 0
