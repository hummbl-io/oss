"""Tests for the doctor command."""

from __future__ import annotations

import os
from pathlib import Path

from hummbl_gitops.doctor import run_doctor
from hummbl_gitops.cli import main as cli_main


class TestDoctor:
    def test_doctor_returns_result(self, tmp_path: Path) -> None:
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
        try:
            result = run_doctor()
            assert len(result.checks) == 6
            check_names = {name for name, _, _ in result.checks}
            assert check_names == {
                "cli_on_path",
                "pre_push_hook",
                "state_dir_writable",
                "gh_authenticated",
                "git_available",
                "python_version",
            }
        finally:
            del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_doctor_state_dir_writable(self, tmp_path: Path) -> None:
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
        try:
            result = run_doctor()
            state_check = next(c for c in result.checks if c[0] == "state_dir_writable")
            assert state_check[1] is True
        finally:
            del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_doctor_python_version_passes(self) -> None:
        result = run_doctor()
        version_check = next(c for c in result.checks if c[0] == "python_version")
        assert version_check[1] is True

    def test_doctor_with_repo_no_hook(self, tmp_path: Path) -> None:
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
        try:
            # Create a fake repo dir without .git/hooks/pre-push
            fake_repo = tmp_path / "fake-repo"
            fake_repo.mkdir()
            result = run_doctor(fake_repo)
            hook_check = next(c for c in result.checks if c[0] == "pre_push_hook")
            assert hook_check[1] is False
        finally:
            del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_doctor_with_repo_has_hook(self, tmp_path: Path) -> None:
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
        try:
            fake_repo = tmp_path / "fake-repo"
            (fake_repo / ".git" / "hooks").mkdir(parents=True)
            (fake_repo / ".git" / "hooks" / "pre-push").write_text("#!/bin/bash\nexit 0\n")
            result = run_doctor(fake_repo)
            hook_check = next(c for c in result.checks if c[0] == "pre_push_hook")
            assert hook_check[1] is True
        finally:
            del os.environ["HUMMBL_GITOPS_STATE_DIR"]

    def test_cli_doctor_command(self, tmp_path: Path, capsys) -> None:
        os.environ["HUMMBL_GITOPS_STATE_DIR"] = str(tmp_path)
        try:
            rc = cli_main(["doctor"])
            out = capsys.readouterr().out
            assert "hummbl-gitops doctor" in out
            assert "Overall:" in out
            # rc is 0 if all passed, 1 if any failed
            # gh_authenticated may fail in CI, so just check rc is 0 or 1
            assert rc in (0, 1)
        finally:
            del os.environ["HUMMBL_GITOPS_STATE_DIR"]
