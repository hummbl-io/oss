"""Regression tests for tools/adr_lint.py — ADR Format Compliance Linter.

Tests cover:
- Standard ADR filename validation (ADR-NNN-kebab-title.md)
- Domain-prefixed ADR filename validation (ADR-FM-NNN-title.md)
- Multi-part domain prefixes (ADR-ATL-WEDGE-NNN-title.md)
- Required header fields
- Status format validation
- Superseded reference validation (standard + domain-prefixed)
- False-positive regression: domain-prefixed refs were not recognized

Origin: hummbl-io/hummbl-governance#94
"""

import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from adr_lint import (  # noqa: E402
    lint_filename,
    lint_header_fields,
    lint_status_format,
    lint_superseded_refs,
    lint_adr_file,
    lint_directory,
)

FIXTURES = Path(__file__).parent / "fixtures" / "adr_lint"
VALID_DIR = FIXTURES / "valid"
INVALID_DIR = FIXTURES / "invalid"


class TestFilenameValidation:
    """Test ADR filename format validation."""

    def test_standard_filename_valid(self):
        """ADR-NNN-kebab-title.md should pass."""
        v = lint_filename("ADR-001-standard-format.md")
        assert v == []

    def test_domain_prefixed_filename_valid(self):
        """ADR-FM-NNN-title.md should pass."""
        v = lint_filename("ADR-FM-001-domain-prefix.md")
        assert v == []

    def test_multi_part_domain_filename_valid(self):
        """ADR-ATL-WEDGE-NNN-title.md should pass."""
        v = lint_filename("ADR-ATL-WEDGE-003-multi-part-domain.md")
        assert v == []

    def test_four_digit_number_invalid(self):
        """ADR-0001-four-digit.md should fail (4 digits, not 3)."""
        v = lint_filename("ADR-0001-four-digit.md")
        assert len(v) == 1
        assert v[0].rule == "F003"

    def test_underscore_invalid(self):
        """ADR-001_underscore.md should fail (underscore, not hyphen)."""
        v = lint_filename("ADR-001_underscore.md")
        assert len(v) == 1
        assert v[0].rule == "F005"


class TestHeaderFields:
    """Test required header field validation."""

    def test_valid_adr_all_fields_present(self):
        """ADR with all required fields in standard format should pass."""
        content = (
            "- **Status:** accepted\n"
            "- **Date:** 2026-01-15\n"
            "- **Decision owner:** devin\n"
            "- **Steward:** reubenbowlby\n"
        )
        v = lint_header_fields("ADR-001-test.md", content)
        assert v == []

    def test_missing_steward(self):
        """ADR missing Steward field should fail."""
        content = (
            "- **Status:** accepted\n"
            "- **Date:** 2026-01-15\n"
            "- **Decision owner:** devin\n"
        )
        v = lint_header_fields("ADR-004-test.md", content)
        assert any(x.rule == "H001" and "Steward" in x.message for x in v)


class TestStatusFormat:
    """Test status value format validation."""

    def test_lowercase_status_valid(self):
        """Lowercase status values should pass."""
        for status in ["accepted", "proposed", "superseded", "deprecated"]:
            content = f"- **Status:** {status}\n"
            v = lint_status_format("ADR-001-test.md", content)
            assert v == [], f"Status '{status}' should be valid, got: {[(x.rule, x.message) for x in v]}"

    def test_uppercase_status_invalid(self):
        """Uppercase status should fail (S001 invalid value + S002 should be lowercase)."""
        content = "- **Status:** APPROVED\n"
        v = lint_status_format("ADR-006-test.md", content)
        rules = {x.rule for x in v}
        assert "S002" in rules, f"Expected S002 (should be lowercase), got: {rules}"


class TestSupersededRefs:
    """Test superseded-by reference validation — includes false-positive regression."""

    def test_standard_reference_valid(self):
        """ADR-001 referenced in Superseded by should be found in numbers."""
        content = "**Superseded by:** ADR-001\n"
        v = lint_superseded_refs("test.md", content, {"001"})
        assert v == []

    def test_standard_reference_not_found(self):
        """ADR-999 not in numbers should fail."""
        content = "**Superseded by:** ADR-999\n"
        v = lint_superseded_refs("test.md", content, {"001"})
        assert len(v) == 1
        assert v[0].rule == "REF001"

    def test_domain_prefixed_reference_valid(self):
        """ADR-FM-001 referenced in Superseded by should be found.

        This is the false-positive regression test — domain-prefixed
        references were not recognized before the fix.
        """
        content = "**Superseded by:** ADR-FM-001\n"
        v = lint_superseded_refs("test.md", content, {"001", "FM-001"})
        assert v == [], "Domain-prefixed reference should be valid"

    def test_domain_prefixed_reference_not_found(self):
        """ADR-FM-999 not in numbers should fail."""
        content = "**Superseded by:** ADR-FM-999\n"
        v = lint_superseded_refs("test.md", content, {"001", "FM-001"})
        assert len(v) == 1
        assert v[0].rule == "REF001"

    def test_multi_part_domain_reference_valid(self):
        """ADR-ATL-WEDGE-003 should be valid when in numbers set."""
        content = "**Superseded by:** ADR-ATL-WEDGE-003\n"
        v = lint_superseded_refs("test.md", content, {"ATL-WEDGE-003"})
        assert v == []

    def test_none_reference_valid(self):
        """Superseded by: none should always pass."""
        content = "**Superseded by:** none\n"
        v = lint_superseded_refs("test.md", content, set())
        assert v == []

    def test_no_superseded_field(self):
        """File without Superseded by field should pass (not all ADRs are superseded)."""
        content = "**Status:** accepted\n"
        v = lint_superseded_refs("test.md", content, set())
        assert v == []


class TestLintDirectory:
    """Test directory-level linting with fixtures."""

    def test_valid_directory_no_violations(self):
        """Valid ADR directory should produce no violations."""
        results, exit_code = lint_directory(str(VALID_DIR))
        assert exit_code == 0
        all_violations = []
        for r in results:
            all_violations.extend(r.violations)
        assert all_violations == [], (
            f"Expected no violations for valid ADRs, got: "
            f"{[(v.file, v.rule, v.message) for v in all_violations]}"
        )

    def test_invalid_directory_has_violations(self):
        """Invalid ADR directory should produce violations."""
        results, exit_code = lint_directory(str(INVALID_DIR))
        all_violations = []
        for r in results:
            all_violations.extend(r.violations)
        assert len(all_violations) > 0, "Expected violations for invalid ADRs"

    def test_domain_prefixed_adrs_in_directory(self):
        """Directory with domain-prefixed ADRs should not false-positive on refs."""
        results, exit_code = lint_directory(str(VALID_DIR))
        assert exit_code == 0
        # Check that ADR-FM-004 (superseded by ADR-FM-001) has no REF001 violation
        for r in results:
            if "ADR-FM-004" in r.file:
                ref_violations = [v for v in r.violations if v.rule == "REF001"]
                assert ref_violations == [], (
                    f"Domain-prefixed superseded ref should not false-positive: "
                    f"{[v.message for v in ref_violations]}"
                )


class TestLintAdrFile:
    """Test single-file linting."""

    def test_valid_standard_adr(self):
        """Valid standard ADR file should pass."""
        filepath = str(VALID_DIR / "ADR-001-standard-format.md")
        result = lint_adr_file(filepath, all_adr_numbers={"001"})
        assert result.violations == [], (
            f"Expected no violations, got: {[(v.rule, v.message) for v in result.violations]}"
        )

    def test_valid_domain_prefixed_adr(self):
        """Valid domain-prefixed ADR file should pass."""
        filepath = str(VALID_DIR / "ADR-FM-001-domain-prefix.md")
        result = lint_adr_file(filepath, all_adr_numbers={"001", "FM-001"})
        assert result.violations == [], (
            f"Expected no violations, got: {[(v.rule, v.message) for v in result.violations]}"
        )

    def test_superseded_by_domain_ref_no_false_positive(self):
        """ADR-FM-004 superseded by ADR-FM-001 should not false-positive.

        This is the key regression test for the false-positive fix.
        Before the fix, lint_superseded_refs() only matched ADR-NNN
        patterns, not ADR-FM-NNN, causing false REF001 violations.
        """
        filepath = str(VALID_DIR / "ADR-FM-004-superseded-by-domain.md")
        result = lint_adr_file(filepath, all_adr_numbers={"001", "FM-001", "FM-004"})
        ref_violations = [v for v in result.violations if v.rule == "REF001"]
        assert ref_violations == [], (
            f"Domain-prefixed superseded ref should not false-positive: "
            f"{[v.message for v in ref_violations]}"
        )
