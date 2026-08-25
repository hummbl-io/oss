"""Tests for the coverage matrix ratchet gate (scripts/coverage_ratchet.py).

Verifies:
1. Ratchet passes when current >= baseline
2. Ratchet fails when current < baseline (regression detected)
3. Ratchet suggests raising baseline when current > baseline
4. --init-baseline creates a valid baseline file
5. Missing baseline file exits with code 2
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "coverage_ratchet.py"


def _run_ratchet(baseline: str, report: str, *extra: str) -> tuple[int, str]:
    """Run the ratchet script and return (exit_code, stdout)."""
    cmd = [sys.executable, str(SCRIPT), "--baseline", baseline, "--report", report, *extra]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def _make_report(
    path: Path,
    validated: int,
    fulfilled: int,
    failed: int,
    row_results: list[dict] | None = None,
) -> None:
    """Create a minimal evidence validation report JSON.

    If row_results is provided, it is placed under the matrix's "rows" key
    so the ratchet can check row identities.
    """
    matrix_data: dict = {
        "totals": {"fulfilled": fulfilled},
        "fulfilled_validation": {
            "rows_passed": validated,
            "rows_failed": failed,
            "rows_without_refs": failed,
        },
    }
    if row_results is not None:
        matrix_data["rows"] = row_results
    data = {"test-matrix.md": matrix_data}
    path.write_text(json.dumps(data), encoding="utf-8")


def _make_baseline(
    path: Path,
    validated: int,
    fulfilled: int,
    pct: float,
    validated_rows: list[dict] | None = None,
) -> None:
    """Create a ratchet baseline file.

    If validated_rows is provided, it is included for row-identity ratchet.
    """
    data: dict = {
        "validated_count": validated,
        "fulfilled_count": fulfilled,
        "validated_pct": pct,
        "description": "Test baseline",
    }
    if validated_rows is not None:
        data["validated_rows"] = validated_rows
    path.write_text(json.dumps(data), encoding="utf-8")


def _row_result(control_id: str, status: str, line_no: int = 1) -> dict:
    """Create a minimal row result for testing."""
    return {
        "control_id": control_id,
        "line_no": line_no,
        "status": status,
        "refs": [],
        "detail": "test",
    }


class TestCoverageRatchetPass:
    def test_ratchet_passes_when_current_matches_baseline(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=5, fulfilled=100, failed=95)
        _make_baseline(baseline, validated=5, fulfilled=100, pct=5.0)
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 0
        assert "RATCHET PASSED" in output

    def test_ratchet_passes_when_current_exceeds_baseline(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=10, fulfilled=100, failed=90)
        _make_baseline(baseline, validated=5, fulfilled=100, pct=5.0)
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 0
        assert "RATCHET PASSED with improvement" in output
        assert "+5" in output


class TestCoverageRatchetFail:
    def test_ratchet_fails_on_regression(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=3, fulfilled=100, failed=97)
        _make_baseline(baseline, validated=5, fulfilled=100, pct=5.0)
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 1
        assert "RATCHET FAILED" in output
        assert "regressed" in output
        assert "3" in output and "5" in output


class TestCoverageRatchetInitBaseline:
    def test_init_baseline_creates_file(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=7, fulfilled=50, failed=43)
        rc, output = _run_ratchet(str(baseline), str(report), "--init-baseline")
        assert rc == 0
        assert "BASELINE SET" in output
        assert baseline.exists()
        data = json.loads(baseline.read_text())
        assert data["validated_count"] == 7
        assert data["fulfilled_count"] == 50


class TestCoverageRatchetMissingBaseline:
    def test_missing_baseline_exits_2(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "nonexistent.json"
        _make_report(report, validated=5, fulfilled=100, failed=95)
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 2
        assert "Baseline file not found" in output


class TestCoverageRatchetPromotionThreshold:
    def test_promotion_notice_when_threshold_reached(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=60, fulfilled=100, failed=40)
        _make_baseline(baseline, validated=5, fulfilled=100, pct=5.0)
        rc, output = _run_ratchet(str(baseline), str(report), "--promote-threshold", "50.0")
        assert rc == 0
        assert "PROMOTION THRESHOLD REACHED" in output
        assert "60.0%" in output

    def test_no_promotion_notice_below_threshold(self, tmp_path):
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_report(report, validated=5, fulfilled=100, failed=95)
        _make_baseline(baseline, validated=5, fulfilled=100, pct=5.0)
        rc, output = _run_ratchet(str(baseline), str(report), "--promote-threshold", "50.0")
        assert rc == 0
        assert "PROMOTION THRESHOLD" not in output
        assert "gap:" in output


class TestCoverageRatchetRowIdentity:
    """Row-identity ratchet — protects specific validated rows, not just count."""

    def test_row_identity_preserved(self, tmp_path):
        """All baseline rows still validate → pass."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        rows = [
            _row_result("Art. 5", "pass", line_no=48),
            _row_result("Art. 29", "pass", line_no=102),
        ]
        _make_report(report, validated=2, fulfilled=10, failed=8, row_results=rows)
        _make_baseline(
            baseline, validated=2, fulfilled=10, pct=20.0,
            validated_rows=[
                {"matrix": "test-matrix.md", "control_id": "Art. 5"},
                {"matrix": "test-matrix.md", "control_id": "Art. 29"},
            ],
        )
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 0
        assert "RATCHET PASSED" in output
        assert "row identity" in output.lower()

    def test_row_identity_lost(self, tmp_path):
        """One baseline row no longer validates → fail, even if count is same."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        # Art. 5 still passes, Art. 29 now fails — but a NEW row (Art. 99) passes
        # so validated count is still 2. Count-only ratchet would pass; row-identity must fail.
        rows = [
            _row_result("Art. 5", "pass", line_no=48),
            _row_result("Art. 29", "fail", line_no=102),
            _row_result("Art. 99", "pass", line_no=200),
        ]
        _make_report(report, validated=2, fulfilled=10, failed=8, row_results=rows)
        _make_baseline(
            baseline, validated=2, fulfilled=10, pct=20.0,
            validated_rows=[
                {"matrix": "test-matrix.md", "control_id": "Art. 5"},
                {"matrix": "test-matrix.md", "control_id": "Art. 29"},
            ],
        )
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 1
        assert "ROW IDENTITY" in output or "row identity" in output.lower()
        assert "Art. 29" in output

    def test_row_identity_gained(self, tmp_path):
        """All baseline rows still validate + new rows added → pass with improvement."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        rows = [
            _row_result("Art. 5", "pass", line_no=48),
            _row_result("Art. 29", "pass", line_no=102),
            _row_result("Art. 99", "pass", line_no=200),  # new
        ]
        _make_report(report, validated=3, fulfilled=10, failed=7, row_results=rows)
        _make_baseline(
            baseline, validated=2, fulfilled=10, pct=20.0,
            validated_rows=[
                {"matrix": "test-matrix.md", "control_id": "Art. 5"},
                {"matrix": "test-matrix.md", "control_id": "Art. 29"},
            ],
        )
        rc, output = _run_ratchet(str(baseline), str(report))
        assert rc == 0
        assert "RATCHET PASSED" in output

    def test_init_baseline_captures_row_identities(self, tmp_path):
        """--init-baseline should capture validated_rows from current report."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        rows = [
            _row_result("Art. 5", "pass", line_no=48),
            _row_result("Art. 29", "pass", line_no=102),
        ]
        _make_report(report, validated=2, fulfilled=10, failed=8, row_results=rows)
        rc, output = _run_ratchet(str(baseline), str(report), "--init-baseline")
        assert rc == 0
        assert "BASELINE SET" in output
        data = json.loads(baseline.read_text())
        assert "validated_rows" in data
        assert len(data["validated_rows"]) == 2
        assert data["validated_rows"][0]["control_id"] == "Art. 5"
        assert data["validated_rows"][1]["control_id"] == "Art. 29"


class TestCoverageRatchetBaselineLowering:
    """Baseline-lowering protection — refuses to lower without --force-lower --reason."""

    def test_init_baseline_refuses_to_lower_without_force(self, tmp_path):
        """--init-baseline refuses to lower baseline when existing baseline is higher."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        # Existing baseline at 10, current report only has 5 validated
        _make_baseline(baseline, validated=10, fulfilled=100, pct=10.0)
        _make_report(report, validated=5, fulfilled=100, failed=95)
        rc, output = _run_ratchet(str(baseline), str(report), "--init-baseline")
        assert rc == 1
        assert "REFUSED" in output or "refuse" in output.lower()
        assert "force-lower" in output.lower()
        # Baseline should NOT be modified
        data = json.loads(baseline.read_text())
        assert data["validated_count"] == 10

    def test_init_baseline_lowers_with_force_and_reason(self, tmp_path):
        """--init-baseline --force-lower --reason lowers the baseline with a warning."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_baseline(baseline, validated=10, fulfilled=100, pct=10.0)
        _make_report(report, validated=5, fulfilled=100, failed=95)
        rc, output = _run_ratchet(
            str(baseline), str(report), "--init-baseline",
            "--force-lower", "--reason", "matrix restructured, rows removed",
        )
        assert rc == 0
        assert "BASELINE SET" in output
        assert "WARNING" in output or "warning" in output.lower()
        assert "force-lower" in output.lower()
        data = json.loads(baseline.read_text())
        assert data["validated_count"] == 5
        assert data.get("lower_reason") == "matrix restructured, rows removed"

    def test_init_baseline_force_without_reason_refuses(self, tmp_path):
        """--force-lower without --reason still refuses."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_baseline(baseline, validated=10, fulfilled=100, pct=10.0)
        _make_report(report, validated=5, fulfilled=100, failed=95)
        rc, output = _run_ratchet(
            str(baseline), str(report), "--init-baseline", "--force-lower",
        )
        assert rc == 1
        assert "reason" in output.lower()
        # Baseline unchanged
        data = json.loads(baseline.read_text())
        assert data["validated_count"] == 10

    def test_init_baseline_raises_without_force(self, tmp_path):
        """--init-baseline raising the baseline (current > existing) works without --force-lower."""
        report = tmp_path / "report.json"
        baseline = tmp_path / "baseline.json"
        _make_baseline(baseline, validated=3, fulfilled=100, pct=3.0)
        _make_report(report, validated=7, fulfilled=100, failed=93)
        rc, output = _run_ratchet(str(baseline), str(report), "--init-baseline")
        assert rc == 0
        assert "BASELINE SET" in output
        data = json.loads(baseline.read_text())
        assert data["validated_count"] == 7
