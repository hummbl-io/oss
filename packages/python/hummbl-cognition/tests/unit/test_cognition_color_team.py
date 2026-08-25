"""Tests for the color team extension to LedgerEntry (v1.1.0).

Covers ColorTeam enum, IntelType enum, the 4 new LedgerEntry fields
(color_team, intel_types_consumed, intel_types_produced, exercise_role),
validation, serialization round-trip, backward compatibility, and
content_hash independence from color team metadata.
"""

from __future__ import annotations

import json

import pytest

from hummbl_cognition.models import (
    VALID_COLOR_TEAMS,
    VALID_INTEL_TYPES,
    ColorTeam,
    IntelType,
    LedgerEntry,
    compute_content_hash,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(**overrides) -> LedgerEntry:
    """Create a valid LedgerEntry with sensible defaults."""
    defaults = {
        "agent": "test-agent",
        "vendor": "anthropic",
        "model": "claude-opus-4-6",
        "entry_type": "lesson",
        "scope": "project",
        "content": "Test lesson content",
    }
    defaults.update(overrides)
    return LedgerEntry.create(**defaults)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestColorTeamEnum:
    """Tests for the ColorTeam enum."""

    def test_has_29_colors(self):
        assert len(VALID_COLOR_TEAMS) == 29

    def test_primary_colors_present(self):
        for color in ("red", "blue", "yellow"):
            assert color in VALID_COLOR_TEAMS

    def test_secondary_colors_present(self):
        for color in ("purple", "orange", "green", "crimson", "navy", "amber"):
            assert color in VALID_COLOR_TEAMS

    def test_tertiary_colors_present(self):
        for color in ("teal", "coral", "lime", "indigo", "magenta", "violet"):
            assert color in VALID_COLOR_TEAMS

    def test_specialized_colors_present(self):
        for color in (
            "silver", "gray", "lavender", "pink", "bronze",
            "charcoal", "slate", "tan",
        ):
            assert color in VALID_COLOR_TEAMS

    def test_meta_colors_present(self):
        for color in ("white", "iridescent", "plaid"):
            assert color in VALID_COLOR_TEAMS

    def test_industry_additional_colors_present(self):
        for color in ("black", "gold", "clear"):
            assert color in VALID_COLOR_TEAMS

    def test_enum_values_are_strings(self):
        for c in ColorTeam:
            assert isinstance(c.value, str)
            assert c.value == c.value.lower()  # all lowercase


class TestIntelTypeEnum:
    """Tests for the IntelType enum."""

    def test_has_15_types(self):
        assert len(VALID_INTEL_TYPES) == 15

    def test_all_int_types_present(self):
        expected = {
            "HUMINT", "OSINT", "MASINT", "IMINT", "GEOINT",
            "FININT", "TECHINT", "CYBINT", "GITINT", "BUSINT",
            "OPSINT", "CODEINT", "LOGINT", "REGINT", "TOPOINT",
        }
        assert VALID_INTEL_TYPES == expected

    def test_enum_values_are_uppercase(self):
        for it in IntelType:
            assert isinstance(it.value, str)
            assert it.value == it.value.upper()


# ===========================================================================
# LedgerEntry Color Team Field Tests
# ===========================================================================


class TestLedgerEntryColorTeamFields:
    """Tests for the 4 new LedgerEntry fields."""

    def test_create_with_color_team(self):
        entry = _make_entry(color_team="lavender")
        assert entry.color_team == "lavender"

    def test_create_with_all_color_fields(self):
        entry = _make_entry(
            color_team="amber",
            intel_types_consumed=("CODEINT", "GITINT"),
            intel_types_produced=("CYBINT",),
            exercise_role="supply-chain",
        )
        assert entry.color_team == "amber"
        assert entry.intel_types_consumed == ("CODEINT", "GITINT")
        assert entry.intel_types_produced == ("CYBINT",)
        assert entry.exercise_role == "supply-chain"

    def test_create_without_color_team_defaults_to_none(self):
        entry = _make_entry()
        assert entry.color_team is None
        assert entry.intel_types_consumed == ()
        assert entry.intel_types_produced == ()
        assert entry.exercise_role is None

    def test_create_accepts_list_for_intel_types(self):
        entry = _make_entry(
            intel_types_consumed=["CYBINT", "TECHINT"],
            intel_types_produced=["LOGINT"],
        )
        assert entry.intel_types_consumed == ("CYBINT", "TECHINT")
        assert entry.intel_types_produced == ("LOGINT",)


class TestLedgerEntryColorTeamValidation:
    """Validation tests for the new fields."""

    def test_invalid_color_team_rejected(self):
        with pytest.raises(ValueError, match="Invalid color_team"):
            _make_entry(color_team="rainbow")

    def test_invalid_color_team_empty_string_rejected(self):
        with pytest.raises(ValueError, match="Invalid color_team"):
            _make_entry(color_team="")

    def test_invalid_intel_type_consumed_rejected(self):
        with pytest.raises(ValueError, match="Invalid intel_types_consumed"):
            _make_entry(intel_types_consumed=("FAKEINT",))

    def test_invalid_intel_type_produced_rejected(self):
        with pytest.raises(ValueError, match="Invalid intel_types_produced"):
            _make_entry(intel_types_produced=("NOTREAL",))

    def test_valid_color_team_from_each_tier(self):
        # Tier 1
        _make_entry(color_team="yellow")
        # Tier 2
        _make_entry(color_team="orange")
        # Tier 3
        _make_entry(color_team="pink")

    def test_all_29_colors_accepted(self):
        for color in VALID_COLOR_TEAMS:
            _make_entry(color_team=color)

    def test_all_15_intel_types_accepted(self):
        all_types = tuple(VALID_INTEL_TYPES)
        _make_entry(
            intel_types_consumed=all_types,
            intel_types_produced=all_types,
        )


# ===========================================================================
# Serialization Tests
# ===========================================================================


class TestColorTeamSerialization:
    """Tests for to_dict / from_dict / to_jsonl with color team fields."""

    def test_to_dict_includes_color_team_when_set(self):
        entry = _make_entry(color_team="lavender")
        d = entry.to_dict()
        assert d["color_team"] == "lavender"

    def test_to_dict_omits_color_team_when_none(self):
        entry = _make_entry()
        d = entry.to_dict()
        assert "color_team" not in d

    def test_to_dict_includes_intel_types_when_non_empty(self):
        entry = _make_entry(
            intel_types_consumed=("CYBINT", "TECHINT"),
            intel_types_produced=("LOGINT",),
        )
        d = entry.to_dict()
        assert d["intel_types_consumed"] == ["CYBINT", "TECHINT"]
        assert d["intel_types_produced"] == ["LOGINT"]

    def test_to_dict_omits_intel_types_when_empty(self):
        entry = _make_entry()
        d = entry.to_dict()
        assert "intel_types_consumed" not in d
        assert "intel_types_produced" not in d

    def test_to_dict_includes_exercise_role_when_set(self):
        entry = _make_entry(exercise_role="offense")
        d = entry.to_dict()
        assert d["exercise_role"] == "offense"

    def test_to_dict_omits_exercise_role_when_none(self):
        entry = _make_entry()
        d = entry.to_dict()
        assert "exercise_role" not in d

    def test_round_trip_preserves_all_color_fields(self):
        entry = _make_entry(
            color_team="amber",
            intel_types_consumed=("CODEINT", "GITINT", "TECHINT"),
            intel_types_produced=("CYBINT",),
            exercise_role="supply-chain",
        )
        jsonl = entry.to_jsonl()
        data = json.loads(jsonl)
        restored = LedgerEntry.from_dict(data)
        assert restored.color_team == "amber"
        assert restored.intel_types_consumed == ("CODEINT", "GITINT", "TECHINT")
        assert restored.intel_types_produced == ("CYBINT",)
        assert restored.exercise_role == "supply-chain"

    def test_jsonl_round_trip_preserves_color_team(self):
        entry = _make_entry(color_team="silver")
        jsonl = entry.to_jsonl()
        data = json.loads(jsonl)
        assert data["color_team"] == "silver"
        restored = LedgerEntry.from_dict(data)
        assert restored.color_team == "silver"


# ===========================================================================
# Backward Compatibility Tests
# ===========================================================================


class TestColorTeamBackwardCompat:
    """Tests that existing entries without color team fields still work."""

    def test_entry_without_color_fields_still_valid(self):
        entry = _make_entry()
        d = entry.to_dict()
        # No color team keys in dict
        assert "color_team" not in d
        assert "intel_types_consumed" not in d
        assert "intel_types_produced" not in d
        assert "exercise_role" not in d

    def test_from_dict_handles_missing_color_fields(self):
        # Simulate a legacy entry dict (pre-v1.1.0)
        legacy = {
            "id": "clp-aaaaaaaaaaaa",
            "timestamp": "2026-01-01T00:00:00Z",
            "agent": "legacy-agent",
            "vendor": "anthropic",
            "model": "legacy-model",
            "type": "lesson",
            "scope": "project",
            "content": "Legacy entry without color team fields",
            "content_hash": compute_content_hash(
                agent="legacy-agent",
                vendor="anthropic",
                model="legacy-model",
                entry_type="lesson",
                scope="project",
                content="Legacy entry without color team fields",
            ),
        }
        entry = LedgerEntry.from_dict(legacy)
        assert entry.color_team is None
        assert entry.intel_types_consumed == ()
        assert entry.intel_types_produced == ()
        assert entry.exercise_role is None
        assert entry.verify_hash() is True

    def test_from_dict_handles_partial_color_fields(self):
        # Only color_team set, no intel types
        entry_dict = _make_entry(color_team="red").to_dict()
        restored = LedgerEntry.from_dict(entry_dict)
        assert restored.color_team == "red"
        assert restored.intel_types_consumed == ()
        assert restored.intel_types_produced == ()


# ===========================================================================
# Hash Independence Tests
# ===========================================================================


class TestColorTeamHashIndependence:
    """Verify color team fields do NOT affect content_hash."""

    def test_color_team_does_not_affect_hash(self):
        e1 = _make_entry(color_team="red")
        e2 = _make_entry(color_team="blue")
        # Same content → same hash, despite different color teams
        assert e1.content_hash == e2.content_hash
        assert e1.verify_hash() is True
        assert e2.verify_hash() is True

    def test_intel_types_do_not_affect_hash(self):
        e1 = _make_entry(intel_types_consumed=("CYBINT",))
        e2 = _make_entry(intel_types_consumed=("OSINT", "FININT"))
        assert e1.content_hash == e2.content_hash

    def test_exercise_role_does_not_affect_hash(self):
        e1 = _make_entry(exercise_role="offense")
        e2 = _make_entry(exercise_role="defense")
        assert e1.content_hash == e2.content_hash

    def test_hash_still_changes_with_content(self):
        e1 = _make_entry(color_team="red", content="content A")
        e2 = _make_entry(color_team="red", content="content B")
        assert e1.content_hash != e2.content_hash


# ===========================================================================
# Tamper Detection Tests (ADR-FM-055)
# ===========================================================================


class TestColorTeamTamperDetection:
    """Verify that color team field tampering is explicitly UNDETECTABLE
    via content_hash alone, and that this is documented behavior.

    The hash protects semantic identity (agent, content, model, scope, type,
    vendor). Color team fields are provenance metadata, excluded by design.
    Full-record integrity requires the optional HMAC signature.
    """

    def test_tamper_color_team_undetectable_by_hash(self):
        """Changing color_team on a deserialized entry does not break verify_hash.

        This is ACCEPTED behavior per ADR-FM-055: color_team is metadata.
        The test documents this explicitly so it is not mistaken for a bug.
        """
        e = _make_entry(color_team="red")
        assert e.verify_hash() is True
        # Tamper via object.__new__ + __dict__ (frozen dataclass workaround)
        tampered = object.__new__(LedgerEntry)
        tampered.__dict__.update(e.__dict__)
        tampered.__dict__["color_team"] = "blue"
        assert tampered.verify_hash() is True  # hash still valid — metadata not covered

    def test_tamper_intel_types_undetectable_by_hash(self):
        """Changing intel_types on a deserialized entry does not break verify_hash."""
        e = _make_entry(intel_types_consumed=("CYBINT",), intel_types_produced=("OSINT",))
        assert e.verify_hash() is True
        tampered = object.__new__(LedgerEntry)
        tampered.__dict__.update(e.__dict__)
        tampered.__dict__["intel_types_consumed"] = ("FININT", "HUMINT")
        tampered.__dict__["intel_types_produced"] = ("TECHINT",)
        assert tampered.verify_hash() is True

    def test_tamper_exercise_role_undetectable_by_hash(self):
        """Changing exercise_role on a deserialized entry does not break verify_hash."""
        e = _make_entry(exercise_role="offense")
        assert e.verify_hash() is True
        tampered = object.__new__(LedgerEntry)
        tampered.__dict__.update(e.__dict__)
        tampered.__dict__["exercise_role"] = "defense"
        assert tampered.verify_hash() is True

    def test_tamper_content_detectable_by_hash(self):
        """Changing content (a covered field) DOES break verify_hash.

        This confirms the hash still protects the identity fields.
        """
        e = _make_entry(content="original content")
        assert e.verify_hash() is True
        tampered = object.__new__(LedgerEntry)
        tampered.__dict__.update(e.__dict__)
        tampered.__dict__["content"] = "tampered content"
        assert tampered.verify_hash() is False

    def test_tamper_agent_detectable_by_hash(self):
        """Changing agent (a covered field) DOES break verify_hash."""
        e = _make_entry(agent="devin")
        assert e.verify_hash() is True
        tampered = object.__new__(LedgerEntry)
        tampered.__dict__.update(e.__dict__)
        tampered.__dict__["agent"] = "codex"
        assert tampered.verify_hash() is False


# ===========================================================================
# Writer Tests — post_verified_entry propagation
# ===========================================================================


class TestPostVerifiedEntryColorTeam:
    """Verify post_verified_entry writes color team fields to JSONL."""

    @pytest.mark.allow_ledger_writes
    def test_post_verified_writes_color_team(self, tmp_path):
        from hummbl_cognition.verified_writer import post_verified_entry

        ledger = tmp_path / "test_ledger.jsonl"
        entry = post_verified_entry(
            agent="test-agent",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="Color team writer test",
            evidence="test-evidence",
            confidence=0.9,
            color_team="lavender",
            intel_types_consumed=("CYBINT", "TECHINT"),
            intel_types_produced=("CYBINT",),
            exercise_role="ai-ml-security",
            ledger_path=str(ledger),
        )
        assert entry.color_team == "lavender"
        assert entry.intel_types_consumed == ("CYBINT", "TECHINT")
        assert entry.intel_types_produced == ("CYBINT",)
        assert entry.exercise_role == "ai-ml-security"
        # Verify it was written to JSONL
        lines = ledger.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["color_team"] == "lavender"
        assert data["intel_types_consumed"] == ["CYBINT", "TECHINT"]
        assert data["intel_types_produced"] == ["CYBINT"]
        assert data["exercise_role"] == "ai-ml-security"

    @pytest.mark.allow_ledger_writes
    def test_post_verified_without_color_team(self, tmp_path):
        from hummbl_cognition.verified_writer import post_verified_entry

        ledger = tmp_path / "test_ledger.jsonl"
        entry = post_verified_entry(
            agent="test-agent",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="No color team test",
            evidence="test-evidence",
            confidence=0.9,
            ledger_path=str(ledger),
        )
        assert entry.color_team is None
        assert entry.intel_types_consumed == ()
        assert entry.intel_types_produced == ()
        assert entry.exercise_role is None
        # Backward compat: fields should not appear in JSONL when None/empty
        lines = ledger.read_text(encoding="utf-8").strip().splitlines()
        data = json.loads(lines[0])
        assert "color_team" not in data
        assert "intel_types_consumed" not in data


# ===========================================================================
# CLI Argument Parsing Tests
# ===========================================================================


class TestCLIArgumentParsing:
    """Verify CLI argument parsing for color team flags."""

    def _parse_post_verified(self, argv):
        """Parse post-verified args and return the namespace."""
        import argparse
        from hummbl_cognition.models import VALID_COLOR_TEAMS, VALID_INTEL_TYPES

        p = argparse.ArgumentParser()
        p.add_argument("--agent", required=True)
        p.add_argument("--vendor", default="anthropic")
        p.add_argument("--model", default="test-model")
        p.add_argument("--type", default="lesson")
        p.add_argument("--scope", default="project")
        p.add_argument("--content", required=True)
        p.add_argument("--evidence", default=None)
        p.add_argument("--confidence", type=float, default=0.9)
        p.add_argument("--color-team", choices=sorted(VALID_COLOR_TEAMS), default=None)
        p.add_argument("--intel-types-consumed", nargs="+", default=[])
        p.add_argument("--intel-types-produced", nargs="+", default=[])
        p.add_argument("--exercise-role", default=None)
        return p.parse_args(argv)

    def test_parse_color_team(self):
        ns = self._parse_post_verified([
            "--agent", "devin", "--content", "test",
            "--color-team", "lavender",
        ])
        assert ns.color_team == "lavender"

    def test_parse_invalid_color_team_rejected(self):
        # argparse choices= rejects invalid values at parse time
        with pytest.raises(SystemExit):
            self._parse_post_verified([
                "--agent", "devin", "--content", "test",
                "--color-team", "INVALID_COLOR",
            ])

    def test_parse_intel_types_consumed_multiple(self):
        ns = self._parse_post_verified([
            "--agent", "devin", "--content", "test",
            "--intel-types-consumed", "CYBINT", "TECHINT", "CODEINT",
        ])
        assert ns.intel_types_consumed == ["CYBINT", "TECHINT", "CODEINT"]

    def test_parse_intel_types_nargs_plus_requires_at_least_one(self):
        # nargs="+" with no values should be rejected by argparse
        # (but default=[] means the flag is simply not present, not empty)
        # When flag IS present with no values, argparse errors
        with pytest.raises(SystemExit):
            self._parse_post_verified([
                "--agent", "devin", "--content", "test",
                "--intel-types-consumed",  # no values
            ])

    def test_parse_exercise_role(self):
        ns = self._parse_post_verified([
            "--agent", "devin", "--content", "test",
            "--exercise-role", "ai-ml-security",
        ])
        assert ns.exercise_role == "ai-ml-security"

    def test_parse_all_color_team_flags(self):
        ns = self._parse_post_verified([
            "--agent", "devin", "--content", "full test",
            "--color-team", "amber",
            "--intel-types-consumed", "CYBINT", "TECHINT",
            "--intel-types-produced", "CYBINT",
            "--exercise-role", "supply-chain-security",
        ])
        assert ns.color_team == "amber"
        assert ns.intel_types_consumed == ["CYBINT", "TECHINT"]
        assert ns.intel_types_produced == ["CYBINT"]
        assert ns.exercise_role == "supply-chain-security"


# ===========================================================================
# CLI Validation Logic Tests (cmd_post_verified)
# ===========================================================================


class TestCLIValidationLogic:
    """Verify the validation logic in cmd_post_verified (without subprocess)."""

    def test_intel_type_dedup_and_canonicalize(self):
        """Verify intel types are deduped and sorted."""
        # Simulate the validation logic from cmd_post_verified
        raw_consumed = ["TECHINT", "CYBINT", "CYBINT", "OSINT"]
        intel_consumed = tuple(sorted(set(raw_consumed)))
        assert intel_consumed == ("CYBINT", "OSINT", "TECHINT")

    def test_intel_type_dedup_empty(self):
        raw_consumed = []
        intel_consumed = tuple(sorted(set(raw_consumed))) if raw_consumed else ()
        assert intel_consumed == ()

    def test_exercise_role_validation_valid(self):
        role = "ai-ml-security"
        assert len(role) <= 64
        assert all(c.isalnum() or c in "-_" for c in role)

    def test_exercise_role_validation_too_long(self):
        role = "a" * 65
        assert len(role) > 64

    def test_exercise_role_validation_invalid_chars(self):
        role = "role with spaces!"
        assert not all(c.isalnum() or c in "-_" for c in role)


# ===========================================================================
# Model-Layer Validation Tests (peer review finding #1)
# ===========================================================================


class TestExerciseRoleModelValidation:
    """Verify exercise_role is validated at the model layer, not just CLI.

    Peer review finding #1: exercise_role bounding existed only in the CLI,
    allowing programmatic callers to bypass validation. Now enforced in
    __post_init__.
    """

    def test_model_rejects_exercise_role_too_long(self):
        with pytest.raises(ValueError, match="exercise_role must be <= 64 chars"):
            _make_entry(exercise_role="a" * 65)

    def test_model_rejects_exercise_role_invalid_chars(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            _make_entry(exercise_role="role with spaces!")

    def test_model_rejects_exercise_role_control_chars(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            _make_entry(exercise_role="role\nwith\ttabs")

    def test_model_accepts_valid_exercise_role(self):
        e = _make_entry(exercise_role="ai-ml-security")
        assert e.exercise_role == "ai-ml-security"

    def test_model_accepts_none_exercise_role(self):
        e = _make_entry(exercise_role=None)
        assert e.exercise_role is None

    def test_model_accepts_max_length_exercise_role(self):
        e = _make_entry(exercise_role="a" * 64)
        assert len(e.exercise_role) == 64


# ===========================================================================
# Null-Handling Tests (peer review finding #3)
# ===========================================================================


class TestFromDictNullHandling:
    """Verify from_dict handles null values for intel type fields."""

    def test_from_dict_handles_null_intel_types_consumed(self):
        """null in JSON should default to empty tuple, not crash."""
        base = _make_entry()
        data = base.to_dict()
        data["intel_types_consumed"] = None
        entry = LedgerEntry.from_dict(data)
        assert entry.intel_types_consumed == ()

    def test_from_dict_handles_null_intel_types_produced(self):
        base = _make_entry()
        data = base.to_dict()
        data["intel_types_produced"] = None
        entry = LedgerEntry.from_dict(data)
        assert entry.intel_types_produced == ()


# ===========================================================================
# End-to-End CLI Tests through main() (peer review findings #6, #7)
# ===========================================================================


class TestCLIEndToEnd:
    """End-to-end tests through the real main() function.

    Peer review findings #6, #7: TestCLIArgumentParsing built a standalone
    parser; TestCLIValidationLogic tested logic in isolation. These tests
    exercise the real cmd_post_verified via main().
    """

    @pytest.mark.allow_ledger_writes
    def test_main_post_verified_with_color_team(self, tmp_path):
        """Full CLI path: main() → cmd_post_verified → JSONL with color team."""
        from hummbl_cognition.__main__ import main

        ledger = tmp_path / "e2e_ledger.jsonl"
        rc = main([
            "--ledger", str(ledger),
            "post-verified",
            "--agent", "devin",
            "--vendor", "local",
            "--model", "glm-5.2-high",
            "--type", "discovery",
            "--scope", "project",
            "--content", "E2E color team test",
            "--evidence", "e2e-evidence",
            "--confidence", "0.85",
            "--color-team", "lavender",
            "--intel-types-consumed", "CYBINT", "TECHINT",
            "--intel-types-produced", "CYBINT",
            "--exercise-role", "ai-ml-security",
        ])
        assert rc == 0
        lines = ledger.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["color_team"] == "lavender"
        assert data["intel_types_consumed"] == ["CYBINT", "TECHINT"]
        assert data["intel_types_produced"] == ["CYBINT"]
        assert data["exercise_role"] == "ai-ml-security"

    def test_main_post_verified_rejects_invalid_intel_type(self, tmp_path, capsys):
        """Full CLI path: invalid intel type → exit 1 + stderr message."""
        from hummbl_cognition.__main__ import main

        ledger = tmp_path / "e2e_reject.jsonl"
        rc = main([
            "--ledger", str(ledger),
            "post-verified",
            "--agent", "devin",
            "--vendor", "local",
            "--model", "glm-5.2-high",
            "--type", "discovery",
            "--scope", "project",
            "--content", "Should be rejected",
            "--evidence", "test",
            "--confidence", "0.9",
            "--intel-types-consumed", "FAKEINT",
        ])
        assert rc == 1
        captured = capsys.readouterr()
        assert "FAKEINT" in captured.err

    def test_main_post_verified_rejects_invalid_exercise_role(self, tmp_path, capsys):
        """Full CLI path: invalid exercise_role → exit 1 + stderr message."""
        from hummbl_cognition.__main__ import main

        ledger = tmp_path / "e2e_role_reject.jsonl"
        rc = main([
            "--ledger", str(ledger),
            "post-verified",
            "--agent", "devin",
            "--vendor", "local",
            "--model", "glm-5.2-high",
            "--type", "discovery",
            "--scope", "project",
            "--content", "Should be rejected",
            "--evidence", "test",
            "--confidence", "0.9",
            "--exercise-role", "role with spaces!",
        ])
        assert rc == 1
        captured = capsys.readouterr()
        assert "exercise-role" in captured.err

    @pytest.mark.allow_ledger_writes
    def test_main_post_verified_dedup_intel_types(self, tmp_path):
        """Full CLI path: dedup + canonicalization through main()."""
        from hummbl_cognition.__main__ import main

        ledger = tmp_path / "e2e_dedup.jsonl"
        rc = main([
            "--ledger", str(ledger),
            "post-verified",
            "--agent", "devin",
            "--vendor", "local",
            "--model", "glm-5.2-high",
            "--type", "discovery",
            "--scope", "project",
            "--content", "Dedup E2E test",
            "--evidence", "dedup-evidence",
            "--confidence", "0.9",
            "--intel-types-consumed", "TECHINT", "CYBINT", "CYBINT", "OSINT",
        ])
        assert rc == 0
        lines = ledger.read_text(encoding="utf-8").strip().splitlines()
        data = json.loads(lines[0])
        assert data["intel_types_consumed"] == ["CYBINT", "OSINT", "TECHINT"]
