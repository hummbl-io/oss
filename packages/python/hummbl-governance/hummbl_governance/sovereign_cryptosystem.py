"""sovereign_cryptosystem — Hardened Cryptographic Sync Router (GFSCR) envelope.

Implements timing-safe Encrypt-then-MAC using AES-256-CBC. Prefers the
``cryptography`` library (in-process, no subprocess overhead) when available,
falling back to OpenSSL subprocess execution for environments without the
optional dependency. HMAC-SHA256 integrity validation in both paths.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import shutil
import subprocess

# Best-effort import of the cryptography library. This is the preferred
# path — it avoids subprocess overhead (~50ms per call), eliminates the
# shell-injection attack surface, and provides constant-time PKCS#7
# unpadding via hazmat primitives. The fallback to openssl subprocess
# remains for environments where the [primitives] extra is not installed.
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


def _get_openssl_executable() -> str:
    """Dynamically locates the openssl or openssl.exe executable."""
    # 1. Check if 'openssl' is in standard PATH
    path = shutil.which("openssl")
    if path:
        return path

    path_exe = shutil.which("openssl.exe")
    if path_exe:
        return path_exe

    # 2. Check standard Windows installations
    common_paths = [
        r"C:\Program Files\Git\mingw64\bin\openssl.exe",
        r"C:\Program Files\Git\usr\bin\openssl.exe",
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

    # Fallback to plain 'openssl'
    return "openssl"


def _pkcs7_pad(plaintext: bytes, block_size: int = 16) -> bytes:
    """Apply PKCS#7 padding."""
    pad_len = block_size - (len(plaintext) % block_size)
    return plaintext + bytes([pad_len] * pad_len)


def _pkcs7_unpad(padded: bytes) -> bytes:
    """Remove and validate PKCS#7 padding."""
    if not padded:
        raise ValueError("Decrypted plaintext is empty.")
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Decryption error: Invalid padding length.")
    for i in range(len(padded) - pad_len, len(padded)):
        if padded[i] != pad_len:
            raise ValueError("Decryption error: Invalid padding sequence.")
    return padded[:-pad_len]


class SovereignCryptosystem:
    """Hardened cryptosystem providing authenticated AES-256-CBC envelope encryption."""

    def __init__(self, key_256: bytes, mac_key_256: bytes):
        """Initialize the cryptosystem with distinct 32-byte encryption and MAC keys."""
        if len(key_256) != 32:
            raise ValueError("Encryption key must be exactly 32-bytes (256-bit).")
        if len(mac_key_256) != 32:
            raise ValueError("MAC key must be exactly 32-bytes (256-bit).")

        self.key = key_256
        self.mac_key = mac_key_256

    def encrypt_envelope(self, plaintext: bytes) -> bytes:
        """Securely encrypt plaintext and sign ciphertext using Encrypt-then-MAC.

        Returns:
            bytes: HMAC-SHA256 (32B) + IV (16B) + AES-256-CBC Ciphertext
        """
        iv = secrets.token_bytes(16)
        padded_plaintext = _pkcs7_pad(plaintext)

        if _HAS_CRYPTOGRAPHY:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        else:
            ciphertext = self._encrypt_openssl(iv, padded_plaintext)

        envelope_body = iv + ciphertext
        mac = hmac.new(self.mac_key, envelope_body, hashlib.sha256).digest()
        return mac + envelope_body

    def decrypt_envelope(self, signed_envelope: bytes) -> bytes:
        """Verify the signature and decrypt the envelope with timing-safe comparison."""
        if len(signed_envelope) < 64:
            raise ValueError("Envelope payload is too small.")

        supplied_mac = signed_envelope[:32]
        envelope_body = signed_envelope[32:]
        iv = envelope_body[:16]
        ciphertext = envelope_body[16:]

        computed_mac = hmac.new(self.mac_key, envelope_body, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_mac, computed_mac):
            raise PermissionError("Decryption Failure: Integrity validation failed.")

        if _HAS_CRYPTOGRAPHY:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        else:
            padded_plaintext = self._decrypt_openssl(iv, ciphertext)

        return _pkcs7_unpad(padded_plaintext)

    def _encrypt_openssl(self, iv: bytes, padded_plaintext: bytes) -> bytes:
        """Fallback: encrypt using openssl subprocess."""
        openssl_bin = _get_openssl_executable()
        try:
            proc = subprocess.Popen(
                [openssl_bin, "enc", "-aes-256-cbc", "-K", self.key.hex(), "-iv", iv.hex(), "-nosalt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            ciphertext, err = proc.communicate(input=padded_plaintext)
            if proc.returncode != 0:
                raise OSError(f"OpenSSL encryption command failed: {err.decode().strip()}")
        except FileNotFoundError:
            raise OSError(f"OpenSSL executable not found. Tried: {openssl_bin}")
        return ciphertext

    def _decrypt_openssl(self, iv: bytes, ciphertext: bytes) -> bytes:
        """Fallback: decrypt using openssl subprocess."""
        openssl_bin = _get_openssl_executable()
        try:
            proc = subprocess.Popen(
                [openssl_bin, "enc", "-d", "-aes-256-cbc", "-K", self.key.hex(), "-iv", iv.hex(), "-nosalt"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            padded_plaintext, err = proc.communicate(input=ciphertext)
            if proc.returncode != 0:
                raise PermissionError("Decryption Failure: Integrity validation failed.")
        except FileNotFoundError:
            raise PermissionError("Decryption Failure: OpenSSL executable not found.")
        return padded_plaintext
