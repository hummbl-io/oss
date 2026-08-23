# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Tests for ReceiptEngine HMAC key management — issue #259.

Covers: env-var injection, file-based migration, fail-closed on
inability to persist, cross-platform file protection, and key rotation.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_governance.kernel import ReceiptEngine


ENV_VAR = "RECEIPTENGINE_HMAC_KEY"
FALLBACK_ENV_VAR = "HUMMBL_SIGNING_SECRET"


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove HMAC-related env vars for a clean test slate."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.delenv(FALLBACK_ENV_VAR, raising=False)


class TestEnvVarKeyInjection:
    """Primary path: caller-injected keys via environment variable."""

    def test_env_var_used_when_set(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "my-secret-key-from-env")
            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == b"my-secret-key-from-env"

    def test_env_var_not_persisted_to_file(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "env-only-key")
            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == b"env-only-key"
            secret_path = Path(tmpdir) / ".kernel_secret"
            assert not secret_path.exists()

    def test_fallback_env_var_used(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(FALLBACK_ENV_VAR, "fallback-key")
            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == b"fallback-key"

    def test_primary_env_var_takes_precedence_over_fallback(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "primary")
            monkeypatch.setenv(FALLBACK_ENV_VAR, "fallback")
            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == b"primary"

    def test_explicit_secret_param_takes_precedence_over_env(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "from-env")
            engine = ReceiptEngine(Path(tmpdir), signing_secret=b"explicit-param")
            assert engine.signing_secret == b"explicit-param"

    def test_receipts_signed_with_env_var_key(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "signing-key")
            engine = ReceiptEngine(Path(tmpdir))
            receipt = engine.create(agent_id="agent", action_type="ACT")
            assert engine.validate(receipt) is True


class TestFileBasedMigration:
    """Existing .kernel_secret files remain valid (backward compat)."""

    def test_existing_secret_file_loaded(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_path = Path(tmpdir) / ".kernel_secret"
            pre_existing = b"\x00\x01\x02" * 10  # 30 bytes, non-random
            secret_path.write_bytes(pre_existing)

            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == pre_existing

    def test_existing_secret_file_not_overwritten(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_path = Path(tmpdir) / ".kernel_secret"
            original = b"original-key-value"
            secret_path.write_bytes(original)

            engine = ReceiptEngine(Path(tmpdir))
            assert engine.signing_secret == original
            # File content unchanged
            assert secret_path.read_bytes() == original

    def test_new_secret_generated_and_persisted(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_path = Path(tmpdir) / ".kernel_secret"
            assert not secret_path.exists()

            engine = ReceiptEngine(Path(tmpdir))
            assert secret_path.exists()
            assert secret_path.read_bytes() == engine.signing_secret
            assert len(engine.signing_secret) == 32

    def test_persisted_secret_survives_restart(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine1 = ReceiptEngine(Path(tmpdir))
            key1 = engine1.signing_secret

            engine2 = ReceiptEngine(Path(tmpdir))
            assert engine2.signing_secret == key1


class TestFailClosed:
    """Fail-closed: refuse to sign if persistence unavailable and no env var."""

    def test_fail_closed_on_write_failure(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.write_bytes", side_effect=OSError("permission denied")):
                with pytest.raises(RuntimeError, match="RECEIPTENGINE_HMAC_KEY"):
                    ReceiptEngine(Path(tmpdir))

    def test_fail_closed_message_mentions_env_var(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.write_bytes", side_effect=OSError("permission denied")):
                with pytest.raises(RuntimeError) as exc_info:
                    ReceiptEngine(Path(tmpdir))
                msg = str(exc_info.value)
                assert "RECEIPTENGINE_HMAC_KEY" in msg

    def test_env_var_bypasses_fail_closed(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.write_bytes", side_effect=OSError("permission denied")):
                monkeypatch.setenv(ENV_VAR, "env-key-bypass")
                engine = ReceiptEngine(Path(tmpdir))
                assert engine.signing_secret == b"env-key-bypass"

    def test_existing_file_bypasses_fail_closed(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_path = Path(tmpdir) / ".kernel_secret"
            secret_path.write_bytes(b"pre-existing-key")

            with patch("pathlib.Path.write_bytes", side_effect=OSError("permission denied")):
                engine = ReceiptEngine(Path(tmpdir))
                assert engine.signing_secret == b"pre-existing-key"


class TestCrossPlatformFileProtection:
    """Platform-appropriate file permissions on the secret file."""

    def test_posix_file_permissions(self, clean_env: None) -> None:
        if os.name == "nt":
            pytest.skip("POSIX-only test")

        with tempfile.TemporaryDirectory() as tmpdir:
            ReceiptEngine(Path(tmpdir))
            secret_path = Path(tmpdir) / ".kernel_secret"
            mode = stat.S_IMODE(secret_path.stat().st_mode)
            assert mode == 0o600

    def test_windows_acl_attempted(self, clean_env: None) -> None:
        if os.name != "nt":
            pytest.skip("Windows-only test")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = None
                ReceiptEngine(Path(tmpdir))
                assert mock_run.called
                call_args = mock_run.call_args
                assert "icacls" in call_args[0][0]

    def test_windows_acl_failure_is_warning_not_error(self, clean_env: None) -> None:
        if os.name != "nt":
            pytest.skip("Windows-only test")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("subprocess.run", side_effect=Exception("icacls not found")):
                # Should not raise — degrades to warning
                engine = ReceiptEngine(Path(tmpdir))
                assert len(engine.signing_secret) == 32


class TestKeyRotation:
    """Key rotation via env var change + receipt chain verification."""

    def test_env_var_change_rotates_key(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv(ENV_VAR, "old-key")
            engine1 = ReceiptEngine(Path(tmpdir))
            receipt1 = engine1.create(agent_id="agent", action_type="ACT")
            assert engine1.validate(receipt1) is True

            monkeypatch.setenv(ENV_VAR, "new-key")
            engine2 = ReceiptEngine(Path(tmpdir))
            assert engine2.signing_secret == b"new-key"

            # Old receipt fails validation with new key
            assert engine2.validate(receipt1) is False

    def test_explicit_secret_rotation(self, clean_env: None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            engine1 = ReceiptEngine(Path(tmpdir), signing_secret=b"old-key")
            receipt1 = engine1.create(agent_id="agent", action_type="ACT")

            engine2 = ReceiptEngine(Path(tmpdir), signing_secret=b"new-key")
            assert engine2.validate(receipt1) is False

            # New receipt validates with new key
            receipt2 = engine2.create(agent_id="agent", action_type="ACT2")
            assert engine2.validate(receipt2) is True
