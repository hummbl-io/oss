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

"""Tests for the Base120 golden corpus directory contract."""

from __future__ import annotations

import json
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "corpus"
VALID_DIR = CORPUS_DIR / "valid"
INVALID_DIR = CORPUS_DIR / "invalid"
EXPECTED_DIR = CORPUS_DIR / "expected"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_corpus_directories_exist() -> None:
    assert VALID_DIR.is_dir()
    assert INVALID_DIR.is_dir()
    assert EXPECTED_DIR.is_dir()


def test_valid_corpus_contains_json_artifacts() -> None:
    valid_files = sorted(VALID_DIR.glob("*.json"))
    assert valid_files, "valid corpus must not be empty"
    for path in valid_files:
        assert isinstance(_load_json(path), dict)


def test_invalid_corpus_has_expected_error_manifests() -> None:
    invalid_files = sorted(INVALID_DIR.glob("*.json"))
    assert invalid_files, "invalid corpus must not be empty"
    for path in invalid_files:
        assert isinstance(_load_json(path), dict)
        expected_path = EXPECTED_DIR / f"{path.stem}.errs.json"
        assert expected_path.exists(), f"missing expected errors for {path.name}"
        expected = _load_json(expected_path)
        assert isinstance(expected, list)
        assert expected, f"expected errors for {path.name} must not be empty"
        assert all(isinstance(item, str) and item.startswith("ERR-") for item in expected)


def test_no_orphan_expected_error_manifests() -> None:
    invalid_stems = {path.stem for path in INVALID_DIR.glob("*.json")}
    expected_stems = {
        path.name.removesuffix(".errs.json") for path in EXPECTED_DIR.glob("*.errs.json")
    }
    assert expected_stems == invalid_stems
