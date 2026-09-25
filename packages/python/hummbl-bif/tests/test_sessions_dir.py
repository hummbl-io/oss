"""Regression tests for SESSIONS_DIR default resolution.

Sessions are cross-lane coordination state — the default must be durable
per-user state, not a volatile tmpdir (lost on reboot on tmpfs systems).
"""

import importlib
import sys
import tempfile
from pathlib import Path

import mcp_server
import pytest


def test_default_sessions_dir_not_tmp(monkeypatch):
    """Without BIF_SESSIONS_DIR, the default must be durable per-user state."""
    if sys.platform == "win32":
        pytest.skip("POSIX XDG path assertion")
    monkeypatch.delenv("BIF_SESSIONS_DIR", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    try:
        default = mcp_server._default_sessions_dir()
        assert not str(default).startswith(tempfile.gettempdir())
        assert default == Path.home() / ".local" / "state" / "bif" / "sessions"
    finally:
        importlib.reload(mcp_server)


def test_xdg_state_home_respected(monkeypatch, tmp_path):
    if sys.platform == "win32":
        pytest.skip("POSIX XDG path assertion")
    monkeypatch.delenv("BIF_SESSIONS_DIR", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    try:
        assert mcp_server._default_sessions_dir() == tmp_path / "bif" / "sessions"
    finally:
        importlib.reload(mcp_server)


def test_env_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("BIF_SESSIONS_DIR", str(tmp_path))
    try:
        importlib.reload(mcp_server)
        assert str(mcp_server.SESSIONS_DIR) == str(tmp_path)
    finally:
        monkeypatch.delenv("BIF_SESSIONS_DIR", raising=False)
        importlib.reload(mcp_server)
