"""CPU-only tests for debate_protocol.py. No Ollama.

Each test injects a fake ollama_fn that returns canned OllamaResult objects,
keyed off the phase name embedded in the user prompt. Mirrors the ollama_fn
injection pattern in test_gen_common.py / test_paideia_detectors.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import _gen_common as gc
import debate_protocol as dp

# Extracts the phase label from "Phase N -- LABEL." in the user prompt.
_PHASE_RE = re.compile(r"PHASE\s+\d+\s+--\s+([A-Z][A-Z -]+)\.")


# ------------------------------- fixtures ----------------------------------- #

def _spec() -> dict:
    return {
        "topic_id": "TEST-001",
        "topic": "Good and Evil as mental models",
        "resolution": "Good and Evil are best treated as revisable mental models.",
        "definitions_required": ["good", "evil", "mental model", "absolute"],
        "constructive_mandate": "Defend the resolution.",
        "adversarial_mandate": "Attack the resolution.",
        "applied_cases": [
            {"case_id": "C1", "case": "Gratuitous cruelty for enjoyment."},
            {"case_id": "C2", "case": "Competing goods: safety vs liberty."},
        ],
    }


def _result(parsed: dict) -> gc.OllamaResult:
    return gc.OllamaResult(
        parsed=parsed, raw=json.dumps(parsed), elapsed_s=0.01,
        prompt_tokens=10, completion_tokens=20, model="fake",
        endpoint_name="fake", parse_error=None)


def _error_result(msg: str) -> gc.OllamaResult:
    return gc.OllamaResult(
        parsed=None, raw="", elapsed_s=0.0, prompt_tokens=0,
        completion_tokens=0, model="fake", endpoint_name="fake",
        parse_error=msg)


# Canned phase outputs. The fake dispatches by detecting "Phase N -- NAME".
_PHASE_OUTPUTS = {
    "formalization": {
        "definitions": [
            {"term": "good", "definition": "a moral predicate", "contested": True},
            {"term": "evil", "definition": "a moral predicate", "contested": True},
        ],
        "assumptions": ["moral discourse is meaningful"],
    },
    "constructive": {
        "claims": [
            {"id": "con-1", "claim": "Good/Evil compress moral patterns",
             "claim_type": "pragmatic", "assumptions": ["compression is useful"],
             "scope": "ordinary discourse", "uncertainty": "low"},
            {"id": "con-2", "claim": "science needs normative premises",
             "claim_type": "normative", "assumptions": ["science is descriptive"],
             "scope": "metaethics", "uncertainty": "med"},
        ],
        "self_identified_limitations": ["revisability may weaken condemnation"],
    },
    "adversarial": {
        "claims": [
            {"id": "adv-1", "claim": "mental-model framing reduces moral reality",
             "claim_type": "metaethical", "assumptions": ["moral realism is coherent"],
             "scope": "ontology", "uncertainty": "high"},
            {"id": "adv-2", "claim": "some moral truths are objective",
             "claim_type": "normative", "assumptions": [],
             "scope": "metaethics", "uncertainty": "med"},
        ],
        "strongest_objection": "revisability weakens condemnation of atrocities",
    },
    "cross_examination": {
        "objections": [
            {"target": "constructive", "weakest_assumption": "compression is useful",
             "hidden_premises": ["usefulness implies adequacy"]},
            {"target": "adversarial", "weakest_assumption": "moral realism is coherent",
             "hidden_premises": ["coherence implies existence"]},
        ],
    },
    "repair": {
        "repairs": [
            {"side": "constructive",
             "revised_claims": [
                 {"id": "con-1r", "claim": "Good/Evil are low-res but useful models",
                  "claim_type": "pragmatic", "assumptions": [],
                  "scope": "ordinary discourse", "uncertainty": "low"}],
             "what_changed": "added low-res qualifier", "why": "address adv-1"},
        ],
    },
    "applied_cases": {
        "applied_case_results": [
            {"case_id": "C1", "case": "Gratuitous cruelty",
             "judgment": "condemned under all models",
             "moral_model_used": "harm + agency", "uncertainty": "low"},
            {"case_id": "C2", "case": "safety vs liberty",
             "judgment": "genuine trade-off, no absolute resolution",
             "moral_model_used": "competing goods", "uncertainty": "high"},
        ],
    },
    "synthesis": {
        "defensible": ["science needs normative premises"],
        "weakened": ["strong mental-model-only framing"],
        "domain_of_validity": ["ordinary moral discourse", "metaethics"],
        "unresolved_questions": ["are objective moral truths possible?"],
    },
    "arbiter_verdict": {
        "verdicts": [
            {"claim_id": "con-1", "verdict": "CONDITIONAL",
             "reasoning": "useful but low-res", "domain_of_validity": "discourse"},
            {"claim_id": "adv-1", "verdict": "DOMAIN_LIMITED",
             "reasoning": "realism is coherent but unproven",
             "domain_of_validity": "metaethics"},
            {"claim_id": "con-2", "verdict": "ACCEPTED",
             "reasoning": "is-ought gap holds", "domain_of_validity": "all"},
            {"claim_id": "adv-2", "verdict": "UNRESOLVED",
             "reasoning": "objectivity contested", "domain_of_validity": "metaethics"},
            {"claim_id": "bad-verdict", "verdict": "MADE_UP_VERDICT",
             "reasoning": "should normalize", "domain_of_validity": "?"},
        ],
        "arbiter_reasoning": "No single winner; claims evaluated individually.",
        "recommended_follow_up": ["formalize objectivity", "test more cases"],
    },
}


def _fake_ollama(endpoint, system, user, seed=None, think=False, timeout=600,
                 fail_phase: str | None = None):
    """Dispatch canned output by extracting the 'Phase N -- NAME' label."""
    m = _PHASE_RE.search(user.upper())
    if not m:
        return _error_result("no phase marker matched")
    label = m.group(1).replace("-", " ").strip()
    for name in dp.PHASES:
        name_norm = name.upper().replace("_", " ")
        if label == name_norm or name_norm in label:
            if fail_phase == name:
                return _error_result(f"forced failure in {name}")
            return _result(_PHASE_OUTPUTS[name])
    return _error_result(f"no canned output for phase label: {label}")


# ------------------------------- tests -------------------------------------- #

def test_load_topic_spec_validates_required_keys(tmp_path: Path):
    bad = _spec()
    del bad["topic_id"]
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    try:
        dp.load_topic_spec(p)
        raise AssertionError("should raise on missing topic_id")
    except SystemExit as e:
        assert "topic_id" in str(e)


def test_load_topic_spec_requires_applied_cases_list(tmp_path: Path):
    bad = _spec()
    bad["applied_cases"] = "not a list"
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    try:
        dp.load_topic_spec(p)
        raise AssertionError("should raise on non-list applied_cases")
    except SystemExit as e:
        assert "applied_cases" in str(e)


def test_run_debate_produces_ledger_with_all_17_fields(tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    ledger = dp.run_debate(
        _spec(), endpoint,
        ollama_fn=lambda *a, **k: _fake_ollama(*a, **k),
        log=lambda m: None, output_dir=tmp_path, write_artifacts=False)
    for field in dp.LEDGER_FIELDS:
        assert field in ledger, f"ledger missing required field: {field}"
    assert ledger["topic_id"] == "TEST-001"
    assert ledger["resolution"].startswith("Good and Evil")
    # provenance recorded
    assert ledger["_provenance"]["prompt_version"] == dp.PROMPT_VERSION
    assert len(ledger["_provenance"]["phases_run"]) == 8


def test_run_debate_arbiter_verdicts_in_allowed_set(tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    ledger = dp.run_debate(
        _spec(), endpoint,
        ollama_fn=lambda *a, **k: _fake_ollama(*a, **k),
        log=lambda m: None, output_dir=tmp_path, write_artifacts=False)
    for v in ledger["verdict_status"]:
        assert v["verdict"] in dp.VERDICT_STATUSES, \
            f"verdict {v['verdict']} not in allowed set"
    # the MADE_UP_VERDICT must have been normalized to UNRESOLVED
    bad = [v for v in ledger["verdict_status"] if v["claim_id"] == "bad-verdict"]
    assert bad and bad[0]["verdict"] == "UNRESOLVED"


def test_run_debate_handles_parse_failure_gracefully(tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    ledger = dp.run_debate(
        _spec(), endpoint,
        ollama_fn=lambda *a, **k: _fake_ollama(*a, **k, fail_phase="synthesis"),
        log=lambda m: None, output_dir=tmp_path, write_artifacts=False)
    # ledger still assembled with all 17 fields
    for field in dp.LEDGER_FIELDS:
        assert field in ledger
    # the failed phase recorded in provenance
    assert "synthesis" in ledger["_provenance"]["phase_errors"]
    # domain_of_validity falls back to [] not missing
    assert ledger["domain_of_validity"] == []


def test_assemble_ledger_separates_claim_types():
    formal = _PHASE_OUTPUTS["formalization"]
    constructive = _PHASE_OUTPUTS["constructive"]
    adversarial = _PHASE_OUTPUTS["adversarial"]
    repair = _PHASE_OUTPUTS["repair"]
    ledger = dp.assemble_ledger(
        spec=_spec(), formalization=formal, constructive=constructive,
        adversarial=adversarial, cross_examination=_PHASE_OUTPUTS["cross_examination"],
        repair=repair, applied_cases=_PHASE_OUTPUTS["applied_cases"],
        synthesis=_PHASE_OUTPUTS["synthesis"], arbiter=_PHASE_OUTPUTS["arbiter_verdict"])
    # con-2 (normative) + adv-2 (normative) -> normative_premises
    norm_ids = [c["id"] for c in ledger["normative_premises"]]
    assert "con-2" in norm_ids and "adv-2" in norm_ids
    # no empirical or theological claims in fixtures -> empty
    assert ledger["empirical_evidence"] == []
    assert ledger["theological_premises"] == []
    # full claim lists preserved
    assert len(ledger["constructive_claims"]) == 2
    assert len(ledger["adversarial_claims"]) == 2


def test_render_ledger_markdown_includes_resolution_and_verdicts(tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    ledger = dp.run_debate(
        _spec(), endpoint,
        ollama_fn=lambda *a, **k: _fake_ollama(*a, **k),
        log=lambda m: None, output_dir=tmp_path, write_artifacts=False)
    md = dp.render_ledger_markdown(ledger)
    assert "Verdict Ledger" in md
    assert "Good and Evil are best treated" in md
    assert "Arbiter Verdicts" in md
    assert "CONDITIONAL" in md
    assert "Unresolved Questions" in md


def test_normalize_verdict():
    assert dp._normalize_verdict("accepted") == "ACCEPTED"
    assert dp._normalize_verdict("domain limited") == "DOMAIN_LIMITED"
    assert dp._normalize_verdict("nonsense") == "UNRESOLVED"
    assert dp._normalize_verdict(None) == "UNRESOLVED"
    assert dp._normalize_verdict(123) == "UNRESOLVED"


def test_run_debate_writes_artifacts(tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    out = tmp_path / "debate"
    dp.run_debate(_spec(), endpoint,
                  ollama_fn=lambda *a, **k: _fake_ollama(*a, **k),
                  log=lambda m: None, output_dir=out, write_artifacts=True)
    assert (out / "verdict_ledger.json").exists()
    # one raw phase file per phase
    for name in dp.PHASES:
        assert (out / f"phase_{name}.json").exists(), f"missing phase_{name}.json"


# ---- arbiter-balance hardening (lopsided-verdict detection) -------------- #

def test_verdict_distribution_counts_statuses():
    verdicts = [{"verdict": "ACCEPTED"}, {"verdict": "ACCEPTED"},
                {"verdict": "CONDITIONAL"}, "REFUTED"]
    counts = dp.verdict_distribution(verdicts)
    assert counts == {"ACCEPTED": 2, "CONDITIONAL": 1, "REFUTED": 1}


def test_flag_lopsided_warns_on_unanimous():
    # 5 identical verdicts -> unanimous AND binary-only (no intermediate).
    verdicts = [{"verdict": "ACCEPTED"}] * 5
    logs: list[str] = []
    warnings = dp.flag_lopsided_verdicts(verdicts, logs.append)
    assert len(warnings) == 2
    assert any("all 5 verdicts are ACCEPTED" in w for w in warnings)
    assert any("none are CONDITIONAL/DOMAIN_LIMITED/NEEDS_FORMALIZATION" in w
               for w in warnings)
    assert len(logs) == 2  # warnings were logged


def test_flag_lopsided_quiet_on_balanced_mix():
    # Uses an intermediate verdict (CONDITIONAL) and is not unanimous.
    verdicts = [{"verdict": v} for v in
                ("ACCEPTED", "REFUTED", "CONDITIONAL", "UNRESOLVED")]
    logs: list[str] = []
    warnings = dp.flag_lopsided_verdicts(verdicts, logs.append)
    assert warnings == []
    assert logs == []


def test_flag_lopsided_warns_on_binary_only_not_unanimous():
    # n=4, only ACCEPTED/REFUTED (no intermediate), but not unanimous.
    verdicts = [{"verdict": v} for v in
                ("ACCEPTED", "REFUTED", "ACCEPTED", "REFUTED")]
    logs: list[str] = []
    warnings = dp.flag_lopsided_verdicts(verdicts, logs.append)
    assert len(warnings) == 1
    assert "binary accept/refute" in warnings[0]


def test_flag_lopsided_ignores_small_n():
    # n=2: too few to flag either failure mode.
    verdicts = [{"verdict": "ACCEPTED"}, {"verdict": "ACCEPTED"}]
    assert dp.flag_lopsided_verdicts(verdicts, lambda m: None) == []


def test_arbiter_prompt_asks_for_full_verdict_range():
    sys, _user = dp.build_arbiter_prompt(
        {"resolution": "x"}, {"defensible": []}, [])
    assert "FULL verdict range" in sys
    assert "MIX of verdicts" in sys


def test_run_debate_records_distribution_and_balance_in_provenance(
        tmp_path: Path):
    endpoint = {"name": "fake", "url": "http://x", "model": "fake"}
    ledger = dp.run_debate(
        _spec(), endpoint,
        ollama_fn=lambda *a, **k: _fake_ollama(*a, **k),
        log=lambda m: None, output_dir=tmp_path, write_artifacts=False)
    prov = ledger["_provenance"]
    assert "verdict_distribution" in prov
    assert "arbiter_balance_warnings" in prov
    # fixture arbiter emits CONDITIONAL + DOMAIN_LIMITED + ACCEPTED + UNRESOLVED
    # (the MADE_UP_VERDICT normalizes to UNRESOLVED) -> balanced, no warnings.
    assert prov["arbiter_balance_warnings"] == []
    assert prov["verdict_distribution"]["CONDITIONAL"] == 1
    assert prov["verdict_distribution"]["DOMAIN_LIMITED"] == 1
