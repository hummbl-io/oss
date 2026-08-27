"""Tests for the HRSI bridge client."""

from __future__ import annotations

import socket
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hummbl_cognition import belonging_check as bc
from hummbl_cognition import hrsi_bridge_client as hcli
from hummbl_cognition import hrsi_bridge_server as hs
from hummbl_cognition import hrsi_checkin as hc


@pytest.fixture
def isolated_cognition(tmp_path, monkeypatch):
    cog_dir = tmp_path / "cognition"
    cog_dir.mkdir()
    cycles = cog_dir / "hrsi_cycles.jsonl"
    baseline = cog_dir / "belonging_baseline.jsonl"

    monkeypatch.setattr(bc, "COGNITION_DIR", cog_dir)
    monkeypatch.setattr(bc, "BASELINE_PATH", baseline)
    monkeypatch.setattr(hc, "COGNITION_DIR", cog_dir)
    monkeypatch.setattr(hc, "CYCLES_PATH", cycles)
    monkeypatch.setattr(hc, "BASELINE_PATH", baseline)
    monkeypatch.setattr(hs, "CYCLES_PATH", cycles)
    monkeypatch.setattr(hs, "BASELINE_PATH", baseline)

    monkeypatch.setenv("HRSI_BRIDGE_TOKEN", "shared-token-xyz")
    monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)

    yield {"cog_dir": cog_dir, "token": "shared-token-xyz"}


@pytest.fixture
def server(isolated_cognition):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = ThreadingHTTPServer(("127.0.0.1", port), hs.HRSIBridgeHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    yield {"base_url": f"http://127.0.0.1:{port}", "port": port, "server": server}

    server.shutdown()
    thread.join(timeout=3)


class TestLoadBridgeToken:
    def test_env_token(self, monkeypatch):
        monkeypatch.setenv("HRSI_BRIDGE_TOKEN", "env-tok")
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)
        assert hcli._load_bridge_token() == "env-tok"

    def test_file_token(self, tmp_path, monkeypatch):
        token_file = tmp_path / "hrsi_token"
        token_file.write_text("file-tok")
        token_file.chmod(0o600)
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN", raising=False)
        monkeypatch.setenv("HRSI_BRIDGE_TOKEN_FILE", str(token_file))
        assert hcli._load_bridge_token() == "file-tok"

    def test_no_token(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN", raising=False)
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)
        # Point DEFAULT_TOKEN_FILE at a nonexistent path
        monkeypatch.setattr(hcli, "DEFAULT_TOKEN_FILE", tmp_path / "nonexistent")
        assert hcli._load_bridge_token() is None


class TestPostToBridge:
    def test_success(self, server, isolated_cognition):
        result = hcli.post_hrsi_to_bridge_url_result(
            server["base_url"],
            cogstate="AVAILABLE",
            safety=4,
            mattering=3,
            connection=4,
            hule="Client test check-in",
            lens="bki",
            energy=3,
            sleep_hours=7.0,
        )
        assert result["ok"] is True
        assert result["status_code"] == 200
        assert result["body"]["status"] == "ok"
        assert result["body"]["cycle"]["hule"] == "Client test check-in"

    def test_auth_failure(self, server, isolated_cognition, monkeypatch):
        # Client sends a wrong token without changing the server's env
        monkeypatch.setattr(hcli, "_load_bridge_token", lambda: "wrong-token")
        result = hcli.post_hrsi_to_bridge_url_result(
            server["base_url"],
            cogstate="AVAILABLE",
            safety=4,
            mattering=3,
            connection=4,
            hule="test",
        )
        assert result["ok"] is False
        assert result["status_code"] == 401
        assert result["permanent_error"] is True

    def test_connection_error(self, isolated_cognition):
        result = hcli.post_hrsi_to_bridge_url_result(
            "http://127.0.0.1:1",  # port 1 = nothing listening
            cogstate="AVAILABLE",
            safety=4,
            mattering=3,
            connection=4,
            hule="test",
        )
        assert result["ok"] is False
        assert result["status_code"] is None
        assert result["permanent_error"] is False

    def test_validation_error_is_permanent(self, server, isolated_cognition):
        result = hcli.post_hrsi_to_bridge_url_result(
            server["base_url"],
            cogstate="INVALID",
            safety=4,
            mattering=3,
            connection=4,
            hule="test",
        )
        assert result["ok"] is False
        assert result["status_code"] == 400
        assert result["permanent_error"] is True


class TestHealthCheck:
    def test_health_ok(self, server):
        assert hcli.health_check("127.0.0.1", server["port"]) is True

    def test_health_fail(self):
        assert hcli.health_check("127.0.0.1", 1) is False
