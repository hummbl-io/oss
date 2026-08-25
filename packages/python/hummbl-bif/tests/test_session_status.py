"""Tests for bif_session_status tool."""
import pytest
from mcp_server import tool_bif_start_session, tool_bif_session_status


class TestSessionStatus:
    def test_no_session_id_lists_all_sessions(self):
        result = tool_bif_session_status({})
        assert "sessions" in result
        assert "count" in result

    def test_empty_listing_has_zero_count(self):
        result = tool_bif_session_status({})
        assert result["count"] == 0
        assert result["sessions"] == []

    def test_created_session_appears_in_listing(self):
        tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({})
        assert result["count"] == 1
        assert result["sessions"][0]["domain"] == "TestDomain"

    def test_valid_session_id_returns_domain(self):
        created = tool_bif_start_session({"domain": "AWS Lambda"})
        sid = created["session_id"]
        result = tool_bif_session_status({"session_id": sid})
        assert result["domain"] == "AWS Lambda"

    def test_invalid_session_id_returns_error(self):
        result = tool_bif_session_status({"session_id": "nonexistent"})
        assert "error" in result

    def test_completion_percentage_is_zero_at_start(self):
        created = tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({"session_id": created["session_id"]})
        assert result["percentage"] == 0

    def test_phase_coverage_is_computed(self):
        created = tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({"session_id": created["session_id"]})
        assert "phase_coverage" in result
        assert "FOUNDATION" in result["phase_coverage"]

    def test_next_batch_is_batch_1_at_start(self):
        created = tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({"session_id": created["session_id"]})
        assert result["next_batch"]["batch_number"] == 1

    def test_completed_batches_empty_at_start(self):
        created = tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({"session_id": created["session_id"]})
        assert result["completed_batches"] == []

    def test_listing_view_has_count_field(self):
        tool_bif_start_session({"domain": "Domain A"})
        tool_bif_start_session({"domain": "Domain B"})
        result = tool_bif_session_status({})
        assert result["count"] == 2

    def test_detail_view_has_completion_string(self):
        created = tool_bif_start_session({"domain": "TestDomain"})
        result = tool_bif_session_status({"session_id": created["session_id"]})
        assert "completion" in result
        assert "/" in result["completion"]

    def test_next_batch_is_none_when_all_done(self):
        """If target_batches=1 and batch 1 is complete, next_batch should be None."""
        from mcp_server import _load_session, _save_session
        created = tool_bif_start_session({"domain": "TestDomain", "target_batches": 1})
        sid = created["session_id"]
        session = _load_session(sid)
        session["completed_batches"] = [1]
        _save_session(session)
        result = tool_bif_session_status({"session_id": sid})
        assert result["next_batch"] is None
