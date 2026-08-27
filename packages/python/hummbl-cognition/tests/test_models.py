"""Tests for hummbl_cognition.models — LedgerEntry, SharedState, enums, helpers."""

from __future__ import annotations

import json

import pytest
from hummbl_cognition.models import (
    CANONICAL_LEDGER_SCOPES,
    CANONICAL_LEDGER_TYPES,
    VALID_VENDORS,
    AssuranceLevel,
    ColorTeam,
    IntelType,
    LedgerEntry,
    LedgerEntryType,
    LedgerScope,
    SharedState,
    _generate_entry_id,
    _is_valid_id,
    _utc_now_iso,
    compute_content_hash,
)

# ---------------------------------------------------------------------------
# ID generation / validation
# ---------------------------------------------------------------------------


class TestEntryId:
    def test_generate_entry_id_format(self) -> None:
        eid = _generate_entry_id()
        assert eid.startswith("clp-")
        assert len(eid) == 16
        # 12 hex chars after prefix
        hex_part = eid[4:]
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_generate_entry_id_uniqueness(self) -> None:
        ids = {_generate_entry_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_valid_id_standard(self) -> None:
        assert _is_valid_id("clp-abc123def456")

    def test_is_valid_id_legacy_uuid(self) -> None:
        assert _is_valid_id("12345678-1234-1234-1234-123456789abc")

    def test_is_valid_id_thoth(self) -> None:
        assert _is_valid_id("thoth-something")

    def test_is_valid_id_short_clp(self) -> None:
        assert _is_valid_id("clp-c86ca7a0")

    def test_is_valid_id_invalid(self) -> None:
        assert not _is_valid_id("invalid-id")
        assert not _is_valid_id("")
        assert not _is_valid_id("xyz-abc123def456")


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------


class TestUtcNow:
    def test_format(self) -> None:
        ts = _utc_now_iso()
        assert ts.endswith("Z")
        assert "T" in ts
        # Should be parseable
        # Replace Z with +00:00 for fromisoformat
        from datetime import datetime

        datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------


class TestComputeContentHash:
    def test_deterministic(self) -> None:
        kwargs = dict(
            agent="test-agent",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="Hello world",
        )
        h1 = compute_content_hash(**kwargs)
        h2 = compute_content_hash(**kwargs)
        assert h1 == h2

    def test_is_sha256_hex(self) -> None:
        h = compute_content_hash(
            agent="a",
            vendor="anthropic",
            model="m",
            entry_type="lesson",
            scope="project",
            content="c",
        )
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_content_different_hash(self) -> None:
        h1 = compute_content_hash(
            agent="a",
            vendor="anthropic",
            model="m",
            entry_type="lesson",
            scope="project",
            content="foo",
        )
        h2 = compute_content_hash(
            agent="a",
            vendor="anthropic",
            model="m",
            entry_type="lesson",
            scope="project",
            content="bar",
        )
        assert h1 != h2

    def test_different_agent_different_hash(self) -> None:
        h1 = compute_content_hash(
            agent="a",
            vendor="anthropic",
            model="m",
            entry_type="lesson",
            scope="project",
            content="c",
        )
        h2 = compute_content_hash(
            agent="b",
            vendor="anthropic",
            model="m",
            entry_type="lesson",
            scope="project",
            content="c",
        )
        assert h1 != h2


# ---------------------------------------------------------------------------
# LedgerEntry
# ---------------------------------------------------------------------------


class TestLedgerEntry:
    def _make_entry(self, **overrides) -> LedgerEntry:
        defaults = dict(
            agent="test-agent",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type=LedgerEntryType.LESSON,
            scope=LedgerScope.PROJECT,
            content="A valuable lesson learned",
        )
        defaults.update(overrides)
        return LedgerEntry.create(**defaults)

    def test_create_basic(self) -> None:
        entry = self._make_entry()
        assert entry.id.startswith("clp-")
        assert entry.type == "lesson"
        assert entry.scope == "project"
        assert entry.content_hash
        assert entry.verify_hash()

    def test_create_with_tags(self) -> None:
        entry = self._make_entry(tags=("python", "testing"))
        assert entry.tags == ("python", "testing")

    def test_create_with_links(self) -> None:
        entry = self._make_entry(links=("clp-aaaaaaaaaaaa",))
        assert entry.links == ("clp-aaaaaaaaaaaa",)

    def test_create_with_color_team(self) -> None:
        entry = self._make_entry(color_team="red")
        assert entry.color_team == "red"

    def test_create_with_intel_types(self) -> None:
        entry = self._make_entry(
            intel_types_consumed=("OSINT", "HUMINT"),
            intel_types_produced=("CODEINT",),
        )
        assert entry.intel_types_consumed == ("OSINT", "HUMINT")
        assert entry.intel_types_produced == ("CODEINT",)

    def test_create_with_previous_hash(self) -> None:
        ph = "a" * 64
        entry = self._make_entry(previous_hash=ph)
        assert entry.previous_hash == ph

    def test_create_with_valid_time(self) -> None:
        entry = self._make_entry(valid_time="2026-01-01T00:00:00Z")
        assert entry.valid_time == "2026-01-01T00:00:00Z"

    def test_create_with_contests(self) -> None:
        entry = self._make_entry(contests="clp-abc123def456")
        assert entry.contests == "clp-abc123def456"

    def test_invalid_vendor_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid vendor"):
            self._make_entry(vendor="invalid-vendor")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid type"):
            self._make_entry(entry_type="invalid-type")

    def test_invalid_scope_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid scope"):
            self._make_entry(scope="invalid-scope")

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValueError, match="Content must be"):
            self._make_entry(content="")

    def test_too_long_content_raises(self) -> None:
        with pytest.raises(ValueError, match="Content must be"):
            self._make_entry(content="x" * 4097)

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="Confidence"):
            self._make_entry(confidence=1.5)

    def test_confidence_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="Confidence"):
            self._make_entry(confidence=-0.1)

    def test_too_many_tags_raises(self) -> None:
        with pytest.raises(ValueError, match="Maximum 10 tags"):
            self._make_entry(tags=tuple(f"tag{i}" for i in range(11)))

    def test_too_many_links_raises(self) -> None:
        with pytest.raises(ValueError, match="Maximum 20 links"):
            self._make_entry(links=tuple(f"clp-{i:012x}" for i in range(21)))

    def test_invalid_link_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid link ID"):
            self._make_entry(links=("invalid-link-id",))

    def test_invalid_color_team_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid color_team"):
            self._make_entry(color_team="not-a-color")

    def test_invalid_intel_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid intel_types_consumed"):
            self._make_entry(intel_types_consumed=("FAKEINT",))

    def test_invalid_previous_hash_raises(self) -> None:
        with pytest.raises(ValueError, match="previous_hash"):
            self._make_entry(previous_hash="not-a-hash")

    def test_invalid_valid_time_raises(self) -> None:
        with pytest.raises(ValueError, match="valid_time"):
            self._make_entry(valid_time="2026-01-01 00:00:00")

    def test_invalid_contests_raises(self) -> None:
        with pytest.raises(ValueError, match="contests"):
            self._make_entry(contests="invalid-id")

    def test_to_dict_roundtrip(self) -> None:
        entry = self._make_entry(
            tags=("a", "b"),
            links=("clp-aaaaaaaaaaaa",),
            assurance_level="SELF",
            color_team="blue",
        )
        d = entry.to_dict()
        restored = LedgerEntry.from_dict(d)
        assert restored.id == entry.id
        assert restored.content == entry.content
        assert restored.tags == entry.tags
        assert restored.links == entry.links
        assert restored.color_team == entry.color_team

    def test_to_jsonl_roundtrip(self) -> None:
        entry = self._make_entry()
        line = entry.to_jsonl()
        # Should be valid JSON
        parsed = json.loads(line)
        assert parsed["id"] == entry.id
        # Round-trip
        restored = LedgerEntry.from_dict(parsed)
        assert restored.content == entry.content

    def test_from_dict_legacy_field_aliases(self) -> None:
        """Legacy entries with old field names should parse correctly."""
        d = {
            "entry_id": "clp-abc123def456",
            "ts": "2026-01-01T00:00:00Z",
            "agent": "legacy-agent",
            "vendor": "human",
            "model": "unknown",
            "type": "lesson",
            "scope": "project",
            "content": "Legacy content",
            "hash": "a" * 64,
        }
        entry = LedgerEntry.from_dict(d)
        assert entry.id == "clp-abc123def456"
        assert entry.timestamp == "2026-01-01T00:00:00Z"
        assert entry.content_hash == "a" * 64

    def test_from_dict_missing_vendor_defaults_human(self) -> None:
        d = {
            "id": "clp-abc123def456",
            "timestamp": "2026-01-01T00:00:00Z",
            "agent": "agent",
            "type": "lesson",
            "scope": "project",
            "content": "content",
            "content_hash": "a" * 64,
        }
        entry = LedgerEntry.from_dict(d)
        assert entry.vendor == "human"
        assert entry.model == "unknown"

    def test_verify_hash_true(self) -> None:
        entry = self._make_entry()
        assert entry.verify_hash() is True

    def test_verify_hash_false_after_tamper(self) -> None:
        entry = self._make_entry()
        # Create a new entry with different content but same hash
        d = entry.to_dict()
        d["content"] = "Tampered content"
        d["content_hash"] = entry.content_hash  # Keep old hash
        tampered = LedgerEntry.from_dict(d)
        assert tampered.verify_hash() is False

    def test_frozen_dataclass(self) -> None:
        entry = self._make_entry()
        with pytest.raises(AttributeError):
            entry.content = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SharedState
# ---------------------------------------------------------------------------


class TestSharedState:
    def test_default_state(self) -> None:
        state = SharedState()
        assert state.version == 0
        assert state.active_agents == {}
        assert state.claimed_files == {}

    def test_increment_version(self) -> None:
        state = SharedState()
        state.increment_version("agent-1")
        assert state.version == 1
        assert state.updated_by == "agent-1"
        assert state.updated_at.endswith("Z")

    def test_to_dict_roundtrip(self) -> None:
        state = SharedState(version=5, updated_by="agent-1")
        state.active_agents["agent-1"] = {"task": "testing"}
        d = state.to_dict()
        restored = SharedState.from_dict(d)
        assert restored.version == 5
        assert restored.updated_by == "agent-1"
        assert "agent-1" in restored.active_agents

    def test_to_json_roundtrip(self) -> None:
        state = SharedState(version=3)
        text = state.to_json()
        restored = SharedState.from_json(text)
        assert restored.version == 3

    def test_from_dict_defaults(self) -> None:
        restored = SharedState.from_dict({})
        assert restored.version == 0
        assert restored.active_agents == {}


# ---------------------------------------------------------------------------
# Enum / constant sanity
# ---------------------------------------------------------------------------


class TestEnums:
    def test_canonical_types_subset_of_all_types(self) -> None:
        all_types = {e.value for e in LedgerEntryType}
        assert CANONICAL_LEDGER_TYPES.issubset(all_types)

    def test_canonical_scopes_subset_of_all_scopes(self) -> None:
        all_scopes = {e.value for e in LedgerScope}
        assert CANONICAL_LEDGER_SCOPES.issubset(all_scopes)

    def test_valid_vendors_contains_known(self) -> None:
        assert "anthropic" in VALID_VENDORS
        assert "openai" in VALID_VENDORS

    def test_color_team_values(self) -> None:
        assert ColorTeam.RED.value == "red"
        assert ColorTeam.BLUE.value == "blue"

    def test_intel_type_values(self) -> None:
        assert IntelType.OSINT.value == "OSINT"
        assert IntelType.HUMINT.value == "HUMINT"

    def test_assurance_level_values(self) -> None:
        assert AssuranceLevel.SELF.value == "SELF"
        assert AssuranceLevel.VERIFIED.value == "VERIFIED"
