"""Tests for bif_list_templates tool."""
import pytest
from mcp_server import tool_bif_list_templates


class TestListTemplates:
    def test_returns_templates_list(self):
        result = tool_bif_list_templates({})
        assert "templates" in result
        assert isinstance(result["templates"], list)

    def test_includes_generic_template(self):
        result = tool_bif_list_templates({})
        ids = [t["template_id"] for t in result["templates"]]
        assert "generic" in ids

    def test_each_template_has_required_keys(self):
        result = tool_bif_list_templates({})
        required = {"template_id", "description", "batch_count", "batches"}
        for tmpl in result["templates"]:
            assert required.issubset(set(tmpl.keys())), f"Missing keys in {tmpl['template_id']}"

    def test_count_matches_length(self):
        result = tool_bif_list_templates({})
        assert result["count"] == len(result["templates"])

    def test_generic_template_has_15_batches(self):
        result = tool_bif_list_templates({})
        generic = next(t for t in result["templates"] if t["template_id"] == "generic")
        assert generic["batch_count"] == 15

    def test_domain_templates_loaded_from_disk(self):
        result = tool_bif_list_templates({})
        # Should include ai-ml-platform, cloud-platform, etc. from templates/
        domain_ids = [t["template_id"] for t in result["templates"] if t["template_id"] != "generic"]
        assert len(domain_ids) >= 1
