"""Unit tests for hummbl_cognition.mcp_server.

Covers: handle_tool dispatch (all 7 tools), get_indexer singleton,
send_response/send_error JSON-RPC helpers, and main() stdin loop.
"""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

# We need to mock the heavy cognition imports before importing the module
# so tests work without a real ledger on disk.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_indexer():
    """Reset the module-level _indexer singleton between tests."""
    import hummbl_cognition.mcp_server as mod

    mod._indexer = None
    mod._index_dirty = False
    yield
    mod._indexer = None
    mod._index_dirty = False


@pytest.fixture
def tmp_state(tmp_path):
    """Create a temporary state directory with ledger and index files."""
    import hummbl_cognition.mcp_server as mod

    ledger_dir = tmp_path / "cognition"
    ledger_dir.mkdir()
    ledger_file = ledger_dir / "ledger.jsonl"
    index_file = ledger_dir / "index.json"

    # Patch module-level paths
    with (
        mock.patch.object(mod, "LEDGER_DIR", ledger_dir),
        mock.patch.object(mod, "LEDGER_FILE", ledger_file),
        mock.patch.object(mod, "INDEX_FILE", index_file),
    ):
        yield {
            "dir": ledger_dir,
            "ledger": ledger_file,
            "index": index_file,
        }


def _write_ledger(path, entries):
    """Helper: write JSONL entries to a ledger file."""
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def test_default_state_paths_share_one_package_relative_root(monkeypatch):
    """Writer, indexer, and MCP must use one default cognition directory."""
    import hummbl_cognition.indexer as indexer
    import hummbl_cognition.ledger_writer as ledger_writer
    import hummbl_cognition.mcp_server as mcp_server

    monkeypatch.delenv("COGNITION_LEDGER", raising=False)
    monkeypatch.delenv("COGNITION_INDEX", raising=False)
    monkeypatch.delenv("CLP_STATE_DIR", raising=False)

    expected_dir = (
        Path(ledger_writer.__file__).resolve().parent.parent / "_state" / "cognition"
    )
    assert ledger_writer._resolve_ledger_path() == expected_dir / "ledger.jsonl"
    assert indexer._resolve_index_path() == expected_dir / "index.json"
    assert expected_dir == mcp_server.LEDGER_DIR


@pytest.mark.allow_ledger_writes
def test_batch_ingest_then_post_is_visible_to_same_process_search(tmp_path):
    """A long-lived MCP process must index entries appended after startup."""
    import hummbl_cognition.mcp_server as mod
    from hummbl_cognition.__main__ import cmd_batch_ingest
    from hummbl_cognition.ledger_writer import post_entry as real_post_entry

    ledger_dir = tmp_path / "cognition"
    ledger_dir.mkdir()
    ledger_file = ledger_dir / "ledger.jsonl"
    index_file = ledger_dir / "index.json"
    source_file = tmp_path / "batch.jsonl"
    source_file.write_text(
        json.dumps(
            {
                "agent": "devin",
                "vendor": "anthropic",
                "model": "claude-sonnet-4-6",
                "type": "discovery",
                "scope": "project",
                "content": "batchmarker seed entry",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    args = SimpleNamespace(
        source=str(source_file),
        ledger=str(ledger_file),
        dry_run=False,
    )

    with (
        mock.patch.object(mod, "LEDGER_DIR", ledger_dir),
        mock.patch.object(mod, "LEDGER_FILE", ledger_file),
        mock.patch.object(mod, "INDEX_FILE", index_file),
        mock.patch.object(mod, "post_entry", real_post_entry),
    ):
        assert cmd_batch_ingest(args) == 0
        initial = mod.handle_tool("ledger_search", {"query": "batchmarker"})
        assert initial["count"] == 1

        posted = mod.handle_tool(
            "ledger_post",
            {
                "title": "Live append",
                "content": "liveappendmarker must be searchable immediately",
                "entry_type": "discovery",
                "agent": "codex",
                "vendor": "openai",
                "model": "gpt-5",
            },
        )
        assert posted["posted"] is True

        after_post = mod.handle_tool(
            "ledger_search",
            {"query": "liveappendmarker"},
        )
        assert after_post["count"] == 1
        assert after_post["results"][0]["doc_id"] == posted["id"]

        with mock.patch.object(
            mod._indexer,
            "build",
            wraps=mod._indexer.build,
        ) as rebuild:
            repeated = mod.handle_tool(
                "ledger_search",
                {"query": "liveappendmarker"},
            )
        assert repeated["count"] == 1
        rebuild.assert_not_called()


# ---------------------------------------------------------------------------
# get_indexer
# ---------------------------------------------------------------------------


class TestGetIndexer:
    def test_creates_singleton(self):
        import hummbl_cognition.mcp_server as mod

        with (
            mock.patch.object(mod, "INDEX_FILE", Path("/nonexistent/index.json")),
            mock.patch.object(mod, "LEDGER_FILE", Path("/nonexistent/ledger.jsonl")),
        ):
            with mock.patch("hummbl_cognition.mcp_server.BM25Index") as MockIdx:
                instance = mock.MagicMock()
                MockIdx.return_value = instance
                result = mod.get_indexer()
                assert result is instance
                MockIdx.assert_called_once()

    def test_returns_same_instance_on_second_call(self):
        import hummbl_cognition.mcp_server as mod

        sentinel = mock.MagicMock()
        mod._indexer = sentinel
        assert mod.get_indexer() is sentinel

    def test_loads_existing_index(self, tmp_path):
        import hummbl_cognition.mcp_server as mod

        index_file = tmp_path / "index.json"
        index_file.write_text("{}")
        ledger_file = tmp_path / "ledger.jsonl"  # does not exist
        with (
            mock.patch.object(mod, "INDEX_FILE", index_file),
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
        ):
            with mock.patch("hummbl_cognition.mcp_server.BM25Index") as MockIdx:
                instance = mock.MagicMock()
                MockIdx.return_value = instance
                mod.get_indexer()
                instance.load.assert_called_once()

    def test_rebuilds_when_ledger_newer_than_index(self, tmp_path):
        """A ledger newer than the index build time triggers a rebuild."""
        import time

        import hummbl_cognition.mcp_server as mod

        ledger_file = tmp_path / "ledger.jsonl"
        index_file = tmp_path / "index.json"

        # Write a ledger with one valid entry
        ledger_file.write_text(
            json.dumps(
                {
                    "id": "clp-test1",
                    "timestamp": "2026-07-13T10:00:00Z",
                    "agent": "devin",
                    "type": "discovery",
                    "scope": "project",
                    "content": "test entry for staleness",
                    "tags": ["test"],
                    "links": [],
                    "confidence": 0.9,
                }
            )
            + "\n"
        )

        # Write a stale index (built before the ledger was modified)
        stale_build_ts = "2026-07-13T09:00:00Z"  # 1 hour before ledger entry
        index_file.write_text(
            json.dumps(
                {
                    "stats": {
                        "total_docs": 0,
                        "avg_doc_length": 0.0,
                        "built_at": stale_build_ts,
                        "entry_count": 0,
                        "term_count": 0,
                    },
                    "inverted_index": {},
                    "doc_lengths": {},
                    "doc_meta": {},
                    "retrieval_counts": {},
                    "retrieval_last_at": {},
                }
            )
        )

        # Make ledger mtime newer than the index build time
        future = time.time() + 100
        import os

        os.utime(ledger_file, (future, future))

        with (
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
            mock.patch.object(mod, "INDEX_FILE", index_file),
        ):
            indexer = mod.get_indexer()
            # Index should have been rebuilt with the new entry
            assert indexer.total_docs == 1
            assert indexer.entry_count == 1
            # Search should find the entry
            results = indexer.search("test", limit=5)
            assert len(results) >= 1
            assert results[0]["id"] == "clp-test1"

    def test_no_rebuild_when_index_current(self, tmp_path):
        """Index should NOT be rebuilt when ledger is older than index build."""
        import os

        import hummbl_cognition.mcp_server as mod

        ledger_file = tmp_path / "ledger.jsonl"
        index_file = tmp_path / "index.json"

        ledger_file.write_text(
            json.dumps(
                {
                    "id": "clp-old1",
                    "timestamp": "2026-07-13T08:00:00Z",
                    "agent": "devin",
                    "type": "discovery",
                    "scope": "project",
                    "content": "old entry",
                    "tags": [],
                    "links": [],
                    "confidence": 0.9,
                }
            )
            + "\n"
        )

        # Index built AFTER the ledger entry — should not trigger rebuild
        fresh_build_ts = "2026-07-13T12:00:00Z"
        index_file.write_text(
            json.dumps(
                {
                    "stats": {
                        "total_docs": 1,
                        "avg_doc_length": 2.0,
                        "built_at": fresh_build_ts,
                        "entry_count": 1,
                        "term_count": 2,
                    },
                    "inverted_index": {"old": [["clp-old1", 1]]},
                    "doc_lengths": {"clp-old1": 2},
                    "doc_meta": {
                        "clp-old1": {
                            "timestamp": "2026-07-13T08:00:00Z",
                            "agent": "devin",
                            "type": "discovery",
                            "scope": "project",
                            "confidence": 0.9,
                            "content_preview": "old entry",
                            "tags": [],
                            "links": [],
                        }
                    },
                    "retrieval_counts": {},
                    "retrieval_last_at": {},
                }
            )
        )

        # Set ledger mtime to before the index build time (12:00 UTC)
        # Use a fixed timestamp well in the past relative to the index build
        from datetime import datetime, timezone

        old_time = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc).timestamp()
        os.utime(ledger_file, (old_time, old_time))

        with (
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
            mock.patch.object(mod, "INDEX_FILE", index_file),
        ):
            indexer = mod.get_indexer()
            # Should load from index without rebuilding
            assert indexer.total_docs == 1
            assert indexer.built_at == fresh_build_ts

    def test_no_rebuild_for_subsecond_ledger_mtime_when_index_file_is_newer(
        self,
        tmp_path,
    ):
        """Whole-second built_at precision must not cause perpetual rebuilds."""
        import os
        from datetime import datetime, timezone

        import hummbl_cognition.mcp_server as mod

        ledger_file = tmp_path / "ledger.jsonl"
        index_file = tmp_path / "index.json"
        ledger_file.write_text("", encoding="utf-8")
        index_file.write_text(
            json.dumps(
                {
                    "stats": {
                        "total_docs": 0,
                        "avg_doc_length": 0.0,
                        "built_at": "2026-07-13T10:00:00Z",
                        "entry_count": 0,
                        "term_count": 0,
                    },
                    "inverted_index": {},
                    "doc_lengths": {},
                    "doc_meta": {},
                    "retrieval_counts": {},
                    "retrieval_last_at": {},
                }
            ),
            encoding="utf-8",
        )

        base = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc).timestamp()
        os.utime(ledger_file, (base + 0.75, base + 0.75))
        os.utime(index_file, (base + 1.0, base + 1.0))

        with (
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
            mock.patch.object(mod, "INDEX_FILE", index_file),
            mock.patch.object(mod.BM25Index, "build", autospec=True) as build,
            mock.patch.object(mod.BM25Index, "save", autospec=True),
        ):
            mod.get_indexer()

        build.assert_not_called()

    def test_rebuilds_when_index_has_no_build_timestamp(self, tmp_path):
        """Index with empty built_at should trigger rebuild."""
        import hummbl_cognition.mcp_server as mod

        ledger_file = tmp_path / "ledger.jsonl"
        index_file = tmp_path / "index.json"

        ledger_file.write_text(
            json.dumps(
                {
                    "id": "clp-rebuild1",
                    "timestamp": "2026-07-13T10:00:00Z",
                    "agent": "devin",
                    "type": "discovery",
                    "scope": "project",
                    "content": "rebuild test entry",
                    "tags": ["rebuild"],
                    "links": [],
                    "confidence": 0.9,
                }
            )
            + "\n"
        )

        # Index with no built_at
        index_file.write_text(
            json.dumps(
                {
                    "stats": {
                        "total_docs": 0,
                        "avg_doc_length": 0.0,
                        "built_at": "",
                        "entry_count": 0,
                        "term_count": 0,
                    },
                    "inverted_index": {},
                    "doc_lengths": {},
                    "doc_meta": {},
                    "retrieval_counts": {},
                    "retrieval_last_at": {},
                }
            )
        )

        with (
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
            mock.patch.object(mod, "INDEX_FILE", index_file),
        ):
            indexer = mod.get_indexer()
            assert indexer.total_docs == 1
            assert indexer.built_at != ""

    def test_rebuilds_when_built_at_is_malformed(self, tmp_path):
        """Regression: a stale index with a malformed built_at timestamp
        must trigger a rebuild, not silently swallow the ValueError.

        Prior to this fix, _check_and_rebuild_if_stale wrapped the
        datetime.fromisoformat call in `except (ValueError, OSError): pass`,
        so a corrupt built_at string (e.g. "not-a-timestamp") caused the
        staleness check to no-op instead of rebuilding. The result was that
        a stale or corrupt index stayed in place and search returned stale
        or empty results.
        """
        import os
        import time

        import hummbl_cognition.mcp_server as mod

        ledger_file = tmp_path / "ledger.jsonl"
        index_file = tmp_path / "index.json"

        ledger_file.write_text(
            json.dumps(
                {
                    "id": "clp-malformed1",
                    "timestamp": "2026-07-13T10:00:00Z",
                    "agent": "devin",
                    "type": "discovery",
                    "scope": "project",
                    "content": "malformed built_at rebuild test",
                    "tags": ["malformed"],
                    "links": [],
                    "confidence": 0.9,
                }
            )
            + "\n"
        )

        # Index with a malformed built_at — cannot be parsed by fromisoformat.
        # The stats claim 0 docs, so if rebuild is skipped the index will
        # be empty and search will return nothing.
        index_file.write_text(
            json.dumps(
                {
                    "stats": {
                        "total_docs": 0,
                        "avg_doc_length": 0.0,
                        "built_at": "not-a-timestamp",
                        "entry_count": 0,
                        "term_count": 0,
                    },
                    "inverted_index": {},
                    "doc_lengths": {},
                    "doc_meta": {},
                    "retrieval_counts": {},
                    "retrieval_last_at": {},
                }
            )
        )

        # Push ledger mtime into the future so it is definitely newer than
        # any reasonable build time — the rebuild decision must not depend
        # on the unparseable timestamp.
        future = time.time() + 100
        os.utime(ledger_file, (future, future))

        with (
            mock.patch.object(mod, "LEDGER_FILE", ledger_file),
            mock.patch.object(mod, "INDEX_FILE", index_file),
        ):
            indexer = mod.get_indexer()
            # Rebuild must have happened: the entry should be indexed.
            assert indexer.total_docs == 1
            assert indexer.entry_count == 1
            results = indexer.search("malformed", limit=5)
            assert len(results) >= 1
            assert results[0]["id"] == "clp-malformed1"
            # And built_at must now be a valid ISO-8601 string.
            assert indexer.built_at
            assert indexer.built_at != "not-a-timestamp"


# ---------------------------------------------------------------------------
# handle_tool: ledger_search
# ---------------------------------------------------------------------------


class TestLedgerSearch:
    def test_basic_search(self):
        import hummbl_cognition.mcp_server as mod

        mock_indexer = mock.MagicMock()
        mock_indexer.search.return_value = [
            {"id": "doc1", "score": 0.953, "meta": {"agent": "claude-code"}},
            {"id": "doc2", "score": 0.421, "meta": {"agent": "codex"}},
        ]
        with mock.patch.object(mod, "get_indexer", return_value=mock_indexer):
            result = mod.handle_tool("ledger_search", {"query": "hello", "limit": 5})
        assert result["query"] == "hello"
        assert result["count"] == 2
        assert result["results"][0]["doc_id"] == "doc1"
        assert result["results"][0]["score"] == 0.953
        assert result["results"][0]["meta"] == {"agent": "claude-code"}
        # Must use limit= (kwarg matching BM25Index.search signature), not k=
        mock_indexer.search.assert_called_once_with("hello", limit=5)

    def test_default_limit(self):
        import hummbl_cognition.mcp_server as mod

        mock_indexer = mock.MagicMock()
        mock_indexer.search.return_value = []
        with mock.patch.object(mod, "get_indexer", return_value=mock_indexer):
            mod.handle_tool("ledger_search", {"query": "test"})
        mock_indexer.search.assert_called_once_with("test", limit=10)

    def test_search_exception_returns_error(self):
        import hummbl_cognition.mcp_server as mod

        mock_indexer = mock.MagicMock()
        mock_indexer.search.side_effect = RuntimeError("index corrupt")
        with mock.patch.object(mod, "get_indexer", return_value=mock_indexer):
            result = mod.handle_tool("ledger_search", {"query": "test"})
        assert "error" in result
        assert "index corrupt" in result["error"]

    def test_search_real_path_no_k_kwarg(self, tmp_path, monkeypatch):
        """Regression: handler must call indexer.search with limit=, not k=.

        Prior to this fix, the handler called `indexer.search(query, k=limit)`,
        which raised TypeError because BM25Index.search takes `limit` (not
        `k`). The error surfaced as 'Search failed: BM25Index.search() got
        an unexpected keyword argument \\'k\\''.
        """
        import hummbl_cognition.mcp_server as mod
        from hummbl_cognition.indexer import BM25Index

        # Fresh empty index; search returns [] for any query without raising.
        idx_path = tmp_path / "index.json"
        real_indexer = BM25Index(str(idx_path))
        with mock.patch.object(mod, "get_indexer", return_value=real_indexer):
            result = mod.handle_tool("ledger_search", {"query": "anything", "limit": 3})
        # No TypeError, clean empty result.
        assert "error" not in result, f"Expected clean result, got: {result}"
        assert result["count"] == 0
        assert result["results"] == []

    def test_search_result_meta_passthrough(self):
        """Result dicts expose doc_id + score + meta."""
        import hummbl_cognition.mcp_server as mod

        mock_indexer = mock.MagicMock()
        mock_indexer.search.return_value = [
            {"id": "x", "score": 1.0, "meta": {"type": "decision"}},
        ]
        with mock.patch.object(mod, "get_indexer", return_value=mock_indexer):
            result = mod.handle_tool("ledger_search", {"query": "q"})
        assert result["results"][0] == {
            "doc_id": "x",
            "score": 1.0,
            "meta": {"type": "decision"},
        }


# ---------------------------------------------------------------------------
# handle_tool: ledger_query
# ---------------------------------------------------------------------------


class TestLedgerQuery:
    def test_query_with_all_filters(self):
        import hummbl_cognition.mcp_server as mod

        mock_entry = mock.MagicMock()
        mock_entry.id = "e1"
        mock_entry.title = "Test"
        mock_entry.content = "Content"
        mock_entry.agent = "claude"
        mock_entry.entry_type = "observation"
        mock_entry.timestamp = "2026-01-01T00:00:00Z"
        mock_entry.confidence = 0.9
        mock_entry.tags = ["ci"]

        with (
            mock.patch(
                "hummbl_cognition.mcp_server.query_entries",
                return_value=iter([mock_entry]),
            ) as mq,
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_query",
                {
                    "agent": "claude",
                    "entry_type": "observation",
                    "scope": "project",
                    "tags": ["ci"],
                    "limit": 5,
                },
            )
        assert result["count"] == 1
        assert result["entries"][0]["id"] == "e1"
        mq.assert_called_once_with(
            ledger_path=str(Path("/fake/ledger.jsonl")),
            agent="claude",
            entry_type="observation",
            scope="project",
            tags=["ci"],
        )

    def test_query_empty_filters(self):
        import hummbl_cognition.mcp_server as mod

        with (
            mock.patch(
                "hummbl_cognition.mcp_server.query_entries", return_value=iter([])
            ) as mq,
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool("ledger_query", {})
        assert result["count"] == 0
        mq.assert_called_once_with(ledger_path=str(Path("/fake/ledger.jsonl")))

    def test_query_respects_limit(self):
        import hummbl_cognition.mcp_server as mod

        entries = [mock.MagicMock() for _ in range(30)]
        for i, e in enumerate(entries):
            e.id = f"e{i}"
            e.title = f"T{i}"
            e.content = "c"
            e.agent = "a"
            e.entry_type = "observation"
            e.timestamp = ""
            e.confidence = 0.5
            e.tags = []

        with (
            mock.patch(
                "hummbl_cognition.mcp_server.query_entries", return_value=iter(entries)
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool("ledger_query", {"limit": 5})
        assert result["count"] == 5

    def test_query_exception(self):
        import hummbl_cognition.mcp_server as mod

        with (
            mock.patch(
                "hummbl_cognition.mcp_server.query_entries",
                side_effect=ValueError("bad"),
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool("ledger_query", {})
        assert "error" in result

    def test_query_content_truncated_to_500(self):
        import hummbl_cognition.mcp_server as mod

        mock_entry = mock.MagicMock()
        mock_entry.id = "e1"
        mock_entry.title = "T"
        mock_entry.content = "x" * 1000
        mock_entry.agent = "a"
        mock_entry.entry_type = "observation"
        mock_entry.timestamp = ""
        mock_entry.confidence = 0.5
        mock_entry.tags = []

        with (
            mock.patch(
                "hummbl_cognition.mcp_server.query_entries",
                return_value=iter([mock_entry]),
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool("ledger_query", {})
        assert len(result["entries"][0]["content"]) == 500


# ---------------------------------------------------------------------------
# handle_tool: ledger_post
# ---------------------------------------------------------------------------


class TestLedgerPost:
    def test_post_success(self):
        import hummbl_cognition.mcp_server as mod

        fake_entry = mock.MagicMock()
        fake_entry.id = "clp-fake123"
        fake_entry.type = "discovery"
        with (
            mock.patch(
                "hummbl_cognition.mcp_server.LedgerEntry.create",
                return_value=fake_entry,
            ) as mc,
            mock.patch(
                "hummbl_cognition.mcp_server.post_entry", return_value=fake_entry
            ) as mp,
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": "My Entry",
                    "content": "Some knowledge",
                    "entry_type": "discovery",
                    "agent": "test-agent",
                    "vendor": "anthropic",
                    "model": "claude-sonnet-4-6",
                    "confidence": 0.8,
                    "tags": ["test"],
                    "scope": "project",
                },
            )
        assert result["posted"] is True
        assert result["id"] == "clp-fake123"
        assert result["title"] == "My Entry"
        assert result["type"] == "discovery"
        mc.assert_called_once()
        ck = mc.call_args.kwargs
        assert ck["agent"] == "test-agent"
        assert ck["vendor"] == "anthropic"
        assert ck["model"] == "claude-sonnet-4-6"
        assert ck["entry_type"] == "discovery"
        assert ck["scope"] == "project"
        assert ck["content"] == "# My Entry\n\nSome knowledge"
        assert ck["confidence"] == 0.8
        assert ck["tags"] == ("test",)
        mp.assert_called_once()
        assert mp.call_args.args == (fake_entry,)
        assert mp.call_args.kwargs["ledger_path"] == str(Path("/fake/ledger.jsonl"))

    def test_post_defaults_with_env_identity(self, monkeypatch):
        import hummbl_cognition.mcp_server as mod

        monkeypatch.setenv("COGNITION_VENDOR", "openai")
        monkeypatch.setenv("COGNITION_MODEL", "gpt-5")
        fake_entry = mock.MagicMock()
        fake_entry.id = "clp-default456"
        fake_entry.type = "discovery"
        with (
            mock.patch(
                "hummbl_cognition.mcp_server.LedgerEntry.create",
                return_value=fake_entry,
            ) as mc,
            mock.patch(
                "hummbl_cognition.mcp_server.post_entry", return_value=fake_entry
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": "T",
                    "content": "C",
                    "entry_type": "discovery",
                },
            )
        assert result["posted"] is True
        assert result["id"] == "clp-default456"
        ck = mc.call_args.kwargs
        assert ck["agent"] == "mcp-client"
        assert ck["vendor"] == "openai"
        assert ck["model"] == "gpt-5"
        assert ck["scope"] == "project"
        assert ck["confidence"] == 0.7
        assert ck["tags"] == ()

    def test_post_missing_identity_returns_schema_error(self, monkeypatch):
        """No vendor/model in args AND no env vars → clear schema error,
        NOT 'Invalid vendor: unknown' from LedgerEntry validator."""
        import hummbl_cognition.mcp_server as mod

        monkeypatch.delenv("COGNITION_VENDOR", raising=False)
        monkeypatch.delenv("COGNITION_MODEL", raising=False)
        # LedgerEntry.create MUST NOT be reached when identity is missing.
        with (
            mock.patch("hummbl_cognition.mcp_server.LedgerEntry.create") as mc,
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": "T",
                    "content": "C",
                    "entry_type": "discovery",
                },
            )
        assert "error" in result
        assert "Missing required identity" in result["error"]
        assert "vendor" in result["error"]
        assert "model" in result["error"]
        assert "COGNITION_VENDOR" in result["error"]
        mc.assert_not_called()

    def test_post_missing_identity_real_path_no_phantom_vendor(
        self, monkeypatch, tmp_path
    ):
        """Real-path regression: with NO mock on LedgerEntry.create, a call
        lacking vendor/model must produce the schema error — never reach the
        validator that would reject 'unknown' with a confusing 'Invalid
        vendor' message."""
        import hummbl_cognition.mcp_server as mod

        monkeypatch.delenv("COGNITION_VENDOR", raising=False)
        monkeypatch.delenv("COGNITION_MODEL", raising=False)
        with mock.patch.object(mod, "LEDGER_FILE", tmp_path / "ledger.jsonl"):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": "T",
                    "content": "C",
                    "entry_type": "discovery",
                },
            )
        assert "error" in result
        assert "Missing required identity" in result["error"]
        assert "Invalid vendor" not in result["error"]
        assert not (tmp_path / "ledger.jsonl").exists()

    def test_post_missing_required_returns_schema_error(self):
        import hummbl_cognition.mcp_server as mod

        # Missing content + entry_type — should NOT reach LedgerEntry.create
        with (
            mock.patch("hummbl_cognition.mcp_server.LedgerEntry.create") as mc,
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool("ledger_post", {"title": "T"})
        assert "error" in result
        assert "Missing required" in result["error"]
        assert "content" in result["error"]
        assert "entry_type" in result["error"]
        mc.assert_not_called()

    def test_post_null_title_does_not_crash(self):
        import hummbl_cognition.mcp_server as mod

        fake_entry = mock.MagicMock()
        fake_entry.id = "clp-null789"
        fake_entry.type = "decision"
        with (
            mock.patch(
                "hummbl_cognition.mcp_server.LedgerEntry.create",
                return_value=fake_entry,
            ) as mc,
            mock.patch(
                "hummbl_cognition.mcp_server.post_entry", return_value=fake_entry
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": None,
                    "content": "body only",
                    "entry_type": "decision",
                    "vendor": "anthropic",
                    "model": "claude-sonnet-4-6",
                },
            )
        assert result["posted"] is True
        # Empty title → no `# title\n\n` prefix added
        assert mc.call_args.kwargs["content"] == "body only"

    def test_post_coerces_non_string_tags(self):
        import hummbl_cognition.mcp_server as mod

        fake_entry = mock.MagicMock()
        fake_entry.id = "clp-tags001"
        fake_entry.type = "discovery"
        with (
            mock.patch(
                "hummbl_cognition.mcp_server.LedgerEntry.create",
                return_value=fake_entry,
            ) as mc,
            mock.patch(
                "hummbl_cognition.mcp_server.post_entry", return_value=fake_entry
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            mod.handle_tool(
                "ledger_post",
                {
                    "title": "T",
                    "content": "C",
                    "entry_type": "discovery",
                    "tags": [1, 2, "three"],
                    "vendor": "anthropic",
                    "model": "claude-sonnet-4-6",
                },
            )
        assert mc.call_args.kwargs["tags"] == ("1", "2", "three")

    def test_post_exception(self):
        import hummbl_cognition.mcp_server as mod

        fake_entry = mock.MagicMock()
        with (
            mock.patch(
                "hummbl_cognition.mcp_server.LedgerEntry.create",
                return_value=fake_entry,
            ),
            mock.patch(
                "hummbl_cognition.mcp_server.post_entry",
                side_effect=IOError("disk full"),
            ),
            mock.patch.object(mod, "LEDGER_FILE", Path("/fake/ledger.jsonl")),
        ):
            result = mod.handle_tool(
                "ledger_post",
                {
                    "title": "T",
                    "content": "C",
                    "entry_type": "discovery",
                    "vendor": "anthropic",
                    "model": "claude-sonnet-4-6",
                },
            )
        assert "error" in result
        assert "disk full" in result["error"]


# ---------------------------------------------------------------------------
# handle_tool: ledger_stats
# ---------------------------------------------------------------------------


class TestLedgerStats:
    def test_stats_with_entries(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [
            {"agent": "claude", "entry_type": "observation"},
            {"agent": "claude", "entry_type": "decision"},
            {"agent": "kimi-1", "entry_type": "observation"},
        ]
        _write_ledger(tmp_state["ledger"], entries)
        # Create a fake index file
        tmp_state["index"].write_text("{}")

        result = mod.handle_tool("ledger_stats", {})
        assert result["total_entries"] == 3
        assert result["agents"]["claude"] == 2
        assert result["agents"]["kimi-1"] == 1
        assert result["types"]["observation"] == 2
        assert result["types"]["decision"] == 1
        assert result["index"]["exists"] is True
        assert result["index"]["status"] == "healthy"

    def test_stats_no_ledger(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        # ledger file doesn't exist
        result = mod.handle_tool("ledger_stats", {})
        assert result["total_entries"] == 0
        assert result["index"]["exists"] is False
        assert "missing" in result["index"]["status"]

    def test_stats_malformed_jsonl(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        with open(tmp_state["ledger"], "w") as f:
            f.write('{"agent": "claude", "entry_type": "observation"}\n')
            f.write("NOT VALID JSON\n")
            f.write('{"agent": "kimi-1", "entry_type": "finding"}\n')
        result = mod.handle_tool("ledger_stats", {})
        # Malformed line is skipped
        assert result["total_entries"] == 2

    def test_stats_uses_type_fallback(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [{"agent": "a", "type": "convention"}]
        _write_ledger(tmp_state["ledger"], entries)
        result = mod.handle_tool("ledger_stats", {})
        assert result["types"]["convention"] == 1

    def test_stats_unknown_agent_and_type(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [{}]  # no agent, no type
        _write_ledger(tmp_state["ledger"], entries)
        result = mod.handle_tool("ledger_stats", {})
        assert result["agents"]["unknown"] == 1
        assert result["types"]["unknown"] == 1


# ---------------------------------------------------------------------------
# handle_tool: boot_context
# ---------------------------------------------------------------------------


class TestBootContext:
    def test_boot_context_success(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        mock_context = {"entries": [{"title": "boot"}]}
        mbc = mock.MagicMock(return_value=mock_context)
        with mock.patch.dict(
            "sys.modules",
            {"hummbl_cognition.boot_context": mock.MagicMock(build_boot_context=mbc)},
        ):
            result = mod.handle_tool("boot_context", {"max_entries": 5})
        assert result["boot_context"] == mock_context
        # Regression guard: handler MUST pass cognition_dir + max_entries,
        # NOT ledger_path / index_path (those kwargs were dropped by the
        # boot_context refactor and triggered TypeError before this fix).
        assert mbc.call_count == 1
        _, kwargs = mbc.call_args
        assert "cognition_dir" in kwargs
        assert kwargs["max_entries"] == 5
        assert "ledger_path" not in kwargs
        assert "index_path" not in kwargs

    def test_boot_context_real_path_no_unexpected_kwarg(self, tmp_state):
        """Regression: real build_boot_context must accept handler's kwargs.

        Prior to this fix, the handler passed ledger_path= and index_path=,
        which build_boot_context() does not accept; the call raised
        'build_boot_context() got an unexpected keyword argument
        \\'ledger_path\\''. This test exercises the real function.
        """
        import hummbl_cognition.mcp_server as mod

        # tmp_state fixture already points LEDGER_DIR / LEDGER_FILE / INDEX_FILE
        # at a tmp_path cognition dir; build_boot_context will resolve cleanly.
        result = mod.handle_tool("boot_context", {"max_entries": 3})
        assert "error" not in result, f"Expected clean result, got: {result}"
        assert "boot_context" in result
        # Output is markdown-formatted string per build_boot_context contract.
        assert isinstance(result["boot_context"], str)

    def test_boot_context_import_error_fallback(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [
            {"title": "Entry1", "content": "C1"},
            {"title": "Entry2", "content": "C2"},
        ]
        _write_ledger(tmp_state["ledger"], entries)

        # Make the import of boot_context fail
        real_import = (
            __builtins__.__import__
            if hasattr(__builtins__, "__import__")
            else __import__
        )

        def fail_import(name, *args, **kwargs):
            if "boot_context" in name:
                raise ImportError("no boot_context")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fail_import):
            result = mod.handle_tool("boot_context", {"max_entries": 10})
        assert result["count"] == 2
        assert result["entries"][0]["title"] == "Entry1"

    def test_boot_context_fallback_respects_limit(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [{"title": f"E{i}", "content": f"C{i}"} for i in range(20)]
        _write_ledger(tmp_state["ledger"], entries)

        def fail_import(name, *args, **kwargs):
            if "boot_context" in name:
                raise ImportError("no boot_context")
            return __import__(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fail_import):
            result = mod.handle_tool("boot_context", {"max_entries": 5})
        assert result["count"] == 5

    def test_boot_context_fallback_truncates_content(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [{"title": "T", "content": "x" * 500}]
        _write_ledger(tmp_state["ledger"], entries)

        def fail_import(name, *args, **kwargs):
            if "boot_context" in name:
                raise ImportError("no boot_context")
            return __import__(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fail_import):
            result = mod.handle_tool("boot_context", {})
        assert len(result["entries"][0]["content"]) == 300


# ---------------------------------------------------------------------------
# handle_tool: reindex
# ---------------------------------------------------------------------------


class TestReindex:
    def test_reindex_success(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        entries = [
            {"title": "T1", "content": "C1", "tags": ["a"]},
            {"title": "T2", "content": "C2", "tags": []},
        ]
        _write_ledger(tmp_state["ledger"], entries)

        with mock.patch("hummbl_cognition.mcp_server.BM25Index") as mock_cls:
            mock_idx = mock_cls.return_value
            result = mod.handle_tool("reindex", {})
        assert result["reindexed"] is True
        assert result["entries_indexed"] == 2
        assert mock_idx.add_document.call_count == 2
        mock_idx.save.assert_called_once()
        # Singleton should be updated
        assert mod._indexer is mock_idx

    def test_reindex_no_ledger(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        with mock.patch("hummbl_cognition.mcp_server.BM25Index"):
            result = mod.handle_tool("reindex", {})
        assert result["reindexed"] is True
        assert result["entries_indexed"] == 0

    def test_reindex_skips_bad_json(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        with open(tmp_state["ledger"], "w") as f:
            f.write('{"title":"T1","content":"C1","tags":[]}\n')
            f.write("BAD LINE\n")
        with mock.patch("hummbl_cognition.mcp_server.BM25Index") as mock_cls:
            mock_idx = mock_cls.return_value
            result = mod.handle_tool("reindex", {})
        assert result["entries_indexed"] == 1
        assert mock_idx.add_document.call_count == 1

    def test_reindex_exception(self, tmp_state):
        import hummbl_cognition.mcp_server as mod

        with mock.patch(
            "hummbl_cognition.mcp_server.BM25Index", side_effect=RuntimeError("boom")
        ):
            result = mod.handle_tool("reindex", {})
        assert "error" in result
        assert "error" in result  # reindex failure captured


# ---------------------------------------------------------------------------
# handle_tool: unknown tool
# ---------------------------------------------------------------------------


class TestUnknownTool:
    def test_unknown_tool_returns_error(self):
        import hummbl_cognition.mcp_server as mod

        result = mod.handle_tool("nonexistent_tool", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------


class TestJsonRpcHelpers:
    def test_send_response(self):
        import hummbl_cognition.mcp_server as mod

        buf = StringIO()
        with mock.patch.object(sys, "stdout", buf):
            mod.send_response(42, {"key": "value"})
        line = buf.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == 42
        assert parsed["result"] == {"key": "value"}

    def test_send_error(self):
        import hummbl_cognition.mcp_server as mod

        buf = StringIO()
        with mock.patch.object(sys, "stdout", buf):
            mod.send_error(7, -32601, "Method not found")
        line = buf.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == 7
        assert parsed["error"]["code"] == -32601
        assert parsed["error"]["message"] == "Method not found"


# ---------------------------------------------------------------------------
# TOOLS constant
# ---------------------------------------------------------------------------


class TestToolsDefinitions:
    def test_seven_tools_defined(self):
        import hummbl_cognition.mcp_server as mod

        assert (
            len(mod.TOOLS) == 6
        )  # ledger_search, ledger_query, ledger_post, ledger_stats, boot_context, reindex

    def test_all_tools_have_required_fields(self):
        import hummbl_cognition.mcp_server as mod

        for tool in mod.TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_tool_names(self):
        import hummbl_cognition.mcp_server as mod

        names = {t["name"] for t in mod.TOOLS}
        expected = {
            "ledger_search",
            "ledger_query",
            "ledger_post",
            "ledger_stats",
            "boot_context",
            "reindex",
        }
        assert names == expected


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_server_metadata(self):
        import hummbl_cognition.mcp_server as mod

        assert mod.SERVER_NAME == "cognitive-ledger"
        assert mod.SERVER_VERSION == "0.1.0"
        assert mod.PROTOCOL_VERSION == "2024-11-05"


# ---------------------------------------------------------------------------
# main() JSON-RPC loop
# ---------------------------------------------------------------------------


class TestMain:
    def _run_main(self, messages):
        """Helper to run main() with a list of JSON-RPC messages."""
        import hummbl_cognition.mcp_server as mod

        stdin_text = "\n".join(json.dumps(m) for m in messages) + "\n"
        buf = StringIO()
        with (
            mock.patch.object(mod, "LEDGER_DIR", Path(tempfile.mkdtemp())),
            mock.patch.object(sys, "stdin", StringIO(stdin_text)),
            mock.patch.object(sys, "stdout", buf),
        ):
            mod.main()
        lines = [l for l in buf.getvalue().strip().split("\n") if l]
        return [json.loads(l) for l in lines]

    def test_initialize(self):
        responses = self._run_main(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            ]
        )
        assert len(responses) == 1
        r = responses[0]
        assert r["id"] == 1
        assert r["result"]["protocolVersion"] == "2024-11-05"
        assert r["result"]["serverInfo"]["name"] == "cognitive-ledger"

    def test_tools_list(self):
        responses = self._run_main(
            [
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            ]
        )
        assert len(responses) == 1
        tools = responses[0]["result"]["tools"]
        assert len(tools) == 6

    def test_ping(self):
        responses = self._run_main(
            [
                {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}},
            ]
        )
        assert responses[0]["result"] == {}

    def test_unknown_method(self):
        responses = self._run_main(
            [
                {"jsonrpc": "2.0", "id": 4, "method": "foo/bar", "params": {}},
            ]
        )
        assert "error" in responses[0]
        assert responses[0]["error"]["code"] == -32601

    def test_notifications_initialized_no_response(self):
        responses = self._run_main(
            [
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "method": "notifications/initialized",
                    "params": {},
                },
            ]
        )
        # notifications/initialized should produce no response
        assert len(responses) == 0

    def test_tools_call(self):
        import hummbl_cognition.mcp_server as mod

        with mock.patch.object(mod, "handle_tool", return_value={"ok": True}) as mh:
            responses = self._run_main(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": "tools/call",
                        "params": {"name": "ledger_stats", "arguments": {}},
                    },
                ]
            )
        assert len(responses) == 1
        content = responses[0]["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        payload = json.loads(content[0]["text"])
        assert payload["ok"] is True
        mh.assert_called_once_with("ledger_stats", {})

    def test_blank_lines_skipped(self):
        import hummbl_cognition.mcp_server as mod

        stdin_text = (
            "\n\n"
            + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
            + "\n\n"
        )
        buf = StringIO()
        with (
            mock.patch.object(mod, "LEDGER_DIR", Path(tempfile.mkdtemp())),
            mock.patch.object(sys, "stdin", StringIO(stdin_text)),
            mock.patch.object(sys, "stdout", buf),
        ):
            mod.main()
        lines = [l for l in buf.getvalue().strip().split("\n") if l]
        assert len(lines) == 1

    def test_invalid_json_skipped(self):
        import hummbl_cognition.mcp_server as mod

        stdin_text = (
            "NOT JSON\n"
            + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
            + "\n"
        )
        buf = StringIO()
        with (
            mock.patch.object(mod, "LEDGER_DIR", Path(tempfile.mkdtemp())),
            mock.patch.object(sys, "stdin", StringIO(stdin_text)),
            mock.patch.object(sys, "stdout", buf),
        ):
            mod.main()
        lines = [l for l in buf.getvalue().strip().split("\n") if l]
        assert len(lines) == 1
        assert json.loads(lines[0])["result"] == {}

    def test_internal_error_handling(self):
        import hummbl_cognition.mcp_server as mod

        with mock.patch.object(mod, "send_response", side_effect=RuntimeError("boom")):
            # The except block in main should catch and send_error
            # But send_error itself is not mocked, so we need a different approach.
            # Let's test by making tools/call raise during handle_tool dispatch
            pass

        # Better: test with a method handler that raises
        def bad_send_response(msg_id, result):
            raise RuntimeError("boom")

        stdin_text = (
            json.dumps({"jsonrpc": "2.0", "id": 99, "method": "ping", "params": {}})
            + "\n"
        )
        buf = StringIO()
        with (
            mock.patch.object(mod, "LEDGER_DIR", Path(tempfile.mkdtemp())),
            mock.patch.object(sys, "stdin", StringIO(stdin_text)),
            mock.patch.object(sys, "stdout", buf),
            mock.patch.object(mod, "send_response", side_effect=RuntimeError("boom")),
        ):
            # send_error writes directly to stdout
            mod.main()
        lines = [l for l in buf.getvalue().strip().split("\n") if l]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["error"]["code"] == -32603
        assert "boom" in parsed["error"]["message"]

    def test_multiple_messages(self):
        responses = self._run_main(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}},
            ]
        )
        assert len(responses) == 2
        assert responses[0]["id"] == 1
        assert responses[1]["id"] == 2
