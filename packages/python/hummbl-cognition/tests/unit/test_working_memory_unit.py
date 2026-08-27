"""Unit tests for hummbl_cognition.working_memory.

Covers all public API, helpers, validation, edge cases, concurrency errors,
TTL expiry, namespace enforcement, promotion, stats, and atomic I/O.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from hummbl_cognition.working_memory import (
    _KEY_PATTERN,
    MAX_CONTENT_LENGTH,
    MAX_ITEMS,
    MAX_TTL_SECONDS,
    ConcurrencyError,
    WorkingMemoryItem,
    WorkingMemoryStore,
    _extract_namespace,
    _is_expired,
    _parse_iso,
    _resolve_store_path,
    _scan_value,
    _utc_now_iso,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


class TestUtcNowIso:
    def test_returns_z_suffix(self):
        result = _utc_now_iso()
        assert result.endswith("Z")

    def test_parseable_iso(self):
        result = _utc_now_iso()
        dt = _parse_iso(result)
        assert dt.tzinfo is not None


class TestParseIso:
    def test_parse_z_suffix(self):
        dt = _parse_iso("2026-03-29T12:00:00Z")
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.hour == 12
        assert dt.tzinfo is not None

    def test_parse_offset_suffix(self):
        dt = _parse_iso("2026-03-29T12:00:00+00:00")
        assert dt.year == 2026

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_iso("not-a-date")


class TestIsExpired:
    def test_not_expired(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        item = {"ttl_seconds": 3600, "expires_utc": future}
        assert _is_expired(item) is False

    def test_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        item = {"ttl_seconds": 3600, "expires_utc": past}
        assert _is_expired(item) is True

    def test_zero_ttl_never_expires(self):
        item = {"ttl_seconds": 0, "expires_utc": "2000-01-01T00:00:00Z"}
        assert _is_expired(item) is False

    def test_empty_expires_utc(self):
        item = {"ttl_seconds": 3600, "expires_utc": ""}
        assert _is_expired(item) is False

    def test_missing_expires_utc(self):
        item = {"ttl_seconds": 3600}
        assert _is_expired(item) is False

    def test_invalid_expires_utc(self):
        item = {"ttl_seconds": 3600, "expires_utc": "garbage"}
        assert _is_expired(item) is False


class TestExtractNamespace:
    def test_simple(self):
        assert _extract_namespace("agent:topic") == "agent"

    def test_multiple_colons(self):
        assert _extract_namespace("agent:topic:sub") == "agent"

    def test_no_colon_raises(self):
        with pytest.raises(ValueError, match="must contain ':'"):
            _extract_namespace("notopic")


class TestKeyPattern:
    def test_valid_keys(self):
        for key in ["agent:topic", "my-agent:my.topic", "a_1:b-2.c_3"]:
            assert _KEY_PATTERN.match(key), f"Should match: {key}"

    def test_invalid_keys(self):
        for key in ["", "notopic", ":topic", "agent:", "ag ent:topic", "agent:to pic"]:
            assert not _KEY_PATTERN.match(key), f"Should not match: {key}"


class TestResolveStorePath:
    def test_override(self, tmp_path):
        p = _resolve_store_path(tmp_path / "custom.json")
        assert p == tmp_path / "custom.json"

    def test_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("COGNITION_WORKING_MEMORY", str(tmp_path / "env.json"))
        p = _resolve_store_path()
        assert p == tmp_path / "env.json"

    def test_git_root_fallback(self, monkeypatch):
        monkeypatch.delenv("COGNITION_WORKING_MEMORY", raising=False)
        with mock.patch("subprocess.check_output", return_value="/fake/root\n"):
            p = _resolve_store_path()
            assert str(p).replace("\\", "/").startswith("/fake/root")

    def test_no_git_fallback(self, monkeypatch):
        monkeypatch.delenv("COGNITION_WORKING_MEMORY", raising=False)
        import subprocess

        with mock.patch(
            "subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            p = _resolve_store_path()
            assert "working_memory.json" in str(p)


class TestScanValue:
    def test_clean_string(self):
        _scan_value("hello world")  # should not raise

    def test_clean_dict(self):
        _scan_value({"key": "value"})

    def test_clean_list(self):
        _scan_value(["a", "b"])

    def test_nested(self):
        _scan_value({"a": [{"b": "c"}]})

    def test_non_string_passthrough(self):
        _scan_value(42)
        _scan_value(None)
        _scan_value(True)


# ---------------------------------------------------------------------------
# WorkingMemoryItem dataclass
# ---------------------------------------------------------------------------


class TestWorkingMemoryItem:
    def _make_item(self, **overrides):
        defaults = dict(
            key="agent:topic",
            value="test value",
            agent="agent",
            created_utc="2026-03-29T10:00:00Z",
            expires_utc="2026-03-29T11:00:00Z",
        )
        defaults.update(overrides)
        return WorkingMemoryItem(**defaults)

    def test_to_dict_basic(self):
        item = self._make_item()
        d = item.to_dict()
        assert d["key"] == "agent:topic"
        assert d["value"] == "test value"
        assert d["agent"] == "agent"
        assert d["version"] == 1
        assert "ttl_seconds" in d
        assert d["ttl_seconds"] == 3600

    def test_to_dict_with_metadata(self):
        item = self._make_item(metadata={"x": 1})
        d = item.to_dict()
        assert d["metadata"] == {"x": 1}

    def test_to_dict_without_metadata(self):
        item = self._make_item(metadata={})
        d = item.to_dict()
        assert "metadata" not in d

    def test_to_dict_with_promoted_to(self):
        item = self._make_item(promoted_to="clp-abc123")
        d = item.to_dict()
        assert d["promoted_to"] == "clp-abc123"

    def test_to_dict_without_promoted_to(self):
        item = self._make_item()
        d = item.to_dict()
        assert "promoted_to" not in d

    def test_to_dict_invalid_dates_default_ttl(self):
        item = self._make_item(created_utc="bad", expires_utc="bad")
        d = item.to_dict()
        assert d["ttl_seconds"] == 3600

    def test_from_dict(self):
        d = {
            "key": "a:b",
            "value": 42,
            "agent": "a",
            "created_utc": "2026-03-29T10:00:00Z",
            "expires_utc": "2026-03-29T11:00:00Z",
            "metadata": {"z": 1},
            "promoted_to": "clp-xyz",
            "version": 3,
        }
        item = WorkingMemoryItem.from_dict(d)
        assert item.key == "a:b"
        assert item.value == 42
        assert item.version == 3
        assert item.promoted_to == "clp-xyz"
        assert item.metadata == {"z": 1}

    def test_from_dict_minimal(self):
        d = {
            "key": "a:b",
            "value": "v",
            "agent": "a",
            "created_utc": "2026-03-29T10:00:00Z",
            "expires_utc": "2026-03-29T11:00:00Z",
        }
        item = WorkingMemoryItem.from_dict(d)
        assert item.metadata == {}
        assert item.promoted_to is None
        assert item.version == 1

    def test_roundtrip(self):
        item = self._make_item(metadata={"x": 1}, promoted_to="clp-abc")
        d = item.to_dict()
        item2 = WorkingMemoryItem.from_dict(d)
        assert item2.key == item.key
        assert item2.value == item.value
        assert item2.agent == item.agent
        assert item2.promoted_to == item.promoted_to


# ---------------------------------------------------------------------------
# WorkingMemoryStore
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    """Return a WorkingMemoryStore backed by a temp directory."""
    return WorkingMemoryStore(store_path=tmp_path / "wm.json")


class TestStorePut:
    def test_basic_put(self, store):
        item = store.put("agent:topic", "hello", "agent")
        assert item.key == "agent:topic"
        assert item.value == "hello"
        assert item.agent == "agent"
        assert item.version == 1

    def test_put_returns_item(self, store):
        item = store.put("agent:x", {"nested": True}, "agent")
        assert item.value == {"nested": True}

    def test_put_update_increments_version(self, store):
        store.put("agent:x", "v1", "agent")
        item2 = store.put("agent:x", "v2", "agent")
        assert item2.version == 2
        assert item2.value == "v2"

    def test_put_preserves_created_utc_on_update(self, store):
        item1 = store.put("agent:x", "v1", "agent")
        item2 = store.put("agent:x", "v2", "agent")
        assert item2.created_utc == item1.created_utc

    def test_put_invalid_key_no_colon(self, store):
        with pytest.raises(ValueError, match="Invalid key format"):
            store.put("badkey", "v", "badkey")

    def test_put_namespace_mismatch(self, store):
        with pytest.raises(ValueError, match="Namespace mismatch"):
            store.put("alice:topic", "v", "bob")

    def test_put_negative_ttl(self, store):
        with pytest.raises(ValueError, match="ttl_seconds must be >= 0"):
            store.put("agent:x", "v", "agent", ttl_seconds=-1)

    def test_put_ttl_too_large(self, store):
        with pytest.raises(ValueError, match="ttl_seconds must be <="):
            store.put("agent:x", "v", "agent", ttl_seconds=MAX_TTL_SECONDS + 1)

    def test_put_zero_ttl(self, store):
        item = store.put("agent:x", "v", "agent", ttl_seconds=0)
        assert item.expires_utc is not None
        # Should be far future
        expires = _parse_iso(item.expires_utc)
        assert expires.year > 2100

    def test_put_value_too_long(self, store):
        with pytest.raises(ValueError, match="Value too long"):
            store.put("agent:x", "a" * (MAX_CONTENT_LENGTH + 1), "agent")

    def test_put_metadata_not_dict(self, store):
        with pytest.raises(ValueError, match="metadata must be a dict"):
            store.put("agent:x", "v", "agent", metadata="bad")

    def test_put_with_metadata(self, store):
        item = store.put("agent:x", "v", "agent", metadata={"tag": "test"})
        assert item.metadata == {"tag": "test"}

    def test_put_non_serializable_value(self, store):
        with pytest.raises(ValueError, match="not JSON-serializable"):
            store.put("agent:x", object(), "agent")

    def test_put_max_items_limit(self, store):
        for i in range(MAX_ITEMS):
            store.put(f"agent:item{i}", f"v{i}", "agent")
        with pytest.raises(ValueError, match="Working memory full"):
            store.put("agent:overflow", "v", "agent")

    def test_put_update_existing_does_not_count_against_limit(self, store):
        for i in range(MAX_ITEMS):
            store.put(f"agent:item{i}", f"v{i}", "agent")
        # Update existing should work
        item = store.put("agent:item0", "updated", "agent")
        assert item.value == "updated"

    def test_put_concurrency_error(self, store):
        store.put("agent:x", "v", "agent")
        with pytest.raises(ConcurrencyError, match="Version mismatch"):
            store.put("agent:y", "v", "agent", expected_version=999)

    def test_put_expected_version_matches(self, store):
        store.put("agent:x", "v1", "agent")
        # Store version is now 1
        item = store.put("agent:y", "v2", "agent", expected_version=1)
        assert item.key == "agent:y"


class TestStoreGet:
    def test_get_existing(self, store):
        store.put("agent:x", "hello", "agent")
        item = store.get("agent:x")
        assert item is not None
        assert item.value == "hello"

    def test_get_missing(self, store):
        assert store.get("agent:nonexistent") is None

    def test_get_expired_item(self, store):
        # Put with very short TTL
        store.put("agent:x", "v", "agent", ttl_seconds=1)
        # Simulate expiry by patching the store file
        data = json.loads(store.path.read_text())
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        data["items"]["agent:x"]["expires_utc"] = past
        store.path.write_text(json.dumps(data))
        assert store.get("agent:x") is None


class TestStoreGetAll:
    def test_get_all_empty(self, store):
        assert store.get_all() == []

    def test_get_all_returns_all(self, store):
        store.put("a:x", "1", "a")
        store.put("b:y", "2", "b")
        items = store.get_all()
        assert len(items) == 2

    def test_get_all_filtered_by_agent(self, store):
        store.put("a:x", "1", "a")
        store.put("b:y", "2", "b")
        items = store.get_all(agent="a")
        assert len(items) == 1
        assert items[0].agent == "a"

    def test_get_all_excludes_expired(self, store):
        store.put("a:x", "1", "a", ttl_seconds=1)
        # Force expiry
        data = json.loads(store.path.read_text())
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        data["items"]["a:x"]["expires_utc"] = past
        store.path.write_text(json.dumps(data))
        assert store.get_all() == []


class TestStoreDelete:
    def test_delete_existing(self, store):
        store.put("agent:x", "v", "agent")
        store.delete("agent:x", "agent")
        assert store.get("agent:x") is None

    def test_delete_missing_key(self, store):
        with pytest.raises(ValueError, match="Key not found"):
            store.delete("agent:missing", "agent")

    def test_delete_wrong_owner(self, store):
        store.put("alice:x", "v", "alice")
        with pytest.raises(ValueError, match="Cannot delete"):
            store.delete("alice:x", "bob")


class TestStoreExpireStale:
    def test_expire_stale_removes_expired(self, store):
        store.put("a:x", "v", "a", ttl_seconds=1)
        # Force expiry
        data = json.loads(store.path.read_text())
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        data["items"]["a:x"]["expires_utc"] = past
        store.path.write_text(json.dumps(data))
        removed = store.expire_stale()
        assert removed == 1
        assert store.get("a:x") is None

    def test_expire_stale_keeps_valid(self, store):
        store.put("a:x", "v", "a", ttl_seconds=3600)
        removed = store.expire_stale()
        assert removed == 0
        assert store.get("a:x") is not None

    def test_expire_stale_empty_store(self, store):
        removed = store.expire_stale()
        assert removed == 0


class TestStorePromoteToLedger:
    def test_promote_basic(self, store):
        store.put("agent:x", "finding", "agent")
        result = store.promote_to_ledger("agent:x", "agent")
        assert result["entry_id"].startswith("clp-")
        assert result["agent"] == "agent"
        assert result["content"] == "finding"
        assert result["key"] == "agent:x"

    def test_promote_dict_value(self, store):
        store.put("agent:x", {"nested": True}, "agent")
        result = store.promote_to_ledger("agent:x", "agent")
        assert json.loads(result["content"]) == {"nested": True}

    def test_promote_marks_item(self, store):
        store.put("agent:x", "v", "agent")
        result = store.promote_to_ledger("agent:x", "agent")
        item = store.get("agent:x")
        assert item.promoted_to == result["entry_id"]

    def test_promote_missing_key(self, store):
        with pytest.raises(ValueError, match="Key not found"):
            store.promote_to_ledger("agent:missing", "agent")

    def test_promote_wrong_owner(self, store):
        store.put("alice:x", "v", "alice")
        with pytest.raises(ValueError, match="Cannot promote"):
            store.promote_to_ledger("alice:x", "bob")

    def test_promote_already_promoted(self, store):
        store.put("agent:x", "v", "agent")
        store.promote_to_ledger("agent:x", "agent")
        with pytest.raises(ValueError, match="already promoted"):
            store.promote_to_ledger("agent:x", "agent")


class TestStoreClear:
    def test_clear_all(self, store):
        store.put("a:x", "1", "a")
        store.put("b:y", "2", "b")
        cleared = store.clear()
        assert cleared == 2
        assert store.get_all() == []

    def test_clear_by_agent(self, store):
        store.put("a:x", "1", "a")
        store.put("b:y", "2", "b")
        cleared = store.clear(agent="a")
        assert cleared == 1
        remaining = store.get_all()
        assert len(remaining) == 1
        assert remaining[0].agent == "b"

    def test_clear_empty_store(self, store):
        cleared = store.clear()
        assert cleared == 0

    def test_clear_agent_no_match(self, store):
        store.put("a:x", "1", "a")
        cleared = store.clear(agent="nobody")
        assert cleared == 0
        assert len(store.get_all()) == 1


class TestStoreStats:
    def test_stats_empty(self, store):
        s = store.stats()
        assert s["count"] == 0
        assert s["expired_count"] == 0
        assert s["oldest"] is None
        assert s["newest"] is None
        assert s["by_agent"] == {}

    def test_stats_with_items(self, store):
        store.put("a:x", "1", "a")
        store.put("b:y", "2", "b")
        s = store.stats()
        assert s["count"] == 2
        assert s["expired_count"] == 0
        assert s["by_agent"]["a"] == 1
        assert s["by_agent"]["b"] == 1
        assert s["oldest"] is not None
        assert s["newest"] is not None
        assert s["version"] > 0

    def test_stats_counts_expired(self, store):
        store.put("a:x", "1", "a", ttl_seconds=1)
        # Force expiry
        data = json.loads(store.path.read_text())
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        data["items"]["a:x"]["expires_utc"] = past
        store.path.write_text(json.dumps(data))
        s = store.stats()
        assert s["count"] == 0
        assert s["expired_count"] == 1


# ---------------------------------------------------------------------------
# Store I/O edge cases
# ---------------------------------------------------------------------------


class TestStoreIO:
    def test_read_missing_file(self, tmp_path):
        s = WorkingMemoryStore(store_path=tmp_path / "missing.json")
        assert s.get_all() == []

    def test_read_empty_file(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text("")
        s = WorkingMemoryStore(store_path=p)
        assert s.get_all() == []

    def test_read_corrupt_json(self, tmp_path):
        p = tmp_path / "corrupt.json"
        p.write_text("{bad json")
        s = WorkingMemoryStore(store_path=p)
        assert s.get_all() == []

    def test_read_valid_json_wrong_structure(self, tmp_path):
        p = tmp_path / "wrong.json"
        p.write_text(json.dumps({"not_items": True}))
        s = WorkingMemoryStore(store_path=p)
        assert s.get_all() == []

    def test_path_property(self, tmp_path):
        p = tmp_path / "wm.json"
        s = WorkingMemoryStore(store_path=p)
        assert s.path == p

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "deep" / "nested" / "wm.json"
        s = WorkingMemoryStore(store_path=p)
        s.put("agent:x", "v", "agent")
        assert p.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions not supported on Windows")
    def test_atomic_write_permissions(self, store):
        store.put("agent:x", "v", "agent")
        mode = store.path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_atomic_write_cleanup_on_error(self, store):
        # Simulate an error during write by making json.dumps fail
        with mock.patch("json.dumps", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                store.put("agent:x", "v", "agent")
        # tmp file should be cleaned up
        tmp_path = store.path.with_suffix(".tmp")
        assert not tmp_path.exists()


class TestStoreContentScanning:
    """Verify that content scanning from ledger_writer is wired in."""

    def test_scan_blocks_credential_pattern(self, store):
        # The scan_content function from ledger_writer catches sk-<20+ alnum>
        from hummbl_cognition.working_memory import ContentScanError

        fake_key = "sk-" + "a" * 40
        with pytest.raises((ContentScanError, ValueError)):
            store.put("agent:x", f"my key is {fake_key}", "agent")

    def test_scan_blocks_metadata_injection(self, store):
        from hummbl_cognition.working_memory import ContentScanError

        fake_key = "sk-" + "b" * 40
        with pytest.raises((ContentScanError, ValueError)):
            store.put("agent:x", "clean", "agent", metadata={"note": f"key {fake_key}"})


# ---------------------------------------------------------------------------
# Concurrency / locking
# ---------------------------------------------------------------------------


class TestStoreLocking:
    @pytest.mark.skipif(sys.platform == "win32", reason="flock is POSIX-only")
    def test_locked_write_uses_flock(self, store):
        """Verify flock is called during writes (on POSIX)."""
        import fcntl as _fcntl

        original_flock = _fcntl.flock
        calls = []

        def tracking_flock(fd, op):
            calls.append(op)
            return original_flock(fd, op)

        with mock.patch.object(_fcntl, "flock", side_effect=tracking_flock):
            store.put("agent:x", "v", "agent")

        # Should have LOCK_EX and LOCK_UN
        assert _fcntl.LOCK_EX in calls
        assert _fcntl.LOCK_UN in calls

    def test_locked_write_msvcrt_path(self, store):
        """Test the msvcrt code path by mocking fcntl away."""
        mock_msvcrt = mock.MagicMock()

        with (
            mock.patch("hummbl_cognition.working_memory.fcntl", None),
            mock.patch("hummbl_cognition.working_memory.msvcrt", mock_msvcrt),
        ):
            store.put("agent:x", "v", "agent")

        assert mock_msvcrt.locking.called
