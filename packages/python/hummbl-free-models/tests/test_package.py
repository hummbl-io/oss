"""Tests for hummbl-free-models package integrity.

Verifies the package is importable and seed data files are present and valid.
"""

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"


def test_package_importable() -> None:
    import hummbl_free_models
    assert hummbl_free_models.__doc__


def test_providers_yaml_exists_and_valid() -> None:
    yaml = pytest.importorskip("yaml")
    p = DATA_DIR / "providers.yaml"
    assert p.exists(), f"missing {p}"
    data = yaml.safe_load(p.read_text())
    assert "providers" in data
    assert isinstance(data["providers"], list)
    assert len(data["providers"]) >= 1


def test_families_yaml_exists_and_valid() -> None:
    yaml = pytest.importorskip("yaml")
    p = DATA_DIR / "families.yaml"
    assert p.exists(), f"missing {p}"
    data = yaml.safe_load(p.read_text())
    assert "families" in data
    assert isinstance(data["families"], list)
    assert len(data["families"]) >= 1


def test_providers_have_required_fields() -> None:
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((DATA_DIR / "providers.yaml").read_text())
    for provider in data["providers"]:
        assert "id" in provider
        assert "name" in provider


def test_families_have_required_fields() -> None:
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((DATA_DIR / "families.yaml").read_text())
    for family in data["families"]:
        assert "id" in family
        assert "name" in family
