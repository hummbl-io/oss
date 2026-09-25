"""Tests for hummbl_cognition.novelty_check -- bounded novelty evidence.

Covers:
- NoveltyNeighbor / NoveltyReport serialization shape
- novelty_check() with a stub retriever
- matched_terms computation
- unseen_terms from index membership
- caveats (always present; no-neighbors case)
- CLI parser + dispatch
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from hummbl_cognition import __main__ as cli_main
from hummbl_cognition.novelty_check import (
    METRIC,
    NoveltyNeighbor,
    NoveltyReport,
    _matched_terms,
    format_report_text,
    novelty_check,
)
from hummbl_cognition.retriever import MemoryResult


def _result(entry_id: str, score: float, content: str, ts: str = "2026-09-25T00:00:00Z") -> MemoryResult:
    return MemoryResult(
        source="ledger",
        entry_id=entry_id,
        score=score,
        content=content,
        metadata={"timestamp": ts},
    )


def _stub_retriever(results, index_terms):
    """Fake retriever exposing the surface novelty_check uses."""
    r = MagicMock()
    r.search.return_value = results
    r.index.inverted_index = {t: [("clp-x", 1)] for t in index_terms}
    return r


# ---------------------------------------------------------------------------
# _matched_terms
# ---------------------------------------------------------------------------


class TestMatchedTerms:
    def test_intersection_sorted(self):
        terms = _matched_terms(
            {"alpha", "beta", "gamma"}, "beta content with alpha only"
        )
        assert terms == ["alpha", "beta"]

    def test_no_overlap(self):
        assert _matched_terms({"quorum"}, "unrelated content") == []


# ---------------------------------------------------------------------------
# novelty_check
# ---------------------------------------------------------------------------


class TestNoveltyCheck:
    def test_report_shape(self):
        results = [
            _result("clp-a", 12.5, "ledger close handoff session content"),
            _result("clp-b", 9.0, "other entry"),
        ]
        r = _stub_retriever(results, index_terms=["ledger", "session"])
        rep = novelty_check(
            "ledger session close claim with novelterm", retriever=r, limit=5
        )

        d = rep.to_dict()
        assert d["schema"] == "novelty-check.v0.1"
        assert d["corpus_scope"] == ["internal"]
        assert d["metric"] == METRIC
        assert d["top_score"] == 12.5
        assert len(d["nearest_neighbors"]) == 2
        n0 = d["nearest_neighbors"][0]
        assert n0["entry_id"] == "clp-a"
        assert "ledger" in n0["matched_terms"]
        assert "session" in n0["matched_terms"]
        # "novelterm" is in no index and no neighbor -> unseen
        assert "novelterm" in d["unseen_terms"]
        assert "ledger" not in d["unseen_terms"]
        assert d["caveats"]  # always non-empty
        assert d["checked_at"].endswith("Z")

    def test_empty_results(self):
        r = _stub_retriever([], index_terms=[])
        rep = novelty_check("anything", retriever=r)
        assert rep.top_score is None
        assert rep.nearest_neighbors == ()
        assert rep.to_dict()["top_score"] is None
        # no-neighbors caveat is prepended
        assert "zero neighbors" in rep.caveats[0].lower()

    def test_limit_and_sources_forwarded(self):
        r = _stub_retriever([], index_terms=[])
        novelty_check("x", retriever=r, limit=3, sources=["ledger"])
        r.search.assert_called_once()
        kwargs = r.search.call_args
        assert kwargs.kwargs["limit"] == 3
        assert kwargs.kwargs["sources"] == ["ledger"]

    def test_unseen_terms_excludes_indexed(self):
        r = _stub_retriever(
            [_result("clp-a", 5.0, "seen term content")],
            index_terms=["seen", "term"],
        )
        rep = novelty_check("seen term freshterm", retriever=r)
        assert rep.unseen_terms == ("freshterm",)
        assert "seen" not in rep.unseen_terms


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_neighbor_to_dict(self):
        n = NoveltyNeighbor(
            source="ledger",
            entry_id="clp-1",
            score=1.23456,
            timestamp="2026-01-01T00:00:00Z",
            content="abc",
            matched_terms=["a"],
        )
        d = n.to_dict()
        assert d["score"] == 1.2346
        assert d["matched_terms"] == ["a"]

    def test_report_json_roundtrip(self):
        rep = NoveltyReport(
            claim="c",
            sources=("ledger",),
            checked_at="2026-01-01T00:00:00Z",
            top_score=1.0,
            nearest_neighbors=(),
            unseen_terms=("x",),
            caveats=("y",),
        )
        d = json.loads(rep.to_json())
        assert d["claim"] == "c"
        assert d["unseen_terms"] == ["x"]


# ---------------------------------------------------------------------------
# Text rendering
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_renders_neighbors_and_caveats(self):
        rep = NoveltyReport(
            claim="test claim",
            sources=("ledger",),
            checked_at="2026-01-01T00:00:00Z",
            top_score=9.9,
            nearest_neighbors=(
                NoveltyNeighbor(
                    source="ledger",
                    entry_id="clp-9",
                    score=9.9,
                    timestamp="2026-01-01T00:00:00Z",
                    content="snippet text",
                    matched_terms=["test"],
                ),
            ),
            unseen_terms=("uniqterm",),
            caveats=("c1",),
        )
        out = format_report_text(rep)
        assert "clp-9" in out
        assert "matched_terms: test" in out
        assert "uniqterm" in out
        assert "c1" in out

    def test_empty_report_renders(self):
        rep = NoveltyReport(
            claim="c",
            sources=("ledger",),
            checked_at="t",
            top_score=None,
            nearest_neighbors=(),
            unseen_terms=(),
            caveats=(),
        )
        assert "No near-neighbors" in format_report_text(rep)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_parser_accepts_subcommand(self):
        parser = cli_main.build_parser()
        args = parser.parse_args(["novelty-check", "my claim"])
        assert args.command == "novelty-check"
        assert args.claim == "my claim"
        assert args.limit == 5

    def test_dispatch_json(self, monkeypatch, capsys):
        import sys

        # Package __init__ re-exports the function under the same name, so
        # resolve the real submodule via sys.modules.
        nc = sys.modules["hummbl_cognition.novelty_check"]

        fake = NoveltyReport(
            claim="x",
            sources=("ledger",),
            checked_at="t",
            top_score=None,
            nearest_neighbors=(),
            unseen_terms=(),
            caveats=(),
        )
        monkeypatch.setattr(nc, "novelty_check", lambda *a, **k: fake)
        rc = cli_main.main(["novelty-check", "x", "--json"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["schema"] == "novelty-check.v0.1"
