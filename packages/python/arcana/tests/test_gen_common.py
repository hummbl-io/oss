"""Tests for _gen_common.py shared library.

Run with: python -m pytest scripts/test_gen_common.py -v
Or:       python scripts/test_gen_common.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc


def _set_env(values: dict[str, str | None]):
    """Set environment values and return old values for restoration."""
    previous = {}
    for key, value in values.items():
        previous[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    return previous


def _restore_env(previous: dict[str, str | None]):
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_snake_case_ok():
    assert gc.snake_case_ok("ok")
    assert gc.snake_case_ok("also_ok")
    assert gc.snake_case_ok("id_123")
    assert not gc.snake_case_ok("BadCase")
    assert not gc.snake_case_ok("1leading_digit")
    assert not gc.snake_case_ok("has-dash")
    assert not gc.snake_case_ok("has space")
    assert not gc.snake_case_ok("")


def test_validate_required_string_fields_happy():
    ok, why = gc.validate_required_string_fields(
        {"a": "x", "b": "yy"}, ("a", "b"))
    assert ok
    assert why == ""


def test_validate_required_string_fields_missing():
    ok, why = gc.validate_required_string_fields(
        {"a": "x"}, ("a", "b"))
    assert not ok
    assert "b" in why


def test_validate_required_string_fields_empty():
    ok, why = gc.validate_required_string_fields(
        {"a": "x", "b": "   "}, ("a", "b"))
    assert not ok
    assert "empty" in why


def test_validate_required_string_fields_type_mismatch():
    ok, _why = gc.validate_required_string_fields(
        {"a": "x", "b": 42}, ("a", "b"))
    assert not ok


def test_validate_required_string_fields_min_len():
    ok, why = gc.validate_required_string_fields(
        {"title": "hi", "body": "short"},
        ("title", "body"),
        min_len={"body": 100})
    assert not ok
    assert "too short" in why

    ok, why = gc.validate_required_string_fields(
        {"title": "hi", "body": "x" * 200},
        ("title", "body"),
        min_len={"body": 100})
    assert ok


def test_dedup_preserve_order():
    assert gc.dedup_preserve_order([1, 2, 2, 3, 1, 4], lambda x: x) == [1, 2, 3, 4]
    assert gc.dedup_preserve_order([], lambda x: x) == []
    # Case-insensitive dedup by lowered string
    items = ["Hello", "hello", "World"]
    assert gc.dedup_preserve_order(items, lambda s: s.lower()) == ["Hello", "World"]


def test_load_endpoint_from_env():
    old = _set_env({
        gc.ENV_OLLAMA_URL: "http://127.0.0.1:11434",
        gc.ENV_OLLAMA_NAME: "env-local",
        gc.ENV_OLLAMA_MODEL: "llama3.1:8b",
        gc.ENV_OLLAMA_MAX_PARALLEL: "4",
    })
    try:
        ep = gc.load_endpoint()
        assert ep["name"] == "env-local"
        assert ep["url"] == "http://127.0.0.1:11434"
        assert ep["model"] == "llama3.1:8b"
        assert ep["max_parallel"] == 4
    finally:
        _restore_env(old)


def test_load_endpoint_from_env_invalid_max_parallel():
    old = _set_env({
        gc.ENV_OLLAMA_URL: "http://127.0.0.1:11434",
        gc.ENV_OLLAMA_MAX_PARALLEL: "bad",
    })
    try:
        try:
            gc.load_endpoint()
            assert False, "expected SystemExit"
        except SystemExit:
            pass
    finally:
        _restore_env(old)


def test_tsv_clean():
    assert gc._tsv_clean("hello\tworld") == "hello world"
    assert gc._tsv_clean("line1\nline2") == "line1 line2"
    assert gc._tsv_clean("carriage\rreturn") == "carriage return"
    assert gc._tsv_clean("clean") == "clean"


def test_tsv_log_writes_header_once(tmp_path):
    log_path = tmp_path / "test.tsv"
    log = gc.TsvLog(log_path, ["a", "b"])
    log.append([{"a": "1", "b": "2"}])
    log.append([{"a": "3", "b": "4"}])
    contents = log_path.read_text(encoding="utf-8")
    # Header appears exactly once
    assert contents.count("a\tb\n") == 1
    assert "1\t2" in contents
    assert "3\t4" in contents


def test_tsv_log_missing_columns_default_empty(tmp_path):
    log_path = tmp_path / "test.tsv"
    log = gc.TsvLog(log_path, ["a", "b", "c"])
    log.append([{"a": "1"}])  # b and c missing
    row = log_path.read_text(encoding="utf-8").splitlines()[1]
    assert row == "1\t\t"


def test_tsv_log_append_empty_rows_no_crash(tmp_path):
    log_path = tmp_path / "test.tsv"
    log = gc.TsvLog(log_path, ["a"])
    written = log.append([])
    assert written == 0
    assert not log_path.exists()


def test_now_utc_iso_format():
    ts = gc.now_utc_iso()
    # Loose format check: YYYY-MM-DDTHH:MM:SSZ
    assert len(ts) == 20
    assert ts.endswith("Z")
    assert ts[4] == "-" and ts[7] == "-" and ts[10] == "T"


def test_provenance_row_shape():
    row = gc.provenance_row(
        source="generator", theme="test theme", model="qwen3.5:9b",
        seed=42, prompt_version="test-v1")
    assert set(row.keys()) == {
        "timestamp_utc", "source", "theme", "model", "seed", "prompt_version"}
    assert row["seed"] == "42"
    assert row["theme"] == "test theme"


def test_provenance_row_none_seed():
    row = gc.provenance_row(
        source="manual", theme="", model="m", seed=None,
        prompt_version="v1")
    assert row["seed"] == ""


# --------------------- retry_until_full -------------------------------- #

def test_retry_stops_when_min_accepted_met():
    # attempt_fn returns 3 accepted on attempt 0, should stop
    calls = []
    def attempt(i):
        calls.append(i)
        return ([{"id": f"x{i}_{n}"} for n in range(3)], [])
    accepted, _rejected = gc.retry_until_full(
        attempt, min_accepted=2, max_retries=5, log_fn=lambda m: None)
    assert len(accepted) == 3
    assert len(calls) == 1  # single attempt was enough


def test_retry_keeps_going_until_min():
    # Each attempt produces 1 accepted; need 3
    def attempt(i):
        return ([{"id": f"x{i}"}], [({"id": "bad"}, "why")])
    accepted, rejected = gc.retry_until_full(
        attempt, min_accepted=3, max_retries=5, log_fn=lambda m: None)
    assert len(accepted) == 3
    # 3 attempts to accumulate 3 items
    assert len(rejected) == 3


def test_retry_exhausts_without_reaching_min():
    # Each attempt gives 0 accepted
    def attempt(i):
        return ([], [({"id": "x"}, "bad")])
    accepted, rejected = gc.retry_until_full(
        attempt, min_accepted=3, max_retries=2, log_fn=lambda m: None)
    assert accepted == []
    # 3 attempts total (1 initial + 2 retries)
    assert len(rejected) == 3


def test_retry_catches_exceptions():
    def attempt(i):
        raise RuntimeError("synthetic failure")
    accepted, rejected = gc.retry_until_full(
        attempt, min_accepted=1, max_retries=2, log_fn=lambda m: None)
    assert accepted == []
    assert len(rejected) == 3
    assert all("attempt_error" in r[1] for r in rejected)


def test_retry_min_zero_runs_once():
    calls = []
    def attempt(i):
        calls.append(i)
        return ([{"id": "x"}], [])
    _accepted, _rejected = gc.retry_until_full(
        attempt, min_accepted=0, max_retries=5, log_fn=lambda m: None)
    assert len(calls) == 1  # no retries when min_accepted=0


def test_ollama_result_ok_states():
    # Happy: parsed, no error
    r1 = gc.OllamaResult(parsed={"x": 1}, raw='{"x": 1}', elapsed_s=0.1,
                         prompt_tokens=10, completion_tokens=5,
                         model="m", endpoint_name="n")
    assert r1.ok()

    # Parse error
    r2 = gc.OllamaResult(parsed=None, raw="not json", elapsed_s=0.1,
                         prompt_tokens=10, completion_tokens=5,
                         model="m", endpoint_name="n",
                         parse_error="JSONDecodeError: x")
    assert not r2.ok()


# ---- run_brainstorm ---------------------------------------------------- #

def _fake_ollama(parsed_payload, parse_error=None):
    """Build a fake ollama_fn that always returns the given payload."""
    def _fn(endpoint, system, user, seed=None, think=False, timeout=600):
        return gc.OllamaResult(
            parsed=parsed_payload, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model=endpoint["model"], endpoint_name=endpoint["name"],
            parse_error=parse_error)
    return _fn


def _ep():
    return {"name": "fake", "model": "fake-model", "url": "http://x"}


def test_run_brainstorm_happy_single_attempt():
    fake = _fake_ollama({"items": [{"id": "a"}, {"id": "b"}]})
    accepted, rejected, last = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("sys", "user"),
        list_key="items",
        item_validator=lambda it: (True, ""),
        base_seed=0, self_review=False,
        ollama_fn=fake)
    assert len(accepted) == 2
    assert rejected == []
    assert last is not None and last.ok()


def test_run_brainstorm_validator_rejects():
    fake = _fake_ollama({"items": [{"id": "good"}, {"id": "bad"}]})
    def vld(it):
        return (True, "") if it["id"] == "good" else (False, "reason-x")
    accepted, rejected, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=vld,
        base_seed=None, self_review=False,
        ollama_fn=fake)
    assert [a["id"] for a in accepted] == ["good"]
    assert len(rejected) == 1 and rejected[0][1] == "reason-x"


def test_run_brainstorm_non_dict_items_rejected():
    fake = _fake_ollama({"items": [{"id": "ok"}, "not-a-dict", 42]})
    accepted, rejected, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=None, self_review=False,
        ollama_fn=fake)
    assert len(accepted) == 1
    assert len(rejected) == 2
    assert all(r[1] == "not a dict" for r in rejected)


def test_run_brainstorm_ollama_failure_short_circuits():
    fake = _fake_ollama(None, parse_error="JSONDecodeError: bad")
    accepted, rejected, last = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=0, self_review=False,
        ollama_fn=fake)
    assert accepted == []
    assert len(rejected) == 1
    assert rejected[0][1].startswith("ollama:")
    assert last is not None and not last.ok()


def test_run_brainstorm_wrong_list_type():
    fake = _fake_ollama({"items": "not a list"})
    accepted, rejected, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=0, self_review=False,
        ollama_fn=fake)
    assert accepted == []
    assert "not a items-list" in rejected[0][1]


def test_run_brainstorm_missing_key_treated_as_empty():
    fake = _fake_ollama({"other_key": [{"id": "x"}]})
    accepted, rejected, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=0, self_review=False,
        ollama_fn=fake)
    assert accepted == [] and rejected == []


def test_run_brainstorm_retry_until_min_met():
    # Each attempt yields one valid item with id matching attempt index.
    counter = {"n": 0}
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        counter["n"] += 1
        return gc.OllamaResult(
            parsed={"items": [{"id": f"a{counter['n']}"}]},
            raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    accepted, _rejected, _last = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=10, self_review=False,
        min_accepted=3, max_retries=5,
        ollama_fn=fake, log_fn=lambda m: None)
    # Should have stopped after 3 attempts (3 items accumulated).
    assert len(accepted) == 3
    assert counter["n"] == 3


def test_run_brainstorm_seed_bumped_per_attempt():
    seeds_seen = []
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        seeds_seen.append(seed)
        return gc.OllamaResult(
            parsed={"items": []}, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=100, self_review=False,
        min_accepted=1, max_retries=2,
        ollama_fn=fake, log_fn=lambda m: None)
    # 3 attempts (initial + 2 retries) with bumped seeds
    assert seeds_seen == [100, 101, 102]


def test_run_brainstorm_seed_none_passes_none():
    seeds_seen = []
    def fake(endpoint, system, user, seed=None, think=False, timeout=600):
        seeds_seen.append(seed)
        return gc.OllamaResult(
            parsed={"items": [{"id": "x"}]}, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=None, self_review=False,
        ollama_fn=fake)
    assert seeds_seen == [None]


def test_run_brainstorm_self_review_replaces_draft_when_ok():
    review_called = {"n": 0}
    def fake_ollama(*args, **kwargs):
        return gc.OllamaResult(
            parsed={"items": [{"id": "draft"}]}, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    def fake_review(endpoint, draft, schema, seed=None, timeout=600):
        review_called["n"] += 1
        return gc.OllamaResult(
            parsed={"items": [{"id": "polished"}]}, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    accepted, _, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=0, self_review=True, schema_hint="hint",
        ollama_fn=fake_ollama, self_review_fn=fake_review)
    assert review_called["n"] == 1
    assert [a["id"] for a in accepted] == ["polished"]


def test_run_brainstorm_self_review_fallback_when_review_fails():
    def fake_ollama(*args, **kwargs):
        return gc.OllamaResult(
            parsed={"items": [{"id": "draft"}]}, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n")
    def bad_review(endpoint, draft, schema, seed=None, timeout=600):
        return gc.OllamaResult(
            parsed=None, raw="", elapsed_s=0.0,
            prompt_tokens=0, completion_tokens=0,
            model="m", endpoint_name="n",
            parse_error="JSONDecodeError: garbage")
    accepted, _, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=lambda it: (True, ""),
        base_seed=0, self_review=True, schema_hint="hint",
        ollama_fn=fake_ollama, self_review_fn=bad_review)
    # Falls back to original draft
    assert [a["id"] for a in accepted] == ["draft"]


def test_run_brainstorm_validator_can_dedup_via_closure():
    fake = _fake_ollama({"items": [{"id": "a"}, {"id": "b"}, {"id": "a"}]})
    seen: set = set()
    def vld(it):
        if it["id"] in seen:
            return False, "duplicate"
        seen.add(it["id"])
        return True, ""
    accepted, rejected, _ = gc.run_brainstorm(
        endpoint=_ep(),
        build_prompt=lambda: ("s", "u"),
        list_key="items", item_validator=vld,
        base_seed=None, self_review=False,
        ollama_fn=fake)
    assert [a["id"] for a in accepted] == ["a", "b"]
    assert len(rejected) == 1 and rejected[0][1] == "duplicate"


def _run_standalone():
    """Fallback runner when pytest isn't available."""
    import inspect
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            sig = inspect.signature(fn)
            if "tmp_path" in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
