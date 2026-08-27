"""Tests for cognition/hrsi_checkin.py — HRSI Gap 2 unified cycle CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from hummbl_cognition.hrsi_checkin import (
    COGNITION_DIR,
    get_status,
    record_cycle,
    resolve_cognition_dir,
    run_cli,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_paths(tmp_path: Path):
    """Returns (baseline_path, cycles_path, ledger_path) all in tmp_path."""
    return (
        tmp_path / "belonging_baseline.jsonl",
        tmp_path / "hrsi_cycles.jsonl",
        tmp_path / "ledger.jsonl",
    )


# ---------------------------------------------------------------------------
# record_cycle
# ---------------------------------------------------------------------------


class TestRecordCycle:
    def test_default_state_dir_is_repository_root_state(self):
        expected = Path(__file__).resolve().parents[3] / "_state" / "cognition"
        assert COGNITION_DIR == expected

    def test_explicit_cognition_dir_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HRSI_COGNITION_DIR", str(tmp_path))
        assert resolve_cognition_dir() == tmp_path.resolve()

    def test_writes_cycle_file(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=5,
            hule="Noticed the link between X and Y",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycles.exists()
        lines = [json.loads(l) for l in cycles.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        assert lines[0]["cogstate"] == "AVAILABLE"
        assert lines[0]["hule"] == "Noticed the link between X and Y"

    def test_belonging_avg_computed(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Test",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["belonging_avg"] == 4.0

    def test_hrsi_safe_when_available_and_all_gte_3(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=3,
            mattering=3,
            connection=3,
            hule="Minimum threshold",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["hrsi_safe"] is True

    def test_not_hrsi_safe_when_not_available(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="HYPERFOCUS",
            safety=5,
            mattering=5,
            connection=5,
            hule="Deep work but not AVAILABLE",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["hrsi_safe"] is False

    def test_not_hrsi_safe_when_belonging_below_3(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=2,
            mattering=4,
            connection=4,
            hule="Low safety day",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["hrsi_safe"] is False

    def test_optional_lens_and_delta(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Applied BKI lens to client conversation",
            lens="bki",
            delta="K+: new integration of Prop 3",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["lens"] == "bki"
        assert cycle["delta"] == "K+: new integration of Prop 3"

    def test_lens_absent_when_not_provided(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="No lens today",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert "lens" not in cycle
        assert "delta" not in cycle

    def test_writes_to_belonging_baseline(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=3,
            connection=5,
            hule="Test baseline write",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert baseline.exists()
        entry = json.loads(baseline.read_text().strip())
        assert entry["safety"] == 4
        assert entry["mattering"] == 3
        assert entry["connection"] == 5
        assert entry["cogstate"] == "AVAILABLE"

    def test_writes_ledger_entry(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Ledger write test",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert ledger.exists()
        assert "ledger_id" in cycle
        assert cycle["ledger_id"].startswith("clp-")
        data = json.loads(ledger.read_text().strip())
        assert "hrsi-cycle" in data["tags"]
        assert "hrsi-gap2" in data["tags"]

    def test_ledger_tags_include_lens(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Lens tag test",
            lens="girard",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        data = json.loads(ledger.read_text().strip())
        assert "lens-girard" in data["tags"]

    def test_ledger_tags_include_hrsi_safe(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=3,
            mattering=3,
            connection=3,
            hule="Safe day",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        data = json.loads(ledger.read_text().strip())
        assert "hrsi-safe" in data["tags"]

    def test_multiple_cycles_appended(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        for i in range(3):
            record_cycle(
                cogstate="AVAILABLE",
                safety=4,
                mattering=4,
                connection=4,
                hule=f"Cycle {i}",
                today=f"2026-04-{10 + i:02d}",
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )
        lines = [l for l in cycles.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_energy_stored_when_provided(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Energy test",
            energy=3,
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["energy"] == 3

    def test_sleep_hours_stored_when_provided(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Sleep test",
            sleep_hours=7.5,
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["sleep_hours"] == 7.5

    def test_relational_note_stored_when_provided(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Relational test",
            relational_note="Coffee with Dan",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert cycle["relational_note"] == "Coffee with Dan"

    def test_shared_ledger_omits_raw_personal_notes_by_default(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="Private client-specific observation",
            relational_note="Coffee with Named Client",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        ledger_text = ledger.read_text(encoding="utf-8")
        assert "Private client-specific observation" not in ledger_text
        assert "Coffee with Named Client" not in ledger_text
        assert "hule_sha256=" in ledger_text
        assert "relational_sha256=" in ledger_text

    def test_failed_ledger_write_rolls_back_baseline_and_cycle(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with patch(
            "hummbl_cognition.hrsi_checkin.post_entry",
            side_effect=OSError("simulated ledger failure"),
        ):
            with pytest.raises(OSError, match="simulated ledger failure"):
                record_cycle(
                    cogstate="AVAILABLE",
                    safety=4,
                    mattering=4,
                    connection=4,
                    hule="Rollback test",
                    baseline_path=baseline,
                    cycles_path=cycles,
                    ledger_path=ledger,
                )
        assert not baseline.exists()
        assert not cycles.exists()
        assert not ledger.exists()

    def test_somatic_fields_absent_when_not_provided(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        cycle = record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="No somatic data",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        assert "energy" not in cycle
        assert "sleep_hours" not in cycle
        assert "relational_note" not in cycle

    def test_invalid_energy_raises(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with pytest.raises(ValueError, match="energy"):
            record_cycle(
                cogstate="AVAILABLE",
                safety=4,
                mattering=4,
                connection=4,
                hule="test",
                energy=6,
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )

    def test_invalid_sleep_hours_raises(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with pytest.raises(ValueError, match="sleep_hours"):
            record_cycle(
                cogstate="AVAILABLE",
                safety=4,
                mattering=4,
                connection=4,
                hule="test",
                sleep_hours=25,
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )

    def test_invalid_cogstate_raises(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with pytest.raises(ValueError, match="cogstate"):
            record_cycle(
                cogstate="INVALID",
                safety=4,
                mattering=4,
                connection=4,
                hule="test",
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )

    def test_invalid_score_raises(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with pytest.raises(ValueError, match="safety"):
            record_cycle(
                cogstate="AVAILABLE",
                safety=6,
                mattering=4,
                connection=4,
                hule="test",
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )

    def test_empty_hule_raises(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        with pytest.raises(ValueError, match="--hule"):
            record_cycle(
                cogstate="AVAILABLE",
                safety=4,
                mattering=4,
                connection=4,
                hule="   ",
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_empty_state(self, tmp_paths):
        baseline, cycles, _ = tmp_paths
        status = get_status(baseline_path=baseline, cycles_path=cycles)
        assert status["gap1_qualifying_days"] == 0
        assert status["gap1_total_days"] == 0
        assert status["gap1_closed"] is False
        assert status["total_cycles"] == 0
        assert status["gap2_closed"] is False

    def test_gap2_closed_after_first_cycle(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        record_cycle(
            cogstate="AVAILABLE",
            safety=4,
            mattering=4,
            connection=4,
            hule="First cycle",
            baseline_path=baseline,
            cycles_path=cycles,
            ledger_path=ledger,
        )
        status = get_status(baseline_path=baseline, cycles_path=cycles)
        assert status["gap2_closed"] is True
        assert status["total_cycles"] == 1

    def test_gap1_closed_after_21_qualifying_days(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        for i in range(21):
            record_cycle(
                cogstate="AVAILABLE",
                safety=4,
                mattering=4,
                connection=4,
                hule=f"Day {i}",
                today=f"2026-0{3 + i // 30}-{1 + i:02d}",
                baseline_path=baseline,
                cycles_path=cycles,
                ledger_path=ledger,
            )
        status = get_status(baseline_path=baseline, cycles_path=cycles)
        assert status["gap1_qualifying_days"] == 21
        assert status["gap1_closed"] is True


# ---------------------------------------------------------------------------
# run_cli (integration)
# ---------------------------------------------------------------------------


class TestRunCli:
    def test_status_exits_zero_on_empty(self, tmp_paths, capsys):
        baseline, cycles, _ = tmp_paths
        code = run_cli(
            [
                "--status",
                "--ledger",
                str(tmp_paths[2]),
            ]
        )
        # --status doesn't use baseline/cycles path overrides yet; just check exit code
        assert code == 0

    def test_full_cycle_exits_zero(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "3",
                "--connection",
                "5",
                "--hule",
                "Insight from today's session",
                "--lens",
                "bki",
                "--delta",
                "K+ belonging integration",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0

    def test_missing_required_flags_exits_nonzero(self, tmp_paths, capsys):
        code = run_cli(["--cogstate", "AVAILABLE"])
        assert code != 0
        captured = capsys.readouterr()
        assert "ERROR" in captured.err

    def test_invalid_cogstate_exits_nonzero(self, tmp_paths):
        baseline, cycles, ledger = tmp_paths
        code = run_cli(
            [
                "--cogstate",
                "BADSTATE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "test",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code != 0

    def test_prints_ledger_id(self, tmp_paths, capsys):
        baseline, cycles, ledger = tmp_paths
        run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "Printed ledger id check",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        captured = capsys.readouterr()
        assert "clp-" in captured.out

    def test_prints_hrsi_safe(self, tmp_paths, capsys):
        baseline, cycles, ledger = tmp_paths
        run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "3",
                "--mattering",
                "3",
                "--connection",
                "3",
                "--hule",
                "HRSI safe day",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        captured = capsys.readouterr()
        assert "HRSI-safe" in captured.out


# ---------------------------------------------------------------------------
# Bridge mode
# ---------------------------------------------------------------------------


class TestBridgeMode:
    """Tests for --bridge flag and HRSI_CANONICAL_BRIDGE_URL env support."""

    def test_bridge_success(self, tmp_paths, monkeypatch, capsys):
        """Successful bridge post returns 0 and does not write locally."""
        baseline, cycles, ledger = tmp_paths
        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            lambda *a, **kw: {
                "ok": True,
                "status_code": 200,
                "body": {
                    "cycle": {
                        "date": "2026-01-01",
                        "cogstate": "AVAILABLE",
                        "belonging_avg": 4.0,
                        "hrsi_safe": True,
                        "energy": 3,
                        "sleep_hours": 7.0,
                        "relational_note": "test",
                    },
                    "status": {"gap1_qualifying_days": 1, "total_cycles": 1},
                },
                "permanent_error": False,
            },
        )
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "bridge test",
                "--bridge",
                "http://test-anvil.local:18791",
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0
        captured = capsys.readouterr()
        assert "via bridge" in captured.out
        # Local files should NOT be written on successful bridge post
        assert not cycles.exists()

    def test_bridge_failure_falls_back_to_local(self, tmp_paths, monkeypatch, capsys):
        """Bridge failure with local_fallback=True writes locally."""
        baseline, cycles, ledger = tmp_paths
        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            lambda *a, **kw: {
                "ok": False,
                "status_code": 500,
                "body": {},
                "permanent_error": False,
            },
        )
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "fallback test",
                "--bridge",
                "http://test-anvil.local:18791",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert cycles.exists()

    def test_bridge_failure_no_fallback_errors(self, tmp_paths, monkeypatch, capsys):
        """Bridge failure with --no-local-fallback returns 1."""
        baseline, cycles, ledger = tmp_paths
        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            lambda *a, **kw: {
                "ok": False,
                "status_code": 500,
                "body": {},
                "permanent_error": False,
            },
        )
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "no fallback test",
                "--bridge",
                "http://test-anvil.local:18791",
                "--no-local-fallback",
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 1
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert not cycles.exists()

    def test_bridge_permanent_error_no_fallback(self, tmp_paths, monkeypatch, capsys):
        """Permanent bridge error (401) returns 1 even with fallback on."""
        baseline, cycles, ledger = tmp_paths
        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            lambda *a, **kw: {
                "ok": False,
                "status_code": 401,
                "body": {},
                "permanent_error": True,
            },
        )
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "auth fail test",
                "--bridge",
                "http://test-anvil.local:18791",
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 1
        captured = capsys.readouterr()
        assert "permanent error" in captured.err

    def test_env_bridge_url_resolves(self, tmp_paths, monkeypatch):
        """HRSI_CANONICAL_BRIDGE_URL env var activates bridge mode."""
        baseline, cycles, ledger = tmp_paths
        called = {}

        def mock_post(url, **kw):
            called["url"] = url
            return {
                "ok": True,
                "status_code": 200,
                "body": {"cycle": {}, "status": {}},
                "permanent_error": False,
            }

        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            mock_post,
        )
        monkeypatch.setenv("HRSI_CANONICAL_BRIDGE_URL", "http://test-anvil.local:18791")
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "env bridge test",
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0
        assert "anvil" in called["url"]

    def test_cli_bridge_overrides_env(self, tmp_paths, monkeypatch):
        """--bridge flag takes precedence over HRSI_CANONICAL_BRIDGE_URL env."""
        baseline, cycles, ledger = tmp_paths
        called = {}

        def mock_post(url, **kw):
            called["url"] = url
            return {
                "ok": True,
                "status_code": 200,
                "body": {"cycle": {}, "status": {}},
                "permanent_error": False,
            }

        monkeypatch.setattr(
            "hummbl_cognition.hrsi_bridge_client.post_hrsi_to_bridge_url_result",
            mock_post,
        )
        monkeypatch.setenv("HRSI_CANONICAL_BRIDGE_URL", "http://env-url:18791")
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "cli override test",
                "--bridge",
                "http://cli-url:18791",
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0
        assert "cli-url" in called["url"]

    def test_no_bridge_url_returns_none(self, tmp_paths, monkeypatch):
        """Without --bridge or env, no bridge call is made."""
        baseline, cycles, ledger = tmp_paths
        monkeypatch.delenv("HRSI_CANONICAL_BRIDGE_URL", raising=False)
        code = run_cli(
            [
                "--cogstate",
                "AVAILABLE",
                "--safety",
                "4",
                "--mattering",
                "4",
                "--connection",
                "4",
                "--hule",
                "no bridge test",
                "--ledger",
                str(ledger),
                "--baseline",
                str(baseline),
                "--cycles",
                str(cycles),
            ]
        )
        assert code == 0
        assert cycles.exists()  # Local write happened
