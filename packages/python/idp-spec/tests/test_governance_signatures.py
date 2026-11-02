"""Persisted audit signatures must cover exactly the redacted JSON payload."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
from unittest.mock import Mock

import pytest

from idp_spec import governance_bus


SECRET = b"test-audit-payload-secret"
FIELDS = ("intent_id", "task_id", "tuple_type", "tuple_data", "state", "drift")


@pytest.fixture(autouse=True)
def signing_environment(monkeypatch):
    monkeypatch.setenv("ENABLE_IDP", "true")
    monkeypatch.setenv("DCT_SECRET", SECRET.decode())


def signature_for(payload):
    """Independent verifier; do not reuse the implementation's signing helper."""
    canonical = json.dumps(
        {field: payload[field] for field in FIELDS}, sort_keys=True, separators=(",", ":")
    )
    return hmac.new(SECRET, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def payload_for(data):
    return {
        "intent_id": "intent", "task_id": "task", "tuple_type": "SYSTEM",
        "tuple_data": data, "state": "blocked", "drift": 0.25,
    }


def append_entry(bus, monkeypatch, convenience, payload, signature=None):
    if convenience:
        monkeypatch.setattr(governance_bus, "_default_bus", bus)
        return governance_bus.append_audit_entry(**payload, signature=signature)
    return bus.append(**payload, signature=signature, auto_sign=signature is None)


@pytest.mark.parametrize("enable_async", [False, True])
@pytest.mark.parametrize("convenience", [False, True])
def test_automatic_signature_verifies_from_persisted_pii_entry(
    tmp_path, monkeypatch, enable_async, convenience
):
    data = {"nested": [["alice@example.com", ("212-555-0199",)]], "label": "caf\u00e9"}
    payload = payload_for(data)
    original_signature = signature_for(payload)
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert append_entry(bus, monkeypatch, convenience, payload) == (True, None)
        data["nested"][0].append("injected@example.com")
        assert bus._flush_buffer() == (True, None)
        serialized = bus._get_current_file().read_text(encoding="utf-8")
        entry = json.loads(serialized)
        assert "@example.com" not in serialized
        assert "212-555-0199" not in serialized
        assert entry["tuple_data"]["label"] == "caf\u00e9"
        assert hmac.compare_digest(entry["signature"], signature_for(entry))
        assert entry["signature"] != original_signature
        assert bus.verify_chain() == (True, [])
        entry["tuple_data"]["label"] = "tampered"
        assert not hmac.compare_digest(entry["signature"], signature_for(entry))


@pytest.mark.parametrize("enable_async", [False, True])
@pytest.mark.parametrize("convenience", [False, True])
def test_caller_can_prepare_sign_and_persist_exact_data(
    tmp_path, monkeypatch, enable_async, convenience
):
    original = {"nested": [["alice@example.com"]]}
    prepared = governance_bus.prepare_audit_tuple_data(original)
    assert original == {"nested": [["alice@example.com"]]}
    assert prepared != original
    payload = payload_for(prepared)
    signature = signature_for(payload)
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert append_entry(bus, monkeypatch, convenience, payload, signature) == (True, None)
        prepared["nested"][0].append("late@example.com")
        assert bus._flush_buffer() == (True, None)
        entry = json.loads(bus._get_current_file().read_text(encoding="utf-8"))
        assert entry["signature"] == signature
        assert hmac.compare_digest(signature, signature_for(entry))
        assert "late@example.com" not in json.dumps(entry)


@pytest.mark.parametrize("enable_async", [False, True])
@pytest.mark.parametrize("convenience", [False, True])
def test_redaction_rejects_caller_signature_without_mutating_log_or_buffer(
    tmp_path, monkeypatch, caplog, enable_async, convenience
):
    with governance_bus.GovernanceBus(tmp_path, enable_async=enable_async) as bus:
        assert bus.append(**payload_for({"event": "existing"}), auto_sign=True) == (True, None)
        assert bus._flush_buffer() == (True, None)
        if enable_async:
            assert bus.append(**payload_for({"event": "pending"}), auto_sign=True) == (True, None)
        path = bus._get_current_file()
        before_bytes = path.read_bytes()
        before_buffer = copy.deepcopy(bus._buffer)
        payload = payload_for({"contact": "alice@example.com"})
        read_hash = Mock(side_effect=AssertionError("must reject before reading prior hash"))
        monkeypatch.setattr(bus, "_get_last_entry_hash", read_hash)
        assert append_entry(
            bus, monkeypatch, convenience, payload, signature_for(payload)
        ) == (False, governance_bus.IDP_E_AUDIT_IMMUTABLE)
        read_hash.assert_not_called()
        assert path.read_bytes() == before_bytes
        assert bus._buffer == before_buffer
        assert "alice@example.com" not in caplog.text


@pytest.mark.parametrize("unavailable", [False, True])
def test_scrub_failure_precedes_signing(tmp_path, monkeypatch, unavailable):
    signer = Mock(side_effect=AssertionError("must not sign rejected data"))
    monkeypatch.setattr(governance_bus, "_compute_entry_signature", signer)
    scrubber = None if unavailable else Mock(side_effect=ValueError("private input"))
    monkeypatch.setattr(governance_bus, "_scrub_pii", scrubber)
    with governance_bus.GovernanceBus(tmp_path) as bus:
        monkeypatch.setattr(governance_bus, "_default_bus", bus)
        with pytest.raises(RuntimeError):
            governance_bus.append_audit_entry(**payload_for({"contact": "alice@example.com"}))
        signer.assert_not_called()
        assert not bus._buffer
        assert not list(tmp_path.glob("*.jsonl"))


def test_automatic_signing_cannot_replace_a_supplied_signature(tmp_path):
    with governance_bus.GovernanceBus(tmp_path) as bus:
        with pytest.raises(ValueError, match="mutually exclusive"):
            bus.append(**payload_for({"safe": True}), signature="caller", auto_sign=True)
        assert not list(tmp_path.glob("*.jsonl"))


def test_direct_append_still_requires_a_signature_by_default(tmp_path):
    with governance_bus.GovernanceBus(tmp_path) as bus:
        assert bus.append(**payload_for({"safe": True})) == (
            False, governance_bus.IDP_E_AUDIT_IMMUTABLE
        )
        assert not list(tmp_path.glob("*.jsonl"))
