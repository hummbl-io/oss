"""Bridge-client tests for request forwarding and idempotency responses."""

from __future__ import annotations

import io
import json
import urllib.error

from hummbl_bus import bridge_client


class _Response:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_success_forwards_proof_and_propagates_duplicate(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, *, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.get_header("Authorization")
        captured["client_id"] = request.get_header("X-bridge-client-id")
        captured["timeout"] = timeout
        return _Response({"status": "ok", "duplicate": True})

    monkeypatch.setattr(bridge_client.urllib.request, "urlopen", fake_urlopen)

    result = bridge_client.post_to_remote_bus_result(
        "bus.example",
        "codex",
        "all",
        "DECISION",
        "host=anvil approved",
        timestamp="2026-08-31T01:02:03Z",
        request_id="request-123",
        correlation_id="correlation-123",
        origin_machine="anvil",
        principal_proof="signed-proof",
        bearer_token="test-bound-token",
        client_id="codex",
    )

    assert captured["payload"] == {
        "from": "codex",
        "to": "all",
        "type": "DECISION",
        "message": "host=anvil approved",
        "timestamp": "2026-08-31T01:02:03Z",
        "request_id": "request-123",
        "correlation_id": "correlation-123",
        "origin_machine": "anvil",
        "principal_proof": "signed-proof",
    }
    assert captured["timeout"] == 10
    assert captured["authorization"] == "Bearer test-bound-token"
    assert captured["client_id"] == "codex"
    assert result == {
        "ok": True,
        "duplicate": True,
        "permanent_error": False,
        "status_code": 200,
        "error": "",
    }


def test_success_without_duplicate_marker_is_not_duplicate(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge_client.urllib.request,
        "urlopen",
        lambda request, *, timeout: _Response({"status": "ok"}),
    )

    result = bridge_client.post_to_remote_bus_result(
        "bus.example",
        "codex",
        "all",
        "STATUS",
        "host=anvil ready",
    )

    assert result["ok"] is True
    assert result["duplicate"] is False
    assert result["permanent_error"] is False


def test_http_409_is_permanent_conflict_not_duplicate(monkeypatch) -> None:
    body = io.BytesIO(
        json.dumps(
            {
                "status": "conflict",
                "code": "idempotency_key_conflict",
                "duplicate": False,
            }
        ).encode("utf-8")
    )
    conflict = urllib.error.HTTPError(
        "http://bus.example:18790/bus",
        409,
        "Conflict",
        hdrs=None,
        fp=body,
    )

    def raise_conflict(request, *, timeout):
        raise conflict

    monkeypatch.setattr(bridge_client.urllib.request, "urlopen", raise_conflict)

    result = bridge_client.post_to_remote_bus_result(
        "bus.example",
        "codex",
        "all",
        "STATUS",
        "host=anvil changed payload",
        request_id="request-123",
    )

    assert result["ok"] is False
    assert result["duplicate"] is False
    assert result["permanent_error"] is True
    assert result["status_code"] == 409
    assert "idempotency_key_conflict" in str(result["error"])
