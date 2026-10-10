"""Application provenance and failure receipts, without actual model calls."""
from __future__ import annotations

import builtins
import http.client
import json
import socket
import subprocess
import urllib.error
import urllib.request
from unittest import mock

import pytest

from basen import basen_tuple
from basen import mcp_server as server

OPERATOR = {"id": "P1", "name": "Perspective", "domain": "P",
            "domain_name": "Perspective", "definition": "Identify the observer.",
            "difficulty": "easy"}
REAL_APPEND = basen_tuple.append_tuple


def forbidden(*args, **kwargs):
    raise AssertionError("Unstubbed external effect")


@pytest.fixture(autouse=True)
def controlled_effects(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": [OPERATOR.copy()]})
    monkeypatch.setattr(server, "_TUPLE_LOG_PATH", tmp_path / "tuples.jsonl")
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "0")
    monkeypatch.setattr(server, "OLLAMA_CHAT_MODEL", "synthetic-model")
    monkeypatch.setattr(server, "OLLAMA_CHAT_URL", "http://127.0.0.1:1/synthetic")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(basen_tuple, "append_tuple", forbidden)


@pytest.mark.parametrize("mode,completion,actual,method,tier", [
    ("advisory", None, "advisory", "operator-description-v0.1", 0),
    ("analytic", None, "analytic", "family-template-v0.2", 1),
    ("empirical", "PRIVATE_COMPLETION", "empirical", "ollama-chat-v0.2", 1),
    ("empirical", None, "analytic", "family-template-v0.2", 1),
])
@pytest.mark.parametrize("persistence", ["disabled", "saved", "failed"])
def test_requested_actual_and_persistence_paths(monkeypatch, mode, completion, actual, method, tier, persistence):
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "0" if persistence == "disabled" else "1")
    args = {"operator_id": "P1", "input": "PRIVATE_INPUT", "mode": mode}
    with mock.patch.object(server, "_chat_complete", return_value=completion) as chat, \
         mock.patch.object(server, "_append_tuple_jsonl", return_value=persistence == "saved") as writer:
        result = server._tool_apply(args)
    assert result["mode"] == mode
    assert result["operator_id"] == "P1" and result["variant"] == "base120"
    execution = result["_execution"]
    assert execution["requested_mode"] == mode
    assert execution["actual_mode"] == actual and execution["actual_method"] == method
    assert execution["fallback_used"] is (mode != actual)
    assert execution.get("fallback_reason") == ("completion_unavailable" if mode != actual else None)
    governance = result["_governance"]
    assert governance["evidence"] == {"application": execution}
    assert governance["args_hash"] == server._args_hash(args)
    assert governance["tier"] == tier and governance["state"] == "ok"
    assert governance["persistence_status"] == ("not_applicable" if tier == 0 else persistence)
    assert governance.get("persisted") == (None if tier == 0 else persistence == "saved")
    assert chat.call_count == (1 if mode == "empirical" else 0)
    assert writer.call_count == (1 if tier == 1 and persistence != "disabled" else 0)
    if mode == "empirical" and actual == "analytic":
        assert result["method"] == "empirical-degraded-to-analytic"
        assert "unreachable" not in result["_note"].lower()
    if actual == "empirical":
        assert result["analysis"] == completion
        assert execution["configured_model"] == "synthetic-model"
    evidence = json.dumps(governance["evidence"])
    assert all(marker not in evidence for marker in ("PRIVATE_INPUT", "PRIVATE_COMPLETION", server.OLLAMA_CHAT_URL))


def test_defaulted_mode_keeps_original_argument_hash():
    args = {"operator_id": "P1", "input": "example"}
    result = server._tool_apply(args)
    assert result["mode"] == "advisory"
    assert result["_execution"]["requested_mode"] == "advisory"
    assert result["_governance"]["args_hash"] == server._args_hash(args)
    assert result["_governance"]["args_hash"] != server._args_hash({**args, "mode": "advisory"})


@pytest.mark.parametrize("args", [
    {"operator_id": 1, "input": "x"}, {"operator_id": "P1", "input": 1},
    {"operator_id": "P1", "input": "x", "mode": "unsupported"},
    {"operator_id": "MISSING", "input": "x"},
])
def test_invalid_application_does_not_execute_or_append(args):
    with mock.patch.object(server, "_chat_complete", side_effect=forbidden), \
         mock.patch.object(server, "_append_tuple_jsonl", side_effect=forbidden), \
         pytest.raises(server.JsonRpcError):
        server._tool_apply(args)


def response(raw):
    value = mock.MagicMock()
    value.__enter__.return_value.read.return_value = raw
    return value


@pytest.mark.parametrize("value", [None, [], True, 42, "text", {}, {"message": None},
    {"message": []}, {"message": True}, {"message": "text"}, {"message": {}},
    {"message": {"content": None}}, {"message": {"content": 42}},
    {"message": {"content": []}}, {"message": {"content": ""}},
    {"message": {"content": " \n\t"}},
])
def test_unusable_response_shapes_fall_back(monkeypatch, value):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: response(json.dumps(value).encode()))
    assert server._chat_complete("input") is None


@pytest.mark.parametrize("raw", [b"\xff", b"{", b"", b"{" + b'"x":[' * 2000])
def test_invalid_response_bytes_fall_back(monkeypatch, raw):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: response(raw))
    assert server._chat_complete("input") is None


@pytest.mark.parametrize("error", [urllib.error.URLError("PRIVATE_ERROR"),
    urllib.error.HTTPError("PRIVATE_ENDPOINT", 500, "PRIVATE_ERROR", {}, None),
    http.client.HTTPException("PRIVATE_ERROR"), OSError("PRIVATE_ERROR"),
    ValueError("PRIVATE_ERROR"), TypeError("PRIVATE_ERROR"),
    OverflowError("PRIVATE_ERROR"), RecursionError("PRIVATE_ERROR"),
])
def test_transport_errors_return_generic_fallback(monkeypatch, error):
    monkeypatch.setattr(urllib.request, "urlopen", mock.Mock(side_effect=error))
    result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "empirical"})
    assert result["_execution"]["actual_mode"] == "analytic"
    assert "PRIVATE_" not in json.dumps(result)


@pytest.mark.parametrize("endpoint", ["PRIVATE_ENDPOINT_MARKER", "http://[PRIVATE_ENDPOINT_MARKER"])
def test_request_construction_failure_is_private(monkeypatch, endpoint):
    monkeypatch.setattr(server, "OLLAMA_CHAT_URL", endpoint)
    response_obj = server.handle_request("tools/call", {"name": "basen_apply", "arguments": {
        "operator_id": "P1", "input": "x", "mode": "empirical"}})
    assert "PRIVATE_ENDPOINT_MARKER" not in json.dumps(response_obj)
    assert json.loads(response_obj["content"][0]["text"])["_execution"]["actual_mode"] == "analytic"


@pytest.mark.parametrize("setting", ["OLLAMA_CHAT_MODEL", "OLLAMA_CHAT_URL"])
@pytest.mark.parametrize("value", [None, "", " ", 1, False, []])
def test_invalid_configuration_does_not_dispatch(monkeypatch, setting, value):
    monkeypatch.setattr(server, setting, value)
    with mock.patch.object(server, "_chat_complete", side_effect=forbidden):
        result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "empirical"})
    assert result["_execution"]["actual_mode"] == "analytic"


def test_captured_configuration_matches_payload_and_receipt(monkeypatch):
    seen = []
    def transport(request, **kwargs):
        seen.append((request.full_url, json.loads(request.data)))
        monkeypatch.setattr(server, "OLLAMA_CHAT_MODEL", "changed-model")
        monkeypatch.setattr(server, "OLLAMA_CHAT_URL", "changed-endpoint")
        return response(b'{"message":{"content":"  usable completion  "}}')
    monkeypatch.setattr(urllib.request, "urlopen", transport)
    result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "empirical"})
    assert seen[0][0] == "http://127.0.0.1:1/synthetic"
    assert seen[0][1]["model"] == result["model"] == result["_execution"]["configured_model"] == "synthetic-model"
    assert result["analysis"] == "  usable completion  "
    assert len(seen) == 1


@pytest.mark.parametrize("error", [OSError("private"), ImportError("private"),
    AttributeError("private"), KeyError("private"), RuntimeError("private")])
def test_preferred_writer_failure_never_selects_fallback(monkeypatch, error):
    writer = mock.Mock(side_effect=error)
    monkeypatch.setattr(basen_tuple, "append_tuple", writer)
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "1")
    with mock.patch.object(builtins, "open", side_effect=forbidden):
        result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "analytic"})
    assert writer.call_count == 1
    assert result["walkthrough"] and result["_governance"]["persistence_status"] == "failed"


def test_partial_append_is_not_retried(monkeypatch):
    def partial(tuple_record, *, path):
        with open(path, "a", encoding="utf-8") as stream:
            stream.write("SYNTHETIC_PARTIAL\n")
        raise OSError("Unconfirmed append")
    monkeypatch.setattr(basen_tuple, "append_tuple", partial)
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "1")
    with mock.patch.object(server, "_chat_complete", return_value="completed") as chat:
        result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "empirical"})
    assert result["analysis"] == "completed" and chat.call_count == 1
    assert result["_governance"]["persistence_status"] == "failed"
    assert server._TUPLE_LOG_PATH.read_text(encoding="utf-8") == "SYNTHETIC_PARTIAL\n"


def test_real_preferred_writer_retains_evidence_in_test_owned_file(monkeypatch):
    monkeypatch.setattr(basen_tuple, "append_tuple", REAL_APPEND)
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "1")
    result = server._tool_apply({"operator_id": "P1", "input": "PRIVATE_INPUT", "mode": "analytic"})
    records = server._TUPLE_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(records) == 1
    stored = json.loads(records[0])
    assert stored["evidence"] == {"application": result["_execution"]}
    assert stored["args_hash"] == result["_governance"]["args_hash"]
    assert "PRIVATE_INPUT" not in records[0]
    assert "persistence_status" not in stored and "persisted" not in stored
    assert result["_governance"]["persistence_status"] == "saved"


def test_import_unavailable_uses_one_compatibility_append(monkeypatch):
    real_import = builtins.__import__
    def import_without_tuple(name, *args, **kwargs):
        if name == "basen.basen_tuple":
            raise ImportError("Synthetic unavailable writer")
        return real_import(name, *args, **kwargs)
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "1")
    with mock.patch.object(builtins, "__import__", side_effect=import_without_tuple):
        result = server._tool_apply({"operator_id": "P1", "input": "x", "mode": "analytic"})
    records = server._TUPLE_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(records) == 1
    assert json.loads(records[0])["evidence"] == {"application": result["_execution"]}
    assert result["_governance"]["persistence_status"] == "saved"


def test_other_tool_persistence_metadata_unchanged(monkeypatch):
    monkeypatch.setattr(server, "_recommend_via_embeddings", lambda *a, **k: None)
    results = [server._tool_operator_lookup({"operator_id": "P1"}),
               server._tool_family_browse({"family": "P"}),
               server._tool_recommend({"problem_description": "observer", "top_k": 1})]
    for result in results:
        assert "_execution" not in result
        assert "persistence_status" not in result["_governance"]
        assert "persisted" not in result["_governance"]
        if "_selection" in result:
            assert result["_governance"]["evidence"] == {"recommendation": result["_selection"]}
        else:
            assert result["_governance"]["evidence"] == {}
