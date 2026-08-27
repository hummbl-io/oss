"""Tests for HRSI Gap 1 belonging baseline CLI (cognition/belonging_check.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hummbl_cognition.belonging_check import (
    COGSTATE_VALUES,
    belonging_score,
    compute_streak,
    fill,
    force_update,
    gap1_progress,
    history,
    is_hrsi_safe,
    run_cli,
    status,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_baseline(tmp_path):
    """Return a temporary baseline JSONL path."""
    return tmp_path / "belonging_baseline.jsonl"


def _write(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# belonging_score
# ---------------------------------------------------------------------------


class TestBelongingScore:
    def test_all_filled(self):
        e = {"safety": 4, "mattering": 3, "connection": 5}
        assert belonging_score(e) == pytest.approx(4.0)

    def test_null_safety(self):
        e = {"safety": None, "mattering": 3, "connection": 5}
        assert belonging_score(e) is None

    def test_missing_field(self):
        e = {"safety": 4, "mattering": 3}
        assert belonging_score(e) is None

    def test_all_ones(self):
        e = {"safety": 1, "mattering": 1, "connection": 1}
        assert belonging_score(e) == pytest.approx(1.0)

    def test_all_fives(self):
        e = {"safety": 5, "mattering": 5, "connection": 5}
        assert belonging_score(e) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# is_hrsi_safe
# ---------------------------------------------------------------------------


class TestIsHrsiSafe:
    def test_safe_entry(self):
        e = {"safety": 3, "mattering": 4, "connection": 5, "cogstate": "AVAILABLE"}
        assert is_hrsi_safe(e) is True

    def test_score_below_threshold(self):
        e = {"safety": 2, "mattering": 4, "connection": 5, "cogstate": "AVAILABLE"}
        assert is_hrsi_safe(e) is False

    def test_wrong_cogstate(self):
        e = {"safety": 4, "mattering": 4, "connection": 4, "cogstate": "HYPERFOCUS"}
        assert is_hrsi_safe(e) is False

    def test_no_cogstate(self):
        e = {"safety": 4, "mattering": 4, "connection": 4, "cogstate": None}
        assert is_hrsi_safe(e) is False

    def test_null_scores(self):
        e = {"safety": None, "mattering": 4, "connection": 4, "cogstate": "AVAILABLE"}
        assert is_hrsi_safe(e) is False

    def test_exactly_threshold(self):
        e = {"safety": 3, "mattering": 3, "connection": 3, "cogstate": "AVAILABLE"}
        assert is_hrsi_safe(e) is True


# ---------------------------------------------------------------------------
# compute_streak
# ---------------------------------------------------------------------------


class TestComputeStreak:
    def test_empty(self):
        assert compute_streak([]) == 0

    def test_all_safe(self):
        entries = [
            {
                "date": "2026-04-10",
                "day": 1,
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },
            {
                "date": "2026-04-11",
                "day": 2,
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },
        ]
        assert compute_streak(entries) == 2

    def test_streak_broken(self):
        entries = [
            {
                "date": "2026-04-10",
                "day": 1,
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },
            {
                "date": "2026-04-11",
                "day": 2,
                "safety": 1,
                "mattering": 1,
                "connection": 1,
                "cogstate": "DEPLETED",
            },
            {
                "date": "2026-04-12",
                "day": 3,
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },
        ]
        assert compute_streak(entries) == 1

    def test_nulls_excluded(self):
        entries = [
            {
                "date": "2026-04-10",
                "day": 1,
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },
            {
                "date": "2026-04-11",
                "day": 2,
                "safety": None,
                "mattering": None,
                "connection": None,
                "cogstate": None,
            },
        ]
        assert compute_streak(entries) == 1  # null excluded, last complete = safe


# ---------------------------------------------------------------------------
# gap1_progress
# ---------------------------------------------------------------------------


class TestGap1Progress:
    def test_empty(self):
        qualifying, total = gap1_progress([])
        assert qualifying == 0
        assert total == 0

    def test_mixed(self):
        entries = [
            {
                "safety": 4,
                "mattering": 4,
                "connection": 4,
                "cogstate": "AVAILABLE",
            },  # score 4.0 ≥ 3
            {
                "safety": 1,
                "mattering": 1,
                "connection": 1,
                "cogstate": "DEPLETED",
            },  # score 1.0 < 3
            {
                "safety": 3,
                "mattering": 3,
                "connection": 3,
                "cogstate": "AVAILABLE",
            },  # score 3.0 ≥ 3
            {"safety": None, "mattering": None, "connection": None},  # excluded
        ]
        qualifying, total = gap1_progress(entries)
        assert qualifying == 2
        assert total == 3

    def test_all_qualifying(self):
        entries = [
            {"safety": 5, "mattering": 5, "connection": 5, "cogstate": "AVAILABLE"}
        ] * 21
        qualifying, total = gap1_progress(entries)
        assert qualifying == 21
        assert total == 21


# ---------------------------------------------------------------------------
# fill
# ---------------------------------------------------------------------------


class TestFill:
    def test_new_entry(self, tmp_baseline):
        entry = fill(4, 3, 5, path=tmp_baseline, today="2026-04-12")
        assert entry["safety"] == 4
        assert entry["mattering"] == 3
        assert entry["connection"] == 5
        assert entry["date"] == "2026-04-12"
        assert entry["day"] == 1
        rows = _read(tmp_baseline)
        assert len(rows) == 1

    def test_fill_scaffolded_null_entry(self, tmp_baseline):
        _write(
            tmp_baseline,
            [
                {
                    "date": "2026-04-12",
                    "day": 1,
                    "safety": None,
                    "mattering": None,
                    "connection": None,
                    "notes": "scaffold",
                    "cogstate": None,
                    "hrsi_cycle_complete": False,
                },
            ],
        )
        entry = fill(
            4, 3, 5, cogstate="AVAILABLE", path=tmp_baseline, today="2026-04-12"
        )
        assert entry["safety"] == 4
        rows = _read(tmp_baseline)
        assert len(rows) == 1  # updated in place, not appended
        assert rows[0]["safety"] == 4

    def test_fill_complete_entry_raises(self, tmp_baseline):
        _write(
            tmp_baseline,
            [
                {
                    "date": "2026-04-12",
                    "day": 1,
                    "safety": 4,
                    "mattering": 3,
                    "connection": 5,
                    "notes": "",
                    "cogstate": None,
                    "hrsi_cycle_complete": False,
                },
            ],
        )
        with pytest.raises(ValueError, match="already has scores"):
            fill(3, 3, 3, path=tmp_baseline, today="2026-04-12")

    def test_invalid_score_raises(self, tmp_baseline):
        with pytest.raises(ValueError):
            fill(6, 3, 3, path=tmp_baseline, today="2026-04-12")
        with pytest.raises(ValueError):
            fill(0, 3, 3, path=tmp_baseline, today="2026-04-12")

    def test_invalid_cogstate_raises(self, tmp_baseline):
        with pytest.raises(ValueError, match="cogstate"):
            fill(4, 3, 5, cogstate="UNICORN", path=tmp_baseline, today="2026-04-12")

    def test_notes_stored(self, tmp_baseline):
        fill(4, 3, 5, notes="great day", path=tmp_baseline, today="2026-04-12")
        rows = _read(tmp_baseline)
        assert rows[0]["notes"] == "great day"

    def test_day_number_increments(self, tmp_baseline):
        fill(4, 3, 5, path=tmp_baseline, today="2026-04-11")
        fill(3, 3, 3, path=tmp_baseline, today="2026-04-12")
        rows = _read(tmp_baseline)
        assert rows[0]["day"] == 1
        assert rows[1]["day"] == 2

    def test_all_valid_cogstates(self, tmp_baseline):
        for i, cog in enumerate(sorted(COGSTATE_VALUES)):
            d = f"2026-04-{i + 1:02d}"
            entry = fill(3, 3, 3, cogstate=cog, path=tmp_baseline, today=d)
            assert entry["cogstate"] == cog

    def test_creates_parent_dir(self, tmp_path):
        p = tmp_path / "deep" / "nested" / "baseline.jsonl"
        fill(3, 3, 3, path=p, today="2026-04-12")
        assert p.exists()


# ---------------------------------------------------------------------------
# force_update
# ---------------------------------------------------------------------------


class TestForceUpdate:
    def test_overwrites_complete_entry(self, tmp_baseline):
        _write(
            tmp_baseline,
            [
                {
                    "date": "2026-04-12",
                    "day": 1,
                    "safety": 4,
                    "mattering": 4,
                    "connection": 4,
                    "notes": "",
                    "cogstate": None,
                    "hrsi_cycle_complete": False,
                },
            ],
        )
        entry = force_update(1, 1, 1, path=tmp_baseline, today="2026-04-12")
        assert entry["safety"] == 1
        rows = _read(tmp_baseline)
        assert len(rows) == 1

    def test_creates_new_if_missing(self, tmp_baseline):
        entry = force_update(3, 3, 3, path=tmp_baseline, today="2026-04-12")
        assert entry["day"] == 1


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_empty(self, tmp_baseline):
        out = status(tmp_baseline)
        assert "No baseline entries" in out

    def test_shows_progress(self, tmp_baseline):
        _write(
            tmp_baseline,
            [
                {
                    "date": "2026-04-11",
                    "day": 1,
                    "safety": 4,
                    "mattering": 4,
                    "connection": 4,
                    "cogstate": "AVAILABLE",
                },
            ],
        )
        out = status(tmp_baseline)
        assert "1/21" in out

    def test_shows_unfilled_today(self, tmp_baseline):
        import datetime

        today = datetime.date.today().isoformat()
        _write(
            tmp_baseline,
            [
                {
                    "date": today,
                    "day": 1,
                    "safety": None,
                    "mattering": None,
                    "connection": None,
                    "notes": "",
                    "cogstate": None,
                    "hrsi_cycle_complete": False,
                },
            ],
        )
        out = status(tmp_baseline)
        assert "UNFILLED" in out


# ---------------------------------------------------------------------------
# history
# ---------------------------------------------------------------------------


class TestHistory:
    def test_empty(self, tmp_baseline):
        out = history(7, tmp_baseline)
        assert "No entries" in out

    def test_shows_n_rows(self, tmp_baseline):
        entries = [
            {
                "date": f"2026-04-{i:02d}",
                "day": i,
                "safety": 3,
                "mattering": 3,
                "connection": 3,
                "cogstate": "AVAILABLE",
            }
            for i in range(1, 11)
        ]
        _write(tmp_baseline, entries)
        out = history(5, tmp_baseline)
        lines = [l for l in out.splitlines() if "2026-04-" in l]
        assert len(lines) == 5

    def test_dash_for_null_scores(self, tmp_baseline):
        _write(
            tmp_baseline,
            [
                {
                    "date": "2026-04-12",
                    "day": 1,
                    "safety": None,
                    "mattering": None,
                    "connection": None,
                    "notes": "",
                    "cogstate": None,
                    "hrsi_cycle_complete": False,
                },
            ],
        )
        out = history(1, tmp_baseline)
        assert "—" in out


# ---------------------------------------------------------------------------
# run_cli
# ---------------------------------------------------------------------------


class TestRunCli:
    def test_status_flag(self, tmp_baseline):
        result = run_cli(["--status", "--path", str(tmp_baseline)])
        assert result == 0

    def test_scores_flag(self, tmp_baseline):
        result = run_cli(
            [
                "--safety",
                "4",
                "--mattering",
                "3",
                "--connection",
                "5",
                "--path",
                str(tmp_baseline),
            ]
        )
        assert result == 0
        rows = _read(tmp_baseline)
        assert rows[0]["safety"] == 4

    def test_scores_with_cogstate(self, tmp_baseline):
        result = run_cli(
            [
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--cogstate",
                "AVAILABLE",
                "--notes",
                "test note",
                "--path",
                str(tmp_baseline),
            ]
        )
        assert result == 0
        rows = _read(tmp_baseline)
        assert rows[0]["cogstate"] == "AVAILABLE"
        assert rows[0]["notes"] == "test note"

    def test_missing_one_score_fails(self, tmp_baseline):
        result = run_cli(
            ["--safety", "4", "--mattering", "3", "--path", str(tmp_baseline)]
        )
        assert result == 1

    def test_history_flag(self, tmp_baseline):
        result = run_cli(["--history", "3", "--path", str(tmp_baseline)])
        assert result == 0

    def test_force_flag_overwrites(self, tmp_baseline):
        run_cli(
            [
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--path",
                str(tmp_baseline),
            ]
        )
        result = run_cli(
            [
                "--safety",
                "1",
                "--mattering",
                "1",
                "--connection",
                "1",
                "--force",
                "--path",
                str(tmp_baseline),
            ]
        )
        assert result == 0
        rows = _read(tmp_baseline)
        assert len(rows) == 1
        assert rows[0]["safety"] == 1

    def test_already_complete_without_force_fails(self, tmp_baseline):
        run_cli(
            [
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--path",
                str(tmp_baseline),
            ]
        )
        result = run_cli(
            [
                "--safety",
                "1",
                "--mattering",
                "1",
                "--connection",
                "1",
                "--path",
                str(tmp_baseline),
            ]
        )
        assert result == 1
