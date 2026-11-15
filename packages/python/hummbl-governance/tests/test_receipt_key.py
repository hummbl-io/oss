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


def test_fail_closed_when_key_cannot_persist(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv("HUMMBL_GOVERNANCE_KEY_DIR", str(blocker / "sub"))
    with pytest.raises(RuntimeError, match="HUMMBL_GOVERNANCE_RECEIPT_KEY"):
        resolve_receipt_key()
