"""Bus-Auditor Daemon — Component 7 of PROPOSAL-012.

Scheduled scanner that audits coordination-bus health and posts a SITREP:

- **Format drift** — malformed lines, wrong tab count, unparseable timestamps.
- **Stale WIPs** — delegates to ``wip_healer`` (Component 6).
- **Unreviewed decisions** — PROPOSAL without ACK/DECISION within window.
- **Message type drift** — types not in canonical registry.

The ``run_audit()`` entry point is designed for cron / scheduled-task
invocation.  It returns a structured report and optionally posts a
``SITREP`` back to the bus.

Promoted from hummbl-governance/bus/bus_auditor.py 2026-08-15. Imports updated
from hummbl_governance.bus.* to hummbl_bus.*.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from hummbl_bus.message_types import (
    LEGACY_MESSAGE_TYPES,
    READABLE_MESSAGE_TYPES,
)
from hummbl_bus.wip_healer import heal as wip_heal

logger = logging.getLogger(__name__)

DEFAULT_UNREVIEWED_HOURS = 72.0


@dataclass
class AuditReport:
    """Structured output from a bus audit run."""

    total_lines: int = 0
    valid_rows: int = 0
    malformed_lines: int = 0
    invalid_timestamps: int = 0
    legacy_types: list[str] = field(default_factory=list)
    unknown_types: list[str] = field(default_factory=list)
    stale_wips_closed: list[str] = field(default_factory=list)
    stale_wips_blocked: list[str] = field(default_factory=list)
    unreviewed_proposals: list[dict] = field(default_factory=list)
    passed: bool = True

    def summary(self) -> str:
        parts = [
            f"physical_rows={self.total_lines}",
            f"valid_rows={self.valid_rows}",
            f"malformed={self.malformed_lines}",
            f"bad_ts={self.invalid_timestamps}",
            f"legacy_types={len(self.legacy_types)}",
            f"unknown_types={len(self.unknown_types)}",
            f"stale_wips_closed={len(self.stale_wips_closed)}",
            f"stale_wips_blocked={len(self.stale_wips_blocked)}",
            f"unreviewed_proposals={len(self.unreviewed_proposals)}",
        ]
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class FormatDriftReport:
    """Format and vocabulary counts with explicit denominators."""

    physical_rows: int = 0
    valid_rows: int = 0
    malformed_rows: int = 0
    invalid_timestamps: int = 0
    legacy_types: tuple[str, ...] = ()
    unknown_types: tuple[str, ...] = ()


def _parse_ts(ts_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def scan_format_drift(
    bus_path: str | Path,
) -> tuple[int, int, int, list[str]]:
    """Compatibility wrapper returning physical, malformed, bad-ts, drift types."""
    report = scan_format_drift_details(bus_path)
    return (
        report.physical_rows,
        report.malformed_rows,
        report.invalid_timestamps,
        list(report.unknown_types),
    )


def scan_format_drift_details(bus_path: str | Path) -> FormatDriftReport:
    """Scan bus using valid five-column rows as the vocabulary denominator.

    Physical rows and malformed rows remain visible, but malformed rows never
    enter timestamp or message-type arithmetic.
    """
    resolved = Path(bus_path).resolve()
    if not resolved.exists():
        return FormatDriftReport()

    text = resolved.read_text(encoding="utf-8")
    lines = text.splitlines()
    physical = 0
    valid = 0
    malformed = 0
    bad_ts = 0
    legacy_types: set[str] = set()
    unknown_types: set[str] = set()

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "timestamp\t", "timestamp_utc\t")):
            continue
        physical += 1
        parts = stripped.split("\t")
        if len(parts) != 5:
            malformed += 1
            continue
        valid += 1
        ts_str, _from, _to, mtype, _body = parts
        if _parse_ts(ts_str) is None:
            bad_ts += 1
        normalized_type = mtype.upper()
        if normalized_type in LEGACY_MESSAGE_TYPES:
            legacy_types.add(normalized_type)
        elif normalized_type not in READABLE_MESSAGE_TYPES:
            unknown_types.add(mtype)

    return FormatDriftReport(
        physical_rows=physical,
        valid_rows=valid,
        malformed_rows=malformed,
        invalid_timestamps=bad_ts,
        legacy_types=tuple(sorted(legacy_types)),
        unknown_types=tuple(sorted(unknown_types)),
    )


def scan_unreviewed_proposals(
    bus_path: str | Path,
    *,
    window_hours: float = DEFAULT_UNREVIEWED_HOURS,
    now: datetime | None = None,
) -> list[dict]:
    """Find PROPOSALs without ACK/DECISION/VETO/APPROVE/REJECT within *window_hours*.

    Returns:
        List of dicts with ``lane``, ``from_id``, ``ts``, ``age_hours``.
    """
    now = now or datetime.now(UTC)
    cutoff = now.timestamp() - (window_hours * 3600)

    resolved = Path(bus_path).resolve()
    if not resolved.exists():
        return []

    text = resolved.read_text(encoding="utf-8")
    lines = text.splitlines()

    open_proposals: dict[str, dict] = {}

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("\t")
        if len(parts) != 5:
            continue
        ts_str, frm, _to, mtype, body = parts
        ts = _parse_ts(ts_str)
        if ts is None:
            continue
        if ts.timestamp() < cutoff:
            continue  # Too old to care

        mtype_upper = mtype.strip().upper()
        lane_match = re.search(r"\blane=([^;,\s]+)", body)
        lane = lane_match.group(1) if lane_match else ""

        if mtype_upper == "PROPOSAL":
            open_proposals[lane] = {
                "lane": lane,
                "from_id": frm,
                "ts": ts_str,
                "age_hours": (now - ts).total_seconds() / 3600.0,
            }
        elif mtype_upper in {"ACK", "DECISION", "VETO", "APPROVE", "REJECT"}:
            open_proposals.pop(lane, None)

    return list(open_proposals.values())


def run_audit(
    bus_path: str | Path,
    *,
    stale_hours: float = 24.0,
    idle_hours: float = 48.0,
    unreviewed_hours: float = DEFAULT_UNREVIEWED_HOURS,
    now: datetime | None = None,
    poster: Callable[[str, str, str, str, str | Path], None] | None = None,
) -> AuditReport:
    """Run the full bus audit and return a structured report.

    Args:
        bus_path: Path to the TSV bus file.
        stale_hours: WIP stale threshold.
        idle_hours: WIP idle classification threshold.
        unreviewed_hours: Proposal review window.
        now: Optional reference time.
        poster: Optional callable for posting SITREP back to bus.

    Returns:
        ``AuditReport`` with all findings.
    """
    now = now or datetime.now(UTC)
    report = AuditReport()

    # Format drift scan
    format_report = scan_format_drift_details(bus_path)
    report.total_lines = format_report.physical_rows
    report.valid_rows = format_report.valid_rows
    report.malformed_lines = format_report.malformed_rows
    report.invalid_timestamps = format_report.invalid_timestamps
    report.legacy_types = list(format_report.legacy_types)
    report.unknown_types = list(format_report.unknown_types)

    # Stale WIP healing
    heal_result = wip_heal(
        bus_path,
        stale_hours=stale_hours,
        idle_hours=idle_hours,
        now=now,
        poster=poster,
    )
    report.stale_wips_closed = heal_result["closed"]
    report.stale_wips_blocked = heal_result["blocked"]

    # Unreviewed proposals
    report.unreviewed_proposals = scan_unreviewed_proposals(
        bus_path,
        window_hours=unreviewed_hours,
        now=now,
    )

    # Determine pass/fail
    report.passed = (
        report.malformed_lines == 0
        and report.invalid_timestamps == 0
        and len(report.unknown_types) == 0
        and len(report.stale_wips_blocked) == 0
        and len(report.unreviewed_proposals) == 0
    )

    logger.info("Bus audit complete: %s", report.summary())

    if poster:
        status = "PASS" if report.passed else "FAIL"
        body = (
            f"audit_status={status} {report.summary()} "
            f"unknown_types={','.join(report.unknown_types) or 'none'}"
        )
        poster("bus-auditor", "all", "SITREP", body, str(bus_path))

    return report
