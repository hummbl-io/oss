"""Tests for the pre-push hook script.

Tests that the hook gracefully skips when hummbl-gitops is not on PATH,
and that it runs the check when the CLI is available.
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest


HOOK_TEMPLATE = """\
#!/usr/bin/env bash
# hummbl-gitops pre-push hook (test copy)

GITOPS="${HUMMBL_GITOPS_BIN:-hummbl-gitops}"

if ! command -v "$GITOPS" &>/dev/null; then
    echo "[hummbl-gitops] CLI not found, skipping pre-push check"
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"

echo "[hummbl-gitops] Running local CI check before push..."

if [ -n "${HUMMBL_GITOPS_FULL_CONTRACT:-}" ]; then
    "$GITOPS" pre-push --repo "$REPO_ROOT" --full-contract || RESULT=$?
else
    "$GITOPS" pre-push --repo "$REPO_ROOT" || RESULT=$?
fi

RESULT=${RESULT:-0}

if [ $RESULT -ne 0 ]; then
    echo "[hummbl-gitops] Local CI check FAILED. Push blocked."
    exit 1
fi

echo "[hummbl-gitops] Local CI check passed."
exit 0
"""


@pytest.fixture
def hook_script(tmp_path: Path) -> Path:
    """Create a test copy of the pre-push hook."""
    hook = tmp_path / "pre-push"
    hook.write_text(HOOK_TEMPLATE)
    hook.chmod(0o755)
    return hook


class TestPrePushHookGracefulSkip:
    """Test that the hook skips gracefully when hummbl-gitops is not installed."""

    def test_skips_when_cli_not_found(self, hook_script: Path) -> None:
        """Hook should exit 0 and print skip message when CLI is not on PATH."""
        env = os.environ.copy()
        # Ensure hummbl-gitops is not findable
        env["PATH"] = "/usr/bin:/bin"  # minimal PATH without hummbl-gitops
        env.pop("HUMMBL_GITOPS_BIN", None)

        result = subprocess.run(
            [str(hook_script)],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0
        assert "CLI not found" in result.stdout
        assert "skipping" in result.stdout

    def test_runs_when_cli_found(self, hook_script: Path, tmp_git_repo: Path) -> None:
        """Hook should run the CLI when hummbl-gitops is on PATH."""
        # Point HUMMBL_GITOPS_BIN to the real CLI
        from hummbl_gitops.cli import main as cli_main

        # The hook calls hummbl-gitops pre-push, which needs a git repo
        # We test the logic by setting HUMMBL_GITOPS_BIN to a script that exits 0
        fake_cli = tmp_git_repo.parent / "fake-gitops"
        fake_cli.write_text("#!/usr/bin/env bash\nexit 0\n")
        fake_cli.chmod(0o755)

        env = os.environ.copy()
        env["HUMMBL_GITOPS_BIN"] = str(fake_cli)

        result = subprocess.run(
            [str(hook_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(tmp_git_repo),
        )

        assert result.returncode == 0
        assert "Running local CI check" in result.stdout
        assert "passed" in result.stdout

    def test_blocks_when_cli_fails(self, hook_script: Path, tmp_git_repo: Path) -> None:
        """Hook should exit 1 when the CLI returns non-zero."""
        fake_cli = tmp_git_repo.parent / "fake-gitops-fail"
        fake_cli.write_text("#!/usr/bin/env bash\necho 'tests failed'\nexit 1\n")
        fake_cli.chmod(0o755)

        env = os.environ.copy()
        env["HUMMBL_GITOPS_BIN"] = str(fake_cli)

        result = subprocess.run(
            [str(hook_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(tmp_git_repo),
        )

        assert result.returncode == 1
        assert "FAILED" in result.stdout
        assert "Push blocked" in result.stdout

    def test_custom_bin_env_var(self, hook_script: Path) -> None:
        """Hook should respect HUMMBL_GITOPS_BIN env var."""
        # Use a non-existent binary path
        env = os.environ.copy()
        env["HUMMBL_GITOPS_BIN"] = "/nonexistent/path/hummbl-gitops"

        result = subprocess.run(
            [str(hook_script)],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should skip because the custom bin doesn't exist
        assert result.returncode == 0
        assert "CLI not found" in result.stdout
