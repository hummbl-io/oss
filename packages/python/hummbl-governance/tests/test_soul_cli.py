"""Tests for the SOUL CLI (soul_cli.py).

Tests the CLI entry point with a minimal SOUL.md fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_governance.soul_cli import main


@pytest.fixture
def soul_md(tmp_path: Path) -> Path:
    """Create a minimal valid SOUL.md file."""
    content = """---
name: test-agent
version: "1.0.0"
description: A test agent for CLI testing
personality: |
  You are a test agent.
governance:
  trust_tier: MEDIUM
  authority_scope: advisory
  regulatory_profile: minimal-risk
---

You are a test agent used for CLI testing.
"""
    path = tmp_path / "SOUL.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def invalid_soul_md(tmp_path: Path) -> Path:
    """Create an invalid SOUL.md (missing required fields)."""
    content = """---
name: incomplete-agent
---

Some prose body.
"""
    path = tmp_path / "InvalidSOUL.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestSoulCLI:
    """Tests for soul_cli.main()."""

    def test_no_args_prints_usage(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul"])
        result = main()
        assert result == 1

    def test_inject(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "inject", str(soul_md)])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "test agent" in captured.out.lower()

    def test_persona(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "persona", str(soul_md)])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_regulatory(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "regulatory", str(soul_md)])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_resolve(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "resolve", str(soul_md)])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["name"] == "test-agent"

    def test_validate_valid(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "validate", str(soul_md)])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "VALID" in captured.out
        assert "test-agent" in captured.out

    def test_validate_invalid_missing_fields(
        self, invalid_soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "validate", str(invalid_soul_md)])
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "INVALID" in captured.out
        assert "missing" in captured.out.lower()

    def test_unknown_command(
        self, soul_md: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["hummbl-soul", "unknown", str(soul_md)])
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
