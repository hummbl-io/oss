"""Regression tests for oss#345 git-vault option-injection guards (A-4/A-5).

Server-dispatch / gateway-wiring coverage (A-2) is provided by
tests/test_mcp_gateway_kill_switch.py, which landed on main via #362. The
former server-level tests in this file were written against the pre-#362
server API (`server.gateway`, older error shape) and were superseded when
main's fail-closed gateway was adopted during the #358 merge.
"""

from pathlib import Path
from unittest.mock import patch

from hummbl_mcp.mcp_git_vault import handle_git_diff, handle_git_stage


def test_vault_git_diff_rejects_option_shaped_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_diff({"paths": ["--output=/tmp/pwned"]})
    assert res["isError"] is True
    assert "Option-shaped path" in res["content"][0]["text"]


def test_vault_git_diff_rejects_outside_workspace_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_diff({"paths": ["../outside.txt"]})
    assert res["isError"] is True
    assert "resolves outside the workspace" in res["content"][0]["text"]


def test_vault_git_stage_rejects_option_shaped_path(tmp_path: Path):
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        res = handle_git_stage({"paths": ["--all"]})
    assert res["isError"] is True
    assert "Option-shaped path" in res["content"][0]["text"]


def test_vault_git_stage_uses_literal_pathspecs(tmp_path: Path):
    (tmp_path / "file[12].txt").write_text("x", encoding="utf-8")
    with patch("hummbl_mcp.mcp_git_vault.get_git_root", return_value=str(tmp_path)):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""
            res = handle_git_stage({"paths": ["file[12].txt"]})
    assert res["isError"] is False
    cmd = mock_run.call_args[0][0]
    assert "--literal-pathspecs" in cmd
