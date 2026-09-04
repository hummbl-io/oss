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
        # Minimum size: 32B MAC + 16B IV + 16B Block (padded payload) = 64B
        assert len(envelope) >= 64

        decrypted = crypto.decrypt_envelope(envelope)
        assert decrypted == payload


def test_tamper_integrity_verification() -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    crypto = SovereignCryptosystem(enc_key, mac_key)

    payload = b"Top secret operational data."
    envelope = crypto.encrypt_envelope(payload)

    # Payload is too small
    with pytest.raises(ValueError, match="Envelope payload is too small"):
        crypto.decrypt_envelope(b"short")

    # Tamper with MAC signature (first 32 bytes)
    mutated_envelope_mac = bytearray(envelope)
    mutated_envelope_mac[0] ^= 1  # Flip one bit in MAC
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(bytes(mutated_envelope_mac))

    # Tamper with IV (next 16 bytes)
    mutated_envelope_iv = bytearray(envelope)
    mutated_envelope_iv[32] ^= 1  # Flip one bit in IV
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(bytes(mutated_envelope_iv))

    # Tamper with Ciphertext (remaining bytes)
    mutated_envelope_ct = bytearray(envelope)
    mutated_envelope_ct[-1] ^= 1  # Flip one bit in Ciphertext
    with pytest.raises(PermissionError, match="Integrity validation failed"):
        crypto.decrypt_envelope(bytes(mutated_envelope_ct))


def test_padding_validation_integrity(monkeypatch) -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)

    # Encrypt some dummy data to form a valid MAC signature envelope FIRST using real Popen
    real_crypto = SovereignCryptosystem(enc_key, mac_key)
    envelope = real_crypto.encrypt_envelope(b"dummy")

    # Force the openssl fallback path so subprocess mocking works.
    # When the cryptography library is available, decrypt_envelope uses
    # in-process AES and never calls subprocess.Popen.
    import hummbl_governance.sovereign_cryptosystem as sc_module
    monkeypatch.setattr(sc_module, "_HAS_CRYPTOGRAPHY", False)

    # We mock subprocess.Popen entirely to return a successful run
    # but with controlled decrypted output to trigger the manual padding checks.
    import subprocess

    class MockPopen:
        def __init__(self, args, stdin=None, stdout=None, stderr=None):
            self.returncode = 0
            self.output = b""

        def communicate(self, input=None):
            return self.output, b""

    mock_proc = MockPopen([])
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: mock_proc)

    crypto = SovereignCryptosystem(enc_key, mac_key)

    # Test bad padding length (> 16)
    mock_proc.output = b"A" * 15 + b"\x11"
    with pytest.raises(ValueError, match="Invalid padding length"):
        crypto.decrypt_envelope(envelope)

    # Test bad padding length (< 1)
    mock_proc.output = b"A" * 16 + b"\x00"
    with pytest.raises(ValueError, match="Invalid padding length"):
        crypto.decrypt_envelope(envelope)

    # Test bad padding sequence
    mock_proc.output = b"A" * 14 + b"\x03\x02"
    with pytest.raises(ValueError, match="Invalid padding sequence"):
        crypto.decrypt_envelope(envelope)
