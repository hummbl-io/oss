# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for HKDF-SHA256 key derivation (RFC 5869)."""

import hashlib
import hmac

from hummbl_governance.key_derivation import derive_key, hkdf_expand, hkdf_extract


class TestHkdf:
    MASTER = b"master-secret-do-not-use-in-production-32B!"

    def test_rfc5869_test_vector_1(self):
        """RFC 5869 Test Case 1: SHA-256 with known inputs."""
        ikm = b"\x0b" * 22
        salt = bytes(range(13))  # 0x00..0x0c
        info = bytes(range(0xf0, 0xfa))  # 0xf0..0xf9
        length = 42

        prk = hkdf_extract(salt, ikm)
        okm = hkdf_expand(prk, info, length)

        # Expected values from RFC 5869 Appendix A.1
        expected_prk = bytes.fromhex(
            "077709362c2e32df0ddc3f0dc47bba63"
            "90b6c73bb50f9c3122ec844ad7c2b3e5"
        )
        expected_okm = bytes.fromhex(
            "3cb25f25faacd57a90434f64d0362f2a"
            "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
            "34007208d5b887185865"
        )
        assert prk == expected_prk
        assert okm == expected_okm

    def test_different_info_yields_different_keys(self):
        """Keys derived with different info strings must be independent."""
        bus_key = derive_key(self.MASTER, info=b"hummbl-bus/signing")
        receipt_key = derive_key(self.MASTER, info=b"hummbl-governance/receipts")
        assert bus_key != receipt_key
        assert len(bus_key) == 32
        assert len(receipt_key) == 32

    def test_same_inputs_yield_same_key(self):
        """Deterministic: same inputs always produce the same key."""
        k1 = derive_key(self.MASTER, info=b"test/purpose")
        k2 = derive_key(self.MASTER, info=b"test/purpose")
        assert k1 == k2

    def test_empty_salt_uses_zero_string(self):
        """Empty salt should use zero-string of hash length (RFC 5869 §2.2)."""
        ikm = b"input-key-material"
        prk_empty = hkdf_extract(b"", ikm)
        prk_zeros = hkdf_extract(b"\x00" * 32, ikm)
        assert prk_empty == prk_zeros

    def test_rejects_too_long_output(self):
        """Expand must reject lengths exceeding 255 * hash_len."""
        import pytest
        with pytest.raises(ValueError, match="Cannot expand"):
            hkdf_expand(b"\x00" * 32, b"info", length=255 * 32 + 1)

    def test_derived_key_is_usable_for_hmac(self):
        """Derived key should work as an HMAC-SHA256 key."""
        key = derive_key(self.MASTER, info=b"test/hmac")
        msg = b"hello world"
        sig = hmac.new(key, msg, hashlib.sha256).hexdigest()
        assert len(sig) == 64  # 32 bytes hex-encoded
