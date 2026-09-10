"""Integration tests for CLI review-claim -> review-coverage roundtrip.

Tests that review-claim persists claims to the coverage matrix and
review-coverage reads them back. Uses a temp state dir to avoid
polluting real coverage data.
"""

from __future__ import annotations

import os
from pathlib import Path

from hummbl_gitops.cli import main as cli_main
from hummbl_gitops.remote.coverage_matrix import get_coverage


class TestReviewClaimCoverageRoundtrip:
    """Test the full CLI claim -> coverage cycle."""

    def test_claim_then_coverage_shows_reviewed_aspects(self, tmp_path: Path, capsys) -> None:
        """review-claim should persist, review-coverage should show it."""
        # Use temp state dir so we don't pollute real data
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)

        # Claim two aspects
        rc1 = cli_main(["review-claim", "100", "--aspect", "security", "--agent", "devin"])
        assert rc1 == 0
        capsys.readouterr()  # clear output

        rc2 = cli_main(["review-claim", "100", "--aspect", "logic", "--agent", "codex"])
        assert rc2 == 0
        capsys.readouterr()  # clear output

        # Query coverage
        rc3 = cli_main(["review-coverage", "100"])
        assert rc3 == 0
        out = capsys.readouterr().out

        assert "security: devin" in out
        assert "logic: codex" in out
        assert "Uncovered" in out  # 6 of 8 still uncovered

        # Also verify via the API directly
        coverage = get_coverage(100, base_dir=tmp_path)
        assert "security" in coverage.covered_aspects
        assert "logic" in coverage.covered_aspects
        assert len(coverage.reviews) == 2

        del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_invalid_aspect_returns_error(self, tmp_path: Path, capsys) -> None:
        """review-claim with invalid aspect should return 1."""
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)

        rc = cli_main(["review-claim", "100", "--aspect", "nonexistent"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "Invalid aspect" in out

        del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_multiple_claims_same_aspect_different_agents(self, tmp_path: Path, capsys) -> None:
        """Two agents claiming the same aspect should both appear."""
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)

        cli_main(["review-claim", "200", "--aspect", "security", "--agent", "devin"])
        capsys.readouterr()
        cli_main(["review-claim", "200", "--aspect", "security", "--agent", "codex"])
        capsys.readouterr()

        cli_main(["review-coverage", "200"])
        out = capsys.readouterr().out

        assert "security: devin, codex" in out

        del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_coverage_empty_pr(self, tmp_path: Path, capsys) -> None:
        """review-coverage on a PR with no claims should show all uncovered."""
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)

        rc = cli_main(["review-coverage", "999"])
        assert rc == 0
        out = capsys.readouterr().out

        assert "No reviews recorded" in out

        del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_default_agent_is_devin(self, tmp_path: Path, capsys) -> None:
        """review-claim without --agent should default to devin."""
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)

        cli_main(["review-claim", "300", "--aspect", "tests"])
        out = capsys.readouterr().out

        assert "agent=devin" in out

        coverage = get_coverage(300, base_dir=tmp_path)
        assert coverage.reviews[0]["agent"] == "devin"

        del os.environ["HUMMBL_GITOPS_STATE_DIR"]
