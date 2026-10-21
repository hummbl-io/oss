"""Recommendation snapshot/effect observations with test-owned data and mocks."""
import copy
import hashlib
import json
import math
import socket
import subprocess
import urllib.request
from pathlib import Path

import pytest

from basen import mcp_server as server

ROWS = [
    {"id": "P1", "name": "Synthetic alpha", "definition": "alpha fixture",
     "domain": "P", "domain_name": "Perspective", "extra": {"text": "\u03bb", "flag": True}},
    {"id": "IN1", "name": "Synthetic beta", "definition": "beta fixture", "domain": "IN"},
]
ARGS = {"problem_description": "alpha", "top_k": 2}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def content_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode())


def forbidden(*args, **kwargs):
    raise AssertionError("Unexpected external effect")


@pytest.fixture(autouse=True)
def controlled(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "DEFAULT_REGISTRY_JSON", tmp_path / "registry.json")
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {})
    monkeypatch.setattr(server, "EMBED_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(server, "OLLAMA_EMBED_MODEL", "fixture-model")
    monkeypatch.setattr(server, "OLLAMA_EMBED_URL", "http://fixture.invalid/?token=PRIVATE_MARKER")
    for obj, name in ((socket, "socket"), (socket, "create_connection"),
                      (subprocess, "Popen"), (urllib.request, "urlopen"),
                      (server, "_append_tuple_jsonl"), (server, "_chat_complete")):
        monkeypatch.setattr(obj, name, forbidden)
    monkeypatch.setattr(server, "_embed_text", lambda *a, **k: [1.0, 0.0])
    server.DEFAULT_REGISTRY_JSON.write_bytes(json.dumps(ROWS, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode())


def result(**extra):
    return server._tool_recommend({**ARGS, **extra})


def telemetry(value):
    return value["_selection"]["embedding"]


def install_cache(payload=None):
    rows = server._registry()
    fingerprint = server._registry_fingerprint(rows)
    path = server.EMBED_CACHE_DIR / f"embeddings_v1_base120_{fingerprint}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if payload is None:
        payload = {"schema": "hummbl.basen.operator-embeddings.v1", "fingerprint": fingerprint,
                   "dimension": 2, "embeddings": {"P1": [1.0, 0.0], "IN1": [0.0, 1.0]}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_observation_binds_loaded_bytes_and_ordered_returned_records():
    raw = server.DEFAULT_REGISTRY_JSON.read_bytes()
    value = result()
    selection = value["_selection"]
    assert selection["schema"] == "hummbl.basen.recommendation-observation.v1"
    assert selection["actual_method"] == value["method"] == "embedding-cosine-v0.2"
    assert selection["fallback_used"] is False
    assert selection["variant"] == "base120"
    observation = selection["registry"]
    assert observation["artifact_sha256"] == digest(raw)
    assert observation["normalized_content_sha256"] == content_digest(ROWS)
    assert observation["artifact_binding"] == "loaded-bytes-matched"
    assert observation["registry_version"] is None
    assert observation["source_authority"] == "not authenticated"
    assert observation["semantic_validation"] == "not performed"
    assert observation["admission"] == "not assessed"
    assert selection["selected_operators"] == [
        {"operator_id": row["id"], "operator_content_sha256": content_digest(row)} for row in ROWS]
    assert value["_governance"]["evidence"] == {"recommendation": selection}
    assert value["_governance"]["tier"] == 0
    assert "persisted" not in value["_governance"]
    assert "persistence_status" not in value["_governance"]
    encoded = json.dumps(selection)
    for marker in ("PRIVATE_MARKER", "fixture.invalid", str(server.EMBED_CACHE_DIR), "alpha fixture"):
        assert marker not in encoded


def test_read_miss_compute_write_and_query_counts():
    value = result()
    observed = telemetry(value)
    assert observed == {
        "computation_fingerprint": server._registry_fingerprint(server._registry()),
        "configured_model": "fixture-model", "operator_cache_read": "miss",
        "operator_cache_write": "write_returned", "operator_embedding_calls": 2,
        "query_embedding_calls": 1, "failure_stage": None,
    }


def test_cache_hit_only_calls_query(monkeypatch):
    path = install_cache()
    raw = path.read_bytes()
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kw: calls.append(text) or [0, 1])
    value = result()
    assert calls == [ARGS["problem_description"]]
    assert telemetry(value)["operator_cache_read"] == "hit"
    assert telemetry(value)["operator_cache_write"] == "not_attempted"
    assert telemetry(value)["operator_embedding_calls"] == 0
    assert telemetry(value)["query_embedding_calls"] == 1
    assert value["recommendations"][0]["operator_id"] == "IN1"
    assert path.read_bytes() == raw


@pytest.mark.parametrize("payload", [{}, [], {"schema": "wrong"}, None])
def test_invalid_cache_recomputed_and_reported(payload):
    path = install_cache({} if payload is None else payload)
    if payload is None:
        path.write_text("{ invalid", encoding="utf-8")
    value = result()
    assert telemetry(value)["operator_cache_read"] == "invalid"
    assert telemetry(value)["operator_cache_write"] == "write_returned"
    assert telemetry(value)["operator_embedding_calls"] == 2


@pytest.mark.parametrize("read_error,write_error", [(True, False), (False, True), (True, True)])
def test_read_and_write_errors_observed_without_leaking_errors(monkeypatch, read_error, write_error):
    server._registry()
    original = Path.open

    def controlled_open(path, mode="r", *args, **kwargs):
        if path.name.startswith("embeddings_v1_") and (
            ("w" in mode and write_error) or ("w" not in mode and read_error)
        ):
            raise PermissionError("PRIVATE_MARKER")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", controlled_open)
    value = result()
    assert value["method"] == "embedding-cosine-v0.2"
    assert telemetry(value)["operator_cache_read"] == ("unavailable" if read_error else "miss")
    assert telemetry(value)["operator_cache_write"] == ("failed" if write_error else "write_returned")
    assert "PRIVATE_MARKER" not in json.dumps(value)


@pytest.mark.parametrize("fail_at,stage,operator_calls,query_calls,write", [
    (1, "operator_embeddings", 1, 0, "not_attempted"),
    (2, "operator_embeddings", 2, 0, "not_attempted"),
    (3, "query_embedding", 2, 1, "write_returned"),
])
def test_fallback_keeps_prior_effects(monkeypatch, fail_at, stage, operator_calls, query_calls, write):
    calls = []

    def embed(text, **kwargs):
        calls.append(text)
        return None if len(calls) == fail_at else [1, 0]

    monkeypatch.setattr(server, "_embed_text", embed)
    value = result()
    assert value["method"] == "keyword-overlap-v0.1-fallback"
    assert value["_selection"]["fallback_used"] is True
    assert telemetry(value)["failure_stage"] == stage
    assert telemetry(value)["operator_embedding_calls"] == operator_calls
    assert telemetry(value)["query_embedding_calls"] == query_calls
    assert telemetry(value)["operator_cache_write"] == write
    assert value["_selection"]["selected_operators"][0]["operator_content_sha256"] == content_digest(ROWS[0])


def test_similarity_failure_retains_cache_and_query_observations(monkeypatch):
    monkeypatch.setattr(server, "_cosine_similarity", lambda *a: math.nan)
    value = result()
    assert telemetry(value)["failure_stage"] == "similarity"
    assert telemetry(value)["operator_cache_write"] == "write_returned"
    assert telemetry(value)["query_embedding_calls"] == 1


@pytest.mark.parametrize("setting", ["OLLAMA_EMBED_MODEL", "OLLAMA_EMBED_URL"])
@pytest.mark.parametrize("value", [None, ""])
def test_unavailable_configuration_does_not_claim_embedding_or_cache_calls(monkeypatch, setting, value):
    monkeypatch.setattr(server, setting, value)
    monkeypatch.setattr(server, "_embed_text", forbidden)
    answer = result()
    assert telemetry(answer) == {**server._new_embedding_observation(), "failure_stage": "embedding_inputs"}
    assert answer["method"] == "keyword-overlap-v0.1-fallback"


@pytest.mark.parametrize("change", ["name", "id", "replacement", "nested"])
@pytest.mark.parametrize("failure", [False, True])
def test_one_snapshot_survives_effect_boundary_mutation(monkeypatch, change, failure):
    original_rows = server._registry()
    calls = []

    def embed(text, **kwargs):
        calls.append(text)
        if change == "replacement":
            changed = copy.deepcopy(ROWS)
            changed[0]["name"] = "Changed alpha"
            server._REGISTRY_CACHE["base120"] = changed
        elif change == "nested":
            original_rows[0]["extra"]["flag"] = False
        else:
            original_rows[0][change] = "Changed alpha"
        return None if failure else [1, 0]

    monkeypatch.setattr(server, "_embed_text", embed)
    value = result()
    assert value["recommendations"][0]["operator_id"] == "P1"
    assert value["recommendations"][0]["name"] == ROWS[0]["name"]
    assert value["recommendations"][0]["definition"] == ROWS[0]["definition"]
    assert value["_selection"]["registry"]["normalized_content_sha256"] == content_digest(ROWS)
    assert value["_selection"]["registry"]["artifact_binding"] == "loaded-bytes-matched"
    assert value["_selection"]["selected_operators"][0]["operator_content_sha256"] == content_digest(ROWS[0])
    assert all("Changed alpha" not in text for text in calls)


def test_direct_embedding_helper_also_captures_before_effects(monkeypatch):
    rows = server._registry()

    def embed(*args, **kwargs):
        rows[0]["id"] = "Changed"
        return [1, 0]

    monkeypatch.setattr(server, "_embed_text", embed)
    value = server._recommend_via_embeddings("query", "base120", 1)
    assert value["recommendations"][0]["operator_id"] == "P1"


def test_file_replacement_after_load_keeps_actual_loaded_binding():
    loaded = server._registry()
    raw = server.DEFAULT_REGISTRY_JSON.read_bytes()
    server.DEFAULT_REGISTRY_JSON.write_text("[]", encoding="utf-8")
    answer = result()
    assert answer["_selection"]["registry"]["artifact_sha256"] == digest(raw)
    assert len(loaded) == 2


@pytest.mark.parametrize("replace", [False, True])
def test_changed_or_unbound_cache_never_inherits_raw_identity(monkeypatch, replace):
    rows = server._registry()
    if replace:
        monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": copy.deepcopy(list(rows))})
    else:
        rows[0]["extra"]["flag"] = False
    observation = result()["_selection"]["registry"]
    assert observation["artifact_sha256"] is None
    assert observation["artifact_binding"] == ("raw-source-unavailable" if replace else "cache-content-changed")


def test_evidence_is_deeply_detached():
    value = result()
    evidence = copy.deepcopy(value["_governance"]["evidence"])
    value["_selection"]["registry"]["artifact_sha256"] = "changed"
    value["_selection"]["embedding"]["operator_embedding_calls"] = 999
    value["_selection"]["selected_operators"][0]["operator_id"] = "changed"
    assert value["_governance"]["evidence"] == evidence
    assert server._registry()[0]["id"] == "P1"


@pytest.mark.parametrize("field", ["name", "definition", "domain", "domain_name"])
@pytest.mark.parametrize("value", [None, 7, {"b": 1, "a": 2}, ["text"]])
def test_malformed_participating_text_rejected_before_effects(monkeypatch, field, value):
    rows = server._registry()
    rows[1][field] = value
    monkeypatch.setattr(server, "_embed_text", forbidden)
    with pytest.raises(server.JsonRpcError, match="Registry content cannot support recommendation capture"):
        result()
    assert not server.EMBED_CACHE_DIR.exists()


@pytest.mark.parametrize("change", ["duplicate", "empty_id", "not_object", "tuple", "cycle", "nan"])
def test_malformed_registry_rejected_before_effects(monkeypatch, change):
    rows = server._registry()
    if change == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif change == "empty_id":
        rows[1]["id"] = " "
    elif change == "not_object":
        rows.append("not a record")
    elif change == "tuple":
        rows[0]["extra"] = (1, 2)
    elif change == "cycle":
        rows[0]["extra"] = rows
    else:
        rows[0]["extra"] = math.nan
    monkeypatch.setattr(server, "_embed_text", forbidden)
    with pytest.raises(server.JsonRpcError, match="Registry content cannot support recommendation capture"):
        result()
    assert not server.EMBED_CACHE_DIR.exists()


def test_absent_family_name_remains_empty_input_text(monkeypatch):
    captured = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kw: captured.append(text) or [1, 0])
    result()
    assert captured[1] == "Synthetic beta —  — beta fixture"


def test_empty_registry_keeps_empty_fallback_without_effects(monkeypatch):
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": []})
    monkeypatch.setattr(server, "_embed_text", forbidden)
    value = result()
    assert value["recommendations"] == []
    assert value["_selection"]["selected_operators"] == []
    assert telemetry(value)["failure_stage"] == "embedding_inputs"
    assert not server.EMBED_CACHE_DIR.exists()


@pytest.mark.parametrize("top_k,expected", [(0, 0), (-1, 1), (1, 1), (2, 2)])
def test_no_overlap_fallback_preserves_existing_top_k_slicing(monkeypatch, top_k, expected):
    monkeypatch.setattr(server, "_embed_text", lambda *a, **k: None)
    value = result(problem_description="zzzzzz", top_k=top_k)
    assert len(value["recommendations"]) == expected
    assert len(value["_selection"]["selected_operators"]) == expected


@pytest.mark.parametrize("top_k,expected", [(0, 1), (-1, 1), (1, 1), (2, 2)])
def test_embedding_preserves_existing_top_k_minimum(top_k, expected):
    value = result(top_k=top_k)
    assert len(value["recommendations"]) == expected
