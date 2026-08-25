from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from hummbl_bus.wip_healer import (
    StaleWip,
    classify_wip,
    find_stale_wips,
    heal,
)


def _write_bus(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_find_stale_wips_empty_when_bus_missing(tmp_path: Path) -> None:
    assert find_stale_wips(tmp_path / "nonexistent.tsv") == []


def test_find_stale_wips_finds_unclosed_wip_start(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    old_ts = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{old_ts}\tcodex\tall\tWIP_START\tlane=feature-x"])

    results = find_stale_wips(bus, stale_hours=24.0, now=now)
    assert len(results) == 1
    assert results[0].lane == "feature-x"
    assert results[0].from_id == "codex"


def test_find_stale_wips_skips_closed_wip(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    old_ts = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_ts = (now - timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(
        bus,
        [
            f"{old_ts}\tcodex\tall\tWIP_START\tlane=feature-x",
            f"{end_ts}\tcodex\tall\tWIP_END\tlane=feature-x",
        ],
    )
    assert find_stale_wips(bus, stale_hours=24.0, now=now) == []


def test_find_stale_wips_skips_recent_wip(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    recent_ts = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{recent_ts}\tcodex\tall\tWIP_START\tlane=feature-x"])
    assert find_stale_wips(bus, stale_hours=24.0, now=now) == []


def test_find_stale_wips_tracks_last_activity(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    start_ts = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    activity_ts = (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(
        bus,
        [
            f"{start_ts}\tcodex\tall\tWIP_START\tlane=feature-x",
            f"{activity_ts}\tcodex\tall\tSTATUS\tlane=feature-x making progress",
        ],
    )
    results = find_stale_wips(bus, stale_hours=24.0, now=now)
    assert len(results) == 1
    assert results[0].last_activity is not None


def test_find_stale_wips_blocked_does_not_count_as_activity(tmp_path: Path) -> None:
    """BLOCKED alerts must not count as activity (regression: peptidecheck)."""
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    start_ts = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    blocked_ts = (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(
        bus,
        [
            f"{start_ts}\tcodex\tall\tWIP_START\tlane=feature-x",
            f"{blocked_ts}\tbus-auditor\tall\tBLOCKED\tlane=feature-x stuck",
        ],
    )
    results = find_stale_wips(bus, stale_hours=24.0, now=now)
    assert len(results) == 1
    # last_activity should be None because BLOCKED doesn't count
    assert results[0].last_activity is None


def test_classify_wip_idle(tmp_path: Path) -> None:
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    wip = StaleWip(
        lane="x",
        from_id="codex",
        started_at=now - timedelta(hours=50),
        last_activity=now - timedelta(hours=49),
        line_number=1,
    )
    assert classify_wip(wip, idle_hours=48.0, now=now) == "idle"


def test_classify_wip_stuck(tmp_path: Path) -> None:
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    wip = StaleWip(
        lane="x",
        from_id="codex",
        started_at=now - timedelta(hours=30),
        last_activity=now - timedelta(hours=5),
        line_number=1,
    )
    assert classify_wip(wip, idle_hours=48.0, now=now) == "stuck"


def test_heal_closes_idle_wips(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    start_ts = (now - timedelta(hours=50)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{start_ts}\tcodex\tall\tWIP_START\tlane=feature-x"])

    posted: list[tuple] = []

    def poster(frm, to, mtype, body, bus_path):
        posted.append((frm, to, mtype, body))

    result = heal(bus, stale_hours=24.0, idle_hours=48.0, now=now, poster=poster)
    assert result["closed"] == ["feature-x"]
    assert result["blocked"] == []
    assert len(posted) == 1
    assert posted[0][2] == "WIP_END"
    assert "healed=true" in posted[0][3]


def test_heal_blocks_stuck_wips(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    start_ts = (now - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    activity_ts = (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(
        bus,
        [
            f"{start_ts}\tcodex\tall\tWIP_START\tlane=feature-x",
            f"{activity_ts}\tcodex\tall\tSTATUS\tlane=feature-x progress",
        ],
    )

    posted: list[tuple] = []

    def poster(frm, to, mtype, body, bus_path):
        posted.append((frm, to, mtype, body))

    result = heal(bus, stale_hours=24.0, idle_hours=48.0, now=now, poster=poster)
    assert result["closed"] == []
    assert result["blocked"] == ["feature-x"]
    assert len(posted) == 1
    assert posted[0][2] == "BLOCKED"


def test_heal_without_poster_only_logs(tmp_path: Path) -> None:
    bus = tmp_path / "bus.tsv"
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
    start_ts = (now - timedelta(hours=50)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_bus(bus, [f"{start_ts}\tcodex\tall\tWIP_START\tlane=feature-x"])

    result = heal(bus, stale_hours=24.0, idle_hours=48.0, now=now)
    assert result["closed"] == ["feature-x"]
