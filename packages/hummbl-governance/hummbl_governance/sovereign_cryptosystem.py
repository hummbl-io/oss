"""sovereign_cryptosystem — Hardened Cryptographic Sync Router (GFSCR) envelope.

Implements timing-safe Encrypt-then-MAC using AES-256-CBC via secure OpenSSL
subprocess execution (no shell shell-injection vulnerability) and HMAC-SHA256 integrity validation.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import shutil
import subprocess


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
        # Generate cryptographically secure random Initialization Vector (16 bytes)
        iv = secrets.token_bytes(16)

        # PKCS#7 Padding
        pad_len = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([pad_len] * pad_len)

        # Execute openssl enc securely without shell=True to block shell injection
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

        # Construct Envelope: IV (16B) + Ciphertext (Variable)
        envelope_body = iv + ciphertext

        # Generate HMAC-SHA256 signature over entire body (IV + Ciphertext)
        mac = hmac.new(self.mac_key, envelope_body, hashlib.sha256).digest()

        # Return composite envelope: HMAC + IV + Ciphertext
        return mac + envelope_body

    def decrypt_envelope(self, signed_envelope: bytes) -> bytes:
        """Verify the signature and decrypt the envelope with timing-safe comparison."""
        # Minimum envelope size: 32B MAC + 16B IV + 16B Ciphertext block = 64B
        if len(signed_envelope) < 64:
            raise ValueError("Envelope payload is too small.")

        # Extract components
        supplied_mac = signed_envelope[:32]
        envelope_body = signed_envelope[32:]
        iv = envelope_body[:16]
        ciphertext = envelope_body[16:]

        # Verify signature FIRST using timing-safe comparison to prevent padding oracle & signature leaks
        computed_mac = hmac.new(self.mac_key, envelope_body, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_mac, computed_mac):
            # Universal error message to prevent padding oracle side-channel info leaks
            raise PermissionError("Decryption Failure: Integrity validation failed.")

        # Decrypt ciphertext securely using openssl
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

        # Validate and strip PKCS#7 padding
        if not padded_plaintext:
            raise ValueError("Decrypted plaintext is empty.")

        pad_len = padded_plaintext[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("Decryption error: Invalid padding length.")

        # Verify padding integrity
        for i in range(len(padded_plaintext) - pad_len, len(padded_plaintext)):
            if padded_plaintext[i] != pad_len:
                raise ValueError("Decryption error: Invalid padding sequence.")

        return padded_plaintext[:-pad_len]
