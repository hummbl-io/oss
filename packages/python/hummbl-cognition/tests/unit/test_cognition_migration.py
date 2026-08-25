"""Tests for cognition migration tools.

Covers MEMORY.md parsing, bus history import, git log import,
helper mappers, and idempotent deterministic ID generation.
"""

from __future__ import annotations

import textwrap
from unittest.mock import patch

import pytest

from hummbl_cognition.migration import (
    _author_to_vendor,
    _commit_prefix_to_type,
    _deterministic_id,
    _parse_memory_sections,
    _section_to_scope,
    _section_to_tags,
    _section_to_type,
    _sender_to_vendor,
    import_from_bus_history,
    import_from_git_log,
    import_from_memory_md,
)

# ---------------------------------------------------------------------------
# _deterministic_id
# ---------------------------------------------------------------------------


class TestDeterministicId:
    def test_format(self):
        result = _deterministic_id("content", "source")
        assert result.startswith("clp-")
        assert len(result) == 16  # clp- + 12 hex chars

    def test_deterministic(self):
        a = _deterministic_id("hello", "test")
        b = _deterministic_id("hello", "test")
        assert a == b

    def test_different_content_different_id(self):
        a = _deterministic_id("hello", "test")
        b = _deterministic_id("world", "test")
        assert a != b

    def test_different_source_different_id(self):
        a = _deterministic_id("hello", "source1")
        b = _deterministic_id("hello", "source2")
        assert a != b

    def test_hex_chars_only(self):
        result = _deterministic_id("test", "test")
        hex_part = result[4:]
        assert all(c in "0123456789abcdef" for c in hex_part)


# ---------------------------------------------------------------------------
# _parse_memory_sections
# ---------------------------------------------------------------------------


class TestParseMemorySections:
    def test_basic_sections(self):
        text = textwrap.dedent("""\
            # Memory

            ## Project Info
            - First bullet
            - Second bullet

            ## Gotchas
            - Watch out for this
        """)
        sections = _parse_memory_sections(text)
        assert len(sections) == 2
        assert sections[0]["heading"] == "Project Info"
        assert sections[0]["bullets"] == ["First bullet", "Second bullet"]
        assert sections[1]["heading"] == "Gotchas"
        assert sections[1]["bullets"] == ["Watch out for this"]

    def test_skips_top_level_heading(self):
        text = "# Top Level\n- bullet\n"
        sections = _parse_memory_sections(text)
        assert len(sections) == 0

    def test_skips_indented_sub_bullets(self):
        text = textwrap.dedent("""\
            ## Section
            - Top bullet
              - Sub bullet (indented)
            - Another top bullet
        """)
        sections = _parse_memory_sections(text)
        assert len(sections) == 1
        assert sections[0]["bullets"] == ["Top bullet", "Another top bullet"]

    def test_empty_text(self):
        assert _parse_memory_sections("") == []

    def test_section_with_no_bullets(self):
        text = "## Empty Section\nSome text but no bullets\n"
        sections = _parse_memory_sections(text)
        assert len(sections) == 0

    def test_multiple_sections_last_flushed(self):
        text = "## A\n- a1\n## B\n- b1\n- b2\n"
        sections = _parse_memory_sections(text)
        assert len(sections) == 2
        assert sections[1]["bullets"] == ["b1", "b2"]


# ---------------------------------------------------------------------------
# Section mappers
# ---------------------------------------------------------------------------


class TestSectionMappers:
    # _section_to_scope
    def test_scope_gotcha(self):
        assert _section_to_scope("Gotchas") == "convention"

    def test_scope_constraint(self):
        assert _section_to_scope("Operational Constraints") == "convention"

    def test_scope_architecture(self):
        assert _section_to_scope("Key Architecture Insights") == "project"

    def test_scope_setup(self):
        assert _section_to_scope(".claude/ Setup") == "project"

    def test_scope_sprint(self):
        assert _section_to_scope("Sprint MARCH-OPS") == "process"

    def test_scope_session(self):
        assert _section_to_scope("Session 2026-03-03") == "process"

    def test_scope_coordination(self):
        assert _section_to_scope("Multi-Agent Coordination") == "process"

    def test_scope_default(self):
        assert _section_to_scope("Random Heading") == "project"

    # _section_to_type
    def test_type_gotcha(self):
        assert _section_to_type("Gotchas") == "lesson"

    def test_type_constraint(self):
        assert _section_to_type("Operational Constraints") == "convention"

    def test_type_architecture(self):
        assert _section_to_type("Architecture Insights") == "discovery"

    def test_type_insight(self):
        assert _section_to_type("Key Insight") == "discovery"

    def test_type_sprint(self):
        assert _section_to_type("Sprint A") == "discovery"

    def test_type_decision(self):
        assert _section_to_type("Key Decisions") == "decision"

    def test_type_default(self):
        assert _section_to_type("Something Else") == "lesson"

    # _section_to_tags
    def test_tags_always_includes_imported(self):
        tags = _section_to_tags("Something")
        assert "imported" in tags
        assert "memory-md" in tags

    def test_tags_gotcha(self):
        assert "gotcha" in _section_to_tags("Gotchas and Issues")

    def test_tags_security(self):
        assert "security" in _section_to_tags("Security Rules")

    def test_tags_ci(self):
        assert "ci" in _section_to_tags("CI Workflow Setup")

    def test_tags_sprint(self):
        assert "sprint" in _section_to_tags("Sprint Status")

    def test_tags_coordination(self):
        assert "coordination" in _section_to_tags("Agent Coordination")

    def test_tags_aaa(self):
        assert "aaa" in _section_to_tags("AAA Repo")

    def test_tags_hummbl(self):
        assert "hummbl" in _section_to_tags("HUMMBL & Founder Mode")

    def test_tags_openclaw(self):
        assert "openclaw" in _section_to_tags("OpenClaw Gateway")

    def test_tags_max_10(self):
        # Even with all keywords, max 10 tags
        tags = _section_to_tags(
            "Gotcha Security CI Sprint Agent AAA HUMMBL OpenClaw Workflow"
        )
        assert len(tags) <= 10


# ---------------------------------------------------------------------------
# Vendor/author mappers
# ---------------------------------------------------------------------------


class TestVendorMappers:
    # _sender_to_vendor
    def test_claude_sender(self):
        assert _sender_to_vendor("claude-code (god-mode)") == "anthropic"

    def test_codex_sender(self):
        assert _sender_to_vendor("codex") == "openai"

    def test_kimi_sender(self):
        assert _sender_to_vendor("kimi-1") == "moonshot"

    def test_gemini_sender(self):
        assert _sender_to_vendor("gemini-2.5") == "google"

    def test_unknown_sender(self):
        assert _sender_to_vendor("reuben") == "local"

    # _author_to_vendor
    def test_claude_author(self):
        assert _author_to_vendor("Claude Opus 4.6") == "anthropic"

    def test_anthropic_author(self):
        assert _author_to_vendor("Anthropic Bot") == "anthropic"

    def test_openai_author(self):
        assert _author_to_vendor("OpenAI Codex") == "openai"

    def test_moonshot_author(self):
        assert _author_to_vendor("Kimi Agent") == "moonshot"

    def test_google_author(self):
        assert _author_to_vendor("Google Gemini") == "google"

    def test_human_author(self):
        assert _author_to_vendor("Reuben Bowlby") == "human"

    # _commit_prefix_to_type
    def test_fix_prefix(self):
        assert _commit_prefix_to_type("fix: resolve null pointer") == "correction"

    def test_feat_prefix(self):
        assert _commit_prefix_to_type("feat: add new feature") == "discovery"

    def test_refactor_prefix(self):
        assert _commit_prefix_to_type("refactor: extract method") == "decision"

    def test_docs_prefix(self):
        assert _commit_prefix_to_type("docs: update README") == "convention"

    def test_chore_prefix(self):
        assert _commit_prefix_to_type("chore: bump version") == "convention"

    def test_unknown_prefix(self):
        assert _commit_prefix_to_type("something else") == "discovery"


# ---------------------------------------------------------------------------
# import_from_memory_md
# ---------------------------------------------------------------------------


@pytest.mark.allow_ledger_writes
class TestImportFromMemoryMd:
    def test_dry_run_basic(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text(textwrap.dedent("""\
            # Memory

            ## Project Info
            - The project uses Python 3.11+
            - Zero third-party dependencies

            ## Gotchas
            - Watch out for singletons leaking between tests
        """))

        entries = import_from_memory_md(memory, dry_run=True)
        assert len(entries) == 3
        assert entries[0].content == "The project uses Python 3.11+"
        assert entries[0].type == "lesson"  # Project Info -> default lesson
        assert entries[0].scope == "project"
        assert entries[2].content == "Watch out for singletons leaking between tests"
        assert entries[2].type == "lesson"  # Gotchas -> lesson
        assert entries[2].scope == "convention"  # Gotchas -> convention

    def test_missing_file_returns_empty(self, tmp_path):
        result = import_from_memory_md(tmp_path / "nonexistent.md", dry_run=True)
        assert result == []

    def test_idempotent_ids(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text("## Section\n- Same content\n")

        entries1 = import_from_memory_md(memory, dry_run=True)
        entries2 = import_from_memory_md(memory, dry_run=True)
        assert entries1[0].id == entries2[0].id

    def test_writes_to_ledger(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text("## Test\n- Entry one\n- Entry two\n")
        ledger = tmp_path / "ledger.jsonl"

        entries = import_from_memory_md(
            memory, ledger_path=ledger, dry_run=False
        )
        assert len(entries) == 2
        assert ledger.exists()
        lines = ledger.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_skips_duplicates_on_reimport(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text("## Test\n- Entry one\n")
        ledger = tmp_path / "ledger.jsonl"

        import_from_memory_md(memory, ledger_path=ledger)
        entries2 = import_from_memory_md(memory, ledger_path=ledger)
        assert len(entries2) == 0  # All skipped as duplicates

    def test_empty_bullets_skipped(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text("## Section\n- \n- Real content\n")
        entries = import_from_memory_md(memory, dry_run=True)
        assert len(entries) == 1
        assert entries[0].content == "Real content"

    def test_tags_from_section(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        memory.write_text("## Security Rules\n- Use HMAC signing\n")
        entries = import_from_memory_md(memory, dry_run=True)
        assert "imported" in entries[0].tags
        assert "memory-md" in entries[0].tags
        assert "security" in entries[0].tags

    def test_content_truncated_at_4096(self, tmp_path):
        memory = tmp_path / "MEMORY.md"
        long_content = "x" * 5000
        memory.write_text(f"## Section\n- {long_content}\n")
        entries = import_from_memory_md(memory, dry_run=True)
        assert len(entries[0].content) == 4096


# ---------------------------------------------------------------------------
# import_from_bus_history
# ---------------------------------------------------------------------------


@pytest.mark.allow_ledger_writes
class TestImportFromBusHistory:
    def _make_bus_file(self, tmp_path, rows):
        bus = tmp_path / "messages.tsv"
        lines = ["timestamp\tfrom\tto\ttype\tmessage"]
        lines.extend(rows)
        bus.write_text("\n".join(lines) + "\n")
        return bus

    def test_dry_run_basic(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tclaude-code\tall\tDECISION\tUse JSONL for storage",
            "2026-03-01T11:00:00Z\tkimi-1\tall\tMILESTONE\tPhase A complete",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert len(entries) == 2
        assert entries[0].type == "decision"
        assert entries[0].vendor == "anthropic"
        assert entries[1].type == "discovery"  # MILESTONE -> discovery
        assert entries[1].vendor == "moonshot"

    def test_filters_by_type(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tSTATUS\tI'm alive",
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\tReal decision",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert len(entries) == 1
        assert entries[0].type == "decision"

    def test_custom_msg_types(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tSTATUS\tI'm alive",
        ])
        entries = import_from_bus_history(
            bus_path=bus, msg_types={"STATUS"}, dry_run=True
        )
        # STATUS maps to default "discovery"
        assert len(entries) == 1

    def test_filters_by_since(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-02-01T10:00:00Z\tagent\tall\tDECISION\tOld decision",
            "2026-03-15T10:00:00Z\tagent\tall\tDECISION\tNew decision",
        ])
        entries = import_from_bus_history(
            bus_path=bus, since="2026-03-01T00:00:00Z", dry_run=True
        )
        assert len(entries) == 1
        assert "New decision" in entries[0].content

    def test_missing_bus_returns_empty(self, tmp_path):
        result = import_from_bus_history(
            bus_path=tmp_path / "nonexistent.tsv", dry_run=True
        )
        assert result == []

    def test_skips_malformed_lines(self, tmp_path):
        bus = tmp_path / "messages.tsv"
        bus.write_text(
            "timestamp\tfrom\tto\ttype\tmessage\n"
            "bad line with wrong columns\n"
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\tGood entry\n"
        )
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert len(entries) == 1

    def test_skips_header_row(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\tReal entry",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert len(entries) == 1

    def test_unescapes_newlines(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\tLine1\\nLine2",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert "Line1\nLine2" in entries[0].content

    def test_evidence_includes_line_number(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\tEntry",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert entries[0].evidence.startswith("bus:line:")

    def test_writes_to_ledger(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tclaude\tall\tDECISION\tTest",
        ])
        ledger = tmp_path / "ledger.jsonl"
        entries = import_from_bus_history(
            bus_path=bus, ledger_path=ledger, dry_run=False
        )
        assert len(entries) == 1
        assert ledger.exists()

    def test_idempotent(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tclaude\tall\tDECISION\tTest",
        ])
        ledger = tmp_path / "ledger.jsonl"
        import_from_bus_history(bus_path=bus, ledger_path=ledger)
        entries2 = import_from_bus_history(bus_path=bus, ledger_path=ledger)
        assert len(entries2) == 0

    def test_empty_message_skipped(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tDECISION\t",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert len(entries) == 0

    def test_correction_type_mapped(self, tmp_path):
        bus = self._make_bus_file(tmp_path, [
            "2026-03-01T10:00:00Z\tagent\tall\tCORRECTION\tFixed an error",
        ])
        entries = import_from_bus_history(bus_path=bus, dry_run=True)
        assert entries[0].type == "correction"


# ---------------------------------------------------------------------------
# import_from_git_log
# ---------------------------------------------------------------------------


@pytest.mark.allow_ledger_writes
class TestImportFromGitLog:
    def _mock_git_output(self, commits):
        """Build mock git log output from list of (hash, date, author, subject)."""
        lines = []
        for h, d, a, s in commits:
            lines.extend([h, d, a, s])
        return "\n".join(lines) + "\n"

    def test_dry_run_basic(self, tmp_path):
        git_output = self._mock_git_output([
            ("abc123def456", "2026-03-01T10:00:00+00:00", "Reuben", "feat: add feature"),
            ("def789ghi012", "2026-03-01T11:00:00+00:00", "Claude", "fix: resolve bug"),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)

        assert len(entries) == 2
        assert entries[0].type == "discovery"  # feat -> discovery
        assert entries[0].vendor == "human"  # Reuben -> human
        assert entries[1].type == "correction"  # fix -> correction
        assert entries[1].vendor == "anthropic"  # Claude -> anthropic

    def test_evidence_has_commit_hash(self, tmp_path):
        git_output = self._mock_git_output([
            ("abcdef123456", "2026-03-01T10:00:00+00:00", "Dev", "feat: test"),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)

        assert entries[0].evidence == "commit:abcdef123456"

    def test_normalizes_to_utc(self):
        # Timezone offset should be normalized to Z
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T15:00:00-05:00", "Dev", "feat: tz test"),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)

        assert entries[0].timestamp.endswith("Z")
        assert "20:00:00" in entries[0].timestamp  # -05:00 -> +5h = 20:00

    def test_git_not_available(self):
        import subprocess
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    side_effect=subprocess.CalledProcessError(1, "git")):
            entries = import_from_git_log(dry_run=True)
        assert entries == []

    def test_empty_output(self):
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=""):
            entries = import_from_git_log(dry_run=True)
        assert entries == []

    def test_skips_empty_subject(self):
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T10:00:00+00:00", "Dev", ""),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)
        assert entries == []

    def test_writes_to_ledger(self, tmp_path):
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T10:00:00+00:00", "Dev", "feat: test write"),
        ])
        ledger = tmp_path / "ledger.jsonl"
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(ledger_path=ledger, dry_run=False)
        assert len(entries) == 1
        assert ledger.exists()

    def test_idempotent(self, tmp_path):
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T10:00:00+00:00", "Dev", "feat: test"),
        ])
        ledger = tmp_path / "ledger.jsonl"
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            import_from_git_log(ledger_path=ledger)
            entries2 = import_from_git_log(ledger_path=ledger)
        assert len(entries2) == 0

    def test_since_passed_to_git(self):
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value="") as mock:
            import_from_git_log(since="2026-03-01", dry_run=True)
        cmd = mock.call_args[0][0]
        assert "--since=2026-03-01" in cmd

    def test_max_commits_passed_to_git(self):
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value="") as mock:
            import_from_git_log(max_commits=50, dry_run=True)
        cmd = mock.call_args[0][0]
        assert "--max-count=50" in cmd

    def test_tags_include_imported_and_git_log(self):
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T10:00:00+00:00", "Dev", "feat: tagged"),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)
        assert "imported" in entries[0].tags
        assert "git-log" in entries[0].tags

    def test_assurance_level_is_verified(self):
        git_output = self._mock_git_output([
            ("aabbccddee00", "2026-03-01T10:00:00+00:00", "Dev", "feat: level"),
        ])
        with patch("hummbl_cognition.migration.subprocess.check_output",
                    return_value=git_output):
            entries = import_from_git_log(dry_run=True)
        assert entries[0].assurance_level == "VERIFIED"
