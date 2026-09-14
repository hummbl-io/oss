"""Tests for the inference tier router (inference_tier.py).

Component 4 of PROPOSAL-012: cost-optimized inference tier routing.
"""

from __future__ import annotations

import pytest

from hummbl_bus.inference_tier import (
    baseline_tier,
    recommended_tier,
    escalate_tier,
    estimate_cost,
    validate_tier_escalation,
)


class TestBaselineTier:
    """Tests for baseline_tier()."""

    def test_baseline_is_t0(self) -> None:
        assert baseline_tier() == "T0"


class TestRecommendedTier:
    """Tests for recommended_tier()."""

    def test_default_is_t0(self) -> None:
        assert recommended_tier(msg_type="STATUS") == "T0"

    def test_review_gate_types_are_t2(self) -> None:
        for mtype in ("PROPOSAL", "REVIEW", "ACK", "VETO", "DECISION",
                       "APPROVE", "REJECT", "BLOCKED"):
            assert recommended_tier(msg_type=mtype) == "T2"

    def test_p0_priority_is_t2(self) -> None:
        assert recommended_tier(msg_type="STATUS", priority="P0") == "T2"

    def test_p1_priority_is_t2(self) -> None:
        assert recommended_tier(msg_type="STATUS", priority="P1") == "T2"

    def test_p2_priority_is_t0(self) -> None:
        assert recommended_tier(msg_type="STATUS", priority="P2") == "T0"

    def test_large_model_flag_is_t1(self) -> None:
        assert recommended_tier(msg_type="STATUS", requires_large_model=True) == "T1"

    def test_complexity_keywords_trigger_t1(self) -> None:
        for kw in ("deep reasoning", "code generation", "security review",
                    "threat model", "architecture design"):
            assert recommended_tier(msg_type="STATUS", description=kw) == "T1"

    def test_long_context_keyword_triggers_t1(self) -> None:
        assert recommended_tier(msg_type="STATUS", description="needs 128k context") == "T1"

    def test_case_insensitive_msg_type(self) -> None:
        assert recommended_tier(msg_type="proposal") == "T2"
        assert recommended_tier(msg_type="Proposal") == "T2"

    def test_whitespace_in_msg_type(self) -> None:
        assert recommended_tier(msg_type="  STATUS  ") == "T0"


class TestEscalateTier:
    """Tests for escalate_tier()."""

    def test_valid_escalation(self) -> None:
        assert escalate_tier("T0", "T1", "needs code generation") == "T1"

    def test_valid_two_step_escalation(self) -> None:
        assert escalate_tier("T0", "T2", "P0 review gate") == "T2"

    def test_no_justification_raises(self) -> None:
        with pytest.raises(ValueError, match="justification"):
            escalate_tier("T0", "T1", "")

    def test_whitespace_justification_raises(self) -> None:
        with pytest.raises(ValueError, match="justification"):
            escalate_tier("T0", "T1", "   ")

    def test_downgrade_raises(self) -> None:
        with pytest.raises(ValueError, match="target tier > current"):
            escalate_tier("T2", "T1", "downgrade attempt")

    def test_same_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="target tier > current"):
            escalate_tier("T1", "T1", "same tier")

    def test_case_insensitive_tiers(self) -> None:
        assert escalate_tier("t0", "t1", "needed") == "t1"


class TestEstimateCost:
    """Tests for estimate_cost()."""

    def test_t0_is_free(self) -> None:
        assert estimate_cost("T0") == 0.0

    def test_t1_cost(self) -> None:
        # 1500 tokens * $0.001/1K = $0.0015
        cost = estimate_cost("T1", input_tokens=1000, output_tokens=500)
        assert cost == pytest.approx(0.0015)

    def test_t2_cost(self) -> None:
        # 1500 tokens * $0.05/1K = $0.075
        cost = estimate_cost("T2", input_tokens=1000, output_tokens=500)
        assert cost == pytest.approx(0.075)

    def test_unknown_tier_is_free(self) -> None:
        assert estimate_cost("T9") == 0.0

    def test_case_insensitive(self) -> None:
        assert estimate_cost("t0") == 0.0


class TestValidateTierEscalation:
    """Tests for validate_tier_escalation()."""

    def test_no_tier_declared_is_ok(self) -> None:
        validate_tier_escalation(msg_type="STATUS", body="just a message")

    def test_tier_at_recommendation_is_ok(self) -> None:
        body = "model_tier=T0; desc=simple task"
        validate_tier_escalation(msg_type="STATUS", body=body)

    def test_escalation_with_justification_is_ok(self) -> None:
        body = "model_tier=T2; tier_justification=P0 review; desc=urgent"
        validate_tier_escalation(msg_type="STATUS", body=body)

    def test_escalation_without_justification_warns(self) -> None:
        body = "model_tier=T2; desc=simple task"
        # Should not raise (enforce=False by default)
        validate_tier_escalation(msg_type="STATUS", body=body)

    def test_escalation_without_justification_enforced_raises(self) -> None:
        body = "model_tier=T2; desc=simple task"
        with pytest.raises(ValueError, match="exceeds recommended"):
            validate_tier_escalation(msg_type="STATUS", body=body, enforce=True)

    def test_t1_for_review_gate_is_ok(self) -> None:
        # T1 <= T2 recommended for REVIEW, so no escalation
        body = "model_tier=T1"
        validate_tier_escalation(msg_type="REVIEW", body=body)
