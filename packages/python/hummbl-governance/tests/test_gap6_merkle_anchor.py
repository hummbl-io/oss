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
# SPDX-License-Identifier: Apache-2.0

"""Tests for gap-6 Merkle anchoring activation script."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# Load the script module (hyphenated filename requires importlib)
_script_path = Path(__file__).parent.parent / "scripts" / "gap6-merkle-anchor.py"
_spec = importlib.util.spec_from_file_location("gap6_merkle_anchor", _script_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

hash_bus_entries = _mod.hash_bus_entries
generate_sth = _mod.generate_sth
anchor = _mod.anchor


class TestHashBusEntries:
    def test_hash_bus_entries(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        bus.write_text("line1\nline2\nline3\n")
        hashes = hash_bus_entries(bus)
        assert len(hashes) == 3
        for h in hashes:
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    def test_hash_empty_bus(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        bus.write_text("")
        hashes = hash_bus_entries(bus)
        assert hashes == []

    def test_hash_missing_bus(self, tmp_path: Path) -> None:
        bus = tmp_path / "nonexistent.tsv"
        hashes = hash_bus_entries(bus)
        assert hashes == []

    def test_hash_skips_blank_lines(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        bus.write_text("line1\n\nline3\n")
        hashes = hash_bus_entries(bus)
        assert len(hashes) == 2


class TestGenerateSTH:
    def test_generate_sth_with_entries(self) -> None:
        hashes = ["a" * 64, "b" * 64, "c" * 64]
        sth = generate_sth(hashes, "test-machine")
        assert sth["machine"] == "test-machine"
        assert sth["tree_size"] == 3
        assert sth["entry_count"] == 3
        assert len(sth["root_hash"]) == 64
        assert sth["first_entry_hash"] == "a" * 64
        assert sth["last_entry_hash"] == "c" * 64
        assert "timestamp" in sth
        assert "timestamp_iso" in sth

    def test_generate_sth_empty(self) -> None:
        sth = generate_sth([], "test-machine")
        assert sth["tree_size"] == 0
        assert sth["root_hash"] == ""
        assert sth["entry_count"] == 0

    def test_sth_is_json_serializable(self) -> None:
        hashes = ["a" * 64, "b" * 64]
        sth = generate_sth(hashes, "test")
        json.dumps(sth)


class TestSTHConsistency:
    def test_same_entries_same_root(self) -> None:
        hashes = ["a" * 64, "b" * 64, "c" * 64]
        sth1 = generate_sth(hashes, "m1")
        sth2 = generate_sth(hashes, "m2")
        assert sth1["root_hash"] == sth2["root_hash"]

    def test_different_entries_different_root(self) -> None:
        hashes1 = ["a" * 64, "b" * 64]
        hashes2 = ["a" * 64, "c" * 64]
        sth1 = generate_sth(hashes1, "m")
        sth2 = generate_sth(hashes2, "m")
        assert sth1["root_hash"] != sth2["root_hash"]

    def test_prefix_consistency(self) -> None:
        """STH of first N entries should match prefix of STH of N+M entries."""
        from hummbl_governance.primitives.merkle_anchor import MerkleTree

        hashes = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
        sth_2 = generate_sth(hashes[:2], "m")
        sth_4 = generate_sth(hashes[:4], "m")

        tree = MerkleTree()
        for h in hashes[:2]:
            tree.append(h)
        assert tree.root_hash() == sth_2["root_hash"]
        assert sth_2["root_hash"] != sth_4["root_hash"]


class TestAnchorDryRun:
    def test_dry_run_does_not_publish(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bus = tmp_path / "messages.tsv"
        bus.write_text("entry1\nentry2\nentry3\n")
        result = anchor(bus, "test-machine", dry_run=True)
        assert result == 0
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "dry-run://gist/" in captured.out
