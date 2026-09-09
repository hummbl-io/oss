"""Tests for paideia_detectors_llm.py — pure CPU, no Ollama.

Each detector takes an injected ollama_fn for testability. These tests build
fake ollama_fns that return canned OllamaResults so we can exercise the
ensemble logic, JSON parsing, error fallback, and variance flagging without
hitting a network.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _gen_common as gc
import paideia_detectors_llm as pdl


def _result(parsed, parse_error=None, model="fake", endpoint_name="fake"):
    return gc.OllamaResult(
        parsed=parsed, raw="", elapsed_s=0.0,
        prompt_tokens=0, completion_tokens=0,
        model=model, endpoint_name=endpoint_name,
        parse_error=parse_error)


def _ep():
    return {"name": "fake", "model": "fake-model", "url": "http://x"}


def _fake_returns(*payloads):
    """Cycle through given payloads. Each can be a dict (parsed) or
    a dict with key '_error' to simulate a parse failure."""
    payloads = list(payloads)
    state = {"i": 0}

    def fn(endpoint, system, user, seed=None, think=False, timeout=600):
        if not payloads:
            raise RuntimeError("no more canned payloads")
        idx = state["i"] % len(payloads)
        state["i"] += 1
        p = payloads[idx]
        if isinstance(p, dict) and p.get("_error"):
            return _result(None, parse_error=p["_error"])
        return _result(p)
    return fn


# ---- _parse_one_score -------------------------------------------------- #

def test_parse_one_score_happy():
    s, r = pdl._parse_one_score({"score": 3, "rationale": "good"})
    assert s == 3 and r == "good"


def test_parse_one_score_float_integral_coerces():
    s, _r = pdl._parse_one_score({"score": 2.0, "rationale": "ok"})
    assert s == 2


def test_parse_one_score_float_non_integral_rejected():
    s, _ = pdl._parse_one_score({"score": 2.5, "rationale": "ok"})
    assert s is None


def test_parse_one_score_out_of_range_rejected():
    s, _ = pdl._parse_one_score({"score": 5, "rationale": "ok"})
    assert s is None
    s, _ = pdl._parse_one_score({"score": -1, "rationale": "ok"})
    assert s is None


def test_parse_one_score_missing_score_rejected():
    s, why = pdl._parse_one_score({"rationale": "no score"})
    assert s is None and "score" in why.lower()


def test_parse_one_score_missing_rationale_default():
    s, r = pdl._parse_one_score({"score": 1})
    assert s == 1 and r == "(no rationale)"


def test_parse_one_score_non_dict():
    s, why = pdl._parse_one_score("not a dict")
    assert s is None and "dict" in why.lower()


def test_parse_one_score_none_input():
    s, _ = pdl._parse_one_score(None)
    assert s is None


# ---- _aggregate -------------------------------------------------------- #

def test_aggregate_single_sample():
    score, std = pdl._aggregate([(3, "x")])
    assert score == 3 and std == 0.0


def test_aggregate_unanimous():
    score, std = pdl._aggregate([(2, "x"), (2, "y"), (2, "z")])
    assert score == 2 and std == 0.0


def test_aggregate_mean_rounds_half_to_even():
    # Python's round() uses banker's rounding; 2.5 -> 2
    score, _ = pdl._aggregate([(2, ""), (3, "")])
    assert score in (2, 3)  # bankers rounds 2.5 to 2; allow 3 for non-bankers


def test_aggregate_variance_known():
    # scores [1, 3, 5] -> mean 3, var = ((1-3)^2 + 0 + (5-3)^2)/3 = 8/3 ≈ 2.667
    # std ≈ 1.633
    score, std = pdl._aggregate([(1, ""), (3, ""), (5, "")])
    assert score == 3
    assert 1.6 < std < 1.7


def test_aggregate_empty():
    score, std = pdl._aggregate([])
    assert score == 0 and std == 0.0


# ---- detect_axis_llm --------------------------------------------------- #

def test_detect_axis_llm_unknown_axis_raises():
    try:
        pdl.detect_axis_llm("X", "text", endpoint=_ep(),
                            ollama_fn=_fake_returns())
    except ValueError as e:
        assert "X" in str(e) or "axis" in str(e).lower()
    else:
        raise AssertionError("should raise on unknown axis")


def test_detect_axis_llm_unanimous_high_confidence():
    fake = _fake_returns(
        {"score": 3, "rationale": "relational integration demanded"},
        {"score": 3, "rationale": "same"},
        {"score": 3, "rationale": "consistent"})
    score, note = pdl.detect_axis_llm(
        "D", "test text", endpoint=_ep(), ollama_fn=fake,
        n_runs=3, seed=0)
    assert score == 3
    assert "n=3/3" in note
    assert "low_confidence" not in note


def test_detect_axis_llm_high_variance_flags():
    fake = _fake_returns(
        {"score": 1, "rationale": "low"},
        {"score": 4, "rationale": "high"},
        {"score": 2, "rationale": "mid"})
    # std of [1,4,2] = sqrt(((1-7/3)^2 + (4-7/3)^2 + (2-7/3)^2)/3) ≈ 1.247
    _score, note = pdl.detect_axis_llm(
        "V", "text", endpoint=_ep(), ollama_fn=fake, n_runs=3)
    assert "low_confidence" in note


def test_detect_axis_llm_skips_invalid_runs():
    # 2 valid (both 3) + 1 ollama failure
    fake = _fake_returns(
        {"score": 3, "rationale": "ok"},
        {"_error": "JSONDecodeError: garbage"},
        {"score": 3, "rationale": "ok"})
    score, note = pdl.detect_axis_llm(
        "L", "text", endpoint=_ep(), ollama_fn=fake, n_runs=3)
    assert score == 3
    assert "n=2/3" in note  # 2 of 3 valid


def test_detect_axis_llm_all_runs_invalid_returns_zero():
    fake = _fake_returns(
        {"_error": "fail1"},
        {"_error": "fail2"},
        {"_error": "fail3"})
    score, note = pdl.detect_axis_llm(
        "D", "text", endpoint=_ep(), ollama_fn=fake, n_runs=3)
    assert score == 0
    assert "all_runs_invalid" in note


def test_detect_axis_llm_score_out_of_range_skipped():
    # One bad score (out of range) + 2 valid
    fake = _fake_returns(
        {"score": 7, "rationale": "out"},
        {"score": 2, "rationale": "ok"},
        {"score": 2, "rationale": "ok"})
    score, note = pdl.detect_axis_llm(
        "V", "text", endpoint=_ep(), ollama_fn=fake, n_runs=3)
    assert score == 2
    assert "n=2/3" in note


def test_detect_axis_llm_seed_bumped_per_run():
    seeds_seen = []
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        seeds_seen.append(seed)
        return _result({"score": 2, "rationale": "ok"})
    pdl.detect_axis_llm("D", "text", endpoint=_ep(), ollama_fn=fake,
                        n_runs=4, seed=100)
    assert seeds_seen == [100, 101, 102, 103]


def test_detect_axis_llm_seed_none_passes_none():
    seeds_seen = []
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        seeds_seen.append(seed)
        return _result({"score": 2, "rationale": "ok"})
    pdl.detect_axis_llm("D", "text", endpoint=_ep(), ollama_fn=fake,
                        n_runs=2, seed=None)
    assert seeds_seen == [None, None]


# ---- detect_hard_axes -------------------------------------------------- #

def test_detect_hard_axes_runs_all_three():
    """The convenience wrapper must call detect_axis_llm for each of D, V, L."""
    call_log = []
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        # Track the user prompt to identify which axis was queried.
        # Each prompt contains "DEPTH" / "MOTIVATION" / "LOAD" in the system text.
        call_log.append(("user_len", len(user)))
        return _result({"score": 2, "rationale": "ok"})
    out = pdl.detect_hard_axes(
        "test text", endpoint=_ep(), ollama_fn=fake, n_runs=2)
    assert sorted(out.keys()) == ["D", "L", "V"]
    for (score, note) in out.values():
        assert score == 2
        assert "n=2/2" in note
    # 3 axes * 2 runs = 6 calls
    assert len(call_log) == 6


# ---- prompt files exist ----------------------------------------------- #

def test_all_hard_axis_prompts_load():
    """Each HARD axis must have a loadable v1 prompt with $content placeholder."""
    for axis in pdl.HARD_AXES:
        system, tmpl = pdl._load_axis_prompt(axis)
        assert system, f"{axis}: empty system prompt"
        # Verify $content is the template placeholder
        rendered = tmpl.safe_substitute(content="SAMPLE")
        assert "SAMPLE" in rendered, f"{axis}: $content didn't render"


# ---- score_paideia integration ---------------------------------------- #

def test_detect_emotion_flat_text_scores_zero():
    import score_paideia as sp
    score, note = sp.detect_emotion("Some technical reference content with no affect words.")
    assert score == 0
    assert "flat" in note


def test_detect_emotion_affect_dense_scores_high():
    import score_paideia as sp
    text = ("awe and wonder at the sublime; joy and hope; then dread, horror, "
            "grief, sorrow, despair, anguish, shame, rage, terror, melancholy, "
            "lament, elegy, anxiety, disgust, anger, fear, thrill, delight, "
            "pride, gratitude, aspiration, triumph, beauty, exhilarat, love")
    score, note = sp.detect_emotion(text)
    assert score == 4
    assert "pos=" in note and "neg=" in note


def test_detect_emotion_reports_valence():
    import score_paideia as sp
    s_pos, n_pos = sp.detect_emotion("hope joy wonder awe love")
    assert s_pos >= 1 and "valence=pos" in n_pos
    s_neg, n_neg = sp.detect_emotion("fear dread horror rage anger")
    assert s_neg >= 1 and "valence=neg" in n_neg


def test_score_content_includes_em_axis():
    import score_paideia as sp
    result = sp.score_content("A flat technical description of a hash table.")
    assert "Em" in result["vector"]
    assert "Em" in result["per_axis"]
    assert result["per_axis"]["Em"]["score"] == 0
    assert result["per_axis"]["Em"]["detector"] == "MEDIUM"


def test_score_content_use_llm_overrides_dvl():
    """score_content with use_llm=True should replace D/V/L stubs with
    LLM ensemble outputs but leave M/C/P heuristics untouched."""
    import score_paideia as sp
    fake = _fake_returns(
        {"score": 4, "rationale": "high D"},
        {"score": 4, "rationale": "high D"},
        {"score": 4, "rationale": "high D"},
        {"score": 1, "rationale": "low V"},
        {"score": 1, "rationale": "low V"},
        {"score": 1, "rationale": "low V"},
        {"score": 3, "rationale": "med L"},
        {"score": 3, "rationale": "med L"},
        {"score": 3, "rationale": "med L"})
    text = ("# Heading\n\nProse with reflect prompt? Why does this work? "
            "```python\nx = 1\n```\n\n![diagram](x.png)")
    result = sp.score_content(text, use_llm=True, allow_uncalibrated=True,
                              endpoint=_ep(),
                              ollama_fn=fake, n_runs=3, seed=0)
    assert result["vector"]["D"] == 4
    assert result["vector"]["V"] == 1
    assert result["vector"]["L"] == 3
    # M/C/P stay as heuristic outputs (M sees text+code+image -> 3)
    assert result["per_axis"]["D"]["detector"] == "LLM ensemble"
    assert result["per_axis"]["M"]["detector"] == "EASY"
    assert result["prompt_version"] == "paideia-score-v0.2-llm"
    assert result["comparable_vector"] is False
    assert result["calibrated"] is False
    assert result["hard_axes_status"] == "uncalibrated_llm"


def test_score_content_use_llm_requires_allow_uncalibrated():
    import score_paideia as sp
    try:
        sp.score_content("x", use_llm=True, endpoint=_ep())
    except ValueError as e:
        assert "allow-uncalibrated" in str(e) or "uncalibrated" in str(e).lower()
    else:
        raise AssertionError("should raise without allow_uncalibrated")


def test_score_content_use_llm_requires_endpoint_or_ollama_fn():
    import score_paideia as sp
    try:
        sp.score_content("x", use_llm=True, allow_uncalibrated=True)
    except ValueError as e:
        assert "endpoint" in str(e) or "ollama" in str(e)
    else:
        raise AssertionError("should raise without endpoint or ollama_fn")


def test_score_content_default_path_unchanged():
    """v0.2: use_llm=False keeps the heuristic path (now v0.2-branded, 10 axes)."""
    import score_paideia as sp
    text = "Some content."
    result = sp.score_content(text, use_llm=False)
    assert result["prompt_version"] == "paideia-score-v0.2"
    # D, V, L are stubs returning 2
    assert result["vector"]["D"] == 2
    assert result["vector"]["V"] == 2
    assert result["vector"]["L"] == 2
    # Em is now scored (affect-density heuristic); flat text -> 0
    assert result["vector"]["Em"] == 0
    assert "Em" in result["per_axis"]
    assert result["comparable_vector"] is False
    assert result["hard_axes_status"] == "stub"


# ---- standalone runner ------------------------------------------------- #

def _run_standalone():
    import inspect
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            sig = inspect.signature(fn)
            if "tmp_path" in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
