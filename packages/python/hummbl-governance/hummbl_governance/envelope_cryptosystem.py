"""envelope_cryptosystem — Hardened Cryptographic Sync Router (GFSCR) envelope.

Implements timing-safe Encrypt-then-MAC using AES-256-CBC + HMAC-SHA256.
Prefers the optional ``cryptography`` library when installed and falls back to
an in-process, stdlib-only FIPS-197 AES-256-CBC implementation so raw key
material is never transported via subprocess command-line arguments (closes
hummbl-io/oss#517 Finding 7).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

# Best-effort import of the optional cryptography library (preferred for C-level
# performance and hardware AES-NI acceleration). When absent, the in-process
# pure-Python AES-256-CBC implementation provides identical wire compatibility
# with zero third-party dependencies and zero subprocess key exposure.
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


# ---------------------------------------------------------------------------
# Pure-Python FIPS-197 AES-256-CBC fallback (zero subprocesses, stdlib-only)
# ---------------------------------------------------------------------------

_SBOX: tuple[int, ...] = (
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
)

_INV_SBOX: tuple[int, ...] = tuple(
    _SBOX.index(i) for i in range(256)
)

_RCON: tuple[int, ...] = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40)


def _xtime(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if (a & 0x80) else (a << 1)


def _gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        a = _xtime(a)
        b >>= 1
    return p


# Precomputed GF(2^8) multiplication tables for MixColumns / InvMixColumns.
_MUL2 = tuple(_gmul(i, 2) for i in range(256))
_MUL3 = tuple(_gmul(i, 3) for i in range(256))
_MUL9 = tuple(_gmul(i, 9) for i in range(256))
_MUL11 = tuple(_gmul(i, 11) for i in range(256))
_MUL13 = tuple(_gmul(i, 13) for i in range(256))
_MUL14 = tuple(_gmul(i, 14) for i in range(256))


def _expand_key_256(key: bytes) -> list[bytes]:
    """Expand a 32-byte AES-256 key into 15 16-byte round keys (FIPS-197 §5.2)."""
    words: list[list[int]] = [list(key[i:i + 4]) for i in range(0, 32, 4)]
    rcon_idx = 0
    for i in range(8, 60):
        temp = list(words[i - 1])
        if i % 8 == 0:
            temp = [_SBOX[temp[1]] ^ _RCON[rcon_idx], _SBOX[temp[2]], _SBOX[temp[3]], _SBOX[temp[0]]]
            rcon_idx += 1
        elif i % 8 == 4:
            temp = [_SBOX[b] for b in temp]
        prev = words[i - 8]
        words.append([prev[j] ^ temp[j] for j in range(4)])
    return [
        bytes(words[r * 4] + words[r * 4 + 1] + words[r * 4 + 2] + words[r * 4 + 3])
        for r in range(15)
    ]


def _aes256_encrypt_block(block: bytes, round_keys: list[bytes]) -> bytes:
    """Encrypt a single 16-byte block under AES-256 (14 rounds, FIPS-197 §5.1)."""
    s = [block[i] ^ round_keys[0][i] for i in range(16)]
    for r in range(1, 14):
        # SubBytes + ShiftRows
        s = [
            _SBOX[s[0]], _SBOX[s[5]], _SBOX[s[10]], _SBOX[s[15]],
            _SBOX[s[4]], _SBOX[s[9]], _SBOX[s[14]], _SBOX[s[3]],
            _SBOX[s[8]], _SBOX[s[13]], _SBOX[s[2]], _SBOX[s[7]],
            _SBOX[s[12]], _SBOX[s[1]], _SBOX[s[6]], _SBOX[s[11]],
        ]
        # MixColumns + AddRoundKey
        rk = round_keys[r]
        out = [0] * 16
        for c in range(0, 16, 4):
            a0, a1, a2, a3 = s[c], s[c + 1], s[c + 2], s[c + 3]
            out[c] = (_MUL2[a0] ^ _MUL3[a1] ^ a2 ^ a3) ^ rk[c]
            out[c + 1] = (a0 ^ _MUL2[a1] ^ _MUL3[a2] ^ a3) ^ rk[c + 1]
            out[c + 2] = (a0 ^ a1 ^ _MUL2[a2] ^ _MUL3[a3]) ^ rk[c + 2]
            out[c + 3] = (_MUL3[a0] ^ a1 ^ a2 ^ _MUL2[a3]) ^ rk[c + 3]
        s = out
    # Final round (SubBytes + ShiftRows + AddRoundKey, no MixColumns)
    rk = round_keys[14]
    return bytes([
        _SBOX[s[0]] ^ rk[0], _SBOX[s[5]] ^ rk[1], _SBOX[s[10]] ^ rk[2], _SBOX[s[15]] ^ rk[3],
        _SBOX[s[4]] ^ rk[4], _SBOX[s[9]] ^ rk[5], _SBOX[s[14]] ^ rk[6], _SBOX[s[3]] ^ rk[7],
        _SBOX[s[8]] ^ rk[8], _SBOX[s[13]] ^ rk[9], _SBOX[s[2]] ^ rk[10], _SBOX[s[7]] ^ rk[11],
        _SBOX[s[12]] ^ rk[12], _SBOX[s[1]] ^ rk[13], _SBOX[s[6]] ^ rk[14], _SBOX[s[11]] ^ rk[15],
    ])


def _aes256_decrypt_block(block: bytes, round_keys: list[bytes]) -> bytes:
    """Decrypt a single 16-byte block under AES-256 (14 rounds, FIPS-197 §5.3)."""
    s = [block[i] ^ round_keys[14][i] for i in range(16)]
    for r in range(13, 0, -1):
        # InvShiftRows + InvSubBytes
        s = [
            _INV_SBOX[s[0]], _INV_SBOX[s[13]], _INV_SBOX[s[10]], _INV_SBOX[s[7]],
            _INV_SBOX[s[4]], _INV_SBOX[s[1]], _INV_SBOX[s[14]], _INV_SBOX[s[11]],
            _INV_SBOX[s[8]], _INV_SBOX[s[5]], _INV_SBOX[s[2]], _INV_SBOX[s[15]],
            _INV_SBOX[s[12]], _INV_SBOX[s[9]], _INV_SBOX[s[6]], _INV_SBOX[s[3]],
        ]
        # AddRoundKey
        rk = round_keys[r]
        s = [s[i] ^ rk[i] for i in range(16)]
        # InvMixColumns
        out = [0] * 16
        for c in range(0, 16, 4):
            a0, a1, a2, a3 = s[c], s[c + 1], s[c + 2], s[c + 3]
            out[c] = _MUL14[a0] ^ _MUL11[a1] ^ _MUL13[a2] ^ _MUL9[a3]
            out[c + 1] = _MUL9[a0] ^ _MUL14[a1] ^ _MUL11[a2] ^ _MUL13[a3]
            out[c + 2] = _MUL13[a0] ^ _MUL9[a1] ^ _MUL14[a2] ^ _MUL11[a3]
            out[c + 3] = _MUL11[a0] ^ _MUL13[a1] ^ _MUL9[a2] ^ _MUL14[a3]
        s = out
    # Final round (InvShiftRows + InvSubBytes + AddRoundKey)
    rk = round_keys[0]
    return bytes([
        _INV_SBOX[s[0]] ^ rk[0], _INV_SBOX[s[13]] ^ rk[1], _INV_SBOX[s[10]] ^ rk[2], _INV_SBOX[s[7]] ^ rk[3],
        _INV_SBOX[s[4]] ^ rk[4], _INV_SBOX[s[1]] ^ rk[5], _INV_SBOX[s[14]] ^ rk[6], _INV_SBOX[s[11]] ^ rk[7],
        _INV_SBOX[s[8]] ^ rk[8], _INV_SBOX[s[5]] ^ rk[9], _INV_SBOX[s[2]] ^ rk[10], _INV_SBOX[s[15]] ^ rk[11],
        _INV_SBOX[s[12]] ^ rk[12], _INV_SBOX[s[9]] ^ rk[13], _INV_SBOX[s[6]] ^ rk[14], _INV_SBOX[s[3]] ^ rk[15],
    ])


def _aes256_cbc_encrypt(key: bytes, iv: bytes, padded_plaintext: bytes) -> bytes:
    """Encrypt block-aligned plaintext with AES-256-CBC in pure Python."""
    if len(padded_plaintext) == 0 or len(padded_plaintext) % 16 != 0:
        raise ValueError("Plaintext must be non-empty and a multiple of 16 bytes.")
    round_keys = _expand_key_256(key)
    out = bytearray()
    prev = iv
    for offset in range(0, len(padded_plaintext), 16):
        block = padded_plaintext[offset:offset + 16]
        xored = bytes(block[i] ^ prev[i] for i in range(16))
        ct_block = _aes256_encrypt_block(xored, round_keys)
        out.extend(ct_block)
        prev = ct_block
    return bytes(out)


def _aes256_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """Decrypt block-aligned ciphertext with AES-256-CBC in pure Python."""
    if len(ciphertext) == 0 or len(ciphertext) % 16 != 0:
        raise ValueError("Ciphertext must be non-empty and a multiple of 16 bytes.")
    round_keys = _expand_key_256(key)
    out = bytearray()
    prev = iv
    for offset in range(0, len(ciphertext), 16):
        ct_block = ciphertext[offset:offset + 16]
        dec_block = _aes256_decrypt_block(ct_block, round_keys)
        out.extend(dec_block[i] ^ prev[i] for i in range(16))
        prev = ct_block
    return bytes(out)


def _pkcs7_pad(plaintext: bytes, block_size: int = 16) -> bytes:
    """Apply PKCS#7 padding."""
    pad_len = block_size - (len(plaintext) % block_size)
    return plaintext + bytes([pad_len] * pad_len)


def _pkcs7_unpad(padded: bytes) -> bytes:
    """Remove and validate PKCS#7 padding."""
    if not padded:
        raise ValueError("Decrypted plaintext is empty.")
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16 or pad_len > len(padded):
        raise ValueError("Decryption error: Invalid padding length.")
    expected = bytes([pad_len] * pad_len)
    if not hmac.compare_digest(padded[-pad_len:], expected):
        raise ValueError("Decryption error: Invalid padding sequence.")
    return padded[:-pad_len]


class EnvelopeCryptosystem:
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
            ciphertext = self._encrypt_stdlib(iv, padded_plaintext)

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
            padded_plaintext = self._decrypt_stdlib(iv, ciphertext)

        return _pkcs7_unpad(padded_plaintext)

    def _encrypt_stdlib(self, iv: bytes, padded_plaintext: bytes) -> bytes:
        """In-process stdlib fallback: AES-256-CBC with zero subprocess execution."""
        return _aes256_cbc_encrypt(self.key, iv, padded_plaintext)

    def _decrypt_stdlib(self, iv: bytes, ciphertext: bytes) -> bytes:
        """In-process stdlib fallback: AES-256-CBC with zero subprocess execution."""
        return _aes256_cbc_decrypt(self.key, iv, ciphertext)
