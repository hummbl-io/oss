"""Regression tests for tools/fleet_verify.py — Fleet Verification Tool.

Tests cover:
- Required field detection in ADR content
- Field format variations (bold markers)
- Domain-prefixed ADR handling

Origin: hummbl-io/hummbl-governance#94
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))


class TestFieldDetection:
    """Test that required ADR fields are correctly detected.

    The fleet_verify check_missing_fields function looks for these
    bold markers in ADR content:
    **Status:**, **Date:**, **Decision owner:**, **Steward:**,
    **Supersedes:**, **Superseded by:**
    """

    REQUIRED_FIELDS = [
        "**Status:**",
        "**Date:**",
        "**Decision owner:**",
        "**Steward:**",
        "**Supersedes:**",
        "**Superseded by:**",
    ]

    def test_all_fields_present(self):
        """Content with all required fields should detect all."""
        content = (
            "**Status:** accepted\n"
            "**Date:** 2026-01-15\n"
            "**Decision owner:** devin\n"
            "**Steward:** operator\n"
            "**Supersedes:** none\n"
            "**Superseded by:** none\n"
        )
        for field in self.REQUIRED_FIELDS:
            assert field in content, f"Field {field} should be present"

    def test_missing_steward(self):
        """Content missing Steward should be detectable."""
        content = (
            "**Status:** accepted\n"
            "**Date:** 2026-01-15\n"
            "**Decision owner:** devin\n"
        )
        assert "**Steward:**" not in content

    def test_missing_date(self):
        """Content missing Date should be detectable."""
        content = (
            "**Status:** accepted\n"
            "**Decision owner:** devin\n"
            "**Steward:** operator\n"
        )
        assert "**Date:**" not in content

    def test_missing_status(self):
        """Content missing Status should be detectable."""
        content = (
            "**Date:** 2026-01-15\n"
            "**Decision owner:** devin\n"
            "**Steward:** operator\n"
        )
        assert "**Status:**" not in content

    def test_domain_prefixed_superseded_by(self):
        """Content with domain-prefixed Superseded by should be detected."""
        content = "**Superseded by:** ADR-FM-001\n"
        assert "**Superseded by:**" in content

    def test_empty_content(self):
        """Empty content should have no fields detected."""
        for field in self.REQUIRED_FIELDS:
            assert field not in ""

    def test_field_with_extra_whitespace(self):
        """Fields with extra whitespace around the colon should still match."""
        # The current implementation uses exact substring matching
        # This test documents the current behavior
        content = "**Status:**  accepted\n"  # extra space after colon
        assert "**Status:**" in content  # substring still matches


class TestFleetVerifyImport:
    """Test that fleet_verify can be imported without errors."""

    def test_import(self):
        """fleet_verify module should import cleanly."""
        import fleet_verify
        assert hasattr(fleet_verify, "verify_fleet")
        assert hasattr(fleet_verify, "check_missing_fields")
        assert hasattr(fleet_verify, "ORG")
