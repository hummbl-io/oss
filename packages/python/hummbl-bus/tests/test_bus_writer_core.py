from __future__ import annotations

import json
import re

import pytest

from hummbl_bus.bus_writer import (
    _redact_metadata,
    _validate_bridge_url,
    _validate_signed_envelope,
    generate_request_id,
)

# --- _redact_metadata ---


def test_redact_metadata_none_returns_none() -> None:
    assert _redact_metadata(None) is None


def test_redact_metadata_empty_returns_empty() -> None:
    assert _redact_metadata({}) == {}


def test_redact_metadata_redacts_bridge_url_credentials() -> None:
    result = _redact_metadata(
        {
            "bridge_url": "https://user:password@host.example.com/path"  # pragma: allowlist secret
        }
    )
    assert result is not None
    assert "password" not in str(result["bridge_url"])
    assert "<redacted>" in str(result["bridge_url"])


def test_redact_metadata_redacts_url_field() -> None:
    result = _redact_metadata(
        {"url": "https://user:secret@host.example.com/path"}  # pragma: allowlist secret
    )
    assert result is not None
    assert "secret" not in str(result["url"])


def test_redact_metadata_redacts_remote_url_field() -> None:
    result = _redact_metadata(
        {
            "remote_url": "https://user:secret@host.example.com/path"  # pragma: allowlist secret
        }
    )
    assert result is not None
    assert "secret" not in str(result["remote_url"])


def test_redact_metadata_redacts_secrets_in_other_fields() -> None:
    result = _redact_metadata({"message": "token=sk-abc123def456ghi789jkl012mno345"})
    assert result is not None
    assert "sk-abc123" not in str(result["message"])


def test_redact_metadata_preserves_non_string_values() -> None:
    result = _redact_metadata({"count": 42, "flag": True})
    assert result is not None
    assert result["count"] == 42
    assert result["flag"] is True


# --- _validate_bridge_url ---


def test_validate_bridge_url_https_any_host_passes() -> None:
    assert (
        _validate_bridge_url("https://example.com/path") == "https://example.com/path"
    )


def test_validate_bridge_url_http_localhost_passes() -> None:
    assert _validate_bridge_url("http://localhost:8080") == "http://localhost:8080"


def test_validate_bridge_url_http_127_passes() -> None:
    assert _validate_bridge_url("http://127.0.0.1:8080") == "http://127.0.0.1:8080"


def test_validate_bridge_url_http_tailscale_passes() -> None:
    assert (
        _validate_bridge_url("http://machine.ts.net:8080")
        == "http://machine.ts.net:8080"
    )


def test_validate_bridge_url_http_tailscale_ip_passes() -> None:
    assert _validate_bridge_url("http://100.64.0.1:8080") == "http://100.64.0.1:8080"


def test_validate_bridge_url_rejects_ftp_scheme() -> None:
    with pytest.raises(ValueError, match="SSRF confinement"):
        _validate_bridge_url("ftp://example.com")


def test_validate_bridge_url_rejects_no_hostname() -> None:
    with pytest.raises(ValueError, match="no hostname"):
        _validate_bridge_url("http://")


def test_validate_bridge_url_rejects_http_to_arbitrary_host() -> None:
    with pytest.raises(ValueError, match="SSRF confinement"):
        _validate_bridge_url("http://evil.com:8080")


def test_validate_bridge_url_allows_extra_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ALLOWED_BRIDGE_HOSTS", "my-bridge.local")
    assert (
        _validate_bridge_url("http://my-bridge.local:8080")
        == "http://my-bridge.local:8080"
    )


# --- generate_request_id ---


def test_generate_request_id_format() -> None:
    rid = generate_request_id("host-01", "codex")
    assert rid.startswith("host-01-codex-")
    # UUID hex is 32 chars
    suffix = rid.split("host-01-codex-")[1]
    assert len(suffix) == 32
    assert re.match(r"^[0-9a-f]{32}$", suffix)


def test_generate_request_id_sanitizes_special_chars() -> None:
    rid = generate_request_id("machine with spaces!", "sender/with/slashes")
    assert " " not in rid
    assert "/" not in rid
    assert "!" not in rid


def test_generate_request_id_unique() -> None:
    ids = {generate_request_id("host-01", "codex") for _ in range(100)}
    assert len(ids) == 100  # All unique


def test_generate_request_id_defaults_for_empty() -> None:
    rid = generate_request_id("", "")
    assert "unknown-origin" in rid
    assert "unknown-sender" in rid


# --- _validate_signed_envelope ---


def test_validate_signed_envelope_plain_text_passes() -> None:
    _validate_signed_envelope("hello world")  # No exception


def test_validate_signed_envelope_unsigned_json_passes() -> None:
    _validate_signed_envelope('{"key": "value"}')  # No exception


def test_validate_signed_envelope_valid_envelope_passes() -> None:
    envelope = json.dumps({"c": "content", "n": "0123456789abcdef", "s": "a" * 64})
    _validate_signed_envelope(envelope)  # No exception


def test_validate_signed_envelope_missing_fields_raises() -> None:
    envelope = json.dumps({"c": "content", "s": "a" * 64})
    with pytest.raises(ValueError, match="missing required fields"):
        _validate_signed_envelope(envelope)


def test_validate_signed_envelope_wrong_type_c_raises() -> None:
    envelope = json.dumps({"c": 123, "n": "0123456789abcdef", "s": "a" * 64})
    with pytest.raises(ValueError, match="'c'.*must be string"):
        _validate_signed_envelope(envelope)


def test_validate_signed_envelope_wrong_type_n_raises() -> None:
    envelope = json.dumps({"c": "content", "n": 123, "s": "a" * 64})
    with pytest.raises(ValueError, match="'n'.*must be string"):
        _validate_signed_envelope(envelope)


def test_validate_signed_envelope_wrong_type_s_raises() -> None:
    envelope = json.dumps({"c": "content", "n": "0123456789abcdef", "s": 123})
    with pytest.raises(ValueError, match="'s'.*must be string"):
        _validate_signed_envelope(envelope)


def test_validate_signed_envelope_short_nonce_raises() -> None:
    envelope = json.dumps({"c": "content", "n": "short", "s": "a" * 64})
    with pytest.raises(ValueError, match="nonce too short"):
        _validate_signed_envelope(envelope)


def test_validate_signed_envelope_invalid_json_passes() -> None:
    _validate_signed_envelope("{not valid json}")  # No exception


def test_validate_signed_envelope_non_dict_json_passes() -> None:
    _validate_signed_envelope("[1, 2, 3]")  # No exception
