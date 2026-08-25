"""Self-healing WIP management — Component 6 of PROPOSAL-012.

Scans the coordination bus for stale ``WIP_START`` entries without matching
``WIP_END``.  For each unclosed lane:

- **Idle** — no lane activity for ``idle_threshold_hours``: auto-post
  ``WIP_END`` with ``healed=true``.
- **Stuck** — lane has recent activity but no progress for
  ``stuck_threshold_hours``: post ``BLOCKED`` alert for operator review.

All thresholds and behavior are configurable via keyword arguments;
the ``heal()`` entry point is designed to be called from a cron job or
scheduled daemon.

Promoted from hummbl-governance/bus/wip_healer.py 2026-08-15. No changes
needed — module is stdlib-only with no hummbl-governance-specific imports.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STALE_HOURS = 24.0
DEFAULT_IDLE_HOURS = 48.0


@dataclass(frozen=True)
class StaleWip:
    """Represents an unclosed WIP_START."""

    lane: str
    from_id: str
    started_at: datetime
    last_activity: datetime | None
    line_number: int


def find_stale_wips(
    bus_path: str | Path,
    *,
    stale_hours: float = DEFAULT_STALE_HOURS,
    now: datetime | None = None,
) -> list[StaleWip]:
    """Scan the bus for unclosed WIP_STARTs older than *stale_hours*.

    Args:
        bus_path: Path to the TSV bus file.
        stale_hours: Age threshold in hours.
        now: Optional reference time (defaults to UTC now).

    Returns:
        List of stale ``StaleWip`` records.
    """
    now = now or datetime.now(UTC)
    cutoff = now.timestamp() - (stale_hours * 3600)

    resolved = Path(bus_path).resolve()
    if not resolved.exists():
        return []

    text = resolved.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Track open WIPs per lane: lane -> (start_ts, from_id, line_number)
    open_wips: dict[str, tuple[str, str, int, datetime]] = {}
    # Track last activity per lane (any non-WIP message with same lane=)
    last_activity: dict[str, datetime] = {}

    for i, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("\t")
        if len(parts) < 5:
            continue
        ts_str = parts[0].strip()
        mtype = parts[3].strip().upper()
        body = parts[4] if len(parts) > 4 else ""

        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        lane_match = re.search(r"\blane=([^;,\s]+)", body)
        lane = lane_match.group(1) if lane_match else ""

        if mtype == "WIP_END":
            if lane:
                open_wips.pop(lane, None)
            # Bulk WIP_END messages list lanes in prose without lane= tags.
            if "bulk wip_end" in body.lower():
                for open_lane in list(open_wips.keys()):
                    if open_lane in body:
                        open_wips.pop(open_lane, None)
            continue

        if not lane:
            continue

        if mtype == "WIP_START":
            open_wips[lane] = (ts_str, parts[1].strip(), i, ts)
        elif mtype == "BLOCKED":
            # BLOCKED alerts describe a lane's stuckness; they are not
            # progress. Counting them as activity creates a feedback loop
            # where bus-auditor BLOCKED alerts every audit cycle keep a
            # lane perpetually classified as "stuck" instead of "idle",
            # preventing auto-heal. (Regression: peptidecheck lanes
            # 2026-06-30..07-04.)
            continue
        else:
            # Any other activity on this lane counts as activity
            if lane not in last_activity or ts > last_activity[lane]:
                last_activity[lane] = ts

    results: list[StaleWip] = []
    for lane, (ts_str, from_id, line_no, start_ts) in open_wips.items():
        start_unix = start_ts.timestamp()
        if start_unix >= cutoff:
            continue  # Not stale yet
        results.append(
            StaleWip(
                lane=lane,
                from_id=from_id,
                started_at=start_ts,
                last_activity=last_activity.get(lane),
                line_number=line_no,
            )
        )

    return results


def classify_wip(
    wip: StaleWip,
    *,
    idle_hours: float = DEFAULT_IDLE_HOURS,
    now: datetime | None = None,
) -> str:
    """Classify a stale WIP as ``idle`` or ``stuck``.

    Args:
        wip: Stale WIP record.
        idle_hours: Hours of no activity to consider idle.
        now: Optional reference time.

    Returns:
        ``"idle"`` or ``"stuck"``.
    """
    now = now or datetime.now(UTC)
    last = wip.last_activity or wip.started_at
    age_hours = (now - last).total_seconds() / 3600.0
    return "idle" if age_hours >= idle_hours else "stuck"


def heal(
    bus_path: str | Path,
    *,
    stale_hours: float = DEFAULT_STALE_HOURS,
    idle_hours: float = DEFAULT_IDLE_HOURS,
    now: datetime | None = None,
    poster: Callable[[str, str, str, str, str | Path], None] | None = None,
) -> dict[str, list[str]]:
    """Run the self-healing WIP loop.

    Args:
        bus_path: Path to the TSV bus file.
        stale_hours: Stale detection threshold.
        idle_hours: Idle classification threshold.
        now: Optional reference time.
        poster: Optional callable ``(from_id, to_id, msg_type, body, bus_path)``
            to post healing messages back to the bus. If ``None``, only logs.

    Returns:
        Dict with ``"closed"`` and ``"blocked"`` keys listing affected lanes.
    """
    now = now or datetime.now(UTC)
    stale = find_stale_wips(bus_path, stale_hours=stale_hours, now=now)
    closed: list[str] = []
    blocked: list[str] = []

    for wip in stale:
        classification = classify_wip(wip, idle_hours=idle_hours, now=now)
        if classification == "idle":
            logger.info(
                "Healing idle WIP: lane=%s from=%s started=%s line=%d",
                wip.lane,
                wip.from_id,
                wip.started_at.isoformat(),
                wip.line_number,
            )
            if poster:
                body = (
                    f"lane={wip.lane} healed=true reason=idle_since_{wip.started_at.isoformat()} "
                    f"source_line={wip.line_number}"
                )
                poster(
                    "wip-healer", wip.from_id or "all", "WIP_END", body, str(bus_path)
                )
            closed.append(wip.lane)
        else:
            logger.warning(
                "Stuck WIP detected: lane=%s from=%s started=%s last_activity=%s line=%d",
                wip.lane,
                wip.from_id,
                wip.started_at.isoformat(),
                wip.last_activity.isoformat() if wip.last_activity else "none",
                wip.line_number,
            )
            if poster:
                body = (
                    f"lane={wip.lane} reason=stuck_since_{wip.started_at.isoformat()} "
                    f"last_activity={wip.last_activity.isoformat() if wip.last_activity else 'none'} "
                    f"source_line={wip.line_number}"
                )
                poster(
                    "wip-healer", wip.from_id or "all", "BLOCKED", body, str(bus_path)
                )
            blocked.append(wip.lane)

    return {"closed": closed, "blocked": blocked}
