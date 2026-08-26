"""Tests for hummbl_validation.primitives."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from hummbl_validation.primitives import (
    require_non_negative,
    require_non_empty_str,
    require_type,
    read_jsonl,
    quarantine_corrupt_state,
)


class TestRequireNonNegative:
    def test_zero_passes(self):
        assert require_non_negative("x", 0) == 0

    def test_positive_passes(self):
        assert require_non_negative("x", 42) == 42

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="x must be non-negative"):
            require_non_negative("x", -1)

    def test_float_zero_passes(self):
        assert require_non_negative("x", 0.0) == 0.0

    def test_float_negative_raises(self):
        with pytest.raises(ValueError):
            require_non_negative("x", -0.01)


class TestRequireNonEmptyStr:
    def test_valid_string_passes(self):
        assert require_non_empty_str("name", "hello") == "hello"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            require_non_empty_str("name", "")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            require_non_empty_str("name", "   ")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            require_non_empty_str("name", 123)


class TestRequireType:
    def test_correct_type_passes(self):
        assert require_type("x", 42, int) == 42

    def test_wrong_type_raises(self):
        with pytest.raises(TypeError, match="x must be int"):
            require_type("x", "hello", int)

    def test_subclass_passes(self):
        class MyDict(dict):
            pass
        d = MyDict()
        assert require_type("x", d, dict) is d


class TestReadJsonl:
    def test_valid_jsonl(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
        result = read_jsonl(p)
        assert len(result) == 2
        assert result[0] == {"a": 1}
        assert result[1] == {"b": 2}

    def test_empty_lines_skipped(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
        result = read_jsonl(p)
        assert len(result) == 2

    def test_corrupt_line_raises(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\nNOT JSON\n{"b": 2}\n', encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupt JSON"):
            read_jsonl(p)

    def test_corrupt_line_skip(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\nNOT JSON\n{"b": 2}\n', encoding="utf-8")
        result = read_jsonl(p, on_error="skip")
        assert len(result) == 2
        assert result[0] == {"a": 1}
        assert result[1] == {"b": 2}

    def test_corrupt_line_error_dict(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\nNOT JSON\n{"b": 2}\n', encoding="utf-8")
        result = read_jsonl(p, on_error="error_dict")
        assert len(result) == 3
        assert result[0] == {"a": 1}
        assert "_error" in result[1]
        assert result[1]["_line"] == 2
        assert result[2] == {"b": 2}

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_jsonl(tmp_path / "nonexistent.jsonl")

    def test_non_dict_entry_raises(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\n[1, 2, 3]\n', encoding="utf-8")
        with pytest.raises(ValueError, match="Non-dict entry"):
            read_jsonl(p)

    def test_non_dict_entry_skip(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"a": 1}\n[1, 2, 3]\n', encoding="utf-8")
        result = read_jsonl(p, on_error="skip")
        assert len(result) == 1
        assert result[0] == {"a": 1}


class TestQuarantineCorruptState:
    def test_sidecar_created(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text('{"corrupt": true}', encoding="utf-8")
        sidecar = quarantine_corrupt_state(p)
        assert sidecar.exists()
        assert not p.exists()  # original moved
        assert ".corrupt." in sidecar.name

    def test_error_stock_logged(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text('{"corrupt": true}', encoding="utf-8")
        stock = tmp_path / "errors.jsonl"
        quarantine_corrupt_state(p, error_stock=stock)
        assert stock.exists()
        lines = stock.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "sha256" in entry
        assert "timestamp" in entry
        assert "file" in entry

    def test_alert_raises(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text('{"corrupt": true}', encoding="utf-8")
        with pytest.raises(RuntimeError, match="Corrupt state quarantined"):
            quarantine_corrupt_state(p, alert=True)

    def test_alert_still_quarantines(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text('{"corrupt": true}', encoding="utf-8")
        try:
            quarantine_corrupt_state(p, alert=True)
        except RuntimeError:
            pass
        # Sidecar should exist even though alert raised
        sidecars = list(tmp_path.glob("*.corrupt.*"))
        assert len(sidecars) == 1

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            quarantine_corrupt_state(tmp_path / "nonexistent.json")

    def test_hash_matches_content(self, tmp_path):
        content = b'{"corrupt": true}'
        p = tmp_path / "state.json"
        p.write_bytes(content)
        stock = tmp_path / "errors.jsonl"
        quarantine_corrupt_state(p, error_stock=stock)
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        entry = json.loads(stock.read_text(encoding="utf-8").strip())
        assert entry["sha256"] == expected
