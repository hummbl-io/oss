"""Tests for cryptographic AuditBus and tamper detection."""

import os
import tempfile
import pytest
from agent_governance import AuditBus


def test_audit_bus_chain_integrity():
    bus = AuditBus()
    r1 = bus.record_event("agent-1", "TOOL_CALL", {"tool": "search", "query": "inversion"})
    r2 = bus.record_event("agent-1", "STATE_MUTATION", {"path": "config.json", "op": "write"})
    r3 = bus.record_event("supervisor", "DELEGATION", {"delegate": "agent-2", "scope": "read"})

    assert len(bus.records) == 3
    assert r1.prev_hash == "0" * 64
    assert r2.prev_hash == r1.entry_hash
    assert r3.prev_hash == r2.entry_hash
    assert bus.verify_chain() is True


def test_audit_bus_tamper_detection():
    bus = AuditBus()
    bus.record_event("agent-1", "ACTION_1", {"data": 100})
    bus.record_event("agent-1", "ACTION_2", {"data": 200})

    assert bus.verify_chain() is True

    # Maliciously mutate an existing record payload
    bus.records[0].payload["data"] = 999
    assert bus.verify_chain() is False


def test_audit_bus_sqlite_and_jsonl_backends():
    with tempfile.TemporaryDirectory() as tmpdir:
        jsonl_path = os.path.join(tmpdir, "audit.jsonl")
        db_path = os.path.join(tmpdir, "audit.db")

        bus = AuditBus(log_file=jsonl_path, db_file=db_path)
        bus.record_event("agent-sec", "LOGIN", {"ip": "127.0.0.1"})
        bus.record_event("agent-sec", "TOKEN_ISSUE", {"token_id": "tok_123"})

        assert os.path.exists(jsonl_path)
        assert os.path.exists(db_path)
        assert bus.verify_chain() is True


def test_audit_bus_db_reload_extends_chain():
    """A new AuditBus pointing at an existing DB must resume the chain,
    not reset it — otherwise persisted records orphan from new ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "audit.db")

        bus1 = AuditBus(db_file=db_path)
        r1 = bus1.record_event("agent-a", "ACTION_1", {"n": 1})
        bus1.record_event("agent-a", "ACTION_2", {"n": 2})

        # Simulate a process restart: new instance, same DB file.
        bus2 = AuditBus(db_file=db_path)
        r3 = bus2.record_event("agent-a", "ACTION_3", {"n": 3})

        assert bus2._seq == 3
        assert r3.prev_hash == r1.entry_hash or r3.prev_hash == bus1.records[-1].entry_hash
        # The new record's prev_hash must chain from the last persisted record,
        # not from the genesis "0"*64 hash.
        assert r3.prev_hash != "0" * 64
