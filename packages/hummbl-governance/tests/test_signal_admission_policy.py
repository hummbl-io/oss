"""Tests for Signal CLI admission policy fixtures and receipt schema.

Validates that all fixtures conform to the signal_receipt schema and that
the policy gates are correctly exercised by each fixture.
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "signal"
SCHEMA_PATH = Path(__file__).parent.parent / "docs" / "ecosystem" / "schemas" / "signal_receipt.schema.json"

REQUIRED_FIELDS = [
    "receipt_id", "surface", "lane", "actor_or_agent", "recipient_alias",
    "event_class", "risk_class", "message_hash", "message_summary",
    "admission_decision", "durable_uri",
]

VALID_LANES = {"notify", "ack", "candidate_command", "agent_coordination"}
VALID_RISK_CLASSES = {"notify_read_only", "ack_only", "candidate_command", "write_pending_approval", "forbidden"}
VALID_ADMISSION_DECISIONS = {"admitted", "denied", "pending_approval", "dry_run"}


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


@pytest.fixture
def schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.mark.parametrize("fixture_name", [
    "notify_allowlisted.json",
    "notify_unknown_recipient.json",
    "inbound_candidate_command.json",
    "broad_broadcast_denied.json",
    "agent_to_agent_no_scope.json",
    "secret_redaction.json",
])
def test_fixture_has_all_required_fields(fixture_name):
    """Every fixture must have all required receipt fields."""
    data = _load_fixture(fixture_name)
    for field in REQUIRED_FIELDS:
        assert field in data, f"{fixture_name} missing required field: {field}"


@pytest.mark.parametrize("fixture_name", [
    "notify_allowlisted.json",
    "notify_unknown_recipient.json",
    "inbound_candidate_command.json",
    "broad_broadcast_denied.json",
    "agent_to_agent_no_scope.json",
    "secret_redaction.json",
])
def test_fixture_surface_is_signal(fixture_name):
    """Every fixture must have surface=signal."""
    data = _load_fixture(fixture_name)
    assert data["surface"] == "signal"


@pytest.mark.parametrize("fixture_name", [
    "notify_allowlisted.json",
    "notify_unknown_recipient.json",
    "inbound_candidate_command.json",
    "broad_broadcast_denied.json",
    "agent_to_agent_no_scope.json",
    "secret_redaction.json",
])
def test_fixture_valid_lane(fixture_name):
    """Every fixture must have a valid lane."""
    data = _load_fixture(fixture_name)
    assert data["lane"] in VALID_LANES, f"{fixture_name} has invalid lane: {data['lane']}"


@pytest.mark.parametrize("fixture_name", [
    "notify_allowlisted.json",
    "notify_unknown_recipient.json",
    "inbound_candidate_command.json",
    "broad_broadcast_denied.json",
    "agent_to_agent_no_scope.json",
    "secret_redaction.json",
])
def test_fixture_valid_risk_class(fixture_name):
    """Every fixture must have a valid risk_class."""
    data = _load_fixture(fixture_name)
    assert data["risk_class"] in VALID_RISK_CLASSES, f"{fixture_name} has invalid risk_class: {data['risk_class']}"


@pytest.mark.parametrize("fixture_name", [
    "notify_allowlisted.json",
    "notify_unknown_recipient.json",
    "inbound_candidate_command.json",
    "broad_broadcast_denied.json",
    "agent_to_agent_no_scope.json",
    "secret_redaction.json",
])
def test_fixture_valid_admission_decision(fixture_name):
    """Every fixture must have a valid admission_decision."""
    data = _load_fixture(fixture_name)
    decision = data["admission_decision"]
    assert decision in VALID_ADMISSION_DECISIONS, f"{fixture_name} invalid admission_decision: {decision}"


def test_notify_allowlisted_is_admitted():
    """Outbound notify to allowlisted recipient should be admitted."""
    data = _load_fixture("notify_allowlisted.json")
    assert data["admission_decision"] == "admitted"
    assert data["risk_class"] == "notify_read_only"


def test_notify_unknown_recipient_is_denied():
    """Outbound notify to unknown recipient should be denied (G-SIGNAL-RECIPIENT-ALLOWLIST)."""
    data = _load_fixture("notify_unknown_recipient.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"


def test_inbound_is_candidate_command():
    """Inbound Signal message must be candidate_command, not direct execution."""
    data = _load_fixture("inbound_candidate_command.json")
    assert data["lane"] == "candidate_command"
    assert data["admission_decision"] == "pending_approval"
    assert data["executor"] is None


def test_broad_broadcast_is_denied():
    """Broadcast without explicit lane policy should be denied."""
    data = _load_fixture("broad_broadcast_denied.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"


def test_agent_to_agent_no_scope_is_denied():
    """Agent-to-agent without declared scope should be denied (G-SIGNAL-AGENT-TO-AGENT-SCOPE)."""
    data = _load_fixture("agent_to_agent_no_scope.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"


def test_secret_redaction_applied():
    """Message with secret-like material should have redactions_applied."""
    data = _load_fixture("secret_redaction.json")
    assert data["admission_decision"] == "admitted"
    assert len(data["redactions_applied"]) > 0
    assert "api_key" in data["redactions_applied"]


def test_all_fixtures_present():
    """All 6 required fixtures must exist."""
    expected = {
        "notify_allowlisted.json",
        "notify_unknown_recipient.json",
        "inbound_candidate_command.json",
        "broad_broadcast_denied.json",
        "agent_to_agent_no_scope.json",
        "secret_redaction.json",
    }
    actual = {f.name for f in FIXTURES_DIR.glob("*.json")}
    assert actual == expected, f"Missing fixtures: {expected - actual}"


def test_schema_file_exists():
    """Schema file must exist at expected path."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_policy_doc_exists():
    """Policy document must exist at expected path."""
    policy_path = Path(__file__).parent.parent / "docs" / "SIGNAL_CLI_ADMISSION_POLICY.md"
    assert policy_path.exists(), f"Policy doc not found at {policy_path}"
