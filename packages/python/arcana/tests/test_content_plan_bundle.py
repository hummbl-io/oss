"""Tests for generate_content_plan_bundle.py -- build_bundle + validate_bundle
+ normalize_plan_intent + implemented_generators.

Pure CPU. Constructs synthetic PAIDEIA plan dicts (reusing generate_paideia_plan
helpers) to exercise the bundle logic. Does NOT call Ollama.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_content_plan_bundle as gcpb
import generate_paideia_plan as gpp


def _vec(value: int = 2) -> dict:
    return {a: value for a in gpp.AXES}


def _per_axis(target: int = 2, referent: str = "artifact",
              rationale: str = "Because reasons.",
              citation: str = "Mayer 2009", intent: str | None = None) -> dict:
    out: dict = {}
    for a in gpp.AXES:
        entry = {"target": target, "referent": referent,
                 "rationale": rationale, "citation": citation}
        if intent is not None:
            entry["intent"] = intent
        out[a] = entry
    return out


def _plan(**overrides) -> dict:
    base = {
        "instructional_intent": True,
        "target_vector": _vec(),
        "per_axis": _per_axis(),
        "constraints": {"load_budget": "med", "modality_budget": 3},
        "downstream_hints": {
            "generate_outline": "build a relational outline",
            "generate_examples": "two worked examples",
            "generate_assessment": "retrieval + feedback",
            "generate_delivery": "solo reading path",
        },
        "content_type_warning": "",
    }
    base.update(overrides)
    return base


# ---- build_bundle ------------------------------------------------------ #

def test_build_bundle_happy():
    bundle = gcpb.build_bundle(_plan())
    assert bundle["bundle_version"] == gcpb.BUNDLE_VERSION
    assert bundle["plan"]["instructional_intent"] is True


def test_build_bundle_downstream_has_all_known_generators():
    bundle = gcpb.build_bundle(_plan())
    for gen in gcpb.KNOWN_DOWNSTREAM:
        assert gen in bundle["downstream"]
        entry = bundle["downstream"][gen]
        assert "hint" in entry and "implemented" in entry and "status" in entry


def test_build_bundle_downstream_hints_flow_through():
    bundle = gcpb.build_bundle(_plan())
    assert bundle["downstream"]["generate_outline"]["hint"] == "build a relational outline"


def test_build_bundle_rejects_invalid_plan():
    bad = _plan()
    bad["target_vector"]["M"] = 9  # out of range
    try:
        gcpb.build_bundle(bad)
        raise AssertionError("should reject invalid plan")
    except ValueError as e:
        assert "invalid PAIDEIA plan" in str(e)


# ---- implemented_generators (honest gate) ------------------------------ #

def test_known_downstream_all_currently_unimplemented():
    """Snapshot: today none of the four downstream generators exist, so
    implemented_generators() is empty and every downstream entry is
    not_implemented. When Lane 4 lands a generator, this test must be updated
    -- that is the intended signal, not a regression."""
    impl = gcpb.implemented_generators()
    assert impl <= set(gcpb.KNOWN_DOWNSTREAM)
    bundle = gcpb.build_bundle(_plan())
    for gen in gcpb.KNOWN_DOWNSTREAM:
        expected = gen in impl
        assert bundle["downstream"][gen]["implemented"] is expected
        assert bundle["downstream"][gen]["status"] == (
            "implemented" if expected else "not_implemented")


# ---- normalize_plan_intent (v0.2 additive layer) ----------------------- #

def test_normalize_intent_adds_default_required():
    plan = gcpb.normalize_plan_intent(_plan())
    for a in gpp.AXES:
        assert plan["per_axis"][a]["intent"] == "required"


def test_normalize_intent_preserves_existing():
    plan = gcpb.normalize_plan_intent(_plan(per_axis=_per_axis(intent="n_a")))
    for a in gpp.AXES:
        assert plan["per_axis"][a]["intent"] == "n_a"


def test_normalize_intent_rejects_bad_value():
    bad = _plan(per_axis=_per_axis(intent="maybe"))
    try:
        gcpb.normalize_plan_intent(bad)
        raise AssertionError("should reject bad intent value")
    except ValueError as e:
        assert "intent" in str(e)


def test_normalize_intent_does_not_mutate_input():
    original = _plan()
    snapshot = {a: dict(e) for a, e in original["per_axis"].items()}
    gcpb.normalize_plan_intent(original)
    assert original["per_axis"] == snapshot


def test_normalize_intent_accepts_all_valid_values():
    for v in gcpb.INTENT_VALUES:
        plan = gcpb.normalize_plan_intent(_plan(per_axis=_per_axis(intent=v)))
        assert all(plan["per_axis"][a]["intent"] == v for a in gpp.AXES)


# ---- intent_polarity derivation ---------------------------------------- #

def test_intent_polarity_defaults_all_required():
    bundle = gcpb.build_bundle(_plan())
    assert set(bundle["intent_polarity"]) == set(gpp.AXES)
    assert all(v == "required" for v in bundle["intent_polarity"].values())


def test_intent_polarity_reflects_per_axis_intent():
    pa = _per_axis()
    pa["S"]["intent"] = "deliberate_absent"
    pa["L"]["intent"] = "n_a"
    bundle = gcpb.build_bundle(_plan(per_axis=pa))
    assert bundle["intent_polarity"]["S"] == "deliberate_absent"
    assert bundle["intent_polarity"]["L"] == "n_a"
    assert bundle["intent_polarity"]["M"] == "required"


# ---- validate_bundle --------------------------------------------------- #

def test_validate_bundle_happy():
    ok, why = gcpb.validate_bundle(gcpb.build_bundle(_plan()))
    assert ok, why


def test_validate_bundle_rejects_wrong_version():
    b = gcpb.build_bundle(_plan())
    b["bundle_version"] = "wrong"
    ok, why = gcpb.validate_bundle(b)
    assert not ok and "bundle_version" in why


def test_validate_bundle_rejects_bad_plan():
    b = gcpb.build_bundle(_plan())
    b["plan"]["target_vector"]["D"] = "x"
    ok, why = gcpb.validate_bundle(b)
    assert not ok and "plan" in why


def test_validate_bundle_rejects_missing_downstream_generator():
    b = gcpb.build_bundle(_plan())
    del b["downstream"]["generate_assessment"]
    ok, why = gcpb.validate_bundle(b)
    assert not ok and "generate_assessment" in why


def test_validate_bundle_rejects_missing_intent_polarity_axis():
    b = gcpb.build_bundle(_plan())
    del b["intent_polarity"]["P"]
    ok, why = gcpb.validate_bundle(b)
    assert not ok and "P" in why


def test_validate_bundle_rejects_bad_intent_value():
    b = gcpb.build_bundle(_plan())
    b["intent_polarity"]["M"] = "maybe"
    ok, why = gcpb.validate_bundle(b)
    assert not ok and "intent_polarity" in why


# ---- structural -------------------------------------------------------- #

def test_bundle_version_is_v1():
    assert gcpb.BUNDLE_VERSION == "content-plan-bundle-v1"


def test_known_downstream_has_four_generators():
    assert len(gcpb.KNOWN_DOWNSTREAM) == 4
    assert set(gcpb.KNOWN_DOWNSTREAM) == {
        "generate_outline", "generate_examples",
        "generate_assessment", "generate_delivery"}


def test_intent_values_are_three():
    assert set(gcpb.INTENT_VALUES) == {"required", "deliberate_absent", "n_a"}


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
