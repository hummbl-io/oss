"""Smoke tests for hummbl-contracts package import and schema loading."""

import hummbl_contracts


def test_package_import():
    """Package imports without error."""
    assert hummbl_contracts.__version__


def test_list_schemas():
    """list_schemas() returns a non-empty list."""
    schemas = hummbl_contracts.list_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) > 0


def test_load_schema():
    """load_schema() returns a dict for a known schema."""
    schemas = hummbl_contracts.list_schemas()
    if schemas:
        schema = hummbl_contracts.load_schema(schemas[0])
        assert isinstance(schema, dict)
