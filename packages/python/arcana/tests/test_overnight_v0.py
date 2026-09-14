"""Tests for overnight_v0.py helpers that don't require Ollama calls.

Covers:
- _as_text / _as_items coercers (the list-instead-of-string render bug fix)
- slugify
- render_markdown robustness against malformed LLM output

Run with: python scripts/test_overnight_v0.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import overnight_v0 as ov


# --------------------- _as_text -----------------------------------------
def test_as_text_string():
    assert ov._as_text("hello") == "hello"


def test_as_text_empty():
    assert ov._as_text("") == ""
    assert ov._as_text(None) == ""


def test_as_text_list_of_strings():
    assert ov._as_text(["a", "b"]) == "a\n\nb"


def test_as_text_nested_list():
    assert "a" in ov._as_text([["a", "b"], "c"])


def test_as_text_dict():
    out = ov._as_text({"a": "1", "b": "2"})
    assert "**a**" in out and "1" in out
    assert "**b**" in out and "2" in out


def test_as_text_int():
    assert ov._as_text(42) == "42"


# --------------------- _as_items ----------------------------------------
def test_as_items_list():
    assert ov._as_items(["a", "b"]) == ["a", "b"]


def test_as_items_skips_empty():
    assert ov._as_items(["a", None, "", "b"]) == ["a", "b"]


def test_as_items_string_becomes_one_item():
    assert ov._as_items("hello") == ["hello"]


def test_as_items_empty_string_becomes_empty_list():
    assert ov._as_items("") == []
    assert ov._as_items("   ") == []


def test_as_items_dict_becomes_bulleted_items():
    result = ov._as_items({"a": "1", "b": "2"})
    assert len(result) == 2
    assert any("**a**" in r for r in result)


def test_as_items_none():
    assert ov._as_items(None) == []


# --------------------- slugify ------------------------------------------
def test_slugify_basic():
    assert ov.slugify("Hello World") == "hello-world"


def test_slugify_punctuation():
    assert ov.slugify("Google's New Platform!") == "google-s-new-platform"


def test_slugify_long():
    long_topic = "a" * 200
    assert len(ov.slugify(long_topic)) == 60


def test_slugify_empty():
    assert ov.slugify("") == "untitled"
    assert ov.slugify("!!!") == "untitled"


# --------------------- render_markdown robustness -----------------------
def _perspective(lens="schmitt", perspective_val="A perspective string",
                 key_claims=None, blind_spots="A blind spot."):
    return {
        "lens": lens,
        "school": "ARCANA / political-theology",
        "parsed": {
            "perspective": perspective_val,
            "key_claims": key_claims if key_claims is not None
                          else ["Claim 1", "Claim 2"],
            "blind_spots": blind_spots,
        },
    }


def _synthesis(convergences=None, divergences=None, synthesis_val="",
               title="Title", summary="Summary text"):
    return {
        "parsed": {
            "title": title,
            "summary": summary,
            "convergences": convergences if convergences is not None
                            else ["Point 1"],
            "divergences": divergences if divergences is not None
                           else ["Point 2"],
            "synthesis": synthesis_val,
            "live_questions": ["Q1", "Q2"],
        }
    }


def test_render_markdown_happy():
    md = ov.render_markdown(
        "Test Topic",
        [_perspective()],
        _synthesis(synthesis_val="A synthesis essay"))
    assert "# Title" in md
    assert "Test Topic" in md
    assert "A perspective string" in md
    assert "Claim 1" in md


def test_render_markdown_list_perspective_does_not_crash():
    # The topic-5 real failure mode: perspective came back as a list
    md = ov.render_markdown(
        "Test",
        [_perspective(perspective_val=["para 1", "para 2", "para 3"])],
        _synthesis())
    assert "para 1" in md
    assert "para 2" in md


def test_render_markdown_dict_convergences_does_not_crash():
    # Malformed synthesis: convergences came back as a dict
    md = ov.render_markdown(
        "Test",
        [_perspective()],
        _synthesis(convergences={"point_a": "text a", "point_b": "text b"}))
    assert "point_a" in md or "text a" in md


def test_render_markdown_missing_parsed_does_not_crash():
    # Error case: synthesis has no 'parsed' key
    md = ov.render_markdown("Test", [_perspective()],
                             {"error": "timeout"})
    assert "Test" in md  # falls back to topic as title


def test_render_markdown_unparseable_perspective():
    bad = {"lens": "x", "school": "y", "parsed": "not a dict"}
    md = ov.render_markdown("Test", [bad], _synthesis())
    assert "unparseable" in md


# --------------------- paideia helpers ---------------------------------
def test_paideia_signature():
    v = {"M": 1, "D": 2, "E": 3, "V": 2, "C": 0,
         "L": 2, "S": 1, "P": 1, "A": 2, "Em": 3}
    assert ov.paideia_signature(v) == "1-2-3-2-0-2-1-1-2-3"


def test_paideia_delta_all_met():
    target = {a: 2 for a in ov.PAIDEIA_AXES}
    actual = {a: 2 for a in ov.PAIDEIA_AXES}
    d = ov.paideia_delta(target, actual)
    assert d["axes_missed"] == []
    assert d["worst_miss"][1] == 0


def test_paideia_delta_all_missed():
    target = {a: 3 for a in ov.PAIDEIA_AXES}
    actual = {a: 1 for a in ov.PAIDEIA_AXES}
    d = ov.paideia_delta(target, actual)
    assert set(d["axes_missed"]) == set(ov.PAIDEIA_AXES)
    assert d["worst_miss"][1] == -2


def test_paideia_delta_mixed():
    target = {a: 3 for a in ov.PAIDEIA_AXES}
    actual = dict(target)
    actual["C"] = 0  # miss by 3
    actual["M"] = 4  # exceeds by 1
    d = ov.paideia_delta(target, actual)
    assert "C" in d["axes_missed"]
    assert "M" in d["axes_met_or_exceeded"]
    assert d["worst_miss"] == ("C", -3)


def test_load_paideia_plan_missing(tmp_path):
    try:
        ov.load_paideia_plan(tmp_path / "nonexistent.json")
        assert False, "should have raised"
    except SystemExit:
        pass


def test_load_paideia_plan_valid(tmp_path):
    import json as _json
    plan = {
        "target_vector": {a: 2 for a in ov.PAIDEIA_AXES},
        "instructional_intent": True,
    }
    path = tmp_path / "plan.json"
    path.write_text(_json.dumps(plan), encoding="utf-8")
    loaded = ov.load_paideia_plan(path)
    assert loaded["target_vector"]["M"] == 2


def test_load_paideia_plan_accepts_v0_1_and_fills_em(tmp_path):
    """Version-aware: a v0.1 plan (9-axis target_vector, no Em) is accepted
    and Em is defaulted to 0 so the v0.2 pipeline can consume it."""
    import json as _json
    import ecosystem_contracts as ec
    v01_plan = {
        "target_vector": {a: 2 for a in ec.PAIDEIA_AXES_V0_1},  # 9 axes, no Em
        "instructional_intent": True,
    }
    path = tmp_path / "plan-v01.json"
    path.write_text(_json.dumps(v01_plan), encoding="utf-8")
    loaded = ov.load_paideia_plan(path)
    # Em filled with default 0
    assert loaded["target_vector"]["Em"] == 0
    assert "Em" in loaded.get("per_axis", {})
    # The 9 original axes preserved
    assert loaded["target_vector"]["M"] == 2
    assert len(loaded["target_vector"]) == 10


def test_format_perspective_full_includes_essay():
    p = _perspective(perspective_val="The long essay body.")
    blob = ov.format_perspective_for_synthesist(p, ov.SYNTH_INPUT_FULL)
    assert blob is not None
    assert "The long essay body." in blob
    assert "Claim 1" in blob


def test_format_perspective_claims_omits_essay():
    p = _perspective(perspective_val="The long essay body.")
    blob = ov.format_perspective_for_synthesist(p, ov.SYNTH_INPUT_CLAIMS)
    assert blob is not None
    assert "The long essay body." not in blob
    assert "Claim 1" in blob
    assert "blind_spots" in blob
    assert "key_claims" in blob


def test_format_perspectives_blob_skips_unparsed():
    good = _perspective()
    bad = {"lens": "x", "school": "y"}
    blob = ov.format_perspectives_blob([good, bad], ov.SYNTH_INPUT_CLAIMS)
    assert "schmitt" in blob
    assert "### x" not in blob


def test_format_perspective_rejects_unknown_mode():
    try:
        ov.format_perspective_for_synthesist(_perspective(), "essays")
        assert False, "should have raised"
    except ValueError as e:
        assert "synth_input" in str(e)


def test_load_paideia_plan_missing_axis(tmp_path):
    import json as _json
    bad = {"target_vector": {"M": 2}}   # missing other 8 axes
    path = tmp_path / "plan.json"
    path.write_text(_json.dumps(bad), encoding="utf-8")
    try:
        ov.load_paideia_plan(path)
        assert False, "should have raised"
    except SystemExit:
        pass


def _run_standalone():
    import inspect
    import tempfile
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
