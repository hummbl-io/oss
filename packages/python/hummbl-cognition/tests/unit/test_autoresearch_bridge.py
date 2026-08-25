"""Tests for the Autoresearch Bridge."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def _write_report(path: Path, title: str, summary: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"# {title}\n\n## Executive Summary\n\n{summary}\n"
    path.write_text(content, encoding="utf-8")
    return path


class TestExtractTitle:
    def test_extracts_h1(self):
        from hummbl_cognition.autoresearch_bridge import _extract_title
        assert _extract_title("# My Report\n\nBody text") == "My Report"

    def test_empty_when_no_heading(self):
        from hummbl_cognition.autoresearch_bridge import _extract_title
        assert _extract_title("Just plain text") == ""


class TestExtractSummary:
    def test_extracts_executive_summary(self):
        from hummbl_cognition.autoresearch_bridge import _extract_summary
        content = "# Title\n\n## Executive Summary\n\nThis is the summary.\n\n## Next Section\n"
        assert "This is the summary" in _extract_summary(content)

    def test_fallback_to_first_paragraph(self):
        from hummbl_cognition.autoresearch_bridge import _extract_summary
        content = "# Title\n\nFirst paragraph here.\n\nSecond paragraph.\n"
        summary = _extract_summary(content)
        assert "First paragraph" in summary


class TestParseReport:
    def test_parses_report(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _parse_report

        report = tmp_path / "reports" / "2026-03-14-test-report.md"
        _write_report(report, "Test Report", "This is a test finding about OAuth patterns.")

        entry = _parse_report(report)
        assert entry is not None
        assert "Test Report" in entry["content"]
        assert "OAuth patterns" in entry["content"]
        assert entry["agent"] == "autoresearch-bridge"
        assert entry["type"] == "discovery"
        assert "autoresearch" in entry["tags"]

    def test_extracts_rq_id(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _parse_report

        report = tmp_path / "reports" / "2026-03-14-rq001.md"
        _write_report(report, "Research Report RQ-001", "About tool use patterns.")

        entry = _parse_report(report)
        assert "rq-001" in entry["tags"]

    def test_skips_empty_files(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _parse_report

        report = tmp_path / "reports" / "empty.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("")

        assert _parse_report(report) is None

    def test_classifies_findings(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _parse_report

        finding = tmp_path / "findings" / "2026-03-14-finding.md"
        _write_report(finding, "A Finding", "Important discovery about caching.")

        entry = _parse_report(finding)
        assert entry["type"] == "discovery"
        assert "source:findings" in entry["tags"]

    def test_classifies_proposals(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _parse_report

        proposal = tmp_path / "proposals" / "2026-03-14-proposal.md"
        _write_report(proposal, "A Proposal", "We should improve the cache layer.")

        entry = _parse_report(proposal)
        assert entry["type"] == "lesson"
        assert "source:proposals" in entry["tags"]


class TestStateManagement:
    def test_load_save_state(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _load_state, _save_state

        state_file = tmp_path / "state.json"
        state = _load_state(state_file)
        assert state["ingested_files"] == {}

        state["ingested_files"]["reports/test.md"] = "abc123"
        _save_state(state_file, state)

        reloaded = _load_state(state_file)
        assert reloaded["ingested_files"]["reports/test.md"] == "abc123"
        assert reloaded["last_run"] is not None

    def test_load_handles_corrupt_file(self, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _load_state

        state_file = tmp_path / "state.json"
        state_file.write_text("not json")

        state = _load_state(state_file)
        assert state["ingested_files"] == {}


class TestRunBridge:
    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    @patch("hummbl_cognition.autoresearch_bridge._ingest_to_open_brain")
    def test_dry_run(self, mock_ingest, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import run_bridge

        mock_git.return_value = True

        # Set up fake repo
        repo_dir = tmp_path / "repo"
        _write_report(
            repo_dir / "reports" / "2026-03-14-test.md",
            "Test Report", "A summary about OAuth.",
        )

        result = run_bridge(
            repo_dir=repo_dir,
            state_file=tmp_path / "state.json",
            dry_run=True,
        )

        assert result["new_files"] == 1
        assert result["ingested"] == 1
        mock_ingest.assert_not_called()

    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    @patch("hummbl_cognition.autoresearch_bridge._ingest_to_open_brain")
    def test_ingests_new_files(self, mock_ingest, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import run_bridge

        mock_git.return_value = True
        mock_ingest.return_value = {"ingested": 1, "errors": []}

        repo_dir = tmp_path / "repo"
        _write_report(
            repo_dir / "reports" / "2026-03-14-test.md",
            "Test Report", "A summary about OAuth.",
        )

        result = run_bridge(
            repo_dir=repo_dir,
            state_file=tmp_path / "state.json",
            brain_url="http://127.0.0.1:11435",
        )

        assert result["ingested"] == 1
        mock_ingest.assert_called_once()

    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    @patch("hummbl_cognition.autoresearch_bridge._ingest_to_open_brain")
    def test_skips_already_ingested(self, mock_ingest, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import (
            _file_hash,
            _save_state,
            run_bridge,
        )

        mock_git.return_value = True

        repo_dir = tmp_path / "repo"
        report = _write_report(
            repo_dir / "reports" / "2026-03-14-test.md",
            "Test Report", "A summary.",
        )

        # Pre-populate state as already ingested
        state_file = tmp_path / "state.json"
        state = {
            "ingested_files": {
                "reports/2026-03-14-test.md": _file_hash(report),
            },
            "last_run": None,
        }
        _save_state(state_file, state)

        result = run_bridge(
            repo_dir=repo_dir,
            state_file=state_file,
        )

        assert result["new_files"] == 0
        mock_ingest.assert_not_called()

    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    def test_handles_git_failure(self, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import run_bridge

        mock_git.return_value = False

        result = run_bridge(
            repo_dir=tmp_path / "repo",
            state_file=tmp_path / "state.json",
        )

        assert result["new_files"] == 0
        assert "git pull/clone failed" in result["errors"]

    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    @patch("hummbl_cognition.autoresearch_bridge._ingest_to_open_brain")
    def test_reingest_on_file_change(self, mock_ingest, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import _save_state, run_bridge

        mock_git.return_value = True
        mock_ingest.return_value = {"ingested": 1, "errors": []}

        repo_dir = tmp_path / "repo"
        _write_report(
            repo_dir / "reports" / "2026-03-14-test.md",
            "Test Report", "Original content.",
        )

        # Pre-populate with OLD hash
        state_file = tmp_path / "state.json"
        _save_state(state_file, {
            "ingested_files": {"reports/2026-03-14-test.md": "old_hash"},
            "last_run": None,
        })

        result = run_bridge(
            repo_dir=repo_dir,
            state_file=state_file,
            brain_url="http://127.0.0.1:11435",
        )

        # File changed, should re-ingest
        assert result["new_files"] == 1
        assert result["ingested"] == 1


class TestCLI:
    @patch("hummbl_cognition.autoresearch_bridge._git_clone_or_pull")
    def test_status_command(self, mock_git, tmp_path):
        from hummbl_cognition.autoresearch_bridge import main

        rc = main(["status", "--state-file", str(tmp_path / "state.json")])
        assert rc == 0

    def test_no_command_shows_help(self):
        from hummbl_cognition.autoresearch_bridge import main

        rc = main([])
        assert rc == 2
