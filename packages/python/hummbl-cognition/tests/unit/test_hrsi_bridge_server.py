"""Tests for the HRSI bridge server."""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hummbl_cognition import belonging_check as bc
from hummbl_cognition import hrsi_bridge_server as hs
from hummbl_cognition import hrsi_checkin as hc

# ---------------------------------------------------------------------------
# Test fixture: ephemeral cognition dir + bridge server on a random port
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_cognition(tmp_path, monkeypatch):
    """Point all HRSI paths at a temp dir and set a known bridge token."""
    cog_dir = tmp_path / "cognition"
    cog_dir.mkdir()
    cycles = cog_dir / "hrsi_cycles.jsonl"
    baseline = cog_dir / "belonging_baseline.jsonl"

    # Patch module-level constants (no reload needed)
    monkeypatch.setattr(bc, "COGNITION_DIR", cog_dir)
    monkeypatch.setattr(bc, "BASELINE_PATH", baseline)
    monkeypatch.setattr(hc, "COGNITION_DIR", cog_dir)
    monkeypatch.setattr(hc, "CYCLES_PATH", cycles)
    monkeypatch.setattr(hc, "BASELINE_PATH", baseline)
    monkeypatch.setattr(hs, "CYCLES_PATH", cycles)
    monkeypatch.setattr(hs, "BASELINE_PATH", baseline)

    monkeypatch.setenv("HRSI_BRIDGE_TOKEN", "test-token-abc123")
    monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)

    yield {
        "cog_dir": cog_dir,
        "cycles_path": cycles,
        "baseline_path": baseline,
        "token": "test-token-abc123",
    }


@pytest.fixture
def running_server(isolated_cognition):
    """Start a bridge server on localhost with a random port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = ThreadingHTTPServer(("127.0.0.1", port), hs.HRSIBridgeHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "port": port,
        "server": server,
        "token": isolated_cognition["token"],
    }

    server.shutdown()
    thread.join(timeout=3)


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------


class TestLoadBridgeCredentials:
    def test_env_token(self, monkeypatch):
        monkeypatch.setenv("HRSI_BRIDGE_TOKEN", "my-token")
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)
        creds = hs._load_bridge_credentials()
        assert creds == {"default": "my-token"}

    def test_no_credentials(self, monkeypatch):
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN", raising=False)
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN_FILE", raising=False)
        assert hs._load_bridge_credentials() == {}

    def test_json_token_file(self, tmp_path, monkeypatch):
        token_file = tmp_path / "tokens.json"
        token_file.write_text(
            json.dumps({"client-a": "token-a", "client-b": "token-b"})
        )
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN", raising=False)
        monkeypatch.setenv("HRSI_BRIDGE_TOKEN_FILE", str(token_file))
        creds = hs._load_bridge_credentials()
        assert creds == {"client-a": "token-a", "client-b": "token-b"}

    def test_plaintext_token_file(self, tmp_path, monkeypatch):
        token_file = tmp_path / "token.txt"
        token_file.write_text("plain-token-value")
        monkeypatch.delenv("HRSI_BRIDGE_TOKEN", raising=False)
        monkeypatch.setenv("HRSI_BRIDGE_TOKEN_FILE", str(token_file))
        creds = hs._load_bridge_credentials()
        assert creds == {"default": "plain-token-value"}


# ---------------------------------------------------------------------------
# HTTP endpoint tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_unauthenticated(self, running_server):
        req = Request(f"{running_server['base_url']}/health")
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["status"] == "up"
            assert data["service"] == "hrsi-bridge"

    def test_health_shows_auth_enabled(self, running_server):
        req = Request(f"{running_server['base_url']}/health")
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            assert data["auth_enabled"] is True


class TestPostHrsi:
    def _post(self, base_url, body, token=None):
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(f"{base_url}/hrsi", data=data, headers=headers, method="POST")
        return req

    def test_valid_checkin(self, running_server, isolated_cognition):
        body = {
            "cogstate": "AVAILABLE",
            "safety": 4,
            "mattering": 3,
            "connection": 4,
            "hule": "Noticed a pattern between bus bridge and HRSI needs",
            "energy": 3,
            "sleep_hours": 7.5,
        }
        req = self._post(running_server["base_url"], body, running_server["token"])
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["status"] == "ok"
            assert data["cycle"]["cogstate"] == "AVAILABLE"
            assert data["cycle"]["safety"] == 4
            assert data["cycle"]["belonging_avg"] == pytest.approx(3.67, abs=0.01)
            assert data["total_cycles"] == 1

        # Verify it was written to the cycles file
        cycles = (
            isolated_cognition["cycles_path"].read_text(encoding="utf-8").splitlines()
        )
        assert len(cycles) == 1
        written = json.loads(cycles[0])
        assert written["hule"] == "Noticed a pattern between bus bridge and HRSI needs"

    def test_missing_auth_returns_401(self, running_server):
        body = {
            "cogstate": "AVAILABLE",
            "safety": 4,
            "mattering": 3,
            "connection": 4,
            "hule": "test",
        }
        req = self._post(running_server["base_url"], body, token=None)
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 401

    def test_wrong_token_returns_401(self, running_server):
        body = {
            "cogstate": "AVAILABLE",
            "safety": 4,
            "mattering": 3,
            "connection": 4,
            "hule": "test",
        }
        req = self._post(running_server["base_url"], body, token="wrong-token")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 401

    def test_missing_fields_returns_400(self, running_server):
        body = {"cogstate": "AVAILABLE", "safety": 4}
        req = self._post(running_server["base_url"], body, running_server["token"])
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 400

    def test_invalid_cogstate_returns_400(self, running_server):
        body = {
            "cogstate": "INVALID",
            "safety": 4,
            "mattering": 3,
            "connection": 4,
            "hule": "test",
        }
        req = self._post(running_server["base_url"], body, running_server["token"])
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 400

    def test_score_out_of_range_returns_400(self, running_server):
        body = {
            "cogstate": "AVAILABLE",
            "safety": 6,
            "mattering": 3,
            "connection": 4,
            "hule": "test",
        }
        req = self._post(running_server["base_url"], body, running_server["token"])
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 400

    def test_optional_fields_accepted(self, running_server, isolated_cognition):
        body = {
            "cogstate": "AVAILABLE",
            "safety": 5,
            "mattering": 5,
            "connection": 5,
            "hule": "great day",
            "lens": "bki",
            "delta": "K+: new insight",
            "energy": 4,
            "sleep_hours": 8.0,
            "relational_note": "Coffee with Dan",
            "origin_machine": "iphone",
        }
        req = self._post(running_server["base_url"], body, running_server["token"])
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["cycle"]["lens"] == "bki"
            assert data["cycle"]["delta"] == "K+: new insight"
            assert data["cycle"]["energy"] == 4
            assert data["cycle"]["sleep_hours"] == 8.0
            assert data["cycle"]["relational_note"] == "Coffee with Dan"
            assert data["origin_machine"] == "iphone"


class TestGetEndpoints:
    def test_status_authenticated(self, running_server):
        req = Request(f"{running_server['base_url']}/hrsi/status")
        req.add_header("Authorization", f"Bearer {running_server['token']}")
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert "gap1_qualifying_days" in data
            assert "total_cycles" in data

    def test_status_unauthenticated_401(self, running_server):
        req = Request(f"{running_server['base_url']}/hrsi/status")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 401

    def test_last_empty(self, running_server):
        req = Request(f"{running_server['base_url']}/hrsi/last")
        req.add_header("Authorization", f"Bearer {running_server['token']}")
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["cycle"] is None

    def test_404_unknown_path(self, running_server):
        req = Request(f"{running_server['base_url']}/unknown")
        with pytest.raises(HTTPError) as exc_info:
            urlopen(req, timeout=5)
        assert exc_info.value.code == 404
