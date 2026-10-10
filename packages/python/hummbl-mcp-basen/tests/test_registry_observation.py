"""Observed registry identity and one detached application input, without models."""
import copy
import hashlib
import json
import socket
import subprocess
import urllib.request
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock

import pytest

from basen import mcp_server as server

ROWS = [
    {"id": "P1", "name": "Synthetic parser record", "definition": "Fixture definition.",
     "domain": "P", "domain_name": "Perspective", "extra": {"flag": True, "text": "\u03bb"}},
    {"id": "IN1", "name": "Second parser record", "definition": "Second fixture.", "domain": "IN"},
]
ARGS = {"operator_id": "P1", "input": "Synthetic input", "mode": "advisory"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def expected_content(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8"))


def forbidden(*args, **kwargs):
    raise AssertionError("Unstubbed external effect")


@pytest.fixture(autouse=True)
def controlled(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "DEFAULT_REGISTRY_JSON", tmp_path / "registry.json")
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {})
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "0")
    for obj, name in ((socket, "socket"), (socket, "create_connection"),
                      (subprocess, "Popen"), (urllib.request, "urlopen"),
                      (server, "_chat_complete"), (server, "_append_tuple_jsonl"),
                      (server, "_embed_text")):
        monkeypatch.setattr(obj, name, forbidden)
    server.DEFAULT_REGISTRY_JSON.write_text(json.dumps(ROWS, ensure_ascii=False), encoding="utf-8")


def observation(**extra):
    return server._tool_apply({**ARGS, **extra})["_execution"]["registry"]


def test_loaded_bytes_and_detached_content_have_distinct_exact_hashes():
    raw = server.DEFAULT_REGISTRY_JSON.read_bytes()
    result = server._tool_apply(ARGS)
    value = result["_execution"]["registry"]
    assert value["artifact_sha256"] == digest(raw)
    assert value["normalized_content_sha256"] == expected_content(ROWS)
    assert value["operator_content_sha256"] == expected_content(ROWS[0])
    assert value["artifact_binding"] == "loaded-bytes-matched"
    assert value["schema"] == "hummbl.basen.registry-observation.v1"
    assert value["content_hash_format"] == "utf8-python-json-sorted-compact-ascii-no-nonfinite-v1"
    assert value["registry_version"] is None
    assert value["source_authority"] == "not authenticated"
    assert value["semantic_validation"] == "not performed" and value["admission"] == "not assessed"
    assert result["_governance"]["evidence"]["application"]["registry"] == value
    assert "Synthetic input" not in json.dumps(value)
    assert "Fixture definition" not in json.dumps(value)
    assert str(server.DEFAULT_REGISTRY_JSON) not in json.dumps(value)


def test_raw_observation_is_immutable_and_not_inherited_by_identical_plain_list(monkeypatch):
    first = observation()
    loaded = server._REGISTRY_CACHE["base120"]
    with pytest.raises(FrozenInstanceError):
        loaded.source_observation.artifact_sha256 = "f" * 64
    with pytest.raises(AttributeError):
        loaded.source_observation = loaded.source_observation
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": copy.deepcopy(list(loaded))})
    second = observation()
    assert first["normalized_content_sha256"] == second["normalized_content_sha256"]
    assert second["artifact_sha256"] is None and second["artifact_binding"] == "raw-source-unavailable"


def test_whitespace_and_key_order_change_raw_identity_only():
    first = observation()
    raw = json.dumps(ROWS, indent=4, sort_keys=True, ensure_ascii=True).encode()
    server.DEFAULT_REGISTRY_JSON.write_bytes(raw)
    server._REGISTRY_CACHE.clear()
    second = observation()
    assert first["artifact_sha256"] != second["artifact_sha256"] == digest(raw)
    assert first["normalized_content_sha256"] == second["normalized_content_sha256"]
    assert first["operator_content_sha256"] == second["operator_content_sha256"]


@pytest.mark.parametrize("index", [0, 1])
def test_selected_and_unselected_changes_are_distinguishable(index):
    first = observation()
    rows = copy.deepcopy(ROWS)
    rows[index]["name"] += " changed"
    raw = json.dumps(rows).encode()
    server.DEFAULT_REGISTRY_JSON.write_bytes(raw)
    server._REGISTRY_CACHE.clear()
    second = observation()
    assert first["artifact_sha256"] != second["artifact_sha256"] == digest(raw)
    assert first["normalized_content_sha256"] != second["normalized_content_sha256"]
    assert (first["operator_content_sha256"] == second["operator_content_sha256"]) is (index == 1)


def test_file_replacement_does_not_relabel_cached_bytes(monkeypatch):
    first = observation()
    server.DEFAULT_REGISTRY_JSON.write_bytes(b"[]")
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    second = observation()
    assert first == second


def test_boolean_to_integer_mutation_invalidates_raw_match_despite_python_equality():
    first = observation()
    rows = server._REGISTRY_CACHE["base120"]
    rows[0]["extra"]["flag"] = 1
    assert rows == ROWS  # Python equality alone would miss the content change.
    second = observation()
    assert second["artifact_binding"] == "cache-content-changed"
    assert second["artifact_sha256"] is None
    assert first["normalized_content_sha256"] != second["normalized_content_sha256"]
    assert first["operator_content_sha256"] != second["operator_content_sha256"]
    assert second["normalized_content_sha256"] == expected_content(rows)


@pytest.mark.parametrize("completion", ["Synthetic completion", None])
def test_completion_mutation_cannot_split_prompt_body_and_observation(monkeypatch, completion):
    first = observation()
    prompts = []
    def chat(prompt, **kwargs):
        prompts.append(prompt)
        row = server._REGISTRY_CACHE["base120"][0]
        row.update(id="IN2", name="AFTER_REQUEST", definition="MUTATED_DEFINITION", domain="IN")
        row["extra"]["flag"] = False
        return completion
    monkeypatch.setattr(server, "_chat_complete", chat)
    result = server._tool_apply({**ARGS, "mode": "empirical"})
    assert len(prompts) == 1 and "operator P1 (Synthetic parser record)" in prompts[0]
    assert "AFTER_REQUEST" not in prompts[0]
    assert result["operator_id"] == result["_execution"]["operator_id"] == "P1"
    assert result["name"] == ROWS[0]["name"] and result["family"] == "P"
    assert result["_execution"]["registry"] == first
    assert result["_governance"]["evidence"]["application"] == result["_execution"]
    if completion is None:
        assert "Fixture definition" in result["walkthrough"][1]["prompt"]
        assert "MUTATED_DEFINITION" not in json.dumps(result)
    else:
        assert result["analysis"] == completion


@pytest.mark.parametrize("mode,completion", [("advisory", None), ("analytic", None),
                                             ("empirical", None), ("empirical", "fixture")])
def test_each_execution_path_carries_the_same_selected_content(monkeypatch, mode, completion):
    monkeypatch.setattr(server, "_chat_complete", Mock(return_value=completion))
    writer = Mock(return_value=True)
    monkeypatch.setattr(server, "_append_tuple_jsonl", writer)
    monkeypatch.setenv("BASEN_PERSIST_TUPLES", "1")
    result = server._tool_apply({**ARGS, "mode": mode})
    value = result["_execution"]["registry"]
    assert value["operator_content_sha256"] == expected_content(ROWS[0])
    assert result["_governance"]["evidence"]["application"] == result["_execution"]
    assert writer.call_count == (0 if mode == "advisory" else 1)
    if mode != "advisory":
        assert writer.call_args.args[0]["evidence"]["application"]["registry"] == value
    value["artifact_sha256"] = "response consumer mutation"
    assert result["_governance"]["evidence"]["application"]["registry"]["artifact_sha256"] != value["artifact_sha256"]


@pytest.mark.parametrize("raw", [b"", b"{", b"\xff", b"{}", b"null", b"[NaN]", b"[Infinity]",
    b"[-Infinity]", b"[1e999]", b'[{"id":"P1","id":"IN1"}]',
    b'[{"extra":{"key":1,"key":2}}]', b"[" * 1500 + b"]" * 1500])
def test_malformed_source_rejected_before_effects(raw):
    server.DEFAULT_REGISTRY_JSON.write_bytes(raw)
    with pytest.raises(server.JsonRpcError) as caught:
        server._tool_apply({**ARGS, "mode": "empirical"})
    assert caught.value.code == server.INTERNAL_ERROR
    assert caught.value.message == "Registry input is unavailable or invalid"


@pytest.mark.parametrize("error", [OSError("PRIVATE_PATH"), ValueError("PRIVATE_DETAIL")])
def test_source_errors_do_not_expose_path_or_exception(monkeypatch, error):
    monkeypatch.setattr(Path, "read_bytes", Mock(side_effect=error))
    with pytest.raises(server.JsonRpcError) as caught:
        server._tool_apply(ARGS)
    assert "PRIVATE" not in json.dumps(caught.value.to_dict())


@pytest.mark.parametrize("kind", ["root", "row", "id_missing", "id_empty", "id_space", "id_bool",
    "duplicate", "name_missing", "definition_number", "domain_list", "nonfinite", "tuple",
    "nonstring_key", "cycle", "object"])
def test_invalid_capture_rejected_before_effects(monkeypatch, kind):
    rows = copy.deepcopy(ROWS)
    if kind == "root": rows = {"operators": rows}
    elif kind == "row": rows.append(None)
    elif kind == "id_missing": rows[1].pop("id")
    elif kind == "id_empty": rows[1]["id"] = ""
    elif kind == "id_space": rows[1]["id"] = " "
    elif kind == "id_bool": rows[1]["id"] = True
    elif kind == "duplicate": rows.append(copy.deepcopy(rows[0]))
    elif kind == "name_missing": rows[0].pop("name")
    elif kind == "definition_number": rows[0]["definition"] = 1
    elif kind == "domain_list": rows[0]["domain"] = []
    elif kind == "nonfinite": rows[1]["extra"] = float("inf")
    elif kind == "tuple": rows[1]["extra"] = (1, 2)
    elif kind == "nonstring_key": rows[1]["extra"] = {1: "x"}
    elif kind == "cycle": rows[1]["extra"] = rows
    elif kind == "object": rows[1]["extra"] = object()
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": rows})
    with pytest.raises(server.JsonRpcError) as caught:
        server._tool_apply({**ARGS, "mode": "empirical"})
    assert caught.value.code == server.INTERNAL_ERROR
    assert caught.value.message == "Registry content cannot support application capture"


def test_missing_requested_id_remains_invalid_argument():
    with pytest.raises(server.JsonRpcError) as caught:
        server._tool_apply({**ARGS, "operator_id": "missing"})
    assert caught.value.code == server.INVALID_PARAMS
