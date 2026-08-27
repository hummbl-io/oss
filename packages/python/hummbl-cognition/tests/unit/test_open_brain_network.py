"""Tests for Open Brain server and client (network layer)."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

import pytest
from hummbl_cognition.models import LedgerEntry


def _make_entry(content: str, **kwargs) -> LedgerEntry:
    defaults = dict(
        agent="test-agent",
        vendor="anthropic",
        model="test-model",
        entry_type="lesson",
        scope="project",
    )
    defaults.update(kwargs)
    return LedgerEntry.create(content=content, **defaults)


def _write_ledger(path: Path, entries: list[LedgerEntry]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for e in entries:
            f.write(e.to_jsonl() + "\n")
    return path


class TestOpenBrainServer:
    """Test the HTTP server + client integration."""

    def _post(self, port: int, path: str, body: dict | None = None) -> tuple[int, dict]:
        """Helper to post JSON payloads and parse response JSON."""
        conn = HTTPConnection("127.0.0.1", port)
        data = json.dumps(body or {}).encode("utf-8")
        conn.request(
            "POST", path, body=data, headers={"Content-Type": "application/json"}
        )
        resp = conn.getresponse()
        return resp.status, json.loads(resp.read().decode("utf-8"))

    @pytest.fixture
    def brain_server(self, tmp_path):
        """Start a test server on a random port."""
        from http.server import HTTPServer

        from hummbl_cognition.server import OpenBrainState, _make_handler

        # Create test data
        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("Circuit breaker tripped for GitHub adapter after 3 failures"),
            _make_entry("Kill switch engaged due to cost overrun threshold breach"),
        ]
        _write_ledger(cog_dir / "ledger.jsonl", entries)

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        handler = _make_handler(state)
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        yield f"http://127.0.0.1:{port}", entries

        server.shutdown()

    def test_health(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        assert client.health() is True

    def test_status(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, entries = brain_server
        client = OpenBrainClient(url)
        status = client.status()
        assert status["service"] == "open-brain"
        assert status["version"] == "0.1.0"
        assert status["index"]["total_docs"] == 3

    def test_search(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, entries = brain_server
        client = OpenBrainClient(url)
        results = client.search("OAuth token refresh")
        assert len(results) > 0
        assert results[0]["source"] == "ledger"
        # First result should be the OAuth entry
        assert (
            "oauth" in results[0]["content"].lower() or "OAuth" in results[0]["content"]
        )

    def test_search_with_budget(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        results = client.search("OAuth", token_budget=50)
        total = sum(r.get("tokens", 0) for r in results)
        assert total <= 50

    def test_search_no_results(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        results = client.search("xyzzy nonexistent gibberish")
        assert results == []

    def test_search_missing_query(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        with pytest.raises(RuntimeError, match="missing"):
            client._request("POST", "/search", {})

    def test_reindex(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        result = client.reindex()
        assert result["reindexed"] is True
        assert result["entry_count"] == 3

    @pytest.mark.allow_ledger_writes
    def test_ingest(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)

        new_entry = _make_entry(
            "Windows Desktop autoresearch found learning rate improvement",
            agent="windows-brain",
        )

        result = client.ingest([new_entry.to_dict()])
        assert result["ingested"] == 1

        # Should be searchable now
        results = client.search("learning rate")
        assert len(results) > 0

    def test_404(self, brain_server):
        from hummbl_cognition.client import OpenBrainClient

        url, _ = brain_server
        client = OpenBrainClient(url)
        with pytest.raises(RuntimeError, match="not found"):
            client._request("GET", "/nonexistent")

    def test_bus_post(self, tmp_path, monkeypatch):
        from http.server import HTTPServer

        from hummbl_bus.bus_policy import reset_bus_policy
        from hummbl_cognition.server import OpenBrainState, _make_handler

        monkeypatch.setenv("BUS_SECURITY_POLICY", "permissive")
        reset_bus_policy()

        entries = [_make_entry("OAuth token refresh failed during morning briefing")]
        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        _write_ledger(cog_dir / "ledger.jsonl", entries)
        bus_root = tmp_path / "_state" / "coordination"

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        handler = _make_handler(state)
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            status, body = self._post(
                port,
                "/bus/post",
                {
                    "from": "codex",
                    "to": "all",
                    "type": "STATUS",
                    "message": "relayed by open-brain",
                },
            )

            assert status == 200
            assert body["posted"] is True
            bus_file = bus_root / "messages.tsv"
            assert bus_file.exists()
            rows = bus_file.read_text(encoding="utf-8").splitlines()
            assert any("relayed by open-brain" in row for row in rows)
        finally:
            server.shutdown()

    def test_bus_post_rejects_missing_message(self, tmp_path):
        from http.server import HTTPServer

        from hummbl_cognition.server import OpenBrainState, _make_handler

        entries = [_make_entry("Token rotation cadence for OAuth clients")]
        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        _write_ledger(cog_dir / "ledger.jsonl", entries)

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        handler = _make_handler(state)
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            status, body = self._post(
                port,
                "/bus/post",
                {
                    "from": "codex",
                    "to": "all",
                    "type": "STATUS",
                },
            )

            assert status == 400
            assert body["error"].startswith("missing required field")
        finally:
            server.shutdown()

    def test_lineage_endpoint(self, tmp_path):
        from http.client import HTTPConnection
        from http.server import HTTPServer

        from hummbl_cognition.server import OpenBrainState, _make_handler

        entries = [
            _make_entry(
                "Original finding",
                previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
            ),
        ]
        target_id = entries[0].id
        child = _make_entry("Correction finding", supersedes=target_id)
        entries.append(child)

        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        _write_ledger(cog_dir / "ledger.jsonl", entries)

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        handler = _make_handler(state)
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            conn = HTTPConnection("127.0.0.1", port)
            conn.request("GET", f"/lineage/{target_id}")
            resp = conn.getresponse()
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))

            assert body["entry_id"] == target_id
            assert len(body["children"]) == 1
            assert body["children"][0]["id"] == child.id
            assert body["children"][0]["relation"] == "superseded_by"
        finally:
            server.shutdown()


class TestOpenBrainClientOffline:
    """Test client behavior when server is unreachable."""

    def test_health_returns_false_when_unreachable(self):
        from hummbl_cognition.client import OpenBrainClient

        client = OpenBrainClient("http://127.0.0.1:19999", timeout=1)
        assert client.health() is False

    def test_default_url_from_env(self, monkeypatch):
        from hummbl_cognition.client import OpenBrainClient

        monkeypatch.setenv("OPEN_BRAIN_URL", "http://10.0.0.1:9999")
        client = OpenBrainClient()
        assert client.host == "10.0.0.1"
        assert client.port == 9999

    def test_default_url_fallback(self, monkeypatch):
        from hummbl_cognition.client import OpenBrainClient

        monkeypatch.delenv("OPEN_BRAIN_URL", raising=False)
        client = OpenBrainClient()
        assert client.host == "100.117.251.32"
        assert client.port == 11435


class TestOpenBrainState:
    """Test server state management."""

    def test_init_builds_index(self, tmp_path):
        from hummbl_cognition.server import OpenBrainState

        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        entries = [_make_entry("test content")]
        _write_ledger(cog_dir / "ledger.jsonl", entries)

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        assert state.index.total_docs == 1

    def test_search_increments_count(self, tmp_path):
        from hummbl_cognition.server import OpenBrainState

        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        _write_ledger(cog_dir / "ledger.jsonl", [_make_entry("test")])

        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        assert state.request_count == 0
        state.search({"query": "test"})
        assert state.request_count == 1


class TestConsolidateEndpoint:
    """Test POST /consolidate endpoint."""

    @pytest.fixture
    def consolidate_server(self, tmp_path):
        """Start a test server with auth token for consolidation tests."""
        from http.server import HTTPServer

        from hummbl_cognition.server import OpenBrainState, _make_handler

        cog_dir = tmp_path / "cognition"
        cog_dir.mkdir()
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token expired causing calendar sync failure"),
            _make_entry("Circuit breaker tripped for GitHub adapter after 3 failures"),
        ]
        _write_ledger(cog_dir / "ledger.jsonl", entries)

        token = "test-secret-token"
        state = OpenBrainState(
            state_dir=tmp_path,
            ledger_path=cog_dir / "ledger.jsonl",
        )
        handler = _make_handler(state, auth_token=token)
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        yield {
            "url": f"http://127.0.0.1:{port}",
            "port": port,
            "token": token,
            "state": state,
            "tmp_path": tmp_path,
        }

        server.shutdown()

    def _post(self, port, path, body=None, token=None):
        """Helper to make a POST request."""
        conn = HTTPConnection("127.0.0.1", port)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(body or {}).encode("utf-8")
        conn.request("POST", path, body=data, headers=headers)
        resp = conn.getresponse()
        return resp.status, json.loads(resp.read().decode("utf-8"))

    @patch("hummbl_cognition.server.run_consolidation")
    def test_consolidate_dry_run(self, mock_consolidate, consolidate_server):
        """POST /consolidate with dry_run=true passes through and returns result."""
        mock_consolidate.return_value = {
            "groups_found": 1,
            "consolidated": 1,
            "skipped": 0,
            "errors": [],
        }

        status, body = self._post(
            consolidate_server["port"],
            "/consolidate",
            body={"dry_run": True},
            token=consolidate_server["token"],
        )

        assert status == 200
        assert body["groups_found"] == 1
        assert body["consolidated"] == 1
        # Verify dry_run was passed through
        mock_consolidate.assert_called_once()
        call_kwargs = mock_consolidate.call_args
        assert call_kwargs[1]["dry_run"] is True

    def test_consolidate_requires_auth(self, consolidate_server):
        """POST /consolidate without auth token returns 401."""
        status, body = self._post(
            consolidate_server["port"],
            "/consolidate",
            body={},
            token=None,
        )

        assert status == 401
        assert body["error"] == "unauthorized"

    @patch("hummbl_cognition.server.run_consolidation")
    def test_consolidate_returns_result(self, mock_consolidate, consolidate_server):
        """POST /consolidate returns the consolidation result dict."""
        mock_consolidate.return_value = {
            "groups_found": 2,
            "consolidated": 2,
            "skipped": 0,
            "errors": [],
        }

        status, body = self._post(
            consolidate_server["port"],
            "/consolidate",
            body={},
            token=consolidate_server["token"],
        )

        assert status == 200
        assert body["groups_found"] == 2
        assert body["consolidated"] == 2
        assert body["skipped"] == 0
        assert body["errors"] == []
