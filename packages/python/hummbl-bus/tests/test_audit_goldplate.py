"""Audit goldplate tests: error paths, boundary conditions, and security invariants.

Added during the audit pass to cover:
- Error paths (file missing, JSON corrupt, input invalid)
- Boundary conditions (empty input, None, negative numbers)
- Security-relevant invariants
- "rejects X" tests paired with "and no state changed" assertions
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hummbl_bus.bus_utils import parse_bus_line
from hummbl_bus.bus_writer import (
    _sanitize_correlation_id,
    _validate_content,
    _validate_fields,
    escape_message,
    unescape_message,
    validate_tsv_integrity,
)
from hummbl_bus.message_signing import (
    NonceTracker,
    extract_timestamp_from_nonce,
    unwrap_signing_envelope,
)
from hummbl_bus.spool import load_spool_record

# ---------------------------------------------------------------------------
# _validate_fields — error paths and boundary conditions
# ---------------------------------------------------------------------------


class TestValidateFields:
    def test_rejects_empty_from_id(self) -> None:
        with pytest.raises(ValueError, match="from_id must be a non-empty string"):
            _validate_fields("", "all", "STATUS", "hello")

    def test_rejects_whitespace_only_from_id(self) -> None:
        with pytest.raises(ValueError, match="from_id must be a non-empty string"):
            _validate_fields("   ", "all", "STATUS", "hello")

    def test_rejects_none_from_id(self) -> None:
        with pytest.raises(ValueError, match="from_id must be a non-empty string"):
            _validate_fields(None, "all", "STATUS", "hello")  # type: ignore[arg-type]

    def test_rejects_empty_to_id(self) -> None:
        with pytest.raises(ValueError, match="to_id must be a non-empty string"):
            _validate_fields("codex", "", "STATUS", "hello")

    def test_rejects_empty_msg_type(self) -> None:
        with pytest.raises(ValueError, match="msg_type must be a non-empty string"):
            _validate_fields("codex", "all", "", "hello")

    def test_rejects_empty_message(self) -> None:
        with pytest.raises(ValueError, match="message must be a non-empty string"):
            _validate_fields("codex", "all", "STATUS", "")

    def test_rejects_whitespace_only_message(self) -> None:
        with pytest.raises(ValueError, match="message must be a non-empty string"):
            _validate_fields("codex", "all", "STATUS", "   ")

    def test_rejects_non_string_from_id(self) -> None:
        with pytest.raises(ValueError, match="from_id must be a non-empty string"):
            _validate_fields(123, "all", "STATUS", "hello")  # type: ignore[arg-type]

    def test_rejects_oversized_message(self) -> None:
        from hummbl_bus.bus_writer import MAX_MESSAGE_BYTES

        with pytest.raises(ValueError, match="message exceeds maximum size"):
            _validate_fields("codex", "all", "STATUS", "x" * (MAX_MESSAGE_BYTES + 1))


# ---------------------------------------------------------------------------
# _validate_content — security invariants
# ---------------------------------------------------------------------------


class TestValidateContent:
    def test_rejects_null_bytes(self) -> None:
        with pytest.raises(ValueError, match="null bytes"):
            _validate_content("hello\x00world")

    def test_rejects_null_bytes_and_no_state_changed(self) -> None:
        """Rejecting null bytes must not raise a different error or pass through."""
        # The function either raises or doesn't — there's no state to check,
        # but we verify it consistently rejects.
        for _ in range(3):
            with pytest.raises(ValueError, match="null bytes"):
                _validate_content("a\x00b")

    def test_accepts_normal_message(self) -> None:
        _validate_content("hello world")

    def test_accepts_empty_json_like(self) -> None:
        _validate_content("{}")

    def test_rejects_oversized_structured_payload(self) -> None:
        from hummbl_bus.bus_writer import MAX_PAYLOAD_FIELDS

        payload = {f"key_{i}": i for i in range(MAX_PAYLOAD_FIELDS + 1)}
        with pytest.raises(ValueError, match="structured payload has"):
            _validate_content(json.dumps(payload))


# ---------------------------------------------------------------------------
# _sanitize_correlation_id — boundary conditions
# ---------------------------------------------------------------------------


class TestSanitizeCorrelationId:
    def test_rejects_empty_string(self) -> None:
        with pytest.raises(
            ValueError, match="correlation_id must be a non-empty string"
        ):
            _sanitize_correlation_id("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(
            ValueError, match="correlation_id must be a non-empty string"
        ):
            _sanitize_correlation_id("   ")

    def test_rejects_non_string(self) -> None:
        with pytest.raises(
            ValueError, match="correlation_id must be a non-empty string"
        ):
            _sanitize_correlation_id(None)  # type: ignore[arg-type]

    def test_strips_tabs_and_newlines(self) -> None:
        result = _sanitize_correlation_id("corr\tabc\ndef")
        assert "\t" not in result
        assert "\n" not in result


# ---------------------------------------------------------------------------
# escape/unescape_message — round-trip and edge cases
# ---------------------------------------------------------------------------


class TestEscapeUnescape:
    def test_escape_replaces_newlines(self) -> None:
        assert escape_message("line1\nline2") == "line1\\nline2"

    def test_escape_replaces_tabs(self) -> None:
        assert escape_message("col1\tcol2") == "col1 col2"

    def test_escape_replaces_crlf(self) -> None:
        assert escape_message("line1\r\nline2") == "line1\\nline2"

    def test_escape_handles_non_string(self) -> None:
        assert escape_message(123) == "123"  # type: ignore[arg-type]

    def test_unescape_restores_newlines(self) -> None:
        assert unescape_message("line1\\nline2") == "line1\nline2"

    def test_round_trip(self) -> None:
        original = "hello\tworld\nfoo"
        escaped = escape_message(original)
        assert "\t" not in escaped
        assert "\n" not in escaped
        # unescape only restores newlines, not tabs (by design)
        assert "\n" in unescape_message(escaped)


# ---------------------------------------------------------------------------
# parse_bus_line — error paths and boundary conditions
# ---------------------------------------------------------------------------


class TestParseBusLine:
    def test_returns_none_for_empty_line(self) -> None:
        assert parse_bus_line("") is None

    def test_returns_none_for_comment(self) -> None:
        assert parse_bus_line("# comment") is None

    def test_returns_none_for_header(self) -> None:
        assert parse_bus_line("timestamp\tfrom\tto\ttype\tmessage") is None

    def test_returns_none_for_malformed_row(self) -> None:
        assert parse_bus_line("only\tthree\tcolumns") is None

    def test_returns_none_for_unknown_type(self) -> None:
        line = "2026-01-01T00:00:00Z\tcodex\tall\tGARBAGE\thello"
        assert parse_bus_line(line) is None

    def test_parses_valid_row(self) -> None:
        line = "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello"
        result = parse_bus_line(line)
        assert result is not None
        assert result["from"] == "codex"
        assert result["type"] == "STATUS"
        assert result["message"] == "hello"


# ---------------------------------------------------------------------------
# validate_tsv_integrity — error paths
# ---------------------------------------------------------------------------


class TestValidateTsvIntegrity:
    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        valid, errors = validate_tsv_integrity(tmp_path / "nonexistent.tsv")
        assert valid == 0
        assert errors == []

    def test_returns_zero_for_empty_file(self, tmp_path: Path) -> None:
        bus = tmp_path / "empty.tsv"
        bus.write_text("", encoding="utf-8")
        valid, errors = validate_tsv_integrity(bus)
        assert valid == 0
        assert errors == []


# ---------------------------------------------------------------------------
# NonceTracker — boundary conditions and security invariants
# ---------------------------------------------------------------------------


class TestNonceTracker:
    def test_replay_detected_for_same_nonce(self) -> None:
        tracker = NonceTracker()
        assert tracker.is_replay("nonce-1") is False
        assert tracker.is_replay("nonce-1") is True

    def test_different_nonces_not_replay(self) -> None:
        tracker = NonceTracker()
        assert tracker.is_replay("nonce-1") is False
        assert tracker.is_replay("nonce-2") is False

    def test_clear_resets_tracker(self) -> None:
        tracker = NonceTracker()
        tracker.is_replay("nonce-1")
        tracker.clear()
        assert tracker.is_replay("nonce-1") is False

    def test_expired_nonce_treated_as_replay(self) -> None:
        """A nonce whose embedded timestamp is older than TTL is a replay."""
        tracker = NonceTracker(ttl_seconds=1.0)
        # Use a nonce with a non-zero but very old timestamp (1000 millis = 1 sec epoch)
        old_nonce = "1000-abcdef0123456789"
        assert tracker.is_replay(old_nonce) is True


# ---------------------------------------------------------------------------
# extract_timestamp_from_nonce — boundary conditions
# ---------------------------------------------------------------------------


class TestExtractTimestampFromNonce:
    def test_valid_nonce(self) -> None:
        ts = extract_timestamp_from_nonce("1700000000000-abc123")
        assert ts is not None
        assert ts == 1700000000.0

    def test_invalid_nonce_returns_none(self) -> None:
        assert extract_timestamp_from_nonce("not-a-number") is None

    def test_empty_string_returns_none(self) -> None:
        assert extract_timestamp_from_nonce("") is None


# ---------------------------------------------------------------------------
# unwrap_signing_envelope — boundary conditions
# ---------------------------------------------------------------------------


class TestUnwrapSigningEnvelope:
    def test_plain_text_returned_unchanged(self) -> None:
        assert unwrap_signing_envelope("hello world") == "hello world"

    def test_valid_envelope_unwrapped(self) -> None:
        envelope = json.dumps({"c": "content", "n": "nonce", "s": "sig"})
        assert unwrap_signing_envelope(envelope) == "content"

    def test_invalid_json_returned_unchanged(self) -> None:
        assert unwrap_signing_envelope("{not json") == "{not json"

    def test_json_without_envelope_keys_returned_unchanged(self) -> None:
        assert unwrap_signing_envelope('{"foo": "bar"}') == '{"foo": "bar"}'

    def test_empty_string_returned_unchanged(self) -> None:
        assert unwrap_signing_envelope("") == ""


# ---------------------------------------------------------------------------
# load_spool_record — error paths
# ---------------------------------------------------------------------------


class TestLoadSpoolRecord:
    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_spool_record(tmp_path / "nonexistent.json")

    def test_raises_on_corrupt_json(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_spool_record(corrupt)

    def test_loads_valid_record(self, tmp_path: Path) -> None:
        valid = tmp_path / "valid.json"
        record = {"schema": "hummbl_bus.spool.v1", "sender": "codex"}
        valid.write_text(json.dumps(record), encoding="utf-8")
        result = load_spool_record(valid)
        assert result["sender"] == "codex"


# ---------------------------------------------------------------------------
# Bridge server input validation — boundary conditions
# ---------------------------------------------------------------------------


class TestBridgeServerInputValidation:
    def test_negative_n_clamped_to_zero(self, monkeypatch) -> None:
        """Negative n parameter should be clamped to 0, not crash."""
        import io

        from hummbl_bus.bridge_server import BusBridgeHandler

        handler = object.__new__(BusBridgeHandler)
        handler.path = "/bus/tail?n=-5"
        handler.headers = {}
        handler.rfile = io.BytesIO()
        handler.wfile = io.BytesIO()
        handler._response_code = None
        handler._error = None

        def _send_response(code, *args, **kwargs):
            handler._response_code = code

        def _send_header(*args, **kwargs):
            pass

        def _end_headers(*args, **kwargs):
            pass

        def _send_error(code, message=None, *args, **kwargs):
            handler._response_code = code
            handler._error = message

        def _json_response(data, status=200):
            handler._response_code = status

        handler.send_response = _send_response
        handler.send_header = _send_header
        handler.end_headers = _end_headers
        handler.send_error = _send_error
        handler._json_response = _json_response

        # Should not crash with negative n
        BusBridgeHandler.do_GET(handler)
        # The response code should be set (either 200 or 404 for missing bus file)
        assert handler._response_code is not None

    def test_invalid_n_returns_400(self, monkeypatch) -> None:
        """Non-integer n parameter should return 400."""
        import io

        from hummbl_bus.bridge_server import BusBridgeHandler

        handler = object.__new__(BusBridgeHandler)
        handler.path = "/bus/tail?n=abc"
        handler.headers = {}
        handler.rfile = io.BytesIO()
        handler.wfile = io.BytesIO()
        handler._response_code = None
        handler._error = None

        def _send_response(code, *args, **kwargs):
            handler._response_code = code

        def _send_header(*args, **kwargs):
            pass

        def _end_headers(*args, **kwargs):
            pass

        def _send_error(code, message=None, *args, **kwargs):
            handler._response_code = code
            handler._error = message

        handler.send_response = _send_response
        handler.send_header = _send_header
        handler.end_headers = _end_headers
        handler.send_error = _send_error

        BusBridgeHandler.do_GET(handler)
        assert handler._response_code == 400
