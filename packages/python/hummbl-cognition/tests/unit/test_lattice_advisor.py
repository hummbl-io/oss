"""Bundled-registry failure behavior and healthy Base120 compatibility."""
from __future__ import annotations

import copy
import io
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_cognition import lattice_advisor as advisor_module

BUNDLE = advisor_module._REGISTRY_PATH.read_bytes()
ROWS = json.loads(BUNDLE)
SOURCE = Path(advisor_module.__file__).read_bytes()
SAFE_MESSAGE = "Bundled Base120 registry is unavailable; restore valid package data and restart."


def isolated_module(content):
    """Exercise module startup without mutating the imported package snapshot."""
    name = "_test_base120_advisor_snapshot"
    module = types.ModuleType(name)
    module.__file__ = advisor_module.__file__
    import builtins
    original_open = builtins.open

    def bundle_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path) == advisor_module._REGISTRY_PATH:
            if isinstance(content, Exception):
                raise content
            return io.StringIO(content.decode("utf-8"))
        return original_open(path, *args, **kwargs)

    with patch.dict(sys.modules, {name: module}), patch("builtins.open", side_effect=bundle_open):
        exec(compile(SOURCE, module.__file__, "exec"), module.__dict__)
    return module


def encoded(rows):
    return json.dumps(rows).encode("utf-8")


@pytest.mark.parametrize("content", [
    FileNotFoundError("PRIVATE_PATH_MARKER"), PermissionError("PRIVATE_PATH_MARKER"),
    b"{PRIVATE_PAYLOAD_MARKER", b"\xff", b"null", b"{}", b"[]", b"[null]",
    b"[" * 1500 + b"0" + b"]" * 1500,
    b"[" + b"9" * 5000 + b"]",
    b'[{"id":"P1","id":"P2"}]',
    b"[NaN]", b"[Infinity]", b"[1e9999]",
])
def test_bad_bundle_keeps_importable_module_without_placeholder_records(content):
    module = isolated_module(content)
    assert module.REGISTRY == {}
    assert module._REGISTRY_LOAD_FAILED is True
    with pytest.raises(module.RegistryUnavailableError, match="Bundled Base120") as caught:
        module.Base120Advisor()
    assert str(caught.value) == SAFE_MESSAGE
    assert "PRIVATE_" not in str(caught.value)


@pytest.mark.parametrize("change", [
    lambda rows: rows.pop(),
    lambda rows: rows.append(copy.deepcopy(rows[0])),
    lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
    lambda rows: rows.__setitem__(0, "not a record"),
    lambda rows: rows[0].update(id="P01"),
    lambda rows: rows[0].update(id=["P1"]),
    lambda rows: rows[0].update(domain="IN"),
    lambda rows: rows[0].update(domain=[]),
    lambda rows: rows[0].update(domain_name="Wrong family"),
    lambda rows: rows[0].pop("name"),
    lambda rows: rows[0].update(name=" "),
    lambda rows: rows[0].update(definition=12),
    lambda rows: rows[0].update(definition="\ud800"),
    lambda rows: rows[0].update(difficulty="unrated"),
    lambda rows: rows[0].update(keywords="keyword"),
    lambda rows: rows[0].update(keywords=[42]),
    lambda rows: rows[0].update(keywords=[" "]),
    lambda rows: rows[0].update(keywords=["\ud800"]),
])
def test_invalid_or_incomplete_records_do_not_publish_partial_registry(change):
    rows = copy.deepcopy(ROWS)
    change(rows)
    module = isolated_module(encoded(rows))
    assert module.REGISTRY == {}
    assert module._REGISTRY_LOAD_FAILED is True


def test_unavailable_constructor_and_reads_fail_before_ledger_or_argument_processing():
    module = isolated_module(FileNotFoundError("PRIVATE_PATH_MARKER"))
    instance = module.Base120Advisor.__new__(module.Base120Advisor)
    with patch.object(module.Base120Advisor, "_load_ledger_signals", side_effect=AssertionError("ledger read")), \
         patch("builtins.open", side_effect=AssertionError("file read")), \
         patch.object(Path, "exists", side_effect=AssertionError("path probe")):
        operations = [lambda: module.Base120Advisor(ledger_path="unused"),
                      lambda: instance.recommend(None), lambda: instance.explain(None),
                      instance.list_domains]
        for operation in operations:
            with pytest.raises(module.RegistryUnavailableError) as caught:
                operation()
            assert str(caught.value) == SAFE_MESSAGE


def test_restoring_file_does_not_silently_reload_failed_snapshot():
    module = isolated_module(FileNotFoundError("missing"))
    with patch("builtins.open", return_value=io.StringIO(BUNDLE.decode("utf-8"))) as opened:
        with pytest.raises(module.RegistryUnavailableError):
            module.Base120Advisor()
        opened.assert_not_called()
    assert module.REGISTRY == {}


def test_direct_loader_failure_has_safe_message_and_suppresses_parser_context():
    with patch.object(advisor_module, "_REGISTRY_PATH", Path("PRIVATE_PATH_MARKER")), \
         patch("builtins.open", side_effect=PermissionError("PRIVATE_PAYLOAD_MARKER")):
        with pytest.raises(advisor_module.RegistryUnavailableError) as caught:
            advisor_module._load_registry()
    assert str(caught.value) == SAFE_MESSAGE
    assert caught.value.__suppress_context__ is True


def test_healthy_bundle_preserves_order_and_source_fields():
    module = isolated_module(BUNDLE)
    assert module._REGISTRY_LOAD_FAILED is False
    assert list(module.REGISTRY) == [row["id"] for row in ROWS]
    for row in ROWS:
        loaded = module.REGISTRY[row["id"]]
        assert all(loaded[key] == value for key, value in row.items())
        assert loaded["keywords"] == module.DOMAIN_KEYWORDS[row["domain"]]
    domains = module.Base120Advisor().list_domains()
    assert [row["code"] for row in domains] == list(module.DOMAIN_NAMES)
    assert [row["model_count"] for row in domains] == [20] * 6


def test_optional_keywords_and_unknown_metadata_are_retained():
    rows = copy.deepcopy(ROWS)
    rows[0].update(keywords=["fixture keyword"], extra={"retained": True})
    rows[1]["keywords"] = []
    module = isolated_module(encoded(rows))
    assert module.REGISTRY["P1"]["keywords"] == ["fixture keyword"]
    assert module.REGISTRY["P1"]["extra"] == {"retained": True}
    assert module.REGISTRY["P2"]["keywords"] == []


def test_healthy_rankings_and_ledger_weighting_match_prechange_examples():
    module = isolated_module(BUNDLE)
    instance = module.Base120Advisor()
    instance._ledger_signals = {"P1": 2.0, "DE4": 1.0}
    instance._signals_loaded = True
    # Observed before the loader repair; bounded compatibility, not utility evidence.
    examples = {
        "root cause bug": [("DE4", 2.6), ("DE1", 2.4), ("DE10", 2.0)],
        "stakeholder frame": [("P1", 3.2), ("P6", 2.4), ("P10", 2.0)],
        "SY1 feedback loop": [("SY1", 5.0), ("RE1", 2.0), ("RE10", 2.0)],
        "zzzzzzzz": [("P1", 1.2), ("DE4", 0.6)],
    }
    with patch("builtins.open", side_effect=AssertionError("unexpected file read")):
        for query, expected in examples.items():
            assert [(row["id"], row["score"]) for row in instance.recommend(query, limit=3)] == expected
        assert instance.explain("p1")["ledger_usage"] == 2.0
        assert instance.explain("unknown") is None
        assert all(row["domain"] == "DE" for row in instance.recommend("root cause", domain="DE"))


def test_healthy_default_selection_and_filters_still_work():
    module = isolated_module(BUNDLE)
    instance = module.Base120Advisor()
    instance._signals_loaded = True
    assert [row["id"] for row in instance.recommend("zzzzzzzz", limit=20)] == ["CO1", "DE1", "IN1", "P1", "RE1", "SY1"]
    result = instance.recommend("root cause", difficulty="advanced", domain="DE", limit=2)
    assert len(result) == 2
    assert all(row["difficulty"] == "advanced" and row["domain"] == "DE" for row in result)


def test_registry_loading_and_guards_do_not_call_network_or_child_processes():
    with patch("socket.socket", side_effect=AssertionError("network")), \
         patch("subprocess.Popen", side_effect=AssertionError("process")):
        assert len(isolated_module(BUNDLE).REGISTRY) == 120
        module = isolated_module(OSError("unavailable"))
        with pytest.raises(module.RegistryUnavailableError):
            module.Base120Advisor()
