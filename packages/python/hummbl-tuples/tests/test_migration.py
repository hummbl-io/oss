#!/usr/bin/env python3
"""Tests for schema versioning and migration (issue #32)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from migrate_tuples import (
    MIGRATIONS,
    detect_version,
    find_migration_path,
    migrate_tuple,
    migrate_v1_to_v2,
)


def test_detect_v1():
    """A tuple without previous_hash should be detected as v1."""
    t = {"tuple_type": "CONTRACT", "id": "test", "tuple_data": {}}
    assert detect_version(t) == "v1"


def test_detect_v2():
    """A tuple with previous_hash should be detected as v2."""
    t = {"tuple_type": "CONTRACT", "id": "test", "previous_hash": None, "tuple_data": {}}
    assert detect_version(t) == "v2"


def test_v1_to_v2_migration():
    """migrate_v1_to_v2 should add previous_hash field."""
    t = {"tuple_type": "CONTRACT", "id": "test", "tuple_data": {}}
    result = migrate_v1_to_v2(t)
    assert "previous_hash" in result
    assert result["previous_hash"] is None


def test_find_migration_path_same():
    """find_migration_path should return [source] when source == target."""
    assert find_migration_path("v1", "v1") == ["v1"]


def test_find_migration_path_v1_to_v2():
    """find_migration_path should find v1 -> v2 path."""
    path = find_migration_path("v1", "v2")
    assert path == ["v1", "v2"]


def test_find_migration_path_no_path():
    """find_migration_path should return None when no path exists."""
    path = find_migration_path("v1", "v999")
    assert path is None


def test_migrate_tuple_v1_to_v2():
    """migrate_tuple should migrate v1 to v2."""
    t = {"tuple_type": "CONTRACT", "id": "test", "tuple_data": {}}
    migrated, path = migrate_tuple(t, "v2")
    assert path == ["v1", "v2"]
    assert "previous_hash" in migrated
    assert migrated["previous_hash"] is None


def test_migrate_tuple_already_v2():
    """migrate_tuple should return unchanged when already at target."""
    t = {"tuple_type": "CONTRACT", "id": "test", "previous_hash": None, "tuple_data": {}}
    migrated, path = migrate_tuple(t, "v2")
    assert path == ["v2"]
    assert migrated == t


def test_migrate_fixture_files():
    """Migration should work on fixture files."""
    fixture_dir = REPO_ROOT / "tests" / "fixtures" / "migration"
    v1_file = fixture_dir / "v1_contract.json"
    with v1_file.open("r", encoding="utf-8") as f:
        t = json.load(f)
    assert detect_version(t) == "v1"
    migrated, path = migrate_tuple(t, "v2")
    assert path == ["v1", "v2"]
    assert "previous_hash" in migrated


def test_migration_registry_has_v1_to_v2():
    """The migration registry should have a v1 to v2 migration."""
    assert ("v1", "v2") in MIGRATIONS


if __name__ == "__main__":
    test_detect_v1()
    test_detect_v2()
    test_v1_to_v2_migration()
    test_find_migration_path_same()
    test_find_migration_path_v1_to_v2()
    test_find_migration_path_no_path()
    test_migrate_tuple_v1_to_v2()
    test_migrate_tuple_already_v2()
    test_migrate_fixture_files()
    test_migration_registry_has_v1_to_v2()
    print("All migration tests passed")
