from __future__ import annotations

import secrets
import pytest

from hummbl_governance.envelope_cryptosystem import EnvelopeCryptosystem


def test_invalid_key_lengths() -> None:
    # Must be 32 bytes each
    with pytest.raises(ValueError, match="Encryption key must be exactly 32-bytes"):
        EnvelopeCryptosystem(secrets.token_bytes(16), secrets.token_bytes(32))

    with pytest.raises(ValueError, match="MAC key must be exactly 32-bytes"):
        EnvelopeCryptosystem(secrets.token_bytes(32), secrets.token_bytes(16))


def test_encrypt_decrypt_lifecycle() -> None:
    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    crypto = EnvelopeCryptosystem(enc_key, mac_key)

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
    crypto = EnvelopeCryptosystem(enc_key, mac_key)

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

    real_crypto = EnvelopeCryptosystem(enc_key, mac_key)
    envelope = real_crypto.encrypt_envelope(b"dummy")

    import hummbl_governance.envelope_cryptosystem as sc_module
    monkeypatch.setattr(sc_module, "_HAS_CRYPTOGRAPHY", False)

    controlled_output = {"data": b""}
    monkeypatch.setattr(
        EnvelopeCryptosystem,
        "_decrypt_stdlib",
        lambda self, iv, ct: controlled_output["data"],
    )

    crypto = EnvelopeCryptosystem(enc_key, mac_key)

    # Test bad padding length (> 16)
    controlled_output["data"] = b"A" * 15 + b"\x11"
    with pytest.raises(ValueError, match="Invalid padding length"):
        crypto.decrypt_envelope(envelope)

    # Test bad padding length (< 1)
    controlled_output["data"] = b"A" * 16 + b"\x00"
    with pytest.raises(ValueError, match="Invalid padding length"):
        crypto.decrypt_envelope(envelope)

    # Test bad padding sequence
    controlled_output["data"] = b"A" * 14 + b"\x03\x02"
    with pytest.raises(ValueError, match="Invalid padding sequence"):
        crypto.decrypt_envelope(envelope)


def test_fips_197_appendix_c3_aes256_vector() -> None:
    """Verify pure-Python AES-256 block cipher against official NIST FIPS-197 C.3."""
    from hummbl_governance.envelope_cryptosystem import (
        _aes256_decrypt_block,
        _aes256_encrypt_block,
        _expand_key_256,
    )

    key = bytes.fromhex(
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    )
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    expected_ct = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")

    rkeys = _expand_key_256(key)
    ct = _aes256_encrypt_block(plaintext, rkeys)
    assert ct == expected_ct
    assert _aes256_decrypt_block(ct, rkeys) == plaintext


def test_stdlib_and_cryptography_backends_are_wire_compatible(monkeypatch) -> None:
    """Envelopes encrypted by one backend must decrypt cleanly under the other."""
    import hummbl_governance.envelope_cryptosystem as sc_module

    enc_key = secrets.token_bytes(32)
    mac_key = secrets.token_bytes(32)
    payloads = [b"", b"x", b"0123456789abcdef", b"0123456789abcdef0", b"B" * 137]

    # Always verify stdlib round-trip with _HAS_CRYPTOGRAPHY=False.
    monkeypatch.setattr(sc_module, "_HAS_CRYPTOGRAPHY", False)
    crypto = EnvelopeCryptosystem(enc_key, mac_key)
    stdlib_envelopes = [crypto.encrypt_envelope(p) for p in payloads]
    for p, env in zip(payloads, stdlib_envelopes):
        assert crypto.decrypt_envelope(env) == p

    # If optional cryptography is installed, verify full bidirectional interop.
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher  # noqa: F401
    except ImportError:
        return

    monkeypatch.setattr(sc_module, "_HAS_CRYPTOGRAPHY", True)
    for p, env in zip(payloads, stdlib_envelopes):
        assert crypto.decrypt_envelope(env) == p

    crypto_envelopes = [crypto.encrypt_envelope(p) for p in payloads]
    monkeypatch.setattr(sc_module, "_HAS_CRYPTOGRAPHY", False)
    for p, env in zip(payloads, crypto_envelopes):
        assert crypto.decrypt_envelope(env) == p
