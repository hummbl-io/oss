from __future__ import annotations

import secrets

import pytest
from hummbl_governance.sovereign_cryptosystem import SovereignCryptosystem


def test_invalid_key_lengths() -> None:
    # Must be 32 bytes each
    with pytest.raises(ValueError, match="Encryption key must be exactly 32-bytes"):
        SovereignCryptosystem(secrets.token_bytes(16), secrets.token_bytes(32))

    with pytest.raises(ValueError, match="MAC key must be exactly 32-bytes"):
        SovereignCryptosystem(secrets.token_bytes(32), secrets.token_bytes(16))


def test_encrypt_decrypt_lifecycle() -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    crypto = SovereignCryptosystem(enc_key, mac_key)

    payloads = [
        b"hello world",
        b"",
        b"exact_block_size_16_bytes_long",
        b"A" * 100,
        b"\x00\xff\x7f\x80" * 10,
    ]

    for payload in payloads:
        envelope = crypto.encrypt_envelope(payload)
        # Minimum size: 12B nonce + 16B GCM tag = 28B
        assert len(envelope) >= 28

        decrypted = crypto.decrypt_envelope(envelope)
        assert decrypted == payload


def test_associated_data_roundtrip() -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    crypto = SovereignCryptosystem(enc_key, mac_key)

    payload = b"authenticated data"
    aad = b"context-label"
    envelope = crypto.encrypt_envelope(payload, aad)
    decrypted = crypto.decrypt_envelope(envelope, aad)
    assert decrypted == payload

    # Tamper with associated data
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(envelope, b"different-context")


def test_tamper_integrity_verification() -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    crypto = SovereignCryptosystem(enc_key, mac_key)

    payload = b"Top secret operational data."
    envelope = crypto.encrypt_envelope(payload)

    # Payload is too small
    with pytest.raises(ValueError, match="Envelope payload is too small"):
        crypto.decrypt_envelope(b"short")

    # Tamper with nonce (first 12 bytes)
    mutated_nonce = bytearray(envelope)
    mutated_nonce[0] ^= 1
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(bytes(mutated_nonce))

    # Tamper with ciphertext
    mutated_ciphertext = bytearray(envelope)
    mutated_ciphertext[-1] ^= 1
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(bytes(mutated_ciphertext))


def test_wrong_key_fails() -> None:
    crypto1 = SovereignCryptosystem(secrets.token_bytes(32), secrets.token_bytes(32))
    crypto2 = SovereignCryptosystem(secrets.token_bytes(32), secrets.token_bytes(32))

    envelope = crypto1.encrypt_envelope(b"secret")
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto2.decrypt_envelope(envelope)
