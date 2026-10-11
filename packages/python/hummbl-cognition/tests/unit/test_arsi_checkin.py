"""Tests for cognition/arsi_checkin.py — agent self-check-in."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_cognition.arsi_checkin import (
    OPSTATE_VALUES,
    _compute_calibration,
    _is_calibrated,
    _load_probe,
    get_status,
    record_cycle,
    run_cli,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_paths(tmp_path: Path):
    """Returns (cycles_path, ledger_path, lock_path) all in tmp_path."""
    return (
        tmp_path / "arsi_cycles.jsonl",
        tmp_path / "ledger.jsonl",
        tmp_path / ".arsi-checkin.lock",
    )


def _record(tmp_paths, **kw):
    cycles, ledger, lock = tmp_paths
    return record_cycle(
        cycles_path=cycles,
        ledger_path=ledger,
        lock_path=lock,
        **kw,
    )


BASE = dict(
    agent="test-agent",
    opstate="AVAILABLE",
    integrity=4,
    scope=4,
    connectivity=5,
    auoe="Observed drift only this agent could see",
)


# ---------------------------------------------------------------------------
# record_cycle — file + computed fields
# ---------------------------------------------------------------------------


class TestRecordCycle:
    def test_writes_cycle_file(self, tmp_paths):
        cycles, _, _ = tmp_paths
        _record(tmp_paths, **BASE)
        assert cycles.exists()
        lines = [
            json.loads(line)
            for line in cycles.read_text().splitlines()
            if line.strip()
        ]
        assert len(lines) == 1
        assert lines[0]["agent"] == "test-agent"
        assert lines[0]["opstate"] == "AVAILABLE"

    def test_gate_avg_computed(self, tmp_paths):
        cycle = _record(tmp_paths, **BASE)
        assert cycle["gate_avg"] == 4.33

    def test_arsi_safe_when_available_and_all_gte_3(self, tmp_paths):
        cycle = _record(tmp_paths, **{**BASE, "integrity": 3, "scope": 3, "connectivity": 3})
        assert cycle["arsi_safe"] is True

    def test_not_arsi_safe_when_not_available(self, tmp_paths):
        cycle = _record(tmp_paths, **{**BASE, "opstate": "DEGRADED"})
        assert cycle["arsi_safe"] is False

    def test_not_arsi_safe_when_dim_below_3(self, tmp_paths):
        cycle = _record(tmp_paths, **{**BASE, "connectivity": 2})
        assert cycle["arsi_safe"] is False

    def test_unverified_without_probe(self, tmp_paths):
        cycle = _record(tmp_paths, **BASE)
        assert cycle["verified"] is False
        assert "calibrated" not in cycle

    def test_ledger_entry_written(self, tmp_paths):
        _, ledger, _ = tmp_paths
        cycle = _record(tmp_paths, **BASE)
        assert ledger.exists()
        entries = [
            json.loads(line)
            for line in ledger.read_text().splitlines()
            if line.strip()
        ]
        assert len(entries) == 1
        assert "arsi-cycle" in entries[0]["tags"]
        assert cycle["ledger_id"] == entries[0]["id"]
        # AUOE hashed by default, not raw
        assert "Observed drift" not in entries[0]["content"]
        assert "auoe_sha256" in entries[0]["content"]

    def test_share_sensitive_notes_writes_raw(self, tmp_paths):
        _, ledger, _ = tmp_paths
        _record(tmp_paths, **BASE, share_sensitive_notes=True)
        entries = [
            json.loads(line)
            for line in ledger.read_text().splitlines()
            if line.strip()
        ]
        assert "Observed drift" in entries[0]["content"]


# ---------------------------------------------------------------------------
# Probe layer — calibration + gate dominance
# ---------------------------------------------------------------------------


class TestProbeLayer:
    def test_calibration_deltas_computed(self, tmp_paths):
        probe = {"integrity": 5, "scope": 4, "connectivity": 5}
        cycle = _record(tmp_paths, **BASE, probe=probe)
        assert cycle["verified"] is True
        assert cycle["calibration"]["integrity"] == {
            "self": 4,
            "measured": 5,
            "delta": -1.0,
        }
        assert cycle["calibrated"] is True

    def test_probe_dominates_gate_when_measured_low(self, tmp_paths):
        # Self-report says 5, measurement says 2 — probe wins, not safe.
        probe = {"integrity": 2, "scope": 4, "connectivity": 5}
        cycle = _record(
            tmp_paths,
            **{**BASE, "integrity": 5},
            probe=probe,
        )
        assert cycle["arsi_safe"] is False

    def test_uncalibrated_fails_gate_even_when_measured_high(self, tmp_paths):
        # Over-reporting AND under-reporting both break calibration.
        probe = {"integrity": 5}  # self=3 → delta -2 > tolerance
        cycle = _record(
            tmp_paths,
            **{**BASE, "integrity": 3},
            probe=probe,
        )
        assert cycle["calibrated"] is False
        assert cycle["arsi_safe"] is False

    def test_calibration_tolerance_boundary(self, tmp_paths):
        cal = {"d": {"self": 4, "measured": 5, "delta": -1}}
        assert _is_calibrated(cal)
        cal = {"d": {"self": 3, "measured": 5, "delta": -2}}
        assert not _is_calibrated(cal)

    def test_compute_calibration_skips_unprobed_dims(self):
        cal = _compute_calibration(
            {"integrity": 4, "scope": 4, "connectivity": 5},
            {"integrity": 4},
        )
        assert list(cal.keys()) == ["integrity"]


# ---------------------------------------------------------------------------
# Multi-agent dedup + force
# ---------------------------------------------------------------------------


class TestForceAndDedup:
    def test_multiple_agents_same_date(self, tmp_paths):
        cycles, _, _ = tmp_paths
        _record(tmp_paths, **BASE)
        _record(tmp_paths, **{**BASE, "agent": "other-agent"})
        lines = cycles.read_text().splitlines()
        assert len(lines) == 2

    def test_force_overwrites_same_agent_only(self, tmp_paths):
        cycles, _, _ = tmp_paths
        _record(tmp_paths, **BASE)
        _record(tmp_paths, **{**BASE, "agent": "other-agent"})
        _record(tmp_paths, **{**BASE, "connectivity": 3}, force=True)
        lines = [
            json.loads(line)
            for line in cycles.read_text().splitlines()
            if line.strip()
        ]
        assert len(lines) == 2
        by_agent = {line["agent"]: line for line in lines}
        assert by_agent["test-agent"]["connectivity"] == 3
        assert by_agent["other-agent"]["connectivity"] == 5


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    @pytest.mark.parametrize(
        "kw",
        [
            {"agent": ""},
            {"opstate": "BOGUS"},
            {"integrity": 9},
            {"scope": 0},
            {"connectivity": 6},
            {"auoe": "   "},
            {"budget": 7},
            {"freshness_hours": -1},
        ],
    )
    def test_rejects_bad_input(self, tmp_paths, kw):
        with pytest.raises(ValueError):
            _record(tmp_paths, **{**BASE, **kw})

    def test_opstate_values_complete(self):
        assert OPSTATE_VALUES == {
            "AVAILABLE",
            "EXECUTING",
            "DEGRADED",
            "QUOTA_BOUND",
            "CONTEXT_STALE",
            "ISOLATED",
            "QUARANTINED",
            "TRANSITION",
        }


# ---------------------------------------------------------------------------
# Probe file loading
# ---------------------------------------------------------------------------


class TestProbeFile:
    def test_load_probe_filters_known_dims(self, tmp_path):
        p = tmp_path / "probe.json"
        p.write_text(json.dumps({"integrity": 3, "unknown_dim": 99}))
        probe = _load_probe(p)
        assert probe == {"integrity": 3}

    def test_load_probe_rejects_non_object(self, tmp_path):
        p = tmp_path / "probe.json"
        p.write_text("[1, 2]")
        with pytest.raises(ValueError):
            _load_probe(p)


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_empty_status(self, tmp_paths):
        status = get_status(cycles_path=tmp_paths[0])
        assert status["total_cycles"] == 0
        assert status["agents_seen"] == []

    def test_status_counts(self, tmp_paths):
        _record(tmp_paths, **BASE)
        _record(tmp_paths, **{**BASE, "agent": "b"}, probe={"integrity": 4})
        status = get_status(cycles_path=tmp_paths[0])
        assert status["total_cycles"] == 2
        assert status["agents_seen"] == ["b", "test-agent"]
        assert status["probed_cycles"] == 1
        assert status["calibrated_cycles"] == 1
        assert status["last_agent"] == "b"


# ---------------------------------------------------------------------------
# run_cli
# ---------------------------------------------------------------------------


class TestRunCli:
    def _args(self, tmp_path, *extra):
        cycles = tmp_path / "arsi_cycles.jsonl"
        ledger = tmp_path / "ledger.jsonl"
        return [
            "--cycles", str(cycles),
            "--ledger", str(ledger),
            *extra,
        ]

    def test_full_cycle_via_cli(self, tmp_path, capsys):
        rc = run_cli(
            self._args(
                tmp_path,
                "--agent", "cli-agent",
                "--opstate", "AVAILABLE",
                "--integrity", "4", "--scope", "4", "--connectivity", "5",
                "--auoe", "CLI observation",
                "--budget", "3",
                "--freshness", "2.5",
                "--peers", "codex,devin",
            )
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "ARSI-safe" in out
        assert "unverified" in out
        assert "cli-agent" in out

    def test_missing_fields_error(self, tmp_path, capsys):
        rc = run_cli(self._args(tmp_path, "--agent", "x"))
        assert rc == 1
        assert "ERROR" in capsys.readouterr().err

    def test_status_via_cli(self, tmp_path, capsys):
        rc = run_cli(self._args(tmp_path, "--status"))
        assert rc == 0
        assert "Total ARSI cycles" in capsys.readouterr().out

    def test_bad_probe_file_errors(self, tmp_path, capsys):
        rc = run_cli(
            self._args(
                tmp_path,
                "--agent", "x",
                "--opstate", "AVAILABLE",
                "--integrity", "4", "--scope", "4", "--connectivity", "5",
                "--auoe", "obs",
                "--probe-json", str(tmp_path / "nonexistent.json"),
            )
        )
        assert rc == 1
        assert "probe" in capsys.readouterr().err.lower()

    def test_probe_cycle_via_cli(self, tmp_path, capsys):
        probe = tmp_path / "probe.json"
        probe.write_text(json.dumps({"integrity": 2}))
        rc = run_cli(
            self._args(
                tmp_path,
                "--agent", "x",
                "--opstate", "AVAILABLE",
                "--integrity", "5", "--scope", "4", "--connectivity", "5",
                "--auoe", "obs",
                "--probe-json", str(probe),
            )
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "NOT ARSI-safe" in out
        assert "Calibrated:     False" in out
        assert "delta +3" in out
