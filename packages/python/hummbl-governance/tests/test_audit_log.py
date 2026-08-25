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

"""Tests for hummbl_governance.audit_log."""

import tempfile


from hummbl_governance.audit_log import (
    AuditEntry,
    AuditLog,
    E_AUDIT_IMMUTABLE,
    E_AUDIT_SIGNATURE_INVALID,
    E_AMENDMENT_TARGET_MISSING,
    E_EVIDENCE_REQUIRED,
    E_VERIFICATION_REF_INVALID,
)


class TestAuditEntry:
    """Test AuditEntry serialization."""

    def test_to_jsonl_round_trip(self):
        import json
        entry = AuditEntry(
            timestamp="2026-01-01T00:00:00Z",
            entry_id="entry-1",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="CONTRACT",
            tuple_data={"name": "test"},
            signature="sig-123",
        )
        line = entry.to_jsonl()
        parsed = json.loads(line)
        restored = AuditEntry.from_dict(parsed)
        assert restored.entry_id == "entry-1"
        assert restored.tuple_type == "CONTRACT"
        assert restored.tuple_data == {"name": "test"}

    def test_optional_fields(self):
        import json
        entry = AuditEntry(
            timestamp="2026-01-01T00:00:00Z",
            entry_id="entry-1",
            intent_id="intent-1",
            task_id="task-1",
            tuple_type="CONTRACT",
            tuple_data={},
            contract_id="contract-1",
            amendment_of="entry-0",
        )
        line = entry.to_jsonl()
        parsed = json.loads(line)
        assert parsed["contract_id"] == "contract-1"
        assert parsed["amendment_of"] == "entry-0"


class TestAuditLogAppend:
    """Test append operations."""

    def test_append_with_signature(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            ok, err = log.append(
                intent_id="i1", task_id="t1",
                tuple_type="CONTRACT",
                tuple_data={"name": "test"},
                signature="sig-123",
            )
            assert ok is True
            assert err is None
            log.close()

    def test_append_without_signature_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=True)
            ok, err = log.append(
                intent_id="i1", task_id="t1",
                tuple_type="CONTRACT",
                tuple_data={"name": "test"},
            )
            assert ok is False
            assert err == E_AUDIT_IMMUTABLE
            log.close()

    def test_append_without_signature_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            ok, err = log.append(
                intent_id="i1", task_id="t1",
                tuple_type="CONTRACT",
                tuple_data={"name": "test"},
            )
            assert ok is True
            log.close()

    def test_attest_requires_verification_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            ok, err = log.append(
                intent_id="i1", task_id="t1",
                tuple_type="ATTEST",
                tuple_data={"verdict": "pass"},
            )
            assert ok is False
            assert err == E_EVIDENCE_REQUIRED
            log.close()

    def test_attest_verification_ref_must_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            ok, err = log.append(
                intent_id="i1", task_id="t1",
                tuple_type="ATTEST",
                tuple_data={"verdict": "pass"},
                verification_id="nonexistent",
            )
            assert ok is False
            assert err == E_VERIFICATION_REF_INVALID
            log.close()


class TestAuditLogQuery:
    """Test query operations."""

    def test_query_by_intent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            log.append("i2", "t2", "CONTRACT", {"n": 2})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_intent("i1"))
            assert len(results) == 1
            assert results[0].intent_id == "i1"
            log2.close()

    def test_query_by_task(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            log.append("i1", "t2", "DCT", {"n": 2})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_task("t1"))
            assert len(results) == 1
            log2.close()

    def test_query_by_entry_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            entries = list(log2.query_by_intent("i1"))
            assert len(entries) == 1
            found = log2.query_by_entry_id(entries[0].entry_id)
            assert found is not None
            assert found.intent_id == "i1"
            log2.close()

    def test_query_by_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1}, contract_id="c1")
            log.append("i1", "t2", "DCT", {"n": 2}, contract_id="c2")
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_contract("c1"))
            assert len(results) == 1
            log2.close()

    def test_query_with_type_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            log.append("i1", "t2", "DCT", {"n": 2})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_intent("i1", tuple_type="CONTRACT"))
            assert len(results) == 1
            assert results[0].tuple_type == "CONTRACT"
            log2.close()


class TestAuditLogAmendments:
    """Test amendment chain tracking."""

    def test_amendment_of_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"v": 1})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            original = list(log2.query_by_intent("i1"))[0]
            ok, err = log2.append(
                "i1", "t1", "CONTRACT", {"v": 2},
                amendment_of=original.entry_id,
            )
            assert ok is True
            log2.close()

    def test_amendment_of_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            ok, err = log.append(
                "i1", "t1", "CONTRACT", {"v": 2},
                amendment_of="nonexistent",
            )
            assert ok is False
            assert err == E_AMENDMENT_TARGET_MISSING
            log.close()

    def test_query_amendments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"v": 1})
            log.close()

            log2 = AuditLog(tmpdir, require_signature=False)
            original = list(log2.query_by_intent("i1"))[0]
            log2.append("i1", "t1", "CONTRACT", {"v": 2}, amendment_of=original.entry_id)
            log2.close()

            log3 = AuditLog(tmpdir, require_signature=False)
            amendments = list(log3.query_amendments(original.entry_id))
            assert len(amendments) == 1
            assert amendments[0].tuple_data == {"v": 2}
            log3.close()


class TestAuditLogContextManager:
    """Test context manager protocol."""

    def test_context_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with AuditLog(tmpdir, require_signature=False) as log:
                log.append("i1", "t1", "CONTRACT", {"n": 1})

            # Verify data persisted
            with AuditLog(tmpdir, require_signature=False) as log2:
                results = list(log2.query_by_intent("i1"))
                assert len(results) == 1


class TestAuditLogRetention:
    """Test retention enforcement."""

    def test_enforce_retention_no_old_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, retention_days=180)
            deleted = log.enforce_retention()
            assert deleted == 0
            log.close()

    def test_enforce_retention_deletes_old_file(self):
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually create a stale governance file with old date
            old_file = os.path.join(tmpdir, "audit-2020-01-01.jsonl")
            with open(old_file, "w") as f:
                f.write("{}\n")
            log = AuditLog(tmpdir, retention_days=30, file_prefix="audit")
            deleted = log.enforce_retention()
            assert deleted == 1
            assert not os.path.exists(old_file)
            log.close()


class TestAuditLogAsync:
    """Test async (buffered) append mode."""

    def test_async_append_buffered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False, enable_async=True)
            # Append fewer than 100 entries — stays in buffer
            ok, err = log.append("i1", "t1", "CONTRACT", {"n": 1})
            assert ok is True
            assert err is None
            # Closing flushes the buffer
            log.close()

            # Now re-open in sync mode and verify it was persisted
            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_intent("i1"))
            assert len(results) == 1
            log2.close()

    def test_async_flush_on_100_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False, enable_async=True)
            # Fill buffer to trigger auto-flush at 100
            for i in range(100):
                log.append(f"i{i}", f"t{i}", "CONTRACT", {"n": i})
            # After 100th append, buffer should be flushed
            log.close()
            log2 = AuditLog(tmpdir, require_signature=False)
            results = list(log2.query_by_intent("i0"))
            assert len(results) >= 1
            log2.close()


class TestAuditLogExplain:
    """Test explain() chain tracing."""

    def test_explain_returns_empty_for_unknown_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            chain = log.explain("nonexistent-id")
            assert chain == []
            log.close()

    def test_explain_single_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            ok, _ = log.append("i1", "t1", "CONTRACT", {"n": 1})
            assert ok
            # Get the entry_id
            entries = list(log.query_by_intent("i1"))
            assert len(entries) == 1
            eid = entries[0].entry_id
            chain = log.explain(eid)
            assert len(chain) == 1
            assert chain[0].entry_id == eid
            log.close()

    def test_explain_amendment_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            # Write root entry
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            root_entries = list(log.query_by_intent("i1"))
            root_id = root_entries[0].entry_id
            # Write amendment pointing to root
            log.append("i2", "t2", "CONTRACT", {"n": 2}, amendment_of=root_id)
            amendment_entries = list(log.query_by_intent("i2"))
            amend_id = amendment_entries[0].entry_id
            # Explain the amendment — should include both entries
            chain = log.explain(amend_id)
            entry_ids = [e.entry_id for e in chain]
            assert root_id in entry_ids
            assert amend_id in entry_ids
            log.close()

    def test_explain_capability_token_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            # Write DCT (capability token)
            log.append("i_dct", "t1", "DCT", {"issuer": "system"})
            dct_entries = list(log.query_by_intent("i_dct"))
            dct_id = dct_entries[0].entry_id
            # Write action that references the DCT
            log.append("i_action", "t2", "INTENT", {"agent": "claude"},
                       capability_token_id=dct_id)
            action_entries = list(log.query_by_intent("i_action"))
            action_id = action_entries[0].entry_id
            chain = log.explain(action_id)
            entry_ids = [e.entry_id for e in chain]
            assert dct_id in entry_ids
            assert action_id in entry_ids
            log.close()


class TestAuditLogClose:
    """Test close() idempotency and double-close safety."""

    def test_close_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            log.append("i1", "t1", "CONTRACT", {"n": 1})
            log.close()
            # Second close should not raise
            log.close()

    def test_close_without_writes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, require_signature=False)
            # Should not raise even with no file handle open
            log.close()


class TestHmacVerification:
    """Test HMAC-SHA256 signature verification (opt-in via hmac_key)."""

    KEY = b"test-key-do-not-use-in-production-32B"

    def _sign(self, entry: AuditEntry) -> str:
        import hmac as _hmac
        from hashlib import sha256
        return _hmac.new(
            self.KEY, AuditLog.canonical_bytes(entry), sha256
        ).hexdigest()

    def _build_entry(
        self, log: AuditLog, intent_id="i1", task_id="t1",
        tuple_type="CONTRACT", tuple_data=None,
    ) -> AuditEntry:
        # Build an AuditEntry matching what AuditLog.append() will construct,
        # so we can pre-compute the canonical signature.
        from datetime import datetime, timezone
        import uuid
        return AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            entry_id=str(uuid.uuid4()),
            intent_id=intent_id,
            task_id=task_id,
            tuple_type=tuple_type,
            tuple_data=tuple_data or {"n": 1},
        )

    def test_no_key_preserves_presence_only_behavior(self):
        """Backward compat: hmac_key=None (default) accepts any non-empty signature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with AuditLog(tmpdir) as log:  # no hmac_key
                ok, err = log.append("i1", "t1", "CONTRACT", {"n": 1}, signature="arbitrary")
                assert ok, f"expected accept, got {err}"

    def test_valid_signature_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, hmac_key=self.KEY)
            # Reproduce the AuditLog.append flow: build entry then sign.
            # The actual append() generates timestamp+entry_id internally,
            # so we test via verify_entry() on a manually-built entry.
            entry = self._build_entry(log)
            sig = self._sign(entry)
            signed = AuditEntry(
                timestamp=entry.timestamp, entry_id=entry.entry_id,
                intent_id=entry.intent_id, task_id=entry.task_id,
                tuple_type=entry.tuple_type, tuple_data=entry.tuple_data,
                signature=sig,
            )
            assert log.verify_entry(signed) is True

    def test_tampered_signature_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, hmac_key=self.KEY)
            entry = self._build_entry(log)
            tampered = AuditEntry(
                timestamp=entry.timestamp, entry_id=entry.entry_id,
                intent_id=entry.intent_id, task_id=entry.task_id,
                tuple_type=entry.tuple_type, tuple_data=entry.tuple_data,
                signature="deadbeef" * 8,
            )
            assert log.verify_entry(tampered) is False

    def test_tampered_data_rejected(self):
        """Signature computed over original data fails when data mutated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, hmac_key=self.KEY)
            entry = self._build_entry(log, tuple_data={"n": 1})
            sig = self._sign(entry)
            mutated = AuditEntry(
                timestamp=entry.timestamp, entry_id=entry.entry_id,
                intent_id=entry.intent_id, task_id=entry.task_id,
                tuple_type=entry.tuple_type,
                tuple_data={"n": 2},  # mutated after signing
                signature=sig,
            )
            assert log.verify_entry(mutated) is False

    def test_append_rejects_bad_signature(self):
        """append() returns E_AUDIT_SIGNATURE_INVALID when HMAC doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, hmac_key=self.KEY)
            ok, err = log.append(
                "i1", "t1", "CONTRACT", {"n": 1}, signature="deadbeef" * 8,
            )
            assert ok is False
            assert err == E_AUDIT_SIGNATURE_INVALID

    def test_verify_entry_returns_false_when_no_key_configured(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)  # no hmac_key
            entry = self._build_entry(log)
            signed = AuditEntry(
                timestamp=entry.timestamp, entry_id=entry.entry_id,
                intent_id=entry.intent_id, task_id=entry.task_id,
                tuple_type=entry.tuple_type, tuple_data=entry.tuple_data,
                signature="anything",
            )
            assert log.verify_entry(signed) is False

    def test_verify_entry_returns_false_when_unsigned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir, hmac_key=self.KEY)
            entry = self._build_entry(log)  # no signature
            assert log.verify_entry(entry) is False

    def test_canonical_bytes_excludes_signature(self):
        """canonical_bytes() must be identical regardless of signature value."""
        from dataclasses import replace
        e1 = AuditEntry(
            timestamp="2026-01-01T00:00:00Z", entry_id="e1",
            intent_id="i1", task_id="t1", tuple_type="CONTRACT",
            tuple_data={"n": 1}, signature="sig-a",
        )
        e2 = replace(e1, signature="sig-b")
        e3 = replace(e1, signature=None)
        assert AuditLog.canonical_bytes(e1) == AuditLog.canonical_bytes(e2)
        assert AuditLog.canonical_bytes(e1) == AuditLog.canonical_bytes(e3)
