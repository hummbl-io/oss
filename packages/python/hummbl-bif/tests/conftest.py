"""Test configuration for BIF test suite."""
import sys
from pathlib import Path

# Make mcp_server importable from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import mcp_server


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    """Redirect SESSIONS_DIR to a temp directory for each test."""
    monkeypatch.setattr(mcp_server, "SESSIONS_DIR", tmp_path / "bif-sessions")
    (tmp_path / "bif-sessions").mkdir()
