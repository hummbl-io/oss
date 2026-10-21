"""Cache identity and numeric correctness without model or network calls."""
import copy
import http.client
import io
import json
import math
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from basen import mcp_server as server


@pytest.fixture(autouse=True)
def prohibit_external_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected network, process or ledger activity")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    monkeypatch.setattr(server, "_emit_tuple", lambda *args, **kwargs: {"fixture": True})


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    bundled = json.loads((Path(server.__file__).parent / "data/base120_registry.json").read_bytes())
    rows = [copy.deepcopy(next(row for row in bundled if row["id"] == code)) for code in ("P1", "IN1")]
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": rows})
    monkeypatch.setattr(server, "EMBED_CACHE_DIR", tmp_path)
    monkeypatch.setattr(server, "OLLAMA_EMBED_MODEL", "fixture-model")
    monkeypatch.setattr(server, "OLLAMA_EMBED_URL", "http://fixture.invalid/embeddings")
    return rows, tmp_path


def cache_path(rows, root):
    return root / f"embeddings_v1_base120_{server._registry_fingerprint(rows)}.json"


def cache_payload(rows):
    return {"schema": "hummbl.basen.operator-embeddings.v1",
            "fingerprint": server._registry_fingerprint(rows), "dimension": 2,
            "embeddings": {"P1": [1.0, 0.0], "IN1": [0.0, 1.0]}}


def test_computes_complete_set_then_reuses_warm_cache(snapshot, monkeypatch):
    rows, root = snapshot
    calls = []
    def embed(text, **kwargs):
        calls.append((text, kwargs))
        return [1.0, 0.0] if len(calls) == 1 else [0.0, 1.0]
    monkeypatch.setattr(server, "_embed_text", embed)
    first = server._load_or_compute_operator_embeddings("base120")
    assert first == {"P1": [1.0, 0.0], "IN1": [0.0, 1.0]}
    assert len(calls) == 2
    assert [text for text, _ in calls] == [server._operator_corpus_text(row) for row in rows]
    assert all(options == {"model": "fixture-model", "endpoint": "http://fixture.invalid/embeddings"}
               for _, options in calls)
    assert json.loads(cache_path(rows, root).read_bytes()) == cache_payload(rows)
    assert server._load_or_compute_operator_embeddings("base120") == first
    assert len(calls) == 2


@pytest.mark.parametrize("change", ["name", "domain_name", "definition", "id", "model", "endpoint", "order"])
def test_changed_computation_inputs_miss_existing_cache(snapshot, monkeypatch, change):
    rows, root = snapshot
    old_path = cache_path(rows, root)
    old_raw = json.dumps(cache_payload(rows)).encode()
    old_path.write_bytes(old_raw)
    if change == "model":
        monkeypatch.setattr(server, "OLLAMA_EMBED_MODEL", "different-model")
    elif change == "endpoint":
        monkeypatch.setattr(server, "OLLAMA_EMBED_URL", "http://different.invalid/embeddings")
    elif change == "order":
        rows.reverse()
    else:
        rows[0][change] += "-changed"
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: calls.append(text) or [0.5, 0.5])
    result = server._load_or_compute_operator_embeddings("base120")
    assert result is not None
    assert len(calls) == 2
    assert cache_path(rows, root) != old_path
    assert old_path.read_bytes() == old_raw


def test_unembedded_metadata_does_not_change_computation_identity(snapshot):
    rows, _ = snapshot
    original = server._registry_fingerprint(rows)
    rows[0]["difficulty"] = "fixture-unembedded-metadata"
    assert server._registry_fingerprint(rows) == original


def test_legacy_cache_is_left_untouched_and_not_reused(snapshot, monkeypatch):
    _, root = snapshot
    legacy = root / "embeddings_base120_legacy.json"
    raw = b'{"P1":[9,9]}'
    legacy.write_bytes(raw)
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: calls.append(text))
    assert server._load_or_compute_operator_embeddings("base120") is None
    assert len(calls) == 1
    assert legacy.read_bytes() == raw
    assert list(root.iterdir()) == [legacy]


@pytest.mark.parametrize("damage", [
    lambda value: value.update(schema="old"),
    lambda value: value.update(fingerprint="f" * 64),
    lambda value: value.update(dimension=3),
    lambda value: value.update(dimension=True),
    lambda value: value.update(unrecognized=True),
    lambda value: value["embeddings"].pop("P1"),
    lambda value: value["embeddings"].update(extra=[1, 0]),
    lambda value: value["embeddings"].update(P1=[]),
    lambda value: value["embeddings"].update(P1=[0, 0]),
    lambda value: value["embeddings"].update(P1=[1, 0, 1]),
    lambda value: value["embeddings"].update(P1=[True, False]),
    lambda value: value["embeddings"].update(P1=["1", "0"]),
    lambda value: value["embeddings"].update(P1=[None, 1]),
    lambda value: value["embeddings"].update(P1=[float("nan"), 1]),
    lambda value: value["embeddings"].update(P1=[float("inf"), 1]),
    lambda value: value["embeddings"].update(P1=[10 ** 1000, 1]),
])
def test_invalid_cache_recomputes_or_falls_back_without_partial_reuse(snapshot, monkeypatch, damage):
    rows, root = snapshot
    value = cache_payload(rows)
    damage(value)
    path = cache_path(rows, root)
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: calls.append(text))
    assert server._load_or_compute_operator_embeddings("base120") is None
    assert len(calls) == 1
    assert path.read_bytes() == raw


@pytest.mark.parametrize("raw", [b"null", b"[]", b"{", b"\xff", b'{"schema":1,"schema":2}',
                                  b"[" * 1500 + b"0" + b"]" * 1500])
def test_unreadable_or_ambiguous_json_cache_is_a_miss(snapshot, monkeypatch, raw):
    rows, root = snapshot
    cache_path(rows, root).write_bytes(raw)
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: calls.append(text))
    assert server._load_or_compute_operator_embeddings("base120") is None
    assert len(calls) == 1


def test_bad_cache_replaced_only_after_complete_valid_computation(snapshot, monkeypatch):
    rows, root = snapshot
    path = cache_path(rows, root)
    path.write_bytes(b"broken")
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: [1, 2])
    assert server._load_or_compute_operator_embeddings("base120") == {"P1": [1.0, 2.0], "IN1": [1.0, 2.0]}
    saved = json.loads(path.read_bytes())
    assert set(saved["embeddings"]) == {"P1", "IN1"}
    assert saved["dimension"] == 2


@pytest.mark.parametrize("second", [None, [], [0, 0], [1, 2, 3], [float("nan"), 1], [True, 1]])
def test_partial_or_inconsistent_computation_is_never_written(snapshot, monkeypatch, second):
    _, root = snapshot
    values = iter(([1, 0], second))
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: next(values))
    assert server._load_or_compute_operator_embeddings("base120") is None
    assert list(root.iterdir()) == []


def test_cache_write_failure_keeps_valid_in_memory_result(snapshot, monkeypatch):
    rows, root = snapshot
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: [1, 2])
    original_open = Path.open
    def open_file(path, mode="r", *args, **kwargs):
        if "w" in mode:
            raise PermissionError("fixture write failure")
        return original_open(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", open_file)
    assert server._load_or_compute_operator_embeddings("base120") == {"P1": [1.0, 2.0], "IN1": [1.0, 2.0]}
    assert not cache_path(rows, root).exists()


@pytest.mark.parametrize("rows", [[], [{"id": "same"}, {"id": "same"}], [{"id": []}], [None]])
def test_invalid_selected_ids_do_not_touch_cache_or_embed(snapshot, monkeypatch, rows):
    monkeypatch.setattr(server, "_REGISTRY_CACHE", {"base120": rows})
    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected cache or embedding call")
    monkeypatch.setattr(server, "_embed_text", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    assert server._load_or_compute_operator_embeddings("base120") is None


def test_materialized_text_and_configuration_stay_together(snapshot, monkeypatch):
    rows, root = snapshot
    initial_texts = [server._operator_corpus_text(row) for row in rows]
    initial_path = cache_path(rows, root)
    calls = []
    def embed(text, **options):
        calls.append((text, options))
        rows[1]["name"] = "changed after capture"
        monkeypatch.setattr(server, "OLLAMA_EMBED_MODEL", "changed-after-capture")
        monkeypatch.setattr(server, "OLLAMA_EMBED_URL", "http://changed.invalid/")
        return [1, 2]
    monkeypatch.setattr(server, "_embed_text", embed)
    assert server._load_or_compute_operator_embeddings("base120") is not None
    assert [text for text, _ in calls] == initial_texts
    assert all(options == {"model": "fixture-model", "endpoint": "http://fixture.invalid/embeddings"}
               for _, options in calls)
    assert initial_path.exists()


@pytest.mark.parametrize("raw", [
    b"null", b"[]", b"{}", b"{", b"\xff", b'{"embedding":null}',
    b'{"embedding":[]}', b'{"embedding":[0,0]}', b'{"embedding":[true,1]}',
    b'{"embedding":["1",2]}', b'{"embedding":[null,2]}', b'{"embedding":[NaN,1]}',
    b'{"embedding":[Infinity,1]}', b'{"embedding":[1e9999,1]}',
    b'{"embedding":[1,0],"embedding":[0,1]}',
])
def test_malformed_transport_response_safely_returns_none(monkeypatch, raw):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(raw))
    assert server._embed_text("fixture", endpoint="http://fixture.invalid/") is None


def test_valid_transport_uses_captured_configuration(monkeypatch):
    calls = []
    def respond(request, **kwargs):
        calls.append(request)
        return io.BytesIO(b'{"embedding":[1,2.5]}')
    monkeypatch.setattr(urllib.request, "urlopen", respond)
    assert server._embed_text("fixture text", model="captured", endpoint="http://fixture.invalid/") == [1.0, 2.5]
    assert json.loads(calls[0].data) == {"model": "captured", "prompt": "fixture text"}


@pytest.mark.parametrize("failure", [urllib.error.URLError("PRIVATE_TOKEN_MARKER"),
                                     http.client.InvalidURL("PRIVATE_TOKEN_MARKER"),
                                     OSError("PRIVATE_TOKEN_MARKER")])
def test_transport_errors_are_safe_unavailability(monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(urllib.request, "urlopen", fail)
    assert server._embed_text("fixture", endpoint="http://fixture.invalid/") is None


def test_endpoint_secret_not_persisted_or_returned_and_bad_endpoint_falls_back(snapshot, monkeypatch):
    rows, root = snapshot
    marker = "PRIVATE_TOKEN_MARKER"
    monkeypatch.setattr(server, "OLLAMA_EMBED_URL", "http://fixture.invalid/?token=" + marker)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b'{"embedding":[1,2]}'))
    result = server._tool_recommend({"problem_description": "perspective", "top_k": 2})
    assert result["method"] == "embedding-cosine-v0.2"
    assert marker not in json.dumps(result)
    assert marker not in repr(server._embedding_inputs(rows))
    for path in root.iterdir():
        assert marker not in path.name
        assert marker.encode() not in path.read_bytes()
    monkeypatch.setattr(server, "OLLAMA_EMBED_URL", marker)
    def forbidden(*args, **kwargs):
        raise AssertionError("Malformed URL should fail before transport")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    response = server.handle_request("tools/call", {"name": "basen_recommend", "arguments": {
        "problem_description": "perspective", "top_k": 2}})
    assert marker not in json.dumps(response)
    assert json.loads(response["content"][0]["text"])["method"] == "keyword-overlap-v0.1-fallback"


@pytest.mark.parametrize("query", [None, [], [0, 0], [1, 0, 0], [float("nan"), 1], [True, 1]])
def test_bad_query_vectors_produce_explicit_keyword_fallback(snapshot, monkeypatch, query):
    rows, root = snapshot
    cache_path(rows, root).write_text(json.dumps(cache_payload(rows)), encoding="utf-8")
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: query)
    result = server._tool_recommend({"problem_description": "perspective", "top_k": 2})
    assert result["method"] == "keyword-overlap-v0.1-fallback"


def test_valid_query_uses_all_selected_cached_operators(snapshot, monkeypatch):
    rows, root = snapshot
    cache_path(rows, root).write_text(json.dumps(cache_payload(rows)), encoding="utf-8")
    calls = []
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: calls.append(text) or [0, 1])
    result = server._recommend_via_embeddings("query", "base120", 2)
    assert calls == ["query"]
    assert [(row["operator_id"], row["score"]) for row in result["recommendations"]] == [("IN1", 1.0), ("P1", 0.0)]


@pytest.mark.parametrize("magnitude", [1.0, 1e308, 1e-308, 5e-324])
def test_stable_cosine_for_extreme_finite_nonzero_vectors(magnitude):
    vector = [magnitude, magnitude]
    assert server._cosine_similarity(vector, vector) == pytest.approx(1.0)
    assert server._cosine_similarity(vector, [-magnitude, -magnitude]) == pytest.approx(-1.0)
    assert server._cosine_similarity([magnitude, 0], [0, magnitude]) == pytest.approx(0.0)


@pytest.mark.parametrize("left,right", [([], []), ([0, 0], [1, 0]), ([1], [1, 2]),
                                        ([float("nan")], [1]), ([True], [1])])
def test_cosine_declines_invalid_vectors(left, right):
    assert server._cosine_similarity(left, right) is None


def test_nonfinite_similarity_cannot_be_labeled_embedding_success(snapshot, monkeypatch):
    rows, root = snapshot
    cache_path(rows, root).write_text(json.dumps(cache_payload(rows)), encoding="utf-8")
    monkeypatch.setattr(server, "_embed_text", lambda text, **kwargs: [1, 0])
    monkeypatch.setattr(server, "_cosine_similarity", lambda left, right: math.nan)
    assert server._tool_recommend({"problem_description": "perspective"})["method"] == "keyword-overlap-v0.1-fallback"
