"""Tests for the security-domain schemas: agent-lock and agent-vulnerability."""

import hashlib
import json
from pathlib import Path

import hummbl_contracts
from hummbl_contracts.schema_validator import validate

FIXTURES = Path(__file__).parent / "fixtures" / "security"


def _load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_security_schemas_discoverable():
    """Both schemas are auto-discovered by the loader under 'security/'."""
    names = hummbl_contracts.list_schemas()
    assert "security/agent-lock" in names
    assert "security/agent-vulnerability" in names


def test_agent_lock_example_valid():
    schema = hummbl_contracts.load_schema("security/agent-lock")
    errors = validate(_load_fixture("agent-lock.example.json"), schema)
    assert errors == [], errors


def test_agent_lock_example_config_sha256_is_computed():
    """provenance.config_sha256 must equal the canonical hash of the doc
    minus 'provenance' -- otherwise the unit identity is decorative."""
    doc = _load_fixture("agent-lock.example.json")
    claimed = doc["provenance"]["config_sha256"]
    payload = {k: v for k, v in doc.items() if k != "provenance"}
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert claimed == hashlib.sha256(canon.encode()).hexdigest()


def test_agent_lock_missing_model_fails():
    schema = hummbl_contracts.load_schema("security/agent-lock")
    doc = _load_fixture("agent-lock.example.json")
    del doc["model"]
    errors = validate(doc, schema)
    assert any("model" in e for e in errors)


def test_agent_lock_missing_provenance_fails():
    schema = hummbl_contracts.load_schema("security/agent-lock")
    doc = _load_fixture("agent-lock.example.json")
    del doc["provenance"]
    assert validate(doc, schema)


def test_avr_examples_valid():
    """Every line of the example JSONL feed validates as an AVR."""
    schema = hummbl_contracts.load_schema("security/agent-vulnerability")
    lines = (FIXTURES / "agent-vulnerability.example.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2  # exercises both component and configuration units
    for line in lines:
        errors = validate(json.loads(line), schema)
        assert errors == [], errors


def test_avr_bad_id_fails():
    schema = hummbl_contracts.load_schema("security/agent-vulnerability")
    rec = json.loads((FIXTURES / "agent-vulnerability.example.jsonl").read_text().splitlines()[0])
    rec["id"] = "CVE-2026-1234"  # CVE- is MITRE's namespace, not ours
    assert any("id" in e for e in validate(rec, schema))


def test_avr_empty_affected_fails():
    schema = hummbl_contracts.load_schema("security/agent-vulnerability")
    rec = json.loads((FIXTURES / "agent-vulnerability.example.jsonl").read_text().splitlines()[0])
    rec["affected"] = []
    assert validate(rec, schema)


def test_avr_affected_entry_without_unit_fails():
    schema = hummbl_contracts.load_schema("security/agent-vulnerability")
    rec = json.loads((FIXTURES / "agent-vulnerability.example.jsonl").read_text().splitlines()[0])
    rec["affected"] = [{"component": {"kind": "tool", "name": "x"}}]
    assert validate(rec, schema)
