"""
HRSI Gap 1 — Belonging Baseline CLI

Manages the 30-day belonging baseline (3 questions: safety / mattering / connection).
Reduces the daily fill from manual JSONL editing to a single command.

Usage:
    python -m hummbl_cognition belonging-check
    python -m hummbl_cognition belonging-check --safety 4 --mattering 3 --connection 5
    python -m hummbl_cognition belonging-check --safety 4 --mattering 3 --connection 5 --cogstate AVAILABLE --notes "good session"
    python -m hummbl_cognition belonging-check --status
    python -m hummbl_cognition belonging-check --history 7

Scoring guide (1–5 each):
    safety     — Did I feel safe enough to be wrong today?
    mattering  — Did my work or presence matter to someone?
    connection — Did I experience genuine contact with another person?

belonging_score = (safety + mattering + connection) / 3
HRSI-safe day: all three >= 3 AND cogstate == AVAILABLE at some point.
Gap 1 CLOSED: 21/30 days with belonging_score >= 3.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

BASELINE_PATH = Path(__file__).resolve().parents[1] / "_state" / "cognition" / "belonging_baseline.jsonl"
COGNITION_DIR = BASELINE_PATH.parent
COGSTATE_VALUES = {"AVAILABLE", "HYPERFOCUS", "TRANSITION", "RECOVERY", "DEPLETED", "RSD_RISK", "SHUTDOWN"}
SCORE_RANGE = range(1, 6)  # 1–5 inclusive


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load(path: Path = BASELINE_PATH) -> list[dict]:
    """Return all entries from the baseline file, oldest first."""
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _save(entries: list[dict], path: Path = BASELINE_PATH) -> None:
    """Rewrite the baseline file from the full entry list (atomic write)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    tmp.replace(path)


def _today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Domain logic
# ---------------------------------------------------------------------------

def belonging_score(entry: dict) -> Optional[float]:
    s, m, c = entry.get("safety"), entry.get("mattering"), entry.get("connection")
    if None in (s, m, c):
        return None
    return round((s + m + c) / 3, 2)


def is_hrsi_safe(entry: dict) -> bool:
    score = belonging_score(entry)
    if score is None:
        return False
    all_three = all(entry.get(k, 0) >= 3 for k in ("safety", "mattering", "connection"))
    return all_three and entry.get("cogstate") == "AVAILABLE"


def compute_streak(entries: list[dict]) -> int:
    """Consecutive HRSI-safe days counting back from the most recent complete entry."""
    complete = [e for e in entries if belonging_score(e) is not None]
    streak = 0
    for entry in reversed(complete):
        if is_hrsi_safe(entry):
            streak += 1
        else:
            break
    return streak


def gap1_progress(entries: list[dict]) -> tuple[int, int]:
    """Returns (days_meeting_threshold, total_complete_days)."""
    complete = [e for e in entries if belonging_score(e) is not None]
    qualifying = sum(1 for e in complete if (belonging_score(e) or 0) >= 3)
    return qualifying, len(complete)


def _get_entry_for_date(entries: list[dict], d: str) -> Optional[dict]:
    for e in entries:
        if e.get("date") == d:
            return e
    return None


def _next_day_number(entries: list[dict]) -> int:
    """Day number for a new entry (1-indexed)."""
    return len(entries) + 1


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def fill(
    safety: int,
    mattering: int,
    connection: int,
    cogstate: Optional[str] = None,
    notes: str = "",
    today: Optional[str] = None,
    path: Path = BASELINE_PATH,
) -> dict:
    """
    Fill today's scores. If today already has a scaffolded null entry, update it.
    If today is already complete, raise ValueError.
    If today has no entry, append a new one.
    """
    for name, val in [("safety", safety), ("mattering", mattering), ("connection", connection)]:
        if val not in SCORE_RANGE:
            raise ValueError(f"{name} must be 1–5, got {val}")
    if cogstate is not None and cogstate not in COGSTATE_VALUES:
        raise ValueError(f"cogstate must be one of {sorted(COGSTATE_VALUES)}, got {cogstate!r}")

    d = today or _today()
    entries = _load(path)
    existing = _get_entry_for_date(entries, d)

    if existing is not None:
        s, m, c = existing.get("safety"), existing.get("mattering"), existing.get("connection")
        if None not in (s, m, c):
            raise ValueError(
                f"Entry for {d} already has scores (safety={s}, mattering={m}, connection={c}). "
                "Pass --force to overwrite."
            )
        # Update the scaffolded entry
        existing["safety"] = safety
        existing["mattering"] = mattering
        existing["connection"] = connection
        if cogstate is not None:
            existing["cogstate"] = cogstate
        if notes:
            existing["notes"] = notes
        _save(entries, path)
        return existing

    # No entry for today — append
    day_num = _next_day_number(entries)
    entry = {
        "date": d,
        "day": day_num,
        "safety": safety,
        "mattering": mattering,
        "connection": connection,
        "notes": notes,
        "cogstate": cogstate,
        "hrsi_cycle_complete": False,
    }
    entries.append(entry)
    _save(entries, path)
    return entry


def force_update(
    safety: int,
    mattering: int,
    connection: int,
    cogstate: Optional[str] = None,
    notes: str = "",
    today: Optional[str] = None,
    path: Path = BASELINE_PATH,
) -> dict:
    """Overwrite today's entry regardless of existing scores."""
    for name, val in [("safety", safety), ("mattering", mattering), ("connection", connection)]:
        if val not in SCORE_RANGE:
            raise ValueError(f"{name} must be 1–5, got {val}")
    if cogstate is not None and cogstate not in COGSTATE_VALUES:
        raise ValueError(f"cogstate must be one of {sorted(COGSTATE_VALUES)}, got {cogstate!r}")

    d = today or _today()
    entries = _load(path)
    existing = _get_entry_for_date(entries, d)
    if existing is not None:
        existing["safety"] = safety
        existing["mattering"] = mattering
        existing["connection"] = connection
        if cogstate is not None:
            existing["cogstate"] = cogstate
        if notes:
            existing["notes"] = notes
        _save(entries, path)
        return existing

    return fill(safety, mattering, connection, cogstate, notes, today, path)


def status(path: Path = BASELINE_PATH) -> str:
    """Return a formatted status string."""
    entries = _load(path)
    if not entries:
        return "No baseline entries yet. Run: belonging-check --safety N --mattering N --connection N"

    today_entry = _get_entry_for_date(entries, _today())
    qualifying, total = gap1_progress(entries)
    streak = compute_streak(entries)
    days_remaining = max(0, 21 - qualifying)

    lines = [
        "HRSI Gap 1 — Belonging Baseline",
        f"  Progress : {qualifying}/21 qualifying days ({total} total entries)",
        f"  Streak   : {streak} consecutive HRSI-safe days",
        f"  Remaining: {days_remaining} qualifying days needed to close Gap 1",
        "",
    ]

    if today_entry:
        score = belonging_score(today_entry)
        if score is None:
            lines.append(f"  Today (Day {today_entry['day']}): UNFILLED — run belonging-check to log scores")
        else:
            safe_marker = " ✓ HRSI-safe" if is_hrsi_safe(today_entry) else ""
            lines.append(
                f"  Today (Day {today_entry['day']}): score={score:.1f}"
                f"  [S={today_entry['safety']} M={today_entry['mattering']} C={today_entry['connection']}]"
                f"  cogstate={today_entry.get('cogstate') or 'unset'}{safe_marker}"
            )
    else:
        lines.append(f"  Today: no entry yet (day {_next_day_number(entries)})")

    return "\n".join(lines)


def history(n: int = 7, path: Path = BASELINE_PATH) -> str:
    """Return the last N entries as a formatted table."""
    entries = _load(path)
    recent = entries[-n:]
    if not recent:
        return "No entries."

    lines = [f"{'Date':<12} {'Day':>4} {'S':>3} {'M':>3} {'C':>3} {'Score':>6} {'State':<12} {'Safe':>5}"]
    lines.append("-" * 55)
    for e in recent:
        score = belonging_score(e)
        score_str = f"{score:.1f}" if score is not None else "  —  "
        s = str(e.get("safety") or "—")
        m = str(e.get("mattering") or "—")
        c = str(e.get("connection") or "—")
        cog = (e.get("cogstate") or "—")[:10]
        safe_str = "  ✓" if is_hrsi_safe(e) else "   "
        lines.append(f"{e['date']:<12} {e['day']:>4} {s:>3} {m:>3} {c:>3} {score_str:>6} {cog:<12} {safe_str:>5}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interactive prompt
# ---------------------------------------------------------------------------

def _prompt_score(question: str, label: str) -> int:
    while True:
        try:
            val = int(input(f"  {label} — {question} [1-5]: ").strip())
            if val in SCORE_RANGE:
                return val
            print("    Enter a number between 1 and 5.")
        except (ValueError, EOFError):
            print("    Invalid input.")


def interactive_fill(path: Path = BASELINE_PATH) -> dict:
    """Walk the user through the 3 questions interactively."""
    entries = _load(path)
    d = _today()
    existing = _get_entry_for_date(entries, d)
    day_num = existing["day"] if existing else _next_day_number(entries)

    print(f"\nHRSI Belonging Check — Day {day_num} ({d})")
    print("Score each 1 (no) → 5 (fully yes)\n")

    safety = _prompt_score("Did I feel safe enough to be wrong today?", "Safety    ")
    mattering = _prompt_score("Did my work or presence matter to someone?", "Mattering ")
    connection = _prompt_score("Did I experience genuine contact with another person?", "Connection")

    cog_input = input("\n  Cogstate (AVAILABLE/HYPERFOCUS/TRANSITION/RECOVERY/DEPLETED/RSD_RISK/SHUTDOWN, or blank): ").strip().upper()
    cogstate = cog_input if cog_input in COGSTATE_VALUES else None

    notes = input("  Notes (optional, blank to skip): ").strip()

    entry = fill(safety, mattering, connection, cogstate, notes or "", path=path)
    score = belonging_score(entry)
    print(f"\n  Logged: score={score:.1f} [S={safety} M={mattering} C={connection}] cogstate={cogstate or 'unset'}")
    return entry


# ---------------------------------------------------------------------------
# CLI entry point (called from cognition/__main__.py)
# ---------------------------------------------------------------------------

def run_cli(args: list[str]) -> int:
    """Parse args and execute. Returns exit code."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="belonging-check",
        description="HRSI Gap 1 — daily belonging baseline (safety / mattering / connection)",
    )
    parser.add_argument("--safety", type=int, choices=list(SCORE_RANGE), help="Safety score 1–5")
    parser.add_argument("--mattering", type=int, choices=list(SCORE_RANGE), help="Mattering score 1–5")
    parser.add_argument("--connection", type=int, choices=list(SCORE_RANGE), help="Connection score 1–5")
    parser.add_argument("--cogstate", choices=sorted(COGSTATE_VALUES), help="Cogstate at time of logging")
    parser.add_argument("--notes", default="", help="Optional free-text notes")
    parser.add_argument("--status", action="store_true", help="Show progress and today's entry")
    parser.add_argument("--history", type=int, metavar="N", nargs="?", const=7, help="Show last N entries (default 7)")
    parser.add_argument("--force", action="store_true", help="Overwrite today's scores even if already filled")
    parser.add_argument("--path", default=str(BASELINE_PATH), help="Override baseline file path")

    parsed = parser.parse_args(args)
    path = Path(parsed.path)

    if parsed.status:
        print(status(path))
        return 0

    if parsed.history is not None:
        print(history(parsed.history, path))
        return 0

    scores_provided = parsed.safety is not None or parsed.mattering is not None or parsed.connection is not None
    if scores_provided:
        missing = [k for k in ("safety", "mattering", "connection") if getattr(parsed, k) is None]
        if missing:
            print(f"Error: must provide all three scores. Missing: {', '.join(missing)}", file=sys.stderr)
            return 1
        try:
            fn = force_update if parsed.force else fill
            entry = fn(
                parsed.safety, parsed.mattering, parsed.connection,
                cogstate=parsed.cogstate, notes=parsed.notes, path=path,
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        score = belonging_score(entry)
        safe_tag = " [HRSI-safe ✓]" if is_hrsi_safe(entry) else ""
        print(f"Logged Day {entry['day']} ({entry['date']}): score={score:.1f} [S={entry['safety']} M={entry['mattering']} C={entry['connection']}] cogstate={entry.get('cogstate') or 'unset'}{safe_tag}")
        return 0

    # No args — interactive
    try:
        interactive_fill(path)
    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    return 0
