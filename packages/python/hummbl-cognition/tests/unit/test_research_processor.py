"""Tests for the Research Queue Processor."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

try:
    from hummbl_governance.kill_switch_core import get_kill_switch_core  # noqa: F401
    _HAS_KILL_SWITCH_CORE = True
except ImportError:
    _HAS_KILL_SWITCH_CORE = False

SAMPLE_QUEUE = [
    {
        "id": "RQ-T01",
        "domain": "testing",
        "query": "What are best practices for testing AI agents?",
        "tier": 1,
        "recurrence": "weekly",
    },
    {
        "id": "RQ-T02",
        "domain": "security",
        "query": "How to secure multi-agent communication channels?",
        "tier": 2,
        "recurrence": "monthly",
    },
    {
        "id": "RQ-T03",
        "domain": "governance",
        "query": "What governance frameworks apply to AI agents?",
        "tier": 3,
        "recurrence": "once",
    },
]


class TestQuestionHash:
    def test_hash_is_deterministic(self):
        from hummbl_cognition.research_processor import _question_hash

        q = {"query": "test question", "recurrence": "weekly"}
        assert _question_hash(q) == _question_hash(q)

    def test_different_queries_different_hash(self):
        from hummbl_cognition.research_processor import _question_hash

        q1 = {"query": "question one", "recurrence": "weekly"}
        q2 = {"query": "question two", "recurrence": "weekly"}
        assert _question_hash(q1) != _question_hash(q2)

    def test_different_recurrence_different_hash(self):
        from hummbl_cognition.research_processor import _question_hash

        q1 = {"query": "same question", "recurrence": "weekly"}
        q2 = {"query": "same question", "recurrence": "monthly"}
        assert _question_hash(q1) != _question_hash(q2)


class TestShouldReprocess:
    def test_never_processed(self):
        from hummbl_cognition.research_processor import _should_reprocess

        q = SAMPLE_QUEUE[0]
        assert _should_reprocess(q, {}) is True

    def test_once_already_done(self):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _should_reprocess,
        )

        q = SAMPLE_QUEUE[2]  # recurrence: once
        processed = {
            q["id"]: {
                "hash": _question_hash(q),
                "last_processed": "2026-03-14T00:00:00Z",
            }
        }
        assert _should_reprocess(q, processed) is False

    def test_weekly_not_yet_due(self):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _should_reprocess,
        )

        q = SAMPLE_QUEUE[0]  # recurrence: weekly
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        processed = {
            q["id"]: {
                "hash": _question_hash(q),
                "last_processed": recent,
            }
        }
        assert _should_reprocess(q, processed) is False

    def test_weekly_overdue(self):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _should_reprocess,
        )

        q = SAMPLE_QUEUE[0]  # recurrence: weekly
        old = (datetime.now(timezone.utc) - timedelta(days=8)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        processed = {
            q["id"]: {
                "hash": _question_hash(q),
                "last_processed": old,
            }
        }
        assert _should_reprocess(q, processed) is True

    def test_monthly_overdue(self):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _should_reprocess,
        )

        q = SAMPLE_QUEUE[1]  # recurrence: monthly
        old = (datetime.now(timezone.utc) - timedelta(days=31)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        processed = {
            q["id"]: {
                "hash": _question_hash(q),
                "last_processed": old,
            }
        }
        assert _should_reprocess(q, processed) is True

    def test_query_changed(self):
        from hummbl_cognition.research_processor import _should_reprocess

        q = SAMPLE_QUEUE[2]  # recurrence: once
        processed = {
            q["id"]: {
                "hash": "old_hash_doesnt_match",
                "last_processed": "2026-03-14T00:00:00Z",
            }
        }
        assert _should_reprocess(q, processed) is True


class TestStateManagement:
    def test_load_empty(self, tmp_path):
        from hummbl_cognition.research_processor import _load_state

        state = _load_state(tmp_path / "state.json")
        assert state["processed"] == {}
        assert state["last_run"] is None

    def test_save_and_reload(self, tmp_path):
        from hummbl_cognition.research_processor import (
            _load_state,
            _save_state,
        )

        state_file = tmp_path / "state.json"
        state = _load_state(state_file)
        state["processed"]["RQ-T01"] = {"hash": "abc", "last_processed": "2026-03-14T00:00:00Z"}
        _save_state(state_file, state)

        reloaded = _load_state(state_file)
        assert reloaded["processed"]["RQ-T01"]["hash"] == "abc"
        assert reloaded["last_run"] is not None

    def test_load_handles_corrupt(self, tmp_path):
        from hummbl_cognition.research_processor import _load_state

        state_file = tmp_path / "state.json"
        state_file.write_text("not json")
        state = _load_state(state_file)
        assert state["processed"] == {}


class TestKillSwitchHelper:
    @pytest.mark.skipif(not _HAS_KILL_SWITCH_CORE, reason="hummbl_governance.kill_switch_core not available")
    def test_runtime_error_fails_closed(self):
        from hummbl_cognition.research_processor import _is_kill_switch_engaged

        with patch(
            "hummbl_governance.kill_switch_core.get_kill_switch_core",
            side_effect=RuntimeError("boom"),
        ):
            assert _is_kill_switch_engaged() is True


class TestRunProcessor:
    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_dry_run(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import run_processor

        result = run_processor(
            queue=SAMPLE_QUEUE,
            state_file=tmp_path / "state.json",
            dry_run=True,
        )

        assert result["processed"] == 3
        mock_ollama.assert_not_called()
        mock_ingest.assert_not_called()

    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_processes_by_tier_priority(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import run_processor

        mock_ollama.return_value = "1. Finding one\n2. Finding two"
        mock_ingest.return_value = {"ingested": 1, "errors": []}

        result = run_processor(
            queue=SAMPLE_QUEUE,
            state_file=tmp_path / "state.json",
            max_per_run=1,  # Only process 1
        )

        # Should pick tier 1 first (RQ-T01)
        assert result["processed"] == 1
        assert result["questions"] == ["RQ-T01"]

    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_skips_already_processed(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _save_state,
            run_processor,
        )

        # Pre-populate state
        state_file = tmp_path / "state.json"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = {
            "processed": {
                q["id"]: {
                    "hash": _question_hash(q),
                    "last_processed": now,
                }
                for q in SAMPLE_QUEUE
            },
            "last_run": None,
            "total_processed": 3,
        }
        _save_state(state_file, state)

        result = run_processor(
            queue=SAMPLE_QUEUE,
            state_file=state_file,
        )

        assert result["processed"] == 0
        assert result["skipped"] == 3
        mock_ollama.assert_not_called()

    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_handles_ollama_failure(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import run_processor

        mock_ollama.return_value = None  # Simulate failure

        result = run_processor(
            queue=[SAMPLE_QUEUE[0]],
            state_file=tmp_path / "state.json",
        )

        assert result["processed"] == 0
        assert any("Ollama call failed" in e for e in result["errors"])
        mock_ingest.assert_not_called()

    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_handles_ingest_failure(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import run_processor

        mock_ollama.return_value = "Some findings"
        mock_ingest.return_value = {"ingested": 0, "errors": ["connection refused"]}

        result = run_processor(
            queue=[SAMPLE_QUEUE[0]],
            state_file=tmp_path / "state.json",
        )

        assert result["processed"] == 0
        assert any("ingest failed" in e for e in result["errors"])

    @patch("hummbl_cognition.research_processor._is_kill_switch_engaged")
    def test_kill_switch_blocks(self, mock_ks, tmp_path):
        from hummbl_cognition.research_processor import run_processor

        mock_ks.return_value = True

        result = run_processor(
            queue=SAMPLE_QUEUE,
            state_file=tmp_path / "state.json",
        )

        assert result["processed"] == 0
        assert "kill switch engaged" in result["errors"]

    @patch("hummbl_cognition.research_processor._ollama_research")
    @patch("hummbl_cognition.research_processor._ingest_finding")
    def test_updates_state_after_success(self, mock_ingest, mock_ollama, tmp_path):
        from hummbl_cognition.research_processor import (
            _load_state,
            run_processor,
        )

        mock_ollama.return_value = "Research findings here"
        mock_ingest.return_value = {"ingested": 1, "errors": []}

        state_file = tmp_path / "state.json"
        run_processor(
            queue=[SAMPLE_QUEUE[2]],  # once recurrence
            state_file=state_file,
        )

        state = _load_state(state_file)
        assert "RQ-T03" in state["processed"]
        assert state["total_processed"] == 1


class TestProcessorStatus:
    def test_all_pending(self, tmp_path):
        from hummbl_cognition.research_processor import processor_status

        s = processor_status(
            queue=SAMPLE_QUEUE,
            state_file=tmp_path / "state.json",
        )
        assert s["total_questions"] == 3
        assert len(s["pending"]) == 3
        assert len(s["completed"]) == 0

    def test_partial_completion(self, tmp_path):
        from hummbl_cognition.research_processor import (
            _question_hash,
            _save_state,
            processor_status,
        )

        state_file = tmp_path / "state.json"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _save_state(state_file, {
            "processed": {
                "RQ-T03": {
                    "hash": _question_hash(SAMPLE_QUEUE[2]),
                    "last_processed": now,
                }
            },
            "last_run": None,
            "total_processed": 1,
        })

        s = processor_status(
            queue=SAMPLE_QUEUE,
            state_file=state_file,
        )
        assert "RQ-T03" in s["completed"]
        assert "RQ-T01" in s["pending"]
        assert "RQ-T02" in s["pending"]


class TestListQueue:
    def test_lists_all(self, tmp_path):
        from hummbl_cognition.research_processor import list_queue

        items = list_queue(
            queue=SAMPLE_QUEUE,
            state_file=tmp_path / "state.json",
        )
        assert len(items) == 3
        assert all(item["status"] == "pending" for item in items)
        assert items[0]["domain"] == "testing"


class TestCLI:
    def test_no_command_shows_help(self):
        from hummbl_cognition.research_processor import main

        rc = main([])
        assert rc == 2

    def test_status_command(self, tmp_path):
        from hummbl_cognition.research_processor import main

        rc = main(["status", "--state-file", str(tmp_path / "state.json")])
        assert rc == 0

    def test_list_command(self, tmp_path):
        from hummbl_cognition.research_processor import main

        rc = main(["list", "--state-file", str(tmp_path / "state.json")])
        assert rc == 0
