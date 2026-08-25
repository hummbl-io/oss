"""Tests for hummbl_cognition.indexer -- BM25 inverted term index."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_cognition.indexer import (
    _STOPWORDS,
    BM25_B,
    BM25_K1,
    BM25Index,
    RETRIEVAL_DECAY_HALF_LIFE_DAYS,
    TIME_DECAY_HALF_LIFE_DAYS,
    _resolve_index_path,
    tokenize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class FakeLedgerEntry:
    """Minimal stand-in for LedgerEntry used by indexer.build()."""
    id: str
    content: str
    type: str
    scope: str
    agent: str
    tags: tuple[str, ...] = ()
    links: tuple[str, ...] = ()
    timestamp: str = "2026-03-29T10:00:00Z"
    confidence: float = 0.9
    # CLP v1.1 extensions (hash-chaining, bi-temporal, belief-DAG)
    supersedes: str | None = None
    previous_hash: str | None = None
    valid_time: str | None = None
    contests: str | None = None


def _make_entry(
    id: str = "clp-000000000001",
    content: str = "circuit breaker tripped on github adapter",
    type: str = "discovery",
    scope: str = "operational",
    agent: str = "claude-code",
    tags: tuple[str, ...] = ("ci", "resilience"),
    links: tuple[str, ...] = (),
    timestamp: str = "2026-03-29T10:00:00Z",
    confidence: float = 0.9,
    supersedes: str | None = None,
    previous_hash: str | None = None,
    valid_time: str | None = None,
    contests: str | None = None,
) -> FakeLedgerEntry:
    return FakeLedgerEntry(
        id=id, content=content, type=type, scope=scope,
        agent=agent, tags=tags, links=links,
        timestamp=timestamp, confidence=confidence,
        supersedes=supersedes, previous_hash=previous_hash,
        valid_time=valid_time, contests=contests,
    )


SAMPLE_ENTRIES = [
    _make_entry(
        id="clp-aaaaaaaaaaaa",
        content="circuit breaker tripped on github adapter",
        type="discovery",
        scope="operational",
        agent="claude-code",
        tags=("ci", "resilience"),
    ),
    _make_entry(
        id="clp-bbbbbbbbbbbb",
        content="linear adapter latency improved after retry backoff",
        type="decision",
        scope="technical",
        agent="kimi-1",
        tags=("performance",),
    ),
    _make_entry(
        id="clp-cccccccccccc",
        content="google calendar oauth token refresh failing silently",
        type="discovery",
        scope="operational",
        agent="claude-code",
        tags=("auth", "google"),
        timestamp="2026-03-28T08:00:00Z",
    ),
]


# ---------------------------------------------------------------------------
# tokenize()
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_basic_tokenization(self):
        tokens = tokenize("Hello World Test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_stopwords_removed(self):
        tokens = tokenize("the quick brown fox is a test")
        for sw in ("the", "is", "a"):
            assert sw not in tokens
        assert "quick" in tokens
        assert "brown" in tokens

    def test_single_char_removed(self):
        tokens = tokenize("a b c real word")
        assert "real" in tokens
        assert "word" in tokens
        # Single chars filtered
        for c in ("b", "c"):
            assert c not in tokens

    def test_dotted_identifiers_kept(self):
        tokens = tokenize("hummbl_cognition.indexer works well")
        assert "hummbl_cognition.indexer" in tokens

    def test_empty_string(self):
        assert tokenize("") == []

    def test_only_stopwords(self):
        assert tokenize("the and or but") == []

    def test_case_insensitive(self):
        tokens = tokenize("GITHUB Adapter GitHub")
        assert tokens.count("github") == 2
        assert tokens.count("adapter") == 1

    def test_numeric_tokens(self):
        tokens = tokenize("port 8081 and version 3.14")
        assert "8081" in tokens
        assert "port" in tokens
        assert "3.14" in tokens


# ---------------------------------------------------------------------------
# _resolve_index_path()
# ---------------------------------------------------------------------------

class TestResolveIndexPath:
    def test_override_wins(self):
        p = _resolve_index_path("/tmp/my_index.json")
        assert p == Path("/tmp/my_index.json")

    def test_env_var(self):
        with patch.dict(os.environ, {"COGNITION_INDEX": "/tmp/env_index.json"}):
            p = _resolve_index_path()
            assert p == Path("/tmp/env_index.json")

    def test_env_var_ignored_when_override(self):
        with patch.dict(os.environ, {"COGNITION_INDEX": "/tmp/env.json"}):
            p = _resolve_index_path("/tmp/override.json")
            assert p == Path("/tmp/override.json")

    def test_default_resolves_relative_to_package(self):
        """The default path resolves from the package, not a Git workspace."""
        p = _resolve_index_path()
        # Must end with _state/cognition/index.json
        assert p.name == "index.json"
        assert p.parent.name == "cognition"
        assert p.parent.parent.name == "_state"
        # Must be an absolute path
        assert p.is_absolute()

    def test_does_not_use_git_rev_parse(self):
        """The old implementation used ``git rev-parse --show-toplevel``
        which returns the workspace root when the repo is nested. Verify
        the new implementation does not shell out to git."""
        import hummbl_cognition.indexer as idx_mod
        # The resolved path should NOT depend on git
        p = _resolve_index_path()
        # Confirm it matches the __file__-based resolution
        expected = Path(idx_mod.__file__).resolve().parent.parent / "_state" / "cognition" / "index.json"
        assert p == expected


# ---------------------------------------------------------------------------
# BM25Index.build()
# ---------------------------------------------------------------------------

class TestBM25IndexBuild:
    @patch("hummbl_cognition.indexer.read_entries")
    def test_build_empty(self, mock_read):
        mock_read.return_value = []
        idx = BM25Index()
        count = idx.build()
        assert count == 0
        assert idx.total_docs == 0
        assert idx.avg_doc_length == 0.0
        assert idx.built_at != ""

    @patch("hummbl_cognition.indexer.read_entries")
    def test_build_populates_structures(self, mock_read):
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        count = idx.build()
        assert count == 3
        assert idx.total_docs == 3
        assert idx.entry_count == 3
        assert idx.avg_doc_length > 0
        assert len(idx.inverted_index) > 0
        assert len(idx.doc_lengths) == 3
        assert len(idx.doc_meta) == 3

    @patch("hummbl_cognition.indexer.read_entries")
    def test_build_meta_correct(self, mock_read):
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        idx.build()
        meta = idx.doc_meta["clp-aaaaaaaaaaaa"]
        assert meta["agent"] == "claude-code"
        assert meta["type"] == "discovery"
        assert meta["scope"] == "operational"
        assert meta["confidence"] == 0.9
        assert "circuit breaker" in meta["content_preview"]
        assert meta["tags"] == ["ci", "resilience"]

    @patch("hummbl_cognition.indexer.read_entries")
    def test_build_clears_previous(self, mock_read):
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        idx.build()
        assert idx.total_docs == 3
        # Rebuild with empty
        mock_read.return_value = []
        idx.build()
        assert idx.total_docs == 0
        assert len(idx.inverted_index) == 0

    @patch("hummbl_cognition.indexer.read_entries")
    def test_inverted_index_terms(self, mock_read):
        mock_read.return_value = [SAMPLE_ENTRIES[0]]
        idx = BM25Index()
        idx.build()
        # "circuit" should be in the inverted index
        assert "circuit" in idx.inverted_index
        postings = idx.inverted_index["circuit"]
        assert any(doc_id == "clp-aaaaaaaaaaaa" for doc_id, _ in postings)


# ---------------------------------------------------------------------------
# BM25Index.search()
# ---------------------------------------------------------------------------

class TestBM25IndexSearch:
    @pytest.fixture()
    def populated_index(self):
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = SAMPLE_ENTRIES
            idx = BM25Index()
            idx.build()
        return idx

    def test_search_returns_results(self, populated_index):
        results = populated_index.search("circuit breaker")
        assert len(results) > 0
        assert results[0]["id"] == "clp-aaaaaaaaaaaa"

    def test_search_empty_query(self, populated_index):
        # All stopwords -> empty tokens
        assert populated_index.search("the and or") == []

    def test_search_no_match(self, populated_index):
        results = populated_index.search("xyzzyplugh")
        assert results == []

    def test_search_limit(self, populated_index):
        results = populated_index.search("adapter", limit=1)
        assert len(results) <= 1

    def test_search_scope_filter(self, populated_index):
        results = populated_index.search("adapter", scope="technical")
        for r in results:
            assert r["meta"]["scope"] == "technical"

    def test_search_type_filter(self, populated_index):
        results = populated_index.search("adapter", entry_type="discovery")
        for r in results:
            assert r["meta"]["type"] == "discovery"

    def test_search_since_filter(self, populated_index):
        # Only entries on or after 2026-03-29
        results = populated_index.search(
            "adapter", since="2026-03-29T00:00:00Z"
        )
        for r in results:
            assert r["meta"]["timestamp"] >= "2026-03-29T00:00:00Z"

    def test_search_score_descending(self, populated_index):
        results = populated_index.search("adapter")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_result_structure(self, populated_index):
        results = populated_index.search("circuit")
        assert len(results) > 0
        r = results[0]
        assert "id" in r
        assert "score" in r
        assert "meta" in r
        assert isinstance(r["score"], float)
        assert r["score"] > 0

    def test_search_combined_filters(self, populated_index):
        results = populated_index.search(
            "adapter",
            scope="operational",
            entry_type="discovery",
        )
        for r in results:
            assert r["meta"]["scope"] == "operational"
            assert r["meta"]["type"] == "discovery"


# ---------------------------------------------------------------------------
# BM25Index.record_retrieval() -- stigmergic ranking
# ---------------------------------------------------------------------------

class TestRecordRetrieval:
    def test_record_increments(self):
        idx = BM25Index()
        assert idx.retrieval_counts.get("clp-aaa") is None
        idx.record_retrieval("clp-aaa")
        assert idx.retrieval_counts["clp-aaa"] == 1
        idx.record_retrieval("clp-aaa")
        assert idx.retrieval_counts["clp-aaa"] == 2

    def test_retrieval_boost_applied(self):
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = SAMPLE_ENTRIES
            idx = BM25Index()
            idx.build()

        # Search without boost
        results_no_boost = idx.search("circuit breaker", boost_retrievals=False)
        score_no_boost = results_no_boost[0]["score"]

        # Record retrievals and search with boost
        idx.record_retrieval("clp-aaaaaaaaaaaa")
        idx.record_retrieval("clp-aaaaaaaaaaaa")
        results_boost = idx.search("circuit breaker", boost_retrievals=True)
        score_boost = results_boost[0]["score"]

        assert score_boost > score_no_boost

    def test_no_boost_when_disabled(self):
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = SAMPLE_ENTRIES
            idx = BM25Index()
            idx.build()

        idx.record_retrieval("clp-aaaaaaaaaaaa")
        r1 = idx.search("circuit breaker", boost_retrievals=False)
        # Run a second time to confirm stability
        r2 = idx.search("circuit breaker", boost_retrievals=False)
        assert r1[0]["score"] == r2[0]["score"]


# ---------------------------------------------------------------------------
# BM25Index.save() / load()
# ---------------------------------------------------------------------------

class TestSaveLoad:
    @patch("hummbl_cognition.indexer.read_entries")
    def test_round_trip(self, mock_read):
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        idx.build()
        idx.record_retrieval("clp-aaaaaaaaaaaa")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            saved = idx.save(path)
            assert saved == path
            assert path.exists()

            idx2 = BM25Index()
            loaded = idx2.load(path)
            assert loaded is True
            assert idx2.total_docs == idx.total_docs
            assert idx2.avg_doc_length == idx.avg_doc_length
            assert idx2.entry_count == idx.entry_count
            assert idx2.built_at == idx.built_at
            assert idx2.doc_lengths == idx.doc_lengths
            assert idx2.doc_meta == idx.doc_meta
            assert idx2.retrieval_counts == idx.retrieval_counts
            assert set(idx2.inverted_index.keys()) == set(idx.inverted_index.keys())

    @patch("hummbl_cognition.indexer.read_entries")
    def test_save_creates_dirs(self, mock_read):
        mock_read.return_value = []
        idx = BM25Index()
        idx.build()

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sub" / "dir" / "index.json"
            idx.save(path)
            assert path.exists()

    def test_load_missing_file(self):
        idx = BM25Index()
        result = idx.load("/tmp/nonexistent_index_12345.json")
        assert result is False

    def test_load_corrupt_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            path.write_text("not json at all", encoding="utf-8")
            idx = BM25Index()
            result = idx.load(path)
            assert result is False

    @patch("hummbl_cognition.indexer.read_entries")
    def test_save_is_valid_json(self, mock_read):
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        idx.build()

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            idx.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "stats" in data
            assert "inverted_index" in data
            assert "doc_lengths" in data
            assert "doc_meta" in data
            assert "retrieval_counts" in data
            assert data["stats"]["total_docs"] == 3

    @patch("hummbl_cognition.indexer.read_entries")
    def test_search_after_load(self, mock_read):
        """Verify loaded index is fully functional for search."""
        mock_read.return_value = SAMPLE_ENTRIES
        idx = BM25Index()
        idx.build()

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            idx.save(path)

            idx2 = BM25Index()
            idx2.load(path)
            results = idx2.search("circuit breaker")
            assert len(results) > 0
            assert results[0]["id"] == "clp-aaaaaaaaaaaa"


# ---------------------------------------------------------------------------
# BM25 scoring correctness
# ---------------------------------------------------------------------------

class TestBM25Scoring:
    def test_idf_higher_for_rare_terms(self):
        """A term appearing in fewer docs should have higher IDF."""
        entries = [
            _make_entry(id="clp-111111111111", content="unique_xyzzy term here"),
            _make_entry(id="clp-222222222222", content="common term everywhere"),
            _make_entry(id="clp-333333333333", content="common term again"),
        ]
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = entries
            idx = BM25Index()
            idx.build()

        # "unique_xyzzy" appears in 1 doc, "common" in 2
        r_rare = idx.search("unique_xyzzy")
        r_common = idx.search("common")
        assert len(r_rare) == 1
        assert len(r_common) == 2
        # The rare term match should score higher
        assert r_rare[0]["score"] > r_common[0]["score"]

    def test_multi_term_query_scores_higher(self):
        """Matching more query terms should yield a higher score."""
        entries = [
            _make_entry(id="clp-111111111111", content="alpha beta gamma"),
            _make_entry(id="clp-222222222222", content="alpha only here"),
        ]
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = entries
            idx = BM25Index()
            idx.build()

        results = idx.search("alpha beta gamma")
        assert results[0]["id"] == "clp-111111111111"


# ---------------------------------------------------------------------------
# Time decay and retrieval decay (Tier 1: inverted-retrieval fix)
# ---------------------------------------------------------------------------

class TestTimeDecay:
    """Test exponential time decay on BM25 scores based on entry age."""

    @pytest.fixture()
    def age_varied_index(self):
        """Index with entries of varying ages but identical content."""
        entries = [
            _make_entry(
                id="clp-recent111111",
                content="circuit breaker tripped on github adapter",
                timestamp="2026-06-27T10:00:00Z",
            ),
            _make_entry(
                id="clp-old222222222",
                content="circuit breaker tripped on github adapter",
                timestamp="2026-01-01T10:00:00Z",
            ),
        ]
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = entries
            idx = BM25Index()
            idx.build()
        return idx

    def test_time_decay_reduces_old_entry_score(self, age_varied_index):
        """Older entries should score lower when time_decay=True."""
        now = "2026-06-27T12:00:00Z"
        results = age_varied_index.search(
            "circuit breaker", time_decay=True, now=now
        )
        assert len(results) == 2
        # Recent entry should score higher than old entry
        recent_score = next(r["score"] for r in results if r["id"] == "clp-recent111111")
        old_score = next(r["score"] for r in results if r["id"] == "clp-old222222222")
        assert recent_score > old_score

    def test_time_decay_disabled_by_default(self, age_varied_index):
        """Without time_decay, entries with identical content should score equally."""
        results = age_varied_index.search("circuit breaker")
        assert len(results) == 2
        assert results[0]["score"] == results[1]["score"]

    def test_time_decay_half_life_approximate(self, age_varied_index):
        """After one half-life, score should be approximately halved."""
        now = "2026-06-27T10:00:00Z"
        # Recent entry is 0 days old, old entry is ~177 days old
        # With 90-day half-life, old entry should be roughly 0.5^(177/90) ≈ 0.255
        results_no_decay = age_varied_index.search(
            "circuit breaker", time_decay=False, now=now
        )
        results_decay = age_varied_index.search(
            "circuit breaker", time_decay=True, now=now
        )
        old_no_decay = next(
            r["score"] for r in results_no_decay if r["id"] == "clp-old222222222"
        )
        old_decay = next(
            r["score"] for r in results_decay if r["id"] == "clp-old222222222"
        )
        # Decay factor should be significant (old entry is ~2 half-lives old)
        assert old_decay < old_no_decay * 0.5

    def test_time_decay_preserves_recent_score(self, age_varied_index):
        """Very recent entries should not be significantly decayed."""
        now = "2026-06-27T10:05:00Z"  # 5 minutes after recent entry
        results = age_varied_index.search(
            "circuit breaker", time_decay=True, now=now
        )
        recent = next(r for r in results if r["id"] == "clp-recent111111")
        # 5 minutes is negligible vs 90-day half-life
        assert recent["score"] > 0.99 * (
            next(r["score"] for r in age_varied_index.search("circuit breaker") if r["id"] == "clp-recent111111")
        )


class TestRetrievalDecay:
    """Test exponential decay on retrieval counts based on time since last retrieval."""

    @pytest.fixture()
    def retrieval_decay_index(self):
        """Index with two entries, both retrieved, but at different times."""
        entries = [
            _make_entry(
                id="clp-fresh1111111",
                content="circuit breaker tripped on github adapter",
                timestamp="2026-06-20T10:00:00Z",
            ),
            _make_entry(
                id="clp-stale2222222",
                content="circuit breaker tripped on github adapter",
                timestamp="2026-06-20T10:00:00Z",
            ),
        ]
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = entries
            idx = BM25Index()
            idx.build()
        # Both retrieved same number of times, but at different times
        idx.record_retrieval("clp-fresh1111111", timestamp="2026-06-27T10:00:00Z")
        idx.record_retrieval("clp-fresh1111111", timestamp="2026-06-27T11:00:00Z")
        idx.record_retrieval("clp-stale2222222", timestamp="2026-05-01T10:00:00Z")
        idx.record_retrieval("clp-stale2222222", timestamp="2026-05-01T11:00:00Z")
        return idx

    def test_retrieval_decay_favors_recent(self, retrieval_decay_index):
        """Entries retrieved recently should get more boost than stale retrievals."""
        now = "2026-06-27T12:00:00Z"
        results = retrieval_decay_index.search(
            "circuit breaker", retrieval_decay=True, now=now
        )
        fresh = next(r for r in results if r["id"] == "clp-fresh1111111")
        stale = next(r for r in results if r["id"] == "clp-stale2222222")
        assert fresh["score"] > stale["score"]

    def test_retrieval_decay_disabled_by_default(self, retrieval_decay_index):
        """Without retrieval_decay, both entries should get equal boost (same count)."""
        results = retrieval_decay_index.search("circuit breaker")
        fresh = next(r for r in results if r["id"] == "clp-fresh1111111")
        stale = next(r for r in results if r["id"] == "clp-stale2222222")
        assert fresh["score"] == stale["score"]

    def test_record_retrieval_stores_timestamp(self):
        """record_retrieval should store the timestamp in retrieval_last_at."""
        idx = BM25Index()
        ts = "2026-06-27T10:00:00Z"
        idx.record_retrieval("clp-test", timestamp=ts)
        assert idx.retrieval_last_at["clp-test"] == ts
        assert idx.retrieval_counts["clp-test"] == 1

    def test_record_retrieval_defaults_to_now(self):
        """record_retrieval without timestamp should use current time."""
        idx = BM25Index()
        before = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        idx.record_retrieval("clp-test")
        after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        stored = idx.retrieval_last_at["clp-test"]
        assert before <= stored <= after

    def test_retrieval_decay_persisted(self):
        """retrieval_last_at should survive save/load round-trip."""
        with patch("hummbl_cognition.indexer.read_entries") as mock_read:
            mock_read.return_value = [SAMPLE_ENTRIES[0]]
            idx = BM25Index()
            idx.build()
        idx.record_retrieval("clp-aaaaaaaaaaaa", timestamp="2026-06-27T10:00:00Z")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            idx.save(path)
            idx2 = BM25Index()
            idx2.load(path)
            assert idx2.retrieval_last_at == idx.retrieval_last_at
            assert idx2.retrieval_counts == idx.retrieval_counts


class TestDecayConstants:
    """Test that decay constants are configurable and have sensible defaults."""

    def test_time_decay_default(self):
        assert TIME_DECAY_HALF_LIFE_DAYS == 90.0

    def test_retrieval_decay_default(self):
        assert RETRIEVAL_DECAY_HALF_LIFE_DAYS == 30.0

    def test_constants_are_floats(self):
        assert isinstance(TIME_DECAY_HALF_LIFE_DAYS, float)
        assert isinstance(RETRIEVAL_DECAY_HALF_LIFE_DAYS, float)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    @patch("hummbl_cognition.indexer.read_entries")
    def test_single_entry(self, mock_read):
        mock_read.return_value = [SAMPLE_ENTRIES[0]]
        idx = BM25Index()
        idx.build()
        assert idx.total_docs == 1
        results = idx.search("circuit")
        assert len(results) == 1

    @patch("hummbl_cognition.indexer.read_entries")
    def test_entry_with_no_tags(self, mock_read):
        entry = _make_entry(tags=())
        mock_read.return_value = [entry]
        idx = BM25Index()
        count = idx.build()
        assert count == 1

    @patch("hummbl_cognition.indexer.read_entries")
    def test_entry_with_links(self, mock_read):
        entry = _make_entry(links=("clp-aaaaaaaaaaaa",))
        mock_read.return_value = [entry]
        idx = BM25Index()
        idx.build()
        meta = idx.doc_meta[entry.id]
        assert meta["links"] == ["clp-aaaaaaaaaaaa"]

    @patch("hummbl_cognition.indexer.read_entries")
    def test_content_preview_truncated(self, mock_read):
        long_content = "x" * 500
        entry = _make_entry(content=long_content)
        mock_read.return_value = [entry]
        idx = BM25Index()
        idx.build()
        preview = idx.doc_meta[entry.id]["content_preview"]
        assert len(preview) == 200

    def test_stopwords_frozen(self):
        """Ensure stopwords set is immutable."""
        assert isinstance(_STOPWORDS, frozenset)

    def test_bm25_constants(self):
        assert BM25_K1 == 1.5
        assert BM25_B == 0.75
