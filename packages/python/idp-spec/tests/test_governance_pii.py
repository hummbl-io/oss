"""PII protection must complete before governance entries become persistent."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import pytest
from hummbl_cognition.ledger_writer import scrub_pii_from_dict

from idp_spec import governance_bus


@pytest.fixture(autouse=True)
def enable_idp(monkeypatch):
    monkeypatch.setenv("ENABLE_IDP", "true")
    monkeypatch.setenv("DCT_SECRET", "test-pii-governance-secret")


def append(bus, data):
    return bus.append("intent", "task", "SYSTEM", data, auto_sign=True)


def test_binds_real_cognition_scrubber():
    assert governance_bus._scrub_pii is scrub_pii_from_dict
    assert governance_bus._scrub_pii.__module__ == "hummbl_cognition.ledger_writer"


@pytest.mark.parametrize("enable_async", [False, True])
def test_pii_is_scrubbed_before_persistence_and_chain_hashing(tmp_path, enable_async):
    data = {
        "email": "alice@example.com",
        "nested": {"phone": "212-555-0199", "ssn": "123-45-6789"},
        "items": ["192.0.2.1", {"email": "bob@example.com"}],
        "count": 7,
    }
    original = copy.deepcopy(data)
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert append(bus, data) == (True, None)
        if enable_async:
            assert bus._buffer[0].tuple_data == scrub_pii_from_dict(data)
            assert not list(tmp_path.glob("*.jsonl"))
            assert bus._flush_buffer() == (True, None)
        first_line = bus._get_current_file().read_text(encoding="utf-8").strip()
        assert json.loads(first_line)["tuple_data"] == scrub_pii_from_dict(data)
        for value in ("alice@example.com", "212-555-0199", "123-45-6789", "192.0.2.1", "bob@example.com"):
            assert value not in first_line
        assert append(bus, {"state": "next"}) == (True, None)
        if enable_async:
            assert bus._flush_buffer() == (True, None)
        entries = [json.loads(line) for line in bus._get_current_file().read_text().splitlines()]
        assert entries[1]["previous_hash"] == bus.compute_entry_hash(first_line)
        assert bus.verify_chain() == (True, [])
    assert data == original


@pytest.mark.parametrize("enable_async", [False, True])
@pytest.mark.parametrize("failure", ["unavailable", "raises", "invalid_result"])
def test_failed_scrub_preserves_existing_log_and_buffer(
    tmp_path, monkeypatch, caplog, enable_async, failure
):
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert append(bus, {"safe": "existing entry"}) == (True, None)
        if enable_async:
            assert bus._flush_buffer() == (True, None)
            assert append(bus, {"safe": "pending entry"}) == (True, None)
        path = bus._get_current_file()
        before_bytes = path.read_bytes()
        before_buffer = copy.deepcopy(bus._buffer)

        def broken_scrubber(data):
            raise ValueError("sensitive input: alice@example.com")

        replacement = {
            "unavailable": None,
            "raises": broken_scrubber,
            "invalid_result": lambda data: None,
        }[failure]
        monkeypatch.setattr(governance_bus, "_scrub_pii", replacement)
        data = {"email": "alice@example.com"}
        with pytest.raises(RuntimeError) as caught:
            append(bus, data)
        assert path.read_bytes() == before_bytes
        assert bus._buffer == before_buffer
        assert bus.verify_chain() == (True, [])
        assert "alice@example.com" not in caplog.text
        assert "alice@example.com" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("failure", ["package_missing", "symbol_missing"])
def test_missing_dependency_at_import_cannot_create_log(tmp_path, failure):
    # Fresh interpreter exercises the real import fallback instead of only
    # monkeypatching an already-imported module's binding.
    script = r'''
import builtins
from pathlib import Path
import sys

real_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name.startswith("hummbl_cognition"):
        if sys.argv[2] == "package_missing":
            raise ModuleNotFoundError("No module named hummbl_cognition")
        raise ImportError("cannot import name scrub_pii_from_dict")
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked_import

from idp_spec import GovernanceBus, governance_bus
assert governance_bus._scrub_pii is None
with GovernanceBus(Path(sys.argv[1])) as bus:
    try:
        bus.append("i", "t", "SYSTEM", {"email": "alice@example.com"}, signature="test")
    except RuntimeError as exc:
        assert "install the cognition extra" in str(exc)
    else:
        raise AssertionError("missing scrubber must reject append")
    assert not bus._buffer
    assert not list(Path(sys.argv[1]).glob("*.jsonl"))
'''
    env = dict(os.environ, ENABLE_IDP="true")
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), failure],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "alice@example.com" not in result.stderr


def test_disabled_idp_does_not_write_even_without_scrubber(tmp_path, monkeypatch):
    monkeypatch.setenv("ENABLE_IDP", "false")
    monkeypatch.setattr(governance_bus, "_scrub_pii", None)
    with governance_bus.GovernanceBus(tmp_path) as bus:
        assert append(bus, {"email": "alice@example.com"}) == (True, None)
        assert not list(tmp_path.glob("*.jsonl"))
        assert not bus._buffer


@pytest.mark.parametrize("enable_async", [False, True])
def test_nested_arrays_are_scrubbed_and_detached_from_caller(tmp_path, enable_async):
    data = {"nested": [["alice@example.com", {"contact": ["bob@example.com"]}]]}
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert append(bus, data) == (True, None)
        expected = {
            "nested": [[
                scrub_pii_from_dict({"v": "alice@example.com"})["v"],
                {"contact": [scrub_pii_from_dict({"v": "bob@example.com"})["v"]]},
            ]]
        }
        # Neither changing an existing nested string nor appending a new one
        # after admission may insert unsanitized text into the async log.
        data["nested"][0][0] = "changed@example.com"
        data["nested"][0].append("injected@example.com")
        data["nested"][0][1]["contact"].append("late@example.com")
        if enable_async:
            assert bus._buffer[0].tuple_data == expected
            assert bus._flush_buffer() == (True, None)
        serialized = bus._get_current_file().read_text(encoding="utf-8")
        assert "@example.com" not in serialized
        assert json.loads(serialized)["tuple_data"] == expected


@pytest.mark.parametrize("enable_async", [False, True])
@pytest.mark.parametrize(
    "data", [{"alice@example.com": "value"}, {"nested": [[{"bob@example.com": "value"}]]}]
)
def test_pii_dictionary_keys_are_rejected_without_persistence(
    tmp_path, enable_async, data, caplog
):
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        with pytest.raises(RuntimeError, match="PII scrubbing failed") as caught:
            append(bus, data)
        assert not bus._buffer
        assert not list(tmp_path.glob("*.jsonl"))
        assert "@example.com" not in caplog.text
        assert "@example.com" not in "".join(traceback.format_exception(caught.value))
