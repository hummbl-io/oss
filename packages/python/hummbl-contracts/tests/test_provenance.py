"""Provenance and integrity verification tests for hummbl-contracts imported fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from hummbl_contracts.schema_validator import validate

_PKG_ROOT = Path(__file__).parent.parent
_REPO_ROOT = _PKG_ROOT.parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "public" / "external-import-record-v1.schema.json"
_RECORD_PATH = _PKG_ROOT / "provenance" / "json-schema-test-suite.import.json"
_FIXTURES_DIR = _PKG_ROOT / "tests" / "fixtures" / "json-schema-test-suite"


def _load_record() -> dict[str, Any]:
    assert _RECORD_PATH.exists(), f"Import record missing at {_RECORD_PATH}"
    return json.loads(_RECORD_PATH.read_text(encoding="utf-8"))


def _load_schema() -> dict[str, Any]:
    assert _SCHEMA_PATH.exists(), f"Import schema missing at {_SCHEMA_PATH}"
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _compute_hashes(content: bytes) -> tuple[str, str]:
    sha256 = hashlib.sha256(content).hexdigest()
    git_blob_sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\x00" + content).hexdigest()
    return sha256, git_blob_sha


def test_import_record_validates_against_schema():
    """Verify that json-schema-test-suite.import.json adheres to external-import-record-v1 schema."""
    record = _load_record()
    schema = _load_schema()
    errors = validate(record, schema)
    assert not errors, f"Import record failed validation: {errors}"


def test_fixture_inventory_digest_integrity():
    """Verify every local fixture file matches its pinned sha256, git_blob_sha, and size."""
    record = _load_record()
    inventory = record["integrity"]["inventory"]
    assert len(inventory) == record["integrity"]["file_count"]
    assert len(inventory) == 17  # 16 test suites + 1 LICENSE

    for item in inventory:
        dest_path = _REPO_ROOT / item["destination_path"]
        assert dest_path.exists(), f"Missing fixture file: {dest_path}"
        content = dest_path.read_bytes()

        assert len(content) == item["bytes"], (
            f"Size mismatch for {item['filename']}: expected {item['bytes']}, got {len(content)}"
        )
        sha256, git_blob = _compute_hashes(content)
        assert sha256 == item["sha256"], (
            f"SHA256 mismatch for {item['filename']}: expected {item['sha256']}, got {sha256}"
        )
        assert git_blob == item["git_blob_sha"], (
            f"Git blob SHA mismatch for {item['filename']}: expected {item['git_blob_sha']}, got {git_blob}"
        )


def test_no_unlisted_or_missing_fixture_files():
    """Ensure directory contents match recorded inventory with no stray or omitted files."""
    record = _load_record()
    inventory_filenames = {item["filename"] for item in record["integrity"]["inventory"]}
    disk_filenames = {p.name for p in _FIXTURES_DIR.iterdir() if p.is_file()}

    missing = inventory_filenames - disk_filenames
    unlisted = disk_filenames - inventory_filenames
    assert not missing, f"Recorded fixture files missing from disk: {missing}"
    assert not unlisted, f"Unlisted fixture files found on disk: {unlisted}"


def test_provenance_rights_and_attribution():
    """Verify required attribution and license files are present and match record."""
    record = _load_record()
    rights = record["rights"]
    assert "MIT" in rights["declared_licenses"]
    assert record["reuse_mode"]["mode"] == "test_fixtures"
    assert record["dependency_treatment"]["runtime_dependency_category"] == "zero_runtime"
    assert record["identity_and_selection"]["immutable_source_revision"] == (
        "f6fd52a0a95472e079cbfc6ef7f089702b80e045"
    )

    license_path = _FIXTURES_DIR / "LICENSE"
    assert license_path.exists()
    license_text = license_path.read_text(encoding="utf-8")
    for attr in rights["attributions"]:
        assert attr in license_text, f"Attribution {attr!r} not found in {license_path}"


def test_negative_modified_content_fails_integrity(tmp_path):
    """Negative test: tampering with fixture content causes hash mismatch."""
    record = _load_record()
    target = record["integrity"]["inventory"][0]
    tampered_content = b"{\"tampered\": true}"
    sha256, git_blob = _compute_hashes(tampered_content)
    assert sha256 != target["sha256"]
    assert git_blob != target["git_blob_sha"]


def test_negative_unlisted_file_fails_inventory_check():
    """Negative test: an extra unlisted fixture file is caught."""
    record = _load_record()
    inventory_filenames = {item["filename"] for item in record["integrity"]["inventory"]}
    disk_filenames = set(inventory_filenames) | {"unauthorized_addition.json"}
    unlisted = disk_filenames - inventory_filenames
    assert unlisted == {"unauthorized_addition.json"}


def test_negative_missing_file_fails_inventory_check():
    """Negative test: a missing recorded fixture file is caught."""
    record = _load_record()
    inventory_filenames = {item["filename"] for item in record["integrity"]["inventory"]}
    assert "type.json" in inventory_filenames
    simulated_disk = inventory_filenames - {"type.json"}
    missing = inventory_filenames - simulated_disk
    assert missing == {"type.json"}
