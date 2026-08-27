from __future__ import annotations

from hummbl_cognition.sonnet5_replay_receipt import (
    Sonnet5ReplayError,
    compute_receipt_hash,
    create_sonnet5_replay_receipt,
    validate_sonnet5_replay_receipt,
)


def _hold_receipt() -> dict:
    """A realistic 'hold' receipt based on the morning receipt's findings."""
    return create_sonnet5_replay_receipt(
        prompt_corpus_ref="hummbl-cognition/tests/fixtures/sonnet5_replay_corpus.jsonl",
        replay_methodology="token_counting_api",
        sonnet_46_token_count=1_000_000,
        sonnet_5_token_count=1_300_000,
        token_delta_ratio=1.30,
        token_delta_pct=30.0,
        standard_pricing_per_1m_input_usd=3.0,
        standard_pricing_per_1m_output_usd=15.0,
        sonnet_46_cost_usd=12.0,
        sonnet_5_cost_usd=15.6,
        cost_delta_pct=30.0,
        behavior_changes_detected=[
            "adaptive_thinking_default_on",
            "manual_extended_thinking_returns_400",
            "non_default_sampling_returns_400",
            "prompt_cache_invalidated_on_model_switch",
        ],
        max_tokens_truncation_observed=True,
        prompt_cache_invalidated=True,
        admission_recommendation="hold",
        corpus_size_prompts=500,
        notes="Token counting API replay. 30% token delta confirmed. Truncation observed on long-output prompts. Hold pending max_tokens revision and 400-mitigation.",
    )


def _conditional_receipt() -> dict:
    return create_sonnet5_replay_receipt(
        prompt_corpus_ref="hummbl-cognition/tests/fixtures/sonnet5_replay_corpus.jsonl",
        replay_methodology="full_replay",
        sonnet_46_token_count=1_000_000,
        sonnet_5_token_count=1_300_000,
        token_delta_ratio=1.30,
        token_delta_pct=30.0,
        standard_pricing_per_1m_input_usd=3.0,
        standard_pricing_per_1m_output_usd=15.0,
        sonnet_46_cost_usd=12.0,
        sonnet_5_cost_usd=15.6,
        cost_delta_pct=30.0,
        behavior_changes_detected=[
            "adaptive_thinking_default_on",
            "manual_extended_thinking_returns_400",
            "non_default_sampling_returns_400",
        ],
        max_tokens_truncation_observed=True,
        prompt_cache_invalidated=True,
        admission_recommendation="conditional",
        admission_conditions=[
            "revise max_tokens to 1.3x Sonnet 4.6 values",
            "remove manual extended_thinking blocks (returns 400 on Sonnet 5)",
            "set temperature=1.0 and top_p=0.95 (non-default sampling returns 400)",
        ],
        operator_approval_ref="risk-acceptance-2026-07-04-sonnet5",
        eval_scores=[
            {
                "eval_name": "BrowseComp",
                "sonnet_46_score": 21.5,
                "sonnet_5_score": 50.0,
                "score_delta": 28.5,
            },
            {
                "eval_name": "HumanEval",
                "sonnet_46_score": 92.0,
                "sonnet_5_score": 95.0,
                "score_delta": 3.0,
            },
        ],
        corpus_size_prompts=500,
        notes="Full replay with evals. Conditional admission with max_tokens revision and 400-mitigation.",
    )


def test_validate_accepts_hold_receipt():
    valid, errors = validate_sonnet5_replay_receipt(_hold_receipt())

    assert valid, errors


def test_validate_accepts_conditional_receipt():
    valid, errors = validate_sonnet5_replay_receipt(_conditional_receipt())

    assert valid, errors


def test_validate_rejects_extra_field():
    receipt = _hold_receipt()
    receipt["raw_secret"] = "sk-leaked"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("unexpected fields" in e for e in errors)


def test_validate_rejects_missing_required_field():
    receipt = _hold_receipt()
    del receipt["token_delta_ratio"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("missing required field: token_delta_ratio" in e for e in errors)


def test_validate_rejects_bad_receipt_id_prefix():
    receipt = _hold_receipt()
    receipt["receipt_id"] = "wrong-prefix-123"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_receipt_id_with_uppercase():
    receipt = _hold_receipt()
    receipt["receipt_id"] = "sonnet5-replay-INVALID-ID"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("receipt_id must match pattern" in e for e in errors)


def test_validate_rejects_bad_timestamp():
    receipt = _hold_receipt()
    receipt["timestamp"] = "not-a-date"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_timezoneless_timestamp():
    receipt = _hold_receipt()
    receipt["timestamp"] = "2026-07-04T00:00:00"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("timestamp must be an RFC3339 date-time" in e for e in errors)


def test_validate_rejects_inconsistent_token_delta_ratio():
    """token_delta_ratio must be consistent with token counts (admission-gating receipt)."""
    receipt = _hold_receipt()
    receipt["sonnet_5_token_count"] = 0
    receipt["token_delta_ratio"] = 1.3  # inconsistent: 0/1000000 = 0.0, not 1.3
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("token_delta_ratio=1.3 is inconsistent" in e for e in errors)


def test_validate_rejects_inconsistent_token_delta_pct():
    """token_delta_pct must be consistent with token counts."""
    receipt = _hold_receipt()
    receipt["sonnet_5_token_count"] = 1_500_000  # 50% increase, not 30%
    receipt["token_delta_pct"] = 30.0  # inconsistent
    receipt["token_delta_ratio"] = 1.5  # consistent with 1.5M/1M
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("token_delta_pct=30.0 is inconsistent" in e for e in errors)


def test_validate_rejects_both_zero_counts_with_nonzero_ratio():
    """Both token counts 0 with token_delta_ratio=1.3 is the exact review probe."""
    receipt = _hold_receipt()
    receipt["sonnet_46_token_count"] = 0
    receipt["sonnet_5_token_count"] = 0
    receipt["token_delta_ratio"] = 1.3
    receipt["token_delta_pct"] = 30.0
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("token_delta_ratio=1.3 is inconsistent" in e for e in errors)
    assert any("token_delta_pct=30.0 is inconsistent" in e for e in errors)


def test_validate_accepts_consistent_token_math():
    """Consistent token math (ratio and pct match recomputed values) is valid."""
    receipt = _hold_receipt()
    # 1_000_000 / 1_300_000 → ratio 1.30, pct 30.0 (already the fixture default)
    valid, errors = validate_sonnet5_replay_receipt(receipt)
    assert valid, errors


def test_validate_accepts_sub_unity_ratio_math():
    """Sub-unity ratio (Sonnet 5 uses fewer tokens) with consistent math is valid."""
    receipt = _hold_receipt()
    receipt["sonnet_46_token_count"] = 1_000_000
    receipt["sonnet_5_token_count"] = 990_000
    receipt["token_delta_ratio"] = 0.99
    receipt["token_delta_pct"] = -1.0
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert valid, errors


def test_validate_rejects_empty_prompt_corpus_ref():
    receipt = _hold_receipt()
    receipt["prompt_corpus_ref"] = ""
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("prompt_corpus_ref must be a non-empty string" in e for e in errors)


def test_validate_rejects_bad_methodology():
    receipt = _hold_receipt()
    receipt["replay_methodology"] = "vibes_based"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("replay_methodology:" in e for e in errors)


def test_validate_rejects_negative_token_count():
    receipt = _hold_receipt()
    receipt["sonnet_5_token_count"] = -1
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any(
        "sonnet_5_token_count must be a non-negative integer" in e for e in errors
    )


def test_validate_rejects_negative_token_delta_ratio():
    receipt = _hold_receipt()
    receipt["token_delta_ratio"] = -0.5
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("token_delta_ratio must be >= 0" in e for e in errors)


def test_validate_rejects_bad_behavior_change():
    receipt = _hold_receipt()
    receipt["behavior_changes_detected"] = ["quantum_collapse"]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("behavior_changes_detected item" in e for e in errors)


def test_validate_rejects_bad_admission_recommendation():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "maybe"
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("admission_recommendation:" in e for e in errors)


def test_side_by_side_eval_requires_eval_scores():
    receipt = _hold_receipt()
    receipt["replay_methodology"] = "side_by_side_eval"
    # no eval_scores
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("requires eval_scores" in e for e in errors)


def test_full_replay_requires_eval_scores():
    receipt = _hold_receipt()
    receipt["replay_methodology"] = "full_replay"
    # no eval_scores
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("requires eval_scores" in e for e in errors)


def test_admit_requires_operator_approval_ref():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "admit"
    receipt["max_tokens_truncation_observed"] = False
    receipt["behavior_changes_detected"] = []
    # no operator_approval_ref
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("admit requires operator_approval_ref" in e for e in errors)


def test_admit_with_clean_replay_and_approval_is_valid():
    receipt = create_sonnet5_replay_receipt(
        prompt_corpus_ref="corpus.jsonl",
        replay_methodology="token_counting_api",
        sonnet_46_token_count=1_000_000,
        sonnet_5_token_count=1_300_000,
        token_delta_ratio=1.30,
        token_delta_pct=30.0,
        standard_pricing_per_1m_input_usd=3.0,
        standard_pricing_per_1m_output_usd=15.0,
        sonnet_46_cost_usd=12.0,
        sonnet_5_cost_usd=15.6,
        cost_delta_pct=30.0,
        behavior_changes_detected=[],
        max_tokens_truncation_observed=False,
        prompt_cache_invalidated=True,
        admission_recommendation="admit",
        operator_approval_ref="risk-acceptance-2026-07-04-sonnet5-admit",
        notes="Clean replay, no 400s, no truncation, operator approved.",
    )

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert valid, errors


def test_truncation_blocks_admit():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "admit"
    receipt["operator_approval_ref"] = "risk-acceptance-001"
    receipt["behavior_changes_detected"] = []
    # max_tokens_truncation_observed stays True
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("max_tokens_truncation_observed" in e for e in errors)


def test_400_change_blocks_admit_without_condition():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "admit"
    receipt["operator_approval_ref"] = "risk-acceptance-001"
    receipt["max_tokens_truncation_observed"] = False
    receipt["behavior_changes_detected"] = ["manual_extended_thinking_returns_400"]
    receipt["admission_conditions"] = []  # not addressed
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("manual_extended_thinking_returns_400" in e for e in errors)


def test_400_change_allows_admit_with_addressed_condition():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "admit"
    receipt["operator_approval_ref"] = "risk-acceptance-001"
    receipt["max_tokens_truncation_observed"] = False
    receipt["behavior_changes_detected"] = ["manual_extended_thinking_returns_400"]
    receipt["admission_conditions"] = [
        "remove manual extended_thinking blocks (returns 400 on Sonnet 5)",
    ]
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert valid, errors


def test_non_default_sampling_400_blocks_admit_without_condition():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "admit"
    receipt["operator_approval_ref"] = "risk-acceptance-001"
    receipt["max_tokens_truncation_observed"] = False
    receipt["behavior_changes_detected"] = ["non_default_sampling_returns_400"]
    receipt["admission_conditions"] = []
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("non_default_sampling_returns_400" in e for e in errors)


def test_conditional_requires_operator_approval_and_conditions():
    receipt = _hold_receipt()
    receipt["admission_recommendation"] = "conditional"
    # no operator_approval_ref, no admission_conditions
    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("conditional requires operator_approval_ref" in e for e in errors)
    assert any(
        "conditional requires a non-empty admission_conditions" in e for e in errors
    )


def test_tampered_hash_rejected():
    receipt = _hold_receipt()
    receipt["receipt_hash"] = "0" * 64

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert not valid
    assert any("receipt_hash does not match" in e for e in errors)


def test_create_raises_on_invalid():
    try:
        create_sonnet5_replay_receipt(
            prompt_corpus_ref="",
            replay_methodology="token_counting_api",
            sonnet_46_token_count=1000,
            sonnet_5_token_count=1300,
            token_delta_ratio=1.3,
            token_delta_pct=30.0,
            standard_pricing_per_1m_input_usd=3.0,
            standard_pricing_per_1m_output_usd=15.0,
            sonnet_46_cost_usd=12.0,
            sonnet_5_cost_usd=15.6,
            cost_delta_pct=30.0,
            behavior_changes_detected=[],
            max_tokens_truncation_observed=False,
            prompt_cache_invalidated=True,
            admission_recommendation="hold",
        )
        assert False, "should have raised"
    except Sonnet5ReplayError as exc:
        assert "prompt_corpus_ref" in str(exc)


def test_create_omits_empty_optional_fields():
    receipt = create_sonnet5_replay_receipt(
        prompt_corpus_ref="corpus.jsonl",
        replay_methodology="token_counting_api",
        sonnet_46_token_count=1000,
        sonnet_5_token_count=1300,
        token_delta_ratio=1.3,
        token_delta_pct=30.0,
        standard_pricing_per_1m_input_usd=3.0,
        standard_pricing_per_1m_output_usd=15.0,
        sonnet_46_cost_usd=12.0,
        sonnet_5_cost_usd=15.6,
        cost_delta_pct=30.0,
        behavior_changes_detected=[],
        max_tokens_truncation_observed=False,
        prompt_cache_invalidated=True,
        admission_recommendation="hold",
    )

    assert "corpus_size_prompts" not in receipt
    assert "eval_scores" not in receipt
    assert "content_type_breakdown" not in receipt
    assert "admission_conditions" not in receipt
    assert "operator_approval_ref" not in receipt


def test_chinese_corpus_can_show_sub_unity_ratio():
    """Chinese text may show < 1.0 ratio per Anthropic — validator allows it."""
    receipt = create_sonnet5_replay_receipt(
        prompt_corpus_ref="chinese_corpus.jsonl",
        replay_methodology="token_counting_api",
        sonnet_46_token_count=1_000_000,
        sonnet_5_token_count=990_000,
        token_delta_ratio=0.99,
        token_delta_pct=-1.0,
        standard_pricing_per_1m_input_usd=3.0,
        standard_pricing_per_1m_output_usd=15.0,
        sonnet_46_cost_usd=12.0,
        sonnet_5_cost_usd=11.88,
        cost_delta_pct=-1.0,
        behavior_changes_detected=[],
        max_tokens_truncation_observed=False,
        prompt_cache_invalidated=True,
        admission_recommendation="hold",
        notes="Chinese-heavy corpus shows ~1.0x per Anthropic guidance.",
    )

    valid, errors = validate_sonnet5_replay_receipt(receipt)

    assert valid, errors
