"""Tests for hummbl_cognition.retriever -- OpenBrainRetriever.

Covers:
- MemoryResult construction and serialization
- Token estimation
- State dir resolution
- Search with token budgeting
- Ledger pool search via mocked BM25Index
- Text pool search (bus TSV, briefings)
- Findings search (autoresearch JSON)
- Memory MD search
- TSV message extraction
- Snippet extraction
- Source filtering
- Feedback tracking integration
- Edge cases (missing dirs, empty queries, malformed data)
"""

from __future__ import annotations

import json
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
from hummbl_cognition.retriever import (
    _resolve_state_dirs as _resolve_state_dir,
)

# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_short_string(self):
        assert _estimate_tokens("hi") == 1  # 2 chars // 4 = 0 -> max(1,0) = 1

    def test_typical_string(self):
        text = "a" * 100
        assert _estimate_tokens(text) == 25

    def test_empty_string(self):
        assert _estimate_tokens("") == 1  # max(1, 0)


# ---------------------------------------------------------------------------
# _resolve_state_dir
# ---------------------------------------------------------------------------


class TestResolveStateDir:
    def test_override_path(self, tmp_path):
        result = _resolve_state_dir(tmp_path / "custom")
        assert result[0] == tmp_path / "custom"

    def test_override_string(self):
        result = _resolve_state_dir("/some/path")
        assert result[0] == Path("/some/path")

    def test_env_var(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HUMMBL_COGNITION_STATE", str(tmp_path / "env_state"))
        result = _resolve_state_dir()
        assert result[0] == tmp_path / "env_state"

    def test_git_root_fallback(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HUMMBL_COGNITION_STATE", raising=False)
        # Create the _state dir so it passes the exists() check
        state_dir = tmp_path / "_state"
        state_dir.mkdir()
        with patch("subprocess.check_output", return_value=str(tmp_path) + "\n"):
            result = _resolve_state_dir()
            assert state_dir in result

    def test_no_git_fallback(self, monkeypatch):
        monkeypatch.delenv("HUMMBL_COGNITION_STATE", raising=False)
        import subprocess

        with patch(
            "subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            result = _resolve_state_dir()
            assert result[0] == Path("_state")


# ---------------------------------------------------------------------------
# MemoryResult
# ---------------------------------------------------------------------------


class TestMemoryResult:
    def test_basic_construction(self):
        r = MemoryResult(
            source="ledger",
            entry_id="clp-123",
            score=0.85,
            content="test content here",
            metadata={"type": "DISCOVERY"},
        )
        assert r.source == "ledger"
        assert r.entry_id == "clp-123"
        assert r.score == 0.85
        assert r.content == "test content here"
        assert r.metadata == {"type": "DISCOVERY"}
        assert r.tokens > 0

    def test_explicit_tokens(self):
        r = MemoryResult(
            source="bus",
            entry_id="bus:1",
            score=0.5,
            content="x",
            metadata={},
            tokens=42,
        )
        assert r.tokens == 42

    def test_auto_token_estimation(self):
        content = "a" * 80
        r = MemoryResult(
            source="bus",
            entry_id="bus:1",
            score=0.5,
            content=content,
            metadata={},
        )
        assert r.tokens == 20  # 80 / 4

    def test_to_dict(self):
        r = MemoryResult(
            source="findings",
            entry_id="f-1",
            score=0.12345,
            content="claim",
            metadata={"k": "v"},
            tokens=10,
        )
        d = r.to_dict()
        assert d["source"] == "findings"
        assert d["entry_id"] == "f-1"
        assert d["score"] == 0.1235  # rounded to 4 decimal places
        assert d["content"] == "claim"
        assert d["metadata"] == {"k": "v"}
        assert d["tokens"] == 10


# ---------------------------------------------------------------------------
# _extract_tsv_messages
# ---------------------------------------------------------------------------


class TestExtractTsvMessages:
    def test_basic_extraction(self):
        tsv = (
            "2026-03-01T00:00:00Z\tagent-a\tall\tSTATUS\thello world\n"
            "2026-03-02T00:00:00Z\tagent-b\tall\tSITREP\tgoodbye world\n"
        )
        result = _extract_tsv_messages(tsv)
        assert "agent-a STATUS hello world" in result
        assert "agent-b SITREP goodbye world" in result

    def test_since_filter(self):
        tsv = (
            "2026-03-01T00:00:00Z\tagent-a\tall\tSTATUS\told message\n"
            "2026-03-10T00:00:00Z\tagent-b\tall\tSITREP\tnew message\n"
        )
        result = _extract_tsv_messages(tsv, since="2026-03-05")
        assert "old message" not in result
        assert "new message" in result

    def test_malformed_lines_skipped(self):
        tsv = "incomplete\tline\n2026-03-01T00:00:00Z\ta\tb\tSTATUS\tok\n"
        result = _extract_tsv_messages(tsv)
        assert "ok" in result
        # The incomplete line should be skipped (< 5 columns)

    def test_max_lines_cap(self):
        lines = [
            f"2026-03-{i:02d}T00:00:00Z\ta\tb\tSTATUS\tmsg{i}" for i in range(1, 31)
        ]
        tsv = "\n".join(lines)
        result = _extract_tsv_messages(tsv, max_lines=5)
        # Should only get last 5
        assert "msg26" in result
        assert "msg30" in result
        assert "msg1" not in result

    def test_empty_input(self):
        assert _extract_tsv_messages("") == ""


# ---------------------------------------------------------------------------
# _extract_snippet
# ---------------------------------------------------------------------------


class TestExtractSnippet:
    def test_finds_relevant_section(self):
        text = (
            "unrelated intro " * 50
            + "important keyword section " * 5
            + "trailing " * 50
        )
        tokens = {"important", "keyword"}
        snippet = _extract_snippet(text, tokens, max_chars=200)
        assert "important" in snippet.lower() or "keyword" in snippet.lower()

    def test_short_text(self):
        text = "hello world"
        tokens = {"hello"}
        snippet = _extract_snippet(text, tokens, max_chars=500)
        assert "hello world" in snippet

    def test_ellipsis_markers(self):
        text = "prefix " * 200 + "target keyword here" + " suffix" * 200
        tokens = {"target", "keyword"}
        snippet = _extract_snippet(text, tokens, max_chars=100)
        # Should have leading ellipsis since best_pos > 0
        assert snippet.startswith("...") or "target" in snippet

    def test_empty_query_tokens(self):
        snippet = _extract_snippet("some text", set(), max_chars=100)
        # With no matching tokens, best_pos stays 0
        assert "some text" in snippet


# ---------------------------------------------------------------------------
# OpenBrainRetriever -- initialization
# ---------------------------------------------------------------------------


class TestRetrieverInit:
    def test_default_init(self, tmp_path):
        r = OpenBrainRetriever(state_dir=tmp_path)
        assert tmp_path in r.state_dirs
        assert r._index_loaded is False

    def test_custom_index(self, tmp_path):
        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        assert r.index is idx


# ---------------------------------------------------------------------------
# OpenBrainRetriever.ensure_index
# ---------------------------------------------------------------------------


class TestEnsureIndex:
    def test_loads_from_disk_if_exists(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        r.ensure_index()
        idx.load.assert_called_once()
        assert r._index_loaded is True

    def test_builds_if_no_saved_index(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = False
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        r.ensure_index()
        idx.build.assert_called_once()
        idx.save.assert_called_once()

    def test_save_failure_non_fatal(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = False
        idx.save.side_effect = OSError("disk full")
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        # Should not raise
        r.ensure_index()
        assert r._index_loaded is True

    def test_idempotent(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        r.ensure_index()
        r.ensure_index()
        # load only called once
        assert idx.load.call_count == 1


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_ledger
# ---------------------------------------------------------------------------


class TestSearchLedger:
    def test_returns_memory_results(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-001",
                "score": 2.5,
                "meta": {
                    "content_preview": "some discovery",
                    "type": "DISCOVERY",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 0.9,
                    "tags": ["ai"],
                },
            },
        ]
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_ledger("test query", limit=10)
        assert len(results) == 1
        assert results[0].source == "ledger"
        assert results[0].entry_id == "clp-001"
        assert results[0].score == 2.5
        assert results[0].metadata["type"] == "DISCOVERY"

    def test_passes_filters_to_index(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        r._search_ledger(
            "query",
            scope="project",
            entry_type="INSIGHT",
            since="2026-03-01",
            limit=5,
        )
        idx.search.assert_called_once_with(
            "query",
            limit=5,
            scope="project",
            entry_type="INSIGHT",
            since="2026-03-01",
            time_decay=False,
            retrieval_decay=False,
        )


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_text_pool
# ---------------------------------------------------------------------------


class TestSearchTextPool:
    def test_finds_matching_files(self, tmp_path):
        pool_dir = tmp_path / "briefings"
        pool_dir.mkdir()
        (pool_dir / "2026-03-01.md").write_text("important briefing about testing")
        (pool_dir / "2026-03-02.md").write_text("nothing relevant here zzzz")

        idx = MagicMock()
        idx.load.return_value = True
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_text_pool(
            "testing important",
            pool_name="briefings",
            search_dir=pool_dir,
            glob_pattern="*.md",
            limit=5,
        )
        assert len(results) >= 1
        assert results[0].source == "briefings"
        assert results[0].entry_id.startswith("briefings:")

    def test_missing_dir_returns_empty(self, tmp_path):
        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_text_pool(
            "query",
            pool_name="bus",
            search_dir=tmp_path / "nonexistent",
            glob_pattern="*.tsv",
            limit=5,
        )
        assert results == []

    def test_tsv_extraction(self, tmp_path):
        bus_dir = tmp_path / "coordination"
        bus_dir.mkdir()
        (bus_dir / "messages.tsv").write_text(
            "2026-03-01T00:00:00Z\tagent\tall\tSTATUS\tdeployment complete\n"
        )

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_text_pool(
            "deployment",
            pool_name="bus",
            search_dir=bus_dir,
            glob_pattern="*.tsv",
            limit=5,
        )
        assert len(results) >= 1

    def test_score_discount(self, tmp_path):
        """Text pool results are discounted by 0.7 vs ledger BM25."""
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        # All query tokens present -> raw score = 1.0, discounted = 0.7
        (pool_dir / "file.md").write_text("alpha beta gamma")

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_text_pool(
            "alpha beta gamma",
            pool_name="test",
            search_dir=pool_dir,
            glob_pattern="*.md",
            limit=5,
        )
        assert len(results) == 1
        assert results[0].score == pytest.approx(0.7, abs=0.1)

    def test_no_overlap_returns_empty(self, tmp_path):
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        (pool_dir / "file.md").write_text("completely unrelated content xyzzy")

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_text_pool(
            "quantum mechanics",
            pool_name="test",
            search_dir=pool_dir,
            glob_pattern="*.md",
            limit=5,
        )
        assert results == []


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_findings
# ---------------------------------------------------------------------------


class TestSearchFindings:
    def test_finds_matching_claims(self, tmp_path):
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        findings = [
            {
                "id": "finding-001",
                "claim": "machine learning improves governance automation",
                "source": "arxiv",
                "confidence": 0.85,
                "category": "ai-governance",
            },
        ]
        (findings_dir / "findings_2026-03-01.json").write_text(json.dumps(findings))

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("governance automation", limit=5)
        assert len(results) == 1
        assert results[0].source == "findings"
        assert results[0].entry_id == "finding-001"
        assert results[0].metadata["confidence"] == 0.85

    def test_dict_format_with_findings_key(self, tmp_path):
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        data = {
            "findings": [
                {"claim": "AI safety research accelerating", "id": "f2"},
            ],
        }
        (findings_dir / "findings_2026-03-02.json").write_text(json.dumps(data))

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("safety research", limit=5)
        assert len(results) == 1

    def test_malformed_json_skipped(self, tmp_path):
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        (findings_dir / "findings_bad.json").write_text("{invalid json")

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("anything", limit=5)
        assert results == []

    def test_missing_dir_returns_empty(self, tmp_path):
        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("query", limit=5)
        assert results == []

    def test_score_discount_findings(self, tmp_path):
        """Findings are discounted by 0.8."""
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        findings = [{"claim": "alpha beta gamma", "id": "f1"}]
        (findings_dir / "findings_1.json").write_text(json.dumps(findings))

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("alpha beta gamma", limit=5)
        assert len(results) == 1
        assert results[0].score == pytest.approx(0.8, abs=0.1)


# ---------------------------------------------------------------------------
# OpenBrainRetriever._search_memory_md
# ---------------------------------------------------------------------------


class TestSearchMemoryMd:
    def test_finds_memory_files(self, tmp_path):
        memory_dir = tmp_path / ".claude" / "projects" / "proj" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text(
            "# Memory\n\nCI infrastructure on nodezero"
        )

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        with patch.object(Path, "home", return_value=tmp_path):
            results = r._search_memory_md("infrastructure nodezero", limit=5)
        assert len(results) >= 1
        assert results[0].source == "memory_md"

    def test_missing_dir_returns_empty(self, tmp_path):
        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        with patch.object(Path, "home", return_value=tmp_path / "nohome"):
            results = r._search_memory_md("anything", limit=5)
        assert results == []

    def test_score_discount_memory(self, tmp_path):
        """Memory MD results are discounted by 0.6."""
        memory_dir = tmp_path / ".claude" / "projects" / "proj" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("alpha beta gamma")

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        with patch.object(Path, "home", return_value=tmp_path):
            results = r._search_memory_md("alpha beta gamma", limit=5)
        assert len(results) == 1
        assert results[0].score == pytest.approx(0.6, abs=0.1)


# ---------------------------------------------------------------------------
# OpenBrainRetriever.search -- full pipeline
# ---------------------------------------------------------------------------


class TestSearch:
    def _make_retriever(self, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-001",
                "score": 3.0,
                "meta": {
                    "content_preview": "high relevance result",
                    "type": "DISCOVERY",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 0.9,
                    "tags": [],
                },
            },
            {
                "id": "clp-002",
                "score": 1.0,
                "meta": {
                    "content_preview": "lower relevance result",
                    "type": "INSIGHT",
                    "scope": "global",
                    "agent": "kimi",
                    "timestamp": "2026-03-02T00:00:00Z",
                    "confidence": 0.5,
                    "tags": [],
                },
            },
        ]
        return OpenBrainRetriever(state_dir=tmp_path, index=idx)

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_returns_sorted_by_score(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        results = r.search("test query", sources=["ledger"], token_budget=10000)
        assert len(results) == 2
        assert results[0].score >= results[1].score

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_token_budget_limits_results(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        # Very small budget -- should only fit first result or truncate
        results = r.search("test query", sources=["ledger"], token_budget=5)
        total_tokens = sum(res.tokens for res in results)
        assert total_tokens <= 5

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_truncation_adds_ellipsis(self, mock_log, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-big",
                "score": 5.0,
                "meta": {
                    "content_preview": "x" * 200,
                    "type": "DISCOVERY",
                    "scope": "project",
                    "agent": "claude",
                    "timestamp": "2026-03-01T00:00:00Z",
                    "confidence": 1.0,
                    "tags": [],
                },
            },
        ]
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r.search("test", sources=["ledger"], token_budget=10)
        assert len(results) == 1
        assert results[0].content.endswith("...")

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_source_filtering(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        # Only search ledger
        results = r.search("test", sources=["ledger"], token_budget=10000)
        # Should only have ledger results
        for res in results:
            assert res.source == "ledger"

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_feedback_tracking_called(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        r.search("test", sources=["ledger"], agent="test-agent", token_budget=10000)
        # Should log retrieval for clp- prefixed entries
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["agent"] == "test-agent"
        assert "clp-001" in call_kwargs["entry_ids"]

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_feedback_tracking_records_retrieval_on_index(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        r.search("test", sources=["ledger"], token_budget=10000)
        # record_retrieval should be called for each clp- entry
        assert r.index.record_retrieval.call_count >= 1

    @patch("hummbl_cognition.retriever.log_retrieval", side_effect=OSError("fail"))
    def test_feedback_tracking_failure_non_fatal(self, mock_log, tmp_path):
        r = self._make_retriever(tmp_path)
        # Should not raise even if feedback logging fails
        results = r.search("test", sources=["ledger"], token_budget=10000)
        assert len(results) >= 1

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_no_feedback_for_non_clp_entries(self, mock_log, tmp_path):
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []

        # Create a briefing that matches
        briefings_dir = tmp_path.parent / "state" / "briefings"
        briefings_dir.mkdir(parents=True)
        (briefings_dir / "2026-03-01.md").write_text("test query content here")

        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        r.search("test query", sources=["briefings"], token_budget=10000)
        # No clp- entries, so log_retrieval should not be called
        mock_log.assert_not_called()

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_default_sources_all(self, mock_log, tmp_path):
        """When no sources specified, all 5 pools are searched."""
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = []
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        # Pin to single state dir so call counts are predictable
        r.state_dirs = [tmp_path]

        with (
            patch.object(r, "_search_ledger", return_value=[]) as m_ledger,
            patch.object(r, "_search_text_pool", return_value=[]) as m_text,
            patch.object(r, "_search_findings", return_value=[]) as m_findings,
            patch.object(r, "_search_memory_md", return_value=[]) as m_memory,
        ):
            r.search("test", token_budget=1000)
            m_ledger.assert_called_once()
            # _search_text_pool called twice (bus + briefings)
            assert m_text.call_count == 2
            m_findings.assert_called_once()
            m_memory.assert_called_once()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_query_text_pool(self, tmp_path):
        """Empty query after tokenization should return empty."""
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        (pool_dir / "file.md").write_text("content")

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        # Stopwords only -> empty token set
        results = r._search_text_pool(
            "the a an",
            pool_name="test",
            search_dir=pool_dir,
            glob_pattern="*.md",
            limit=5,
        )
        assert results == []

    def test_empty_query_findings(self, tmp_path):
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        (findings_dir / "findings_1.json").write_text(json.dumps([{"claim": "test"}]))

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("the a an", limit=5)
        assert results == []

    def test_unreadable_file_in_text_pool(self, tmp_path):
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        bad_file = pool_dir / "bad.md"
        bad_file.write_text("content")
        bad_file.chmod(0o000)

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        try:
            results = r._search_text_pool(
                "content",
                pool_name="test",
                search_dir=pool_dir,
                glob_pattern="*.md",
                limit=5,
            )
            # Should not crash, just skip unreadable files
            assert isinstance(results, list)
        finally:
            bad_file.chmod(0o644)

    def test_findings_with_missing_fields(self, tmp_path):
        """Findings entries missing optional fields should still work."""
        findings_dir = tmp_path / "autoresearch"
        findings_dir.mkdir()
        findings = [
            {"claim": "governance tool released"}
        ]  # No id, source, confidence, category
        (findings_dir / "findings_1.json").write_text(json.dumps(findings))

        idx = MagicMock()
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r._search_findings("governance tool", limit=5)
        assert len(results) == 1
        assert results[0].entry_id.startswith("finding:")

    @patch("hummbl_cognition.retriever.log_retrieval")
    def test_zero_token_budget(self, mock_log, tmp_path):
        """Zero budget should return nothing."""
        idx = MagicMock()
        idx.load.return_value = True
        idx.search.return_value = [
            {
                "id": "clp-001",
                "score": 5.0,
                "meta": {
                    "content_preview": "test",
                    "type": "D",
                    "scope": "p",
                    "agent": "c",
                    "timestamp": "t",
                    "confidence": 1,
                    "tags": [],
                },
            },
        ]
        r = OpenBrainRetriever(state_dir=tmp_path, index=idx)
        results = r.search("test", sources=["ledger"], token_budget=0)
        assert results == []
