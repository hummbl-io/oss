"""Tests for governance_bus module.

Tests GovernanceEntry, GovernanceBus, and audit log operations
with mocked filesystem and IDP feature flag.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from idp_spec.governance_bus import (
    DEFAULT_RETENTION_DAYS,
    IDP_E_AMENDMENT_TARGET_MISSING,
    IDP_E_EVIDENCE_REQUIRED,
    IDP_E_VERIFICATION_REF_INVALID,
    GovernanceBus,
    GovernanceEntry,
    _is_idp_enabled,
    append_audit_entry,
    get_governance_bus,
    query_intent,
)

_TEST_SECRET = b"test-governance-bus-secret"


def _test_sig(data: dict) -> str:
    """Generate a test HMAC-SHA256 signature for governance bus entries."""
    import json as _json
    payload = _json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hmac.new(_TEST_SECRET, payload.encode(), hashlib.sha256).hexdigest()


class TestIsIdpEnabled:
    """Test _is_idp_enabled function."""

    def test_enabled_when_true(self):
        """Should return True when ENABLE_IDP=true."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            assert _is_idp_enabled() is True

    def test_disabled_when_false(self):
        """Should return False when ENABLE_IDP=false."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            assert _is_idp_enabled() is False

    def test_enabled_when_missing(self):
        """Should return True when ENABLE_IDP not set (default enabled)."""
        with patch.dict(os.environ, {}, clear=True):
            assert _is_idp_enabled() is True

    def test_case_insensitive(self):
        """Should be case insensitive."""
        with patch.dict(os.environ, {"ENABLE_IDP": "TRUE"}):
            assert _is_idp_enabled() is True
        with patch.dict(os.environ, {"ENABLE_IDP": "True"}):
            assert _is_idp_enabled() is True


class TestGovernanceEntry:
    """Test GovernanceEntry dataclass."""

    def test_creation(self):
        """Should create entry with all fields."""
        entry = GovernanceEntry(
            timestamp="2026-02-17T10:00:00Z",
            entry_id="uuid-123",
            intent_id="intent-456",
            task_id="task-789",
            tuple_type="DCT",
            tuple_data={"key": "value"},
            signature="sig-abc",
        )

        assert entry.timestamp == "2026-02-17T10:00:00Z"
        assert entry.entry_id == "uuid-123"
        assert entry.intent_id == "intent-456"
        assert entry.tuple_type == "DCT"
        assert entry.tuple_data == {"key": "value"}
        assert entry.signature == "sig-abc"

    def test_creation_without_signature(self):
        """Should create entry without signature."""
        entry = GovernanceEntry(
            timestamp="2026-02-17T10:00:00Z",
            entry_id="uuid-123",
            intent_id="intent-456",
            task_id="task-789",
            tuple_type="SYSTEM",
            tuple_data={"event": "test"},
        )

        assert entry.signature is None

    def test_to_jsonl(self):
        """Should serialize to JSONL."""
        entry = GovernanceEntry(
            timestamp="2026-02-17T10:00:00Z",
            entry_id="uuid-123",
            intent_id="intent-456",
            task_id="task-789",
            tuple_type="DCT",
            tuple_data={"key": "value"},
            signature="sig-abc",
        )

        jsonl = entry.to_jsonl()
        data = json.loads(jsonl)

        assert data["timestamp"] == "2026-02-17T10:00:00Z"
        assert data["entry_id"] == "uuid-123"
        assert data["tuple_type"] == "DCT"
        assert data["tuple_data"] == {"key": "value"}
        assert data["signature"] == "sig-abc"

    def test_to_jsonl_sorts_keys(self):
        """Should sort keys in JSONL output."""
        entry = GovernanceEntry(
            timestamp="2026-02-17T10:00:00Z",
            entry_id="uuid-123",
            intent_id="intent-456",
            task_id="task-789",
            tuple_type="DCT",
            tuple_data={"z": 1, "a": 2},
        )

        jsonl = entry.to_jsonl()

        # Keys should be sorted alphabetically
        assert jsonl.index('"entry_id"') < jsonl.index('"intent_id"')
        assert jsonl.index('"intent_id"') < jsonl.index('"signature"')

    def test_from_dict(self):
        """Should deserialize from dict."""
        data = {
            "timestamp": "2026-02-17T10:00:00Z",
            "entry_id": "uuid-123",
            "intent_id": "intent-456",
            "task_id": "task-789",
            "tuple_type": "DCT",
            "tuple_data": {"key": "value"},
            "signature": "sig-abc",
        }

        entry = GovernanceEntry.from_dict(data)

        assert entry.timestamp == "2026-02-17T10:00:00Z"
        assert entry.entry_id == "uuid-123"
        assert entry.signature == "sig-abc"

    def test_from_dict_without_signature(self):
        """Should deserialize without signature field."""
        data = {
            "timestamp": "2026-02-17T10:00:00Z",
            "entry_id": "uuid-123",
            "intent_id": "intent-456",
            "task_id": "task-789",
            "tuple_type": "SYSTEM",
            "tuple_data": {},
        }

        entry = GovernanceEntry.from_dict(data)

        assert entry.signature is None

    def test_roundtrip(self):
        """Should roundtrip through to_jsonl and from_dict."""
        original = GovernanceEntry(
            timestamp="2026-02-17T10:00:00Z",
            entry_id="uuid-123",
            intent_id="intent-456",
            task_id="task-789",
            tuple_type="DCT",
            tuple_data={"key": "value"},
            signature="sig-abc",
        )

        jsonl = original.to_jsonl()
        data = json.loads(jsonl)
        restored = GovernanceEntry.from_dict(data)

        assert original == restored


class TestGovernanceBusInit:
    """Test GovernanceBus initialization."""

    def test_default_init(self, tmp_path: Path):
        """Should initialize with default settings."""
        bus = GovernanceBus(base_dir=tmp_path / "governance")

        assert bus._base_dir == tmp_path / "governance"
        assert bus._retention_days == DEFAULT_RETENTION_DAYS
        assert bus._enable_async is False
        assert bus._lock is not None

    def test_custom_init(self, tmp_path: Path):
        """Should initialize with custom settings."""
        bus = GovernanceBus(
            base_dir=tmp_path / "custom",
            retention_days=30,
            enable_async=True,
        )

        assert bus._retention_days == 30
        assert bus._enable_async is True

    def test_creates_directory(self, tmp_path: Path):
        """Should create directory if not exists."""
        gov_dir = tmp_path / "new_governance"

        GovernanceBus(base_dir=gov_dir)

        assert gov_dir.exists()

    def test_default_directory(self):
        """Should use default path when none provided."""
        bus = GovernanceBus()

        assert "idp-spec" in bus._base_dir.as_posix() and "governance" in bus._base_dir.as_posix()


class TestGovernanceBusAppend:
    """Test GovernanceBus.append() method."""

    def test_append_sync_success(self, tmp_path: Path):
        """Should append entry synchronously."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"test": "data"}
            success, error = bus.append(
                intent_id="intent-123",
                task_id="task-456",
                tuple_type="DCT",
                tuple_data=td,
                signature=_test_sig(td),
            )

            assert success is True
            assert error is None

    def test_append_when_disabled(self, tmp_path: Path):
        """Should silently succeed when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            success, error = bus.append(
                intent_id="intent-123",
                task_id="task-456",
                tuple_type="DCT",
                tuple_data={"test": "data"},
            )

            assert success is True
            assert error is None

    def test_append_creates_file(self, tmp_path: Path):
        """Should create log file with entry."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"test": "data"}
            bus.append(
                intent_id="intent-123",
                task_id="task-456",
                tuple_type="DCT",
                tuple_data=td,
                signature=_test_sig(td),
            )

            # Check file was created
            log_files = list((tmp_path / "gov").glob("governance-*.jsonl"))
            assert len(log_files) == 1

            # Verify content
            content = log_files[0].read_text()
            data = json.loads(content.strip())
            assert data["intent_id"] == "intent-123"
            assert data["tuple_type"] == "DCT"

    def test_append_async_buffer(self, tmp_path: Path):
        """Should buffer entries in async mode."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(
                base_dir=tmp_path / "gov",
                enable_async=True,
            )

            td = {"test": "data"}
            success, error = bus.append(
                intent_id="intent-123",
                task_id="task-456",
                tuple_type="DCT",
                tuple_data=td,
                signature=_test_sig(td),
            )

            assert success is True
            assert len(bus._buffer) == 1

    def test_append_async_flush_at_100(self, tmp_path: Path):
        """Should flush buffer when reaching 100 entries."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(
                base_dir=tmp_path / "gov",
                enable_async=True,
            )

            # Add 100 entries
            for i in range(100):
                td = {"i": i}
                bus.append(
                    intent_id=f"intent-{i}",
                    task_id=f"task-{i}",
                    tuple_type="SYSTEM",
                    tuple_data=td,
                    signature=_test_sig(td),
                )

            # Buffer should be flushed
            assert len(bus._buffer) == 0

            # File should have entries
            log_files = list((tmp_path / "gov").glob("governance-*.jsonl"))
            assert len(log_files) == 1


class TestGovernanceBusQuery:
    """Test GovernanceBus query methods."""

    def test_query_by_intent(self, tmp_path: Path):
        """Should query entries by intent_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            # Add entries with different intents
            bus.append("intent-a", "task-1", "DCT", {"data": 1}, signature=_test_sig({"data": 1}))
            bus.append("intent-b", "task-2", "DCT", {"data": 2}, signature=_test_sig({"data": 2}))
            bus.append("intent-a", "task-3", "SYSTEM", {"data": 3}, signature=_test_sig({"data": 3}))

            # Query for intent-a
            results = list(bus.query_by_intent("intent-a"))

            assert len(results) == 2
            assert all(r.intent_id == "intent-a" for r in results)

    def test_query_by_intent_with_type_filter(self, tmp_path: Path):
        """Should filter by tuple type."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            bus.append("intent-a", "task-1", "DCT", {"data": 1}, signature=_test_sig({"data": 1}))
            bus.append("intent-a", "task-2", "SYSTEM", {"data": 2}, signature=_test_sig({"data": 2}))

            results = list(bus.query_by_intent("intent-a", tuple_type="DCT"))

            assert len(results) == 1
            assert results[0].tuple_type == "DCT"

    def test_query_by_task(self, tmp_path: Path):
        """Should query entries by task_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            bus.append("intent-a", "task-1", "DCT", {"data": 1}, signature=_test_sig({"data": 1}))
            bus.append("intent-b", "task-1", "DCT", {"data": 2}, signature=_test_sig({"data": 2}))
            bus.append("intent-c", "task-2", "DCT", {"data": 3}, signature=_test_sig({"data": 3}))

            results = list(bus.query_by_task("task-1"))

            assert len(results) == 2
            assert all(r.task_id == "task-1" for r in results)

    def test_query_skips_corrupted_lines(self, tmp_path: Path):
        """Should skip corrupted JSON lines."""
        gov_dir = tmp_path / "gov"
        gov_dir.mkdir()

        # Create file with one good and one bad line
        log_file = gov_dir / "governance-2026-02-17.jsonl"
        log_file.write_text(
            '{"timestamp":"2026-02-17T10:00:00Z","entry_id":"uuid-1","intent_id":"intent-1","task_id":"task-1","tuple_type":"DCT","tuple_data":{}}\n'
            "this is not valid json\n"
            '{"timestamp":"2026-02-17T10:01:00Z","entry_id":"uuid-2","intent_id":"intent-2","task_id":"task-2","tuple_type":"SYSTEM","tuple_data":{}}\n'
        )

        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=gov_dir)
            results = list(bus.query_by_intent("intent-2"))

            assert len(results) == 1
            assert results[0].intent_id == "intent-2"

    def test_query_returns_empty_when_disabled(self, tmp_path: Path):
        """Should return empty iterator when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            results = list(bus.query_by_intent("intent-1"))

            assert len(results) == 0


class TestGovernanceBusRetention:
    """Test GovernanceBus retention enforcement."""

    def test_enforce_retention_deletes_old_files(self, tmp_path: Path):
        """Should delete files older than retention period."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            # Create old file
            gov_dir = tmp_path / "gov"
            old_file = gov_dir / "governance-2026-01-01.jsonl"
            old_file.parent.mkdir(parents=True, exist_ok=True)
            old_file.write_text("{}\n")

            bus = GovernanceBus(
                base_dir=gov_dir,
                retention_days=30,
            )

            # Mock current time to be 60 days later
            future = datetime(2026, 3, 1, tzinfo=timezone.utc)
            with patch("idp_spec.governance_bus.datetime") as mock_dt:
                mock_dt.now.return_value = future
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

                deleted = bus.enforce_retention()

            assert deleted == 1
            assert not old_file.exists()

    def test_enforce_retention_keeps_recent_files(self, tmp_path: Path):
        """Should keep files within retention period."""
        # Create recent file
        gov_dir = tmp_path / "gov"
        recent_file = gov_dir / "governance-2026-02-10.jsonl"
        recent_file.parent.mkdir(parents=True, exist_ok=True)
        recent_file.write_text("{}\n")

        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(
                base_dir=gov_dir,
                retention_days=90,
            )

            # Mock current time
            now = datetime(2026, 2, 17, tzinfo=timezone.utc)
            with patch("idp_spec.governance_bus.datetime") as mock_dt:
                mock_dt.now.return_value = now
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

                deleted = bus.enforce_retention()

            assert deleted == 0
            assert recent_file.exists()

    def test_enforce_retention_returns_zero_when_disabled(self, tmp_path: Path):
        """Should return 0 when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            deleted = bus.enforce_retention()

            assert deleted == 0


class TestGovernanceBusContextManager:
    """Test GovernanceBus context manager."""

    def test_context_manager_closes_file(self, tmp_path: Path):
        """Should close file handle on exit."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            file_handle = None
            with bus:
                bus.append("intent-1", "task-1", "DCT", {}, signature=_test_sig({}))
                # File handle should be open
                assert bus._file_handle is not None
                file_handle = bus._file_handle
                assert not file_handle.closed

            # File handle should be closed after exit (set to None by close())
            assert bus._file_handle is None or file_handle.closed

    def test_context_manager_flushes_async(self, tmp_path: Path):
        """Should flush async buffer on exit."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            with GovernanceBus(
                base_dir=tmp_path / "gov",
                enable_async=True,
            ) as bus:
                bus.append("intent-1", "task-1", "DCT", {}, signature=_test_sig({}))
                assert len(bus._buffer) == 1

            # Buffer should be flushed
            assert len(bus._buffer) == 0


class TestSingletonFunctions:
    """Test module-level singleton functions."""

    def test_get_governance_bus_returns_singleton(self):
        """Should return same instance."""
        # Clear any existing singleton
        import idp_spec.governance_bus as gov_module

        gov_module._default_bus = None

        bus1 = get_governance_bus()
        bus2 = get_governance_bus()

        assert bus1 is bus2

    def test_append_audit_entry_uses_default_bus(self, tmp_path: Path):
        """Should append via default bus."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            # Clear singleton and set custom path
            import idp_spec.governance_bus as gov_module

            gov_module._default_bus = None

            with patch.object(gov_module, "DEFAULT_GOVERNANCE_DIR", tmp_path / "gov"):
                td = {"test": "data"}
                success, error = append_audit_entry(
                    intent_id="intent-1",
                    task_id="task-1",
                    tuple_type="DCT",
                    tuple_data=td,
                    signature=_test_sig(td),
                )

                assert success is True

    def test_append_audit_entry_auto_signs_when_omitted(self, tmp_path: Path):
        """Should auto-sign convenience writes when caller omits signature."""
        with patch.dict(
            os.environ,
            {"ENABLE_IDP": "true", "DCT_SECRET": "test-governance-secret"},
        ):
            import idp_spec.governance_bus as gov_module

            gov_module._default_bus = None

            with patch.object(gov_module, "DEFAULT_GOVERNANCE_DIR", tmp_path / "gov"):
                success, error = append_audit_entry(
                    intent_id="intent-auto-sign",
                    task_id="task-auto-sign",
                    tuple_type="SYSTEM",
                    tuple_data={"event": "auto-signed"},
                )

                assert success is True
                assert error is None

                log_files = list((tmp_path / "gov").glob("governance-*.jsonl"))
                assert len(log_files) == 1

                line = log_files[0].read_text().strip()
                entry = json.loads(line)
                assert entry["signature"]
                assert len(entry["signature"]) == 64

    def test_query_intent_uses_default_bus(self):
        """Should query via default bus."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            results = list(query_intent("nonexistent-intent"))

            assert len(results) == 0


class TestGovernanceBusFileRotation:
    """Test file rotation logic."""

    def test_rotation_on_size_limit(self, tmp_path: Path):
        """Should rotate file when size exceeds limit."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            # Patch rotation size to smaller value for testing
            with patch("idp_spec.governance_bus.ROTATION_SIZE_BYTES", 100):
                bus = GovernanceBus(base_dir=tmp_path / "gov")

                # Create file at size limit
                log_file = tmp_path / "gov" / bus._get_current_file().name
                log_file.parent.mkdir(parents=True, exist_ok=True)
                log_file.write_bytes(b"x" * 101)  # Over 100 byte limit

                # Add new entry
                bus.append("intent-1", "task-1", "DCT", {}, signature=_test_sig({}))

                # Compressed file should exist or original should be gone
                compressed = log_file.with_suffix(".jsonl.gz")
                assert compressed.exists() or not log_file.exists()


class TestGovernanceEntryCrossLinks:
    """Test GovernanceEntry cross-link fields (contract_id, capability_token_id, verification_id, amendment_of)."""

    def test_creation_with_cross_links(self):
        """Should create entry with all cross-link fields."""
        entry = GovernanceEntry(
            timestamp="2026-03-13T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCTX",
            tuple_data={"state": "PROPOSED"},
            signature="sig-xyz",
            contract_id="contract-abc",
            capability_token_id="dct-def",
            verification_id="evidence-ghi",
            amendment_of="uuid-99",
        )

        assert entry.contract_id == "contract-abc"
        assert entry.capability_token_id == "dct-def"
        assert entry.verification_id == "evidence-ghi"
        assert entry.amendment_of == "uuid-99"

    def test_cross_links_default_none(self):
        """Cross-link fields should default to None."""
        entry = GovernanceEntry(
            timestamp="2026-03-13T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCT",
            tuple_data={},
        )

        assert entry.contract_id is None
        assert entry.capability_token_id is None
        assert entry.verification_id is None
        assert entry.amendment_of is None

    def test_to_jsonl_includes_cross_links(self):
        """Cross-link fields should appear in JSONL when set."""
        entry = GovernanceEntry(
            timestamp="2026-03-13T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCTX",
            tuple_data={},
            signature="sig",
            contract_id="c-1",
            capability_token_id="dct-2",
            verification_id="ev-3",
            amendment_of="uuid-50",
        )

        data = json.loads(entry.to_jsonl())
        assert data["contract_id"] == "c-1"
        assert data["capability_token_id"] == "dct-2"
        assert data["verification_id"] == "ev-3"
        assert data["amendment_of"] == "uuid-50"

    def test_to_jsonl_omits_none_cross_links(self):
        """Cross-link fields should NOT appear in JSONL when None (backward compat)."""
        entry = GovernanceEntry(
            timestamp="2026-03-13T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCT",
            tuple_data={},
            signature="sig",
        )

        data = json.loads(entry.to_jsonl())
        assert "contract_id" not in data
        assert "capability_token_id" not in data
        assert "verification_id" not in data
        assert "amendment_of" not in data

    def test_from_dict_with_cross_links(self):
        """Should deserialize cross-link fields from dict."""
        data = {
            "timestamp": "2026-03-13T10:00:00Z",
            "entry_id": "uuid-100",
            "intent_id": "intent-1",
            "task_id": "task-1",
            "tuple_type": "DCTX",
            "tuple_data": {},
            "signature": "sig",
            "contract_id": "c-1",
            "capability_token_id": "dct-2",
            "verification_id": "ev-3",
            "amendment_of": "uuid-50",
        }

        entry = GovernanceEntry.from_dict(data)
        assert entry.contract_id == "c-1"
        assert entry.capability_token_id == "dct-2"
        assert entry.verification_id == "ev-3"
        assert entry.amendment_of == "uuid-50"

    def test_from_dict_backward_compat(self):
        """Old entries without cross-link fields should parse correctly."""
        data = {
            "timestamp": "2026-02-17T10:00:00Z",
            "entry_id": "uuid-old",
            "intent_id": "intent-old",
            "task_id": "task-old",
            "tuple_type": "DCT",
            "tuple_data": {"legacy": True},
            "signature": "sig-old",
        }

        entry = GovernanceEntry.from_dict(data)
        assert entry.contract_id is None
        assert entry.capability_token_id is None
        assert entry.verification_id is None
        assert entry.amendment_of is None

    def test_roundtrip_with_cross_links(self):
        """Should roundtrip cross-link fields through serialization."""
        original = GovernanceEntry(
            timestamp="2026-03-13T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="EVIDENCE",
            tuple_data={"result": "pass"},
            signature="sig-xyz",
            contract_id="c-abc",
            capability_token_id="dct-def",
            verification_id="ev-ghi",
            amendment_of="uuid-50",
        )

        jsonl = original.to_jsonl()
        restored = GovernanceEntry.from_dict(json.loads(jsonl))
        assert original == restored


class TestI1Enforcement:
    """Test I1 invariant: ATTEST tuples require verification_id."""

    def test_attest_without_verification_id_rejected(self, tmp_path: Path):
        """ATTEST tuple without verification_id should be rejected."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"verdict": "pass"}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="ATTEST",
                tuple_data=td,
                signature=_test_sig(td),
                verification_id=None,
            )

            assert success is False
            assert error == IDP_E_EVIDENCE_REQUIRED

    def test_attest_with_valid_evidence_ref_accepted(self, tmp_path: Path):
        """ATTEST with verification_id referencing existing EVIDENCE entry."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            # First create an EVIDENCE entry
            ev_td = {"tool_outputs": "result"}
            bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="EVIDENCE",
                tuple_data=ev_td,
                signature=_test_sig(ev_td),
            )
            ev_entry = list(bus._query(lambda e: e.tuple_type == "EVIDENCE"))[0]

            # Now ATTEST referencing the EVIDENCE entry
            td = {"verdict": "pass"}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="ATTEST",
                tuple_data=td,
                signature=_test_sig(td),
                verification_id=ev_entry.entry_id,
            )

            assert success is True
            assert error is None

    def test_attest_with_nonexistent_verification_id_rejected(self, tmp_path: Path):
        """ATTEST referencing non-existent entry should be rejected."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"verdict": "pass"}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="ATTEST",
                tuple_data=td,
                signature=_test_sig(td),
                verification_id="nonexistent-entry-id",
            )

            assert success is False
            assert error == IDP_E_VERIFICATION_REF_INVALID

    def test_attest_with_wrong_type_verification_id_rejected(self, tmp_path: Path):
        """ATTEST referencing a CONTRACT entry (wrong type) should be rejected."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            # Create a CONTRACT entry
            c_td = {"objective": "test"}
            bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="CONTRACT",
                tuple_data=c_td,
                signature=_test_sig(c_td),
            )
            contract_entry = list(bus._query(lambda e: e.tuple_type == "CONTRACT"))[0]

            # ATTEST referencing the CONTRACT (wrong type)
            td = {"verdict": "pass"}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="ATTEST",
                tuple_data=td,
                signature=_test_sig(td),
                verification_id=contract_entry.entry_id,
            )

            assert success is False
            assert error == IDP_E_VERIFICATION_REF_INVALID

    def test_non_attest_without_verification_id_ok(self, tmp_path: Path):
        """Non-ATTEST tuples should not require verification_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            for tt in ["DCTX", "CONTRACT", "EVIDENCE", "DCT", "SYSTEM"]:
                td = {"type": tt}
                success, error = bus.append(
                    intent_id="intent-1",
                    task_id=f"task-{tt}",
                    tuple_type=tt,
                    tuple_data=td,
                    signature=_test_sig(td),
                )
                assert success is True, f"{tt} should not require verification_id"


class TestAmendmentValidation:
    """Test amendment_of validation — must reference existing entry."""

    def test_amendment_of_existing_entry_accepted(self, tmp_path: Path):
        """Amendment referencing an existing entry should succeed."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            # Append original entry
            td1 = {"version": 1}
            bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="CONTRACT",
                tuple_data=td1,
                signature=_test_sig(td1),
            )

            # Get its entry_id
            entries = list(bus.query_by_intent("intent-1"))
            assert len(entries) == 1
            original_id = entries[0].entry_id

            # Amend it
            td2 = {"version": 2}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="CONTRACT",
                tuple_data=td2,
                signature=_test_sig(td2),
                amendment_of=original_id,
            )

            assert success is True
            assert error is None

    def test_amendment_of_nonexistent_entry_rejected(self, tmp_path: Path):
        """Amendment referencing a nonexistent entry should be rejected."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"version": 2}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="CONTRACT",
                tuple_data=td,
                signature=_test_sig(td),
                amendment_of="nonexistent-uuid",
            )

            assert success is False
            assert error == IDP_E_AMENDMENT_TARGET_MISSING

    def test_no_amendment_of_always_accepted(self, tmp_path: Path):
        """Entries without amendment_of should not trigger validation."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            td = {"data": "new"}
            success, error = bus.append(
                intent_id="intent-1",
                task_id="task-1",
                tuple_type="DCT",
                tuple_data=td,
                signature=_test_sig(td),
                amendment_of=None,
            )

            assert success is True
            assert error is None


class TestCrossLinkQueries:
    """Test query_by_entry_id, query_by_contract, query_amendments."""

    def _append(self, bus, intent_id, task_id, tuple_type, td, **kwargs):
        """Helper to append with test signature."""
        return bus.append(
            intent_id=intent_id,
            task_id=task_id,
            tuple_type=tuple_type,
            tuple_data=td,
            signature=_test_sig(td),
            **kwargs,
        )

    def test_query_by_entry_id_found(self, tmp_path: Path):
        """Should find entry by its entry_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            self._append(bus, "intent-1", "task-1", "DCT", {"n": 1})
            self._append(bus, "intent-2", "task-2", "DCT", {"n": 2})

            # Get entry_ids from query
            entries = list(bus.query_by_intent("intent-1"))
            assert len(entries) == 1
            target_id = entries[0].entry_id

            # Lookup by entry_id
            result = bus.query_by_entry_id(target_id)
            assert result is not None
            assert result.intent_id == "intent-1"
            assert result.entry_id == target_id

    def test_query_by_entry_id_not_found(self, tmp_path: Path):
        """Should return None for nonexistent entry_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            result = bus.query_by_entry_id("nonexistent")
            assert result is None

    def test_query_by_contract(self, tmp_path: Path):
        """Should find entries by contract_id."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            self._append(bus, "i-1", "t-1", "DCTX", {"s": 1}, contract_id="c-100")
            self._append(bus, "i-2", "t-2", "DCT", {"s": 2}, contract_id="c-100")
            self._append(bus, "i-3", "t-3", "DCT", {"s": 3}, contract_id="c-200")

            results = list(bus.query_by_contract("c-100"))
            assert len(results) == 2
            assert all(r.contract_id == "c-100" for r in results)

    def test_query_by_contract_with_type_filter(self, tmp_path: Path):
        """Should filter by tuple_type within contract_id query."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            self._append(bus, "i-1", "t-1", "DCTX", {"s": 1}, contract_id="c-100")
            self._append(bus, "i-2", "t-2", "DCT", {"s": 2}, contract_id="c-100")

            results = list(bus.query_by_contract("c-100", tuple_type="DCT"))
            assert len(results) == 1
            assert results[0].tuple_type == "DCT"

    def test_query_amendments(self, tmp_path: Path):
        """Should find all amendments to a given entry."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            # Original
            self._append(bus, "i-1", "t-1", "CONTRACT", {"v": 1})
            entries = list(bus.query_by_intent("i-1"))
            original_id = entries[0].entry_id

            # Two amendments
            self._append(bus, "i-1", "t-1", "CONTRACT", {"v": 2}, amendment_of=original_id)
            self._append(bus, "i-1", "t-1", "CONTRACT", {"v": 3}, amendment_of=original_id)

            amendments = list(bus.query_amendments(original_id))
            assert len(amendments) == 2
            assert all(a.amendment_of == original_id for a in amendments)

    def test_query_amendments_empty(self, tmp_path: Path):
        """Should return empty for entry with no amendments."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")

            self._append(bus, "i-1", "t-1", "DCT", {"v": 1})
            entries = list(bus.query_by_intent("i-1"))
            entry_id = entries[0].entry_id

            amendments = list(bus.query_amendments(entry_id))
            assert len(amendments) == 0

    def test_query_by_entry_id_disabled(self, tmp_path: Path):
        """Should return None when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            assert bus.query_by_entry_id("any-id") is None

    def test_query_by_contract_disabled(self, tmp_path: Path):
        """Should return empty when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            assert list(bus.query_by_contract("any-contract")) == []

    def test_query_amendments_disabled(self, tmp_path: Path):
        """Should return empty when IDP disabled."""
        with patch.dict(os.environ, {"ENABLE_IDP": "false"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            assert list(bus.query_amendments("any-id")) == []


class TestAppendAuditEntryCrossLinks:
    """Test append_audit_entry convenience function with cross-link fields."""

    def test_passes_through_cross_links(self, tmp_path: Path):
        """append_audit_entry should pass cross-link fields to bus."""
        with patch.dict(
            os.environ,
            {"ENABLE_IDP": "true", "DCT_SECRET": "test-secret"},
        ):
            import idp_spec.governance_bus as gov_module

            gov_module._default_bus = None

            with patch.object(gov_module, "DEFAULT_GOVERNANCE_DIR", tmp_path / "gov"):
                success, error = append_audit_entry(
                    intent_id="intent-cl",
                    task_id="task-cl",
                    tuple_type="DCTX",
                    tuple_data={"state": "PROPOSED"},
                    contract_id="c-123",
                    capability_token_id="dct-456",
                )

                assert success is True

                log_files = list((tmp_path / "gov").glob("governance-*.jsonl"))
                assert len(log_files) == 1
                data = json.loads(log_files[0].read_text().strip())
                assert data["contract_id"] == "c-123"
                assert data["capability_token_id"] == "dct-456"

    def test_i1_enforced_via_convenience(self, tmp_path: Path):
        """append_audit_entry should enforce I1 for ATTEST tuples."""
        with patch.dict(
            os.environ,
            {"ENABLE_IDP": "true", "DCT_SECRET": "test-secret"},
        ):
            import idp_spec.governance_bus as gov_module

            gov_module._default_bus = None

            with patch.object(gov_module, "DEFAULT_GOVERNANCE_DIR", tmp_path / "gov"):
                success, error = append_audit_entry(
                    intent_id="intent-cl",
                    task_id="task-cl",
                    tuple_type="ATTEST",
                    tuple_data={"verdict": "pass"},
                    # No verification_id → should fail
                )

                assert success is False
                assert error == IDP_E_EVIDENCE_REQUIRED


class TestHashChaining:
    """Test tamper-evident hash-chaining in governance audit trail."""

    def _append(self, bus, intent_id, task_id, tuple_type, td, **kwargs):
        """Helper to append with test signature."""
        return bus.append(
            intent_id=intent_id,
            task_id=task_id,
            tuple_type=tuple_type,
            tuple_data=td,
            signature=_test_sig(td),
            **kwargs,
        )

    def test_genesis_entry_has_no_previous_hash(self, tmp_path: Path):
        """First entry in a log should have previous_hash=None."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            self._append(bus, "intent-1", "task-1", "DCT", {"n": 1})

            entries = list(bus._query(lambda e: True))
            assert len(entries) == 1
            assert entries[0].previous_hash is None

    def test_second_entry_chains_to_first(self, tmp_path: Path):
        """Second entry's previous_hash should be SHA-256 of first entry's JSONL."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            self._append(bus, "intent-1", "task-1", "DCT", {"n": 1})
            self._append(bus, "intent-2", "task-2", "DCT", {"n": 2})

            log_file = bus._get_current_file()
            lines = [l.strip() for l in log_file.read_text().splitlines() if l.strip()]
            assert len(lines) == 2

            expected_hash = GovernanceBus.compute_entry_hash(lines[0])
            entry2 = GovernanceEntry.from_dict(json.loads(lines[1]))
            assert entry2.previous_hash == expected_hash

    def test_chain_of_five_entries(self, tmp_path: Path):
        """Five entries should form a valid chain."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            for i in range(5):
                self._append(bus, f"intent-{i}", f"task-{i}", "DCT", {"n": i})

            valid, breaks = bus.verify_chain()
            assert valid is True
            assert breaks == []

    def test_verify_chain_on_empty_log(self, tmp_path: Path):
        """verify_chain on empty/nonexistent log should be valid."""
        bus = GovernanceBus(base_dir=tmp_path / "gov")
        valid, breaks = bus.verify_chain()
        assert valid is True
        assert breaks == []

    def test_verify_chain_single_entry(self, tmp_path: Path):
        """Single entry (genesis) should be valid."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            self._append(bus, "intent-1", "task-1", "DCT", {"n": 1})

            valid, breaks = bus.verify_chain()
            assert valid is True
            assert breaks == []

    def test_tamper_detected_when_entry_modified(self, tmp_path: Path):
        """Modifying an entry mid-chain should break the chain."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            for i in range(3):
                self._append(bus, f"intent-{i}", f"task-{i}", "DCT", {"n": i})
            bus.close()

            # Tamper: modify the first entry
            log_file = bus._get_current_file()
            lines = log_file.read_text().splitlines()
            data = json.loads(lines[0])
            data["tuple_data"]["n"] = 999  # tamper
            lines[0] = json.dumps(data, sort_keys=True, separators=(",", ":"))
            log_file.write_text("\n".join(lines) + "\n")

            valid, breaks = bus.verify_chain()
            assert valid is False
            assert len(breaks) >= 1
            # The break should be at line 2 (entry after tampered line)
            assert breaks[0]["line"] == 2

    def test_tamper_detected_when_entry_deleted(self, tmp_path: Path):
        """Deleting an entry should break the chain."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            for i in range(4):
                self._append(bus, f"intent-{i}", f"task-{i}", "DCT", {"n": i})
            bus.close()

            # Delete the second entry
            log_file = bus._get_current_file()
            lines = [l for l in log_file.read_text().splitlines() if l.strip()]
            del lines[1]  # remove entry 2
            log_file.write_text("\n".join(lines) + "\n")

            valid, breaks = bus.verify_chain()
            assert valid is False
            assert len(breaks) >= 1

    def test_tamper_detected_when_entry_inserted(self, tmp_path: Path):
        """Inserting a rogue entry should break the chain."""
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            bus = GovernanceBus(base_dir=tmp_path / "gov")
            for i in range(3):
                self._append(bus, f"intent-{i}", f"task-{i}", "DCT", {"n": i})
            bus.close()

            # Insert a rogue entry between line 1 and 2
            log_file = bus._get_current_file()
            lines = [l for l in log_file.read_text().splitlines() if l.strip()]
            rogue = json.dumps({
                "timestamp": "2026-03-31T00:00:00Z",
                "entry_id": "rogue-uuid",
                "intent_id": "rogue",
                "task_id": "rogue",
                "tuple_type": "SYSTEM",
                "tuple_data": {"injected": True},
                "signature": None,
                "previous_hash": "fake-hash",
            }, sort_keys=True, separators=(",", ":"))
            lines.insert(1, rogue)
            log_file.write_text("\n".join(lines) + "\n")

            valid, breaks = bus.verify_chain()
            assert valid is False
            assert len(breaks) >= 1

    def test_previous_hash_field_in_jsonl(self, tmp_path: Path):
        """previous_hash should appear in serialized JSONL."""
        entry = GovernanceEntry(
            timestamp="2026-03-31T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCT",
            tuple_data={},
            signature="sig",
            previous_hash="abc123def456",
        )
        data = json.loads(entry.to_jsonl())
        assert data["previous_hash"] == "abc123def456"

    def test_previous_hash_omitted_when_none(self):
        """previous_hash should NOT appear in JSONL when None (backward compat)."""
        entry = GovernanceEntry(
            timestamp="2026-03-31T10:00:00Z",
            entry_id="uuid-100",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="DCT",
            tuple_data={},
            signature="sig",
        )
        data = json.loads(entry.to_jsonl())
        assert "previous_hash" not in data

    def test_from_dict_backward_compat_no_previous_hash(self):
        """Old entries without previous_hash should deserialize with None."""
        data = {
            "timestamp": "2026-02-17T10:00:00Z",
            "entry_id": "uuid-old",
            "intent_id": "intent-old",
            "task_id": "task-old",
            "tuple_type": "DCT",
            "tuple_data": {},
            "signature": "sig",
        }
        entry = GovernanceEntry.from_dict(data)
        assert entry.previous_hash is None

    def test_compute_entry_hash_deterministic(self):
        """compute_entry_hash should be deterministic for same input."""
        line = '{"entry_id":"uuid-1","intent_id":"i-1","task_id":"t-1","tuple_type":"DCT"}'
        h1 = GovernanceBus.compute_entry_hash(line)
        h2 = GovernanceBus.compute_entry_hash(line)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_compute_entry_hash_changes_with_content(self):
        """Different content should produce different hashes."""
        h1 = GovernanceBus.compute_entry_hash('{"n":1}')
        h2 = GovernanceBus.compute_entry_hash('{"n":2}')
        assert h1 != h2
