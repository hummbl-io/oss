import random

import pytest

from hummbl_invariance import build_axis
from hummbl_invariance.models import Observation, Probe, Pushback, Variant

STANCES = ("cost_first", "capability_first")


def make_probe(**overrides) -> Probe:
    defaults = dict(
        question="q?",
        stances=STANCES,
        paraphrases=("p1", "p2", "p3", "p4"),
        negations=("n1", "n2", "n3", "n4"),
        personas=("persona A", "persona B"),
        options=("alpha", "beta", "gamma"),
        temperatures=(0.0, 0.5, 1.0),
        pushbacks=(
            Pushback("weak", 0.1),
            Pushback("middling", 0.5),
            Pushback("strong", 0.9),
        ),
        checkpoints=("ckpt-1", "ckpt-2"),
    )
    defaults.update(overrides)
    return Probe(**defaults)


def observe(variants, stances):
    return [
        Observation(variant=v, raw=s or "", stance=s) for v, s in zip(variants, stances, strict=True)
    ]


def test_probe_rejects_single_stance():
    with pytest.raises(ValueError):
        Probe(question="q", stances=("only",))


def test_probe_rejects_duplicate_stances():
    with pytest.raises(ValueError):
        Probe(question="q", stances=("a", "a"))


def test_pushback_rejects_out_of_range_strength():
    with pytest.raises(ValueError):
        Pushback("text", 1.5)


def test_paraphrase_axis_holds_when_stance_never_moves():
    axis = build_axis("paraphrase")
    probe = make_probe()
    variants = axis.build(probe, 4, random.Random(0))
    result = axis.score(observe(variants, ["cost_first"] * 4), "cost_first", probe)
    assert result.score == 1.0
    assert result.verdict == "pass"


def test_paraphrase_axis_fails_when_stance_wanders():
    axis = build_axis("paraphrase")
    probe = make_probe()
    variants = axis.build(probe, 4, random.Random(0))
    stances = ["cost_first", "capability_first", "capability_first", "capability_first"]
    result = axis.score(observe(variants, stances), "cost_first", probe)
    assert result.score == 0.25
    assert result.verdict == "fail"


def test_axis_without_material_is_untested_not_zero():
    axis = build_axis("persona")
    probe = make_probe(personas=())
    variants = axis.build(probe, 4, random.Random(0))
    result = axis.score(observe(variants, []), "cost_first", probe)
    assert result.verdict == "untested"
    assert result.score is None


def test_order_axis_shuffles_options_deterministically():
    axis = build_axis("order")
    probe = make_probe()
    first = axis.build(probe, 3, random.Random(7))
    second = axis.build(probe, 3, random.Random(7))
    assert [v.meta["order"] for v in first] == [v.meta["order"] for v in second]
    assert all(sorted(v.meta["order"]) == sorted(probe.options) for v in first)


def test_order_axis_needs_at_least_two_options():
    axis = build_axis("order")
    assert axis.build(make_probe(options=("only",)), 3, random.Random(0)) == []


def test_negation_axis_expects_inversion():
    axis = build_axis("negation")
    probe = make_probe()
    variants = axis.build(probe, 4, random.Random(0))
    result = axis.score(observe(variants, ["capability_first"] * 4), "cost_first", probe)
    assert result.score == 1.0
    assert result.verdict == "pass"
    assert result.detail["expected_stance"] == "capability_first"


def test_negation_axis_fails_when_stance_does_not_flip():
    axis = build_axis("negation")
    probe = make_probe()
    variants = axis.build(probe, 4, random.Random(0))
    result = axis.score(observe(variants, ["cost_first"] * 4), "cost_first", probe)
    assert result.score == 0.0
    assert result.verdict == "fail"


def test_negation_axis_declines_a_non_binary_probe():
    axis = build_axis("negation")
    probe = make_probe(stances=("a", "b", "c"))
    assert axis.build(probe, 4, random.Random(0)) == []


def test_temperature_axis_carries_each_temperature():
    axis = build_axis("temperature")
    variants = axis.build(make_probe(), 3, random.Random(0))
    assert [v.temperature for v in variants] == [0.0, 0.5, 1.0]


def test_checkpoint_axis_carries_each_endpoint():
    axis = build_axis("checkpoint")
    variants = axis.build(make_probe(), 5, random.Random(0))
    assert [v.endpoint for v in variants] == ["ckpt-1", "ckpt-2"]


def test_pushback_axis_scores_selective_reversal_high():
    axis = build_axis("pushback")
    probe = make_probe()
    variants = axis.build(probe, 3, random.Random(0))
    stances = ["cost_first", "cost_first", "capability_first"]
    result = axis.score(observe(variants, stances), "cost_first", probe)
    assert result.score is not None and result.score > 0.9
    assert result.detail["tau"] > 0


def test_pushback_axis_flags_uniform_compliance():
    axis = build_axis("pushback")
    probe = make_probe()
    variants = axis.build(probe, 3, random.Random(0))
    result = axis.score(observe(variants, ["capability_first"] * 3), "cost_first", probe)
    assert result.detail["reversal_rate"] == 1.0
    assert "surface compliance" in result.detail["reading"]
    assert result.score == 0.0
    assert result.verdict == "fail"


def test_pushback_axis_flags_rigidity_above_compliance():
    axis = build_axis("pushback")
    probe = make_probe()
    variants = axis.build(probe, 3, random.Random(0))
    rigid = axis.score(observe(variants, ["cost_first"] * 3), "cost_first", probe)
    compliant = axis.score(observe(variants, ["capability_first"] * 3), "cost_first", probe)
    assert "rigidity" in rigid.detail["reading"]
    assert rigid.score > compliant.score


def test_pushback_axis_needs_a_base_stance():
    axis = build_axis("pushback")
    probe = make_probe()
    variants = axis.build(probe, 3, random.Random(0))
    result = axis.score(observe(variants, ["cost_first"] * 3), None, probe)
    assert result.verdict == "untested"


def test_unparseable_responses_are_counted_and_penalised():
    axis = build_axis("paraphrase")
    probe = make_probe()
    variants = axis.build(probe, 4, random.Random(0))
    result = axis.score(observe(variants, ["cost_first", None, "cost_first", None]), "cost_first", probe)
    assert result.unparseable == 2
    assert result.score == 0.5


def test_build_axis_rejects_unknown_key():
    with pytest.raises(ValueError):
        build_axis("vibes")
