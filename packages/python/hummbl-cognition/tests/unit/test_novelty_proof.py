"""Tests for hummbl_cognition.novelty_proof -- NOVELTY_PROOF receipts.

Covers:
- grade_for_scopes coverage matrix
- build_novelty_proof shape, falsifier requirement, scope derivation
- post_novelty_proof ledger mapping (discovery/project + tag)
- format_proof_text rendering
- CLI parser + dispatch
"""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock

import pytest

from hummbl_cognition import __main__ as cli_main
from hummbl_cognition.novelty_proof import (
    SCHEMA_VERSION,
    build_novelty_proof,
    format_proof_text,
    grade_for_scopes,
    post_novelty_proof,
)

# ---------------------------------------------------------------------------
# grade_for_scopes
# ---------------------------------------------------------------------------


class TestGrading:
    @pytest.mark.parametrize(
        "scopes,expected",
        [
            ({"internal", "literature", "market"}, "A"),
            ({"internal", "literature"}, "B"),
            ({"internal"}, "C"),
            ({"internal", "market"}, "ungraded"),  # no literature -> not in A/B/C ladder
            ({"literature", "market"}, "ungraded"),  # no internal
            (set(), "ungraded"),
        ],
    )
    def test_ladder(self, scopes, expected):
        assert grade_for_scopes(scopes) == expected


# ---------------------------------------------------------------------------
# build_novelty_proof
# ---------------------------------------------------------------------------


def _internal_dict():
    return {
        "schema": "novelty-check.v0.1",
        "top_score": 3.3,
        "nearest_neighbors": [{"entry_id": "clp-1"}],
        "unseen_terms": ["xylophone"],
        "caveats": ["internal caveat"],
    }


class TestBuild:
    def test_falsifier_required(self):
        with pytest.raises(ValueError):
            build_novelty_proof("c", falsifier="")

    def test_grade_and_scopes_from_evidence(self):
        r = build_novelty_proof(
            "claim",
            falsifier="prior art showing same mechanism",
            internal_report=_internal_dict(),
            external_evidence=[
                {"scope": "literature", "source": "arxiv", "query": "q1"},
                {"scope": "market", "source": "github", "query": "q2"},
            ],
            falsification_attempts=["q1", "q2"],
            recheck_due="2026-12-25",
        )
        assert r["schema"] == SCHEMA_VERSION
        assert r["grade"] == "A"
        assert r["corpus_scope"] == ["internal", "literature", "market"]
        assert r["falsification_attempts"] == ["q1", "q2"]
        assert r["recheck_due"] == "2026-12-25"
        assert "internal caveat" in r["caveats"]
        assert any("caller-attested" in c for c in r["caveats"])

    def test_internal_only_is_grade_c_with_caveat(self):
        r = build_novelty_proof("c", falsifier="f", internal_report=_internal_dict())
        assert r["grade"] == "C"
        assert r["corpus_scope"] == ["internal"]
        assert any("internal-only" in c for c in r["caveats"])

    def test_no_internal_is_ungraded(self):
        r = build_novelty_proof(
            "c",
            falsifier="f",
            external_evidence=[{"scope": "market", "source": "gh"}],
        )
        assert r["grade"] == "ungraded"
        assert r["corpus_scope"] == ["market"]

    def test_unknown_scope_not_counted(self):
        r = build_novelty_proof(
            "c",
            falsifier="f",
            internal_report=_internal_dict(),
            external_evidence=[{"scope": "narnia", "source": "x"}],
        )
        assert r["grade"] == "C"
        assert "narnia" not in r["corpus_scope"]

    def test_report_object_accepted(self):
        from hummbl_cognition.novelty_check import NoveltyReport

        rep = NoveltyReport(
            claim="c",
            sources=("ledger",),
            checked_at="t",
            top_score=1.0,
            nearest_neighbors=(),
            unseen_terms=(),
            caveats=(),
        )
        r = build_novelty_proof("c", falsifier="f", internal_report=rep)
        assert r["internal"]["schema"] == "novelty-check.v0.1"


# ---------------------------------------------------------------------------
# post_novelty_proof
# ---------------------------------------------------------------------------


class TestPost:
    def test_posts_as_discovery_with_tag(self, monkeypatch):
        mod = sys.modules["hummbl_cognition.novelty_proof"]
        fake_post = MagicMock(return_value="ENTRY")
        monkeypatch.setattr(mod, "post_verified_entry", fake_post)

        receipt = build_novelty_proof(
            "claim", falsifier="f", internal_report=_internal_dict()
        )
        out = post_novelty_proof(
            receipt, agent="a", vendor="local", model="m", ledger_path="x"
        )
        assert out == "ENTRY"
        kw = fake_post.call_args.kwargs
        assert kw["entry_type"] == "discovery"
        assert kw["scope"] == "project"
        assert "novelty-proof" in kw["tags"]
        assert kw["evidence"].startswith(SCHEMA_VERSION)
        # content round-trips the receipt
        posted = json.loads(kw["content"])
        assert posted["claim"] == "claim"

    def test_rejects_wrong_schema(self):
        with pytest.raises(ValueError):
            post_novelty_proof({"schema": "nope"}, agent="a", vendor="v", model="m")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


class TestFormat:
    def test_renders_key_fields(self):
        r = build_novelty_proof(
            "claim text",
            falsifier="the falsifier",
            internal_report=_internal_dict(),
            external_evidence=[{"scope": "market", "source": "gh", "query": "q"}],
            falsification_attempts=["q"],
        )
        out = format_proof_text(r)
        assert "grade=" in out
        assert "claim text" in out
        assert "the falsifier" in out
        assert "[market]" in out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_parser_accepts_subcommand(self):
        parser = cli_main.build_parser()
        args = parser.parse_args(
            ["novelty-proof", "--claim", "c", "--falsifier", "f", "--no-internal"]
        )
        assert args.command == "novelty-proof"
        assert args.claim == "c"
        assert args.no_internal is True

    def test_parse_external_arg(self):
        ev = cli_main._parse_external_arg("literature|arxiv|my query|paper-1|note")
        assert ev["scope"] == "literature"
        assert ev["source"] == "arxiv"
        assert ev["query"] == "my query"
        assert ev["nearest_ref"] == "paper-1"
        assert ev["note"] == "note"

    def test_dispatch_json_no_internal(self, capsys):
        rc = cli_main.main(
            [
                "novelty-proof",
                "--claim",
                "c",
                "--falsifier",
                "f",
                "--no-internal",
                "--json",
            ]
        )
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["schema"] == SCHEMA_VERSION
        assert out["grade"] == "ungraded"
        assert out["internal"] is None
