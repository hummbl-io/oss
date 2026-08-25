"""HRSI Gap 2 — Unified daily check-in CLI.

Records one HRSI measurement cycle in a single command. Cogstate,
belonging, and HULE are required; lens and delta are optional enrichment:

    1. Cogstate log  — what state, what modes accessible  (K + C)
    2. Belonging check — safety / mattering / connection   (D substrate)
    3. Lens applied  — which ARCANA/PRAXIS model, to what
    4. HULE entry    — the human-unique lived-experience note
    5. Delta noted   — did K, C, or D measurably shift?

One cycle = the three required components present in a 24-hour window.
21 qualifying days in a 30-day baseline window = Gap 1 closed.
Existence of this command = Gap 2 closed.

Usage:
    python -m hummbl_cognition hrsi-checkin \\
        --cogstate AVAILABLE \\
        --safety 4 --mattering 3 --connection 5 \\
        --hule "Noticed pattern between X and Y that no agent could surface" \\
        --lens "bki" \\
        --delta "K+: new integration of Prop 3; D: high voluntary return"

    python -m hummbl_cognition hrsi-checkin --status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from hummbl_cognition.belonging_check import (
    COGSTATE_VALUES,
    SCORE_RANGE,
    compute_streak,
    gap1_progress,
)
from hummbl_cognition.belonging_check import (
    _load as _load_baseline,
)
from hummbl_cognition.belonging_check import (
    fill as belonging_fill,
)
from hummbl_cognition.belonging_check import (
    force_update as belonging_force_update,
)
from hummbl_cognition.ledger_writer import _lock_file, _unlock_file, post_entry
from hummbl_cognition.models import LedgerEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AGENT = "reuben"
_VENDOR = "human"
_MODEL = "homo-temporalis-v0"
_TYPE = "convention"
_SCOPE = "convention"
_BASE_TAGS = ("hrsi-cycle", "hrsi-gap2")


def resolve_cognition_dir() -> Path:
    """Resolve the shared HRSI state directory.

    HRSI_COGNITION_DIR is the only supported override. Otherwise state lives
    at the repository root so skills and CLI processes observe the same files.
    """
    explicit = os.environ.get("HRSI_COGNITION_DIR", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "_state" / "cognition"


COGNITION_DIR = resolve_cognition_dir()
BASELINE_PATH = COGNITION_DIR / "belonging_baseline.jsonl"
CYCLES_PATH = COGNITION_DIR / "hrsi_cycles.jsonl"
LEDGER_PATH = COGNITION_DIR / "ledger.jsonl"
LOCK_PATH = COGNITION_DIR / ".hrsi-checkin.lock"


# ---------------------------------------------------------------------------
# Cycle I/O
# ---------------------------------------------------------------------------

def _load_cycles(path: Path = CYCLES_PATH) -> list[dict]:
    if not path.exists():
        return []
    cycles = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cycles.append(json.loads(line))
    return cycles


def _append_cycle(cycle: dict, path: Path = CYCLES_PATH, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if force:
        existing = []
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            if entry.get("date") != cycle.get("date"):
                                existing.append(line)
                        except json.JSONDecodeError:
                            existing.append(line)
        with open(path, "w", encoding="utf-8") as f:
            for line in existing:
                f.write(line + "\n")
            f.write(json.dumps(cycle, ensure_ascii=False) + "\n")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(cycle, ensure_ascii=False) + "\n")


@contextmanager
def _cycle_transaction_lock(path: Path = LOCK_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+", encoding="utf-8") as lock_file:
        _lock_file(lock_file)
        try:
            yield
        finally:
            _unlock_file(lock_file)


def _snapshot(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def _restore(path: Path, content: bytes | None) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    rollback = path.with_name(f".{path.name}.hrsi-rollback.tmp")
    rollback.write_bytes(content)
    rollback.replace(path)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def record_cycle(
    cogstate: str,
    safety: int,
    mattering: int,
    connection: int,
    hule: str,
    lens: Optional[str] = None,
    delta: Optional[str] = None,
    energy: Optional[int] = None,
    sleep_hours: Optional[float] = None,
    relational_note: Optional[str] = None,
    share_sensitive_notes: bool = False,
    today: Optional[str] = None,
    baseline_path: Optional[Path] = None,
    cycles_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    force: bool = False,
) -> dict:
    """Record one complete HRSI measurement cycle.

    Writes to:
    - belonging_baseline.jsonl (steps 1+2 via belonging_fill)
    - hrsi_cycles.jsonl (full cycle record)
    - CLP ledger (HULE entry + cycle summary)

    Returns the cycle dict.
    """
    if baseline_path is None:
        baseline_path = BASELINE_PATH
    if cycles_path is None:
        cycles_path = CYCLES_PATH
    if cogstate not in COGSTATE_VALUES:
        raise ValueError(f"cogstate must be one of {sorted(COGSTATE_VALUES)}, got {cogstate!r}")
    for name, val in [("safety", safety), ("mattering", mattering), ("connection", connection)]:
        if val not in SCORE_RANGE:
            raise ValueError(f"{name} must be 1–5, got {val}")
    if not hule or not hule.strip():
        raise ValueError("--hule is required: record what only you could observe today")
    if energy is not None and energy not in SCORE_RANGE:
        raise ValueError(f"energy must be 1–5, got {energy}")
    if sleep_hours is not None and not (0 <= sleep_hours <= 24):
        raise ValueError(f"sleep_hours must be 0–24, got {sleep_hours}")

    d = today or date.today().isoformat()
    ts = datetime.now(timezone.utc).isoformat()

    # Build cycle record
    belonging_avg = round((safety + mattering + connection) / 3, 2)
    hrsi_safe = cogstate == "AVAILABLE" and all(v >= 3 for v in (safety, mattering, connection))

    cycle: dict = {
        "date": d,
        "timestamp": ts,
        "cogstate": cogstate,
        "safety": safety,
        "mattering": mattering,
        "connection": connection,
        "belonging_avg": belonging_avg,
        "hrsi_safe": hrsi_safe,
        "hule": hule.strip(),
    }
    if lens:
        cycle["lens"] = lens.strip()
    if delta:
        cycle["delta"] = delta.strip()
    if energy is not None:
        cycle["energy"] = energy
    if sleep_hours is not None:
        cycle["sleep_hours"] = sleep_hours
    if relational_note:
        cycle["relational_note"] = relational_note.strip()

    # Step 3+4+5: CLP ledger — HULE entry
    tags = list(_BASE_TAGS)
    if lens:
        tags.append(f"lens-{lens.strip().lower().replace(' ', '-')}")
    if hrsi_safe:
        tags.append("hrsi-safe")

    content_parts = [f"HRSI cycle {d}: cogstate={cogstate}"]
    content_parts.append(
        f"belonging={belonging_avg:.1f} (s={safety}/m={mattering}/c={connection})"
    )
    hule_value = hule.strip()
    hule_hash = hashlib.sha256(hule_value.encode("utf-8")).hexdigest()
    if share_sensitive_notes:
        content_parts.append(f"HULE: {hule_value}")
    else:
        content_parts.append(f"HULE recorded locally; hule_sha256={hule_hash}")
    if lens:
        content_parts.append(f"lens: {lens.strip()}")
    if delta:
        content_parts.append(f"delta: {delta.strip()}")
    if energy is not None:
        content_parts.append(f"energy: {energy}/5")
    if sleep_hours is not None:
        content_parts.append(f"sleep: {sleep_hours}h")
    if relational_note:
        relational_value = relational_note.strip()
        if share_sensitive_notes:
            content_parts.append(f"relational: {relational_value}")
        else:
            relational_hash = hashlib.sha256(relational_value.encode("utf-8")).hexdigest()
            content_parts.append(f"relational note recorded locally; relational_sha256={relational_hash}")

    content = " | ".join(content_parts)
    if len(content) > 4096:
        content = content[:4096]

    entry = LedgerEntry.create(
        agent=_AGENT,
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
    transaction_lock = cycles_path.parent / ".hrsi-checkin.lock"
    with _cycle_transaction_lock(transaction_lock):
        baseline_before = _snapshot(baseline_path)
        cycles_before = _snapshot(cycles_path)
        ledger_before = _snapshot(effective_ledger_path)
        try:
            _belonging_fn = belonging_force_update if force else belonging_fill
            _belonging_fn(
                safety=safety,
                mattering=mattering,
                connection=connection,
                cogstate=cogstate,
                notes=delta or "",
                today=d,
                path=baseline_path,
            )
            _append_cycle(cycle, cycles_path, force=force)
            post_entry(entry, ledger_path=effective_ledger_path)
        except Exception:
            _restore(baseline_path, baseline_before)
            _restore(cycles_path, cycles_before)
            _restore(effective_ledger_path, ledger_before)
            raise

    return cycle


def get_status(
    baseline_path: Optional[Path] = None,
    cycles_path: Optional[Path] = None,
) -> dict:
    """Return current HRSI Gap 2 status summary."""
    if baseline_path is None:
        baseline_path = BASELINE_PATH
    if cycles_path is None:
        cycles_path = CYCLES_PATH
    baseline = _load_baseline(baseline_path)
    cycles = _load_cycles(cycles_path)
    qualifying, total = gap1_progress(baseline)
    streak = compute_streak(baseline)
    return {
        "gap1_qualifying_days": qualifying,
        "gap1_total_days": total,
        "gap1_closed": qualifying >= 21,
        "current_streak": streak,
        "total_cycles": len(cycles),
        "gap2_closed": len(cycles) > 0,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition hrsi-checkin",
        description="HRSI Gap 2 — unified daily cycle check-in (5 components)",
    )
    parser.add_argument(
        "--cogstate",
        choices=sorted(COGSTATE_VALUES),
        help="Current cognitive state",
    )
    parser.add_argument("--safety", type=int, choices=range(1, 6), metavar="1-5")
    parser.add_argument("--mattering", type=int, choices=range(1, 6), metavar="1-5")
    parser.add_argument("--connection", type=int, choices=range(1, 6), metavar="1-5")
    parser.add_argument(
        "--hule",
        help="Human Unique Lived Experience entry (required for full cycle)",
    )
    parser.add_argument("--lens", help="ARCANA/PRAXIS lens applied today (e.g. 'bki', 'girard')")
    parser.add_argument("--delta", help="K/C/D shift description")
    parser.add_argument("--energy", type=int, choices=range(1, 6), metavar="1-5",
                        help="Somatic energy level (1=depleted, 5=thriving)")
    parser.add_argument("--sleep", type=float, metavar="HOURS",
                        help="Hours of sleep last night (0-24)")
    parser.add_argument("--relational-note",
                        help="Who you connected with today (free text, optional)")
    parser.add_argument(
        "--share-sensitive-notes",
        action="store_true",
        help="Opt in to copying raw HULE and relational text into the shared CLP ledger",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current HRSI Gap progress without recording",
    )
    parser.add_argument("--ledger", help="Override ledger path")
    parser.add_argument("--baseline", help="Override belonging baseline path (for testing)")
    parser.add_argument("--cycles", help="Override hrsi_cycles path (for testing)")
    parser.add_argument(
        "--bridge",
        help="Post to HRSI bridge at this base URL instead of writing locally. "
             "Overrides HRSI_CANONICAL_BRIDGE_URL env.",
    )
    parser.add_argument(
        "--origin-machine",
        help="Origin machine tag for bridge writes (auto-detected if omitted)",
    )
    parser.add_argument(
        "--local-fallback",
        action="store_true",
        default=True,
        help="If bridge write fails, write locally instead of erroring (default: on)",
    )
    parser.add_argument(
        "--no-local-fallback",
        action="store_false",
        dest="local_fallback",
        help="If bridge write fails, error instead of writing locally",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite today's entry if it already exists",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    baseline_path = Path(args.baseline) if getattr(args, "baseline", None) else BASELINE_PATH
    cycles_path = Path(args.cycles) if getattr(args, "cycles", None) else CYCLES_PATH

    if args.status:
        status = get_status(baseline_path=baseline_path, cycles_path=cycles_path)
        gap1_pct = (
            f"{status['gap1_qualifying_days']}/21 qualifying-day target "
            f"across {status['gap1_total_days']} logged day(s) "
            f"({'CLOSED' if status['gap1_closed'] else 'open'})"
        )
        print(f"Gap 1 (belonging baseline): {gap1_pct}")
        print(f"Gap 2 (hrsi-checkin):        {'CLOSED' if status['gap2_closed'] else 'OPEN'}")
        print(f"Total HRSI cycles logged:    {status['total_cycles']}")
        print(f"Current streak:              {status['current_streak']} day(s)")
        return 0

    # Full cycle — all core fields required
    missing = []
    for field in ("cogstate", "safety", "mattering", "connection", "hule"):
        if getattr(args, field) is None:
            missing.append(f"--{field}")
    if missing:
        print(
            f"ERROR: full cycle requires {', '.join(missing)}",
            file=sys.stderr,
        )
        print(
            "  Use --status to see current progress without recording.",
            file=sys.stderr,
        )
        parser.print_usage(sys.stderr)
        return 1

    ledger_path = Path(args.ledger) if args.ledger else None

    # Bridge mode: post to remote bridge instead of writing locally
    bridge_url = getattr(args, "bridge", None) or os.environ.get("HRSI_CANONICAL_BRIDGE_URL", "")
    if bridge_url:
        from hummbl_cognition.hrsi_bridge_client import post_hrsi_to_bridge_url_result

        origin = getattr(args, "origin_machine", None) or socket.gethostname().split(".")[0]
        result = post_hrsi_to_bridge_url_result(
            bridge_url,
            cogstate=args.cogstate,
            safety=args.safety,
            mattering=args.mattering,
            connection=args.connection,
            hule=args.hule,
            lens=args.lens,
            delta=args.delta,
            energy=args.energy,
            sleep_hours=args.sleep,
            relational_note=getattr(args, "relational_note", None),
            origin_machine=origin,
            force=getattr(args, "force", False),
        )
        if result["ok"]:
            body = result.get("body", {})
            cycle = body.get("cycle", {})
            status_body = body.get("status", {})
            hrsi_safe_str = "HRSI-safe" if cycle.get("hrsi_safe") else "not HRSI-safe"
            print(f"Cycle recorded via bridge: {cycle.get('date', '?')} | {cycle.get('cogstate', '?')} | {hrsi_safe_str}")
            print(f"Belonging avg:  {cycle.get('belonging_avg', 0):.1f}/5.0")
            if cycle.get("energy"):
                print(f"Energy:         {cycle['energy']}/5")
            if cycle.get("sleep_hours") is not None:
                print(f"Sleep:          {cycle['sleep_hours']}h")
            if cycle.get("relational_note"):
                print(f"Relational:     {cycle['relational_note']}")
            print(f"Bridge status:  gap1={status_body.get('gap1_qualifying_days', '?')}/30 cycles={status_body.get('total_cycles', '?')}")
            return 0

        # Bridge failed
        if result.get("permanent_error") or not getattr(args, "local_fallback", True):
            print(
                f"ERROR: bridge write failed (status={result['status_code']}) "
                f"and {'permanent error' if result.get('permanent_error') else 'no local fallback'}",
                file=sys.stderr,
            )
            return 1

        print(
            f"WARNING: bridge write failed (status={result['status_code']}), "
            f"falling back to local write",
            file=sys.stderr,
        )
        # Fall through to local record_cycle below

    try:
        cycle = record_cycle(
            cogstate=args.cogstate,
            safety=args.safety,
            mattering=args.mattering,
            connection=args.connection,
            hule=args.hule,
            lens=args.lens,
            delta=args.delta,
            energy=args.energy,
            sleep_hours=args.sleep,
            relational_note=getattr(args, "relational_note", None),
            share_sensitive_notes=args.share_sensitive_notes,
            baseline_path=baseline_path,
            cycles_path=cycles_path,
            ledger_path=ledger_path,
            force=getattr(args, "force", False),
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    hrsi_safe_str = "HRSI-safe" if cycle["hrsi_safe"] else "not HRSI-safe"
    print(f"Cycle recorded: {cycle['date']} | {cycle['cogstate']} | {hrsi_safe_str}")
    print(f"Belonging avg:  {cycle['belonging_avg']:.1f}/5.0")
    if cycle.get("lens"):
        print(f"Lens:           {cycle['lens']}")
    if cycle.get("delta"):
        print(f"Delta:          {cycle['delta']}")
    if cycle.get("energy"):
        print(f"Energy:         {cycle['energy']}/5")
    if cycle.get("sleep_hours") is not None:
        print(f"Sleep:          {cycle['sleep_hours']}h")
    if cycle.get("relational_note"):
        print(f"Relational:     {cycle['relational_note']}")
    print(f"Ledger entry:   {cycle.get('ledger_id', 'n/a')}")

    # Show updated gap status
    status = get_status(baseline_path=baseline_path, cycles_path=cycles_path)
    print(
        f"\nGap 1 progress: {status['gap1_qualifying_days']}/21 qualifying-day target "
        f"across {status['gap1_total_days']} logged day(s) "
        f"| streak={status['current_streak']}"
    )
    print(f"Gap 2:          {status['total_cycles']} cycle(s) logged | CLOSED")
    return 0
