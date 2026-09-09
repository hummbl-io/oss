"""Tests for SYNTHESIS/runtime.py -- the paideia-review workflow debut.

Pure stdlib. No Ollama. Composes score_paideia (use_llm=False) +
overnight_v0.load_paideia_plan (version-aware) + gap_analysis attribution +
prompt_refiner edit proposal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SYNTHESIS"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import runtime as syn  # noqa: E402
import ecosystem_contracts as ec  # noqa: E402


def _v02_plan() -> dict:
    return {
        "instructional_intent": True,
        "target_vector": {a: 3 for a in ec.PAIDEIA_AXES},  # 10 axes, target 3
        "prompt_version": "paideia-plan-v2",
    }


def _v01_plan() -> dict:
    return {
        "instructional_intent": True,
        "target_vector": {a: 3 for a in ec.PAIDEIA_AXES_V0_1},  # 9 axes, no Em
        "prompt_version": "paideia-plan-v1",
    }


def _write(tmp_path: Path, name: str, payload: dict | str) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload) if isinstance(payload, dict) else payload,
                 encoding="utf-8")
    return p


def test_build_paideia_review_bundle_shape(tmp_path):
    article = _write(tmp_path, "article.md",
                     "# Test\n\nA real-world case study in production.\n")
    plan = _write(tmp_path, "plan.json", _v02_plan())
    bundle = syn.build_paideia_review_bundle(article, plan)
    assert bundle["schema_version"] == "synthesis-paideia-review-v0.1"
    assert bundle["workflow"] == "paideia-review"
    assert bundle["inputs"]["article"]["sha256"]
    assert bundle["inputs"]["plan"]["paideia_version"] == "paideia-plan-v2"
    # PAIDEIA score is v0.2 (10-axis)
    sig = bundle["paideia_score"]["signature"]
    assert sig.count("-") == 9  # 10 elements -> 9 dashes
    assert bundle["paideia_score"]["prompt_version"] == "paideia-score-v0.2"
    # All 10 axes compared (v0.2 plan + v0.2 score)
    assert len(bundle["gaps"]["axis_gaps"]) == 10
    assert "Em" in [g["axis"] for g in bundle["gaps"]["axis_gaps"]]
    # edits is a list (likely empty for single-article insufficient_data)
    assert isinstance(bundle["edits"], list)
    assert isinstance(bundle["proposal_markdown"], str)


def test_bundle_accepts_v0_1_plan_and_fills_em(tmp_path):
    """Version-aware: a v0.1 9-axis plan is accepted; Em is filled to 0 so
    all 10 axes are comparable against a v0.2 score."""
    article = _write(tmp_path, "article.md", "# Test\n\nSome content.\n")
    plan = _write(tmp_path, "plan-v01.json", _v01_plan())
    bundle = syn.build_paideia_review_bundle(article, plan)
    # 10 axes compared (Em filled from plan side; score has Em)
    assert len(bundle["gaps"]["axis_gaps"]) == 10
    em_gap = next(g for g in bundle["gaps"]["axis_gaps"] if g["axis"] == "Em")
    # plan Em defaulted 0, score Em 0 -> gap 0
    assert em_gap["target"] == 0


def test_missing_article_raises(tmp_path):
    plan = _write(tmp_path, "plan.json", _v02_plan())
    try:
        syn.build_paideia_review_bundle(tmp_path / "nope.md", plan)
        assert False, "should have raised"
    except FileNotFoundError:
        pass


def test_missing_plan_raises(tmp_path):
    article = _write(tmp_path, "article.md", "# Test\n")
    try:
        syn.build_paideia_review_bundle(article, tmp_path / "nope.json")
        assert False, "should have raised"
    except FileNotFoundError:
        pass


def test_render_summary_contains_signature_and_edits_count(tmp_path):
    article = _write(tmp_path, "article.md", "# Test\n\nContent.\n")
    plan = _write(tmp_path, "plan.json", _v02_plan())
    bundle = syn.build_paideia_review_bundle(article, plan)
    md = syn.render_summary(bundle)
    assert "Paideia-Review Summary" in md
    assert bundle["paideia_score"]["signature"] in md
    assert "edits proposed:" in md
    assert "insufficient_data" in md or len(bundle["edits"]) > 0


def test_write_outputs_writes_json_and_md(tmp_path):
    article = _write(tmp_path, "article.md", "# Test\n\nContent here.\n")
    plan = _write(tmp_path, "plan.json", _v02_plan())
    bundle = syn.build_paideia_review_bundle(article, plan)
    out = tmp_path / "out"
    json_path, md_path = syn.write_outputs(bundle, out)
    assert json_path.exists() and md_path.exists()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["workflow"] == "paideia-review"
    assert "Paideia-Review Summary" in md_path.read_text(encoding="utf-8")


def test_cli_emits_json(tmp_path):
    article = _write(tmp_path, "article.md", "# Test\n\nContent.\n")
    plan = _write(tmp_path, "plan.json", _v02_plan())
    out = tmp_path / "cli"
    rc = syn.main(["--article", str(article), "--plan", str(plan),
                   "--output-dir", str(out)])
    assert rc == 0
    assert (out / "synthesis_paideia_review.json").exists()
    assert (out / "synthesis_paideia_review.md").exists()
