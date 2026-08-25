"""sovereign_cryptosystem — Authenticated envelope encryption using AES-256-GCM.

Uses the `cryptography` library's AESGCM AEAD primitive, which provides both
confidentiality and integrity without manual padding or HMAC composition. The
constructor accepts two 32-byte keys and combines them into a single AES-256
key via SHA-256 for backward compatibility with the original key separation.
"""

from __future__ import annotations

import hashlib
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SovereignCryptosystem:
    """Authenticated envelope encryption using AES-256-GCM."""

    NONCE_SIZE = 12
    MINIMUM_ENVELOPE_SIZE = 28  # 12B nonce + 16B GCM tag

    def __init__(self, key_256: bytes, mac_key_256: bytes):
        """Initialize the cryptosystem with distinct 32-byte encryption and MAC keys.

        The two supplied keys are combined into a single 32-byte AES-256 key via
        SHA-256. This preserves the original dual-key API while using one
        authenticated cipher.
        """
        if len(key_256) != 32:
            raise ValueError("Encryption key must be exactly 32-bytes (256-bit).")
        if len(mac_key_256) != 32:
            raise ValueError("MAC key must be exactly 32-bytes (256-bit).")

        # Combine the two independent 32-byte keys into a single AES-256 key.
        combined_key = hashlib.sha256(key_256 + mac_key_256).digest()
        self._cipher = AESGCM(combined_key)

    def encrypt_envelope(self, plaintext: bytes, associated_data: bytes = b"") -> bytes:
        """Encrypt plaintext and authenticate the result.

        Returns:
            bytes: nonce (12B) + ciphertext + GCM tag
        """
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        ciphertext = self._cipher.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext

    def decrypt_envelope(self, signed_envelope: bytes, associated_data: bytes = b"") -> bytes:
        """Verify the GCM tag and decrypt the envelope.

        Raises:
            PermissionError: If authentication fails or the envelope is invalid.
            ValueError: If the envelope is too small.
        """
        if len(signed_envelope) < self.MINIMUM_ENVELOPE_SIZE:
            raise ValueError("Envelope payload is too small.")

        nonce = signed_envelope[:self.NONCE_SIZE]
        ciphertext = signed_envelope[self.NONCE_SIZE:]

        try:
            return self._cipher.decrypt(nonce, ciphertext, associated_data)
        except Exception as exc:
            # Universal error message to prevent side-channel information leaks.
            raise PermissionError("Decryption Failure: Integrity validation failed.") from exc
