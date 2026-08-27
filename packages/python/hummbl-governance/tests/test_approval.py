# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_governance.approval (HITL ApprovalManager)."""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hummbl_governance import (
    ApprovalAlreadyDecidedError,
    ApprovalError,
    ApprovalExpiredError,
    ApprovalManager,
    ApprovalNotFoundError,
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)


class TestApprovalRequestCreation:
    """Tests for request creation and basic lifecycle."""

    def test_request_starts_pending(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="send_email",
            action_args="to=client@example.com",
            risk_level=RiskLevel.LOW,
            justification="Weekly report",
        )
        assert req.status == ApprovalStatus.PENDING
        assert req.is_pending
        assert not req.is_terminal
        assert req.request_id  # UUID generated
        assert req.agent_id == "agent-1"
        assert req.action == "send_email"

    def test_invalid_risk_level_raises(self):
        mgr = ApprovalManager()
        with pytest.raises(ValueError, match="Unknown RiskLevel"):
            mgr.request_approval(
                agent_id="agent-1",
                action="test",
                action_args="",
                risk_level="HIGH",  # type: ignore[arg-type]
                justification="test",
            )

    def test_request_with_metadata(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="delete_file",
            action_args="/data/db.sqlite",
            risk_level=RiskLevel.HIGH,
            justification="Cleanup",
            metadata={"task_id": "task-123", "intent_id": "intent-456"},
        )
        assert req.metadata["task_id"] == "task-123"
        assert req.metadata["intent_id"] == "intent-456"

    def test_request_with_expiry(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=60,
        )
        assert req.expires_at is not None
        assert req.status == ApprovalStatus.PENDING

    def test_request_no_expiry(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=None,
        )
        assert req.expires_at is None


class TestApprovalDecisions:
    """Tests for approve / deny / cancel."""

    def test_approve_pending(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
        )
        result = mgr.approve(req.request_id, decided_by="operator", reason="OK")
        assert result.status == ApprovalStatus.APPROVED
        assert result.decided_by == "operator"
        assert result.decision_reason == "OK"
        assert result.is_terminal

    def test_deny_pending(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
        )
        result = mgr.deny(req.request_id, decided_by="operator", reason="Too risky")
        assert result.status == ApprovalStatus.DENIED
        assert result.decision_reason == "Too risky"

    def test_cancel_pending(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
        )
        result = mgr.cancel(req.request_id, decided_by="agent-1", reason="Aborted")
        assert result.status == ApprovalStatus.CANCELLED

    def test_approve_already_approved_raises(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
        )
        mgr.approve(req.request_id, decided_by="op")
        with pytest.raises(ApprovalAlreadyDecidedError):
            mgr.deny(req.request_id, decided_by="op")

    def test_approve_nonexistent_raises(self):
        mgr = ApprovalManager()
        with pytest.raises(ApprovalNotFoundError):
            mgr.approve("nonexistent-id", decided_by="op")


class TestApprovalExpiration:
    """Tests for auto-expiration."""

    def test_expired_request_cannot_be_approved(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=0.01,
        )
        time.sleep(0.05)
        with pytest.raises(ApprovalExpiredError):
            mgr.approve(req.request_id, decided_by="op")

    def test_expire_stale_expires_pending(self):
        mgr = ApprovalManager()
        mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=0.01,
        )
        time.sleep(0.05)
        count = mgr.expire_stale()
        assert count == 1

    def test_check_status_auto_expires(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=0.01,
        )
        time.sleep(0.05)
        status = mgr.check_status(req.request_id)
        assert status["status"] == "EXPIRED"
        assert status["expired"] is True

    def test_no_expiry_never_expires(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=None,
        )
        count = mgr.expire_stale()
        assert count == 0
        assert mgr.check_status(req.request_id)["status"] == "PENDING"


class TestApprovalWait:
    """Tests for blocking wait_for_decision."""

    def test_wait_returns_immediately_if_approved(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
        )
        mgr.approve(req.request_id, decided_by="op")
        result = mgr.wait_for_decision(req.request_id, timeout=1)
        assert result["status"] == "APPROVED"

    def test_wait_times_out_and_expires(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="agent-1",
            action="test",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="test",
            timeout_seconds=0.05,
        )
        result = mgr.wait_for_decision(req.request_id, timeout=0.2, poll_interval=0.02)
        assert result["status"] == "EXPIRED"

    def test_wait_nonexistent_raises(self):
        mgr = ApprovalManager()
        with pytest.raises(ApprovalNotFoundError):
            mgr.wait_for_decision("nonexistent", timeout=0.1)


class TestApprovalGate:
    """Tests for the one-call gate() convenience method."""

    def test_gate_auto_approves_below_threshold(self):
        mgr = ApprovalManager()
        result = mgr.gate(
            agent_id="agent-1",
            action="read_file",
            action_args="/tmp/test.txt",
            risk_level=RiskLevel.LOW,
            justification="Reading config",
            threshold=RiskLevel.MEDIUM,
        )
        assert result["allowed"] is True
        assert result["status"] == "AUTO_APPROVED"
        assert result["request_id"] is None

    def test_gate_requires_approval_at_threshold(self):
        mgr = ApprovalManager()
        # Use a very short timeout so the test doesn't hang.
        result = mgr.gate(
            agent_id="agent-1",
            action="delete_file",
            action_args="/data/production.db",
            risk_level=RiskLevel.HIGH,
            justification="Cleanup",
            threshold=RiskLevel.MEDIUM,
            timeout_seconds=0.05,
        )
        assert result["allowed"] is False
        assert result["status"] == "EXPIRED"
        assert result["request_id"] is not None

    def test_requires_approval_static(self):
        assert ApprovalManager.requires_approval("test", RiskLevel.LOW, RiskLevel.MEDIUM) is False
        assert ApprovalManager.requires_approval("test", RiskLevel.MEDIUM, RiskLevel.MEDIUM) is True
        assert ApprovalManager.requires_approval("test", RiskLevel.CRITICAL, RiskLevel.HIGH) is True


class TestApprovalListing:
    """Tests for list_pending / list_all / get_stats."""

    def test_list_pending(self):
        mgr = ApprovalManager()
        r1 = mgr.request_approval("a", "act1", "", RiskLevel.LOW, "j")
        r2 = mgr.request_approval("b", "act2", "", RiskLevel.HIGH, "j")
        mgr.approve(r1.request_id, decided_by="op")
        pending = mgr.list_pending()
        assert len(pending) == 1
        assert pending[0]["request_id"] == r2.request_id

    def test_list_all_with_limit(self):
        mgr = ApprovalManager()
        for i in range(5):
            mgr.request_approval("a", f"act{i}", "", RiskLevel.LOW, "j")
        all_reqs = mgr.list_all(limit=3)
        assert len(all_reqs) == 3

    def test_get_stats(self):
        mgr = ApprovalManager()
        mgr.request_approval("a", "act1", "", RiskLevel.LOW, "j")
        mgr.request_approval("b", "act2", "", RiskLevel.HIGH, "j")
        mgr.approve(mgr.list_pending()[0]["request_id"], decided_by="op")
        stats = mgr.get_stats()
        assert stats["total"] == 2
        assert stats["pending"] == 1
        assert stats["by_status"]["APPROVED"] == 1
        assert stats["by_risk"]["LOW"] == 1
        assert stats["by_risk"]["HIGH"] == 1


class TestApprovalPersistence:
    """Tests for state persistence to disk."""

    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mgr1 = ApprovalManager(state_dir=state_dir)
            req = mgr1.request_approval(
                agent_id="agent-1",
                action="delete_file",
                action_args="/data/db",
                risk_level=RiskLevel.HIGH,
                justification="Cleanup",
            )
            mgr1.approve(req.request_id, decided_by="op")

            # New manager loads from same state dir.
            mgr2 = ApprovalManager(state_dir=state_dir)
            loaded = mgr2.get_request(req.request_id)
            assert loaded.status == ApprovalStatus.APPROVED
            assert loaded.agent_id == "agent-1"
            assert loaded.action == "delete_file"

    def test_persist_pending_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mgr1 = ApprovalManager(state_dir=state_dir)
            req = mgr1.request_approval(
                agent_id="agent-1",
                action="test",
                action_args="",
                risk_level=RiskLevel.LOW,
                justification="test",
            )
            mgr2 = ApprovalManager(state_dir=state_dir)
            loaded = mgr2.get_request(req.request_id)
            assert loaded.status == ApprovalStatus.PENDING

    def test_no_persistence_without_state_dir(self):
        mgr = ApprovalManager()
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        # Should not raise; just no persistence.
        assert req.status == ApprovalStatus.PENDING


class TestApprovalNotifications:
    """Tests for notification hooks."""

    def test_custom_notification_hook_called(self):
        mgr = ApprovalManager()
        received: list[ApprovalRequest] = []
        mgr.add_notification_hook(lambda req: received.append(req))
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        assert len(received) == 1
        assert received[0].request_id == req.request_id
        assert "custom" in req.notification_channels

    def test_custom_hook_exception_does_not_break_request(self):
        mgr = ApprovalManager()

        def bad_hook(req):
            raise RuntimeError("hook failed")

        mgr.add_notification_hook(bad_hook)
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        assert req.status == ApprovalStatus.PENDING

    @patch("hummbl_governance.approval.ApprovalManager._send_webhook")
    def test_webhook_notification(self, mock_send):
        mock_send.return_value = True
        mgr = ApprovalManager(webhook_url="https://example.com/hook")
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        assert mock_send.called
        assert "webhook" in req.notification_channels

    @patch("hummbl_governance.approval.ApprovalManager._send_slack")
    def test_slack_notification(self, mock_send):
        mock_send.return_value = True
        mgr = ApprovalManager(slack_webhook_url="https://hooks.slack.com/T/B/X")
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.HIGH, justification="j"
        )
        assert mock_send.called
        assert "slack" in req.notification_channels

    @patch("hummbl_governance.approval.ApprovalManager._send_email")
    def test_email_notification(self, mock_send):
        mock_send.return_value = True
        config = {"host": "smtp.example.com", "port": 587, "from": "a@b.com", "to": "c@d.com"}
        mgr = ApprovalManager(email_config=config)
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.CRITICAL, justification="j"
        )
        assert mock_send.called
        assert "email" in req.notification_channels


class TestApprovalAuditIntegration:
    """Tests for AuditLog integration."""

    def test_audit_log_emitted_on_request(self):
        mock_audit = MagicMock()
        mock_audit.append.return_value = (True, None)
        mgr = ApprovalManager(audit_log=mock_audit)
        mgr.request_approval(agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j")
        assert mock_audit.append.called
        call_args = mock_audit.append.call_args
        assert call_args.kwargs["tuple_data"]["event"] == "approval_requested"

    def test_audit_log_emitted_on_approve(self):
        mock_audit = MagicMock()
        mock_audit.append.return_value = (True, None)
        mgr = ApprovalManager(audit_log=mock_audit)
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        mock_audit.reset_mock()
        mgr.approve(req.request_id, decided_by="op")
        assert mock_audit.append.called
        call_args = mock_audit.append.call_args
        assert call_args.kwargs["tuple_data"]["event"] == "approval_granted"

    def test_audit_log_failure_does_not_break(self):
        mock_audit = MagicMock()
        mock_audit.append.side_effect = RuntimeError("audit broken")
        mgr = ApprovalManager(audit_log=mock_audit)
        # Should not raise.
        req = mgr.request_approval(
            agent_id="a", action="t", action_args="", risk_level=RiskLevel.LOW, justification="j"
        )
        assert req.status == ApprovalStatus.PENDING


class TestApprovalSerialization:
    """Tests for ApprovalRequest to_dict / from_dict roundtrip."""

    def test_to_dict_from_dict_roundtrip(self):
        req = ApprovalRequest(
            request_id="test-123",
            agent_id="agent-1",
            action="delete_file",
            action_args="/data/db",
            risk_level=RiskLevel.HIGH,
            justification="Cleanup",
            created_at="2026-01-01T00:00:00+00:00",
            expires_at="2026-01-01T00:05:00+00:00",
            metadata={"task_id": "t1"},
        )
        d = req.to_dict()
        restored = ApprovalRequest.from_dict(d)
        assert restored.request_id == req.request_id
        assert restored.risk_level == req.risk_level
        assert restored.status == req.status
        assert restored.metadata == req.metadata


class TestApprovalBackgroundExpiration:
    """Tests for the background expiration thread."""

    def test_background_expire_loop(self):
        mgr = ApprovalManager(auto_expire_interval=0.1)
        mgr.request_approval(
            agent_id="a",
            action="t",
            action_args="",
            risk_level=RiskLevel.LOW,
            justification="j",
            timeout_seconds=0.05,
        )
        # Wait for the background sweep (runs every 0.1s) to fire.
        # 0.3s is 3x the interval — enough margin for the sweep to fire
        # without flakiness, while keeping the test under 0.5s.
        time.sleep(0.3)
        stats = mgr.get_stats()
        # Should have been expired by the background thread.
        assert stats["by_status"].get("EXPIRED", 0) == 1
        mgr.shutdown()


class TestApprovalErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_errors_inherit_from_approval_error(self):
        assert issubclass(ApprovalExpiredError, ApprovalError)
        assert issubclass(ApprovalNotFoundError, ApprovalError)
        assert issubclass(ApprovalAlreadyDecidedError, ApprovalError)

    def test_error_carries_request_id(self):
        try:
            raise ApprovalNotFoundError("req-123")
        except ApprovalError as e:
            assert e.request_id == "req-123"
