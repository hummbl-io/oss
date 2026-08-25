"""Tests for bif_start_session tool."""
import json
import pytest
import mcp_server
from mcp_server import tool_bif_start_session


class TestStartSession:
    def test_returns_required_keys(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        assert "session_id" in result
        assert "domain" in result
        assert "target_batches" in result
        assert "created_at" in result
        assert "phase_1_prompt" in result
        assert "pre_ingestion_checklist" in result
        assert "phases_overview" in result

    def test_session_id_is_nonempty_string(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        assert isinstance(result["session_id"], str)
        assert len(result["session_id"]) > 0

    def test_domain_stored_correctly(self):
        result = tool_bif_start_session({"domain": "Anthropic Ecosystem"})
        assert result["domain"] == "Anthropic Ecosystem"

    def test_target_batches_defaults_to_10(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        assert result["target_batches"] == 10

    def test_target_batches_can_be_customized(self):
        result = tool_bif_start_session({"domain": "TestDomain", "target_batches": 5})
        assert result["target_batches"] == 5

    def test_pre_ingestion_checklist_has_10_items(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        assert len(result["pre_ingestion_checklist"]) == 10

    def test_phases_overview_has_all_4_phases(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        overview = result["phases_overview"]
        assert set(overview.keys()) == {"1", "2", "3", "4"}

    def test_phase_1_prompt_contains_execution_steps(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        prompt = result["phase_1_prompt"]
        assert "IDENTIFY" in prompt
        assert "FETCH" in prompt
        assert "EXTRACT" in prompt
        assert "COMPILE" in prompt
        assert "VALIDATE" in prompt
        assert "DELIVER" in prompt

    def test_session_file_created(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        session_file = mcp_server.SESSIONS_DIR / f"{result['session_id']}.json"
        assert session_file.exists()

    def test_session_file_has_correct_content(self):
        result = tool_bif_start_session({"domain": "TestDomain"})
        session_file = mcp_server.SESSIONS_DIR / f"{result['session_id']}.json"
        session = json.loads(session_file.read_text())
        assert session["domain"] == "TestDomain"
        assert session["completed_batches"] == []
        assert session["current_phase"] == 1
        assert session["current_batch"] == 1

    def test_phase_1_prompt_contains_domain(self):
        result = tool_bif_start_session({"domain": "React"})
        assert "React" in result["phase_1_prompt"]
