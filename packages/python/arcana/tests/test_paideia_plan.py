"""Tests for generate_paideia_plan.py — validate_plan + slugify.

Pure CPU. Constructs synthetic plan dicts to exercise validate_plan, and
checks slugify edge cases. Does NOT call Ollama.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_paideia_plan as gpp


def _vec(value: int = 2) -> dict:
    return {a: value for a in gpp.AXES}


def _per_axis(target: int = 2, referent: str = "artifact",
              rationale: str = "Because reasons.",
              citation: str = "Mayer 2009") -> dict:
    return {a: {"target": target, "referent": referent,
                "rationale": rationale, "citation": citation}
            for a in gpp.AXES}


def _plan(**overrides) -> dict:
    base = {
        "instructional_intent": True,
        "target_vector": _vec(),
        "per_axis": _per_axis(),
        "constraints": {"load_budget": "med", "modality_budget": 3},
        "downstream_hints": {},
        "content_type_warning": "",
    }
    base.update(overrides)
    return base


# ---- happy path -------------------------------------------------------- #

def test_validate_plan_happy():
    ok, why = gpp.validate_plan(_plan())
    assert ok, why


# ---- target_vector errors --------------------------------------------- #

def test_validate_plan_missing_target_vector():
    ok, why = gpp.validate_plan(_plan(target_vector=None))
    assert not ok and "target_vector" in why


def test_validate_plan_target_vector_missing_axis():
    bad_vec = _vec()
    del bad_vec["L"]
    ok, why = gpp.validate_plan(_plan(target_vector=bad_vec))
    assert not ok and "L" in why


def test_validate_plan_target_vector_out_of_range():
    bad_vec = _vec()
    bad_vec["M"] = 5
    ok, why = gpp.validate_plan(_plan(target_vector=bad_vec))
    assert not ok and "0..4" in why


def test_validate_plan_target_vector_negative():
    bad_vec = _vec()
    bad_vec["D"] = -1
    ok, _why = gpp.validate_plan(_plan(target_vector=bad_vec))
    assert not ok


def test_validate_plan_target_vector_non_int():
    bad_vec = _vec()
    bad_vec["E"] = "two"
    ok, _why = gpp.validate_plan(_plan(target_vector=bad_vec))
    assert not ok


# ---- per_axis errors --------------------------------------------------- #

def test_validate_plan_missing_per_axis():
    ok, why = gpp.validate_plan(_plan(per_axis=None))
    assert not ok and "per_axis" in why


def test_validate_plan_per_axis_missing_axis():
    bad = _per_axis()
    del bad["S"]
    ok, why = gpp.validate_plan(_plan(per_axis=bad))
    assert not ok and "S" in why


def test_validate_plan_per_axis_missing_field():
    bad = _per_axis()
    del bad["M"]["citation"]
    ok, why = gpp.validate_plan(_plan(per_axis=bad))
    assert not ok and "citation" in why


def test_validate_plan_per_axis_bad_referent():
    bad = _per_axis()
    bad["P"]["referent"] = "wonky"
    ok, why = gpp.validate_plan(_plan(per_axis=bad))
    assert not ok and "referent" in why


# ---- v0.2 intent polarity (additive, optional) ------------------------- #

def test_validate_plan_accepts_optional_intent():
    pa = _per_axis()
    pa["S"]["intent"] = "deliberate_absent"
    pa["L"]["intent"] = "n_a"
    ok, why = gpp.validate_plan(_plan(per_axis=pa))
    assert ok, why


def test_validate_plan_rejects_bad_intent_value():
    pa = _per_axis()
    pa["M"]["intent"] = "maybe"
    ok, why = gpp.validate_plan(_plan(per_axis=pa))
    assert not ok and "intent" in why


def test_validate_plan_accepts_all_valid_intent_values():
    for v in ("required", "deliberate_absent", "n_a"):
        pa = _per_axis()
        pa["P"]["intent"] = v
        ok, why = gpp.validate_plan(_plan(per_axis=pa))
        assert ok, f"{v}: {why}"


def test_validate_plan_per_axis_valid_referents():
    for r in ("artifact", "reader_state", "reader_demand"):
        bad = _per_axis(referent=r)
        ok, why = gpp.validate_plan(_plan(per_axis=bad))
        assert ok, f"{r}: {why}"


# ---- constraints ------------------------------------------------------- #

def test_validate_plan_missing_constraints():
    p = _plan()
    del p["constraints"]
    ok, why = gpp.validate_plan(p)
    assert not ok and "constraints" in why


# ---- slugify ----------------------------------------------------------- #

def test_slugify_basic():
    assert gpp.slugify("Hello World") == "hello-world"


def test_slugify_punctuation():
    assert gpp.slugify("Google's New Platform!") == "google-s-new-platform"


def test_slugify_long_truncates():
    s = gpp.slugify("a" * 200)
    assert len(s) <= 60


def test_slugify_custom_max_len():
    assert len(gpp.slugify("a" * 100, max_len=20)) <= 20


def test_slugify_empty_returns_untitled():
    assert gpp.slugify("") == "untitled"
    assert gpp.slugify("   ") == "untitled"
    assert gpp.slugify("!!!") == "untitled"


def test_slugify_strips_dashes():
    assert not gpp.slugify("---hello---").startswith("-")
    assert not gpp.slugify("---hello---").endswith("-")


# ---- structural -------------------------------------------------------- #

def test_axes_count_is_ten():
    assert len(gpp.AXES) == 10
    assert "Em" in gpp.AXES


def test_log_columns_include_provenance():
    assert "timestamp_utc" in gpp.LOG_COLUMNS
    assert "prompt_version" in gpp.LOG_COLUMNS
    assert "target_vector" in gpp.LOG_COLUMNS


def _run_standalone():
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
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
