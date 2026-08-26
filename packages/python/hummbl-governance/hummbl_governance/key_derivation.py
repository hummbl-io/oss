"""HKDF-SHA256 key derivation (RFC 5869) — stdlib only.

Provides a minimal, dependency-free HKDF implementation for deriving
per-package or per-function signing keys from a single master key.
This enables a key hierarchy without requiring the ``cryptography``
package.

Usage::

    from hummbl_governance.key_derivation import derive_key

    # Derive a 32-byte HMAC key for the bus from a master secret
    bus_key = derive_key(master_secret, info=b"hummbl-bus/signing")
    # Derive a separate key for the receipt engine
    receipt_key = derive_key(master_secret, info=b"hummbl-governance/receipts")

Reference: RFC 5869, NIST SP 800-108 (KDF in Counter Mode).
"""

from __future__ import annotations

import hashlib
import hmac

_HASH = hashlib.sha256
_HASH_LEN = 32  # SHA-256 output length in bytes


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """HKDF-Extract: derive a pseudo-random key (PRK) from input key material.

    Parameters
    ----------
    salt : bytes
        Salt value (use empty bytes if none; HMAC-SHA256 uses a
        zero-string of hash-length as the key when salt is empty).
    ikm : bytes
        Input key material (the master secret).

    Returns:
    -------
    bytes
        32-byte pseudo-random key (PRK).
    """
    if not salt:
        salt = b"\x00" * _HASH_LEN
    return hmac.new(salt, ikm, _HASH).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int = _HASH_LEN) -> bytes:
    """HKDF-Expand: expand a PRK into output key material of the requested length.

    Parameters
    ----------
    prk : bytes
        Pseudo-random key from ``hkdf_extract`` (must be 32 bytes for SHA-256).
    info : bytes
        Context/application-specific string (e.g. ``b"hummbl-bus/signing"``).
    length : int
        Number of bytes to produce (max 255 * 32 = 8160 for SHA-256).

    Returns:
    -------
    bytes
        ``length`` bytes of derived key material.
    """
    if length > 255 * _HASH_LEN:
        raise ValueError(
            f"Cannot expand to {length} bytes; max is {255 * _HASH_LEN} for SHA-256"
        )
    blocks: list[bytes] = []
    t = b""
    for i in range(1, (length + _HASH_LEN - 1) // _HASH_LEN + 1):
        t = hmac.new(prk, t + info + bytes([i]), _HASH).digest()
        blocks.append(t)
    return b"".join(blocks)[:length]


def derive_key(
    master_secret: bytes,
    info: bytes,
    salt: bytes = b"",
    length: int = _HASH_LEN,
) -> bytes:
    """Derive a key from a master secret using HKDF-SHA256.

    Convenience wrapper combining extract + expand. Use different ``info``
    strings to derive independent keys for different packages or functions
    from the same master secret.

    Parameters
    ----------
    master_secret : bytes
        The master key material (e.g. from ``HUMMBL_MASTER_KEY`` env var).
    info : bytes
        Context string identifying the derived key's purpose.
    salt : bytes
        Optional salt (default empty).
    length : int
        Desired output length in bytes (default 32 for HMAC-SHA256).

    Returns:
    -------
    bytes
        Derived key material.
    """
    prk = hkdf_extract(salt, master_secret)
    return hkdf_expand(prk, info, length)
