"""Tests for bif_validate_batch tool."""
import pytest
from mcp_server import tool_bif_validate_batch

# A well-formed batch that should pass all checks
GOOD_BATCH = """# Anthropic API — Core Reference
> Source: https://docs.anthropic.com/
> Fetched: 2026-04-11
> Purpose: Official API documentation, llms.txt, and site map for the Anthropic ecosystem

---

## Overview

The Anthropic Claude API provides access to Claude models via REST.

## Authentication

```python
import anthropic
client = anthropic.Anthropic(api_key="sk-...")
```

## Models

| Model | Context | Best For |
|-------|---------|----------|
| claude-opus-4-6 | 200K | Complex tasks |
| claude-sonnet-4-6 | 200K | Balanced |

## Site Map

- docs.anthropic.com/en/api — API reference
- docs.anthropic.com/en/docs — User guide

---

## Summary

Core reference complete.
"""


class TestValidateBatch:
    def test_good_batch_passes(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert result["overall"] == "PASS"

    def test_missing_metadata_fails(self):
        content = "# Title\n\n## Section\n\nContent here.\n\n```python\ncode\n```\n"
        result = tool_bif_validate_batch({
            "batch_content": content, "phase": 1, "batch_number": 1
        })
        metadata_check = next(c for c in result["checks"] if c["check"] == "metadata")
        assert not metadata_check["passed"]

    def test_no_headers_fails_structured_check(self):
        content = (
            "> Source: https://example.com\n> Fetched: 2026-04-11\n> Purpose: test\n\n"
            "Just a wall of text with no headers whatsoever.\n"
        )
        result = tool_bif_validate_batch({
            "batch_content": content, "phase": 1, "batch_number": 1
        })
        structured_check = next(c for c in result["checks"] if c["check"] == "structured")
        assert not structured_check["passed"]

    def test_two_headers_passes_structured_check(self):
        content = (
            "> Source: https://example.com\n> Fetched: 2026-04-11\n> Purpose: test\n\n"
            "## Section One\nContent.\n## Section Two\nContent.\n"
        )
        result = tool_bif_validate_batch({
            "batch_content": content, "phase": 2, "batch_number": 5
        })
        structured_check = next(c for c in result["checks"] if c["check"] == "structured")
        assert structured_check["passed"]

    def test_token_budget_under_50k_passes(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        budget_check = next(c for c in result["checks"] if c["check"] == "token_budget")
        assert budget_check["passed"]

    def test_token_budget_over_50k_fails(self):
        huge_content = GOOD_BATCH + ("x" * 200_001)
        result = tool_bif_validate_batch({
            "batch_content": huge_content, "phase": 1, "batch_number": 1
        })
        budget_check = next(c for c in result["checks"] if c["check"] == "token_budget")
        assert not budget_check["passed"]
        assert "OVER" in budget_check["detail"]

    def test_phase1_without_sitemap_fails_sitemap_check(self):
        content = (
            "> Source: https://example.com\n> Fetched: 2026-04-11\n> Purpose: test\n\n"
            "## Overview\nContent.\n## Details\nMore.\n\n```python\ncode\n```\n"
        )
        result = tool_bif_validate_batch({
            "batch_content": content, "phase": 1, "batch_number": 1
        })
        sitemap_check = next((c for c in result["checks"] if c["check"] == "sitemap"), None)
        assert sitemap_check is not None
        assert not sitemap_check["passed"]

    def test_phase1_with_sitemap_passes_sitemap_check(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        sitemap_check = next((c for c in result["checks"] if c["check"] == "sitemap"), None)
        assert sitemap_check is not None
        assert sitemap_check["passed"]

    def test_phase2_skips_sitemap_check(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 2, "batch_number": 5
        })
        sitemap_check = next((c for c in result["checks"] if c["check"] == "sitemap"), None)
        assert sitemap_check is None

    def test_result_has_overall_field(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert "overall" in result
        assert result["overall"] in {"PASS", "FAIL"}

    def test_result_has_passed_and_failed_counts(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert "passed" in result
        assert "failed" in result
        assert result["passed"] + result["failed"] == result["total_checks"]

    def test_result_has_gaps_list(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert "gaps" in result
        assert isinstance(result["gaps"], list)

    def test_perfect_batch_has_empty_gaps(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert result["gaps"] == []

    def test_missing_batch_content_returns_error(self):
        result = tool_bif_validate_batch({"phase": 1, "batch_number": 1})
        assert "error" in result

    def test_score_format_is_n_over_m(self):
        result = tool_bif_validate_batch({
            "batch_content": GOOD_BATCH, "phase": 1, "batch_number": 1
        })
        assert "/" in result["score"]
        parts = result["score"].split("/")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_fail_result_lists_failed_checks_in_gaps(self):
        minimal = "> Source: x\n> Fetched: y\n> Purpose: z\n\n## A\n\n## B\n"
        result = tool_bif_validate_batch({
            "batch_content": minimal, "phase": 2, "batch_number": 5
        })
        # code_examples check should fail (no ```)
        assert result["failed"] > 0
        assert len(result["gaps"]) == result["failed"]
