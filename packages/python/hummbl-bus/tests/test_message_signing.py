from __future__ import annotations

import math

from hummbl_bus.message_signing import (
    extract_timestamp_from_nonce,
    generate_secret,
    sign_payload,
    unwrap_signing_envelope,
    verify_signature,
)

SECRET = b"0123456789abcdef0123456789abcdef"


def test_generate_secret_is_32_bytes() -> None:
    assert len(generate_secret()) == 32


def test_sign_payload_is_deterministic() -> None:
    payload = {"beta": 2, "alpha": 1}

    signature_1 = sign_payload(
        SECRET,
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        payload,
        "nonce-123",
    )
    signature_2 = sign_payload(
        SECRET,
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        payload,
        "nonce-123",
    )

    assert signature_1 == signature_2
    assert verify_signature(
        SECRET,
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        payload,
        "nonce-123",
        signature_1,
    )


def test_verify_signature_detects_tampering() -> None:
    payload = {"message": "hello"}
    signature = sign_payload(
        SECRET,
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        payload,
        "nonce-123",
    )

    assert not verify_signature(
        SECRET,
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        {"message": "goodbye"},
        "nonce-123",
        signature,
    )


def test_unwrap_signing_envelope_returns_content() -> None:
    assert unwrap_signing_envelope('{"c":"hello","n":"nonce-123","s":"sig"}') == "hello"
    assert unwrap_signing_envelope("plain text") == "plain text"


def test_extract_timestamp_from_nonce() -> None:
    assert math.isclose(
        extract_timestamp_from_nonce("1718283257265-abcd"),
        1718283257.265,
    )
    assert extract_timestamp_from_nonce("invalid") is None
