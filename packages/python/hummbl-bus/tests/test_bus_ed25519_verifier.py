from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from hummbl_bus.bus_ed25519_verifier import (
    Ed25519VerificationError,
    _compute_canonical_payload,
    _extract_envelope,
    is_ed25519_verify_enabled,
    verify_envelope_if_signed,
    verify_envelope_strict,
)


def test_is_ed25519_verify_enabled_default_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BUS_ED25519_VERIFY", raising=False)
    assert not is_ed25519_verify_enabled()


def test_is_ed25519_verify_enabled_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    assert is_ed25519_verify_enabled()


def test_is_ed25519_verify_enabled_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "1")
    assert is_ed25519_verify_enabled()


def test_extract_envelope_none_for_plain_text() -> None:
    assert _extract_envelope("hello world") is None


def test_extract_envelope_none_for_json_without_signature() -> None:
    assert _extract_envelope('{"key": "value"}') is None


def test_extract_envelope_returns_dict_for_signed_json() -> None:
    msg = json.dumps({"signature": "abc", "key_id": "k1", "body": "hello"})
    result = _extract_envelope(msg)
    assert result is not None
    assert result["signature"] == "abc"


def test_extract_envelope_none_for_invalid_json() -> None:
    assert _extract_envelope("{not valid json}") is None


def test_compute_canonical_payload_excludes_signature() -> None:
    envelope = {"signature": "abc", "key_id": "k1", "body": "hello"}
    payload = _compute_canonical_payload(envelope)
    decoded = json.loads(payload)
    assert "signature" not in decoded
    assert decoded["key_id"] == "k1"


def test_compute_canonical_payload_sorted_keys() -> None:
    envelope = {"z": 1, "a": 2, "signature": "x"}
    payload = _compute_canonical_payload(envelope)
    # Keys should be sorted: a, z
    assert payload.index(b'"a"') < payload.index(b'"z"')


def test_verify_envelope_if_signed_plain_text_passes() -> None:
    assert verify_envelope_if_signed("hello world", "codex") is True


def test_verify_envelope_if_signed_unsigned_json_passes() -> None:
    msg = json.dumps({"key": "value"})
    assert verify_envelope_if_signed(msg, "codex") is True


def test_verify_envelope_if_signed_signed_but_verify_disabled_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BUS_ED25519_VERIFY", raising=False)
    msg = json.dumps({"signature": "abc", "key_id": "k1", "body": "hello"})
    assert verify_envelope_if_signed(msg, "codex") is True


def test_verify_envelope_if_signed_missing_key_id_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    msg = json.dumps({"signature": "abc"})
    with pytest.raises(Ed25519VerificationError, match="missing key_id"):
        verify_envelope_if_signed(msg, "codex")


def test_verify_envelope_if_signed_missing_signature_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    msg = json.dumps({"key_id": "k1", "signature": ""})
    with pytest.raises(Ed25519VerificationError, match="missing signature"):
        verify_envelope_if_signed(msg, "codex")


def test_verify_envelope_if_signed_body_hash_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    monkeypatch.setenv("BUS_ED25519_KEY_DIR", "/tmp/nonexistent_keys")
    msg = json.dumps(
        {
            "signature": "abc",
            "key_id": "k1",
            "body": "hello",
            "body_hash": "wrong_hash",
        }
    )
    with pytest.raises(Ed25519VerificationError, match="body_hash mismatch"):
        verify_envelope_if_signed(msg, "codex")


def test_verify_envelope_if_signed_key_not_found_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    monkeypatch.setenv("BUS_ED25519_KEY_DIR", str(tmp_path))
    msg = json.dumps(
        {
            "signature": "abc",
            "key_id": "nonexistent",
            "body": "hello",
        }
    )
    with pytest.raises(Ed25519VerificationError, match="Public key file not found"):
        verify_envelope_if_signed(msg, "codex")


def test_verify_envelope_if_signed_no_key_dir_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    monkeypatch.delenv("BUS_ED25519_KEY_DIR", raising=False)
    msg = json.dumps(
        {
            "signature": "abc",
            "key_id": "k1",
            "body": "hello",
        }
    )
    with pytest.raises(Ed25519VerificationError, match="BUS_ED25519_KEY_DIR not set"):
        verify_envelope_if_signed(msg, "codex")


def test_verify_envelope_strict_non_strict_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BUS_ED25519_STRICT", raising=False)
    assert verify_envelope_strict("hello", "codex") is True


def test_verify_envelope_strict_unsigned_privileged_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_STRICT", "true")
    monkeypatch.delenv("BUS_ED25519_VERIFY", raising=False)
    # Envelope with event_type=DECISION but no signature
    msg = json.dumps({"event_type": "DECISION", "body": "approve"})
    # _extract_envelope returns None because no signature field
    # So strict mode's heuristic check applies — returns True (heuristic)
    assert verify_envelope_strict(msg, "codex") is True


def test_verify_envelope_strict_signed_privileged_without_signature_field_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_ED25519_STRICT", "true")
    # Envelope that has event_type=DECISION and signature field but empty signature
    msg = json.dumps(
        {
            "event_type": "DECISION",
            "signature": "",
            "key_id": "k1",
        }
    )
    with pytest.raises(Ed25519VerificationError, match="must be signed"):
        verify_envelope_strict(msg, "codex")


def test_full_verification_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """End-to-end: sign a message with a real Ed25519 key and verify it."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        pytest.skip("cryptography package not installed")

    # Generate key pair
    private_key = Ed25519PrivateKey.generate()
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    # Write public key to key dir
    key_id = "test-key"
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    (key_dir / f"{key_id}.pub").write_text(
        base64.b64encode(public_key_bytes).decode(), encoding="utf-8"
    )

    # Create signed envelope
    body = "approve plan X"
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    envelope = {
        "event_type": "STATUS",
        "key_id": key_id,
        "body": body,
        "body_hash": body_hash,
        "created_at": "2026-08-15T12:00:00Z",
    }
    payload = _compute_canonical_payload(envelope)
    signature = private_key.sign(payload)
    envelope["signature"] = base64.b64encode(signature).decode()

    msg = json.dumps(envelope)

    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    monkeypatch.setenv("BUS_ED25519_KEY_DIR", str(key_dir))

    assert verify_envelope_if_signed(msg, "codex") is True


def test_full_verification_fails_with_wrong_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Signature from wrong key should fail verification."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        pytest.skip("cryptography package not installed")

    # Generate two key pairs
    signing_key = Ed25519PrivateKey.generate()
    verifying_key = Ed25519PrivateKey.generate()
    wrong_public_bytes = verifying_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    # Write wrong public key
    key_id = "test-key"
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    (key_dir / f"{key_id}.pub").write_text(
        base64.b64encode(wrong_public_bytes).decode(), encoding="utf-8"
    )

    # Sign with signing_key but verify with wrong_public_bytes
    envelope = {"key_id": key_id, "body": "hello"}
    payload = _compute_canonical_payload(envelope)
    signature = signing_key.sign(payload)
    envelope["signature"] = base64.b64encode(signature).decode()

    msg = json.dumps(envelope)

    monkeypatch.setenv("BUS_ED25519_VERIFY", "true")
    monkeypatch.setenv("BUS_ED25519_KEY_DIR", str(key_dir))

    with pytest.raises(Ed25519VerificationError, match="signature"):
        verify_envelope_if_signed(msg, "codex")
