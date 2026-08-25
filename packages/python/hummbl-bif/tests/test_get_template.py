"""Tests for bif_get_template tool."""
import pytest
from mcp_server import tool_bif_get_template


class TestGetTemplate:
    def test_phase1_batch1_correct_name(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        assert result["batch_name"] == "Core Reference"
        assert result["phase_name"] == "FOUNDATION"

    def test_phase2_batch5_technique(self):
        result = tool_bif_get_template({"phase": 2, "batch_number": 5})
        assert result["phase_name"] == "TECHNIQUE"
        assert result["batch_name"] == "Best Practices"

    def test_phase3_batch8_source(self):
        result = tool_bif_get_template({"phase": 3, "batch_number": 8})
        assert result["phase_name"] == "SOURCE"
        assert result["batch_name"] == "Production Configs"

    def test_phase4_batch11_ecosystem(self):
        result = tool_bif_get_template({"phase": 4, "batch_number": 11})
        assert result["phase_name"] == "ECOSYSTEM"
        assert result["batch_name"] == "Cookbooks & Deep-Dives"

    def test_returns_all_required_keys(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        required = {
            "phase", "phase_name", "phase_description", "batch_number",
            "batch_name", "what_to_capture", "priority", "exit_criteria",
            "execution_steps", "quality_checks", "file_naming", "prompt",
            "knowledge_file_header",
        }
        assert required.issubset(set(result.keys()))

    def test_phase1_includes_source_priority(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        assert "source_priority" in result
        assert len(result["source_priority"]) == 10

    def test_phase2_excludes_source_priority(self):
        result = tool_bif_get_template({"phase": 2, "batch_number": 5})
        assert "source_priority" not in result

    def test_phase3_excludes_source_priority(self):
        result = tool_bif_get_template({"phase": 3, "batch_number": 8})
        assert "source_priority" not in result

    def test_invalid_phase_returns_error(self):
        result = tool_bif_get_template({"phase": 99, "batch_number": 1})
        assert "error" in result
        assert "99" in result["error"]

    def test_invalid_batch_for_phase_returns_error_with_valid_options(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 99})
        assert "error" in result
        assert "valid" in result["error"].lower() or "1" in result["error"]

    def test_file_naming_zero_pads_batch_number(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        assert "01_" in result["file_naming"]

    def test_file_naming_for_double_digit_batch(self):
        result = tool_bif_get_template({"phase": 4, "batch_number": 11})
        assert "11_" in result["file_naming"]

    def test_execution_steps_has_6_items(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        assert len(result["execution_steps"]) == 6

    def test_quality_checks_has_10_items(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        assert len(result["quality_checks"]) == 10

    def test_prompt_includes_batch_name(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 2})
        assert "Protocol / Architecture" in result["prompt"] or "Architecture" in result["prompt"]

    def test_knowledge_file_header_has_metadata_fields(self):
        result = tool_bif_get_template({"phase": 1, "batch_number": 1})
        header = result["knowledge_file_header"]
        assert "> Source:" in header
        assert "> Fetched:" in header
        assert "> Purpose:" in header
