"""Tests for Slack mobile command surface policy fixtures and receipt schema.

Validates that all fixtures conform to the slack_command_receipt schema and that
the policy gates are correctly exercised by each fixture.
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "slack"
SCHEMA_PATH = Path(__file__).parent.parent / "docs" / "ecosystem" / "schemas" / "slack_command_receipt.schema.json"

REQUIRED_FIELDS = [
    "receipt_id", "surface", "workspace_id_hash", "channel_id_hash",
    "actor_id_hash", "received_at", "command_text_hash", "parsed_intent",
    "risk_class", "authority", "admission_decision", "output_policy",
    "durable_receipt_uri",
]

VALID_RISK_CLASSES = {"read_only", "draft_only", "write_pending_approval", "destructive", "forbidden"}
VALID_ADMISSION_DECISIONS = {"admitted", "denied", "pending_approval"}
VALID_OUTPUT_POLICIES = {"summarized", "redacted", "link_only"}


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


@pytest.fixture
def schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_has_all_required_fields(fixture_name):
    """Every fixture must have all required receipt fields."""
    data = _load_fixture(fixture_name)
    for field in REQUIRED_FIELDS:
        assert field in data, f"{fixture_name} missing required field: {field}"


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_surface_is_slack(fixture_name):
    """Every fixture must have surface=slack."""
    data = _load_fixture(fixture_name)
    assert data["surface"] == "slack"


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_valid_risk_class(fixture_name):
    """Every fixture must have a valid risk_class."""
    data = _load_fixture(fixture_name)
    assert data["risk_class"] in VALID_RISK_CLASSES, f"{fixture_name} has invalid risk_class: {data['risk_class']}"


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_valid_admission_decision(fixture_name):
    """Every fixture must have a valid admission_decision."""
    data = _load_fixture(fixture_name)
    decision = data["admission_decision"]
    assert decision in VALID_ADMISSION_DECISIONS, f"{fixture_name} invalid admission_decision: {decision}"


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_valid_output_policy(fixture_name):
    """Every fixture must have a valid output_policy."""
    data = _load_fixture(fixture_name)
    policy = data["output_policy"]
    assert policy in VALID_OUTPUT_POLICIES, f"{fixture_name} invalid output_policy: {policy}"


@pytest.mark.parametrize("fixture_name", [
    "valid_read_only.json",
    "valid_draft_only.json",
    "invalid_write_without_approval.json",
    "invalid_raw_shell.json",
    "invalid_secret_exposure.json",
    "invalid_unknown_verb.json",
])
def test_fixture_no_raw_identifiers(fixture_name):
    """Fixtures must use hashed identifiers, not raw workspace/channel/actor IDs."""
    data = _load_fixture(fixture_name)
    # workspace_id_hash, channel_id_hash, actor_id_hash must be 64-char hex
    for field in ["workspace_id_hash", "channel_id_hash", "actor_id_hash"]:
        val = data[field]
        assert len(val) == 64, f"{fixture_name} {field} must be 64 chars, got {len(val)}"
        assert all(c in "0123456789abcdef" for c in val), f"{fixture_name} {field} must be hex"


def test_valid_read_only_is_admitted():
    """Valid read-only status command should be admitted."""
    data = _load_fixture("valid_read_only.json")
    assert data["admission_decision"] == "admitted"
    assert data["risk_class"] == "read_only"


def test_valid_draft_only_is_admitted():
    """Valid draft-only request should be admitted with no external write."""
    data = _load_fixture("valid_draft_only.json")
    assert data["admission_decision"] == "admitted"
    assert data["risk_class"] == "draft_only"


def test_write_without_approval_is_denied():
    """Write command without approval should be denied (G-SLACK-APPROVAL-BEFORE-WRITE)."""
    data = _load_fixture("invalid_write_without_approval.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "write_pending_approval"
    assert data["executor"] is None


def test_raw_shell_is_denied():
    """Raw shell command should be denied."""
    data = _load_fixture("invalid_raw_shell.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"


def test_secret_exposure_is_denied_and_redacted():
    """Secret in command should be denied with redactions applied."""
    data = _load_fixture("invalid_secret_exposure.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"
    assert len(data["redactions_applied"]) > 0
    assert "api_key" in data["redactions_applied"]


def test_unknown_verb_is_denied():
    """Unknown command verb should be denied by default."""
    data = _load_fixture("invalid_unknown_verb.json")
    assert data["admission_decision"] == "denied"
    assert data["risk_class"] == "forbidden"


def test_all_fixtures_present():
    """All 6 required fixtures must exist."""
    expected = {
        "valid_read_only.json",
        "valid_draft_only.json",
        "invalid_write_without_approval.json",
        "invalid_raw_shell.json",
        "invalid_secret_exposure.json",
        "invalid_unknown_verb.json",
    }
    actual = {f.name for f in FIXTURES_DIR.glob("*.json")}
    assert actual == expected, f"Missing fixtures: {expected - actual}"


def test_schema_file_exists():
    """Schema file must exist at expected path."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_policy_doc_exists():
    """Policy document must exist at expected path."""
    policy_path = Path(__file__).parent.parent / "docs" / "SLACK_MOBILE_COMMAND_POLICY.md"
    assert policy_path.exists(), f"Policy doc not found at {policy_path}"
