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

"""Tests for hummbl_governance.schema_validator."""

import json
import tempfile
from pathlib import Path

from hummbl_governance.schema_validator import RefRegistry, SchemaValidator


class TestTypeValidation:
    """Test type keyword validation."""

    def test_string_valid(self):
        errors = SchemaValidator.validate("hello", {"type": "string"})
        assert errors == []

    def test_string_invalid(self):
        errors = SchemaValidator.validate(42, {"type": "string"})
        assert len(errors) == 1

    def test_integer_valid(self):
        errors = SchemaValidator.validate(42, {"type": "integer"})
        assert errors == []

    def test_number_valid(self):
        errors = SchemaValidator.validate(3.14, {"type": "number"})
        assert errors == []

    def test_boolean_valid(self):
        errors = SchemaValidator.validate(True, {"type": "boolean"})
        assert errors == []

    def test_array_valid(self):
        errors = SchemaValidator.validate([1, 2, 3], {"type": "array"})
        assert errors == []

    def test_object_valid(self):
        errors = SchemaValidator.validate({"a": 1}, {"type": "object"})
        assert errors == []

    def test_null_valid(self):
        errors = SchemaValidator.validate(None, {"type": "null"})
        assert errors == []

    def test_multi_type(self):
        errors = SchemaValidator.validate("hello", {"type": ["string", "null"]})
        assert errors == []
        errors = SchemaValidator.validate(None, {"type": ["string", "null"]})
        assert errors == []


class TestObjectValidation:
    """Test object schema validation."""

    def test_required_present(self):
        schema = {"type": "object", "required": ["name"]}
        errors = SchemaValidator.validate({"name": "test"}, schema)
        assert errors == []

    def test_required_missing(self):
        schema = {"type": "object", "required": ["name"]}
        errors = SchemaValidator.validate({}, schema)
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        errors = SchemaValidator.validate({"name": "Alice", "age": 30}, schema)
        assert errors == []

    def test_property_type_mismatch(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        errors = SchemaValidator.validate({"name": 42}, schema)
        assert len(errors) == 1

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = SchemaValidator.validate({"name": "test", "extra": 1}, schema)
        assert len(errors) == 1
        assert "extra" in errors[0]

    def test_additional_properties_schema(self):
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": {"type": "string"},
        }
        errors = SchemaValidator.validate({"a": "ok", "b": 42}, schema)
        assert len(errors) == 1  # b is not a string


class TestStringValidation:
    """Test string-specific keywords."""

    def test_min_length(self):
        errors = SchemaValidator.validate("ab", {"type": "string", "minLength": 3})
        assert len(errors) == 1

    def test_max_length(self):
        errors = SchemaValidator.validate("abcd", {"type": "string", "maxLength": 3})
        assert len(errors) == 1

    def test_pattern_match(self):
        errors = SchemaValidator.validate("abc123", {"type": "string", "pattern": r"^[a-z]+\d+$"})
        assert errors == []

    def test_pattern_no_match(self):
        errors = SchemaValidator.validate("123abc", {"type": "string", "pattern": r"^[a-z]+$"})
        assert len(errors) == 1

    def test_enum(self):
        errors = SchemaValidator.validate("a", {"enum": ["a", "b", "c"]})
        assert errors == []

    def test_enum_invalid(self):
        errors = SchemaValidator.validate("d", {"enum": ["a", "b", "c"]})
        assert len(errors) == 1


class TestNumberValidation:
    """Test number-specific keywords."""

    def test_minimum(self):
        errors = SchemaValidator.validate(5, {"type": "integer", "minimum": 10})
        assert len(errors) == 1

    def test_maximum(self):
        errors = SchemaValidator.validate(15, {"type": "integer", "maximum": 10})
        assert len(errors) == 1

    def test_within_range(self):
        errors = SchemaValidator.validate(7, {"type": "integer", "minimum": 0, "maximum": 10})
        assert errors == []


class TestArrayValidation:
    """Test array-specific keywords."""

    def test_min_items(self):
        errors = SchemaValidator.validate([1], {"type": "array", "minItems": 2})
        assert len(errors) == 1

    def test_max_items(self):
        errors = SchemaValidator.validate([1, 2, 3], {"type": "array", "maxItems": 2})
        assert len(errors) == 1

    def test_items_schema(self):
        schema = {"type": "array", "items": {"type": "string"}}
        errors = SchemaValidator.validate(["a", "b"], schema)
        assert errors == []

    def test_items_schema_invalid(self):
        schema = {"type": "array", "items": {"type": "string"}}
        errors = SchemaValidator.validate(["a", 42], schema)
        assert len(errors) == 1


class TestCompositionKeywords:
    """Test oneOf and anyOf."""

    def test_one_of_match(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        errors = SchemaValidator.validate("hello", schema)
        assert errors == []

    def test_one_of_no_match(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        errors = SchemaValidator.validate(3.14, schema)
        assert len(errors) == 1

    def test_any_of_match(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        errors = SchemaValidator.validate(42, schema)
        assert errors == []

    def test_any_of_no_match(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        errors = SchemaValidator.validate(3.14, schema)
        assert len(errors) == 1

    def test_const(self):
        errors = SchemaValidator.validate("exact", {"const": "exact"})
        assert errors == []

    def test_const_mismatch(self):
        errors = SchemaValidator.validate("wrong", {"const": "exact"})
        assert len(errors) == 1


class TestValidateDict:
    """Test validate_dict convenience method."""

    def test_valid(self):
        schema = {"type": "object", "required": ["name"]}
        valid, errors = SchemaValidator.validate_dict({"name": "test"}, schema)
        assert valid is True
        assert errors == []

    def test_invalid(self):
        schema = {"type": "object", "required": ["name"]}
        valid, errors = SchemaValidator.validate_dict({}, schema)
        assert valid is False
        assert len(errors) == 1


class TestValidateFile:
    """Test file validation."""

    def test_validate_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            instance_path = Path(tmpdir) / "data.json"
            schema_path = Path(tmpdir) / "schema.json"

            instance_path.write_text(json.dumps({"name": "test"}))
            schema_path.write_text(
                json.dumps(
                    {
                        "type": "object",
                        "required": ["name"],
                        "properties": {"name": {"type": "string"}},
                    }
                )
            )

            valid, errors = SchemaValidator.validate_file(instance_path, schema_path)
            assert valid is True

    def test_validate_file_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            instance_path = Path(tmpdir) / "data.json"
            schema_path = Path(tmpdir) / "schema.json"

            instance_path.write_text(json.dumps({"count": "not a number"}))
            schema_path.write_text(
                json.dumps(
                    {
                        "type": "object",
                        "properties": {"count": {"type": "integer"}},
                    }
                )
            )

            valid, errors = SchemaValidator.validate_file(instance_path, schema_path)
            assert valid is False

    def test_validate_file_invalid_json_instance(self):
        """Invalid JSON in instance file returns errors, not an exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            instance_path = Path(tmpdir) / "data.json"
            schema_path = Path(tmpdir) / "schema.json"

            instance_path.write_text("{not valid json}")
            schema_path.write_text(json.dumps({"type": "object"}))

            valid, errors = SchemaValidator.validate_file(instance_path, schema_path)
            assert valid is False
            assert "invalid JSON" in errors[0]

    def test_validate_file_invalid_json_schema(self):
        """Invalid JSON in schema file returns errors, not an exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            instance_path = Path(tmpdir) / "data.json"
            schema_path = Path(tmpdir) / "schema.json"

            instance_path.write_text(json.dumps({"name": "test"}))
            schema_path.write_text("{broken")

            valid, errors = SchemaValidator.validate_file(instance_path, schema_path)
            assert valid is False
            assert "invalid JSON" in errors[0]

    def test_validate_file_missing_instance(self):
        """Missing instance file returns errors, not an exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            instance_path = Path(tmpdir) / "missing.json"
            schema_path = Path(tmpdir) / "schema.json"
            schema_path.write_text(json.dumps({"type": "object"}))

            valid, errors = SchemaValidator.validate_file(instance_path, schema_path)
            assert valid is False


class TestRefResolution:
    """Test ``$ref`` resolution against the root document and registry."""

    def test_local_ref_to_defs(self):
        schema = {
            "$id": "https://example.com/root.json",
            "$defs": {
                "name": {"type": "string", "minLength": 2},
            },
            "type": "object",
            "properties": {
                "first": {"$ref": "#/$defs/name"},
                "second": {"$ref": "#/$defs/name"},
            },
        }
        errors = SchemaValidator.validate({"first": "ab", "second": "cd"}, schema)
        assert errors == []

    def test_local_ref_enforces_target_constraints(self):
        schema = {
            "$defs": {"name": {"type": "string", "minLength": 5}},
            "type": "object",
            "properties": {"first": {"$ref": "#/$defs/name"}},
        }
        errors = SchemaValidator.validate({"first": "ab"}, schema)
        assert len(errors) == 1
        assert "minLength" in errors[0]

    def test_local_ref_type_mismatch(self):
        schema = {
            "$defs": {"name": {"type": "string"}},
            "type": "object",
            "properties": {"first": {"$ref": "#/$defs/name"}},
        }
        errors = SchemaValidator.validate({"first": 42}, schema)
        assert len(errors) == 1
        assert "expected type" in errors[0]

    def test_ref_at_root(self):
        schema = {
            "$defs": {"positive": {"type": "integer", "minimum": 1}},
            "type": "array",
            "items": {"$ref": "#/$defs/positive"},
        }
        errors = SchemaValidator.validate([1, 2, 3], schema)
        assert errors == []
        errors = SchemaValidator.validate([1, 0, 3], schema)
        assert len(errors) == 1
        assert "minimum" in errors[0]

    def test_ref_with_sibling_keywords(self):
        # Draft 2020-12: $ref may appear alongside sibling keywords.
        schema = {
            "$defs": {"base": {"type": "string"}},
            "type": "object",
            "properties": {
                "value": {"$ref": "#/$defs/base", "maxLength": 3},
            },
        }
        errors = SchemaValidator.validate({"value": "ab"}, schema)
        assert errors == []
        errors = SchemaValidator.validate({"value": "abcd"}, schema)
        assert any("maxLength" in e for e in errors)

    def test_nested_ref_chain(self):
        schema = {
            "$defs": {
                "a": {"$ref": "#/$defs/b"},
                "b": {"type": "integer", "minimum": 10},
            },
            "type": "object",
            "properties": {"x": {"$ref": "#/$defs/a"}},
        }
        errors = SchemaValidator.validate({"x": 15}, schema)
        assert errors == []
        errors = SchemaValidator.validate({"x": 5}, schema)
        assert any("minimum" in e for e in errors)

    def test_circular_ref_is_detected(self):
        schema = {
            "$defs": {
                "node": {
                    "type": "object",
                    "properties": {"child": {"$ref": "#/$defs/node"}},
                },
            },
            "type": "object",
            "properties": {"root": {"$ref": "#/$defs/node"}},
        }
        # Deep nesting triggers the cycle guard (ref_stack grows on each hop).
        instance = {"root": {"child": {"child": {"child": {}}}}}
        errors = SchemaValidator.validate(instance, schema)
        assert any("circular $ref" in e for e in errors)

    def test_self_ref_with_terminating_type_is_allowed(self):
        # A self-referential schema that terminates via a type mismatch is fine.
        schema = {
            "$defs": {
                "leaf": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                },
            },
            "type": "object",
            "properties": {"data": {"$ref": "#/$defs/leaf"}},
        }
        errors = SchemaValidator.validate({"data": {"value": "ok"}}, schema)
        assert errors == []

    def test_unresolvable_local_ref(self):
        schema = {
            "type": "object",
            "properties": {"x": {"$ref": "#/$defs/missing"}},
        }
        errors = SchemaValidator.validate({"x": 1}, schema)
        assert len(errors) == 1
        assert "not found" in errors[0] or "unresolvable" in errors[0].lower() or "missing" in errors[0]

    def test_ref_in_oneof(self):
        schema = {
            "$defs": {"str_def": {"type": "string"}},
            "oneOf": [
                {"$ref": "#/$defs/str_def"},
                {"type": "integer"},
            ],
        }
        errors = SchemaValidator.validate("hello", schema)
        assert errors == []
        errors = SchemaValidator.validate(42, schema)
        assert errors == []
        errors = SchemaValidator.validate(3.14, schema)
        assert len(errors) == 1

    def test_ref_in_anyof(self):
        schema = {
            "$defs": {"str_def": {"type": "string"}},
            "anyOf": [
                {"$ref": "#/$defs/str_def"},
                {"type": "integer"},
            ],
        }
        errors = SchemaValidator.validate("hello", schema)
        assert errors == []
        errors = SchemaValidator.validate(42, schema)
        assert errors == []

    def test_root_ref(self):
        schema = {
            "$id": "https://example.com/root.json",
            "type": "object",
            "properties": {"self": {"$ref": "#"}},
        }
        errors = SchemaValidator.validate({"self": {}}, schema)
        assert errors == []

    def test_json_pointer_with_tilde(self):
        schema = {
            "$defs": {
                "a~b": {"type": "string"},
            },
            "type": "object",
            "properties": {"x": {"$ref": "#/$defs/a~0b"}},
        }
        errors = SchemaValidator.validate({"x": "ok"}, schema)
        assert errors == []
        errors = SchemaValidator.validate({"x": 1}, schema)
        assert len(errors) == 1


class TestRefRegistry:
    """Test cross-document ``$ref`` resolution via :class:`RefRegistry`."""

    def test_cross_document_ref(self):
        refs_schema = {
            "$id": "https://example.com/refs.json",
            "$defs": {"name": {"type": "string", "minLength": 3}},
        }
        main_schema = {
            "$id": "https://example.com/main.json",
            "type": "object",
            "properties": {"x": {"$ref": "https://example.com/refs.json#/$defs/name"}},
        }
        registry = RefRegistry()
        registry.register(refs_schema)
        errors = SchemaValidator.validate({"x": "abc"}, main_schema, registry=registry)
        assert errors == []
        errors = SchemaValidator.validate({"x": "ab"}, main_schema, registry=registry)
        assert any("minLength" in e for e in errors)

    def test_cross_document_ref_without_registry_errors(self):
        schema = {
            "type": "object",
            "properties": {"x": {"$ref": "https://example.com/other.json#/$defs/name"}},
        }
        errors = SchemaValidator.validate({"x": "ab"}, schema)
        assert len(errors) == 1
        assert "no registry" in errors[0] or "registry" in errors[0]

    def test_cross_document_ref_unregistered_doc(self):
        schema = {
            "type": "object",
            "properties": {"x": {"$ref": "https://example.com/missing.json#/$defs/name"}},
        }
        registry = RefRegistry()
        errors = SchemaValidator.validate({"x": "ab"}, schema, registry=registry)
        assert len(errors) == 1
        assert "unregistered" in errors[0]

    def test_registry_alias(self):
        refs_schema = {
            "$defs": {"name": {"type": "string"}},
        }
        main_schema = {
            "type": "object",
            "properties": {"x": {"$ref": "alias:refs#/$defs/name"}},
        }
        registry = RefRegistry()
        registry.register(refs_schema, alias="alias:refs")
        errors = SchemaValidator.validate({"x": "ok"}, main_schema, registry=registry)
        assert errors == []

    def test_registry_requires_id_or_alias(self):
        registry = RefRegistry()
        try:
            registry.register({"type": "string"})
            raise AssertionError("expected RefResolutionError")
        except Exception as exc:
            assert "no $id" in str(exc).lower() or "alias" in str(exc).lower()

    def test_registry_without_fragment(self):
        refs_schema = {
            "$id": "https://example.com/refs.json",
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        main_schema = {
            "type": "object",
            "properties": {"x": {"$ref": "https://example.com/refs.json"}},
        }
        registry = RefRegistry()
        registry.register(refs_schema)
        errors = SchemaValidator.validate({"x": {"name": "ok"}}, main_schema, registry=registry)
        assert errors == []
        errors = SchemaValidator.validate({"x": {}}, main_schema, registry=registry)
        assert any("missing required" in e for e in errors)

    def test_validate_file_with_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            refs_path = Path(tmpdir) / "refs.json"
            schema_path = Path(tmpdir) / "schema.json"
            instance_path = Path(tmpdir) / "data.json"

            refs_path.write_text(
                json.dumps(
                    {
                        "$id": "https://example.com/refs.json",
                        "$defs": {"name": {"type": "string", "minLength": 2}},
                    }
                )
            )
            schema_path.write_text(
                json.dumps(
                    {
                        "type": "object",
                        "properties": {"x": {"$ref": "https://example.com/refs.json#/$defs/name"}},
                    }
                )
            )
            instance_path.write_text(json.dumps({"x": "ab"}))

            refs = json.loads(refs_path.read_text())
            registry = RefRegistry()
            registry.register(refs)
            valid, errors = SchemaValidator.validate_file(instance_path, schema_path, registry=registry)
            assert valid is True

    def test_validate_dict_with_registry(self):
        refs_schema = {
            "$id": "https://example.com/refs.json",
            "$defs": {"name": {"type": "string"}},
        }
        main_schema = {
            "type": "object",
            "properties": {"x": {"$ref": "https://example.com/refs.json#/$defs/name"}},
        }
        registry = RefRegistry()
        registry.register(refs_schema)
        valid, errors = SchemaValidator.validate_dict({"x": "ok"}, main_schema, registry=registry)
        assert valid is True
        assert errors == []
