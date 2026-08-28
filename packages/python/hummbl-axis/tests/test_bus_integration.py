"""Tests for bus integration — message formatting and posting logic."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from hummbl_axis.cli import _format_bus_message, _bus_post
from hummbl_axis.contradiction import Contradiction


def _make_contradiction(severity: str = "P2", scope: str = "test") -> Contradiction:
    return Contradiction(
        scope=scope,
        claim="declared: 360",
        observation="observed: 547",
        severity=severity,
        confidence=0.85,
        volatility="medium",
        evidence_source="atlas.json",
        claim_source="manifest.json",
    )


class TestFormatBusMessage:
    def test_basic_message_with_counts(self):
        c1 = _make_contradiction("P1", "scope-a")
        c2 = _make_contradiction("P2", "scope-b")
        c3 = _make_contradiction("P2", "scope-c")
        results = [(c1, 0), (c2, 0), (c3, 0)]
        msg = _format_bus_message(results, cycle=3, host="delta")
        assert "host=delta" in msg
        assert "cycle 3" in msg
        assert "3 contradictions" in msg
        assert "P1: 1" in msg
        assert "P2: 2" in msg
        assert "P0: 0" in msg
        assert "P3: 0" in msg

    def test_includes_top_contradiction(self):
        c = _make_contradiction("P1", "count:skills")
        results = [(c, 0)]
        msg = _format_bus_message(results, cycle=1, host="delta")
        assert "[P1]" in msg
        assert "count:skills" in msg
        assert "declared: 360" in msg
        assert "observed: 547" in msg

    def test_stuck_flag(self):
        c = _make_contradiction("P1", "count:skills")
        results = [(c, 3)]  # unchanged for 3 cycles
        msg = _format_bus_message(results, cycle=4, host="delta")
        assert "[STUCK 3c]" in msg

    def test_no_stuck_flag_below_threshold(self):
        c = _make_contradiction("P1", "count:skills")
        results = [(c, 2)]  # unchanged for 2 cycles
        msg = _format_bus_message(results, cycle=3, host="delta")
        assert "STUCK" not in msg

    def test_empty_results(self):
        msg = _format_bus_message([], cycle=1, host="delta")
        assert "host=delta" in msg
        assert "0 contradictions" in msg
        assert "P0: 0" in msg


class TestBusPost:
    def test_dry_run_does_not_post(self, tmp_path: Path, capsys):
        c = _make_contradiction("P1", "test")
        results = [(c, 0)]
        posted = _bus_post(results, "delta", cycle=1, host="delta", dry_run=True)
        assert posted is True
        err = capsys.readouterr().err
        assert "dry-run" in err

    def test_bus_global_success(self, tmp_path: Path, capsys):
        """When bus-global.py exists and returns 0, post succeeds."""
        bus_script = tmp_path / "bus-global.py"
        bus_script.write_text("# mock", encoding="utf-8")

        c = _make_contradiction("P1", "test")
        results = [(c, 0)]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            posted = _bus_post(results, "delta", cycle=1, host="delta", bus_path=bus_script)

        assert posted is True
        assert mock_run.call_count == 1
        # Verify the command includes the right args
        call_args = mock_run.call_args[0][0]
        assert "post" in call_args
        assert "axis" in call_args
        assert "all" in call_args
        assert "SITREP" in call_args

    def test_bus_global_failure_falls_back_to_tsv(self, tmp_path: Path, capsys):
        """When bus-global.py fails, falls back to direct TSV append."""
        bus_script = tmp_path / "bus-global.py"
        bus_script.write_text("# mock", encoding="utf-8")

        # Create a fallback TSV path
        fallback_tsv = tmp_path / "messages.tsv"

        c = _make_contradiction("P1", "test")
        results = [(c, 0)]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="connection refused", stdout="")
            with patch("hummbl_axis.cli.Path.home", return_value=tmp_path):
                # Create the directory structure the fallback expects
                fb_dir = tmp_path / "Projects" / "hummbl-governance" / "_state" / "coordination"
                fb_dir.mkdir(parents=True, exist_ok=True)
                posted = _bus_post(results, "delta", cycle=1, host="delta", bus_path=bus_script)

        assert posted is True
        # Verify TSV was written
        tsv_path = fb_dir / "messages.tsv"
        assert tsv_path.exists()
        content = tsv_path.read_text(encoding="utf-8")
        assert "axis" in content
        assert "SITREP" in content
        assert "host=delta" in content

    def test_all_paths_fail(self, tmp_path: Path, capsys):
        """When bus-global.py doesn't exist and fallback paths are unwritable, returns False."""
        c = _make_contradiction("P1", "test")
        results = [(c, 0)]

        nonexistent = tmp_path / "nonexistent-bus.py"
        # Patch Path.home to a path where we can't create directories
        # and also patch open to raise on the fallback TSV paths
        with patch("hummbl_axis.cli.Path.home", return_value=tmp_path / "nonexistent-home"):
            with patch("builtins.open", side_effect=PermissionError("no write access")):
                posted = _bus_post(results, "delta", cycle=1, host="delta", bus_path=nonexistent)

        assert posted is False
        err = capsys.readouterr().err
        assert "failed" in err.lower()
