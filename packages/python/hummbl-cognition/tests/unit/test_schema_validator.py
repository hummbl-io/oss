"""Tests for hummbl_cognition.schema_validator.

Covers all supported JSON Schema keywords: type, required, properties,
enum, pattern, minimum, maximum, minLength, maxLength, minItems, maxItems,
items, additionalProperties, const, oneOf, anyOf.
Also covers validate_file, validate_entry_dict, validate_state_dict,
and _load_default_schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from hummbl_cognition.schema_validator import (
    ValidationError,
    validate,
    validate_entry_dict,
    validate_file,
    validate_state_dict,
)

# ---------------------------------------------------------------------------
# Embedded schemas (avoid symlink dependency on contracts/)
# ---------------------------------------------------------------------------

_LEDGER_SCHEMA = {
    "type": "object",
    "required": [
        "id",
        "timestamp",
        "agent",
        "vendor",
        "model",
        "type",
        "scope",
        "content",
        "content_hash",
    ],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "pattern": "^clp-[a-f0-9]{12}$"},
        "timestamp": {"type": "string"},
        "agent": {"type": "string", "minLength": 1},
        "vendor": {
            "type": "string",
            "enum": ["anthropic", "google", "human", "local", "moonshot", "openai"],
        },
        "model": {"type": "string", "minLength": 1},
        "type": {
            "type": "string",
            "enum": ["lesson", "decision", "discovery", "correction", "convention"],
        },
        "scope": {
            "type": "string",
            "enum": ["project", "module", "file", "convention", "process"],
        },
        "content": {"type": "string", "minLength": 1, "maxLength": 4096},
        "content_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "evidence": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "supersedes": {"type": ["string", "null"], "pattern": "^clp-[a-f0-9]{12}$"},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "assurance_level": {
            "type": ["string", "null"],
            "enum": ["SELF", "PEER", "VERIFIED", None],
        },
        "signature": {"type": ["string", "null"]},
    },
}

_STATE_SCHEMA = {
    "type": "object",
    "required": ["version", "updated_at", "updated_by"],
    "additionalProperties": False,
    "properties": {
        "version": {"type": "integer", "minimum": 0},
        "updated_at": {"type": "string"},
        "updated_by": {"type": "string"},
        "active_agents": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["active", "idle", "offline"]},
                    "capabilities": {"type": "array", "items": {"type": "string"}},
                    "last_seen": {"type": "string"},
                    "vendor": {"type": "string"},
                    "model": {"type": "string"},
                },
            },
        },
        "claimed_files": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "claimed_at": {"type": "string"},
                    "purpose": {"type": "string"},
                },
            },
        },
        "active_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["decision_id", "question", "proposed_by"],
                "properties": {
                    "decision_id": {"type": "string"},
                    "question": {"type": "string"},
                    "proposed_by": {"type": "string"},
                    "proposed_at": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "resolved": {"type": "boolean"},
                },
            },
        },
        "sprint": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "lanes": {"type": "object", "additionalProperties": {"type": "string"}},
                "started_at": {"type": "string"},
            },
        },
        "flags": {"type": "object", "additionalProperties": True},
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_ledger_entry(**overrides) -> dict:
    """Return a minimal valid CLP ledger entry."""
    entry = {
        "id": "clp-aabbccddeeff",
        "timestamp": "2026-03-04T12:00:00Z",
        "agent": "claude-code",
        "vendor": "anthropic",
        "model": "claude-opus-4-6",
        "type": "lesson",
        "scope": "project",
        "content": "Bus writes must use bus_writer for flock safety.",
        "content_hash": "a" * 64,
    }
    entry.update(overrides)
    return entry


def _valid_shared_state(**overrides) -> dict:
    """Return a minimal valid CLP shared state."""
    state = {
        "version": 1,
        "updated_at": "2026-03-04T12:00:00Z",
        "updated_by": "claude-code",
    }
    state.update(overrides)
    return state


# ===================================================================
# Core validate() -- type keyword
# ===================================================================


class TestTypeKeyword:
    def test_string_valid(self):
        assert validate("hello", {"type": "string"}) == []

    def test_string_invalid(self):
        errs = validate(42, {"type": "string"})
        assert len(errs) == 1
        assert "expected type" in errs[0]

    def test_integer_valid(self):
        assert validate(7, {"type": "integer"}) == []

    def test_integer_rejects_float(self):
        errs = validate(7.5, {"type": "integer"})
        assert len(errs) == 1

    def test_number_accepts_int(self):
        assert validate(7, {"type": "number"}) == []

    def test_number_accepts_float(self):
        assert validate(7.5, {"type": "number"}) == []

    def test_boolean_valid(self):
        assert validate(True, {"type": "boolean"}) == []

    def test_boolean_invalid(self):
        errs = validate(1, {"type": "boolean"})
        assert len(errs) == 1

    def test_array_valid(self):
        assert validate([1, 2], {"type": "array"}) == []

    def test_object_valid(self):
        assert validate({"a": 1}, {"type": "object"}) == []

    def test_null_valid(self):
        assert validate(None, {"type": "null"}) == []

    def test_type_list(self):
        schema = {"type": ["string", "null"]}
        assert validate("hello", schema) == []
        assert validate(None, schema) == []
        errs = validate(42, schema)
        assert len(errs) == 1


# ===================================================================
# const keyword
# ===================================================================


class TestConstKeyword:
    def test_const_match(self):
        assert validate("fixed", {"const": "fixed"}) == []

    def test_const_mismatch(self):
        errs = validate("other", {"const": "fixed"})
        assert len(errs) == 1
        assert "expected const" in errs[0]

    def test_const_short_circuits(self):
        """Const mismatch returns immediately, skipping further checks."""
        schema = {"const": "x", "minLength": 100}
        errs = validate("y", schema)
        assert len(errs) == 1
        assert "const" in errs[0]


# ===================================================================
# enum keyword
# ===================================================================


class TestEnumKeyword:
    def test_enum_valid(self):
        schema = {"enum": ["a", "b", "c"]}
        assert validate("b", schema) == []

    def test_enum_invalid(self):
        schema = {"enum": ["a", "b", "c"]}
        errs = validate("d", schema)
        assert len(errs) == 1
        assert "not in enum" in errs[0]


# ===================================================================
# pattern keyword
# ===================================================================


class TestPatternKeyword:
    def test_pattern_match(self):
        schema = {"type": "string", "pattern": "^clp-[a-f0-9]{12}$"}
        assert validate("clp-aabbccddeeff", schema) == []

    def test_pattern_mismatch(self):
        schema = {"type": "string", "pattern": "^clp-[a-f0-9]{12}$"}
        errs = validate("bad-id", schema)
        assert len(errs) == 1
        assert "does not match pattern" in errs[0]

    def test_pattern_skipped_for_non_string(self):
        schema = {"pattern": "^abc$"}
        assert validate(42, schema) == []


# ===================================================================
# minLength / maxLength
# ===================================================================


class TestStringLength:
    def test_minlength_valid(self):
        assert validate("abc", {"type": "string", "minLength": 3}) == []

    def test_minlength_invalid(self):
        errs = validate("ab", {"type": "string", "minLength": 3})
        assert len(errs) == 1
        assert "minLength" in errs[0]

    def test_maxlength_valid(self):
        assert validate("ab", {"type": "string", "maxLength": 5}) == []

    def test_maxlength_invalid(self):
        errs = validate("toolong", {"type": "string", "maxLength": 3})
        assert len(errs) == 1
        assert "maxLength" in errs[0]


# ===================================================================
# minimum / maximum
# ===================================================================


class TestNumericBounds:
    def test_minimum_valid(self):
        assert validate(5, {"type": "number", "minimum": 0}) == []

    def test_minimum_invalid(self):
        errs = validate(-1, {"type": "number", "minimum": 0})
        assert len(errs) == 1
        assert "minimum" in errs[0]

    def test_maximum_valid(self):
        assert validate(0.5, {"type": "number", "maximum": 1.0}) == []

    def test_maximum_invalid(self):
        errs = validate(1.5, {"type": "number", "maximum": 1.0})
        assert len(errs) == 1
        assert "maximum" in errs[0]

    def test_both_bounds(self):
        schema = {"type": "number", "minimum": 0, "maximum": 1}
        assert validate(0.5, schema) == []
        assert len(validate(-0.1, schema)) == 1
        assert len(validate(1.1, schema)) == 1


# ===================================================================
# Object: required, properties, additionalProperties
# ===================================================================


class TestObjectKeywords:
    def test_required_present(self):
        schema = {"type": "object", "required": ["a"]}
        assert validate({"a": 1}, schema) == []

    def test_required_missing(self):
        schema = {"type": "object", "required": ["a", "b"]}
        errs = validate({"a": 1}, schema)
        assert len(errs) == 1
        assert "missing required property 'b'" in errs[0]

    def test_properties_validated(self):
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
        }
        assert validate({"x": 5}, schema) == []
        errs = validate({"x": "nope"}, schema)
        assert len(errs) == 1

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": False,
        }
        assert validate({"a": 1}, schema) == []
        errs = validate({"a": 1, "b": 2}, schema)
        assert len(errs) == 1
        assert "unexpected property" in errs[0]

    def test_additional_properties_schema(self):
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": {"type": "string"},
        }
        assert validate({"k": "v"}, schema) == []
        errs = validate({"k": 42}, schema)
        assert len(errs) == 1

    def test_nested_path(self):
        schema = {
            "type": "object",
            "properties": {
                "outer": {
                    "type": "object",
                    "properties": {"inner": {"type": "integer"}},
                }
            },
        }
        errs = validate({"outer": {"inner": "wrong"}}, schema)
        assert len(errs) == 1
        assert "outer.inner" in errs[0]


# ===================================================================
# Array: minItems, maxItems, items
# ===================================================================


class TestArrayKeywords:
    def test_minitems_valid(self):
        assert validate([1, 2], {"type": "array", "minItems": 1}) == []

    def test_minitems_invalid(self):
        errs = validate([], {"type": "array", "minItems": 1})
        assert len(errs) == 1
        assert "minItems" in errs[0]

    def test_maxitems_valid(self):
        assert validate([1], {"type": "array", "maxItems": 3}) == []

    def test_maxitems_invalid(self):
        errs = validate([1, 2, 3, 4], {"type": "array", "maxItems": 3})
        assert len(errs) == 1
        assert "maxItems" in errs[0]

    def test_items_validated(self):
        schema = {"type": "array", "items": {"type": "string"}}
        assert validate(["a", "b"], schema) == []
        errs = validate(["a", 2], schema)
        assert len(errs) == 1
        assert "[1]" in errs[0]


# ===================================================================
# oneOf / anyOf
# ===================================================================


class TestCompositionKeywords:
    def test_oneof_single_match(self):
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        assert validate("hello", schema) == []

    def test_oneof_no_match(self):
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        errs = validate([], schema)
        assert len(errs) == 1
        assert "oneOf" in errs[0]

    def test_oneof_multiple_match(self):
        """Both schemas match integer -- oneOf requires exactly one."""
        schema = {
            "oneOf": [
                {"type": "number"},
                {"type": "integer"},
            ]
        }
        errs = validate(5, schema)
        assert len(errs) == 1
        assert "got 2" in errs[0]

    def test_anyof_match(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        assert validate("hello", schema) == []
        assert validate(42, schema) == []

    def test_anyof_no_match(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        errs = validate([], schema)
        assert len(errs) == 1
        assert "anyOf" in errs[0]


# ===================================================================
# Path prefix propagation
# ===================================================================


class TestPathPropagation:
    def test_root_path_empty(self):
        errs = validate(42, {"type": "string"})
        assert errs[0].startswith(": ") or "expected type" in errs[0]

    def test_custom_root_path(self):
        errs = validate(42, {"type": "string"}, path="$.root")
        assert "$.root" in errs[0]


# ===================================================================
# ValidationError
# ===================================================================


class TestValidationError:
    def test_with_path(self):
        e = ValidationError("bad value", path="a.b")
        assert str(e) == "a.b: bad value"
        assert e.path == "a.b"

    def test_without_path(self):
        e = ValidationError("bad value")
        assert str(e) == "bad value"
        assert e.path == ""


# ===================================================================
# validate_file
# ===================================================================


class TestValidateFile:
    def test_valid_file(self, tmp_path):
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                }
            )
        )
        instance_file = tmp_path / "data.json"
        instance_file.write_text(json.dumps({"name": "test"}))

        ok, errors = validate_file(instance_file, schema_file)
        assert ok is True
        assert errors == []

    def test_invalid_file(self, tmp_path):
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(
            json.dumps(
                {
                    "type": "object",
                    "required": ["name"],
                }
            )
        )
        instance_file = tmp_path / "data.json"
        instance_file.write_text(json.dumps({}))

        ok, errors = validate_file(instance_file, schema_file)
        assert ok is False
        assert len(errors) == 1

    def test_path_objects(self, tmp_path):
        """Accept both str and Path arguments."""
        schema_file = tmp_path / "s.json"
        schema_file.write_text(json.dumps({"type": "integer"}))
        instance_file = tmp_path / "d.json"
        instance_file.write_text(json.dumps(42))

        ok, errors = validate_file(str(instance_file), str(schema_file))
        assert ok is True


# ===================================================================
# validate_entry_dict -- CLP ledger entry
# ===================================================================


class TestValidateEntryDict:
    def test_valid_entry(self):
        entry = _valid_ledger_entry()
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is True, errors

    def test_missing_required_field(self):
        entry = _valid_ledger_entry()
        del entry["agent"]
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("agent" in e for e in errors)

    def test_bad_id_pattern(self):
        entry = _valid_ledger_entry(id="bad-id")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("pattern" in e for e in errors)

    def test_bad_vendor_enum(self):
        entry = _valid_ledger_entry(vendor="microsoft")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("enum" in e for e in errors)

    def test_bad_type_enum(self):
        entry = _valid_ledger_entry(type="opinion")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False

    def test_content_too_long(self):
        entry = _valid_ledger_entry(content="x" * 4097)
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("maxLength" in e for e in errors)

    def test_content_empty(self):
        entry = _valid_ledger_entry(content="")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("minLength" in e for e in errors)

    def test_bad_content_hash(self):
        entry = _valid_ledger_entry(content_hash="tooshort")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("pattern" in e for e in errors)

    def test_confidence_bounds(self):
        entry = _valid_ledger_entry(confidence=0.5)
        ok, _ = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is True

        entry_low = _valid_ledger_entry(confidence=-0.1)
        ok, errors = validate_entry_dict(entry_low, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("minimum" in e for e in errors)

        entry_high = _valid_ledger_entry(confidence=1.1)
        ok, errors = validate_entry_dict(entry_high, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("maximum" in e for e in errors)

    def test_optional_tags(self):
        entry = _valid_ledger_entry(tags=["ops", "bus"])
        ok, _ = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is True

    def test_tags_too_many(self):
        entry = _valid_ledger_entry(tags=["t"] * 11)
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("maxItems" in e for e in errors)

    def test_additional_properties_rejected(self):
        entry = _valid_ledger_entry(extra_field="nope")
        ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is False
        assert any("unexpected property" in e for e in errors)

    def test_explicit_schema(self):
        """Pass schema explicitly instead of loading from contracts/."""
        schema = {"type": "object", "required": ["id"]}
        ok, _ = validate_entry_dict({"id": "test"}, schema=schema)
        assert ok is True

    def test_supersedes_pattern(self):
        entry = _valid_ledger_entry(supersedes="clp-112233445566")
        ok, _ = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is True

        entry_bad = _valid_ledger_entry(supersedes="invalid")
        ok, errors = validate_entry_dict(entry_bad, schema=_LEDGER_SCHEMA)
        assert ok is False

    def test_assurance_level_enum(self):
        for level in ["SELF", "PEER", "VERIFIED", None]:
            entry = _valid_ledger_entry(assurance_level=level)
            ok, _ = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
            assert ok is True, f"Failed for assurance_level={level}"

    def test_evidence_nullable(self):
        entry = _valid_ledger_entry(evidence=None)
        ok, _ = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
        assert ok is True

        entry2 = _valid_ledger_entry(evidence="commit:abc123")
        ok, _ = validate_entry_dict(entry2, schema=_LEDGER_SCHEMA)
        assert ok is True


# ===================================================================
# validate_state_dict -- CLP shared state
# ===================================================================


class TestValidateStateDict:
    def test_valid_state(self):
        state = _valid_shared_state()
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is True, errors

    def test_missing_required(self):
        state = _valid_shared_state()
        del state["version"]
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is False
        assert any("version" in e for e in errors)

    def test_version_must_be_integer(self):
        state = _valid_shared_state(version="1")
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is False

    def test_version_minimum(self):
        state = _valid_shared_state(version=-1)
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is False
        assert any("minimum" in e for e in errors)

    def test_active_agents(self):
        state = _valid_shared_state(
            active_agents={
                "claude-code": {
                    "status": "active",
                    "capabilities": ["code", "review"],
                    "last_seen": "2026-03-04T12:00:00Z",
                    "vendor": "anthropic",
                    "model": "claude-opus-4-6",
                }
            }
        )
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is True, errors

    def test_claimed_files(self):
        state = _valid_shared_state(
            claimed_files={
                "services/health.py": {
                    "agent": "claude-code",
                    "claimed_at": "2026-03-04T12:00:00Z",
                    "purpose": "health probe update",
                }
            }
        )
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is True, errors

    def test_active_decisions(self):
        state = _valid_shared_state(
            active_decisions=[
                {
                    "decision_id": "d-001",
                    "question": "Which auth flow?",
                    "proposed_by": "claude-code",
                    "resolved": False,
                }
            ]
        )
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is True, errors

    def test_additional_properties_rejected(self):
        state = _valid_shared_state(rogue_field="nope")
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is False
        assert any("unexpected property" in e for e in errors)

    def test_explicit_schema(self):
        schema = {"type": "object", "required": ["version"]}
        ok, _ = validate_state_dict({"version": 1}, schema=schema)
        assert ok is True

    def test_flags_allows_arbitrary(self):
        state = _valid_shared_state(flags={"debug": True, "count": 42})
        ok, errors = validate_state_dict(state, schema=_STATE_SCHEMA)
        assert ok is True, errors


# ===================================================================
# _load_default_schema
# ===================================================================


class TestLoadDefaultSchema:
    def test_schema_not_found_raises(self):
        """FileNotFoundError when schema doesn't exist."""
        with patch("subprocess.check_output", side_effect=FileNotFoundError):
            # Also ensure fallback path doesn't exist
            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(FileNotFoundError, match="Schema file not found"):
                    validate_entry_dict({}, schema=None)

    def test_git_not_available_fallback(self):
        """Falls back to relative path when git is unavailable."""
        import subprocess

        with patch(
            "subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            # On CI, contracts/ symlink won't resolve, so use embedded schema
            entry = _valid_ledger_entry()
            ok, errors = validate_entry_dict(entry, schema=_LEDGER_SCHEMA)
            assert ok is True, errors


# ===================================================================
# Multiple errors accumulated
# ===================================================================


class TestMultipleErrors:
    def test_accumulates_errors(self):
        schema = {
            "type": "object",
            "required": ["a", "b"],
            "properties": {
                "c": {"type": "integer"},
            },
        }
        errs = validate({"c": "wrong"}, schema)
        # missing a, missing b, wrong type for c
        assert len(errs) == 3

    def test_array_multiple_bad_items(self):
        schema = {"type": "array", "items": {"type": "string"}}
        errs = validate([1, 2, 3], schema)
        assert len(errs) == 3
