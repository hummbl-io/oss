#!/usr/bin/env python3
"""Tests for schema registry (issue #37)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from static_registry import generate_manifest


def test_generate_manifest():
    """generate_manifest should produce a valid manifest from schemas/."""
    schemas_dir = REPO_ROOT / "schemas"
    manifest = generate_manifest(schemas_dir)
    assert "registry_version" in manifest
    assert "schemas" in manifest
    assert manifest["schema_count"] > 0
    assert len(manifest["schemas"]) == manifest["schema_count"]


def test_manifest_schema_entries():
    """Each schema entry should have required fields."""
    schemas_dir = REPO_ROOT / "schemas"
    manifest = generate_manifest(schemas_dir)
    for s in manifest["schemas"]:
        assert "schema_id" in s
        assert "url" in s
        assert "title" in s


def test_manifest_includes_contract():
    """The manifest should include the contract schema."""
    schemas_dir = REPO_ROOT / "schemas"
    manifest = generate_manifest(schemas_dir)
    ids = [s["schema_id"] for s in manifest["schemas"]]
    assert "contract.schema.json" in ids


def test_manifest_tuple_type_extraction():
    """The manifest should extract tuple_type const from schemas that have it."""
    schemas_dir = REPO_ROOT / "schemas"
    manifest = generate_manifest(schemas_dir)
    contract_entry = next(
        s for s in manifest["schemas"] if s["schema_id"] == "contract.schema.json"
    )
    assert contract_entry["tuple_type"] == "CONTRACT"


def test_manifest_updated_at():
    """The manifest should have an updated_at timestamp."""
    schemas_dir = REPO_ROOT / "schemas"
    manifest = generate_manifest(schemas_dir)
    assert "updated_at" in manifest
    assert len(manifest["updated_at"]) > 0


if __name__ == "__main__":
    test_generate_manifest()
    test_manifest_schema_entries()
    test_manifest_includes_contract()
    test_manifest_tuple_type_extraction()
    test_manifest_updated_at()
    print("All schema registry tests passed")
