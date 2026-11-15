# Copyright 2024-2026 HUMMBL
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
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_governance._receipt_key (issue #458 key resolution)."""

import os
from pathlib import Path

import pytest

from hummbl_governance import _receipt_key
from hummbl_governance._receipt_key import resolve_receipt_key


@pytest.fixture(autouse=True)
def _clear_key_cache(monkeypatch):
    resolve_receipt_key.cache_clear()
    monkeypatch.delenv("HUMMBL_GOVERNANCE_RECEIPT_KEY", raising=False)
    monkeypatch.delenv("HUMMBL_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("HUMMBL_GOVERNANCE_KEY_DIR", raising=False)
    yield
    resolve_receipt_key.cache_clear()


def test_env_var_primary(monkeypatch):
    monkeypatch.setenv("HUMMBL_GOVERNANCE_RECEIPT_KEY", "module-key")
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "fleet-key")
    assert resolve_receipt_key() == b"module-key"


def test_fleet_env_fallback(monkeypatch):
    monkeypatch.setenv("HUMMBL_SIGNING_SECRET", "fleet-key")
    assert resolve_receipt_key() == b"fleet-key"


def test_persisted_key_generated_and_reused(tmp_path, monkeypatch):
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(tmp_path))
    key1 = resolve_receipt_key()
    assert len(key1) == 32
    key_path = tmp_path / "receipt.key"
    assert key_path.read_bytes() == key1
    resolve_receipt_key.cache_clear()
    assert resolve_receipt_key() == key1


def test_lost_first_run_race_reads_winning_key(tmp_path, monkeypatch):
    """If another process persists the key between our read and create,
    O_EXCL raises FileExistsError and we must return the winner's key,
    not our own generated secret (TOCTOU regression test)."""
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(tmp_path))
    real_open = os.open

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):
        if flags & os.O_EXCL:
            Path(path).write_bytes(b"racer-won-key")
            raise FileExistsError(17, "File exists", str(path))
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", fake_open)
    assert resolve_receipt_key() == b"racer-won-key"


def test_empty_persisted_key_regenerates(tmp_path, monkeypatch):
    """An empty receipt.key (interrupted first-run write) must not be
    returned — hmac accepts b"" silently. Regenerate instead."""
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(tmp_path))
    key_path = tmp_path / "receipt.key"
    key_path.write_bytes(b"")
    key = resolve_receipt_key()
    assert len(key) == 32
    assert key_path.read_bytes() == key


def test_lost_race_with_empty_winner_fails_closed(tmp_path, monkeypatch):
    """If the race winner's key file is empty, fail closed rather than
    adopt a weak key."""
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(tmp_path))
    real_open = os.open

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):
        if flags & os.O_EXCL:
            Path(path).write_bytes(b"")
            raise FileExistsError(17, "File exists", str(path))
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", fake_open)
    with pytest.raises(RuntimeError, match="empty"):
        resolve_receipt_key()


def test_secure_failure_fails_closed_and_cleans_up(tmp_path, monkeypatch):
    """If the key file cannot be ACL-restricted, raise and leave no file."""
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(tmp_path))

    def boom(_path):
        raise RuntimeError("cannot secure")

    monkeypatch.setattr(_receipt_key, "_secure_secret_file", boom)
    with pytest.raises(RuntimeError, match="cannot secure"):
        resolve_receipt_key()
    assert not (tmp_path / "receipt.key").exists()


def test_fail_closed_when_key_cannot_persist(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(blocker / "sub"))
    with pytest.raises(RuntimeError, match="HUMMBL_GOVERNANCE_RECEIPT_KEY"):
        resolve_receipt_key()
