"""Subprocess-based CLI tests for bif_cli.py."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
CLI = str(REPO_ROOT / "bif_cli.py")


def run(args: list[str], tmp_path: Path, **kwargs) -> subprocess.CompletedProcess:
    """Run the CLI with BIF_SESSIONS_DIR isolated to tmp_path."""
    env = {**os.environ, "BIF_SESSIONS_DIR": str(tmp_path)}
    return subprocess.run(
        [sys.executable, CLI] + args,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# bif --help
# ---------------------------------------------------------------------------
class TestHelp:
    def test_help_exits_0(self, tmp_path):
        result = run(["--help"], tmp_path)
        assert result.returncode == 0

    def test_help_mentions_subcommands(self, tmp_path):
        result = run(["--help"], tmp_path)
        for cmd in ("start", "status", "template", "validate", "templates"):
            assert cmd in result.stdout


# ---------------------------------------------------------------------------
# bif start
# ---------------------------------------------------------------------------
class TestStart:
    def test_start_exits_0(self, tmp_path):
        result = run(["start", "TestDomain"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_start_stdout_contains_session_id(self, tmp_path):
        result = run(["start", "TestDomain"], tmp_path)
        assert "Session ID" in result.stdout or "session_id" in result.stdout.lower()

    def test_start_with_batches_exits_0(self, tmp_path):
        result = run(["start", "TestDomain", "--batches", "5"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_start_stdout_contains_domain(self, tmp_path):
        result = run(["start", "MySpecialDomain"], tmp_path)
        assert "MySpecialDomain" in result.stdout

    def test_start_stdout_contains_phase_prompt(self, tmp_path):
        result = run(["start", "TestDomain"], tmp_path)
        # Phase 1 prompt should mention FOUNDATION or Phase 1
        assert "Phase 1" in result.stdout or "FOUNDATION" in result.stdout

    def test_start_creates_session_file(self, tmp_path):
        result = run(["start", "TestDomain"], tmp_path)
        assert result.returncode == 0
        # Session files should exist in tmp_path
        session_files = list(tmp_path.glob("*.json"))
        assert len(session_files) == 1


# ---------------------------------------------------------------------------
# bif status
# ---------------------------------------------------------------------------
class TestStatus:
    def test_status_no_arg_exits_0(self, tmp_path):
        result = run(["status"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_status_lists_sessions(self, tmp_path):
        # Create a session first
        run(["start", "DomainA"], tmp_path)
        result = run(["status"], tmp_path)
        assert result.returncode == 0
        assert "DomainA" in result.stdout

    def test_status_with_session_id_exits_0(self, tmp_path):
        # Start a session and capture its ID
        start_result = run(["start", "TestDomain"], tmp_path)
        assert start_result.returncode == 0
        # Extract session ID from output
        for line in start_result.stdout.splitlines():
            if "Session ID" in line:
                session_id = line.split(":")[-1].strip()
                break
        result = run(["status", session_id], tmp_path)
        assert result.returncode == 0

    def test_status_no_sessions_shows_message(self, tmp_path):
        result = run(["status"], tmp_path)
        assert result.returncode == 0
        # With no sessions, total count is 0 or "No sessions"
        assert "0" in result.stdout or "No sessions" in result.stdout


# ---------------------------------------------------------------------------
# bif template
# ---------------------------------------------------------------------------
class TestTemplate:
    def test_template_phase1_batch1_exits_0(self, tmp_path):
        result = run(["template", "1", "1"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_template_phase1_batch1_mentions_core_reference(self, tmp_path):
        result = run(["template", "1", "1"], tmp_path)
        assert "Core Reference" in result.stdout or "FOUNDATION" in result.stdout

    def test_template_phase2_batch5_exits_0(self, tmp_path):
        result = run(["template", "2", "5"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_template_phase2_batch5_mentions_technique(self, tmp_path):
        result = run(["template", "2", "5"], tmp_path)
        assert "TECHNIQUE" in result.stdout or "Best Practices" in result.stdout

    def test_template_invalid_phase_exits_nonzero(self, tmp_path):
        result = run(["template", "99", "1"], tmp_path)
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# bif templates
# ---------------------------------------------------------------------------
class TestTemplates:
    def test_templates_exits_0(self, tmp_path):
        result = run(["templates"], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_templates_mentions_generic(self, tmp_path):
        result = run(["templates"], tmp_path)
        assert "generic" in result.stdout.lower()


# ---------------------------------------------------------------------------
# bif validate
# ---------------------------------------------------------------------------
class TestValidate:
    def test_validate_nonexistent_file_exits_nonzero(self, tmp_path):
        result = run(["validate", "nonexistent_file.md"], tmp_path)
        assert result.returncode != 0

    def test_validate_good_file_exits_0(self, tmp_path):
        """A well-formed batch file should exit 0 regardless of PASS/FAIL."""
        good_content = (
            "# Anthropic -- Core Reference\n"
            "> Source: https://docs.anthropic.com\n"
            "> Fetched: 2026-04-11\n"
            "> Purpose: Official API/product docs\n"
            "\n---\n"
            "\n## Overview\n"
            "Anthropic builds Claude models.\n"
            "\n## API Reference\n"
            "See https://docs.anthropic.com/api\n"
            "\n## Models\n"
            "| Model | Context | Cost |\n"
            "| --- | --- | --- |\n"
            "| claude-3-5-sonnet | 200k | $3/M |\n"
            "\n```python\nimport anthropic\nclient = anthropic.Anthropic()\n```\n"
        )
        good_file = tmp_path / "good_batch.md"
        good_file.write_text(good_content)
        result = run(["validate", str(good_file)], tmp_path)
        assert result.returncode == 0, result.stderr

    def test_validate_good_file_shows_pass(self, tmp_path):
        good_content = (
            "# Anthropic -- Core Reference\n"
            "> Source: https://docs.anthropic.com\n"
            "> Fetched: 2026-04-11\n"
            "> Purpose: Official API/product docs\n"
            "\n---\n"
            "\n## Overview\n"
            "Anthropic builds Claude models.\n"
            "\n## API Reference\n"
            "See https://docs.anthropic.com/api\n"
            "\n## Models\n"
            "| Model | Context | Cost |\n"
            "| --- | --- | --- |\n"
            "| claude-3-5-sonnet | 200k | $3/M |\n"
            "\n```python\nimport anthropic\nclient = anthropic.Anthropic()\n```\n"
        )
        good_file = tmp_path / "good_batch.md"
        good_file.write_text(good_content)
        result = run(["validate", str(good_file)], tmp_path)
        assert "PASS" in result.stdout

    def test_validate_minimal_file_shows_fail(self, tmp_path):
        """Minimal content should fail most BIF quality checks."""
        bad_content = "# Hello\n\nThis is minimal content.\n"
        bad_file = tmp_path / "bad_batch.md"
        bad_file.write_text(bad_content)
        result = run(["validate", str(bad_file)], tmp_path)
        # Should exit 0 (tool ran) but output FAIL
        assert result.returncode == 0, result.stderr
        assert "FAIL" in result.stdout

    def test_validate_shows_check_details(self, tmp_path):
        content = "# Test\n\nSome content.\n"
        f = tmp_path / "test_batch.md"
        f.write_text(content)
        result = run(["validate", str(f)], tmp_path)
        assert "PASS" in result.stdout or "FAIL" in result.stdout
        # Should show individual check results
        assert "[PASS]" in result.stdout or "[FAIL]" in result.stdout
