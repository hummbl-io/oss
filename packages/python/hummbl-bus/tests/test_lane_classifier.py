"""Unit tests for lane_classifier.py ΓÇö Component 2 of PROPOSAL-012."""

import logging
import os
from unittest.mock import patch

import pytest

from hummbl_bus.lane_classifier import (
    classify_lane,
    classify_message,
    classify_message_from_body,
    expected_model_tier,
    is_background,
    is_foreground,
    validate_model_tier_for_task,
)


class TestClassifyMessage:
    """Tests for classify_message() based on message type."""

    def test_proposal_is_foreground(self):
        assert classify_message("PROPOSAL") == "foreground"

    def test_review_is_foreground(self):
        assert classify_message("REVIEW") == "foreground"

    def test_ack_is_foreground(self):
        assert classify_message("ACK") == "foreground"

    def test_veto_is_foreground(self):
        assert classify_message("VETO") == "foreground"

    def test_decision_is_foreground(self):
        assert classify_message("DECISION") == "foreground"

    def test_status_is_background(self):
        assert classify_message("STATUS") == "background"

    def test_task_complete_is_background(self):
        assert classify_message("TASK_COMPLETE") == "background"

    def test_heartbeat_is_background(self):
        assert classify_message("HEARTBEAT") == "background"

    def test_alert_is_background(self):
        assert classify_message("ALERT") == "background"

    def test_receipt_is_background(self):
        assert classify_message("RECEIPT") == "background"

    def test_priority_p0_forces_foreground(self):
        assert classify_message("STATUS", priority="P0") == "foreground"

    def test_priority_p1_forces_foreground(self):
        assert classify_message("STATUS", priority="P1") == "foreground"

    def test_priority_p2_forces_background(self):
        assert classify_message("PROPOSAL", priority="P2") == "background"

    def test_priority_p3_forces_background(self):
        assert classify_message("PROPOSAL", priority="P3") == "background"

    def test_unknown_type_defaults_foreground(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="hummbl_bus.lane_classifier"):
            assert classify_message("MYSTERY_TYPE") == "foreground"
        assert "Unknown message type" in caplog.text

    def test_case_insensitive(self):
        assert classify_message("status") == "background"
        assert classify_message("proposal") == "foreground"


class TestClassifyLane:
    """Tests for classify_lane() combining lane name + type + priority."""

    def test_audit_lane_is_background(self):
        assert classify_lane("audit/codex/rules-check", "STATUS") == "background"

    def test_health_lane_is_background(self):
        assert classify_lane("health/codex/disk-check", "STATUS") == "background"

    def test_adr_lane_is_foreground(self):
        assert classify_lane("adr/claude-code/token-encryption", "PROPOSAL") == "foreground"

    def test_security_lane_is_foreground(self):
        assert classify_lane("security/codex/stride-review", "REVIEW") == "foreground"

    def test_priority_overrides_lane_prefix(self):
        # audit/ is background by prefix, but P0 forces foreground
        assert classify_lane("audit/codex/rules-check", "STATUS", priority="P0") == "foreground"

    def test_ops_lane_defaults_to_message_type(self):
        # ops/ has no explicit prefix bias
        assert classify_lane("ops/codex/steward-watcher", "STATUS") == "background"
        assert classify_lane("ops/codex/steward-watcher", "PROPOSAL") == "foreground"


class TestIsForegroundBackground:
    """Tests for boolean helpers."""

    def test_is_foreground(self):
        assert is_foreground("PROPOSAL") is True
        assert is_foreground("STATUS") is False

    def test_is_background(self):
        assert is_background("STATUS") is True
        assert is_background("PROPOSAL") is False


class TestClassifyMessageFromBody:
    """Tests for classify_message_from_body() parsing lane= and priority=."""

    def test_extracts_priority_from_body(self):
        body = "priority=P0 lane=ops/codex/fix host=anvil task complete"
        assert classify_message_from_body("STATUS", body) == "foreground"

    def test_extracts_lane_from_body(self):
        body = "lane=audit/codex/rules-check priority=P2"
        assert classify_message_from_body("STATUS", body) == "background"

    def test_no_tags_falls_to_message_type(self):
        assert classify_message_from_body("STATUS", "plain message") == "background"


class TestExpectedModelTier:
    """Tests for expected_model_tier() per PROPOSAL-012 Component 5."""

    def test_background_status_is_t0(self):
        assert expected_model_tier("STATUS", priority="P2") == "T0"

    def test_background_heartbeat_is_t0(self):
        assert expected_model_tier("HEARTBEAT") == "T0"

    def test_foreground_proposal_is_t2(self):
        assert expected_model_tier("PROPOSAL") == "T2"

    def test_foreground_review_is_t2(self):
        assert expected_model_tier("REVIEW") == "T2"

    def test_foreground_ack_is_t2(self):
        assert expected_model_tier("ACK") == "T2"

    def test_foreground_veto_is_t2(self):
        assert expected_model_tier("VETO") == "T2"

    def test_foreground_blocked_is_t2(self):
        assert expected_model_tier("BLOCKED") == "T2"

    def test_foreground_non_review_is_t1(self):
        assert expected_model_tier("WIP_START") == "T1"

    def test_p0_status_is_t2(self):
        assert expected_model_tier("STATUS", priority="P0") == "T2"

    def test_p1_proposal_is_t2(self):
        assert expected_model_tier("PROPOSAL", priority="P1") == "T2"


class TestValidateModelTierForTask:
    """Tests for validate_model_tier_for_task() enforcement."""

    def test_no_tier_declared_passes(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(msg_type="STATUS", body="plain message")
        assert "No model_tier declared" in caplog.text

    def test_background_with_t0_passes(self, caplog):
        with caplog.at_level(logging.WARNING, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(
                msg_type="STATUS",
                body="priority=P2 model_tier=T0",
            )
        assert "high-stakes" not in caplog.text

    def test_background_with_t1_passes(self, caplog):
        with caplog.at_level(logging.WARNING, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(
                msg_type="STATUS",
                body="priority=P2 model_tier=T1",
            )
        assert "high-stakes" not in caplog.text

    def test_background_with_t2_warns(self, caplog):
        with caplog.at_level(logging.WARNING, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(
                msg_type="STATUS",
                body="priority=P2 model_tier=T2",
            )
        assert "high-stakes model tier" in caplog.text

    def test_foreground_review_with_t2_passes(self, caplog):
        with caplog.at_level(logging.WARNING, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(
                msg_type="REVIEW",
                body="model_tier=T2",
            )
        assert "free/local tier" not in caplog.text

    def test_foreground_review_with_t0_warns(self, caplog):
        with caplog.at_level(logging.WARNING, logger="hummbl_bus.lane_classifier"):
            validate_model_tier_for_task(
                msg_type="REVIEW",
                body="model_tier=T0",
            )
        assert "free/local tier" in caplog.text

    def test_enforcement_raises_for_background_t2(self):
        with pytest.raises(ValueError, match="high-stakes model tier"):
            validate_model_tier_for_task(
                msg_type="STATUS",
                body="priority=P2 model_tier=T2",
                enforce=True,
            )

    def test_enforcement_raises_for_foreground_t0(self):
        with pytest.raises(ValueError, match="free/local tier"):
            validate_model_tier_for_task(
                msg_type="REVIEW",
                body="model_tier=T0",
                enforce=True,
            )

    def test_env_enforcement(self):
        with patch.dict(os.environ, {"BUS_ENFORCE_TIER_ROUTING": "true"}):
            with pytest.raises(ValueError, match="high-stakes model tier"):
                validate_model_tier_for_task(
                    msg_type="STATUS",
                    body="priority=P2 model_tier=T2",
                )
