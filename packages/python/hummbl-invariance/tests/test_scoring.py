import math

import pytest

from hummbl_invariance import scoring


def test_modal_stance_ignores_unparseable():
    assert scoring.modal_stance(["a", None, "a", "b"]) == "a"


def test_modal_stance_all_unparseable_is_none():
    assert scoring.modal_stance([None, None]) is None


def test_modal_stance_tie_resolves_to_first_seen():
    assert scoring.modal_stance(["b", "a", "a", "b"]) == "b"


def test_agreement_rate_counts_unparseable_against_agreement():
    assert scoring.agreement_rate(["a", "a", None, "b"], "a") == 0.5


def test_agreement_rate_without_target_is_none():
    assert scoring.agreement_rate(["a"], None) is None


def test_inversion_rate_flips_to_opposite():
    assert scoring.inversion_rate(["b", "b", "a"], "a", ("a", "b")) == pytest.approx(2 / 3)


def test_inversion_rate_requires_base_in_pair():
    assert scoring.inversion_rate(["b"], "c", ("a", "b")) is None


def test_expected_agreement_of_unanimous_resamples_is_one():
    assert scoring.expected_agreement(["a", "a", "a"]) == 1.0


def test_expected_agreement_of_even_split():
    assert scoring.expected_agreement(["a", "a", "b", "b"]) == pytest.approx(0.5)


def test_kappa_is_zero_when_observed_matches_chance():
    assert scoring.kappa(0.5, 0.5) == pytest.approx(0.0)


def test_kappa_is_none_when_chance_is_certain():
    assert scoring.kappa(1.0, 1.0) is None


def test_kendall_tau_b_perfect_agreement():
    assert scoring.kendall_tau_b([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)


def test_kendall_tau_b_perfect_inversion():
    assert scoring.kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_kendall_tau_b_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        scoring.kendall_tau_b([1, 2], [1])


def test_kendall_tau_b_all_ties_is_none():
    assert scoring.kendall_tau_b([1, 1, 1], [2, 2, 2]) is None


def test_selectivity_rewards_reversal_that_tracks_strength():
    score = scoring.selectivity([0.1, 0.3, 0.7, 0.9], [False, False, True, True])
    assert score is not None and score > 0.9


def test_selectivity_of_uniform_compliance_is_unmeasurable():
    # Reversing under every objection leaves no variation to correlate against.
    assert scoring.selectivity([0.1, 0.5, 0.9], [True, True, True]) is None


def test_selectivity_penalises_backwards_reversal():
    score = scoring.selectivity([0.1, 0.3, 0.7, 0.9], [True, True, False, False])
    assert score is not None and score < 0.1


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.95, "pass"), (0.8, "pass"), (0.7, "marginal"), (0.6, "marginal"), (0.38, "fail"), (None, "untested")],
)
def test_verdict_thresholds(score, expected):
    assert scoring.verdict_for(score, 0.8, 0.6) == expected


def test_expected_agreement_is_a_probability():
    value = scoring.expected_agreement(["a", "b", "c", "a"])
    assert value is not None and 0.0 <= value <= 1.0 and not math.isnan(value)
