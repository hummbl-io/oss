"""Tests for the CLI — scan, report, contradictions commands."""

import json
from pathlib import Path

from hummbl_axis.cli import main


SAMPLE_LEDGER = """\
# HUMMBL Atlas — Test Ledger

## AR-TEST-001

- **Scope:** Skill count drift
- **Direct observation:** 547 skills found in filesystem scan.
- **Contradiction:** Manifest declares 360 skills but 547 exist in the filesystem.
- **Verdict:** Manifest is stale; update or reconcile.
- **Confidence:** High
- **Volatility:** Medium
"""


class TestCLIContradictions:
    def test_contradictions_command_lists_them(self, tmp_path: Path, capsys):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")

        rc = main(["contradictions", "--atlas-dir", str(atlas_dir)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "547" in out
        assert "360" in out

    def test_contradictions_nonexistent_dir(self, tmp_path: Path, capsys):
        rc = main(["contradictions", "--atlas-dir", str(tmp_path / "nonexistent")])
        assert rc == 1


class TestCLIScan:
    def test_scan_with_atlas_dir(self, tmp_path: Path, capsys):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        state_path = tmp_path / "state.json"

        rc = main(["scan", "--atlas-dir", str(atlas_dir), "--cycle-state", str(state_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "cycle 1" in out
        assert "547" in out
        assert state_path.exists()

    def test_scan_creates_cycle_state(self, tmp_path: Path):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        state_path = tmp_path / "state.json"

        main(["scan", "--atlas-dir", str(atlas_dir), "--cycle-state", str(state_path)])
        state = json.loads(state_path.read_text())
        assert state["cycle"] == 1
        assert len(state["seen"]) == 1

    def test_scan_with_inventory_diff(self, tmp_path: Path, capsys):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")

        inv_path = tmp_path / "inventory.json"
        inv_path.write_text(json.dumps({"stats": {"skills": 360}}), encoding="utf-8")

        obs_path = tmp_path / "observed.json"
        obs_path.write_text(json.dumps({"skills": 547}), encoding="utf-8")

        state_path = tmp_path / "state.json"
        rc = main([
            "scan",
            "--atlas-dir", str(atlas_dir),
            "--inventory", str(inv_path),
            "--observed-counts", str(obs_path),
            "--cycle-state", str(state_path),
        ])
        out = capsys.readouterr().out
        assert rc == 0
        # Should have both markdown + count diff contradictions
        assert "count:skills" in out

    def test_scan_exit_when_stuck(self, tmp_path: Path, capsys):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        state_path = tmp_path / "state.json"

        # Run 4 cycles with the same contradiction
        for i in range(4):
            rc = main(["scan", "--atlas-dir", str(atlas_dir), "--cycle-state", str(state_path)])

        out = capsys.readouterr().out
        assert rc == 2  # stuck exit code
        assert "EXIT" in out
        assert "stuck" in out


class TestCLIReport:
    def test_report_shows_cycle_history(self, tmp_path: Path, capsys):
        atlas_dir = tmp_path / "atlas"
        atlas_dir.mkdir()
        (atlas_dir / "hummbl-atlas-test.md").write_text(SAMPLE_LEDGER, encoding="utf-8")
        state_path = tmp_path / "state.json"

        main(["scan", "--atlas-dir", str(atlas_dir), "--cycle-state", str(state_path)])
        capsys.readouterr()  # clear

        rc = main(["report", "--cycle-state", str(state_path)])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert data["cycle"] == 1
        assert len(data["history"]) == 1
