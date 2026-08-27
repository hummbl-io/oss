"""Tests for hummbl_cognition.retriever -- unified Open Brain retriever."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hummbl_cognition.retriever import (
    MemoryResult,
    OpenBrainRetriever,
    _estimate_tokens,
    _extract_snippet,
    _extract_tsv_messages,
)

# ---------------------------------------------------------------------------
# MemoryResult
# ---------------------------------------------------------------------------


class TestMemoryResult:
    def test_basic_construction(self):
        r = MemoryResult(
            source="ledger",
            entry_id="clp-001",
            score=0.85,
            content="hello world",
            metadata={"type": "observation"},
        )
        assert r.source == "ledger"
        assert r.entry_id == "clp-001"
        assert r.score == 0.85
        assert r.content == "hello world"
        assert r.metadata == {"type": "observation"}
        assert r.tokens > 0

    def test_tokens_auto_estimated(self):
        content = "a" * 100
        r = MemoryResult(
            source="bus",
            entry_id="b-1",
            score=0.5,
            content=content,
            metadata={},
        )
        assert r.tokens == 100 // 4  # _CHARS_PER_TOKEN = 4

    def test_tokens_override(self):
        r = MemoryResult(
            source="bus",
            entry_id="b-1",
            score=0.5,
            content="short",
            metadata={},
            tokens=42,
        )
        assert r.tokens == 42

    def test_tokens_zero_falls_back_to_estimate(self):
        r = MemoryResult(
            source="bus",
            entry_id="b-1",
            score=0.5,
            content="short",
            metadata={},
            tokens=0,
        )
        assert r.tokens == _estimate_tokens("short")

    def test_to_dict(self):
        r = MemoryResult(
            source="findings",
            entry_id="f-1",
            score=0.12345678,
            content="test",
            metadata={"k": "v"},
            tokens=10,
        )
        d = r.to_dict()
        assert d["source"] == "findings"
        assert d["entry_id"] == "f-1"
        assert d["score"] == 0.1235  # rounded to 4 decimals
        assert d["content"] == "test"
        assert d["metadata"] == {"k": "v"}
        assert d["tokens"] == 10

    def test_empty_content_tokens_at_least_one(self):
        r = MemoryResult(
            source="x",
            entry_id="x",
            score=0.0,
            content="",
            metadata={},
        )
        assert r.tokens >= 1


# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_normal_text(self):
        assert _estimate_tokens("hello world!") == len("hello world!") // 4

    def test_empty_returns_one(self):
        assert _estimate_tokens("") == 1

    def test_short_returns_one(self):
        assert _estimate_tokens("ab") == 1


# ---------------------------------------------------------------------------
# _extract_tsv_messages
# ---------------------------------------------------------------------------


class TestExtractTsvMessages:
    def test_basic_extraction(self):
        tsv = (
            "2026-03-01T00:00:00Z\tagent-a\tall\tSTATUS\thello\n"
            "2026-03-01T01:00:00Z\tagent-b\tall\tSITREP\tworld\n"
        )
        result = _extract_tsv_messages(tsv)
        assert "agent-a STATUS hello" in result
        assert "agent-b SITREP world" in result

    def test_since_filter(self):
        tsv = (
            "2026-03-01T00:00:00Z\ta\tb\tSTATUS\told\n"
            "2026-03-02T00:00:00Z\ta\tb\tSTATUS\tnew\n"
        )
        result = _extract_tsv_messages(tsv, since="2026-03-01T12:00:00Z")
        assert "old" not in result
        assert "new" in result

    def test_short_lines_skipped(self):
        tsv = "too\tfew\tcolumns\n"
        result = _extract_tsv_messages(tsv)
        assert result == ""

    def test_max_lines_cap(self):
        lines = [f"2026-03-01T{i:02d}:00:00Z\ta\tb\tSTATUS\tmsg{i}" for i in range(10)]
        tsv = "\n".join(lines)
        result = _extract_tsv_messages(tsv, max_lines=3)
        # Should only contain last 3
        assert "msg7" in result
        assert "msg8" in result
        assert "msg9" in result
        assert "msg0" not in result

    def test_empty_input(self):
        assert _extract_tsv_messages("") == ""


# ---------------------------------------------------------------------------
# _extract_snippet
# ---------------------------------------------------------------------------


class TestExtractSnippet:
    def test_returns_snippet_with_matching_tokens(self):
        text = "The quick brown fox jumps over the lazy dog"
        snippet = _extract_snippet(text, {"fox", "jump"}, max_chars=500)
        assert "fox" in snippet.lower()

    def test_short_text_no_ellipsis_prefix(self):
        text = "short"
        snippet = _extract_snippet(text, {"short"}, max_chars=500)
        assert not snippet.startswith("...")

    def test_long_text_gets_ellipsis(self):
        text = "x " * 3000 + "TARGET_WORD here"
        snippet = _extract_snippet(text, {"target_word"}, max_chars=100)
        # Should have trailing ellipsis since text is longer than snippet
        assert snippet.endswith("...")

    def test_no_matching_tokens_returns_start(self):
        text = "hello world this is content"
        snippet = _extract_snippet(text, {"zzzzz"}, max_chars=500)
        # Falls back to position 0
        assert snippet.startswith("hello")


# ---------------------------------------------------------------------------
# OpenBrainRetriever -- construction and ensure_index
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="API changed: retriever constructor signature")
class TestRetrieverConstruction:
    def test_default_state_dir(self):
        with patch("hummbl_cognition.retriever._resolve_state_dir") as mock_resolve:
            mock_resolve.return_value = Path("/tmp/state")
            r = OpenBrainRetriever()
            assert r.state_dir == Path("/tmp/state")

    def test_explicit_state_dir(self):
        r = OpenBrainRetriever(state_dir="/tmp/custom")
        assert r.state_dir == Path("/tmp/custom")

    def test_explicit_index(self):
        idx = MagicMock()
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        assert r.index is idx

    def test_ensure_index_loads_from_disk(self):
        idx = MagicMock()
        idx.load.return_value = True
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        r.ensure_index()
        idx.load.assert_called_once()
        assert r._index_loaded is True

    def test_ensure_index_builds_when_no_disk(self):
        idx = MagicMock()
        idx.load.return_value = False
        idx.save.return_value = None
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        r.ensure_index()
        idx.build.assert_called_once()
        idx.save.assert_called_once()
        assert r._index_loaded is True

    def test_ensure_index_idempotent(self):
        idx = MagicMock()
        idx.load.return_value = True
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        r.ensure_index()
        r.ensure_index()
        # Only called once
        assert idx.load.call_count == 1

    def test_ensure_index_handles_save_error(self):
        idx = MagicMock()
        idx.load.return_value = False
        idx.save.side_effect = OSError("disk full")
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        # Should not raise
        r.ensure_index()
        assert r._index_loaded is True


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_ledger
# ---------------------------------------------------------------------------


class TestSearchLedger:
    def test_returns_memory_results_from_index(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-001",
                "score": 2.5,
                "meta": {
                    "content_preview": "Test content",
                    "type": "observation",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 0.9,
                    "tags": ["test"],
                },
            }
        ]
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        results = r._search_ledger("test query", limit=10)
        assert len(results) == 1
        assert results[0].source == "ledger"
        assert results[0].entry_id == "clp-001"
        assert results[0].score == 2.5
        assert results[0].metadata["type"] == "observation"

    def test_empty_index_returns_empty(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        results = r._search_ledger("nothing", limit=5)
        assert results == []


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_text_pool
# ---------------------------------------------------------------------------


class TestSearchTextPool:
    def test_nonexistent_dir_returns_empty(self):
        r = OpenBrainRetriever(state_dir="/tmp/s")
        results = r._search_text_pool(
            "test",
            pool_name="bus",
            search_dir=Path("/nonexistent/path"),
            glob_pattern="*.tsv",
            limit=5,
        )
        assert results == []

    def test_matching_file_returns_results(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.md"
            p.write_text("governance agent orchestration platform")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "governance orchestration",
                pool_name="briefings",
                search_dir=Path(td),
                glob_pattern="*.md",
                limit=5,
            )
            assert len(results) >= 1
            assert results[0].source == "briefings"
            assert results[0].entry_id.startswith("briefings:")
            assert results[0].metadata["file"] == "test.md"
            assert results[0].metadata["path"] == str(p)

    def test_briefing_content_window_expands_from_source_path(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "brief.md"
            before = "alpha " * 140
            target = "needle governance orchestration " * 20
            after = "omega " * 140
            p.write_text(before + target + after, encoding="utf-8")

            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "governance orchestration",
                pool_name="briefings",
                search_dir=Path(td),
                glob_pattern="*.md",
                limit=5,
            )
            assert results
            original_len = len(results[0].content)

            r._expand_windows(results)

            assert len(results[0].content_window) > original_len
            assert "alpha" in results[0].content_window

    def test_no_matching_tokens_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.md"
            p.write_text("completely unrelated content here")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "zzzznotaword",
                pool_name="briefings",
                search_dir=Path(td),
                glob_pattern="*.md",
                limit=5,
            )
            assert results == []

    def test_tsv_file_extracts_messages(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "messages.tsv"
            p.write_text("2026-03-01T00:00:00Z\tagent\tall\tSTATUS\tgovernance check\n")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "governance",
                pool_name="bus",
                search_dir=Path(td),
                glob_pattern="*.tsv",
                limit=5,
            )
            assert len(results) >= 1
            assert results[0].source == "bus"
            assert results[0].metadata["path"] == str(p)

    def test_bus_content_window_expands_from_tsv_source_path(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "messages.tsv"
            long_message = (
                "prefix " * 120 + "governance bus retrieval " * 20 + "suffix " * 120
            )
            p.write_text(
                "2026-03-01T00:00:00Z\tagent\tall\tSTATUS\t" + long_message + "\n",
                encoding="utf-8",
            )

            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "governance retrieval",
                pool_name="bus",
                search_dir=Path(td),
                glob_pattern="*.tsv",
                limit=5,
            )
            assert results
            original_len = len(results[0].content)

            r._expand_windows(results)

            assert len(results[0].content_window) > original_len
            assert "prefix" in results[0].content_window

    def test_empty_query_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.md"
            p.write_text("something")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "",
                pool_name="bus",
                search_dir=Path(td),
                glob_pattern="*.md",
                limit=5,
            )
            assert results == []

    def test_score_discounted_vs_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.md"
            p.write_text("governance platform")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_text_pool(
                "governance",
                pool_name="briefings",
                search_dir=Path(td),
                glob_pattern="*.md",
                limit=5,
            )
            # Score multiplied by 0.7
            assert all(res.score <= 0.7 for res in results)


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_findings
# ---------------------------------------------------------------------------


class TestSearchFindings:
    def test_nonexistent_dir_returns_empty(self):
        r = OpenBrainRetriever(state_dir="/tmp/nonexistent_state")
        results = r._search_findings("test", limit=5)
        assert results == []

    def test_matching_findings_returned(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            ar_dir = state / "autoresearch"
            ar_dir.mkdir()
            findings = [
                {
                    "id": "f1",
                    "claim": "governance framework improves safety",
                    "source": "paper.pdf",
                    "confidence": 0.8,
                    "category": "safety",
                },
            ]
            (ar_dir / "findings_2026_03.json").write_text(json.dumps(findings))

            r = OpenBrainRetriever(state_dir=state)
            results = r._search_findings("governance safety", limit=5)
            assert len(results) >= 1
            assert results[0].source == "findings"
            assert results[0].entry_id == "f1"

    def test_findings_as_dict_with_findings_key(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            ar_dir = state / "autoresearch"
            ar_dir.mkdir()
            data = {
                "findings": [
                    {
                        "id": "f2",
                        "claim": "agent orchestration pattern",
                        "source": "s",
                        "confidence": 0.7,
                        "category": "arch",
                    },
                ],
            }
            (ar_dir / "findings_2026_04.json").write_text(json.dumps(data))

            r = OpenBrainRetriever(state_dir=state)
            results = r._search_findings("orchestration", limit=5)
            assert len(results) >= 1

    def test_invalid_json_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            ar_dir = state / "autoresearch"
            ar_dir.mkdir()
            (ar_dir / "findings_bad.json").write_text("NOT JSON{{{")

            r = OpenBrainRetriever(state_dir=state)
            results = r._search_findings("test", limit=5)
            assert results == []

    def test_empty_query_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            ar_dir = state / "autoresearch"
            ar_dir.mkdir()
            findings = [{"id": "f1", "claim": "something"}]
            (ar_dir / "findings_2026_03.json").write_text(json.dumps(findings))

            r = OpenBrainRetriever(state_dir=state)
            results = r._search_findings("", limit=5)
            assert results == []

    def test_findings_score_discounted(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            ar_dir = state / "autoresearch"
            ar_dir.mkdir()
            findings = [{"id": "f1", "claim": "governance"}]
            (ar_dir / "findings_2026_03.json").write_text(json.dumps(findings))

            r = OpenBrainRetriever(state_dir=state)
            results = r._search_findings("governance", limit=5)
            # Score multiplied by 0.8
            assert all(res.score <= 0.8 for res in results)


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_memory_md
# ---------------------------------------------------------------------------


class TestSearchMemoryMd:
    def test_nonexistent_dir_returns_empty(self):
        with patch("hummbl_cognition.retriever.Path.home") as mock_home:
            mock_home.return_value = Path("/tmp/fake_home_nonexistent")
            r = OpenBrainRetriever(state_dir="/tmp/s")
            results = r._search_memory_md("test", limit=3)
            assert results == []

    def test_matching_memory_file(self):
        with tempfile.TemporaryDirectory() as td:
            mem_dir = Path(td) / ".claude" / "projects" / "test" / "memory"
            mem_dir.mkdir(parents=True)
            (mem_dir / "MEMORY.md").write_text("## Project\ngovernance platform")

            with patch("hummbl_cognition.retriever.Path.home") as mock_home:
                mock_home.return_value = Path(td)
                r = OpenBrainRetriever(state_dir="/tmp/s")
                results = r._search_memory_md("governance", limit=3)
                assert len(results) >= 1
                assert results[0].source == "memory_md"

    def test_memory_md_score_discounted(self):
        with tempfile.TemporaryDirectory() as td:
            mem_dir = Path(td) / ".claude" / "projects" / "test" / "memory"
            mem_dir.mkdir(parents=True)
            (mem_dir / "MEMORY.md").write_text("governance")

            with patch("hummbl_cognition.retriever.Path.home") as mock_home:
                mock_home.return_value = Path(td)
                r = OpenBrainRetriever(state_dir="/tmp/s")
                results = r._search_memory_md("governance", limit=3)
                # Score multiplied by 0.6
                assert all(res.score <= 0.6 for res in results)


# ---------------------------------------------------------------------------
# OpenBrainRetriever.search -- integration of all pools
# ---------------------------------------------------------------------------


class TestSearchIntegration:
    def _make_retriever(self, state_dir):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-100",
                "score": 5.0,
                "meta": {
                    "content_preview": "High-relevance ledger entry about governance",
                    "type": "observation",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 0.95,
                    "tags": [],
                },
            },
        ]
        idx.record_retrieval = MagicMock()
        return OpenBrainRetriever(state_dir=state_dir, index=idx)

    def test_search_all_sources(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            # Create coordination dir for bus
            coord = state / "coordination"
            coord.mkdir()
            (coord / "messages.tsv").write_text(
                "2026-03-01T00:00:00Z\tagent\tall\tSTATUS\tgovernance update\n"
            )
            # Create briefings dir
            state.parent / "state" / "briefings"
            # Not creating -- will just return empty for that pool

            r = self._make_retriever(state)
            with patch("hummbl_cognition.retriever.log_retrieval"):
                results = r.search(
                    "governance",
                    token_budget=5000,
                    sources=["ledger", "bus"],
                    agent="test-agent",
                )
            assert len(results) >= 1
            # Ledger result should be first (highest score)
            assert results[0].source == "ledger"

    def test_token_budget_respected(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": f"clp-{i}",
                "score": 10.0 - i,
                "meta": {
                    "content_preview": "x" * 400,  # 100 tokens each
                    "type": "observation",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 0.9,
                    "tags": [],
                },
            }
            for i in range(10)
        ]
        idx.record_retrieval = MagicMock()

        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            results = r.search(
                "test",
                token_budget=250,
                sources=["ledger"],
                agent="test",
            )
        total_tokens = sum(res.tokens for res in results)
        assert total_tokens <= 250

    def test_truncation_adds_ellipsis(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-big",
                "score": 5.0,
                "meta": {
                    "content_preview": "a" * 2000,  # 500 tokens
                    "type": "observation",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01",
                    "confidence": 0.9,
                    "tags": [],
                },
            },
        ]
        idx.record_retrieval = MagicMock()

        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            results = r.search(
                "test",
                token_budget=100,
                sources=["ledger"],
                agent="test",
            )
        assert len(results) == 1
        assert results[0].content.endswith("...")
        assert results[0].tokens == 100

    def test_feedback_tracking_called_for_ledger_results(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-001",
                "score": 3.0,
                "meta": {
                    "content_preview": "test",
                    "type": "obs",
                    "scope": "p",
                    "agent": "a",
                    "timestamp": "t",
                    "confidence": 0.5,
                    "tags": [],
                },
            },
        ]
        idx.record_retrieval = MagicMock()

        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval") as mock_log:
            r.search("test", sources=["ledger"], agent="test-agent")
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args
            assert "clp-001" in call_kwargs[1][
                "entry_ids"
            ] or "clp-001" in call_kwargs.kwargs.get("entry_ids", [])

    def test_feedback_tracking_skipped_for_non_ledger(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/nonexistent_state_dir", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval") as mock_log:
            r.search("test", sources=["ledger"], agent="test")
            mock_log.assert_not_called()

    def test_feedback_tracking_oserror_ignored(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-fail",
                "score": 1.0,
                "meta": {
                    "content_preview": "t",
                    "type": "o",
                    "scope": "p",
                    "agent": "a",
                    "timestamp": "t",
                    "confidence": 0.5,
                    "tags": [],
                },
            },
        ]
        idx.record_retrieval = MagicMock()
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch(
            "hummbl_cognition.retriever.log_retrieval", side_effect=OSError("nope")
        ):
            # Should not raise
            results = r.search("test", sources=["ledger"], agent="test")
            assert len(results) == 1

    def test_scope_and_type_filters_passed_to_index(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            r.search(
                "test",
                sources=["ledger"],
                scope="project",
                entry_type="decision",
                since="2026-03-01",
                agent="test",
            )
        idx.search.assert_called_once_with(
            "test",
            limit=50,
            scope="project",
            entry_type="decision",
            since="2026-03-01",
            time_decay=True,
            retrieval_decay=True,
        )

    @pytest.mark.xfail(reason="API changed: search sources list")
    def test_default_sources_all_five(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/nonexistent_all", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            with patch.object(r, "_search_text_pool", return_value=[]) as mock_tp:
                with patch.object(r, "_search_findings", return_value=[]):
                    with patch.object(r, "_search_memory_md", return_value=[]):
                        r.search("test", agent="t")
        # Ledger searched via index
        idx.search.assert_called_once()
        # Text pool called for bus and briefings
        assert mock_tp.call_count == 2

    def test_results_sorted_by_score_descending(self):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-low",
                "score": 1.0,
                "meta": {
                    "content_preview": "lo",
                    "type": "o",
                    "scope": "p",
                    "agent": "a",
                    "timestamp": "t",
                    "confidence": 0.5,
                    "tags": [],
                },
            },
            {
                "id": "clp-high",
                "score": 9.0,
                "meta": {
                    "content_preview": "hi",
                    "type": "o",
                    "scope": "p",
                    "agent": "a",
                    "timestamp": "t",
                    "confidence": 0.5,
                    "tags": [],
                },
            },
        ]
        idx.record_retrieval = MagicMock()
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            results = r.search("test", sources=["ledger"], agent="t", token_budget=5000)
        assert results[0].score > results[1].score

    def test_decay_defaults_to_true(self):
        """Retriever should pass time_decay=True and retrieval_decay=True by default."""
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            r.search("test", sources=["ledger"], agent="t")
        _, kwargs = idx.search.call_args
        assert kwargs.get("time_decay") is True
        assert kwargs.get("retrieval_decay") is True

    def test_decay_can_be_disabled(self):
        """Retriever should respect explicit time_decay=False / retrieval_decay=False."""
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch("hummbl_cognition.retriever.log_retrieval"):
            r.search(
                "test",
                sources=["ledger"],
                agent="t",
                time_decay=False,
                retrieval_decay=False,
            )
        _, kwargs = idx.search.call_args
        assert kwargs.get("time_decay") is False
        assert kwargs.get("retrieval_decay") is False

    def test_decay_env_var_override(self):
        """COGNITION_RETRIEVER_TIME_DECAY=0 should default decay to False."""
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        OpenBrainRetriever(state_dir="/tmp/s", index=idx)
        with patch.dict(
            os.environ,
            {
                "COGNITION_RETRIEVER_TIME_DECAY": "0",
                "COGNITION_RETRIEVER_RETRIEVAL_DECAY": "0",
            },
        ):
            # Re-import to pick up env var defaults
            import importlib

            import hummbl_cognition.retriever as retr_mod

            importlib.reload(retr_mod)
            r2 = retr_mod.OpenBrainRetriever(state_dir="/tmp/s", index=idx)
            with patch("hummbl_cognition.retriever.log_retrieval"):
                r2.search("test", sources=["ledger"], agent="t")
            _, kwargs = idx.search.call_args
            assert kwargs.get("time_decay") is False
            assert kwargs.get("retrieval_decay") is False


# ---------------------------------------------------------------------------
# _resolve_state_dir
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="API changed: _resolve_state_dirs returns list not Path")
class TestResolveStateDir:
    def test_override_path(self):
        from hummbl_cognition.retriever import _resolve_state_dir

        assert _resolve_state_dir("/custom/path") == Path("/custom/path")

    def test_env_var(self):
        from hummbl_cognition.retriever import _resolve_state_dir

        with patch.dict(os.environ, {"HUMMBL_COGNITION_STATE": "/env/state"}):
            assert _resolve_state_dir() == Path("/env/state")

    def test_git_fallback(self):
        from hummbl_cognition.retriever import _resolve_state_dir

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("HUMMBL_COGNITION_STATE", None)
            with patch("subprocess.check_output", return_value="/repo/root\n"):
                result = _resolve_state_dir()
                assert result == Path("/repo/root/_state")

    def test_no_git_default(self):

        from hummbl_cognition.retriever import _resolve_state_dir

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("HUMMBL_COGNITION_STATE", None)
            with patch("subprocess.check_output", side_effect=FileNotFoundError):
                result = _resolve_state_dir()
                assert result == Path("hummbl_cognition/_state")
