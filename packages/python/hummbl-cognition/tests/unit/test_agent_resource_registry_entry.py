from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_cognition.agent_resource_registry_entry import (
    AgentResourceRegistryError,
    compute_entry_hash,
    compute_receipt_hash,
    create_discovery_receipt,
    create_registry_entry,
    validate_discovery_receipt,
    validate_registry_batch,
    validate_registry_entry,
)


def _admitted_entry() -> dict:
    return create_registry_entry(
        resource_id="res-github-mcp-server",
        resource_type="mcp_server",
        resource_owner="operator",
        namespace_status="admitted",
        install_authority="trusted",
        invoke_authority="active",
        risk_class="high",
        privacy_class="internal",
        receipt_required=True,
        last_reviewed_at="2026-07-04T00:00:00Z",
        resource_name="GitHub MCP Server",
        source_registry="mcp-server-registry",
        publish_authority="trusted",
        allowed_contexts=["development", "testing", "production", "governance"],
        blocked_contexts=["external_facing"],
        secrets_required=True,
        network_required=True,
        reviewed_by="devin",
    )


def _candidate_entry() -> dict:
    return create_registry_entry(
        resource_id="res-vertex-ai-extensions",
        resource_type="vertex-extension",
        resource_owner="operator",
        namespace_status="candidate",
        install_authority="disabled",
        invoke_authority="disabled",
        risk_class="high",
        privacy_class="internal",
        receipt_required=True,
        last_reviewed_at="2026-07-04T00:00:00Z",
        resource_name="Vertex AI Extensions",
        source_registry="vertex-ai-extensions-catalog",
        publish_authority="disabled",
        blocked_contexts=["production", "external_facing"],
        secrets_required=True,
        network_required=True,
        admission_conditions=[
            "inventory all available Vertex AI Extensions",
            "obtain operator approval before any extension is invoked",
        ],
        migration_decision="hold",
        reviewed_by="devin",
    )


def _rejected_entry() -> dict:
    return create_registry_entry(
        resource_id="res-raw-shell-exec",
        resource_type="tool",
        resource_owner="operator",
        namespace_status="rejected",
        install_authority="disabled",
        invoke_authority="disabled",
        risk_class="critical",
        privacy_class="restricted",
        receipt_required=True,
        last_reviewed_at="2026-07-04T00:00:00Z",
        resource_name="Raw Shell Execution (unrestricted)",
        publish_authority="disabled",
        blocked_contexts=["development", "testing", "production", "research",
                          "briefing", "governance", "external_facing"],
        rejection_reason="Unrestricted shell execution bypasses all guardrails.",
        migration_decision="reject_migration",
        reviewed_by="operator",
    )


def test_validate_accepts_admitted_entry():
    valid, errors = validate_registry_entry(_admitted_entry())
    assert valid, errors


def test_validate_accepts_candidate_entry():
    valid, errors = validate_registry_entry(_candidate_entry())
    assert valid, errors


def test_validate_accepts_rejected_entry():
    valid, errors = validate_registry_entry(_rejected_entry())
    assert valid, errors


def test_validate_rejects_extra_field():
    entry = _admitted_entry()
    entry["raw_secret"] = "sk-leaked"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("unexpected fields" in e for e in errors)


def test_validate_rejects_missing_required_field():
    entry = _admitted_entry()
    del entry["risk_class"]
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("missing required field: risk_class" in e for e in errors)


def test_validate_rejects_bad_resource_id_prefix():
    entry = _admitted_entry()
    entry["resource_id"] = "wrong-prefix-123"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("resource_id must match pattern" in e for e in errors)


def test_validate_rejects_resource_id_with_uppercase():
    """resource_id must be lowercase alphanumeric + hyphens only."""
    entry = _admitted_entry()
    entry["resource_id"] = "res-Invalid_ID"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("resource_id must match pattern" in e for e in errors)


def test_validate_rejects_resource_id_with_underscores():
    entry = _admitted_entry()
    entry["resource_id"] = "res-invalid_id"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("resource_id must match pattern" in e for e in errors)


def test_validate_rejects_bad_last_reviewed_at():
    """last_reviewed_at must be a valid ISO 8601 date-time, not just a string."""
    entry = _admitted_entry()
    entry["last_reviewed_at"] = "not-a-date"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("last_reviewed_at must be an ISO 8601 date-time" in e for e in errors)


def test_validate_rejects_date_only_last_reviewed_at():
    """Date-only strings are not valid date-times."""
    entry = _admitted_entry()
    entry["last_reviewed_at"] = "2026-07-04"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("last_reviewed_at must be an ISO 8601 date-time" in e for e in errors)


def test_validate_accepts_z_suffix_last_reviewed_at():
    """'2026-07-04T00:00:00Z' is the canonical form and must validate."""
    entry = _admitted_entry()
    # already uses Z suffix — should be valid
    valid, errors = validate_registry_entry(entry)
    assert valid, errors


def test_validate_accepts_offset_last_reviewed_at():
    """ISO 8601 with explicit offset must validate."""
    entry = _admitted_entry()
    entry["last_reviewed_at"] = "2026-07-04T00:00:00+00:00"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert valid, errors


def test_validate_rejects_timezoneless_last_reviewed_at():
    """RFC3339 date-time requires a timezone — '2026-07-04T00:00:00' is invalid."""
    entry = _admitted_entry()
    entry["last_reviewed_at"] = "2026-07-04T00:00:00"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("last_reviewed_at must be an ISO 8601 date-time" in e for e in errors)


def test_validate_accepts_negative_offset_last_reviewed_at():
    """ISO 8601 with negative offset (e.g. US timezone) must validate."""
    entry = _admitted_entry()
    entry["last_reviewed_at"] = "2026-07-04T00:00:00-05:00"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert valid, errors


def test_validate_rejects_bad_resource_type():
    entry = _admitted_entry()
    entry["resource_type"] = "quantum_device"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("resource_type:" in e for e in errors)


def test_admitted_requires_non_disabled_install_authority():
    entry = _admitted_entry()
    entry["install_authority"] = "disabled"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("admitted requires install_authority != 'disabled'" in e for e in errors)


def test_admitted_requires_non_disabled_invoke_authority():
    entry = _admitted_entry()
    entry["invoke_authority"] = "disabled"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("admitted requires invoke_authority != 'disabled'" in e for e in errors)


def test_candidate_requires_disabled_install_authority():
    """No ambient authority — candidates are not usable until admitted."""
    entry = _candidate_entry()
    entry["install_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("candidate requires install_authority='disabled'" in e for e in errors)


def test_candidate_requires_disabled_invoke_authority():
    entry = _candidate_entry()
    entry["invoke_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("candidate requires invoke_authority='disabled'" in e for e in errors)


def test_candidate_requires_restricted_publish_authority():
    """Candidates must not be publishable/cited in external artifacts until admitted."""
    entry = _candidate_entry()
    entry["publish_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("candidate requires publish_authority" in e for e in errors)


def test_candidate_allows_operator_only_publish_authority():
    """operator_only publish_authority is allowed for candidates (operator can cite)."""
    entry = _candidate_entry()
    entry["publish_authority"] = "operator_only"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert valid, errors


def test_rejected_requires_disabled_install_authority():
    """A rejected resource must not remain installable — no ambient authority after rejection."""
    entry = _rejected_entry()
    entry["install_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("rejected requires install_authority='disabled'" in e for e in errors)


def test_rejected_requires_disabled_invoke_authority():
    """A rejected resource must not remain invocable — no ambient authority after rejection."""
    entry = _rejected_entry()
    entry["invoke_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("rejected requires invoke_authority='disabled'" in e for e in errors)


def test_retired_requires_disabled_install_authority():
    """A retired resource must not remain installable."""
    entry = _rejected_entry()
    entry["namespace_status"] = "retired"
    entry["install_authority"] = "trusted"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("retired requires install_authority='disabled'" in e for e in errors)


def test_retired_requires_disabled_invoke_authority():
    """A retired resource must not remain invocable."""
    entry = _rejected_entry()
    entry["namespace_status"] = "retired"
    entry["invoke_authority"] = "trusted"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("retired requires invoke_authority='disabled'" in e for e in errors)


def test_rejected_requires_rejection_reason():
    entry = _rejected_entry()
    entry["rejection_reason"] = ""
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("rejected requires a non-empty rejection_reason" in e for e in errors)


def test_retired_requires_rejection_reason():
    entry = _rejected_entry()
    entry["namespace_status"] = "retired"
    entry["rejection_reason"] = ""
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("retired requires a non-empty rejection_reason" in e for e in errors)


def test_critical_risk_requires_restricted_publish_authority():
    entry = _admitted_entry()
    entry["risk_class"] = "critical"
    entry["publish_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("critical requires publish_authority" in e for e in errors)


def test_restricted_privacy_requires_restricted_publish_authority():
    entry = _admitted_entry()
    entry["privacy_class"] = "restricted"
    entry["publish_authority"] = "active"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("restricted requires publish_authority" in e for e in errors)


def test_secrets_required_requires_medium_risk_or_higher():
    entry = _admitted_entry()
    entry["secrets_required"] = True
    entry["risk_class"] = "low"
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("secrets_required=true requires risk_class >= 'medium'" in e for e in errors)


def test_migration_migrate_requires_migration_target():
    entry = _candidate_entry()
    entry["migration_decision"] = "migrate"
    entry["migration_target"] = ""
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("migration_decision=migrate requires a non-empty migration_target" in e for e in errors)


def test_allowed_and_blocked_contexts_must_not_overlap():
    entry = _admitted_entry()
    entry["allowed_contexts"] = ["development", "testing"]
    entry["blocked_contexts"] = ["testing", "production"]
    entry["entry_hash"] = compute_entry_hash(entry)

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("must not overlap" in e for e in errors)


def test_tampered_hash_rejected():
    entry = _admitted_entry()
    entry["entry_hash"] = "0" * 64

    valid, errors = validate_registry_entry(entry)

    assert not valid
    assert any("entry_hash does not match" in e for e in errors)


def test_create_raises_on_invalid():
    try:
        create_registry_entry(
            resource_id="bad-prefix",
            resource_type="mcp_server",
            resource_owner="operator",
            namespace_status="admitted",
            install_authority="trusted",
            invoke_authority="active",
            risk_class="high",
            privacy_class="internal",
            receipt_required=True,
            last_reviewed_at="2026-07-04T00:00:00Z",
        )
        assert False, "should have raised"
    except AgentResourceRegistryError as exc:
        assert "resource_id" in str(exc)


def test_create_omits_empty_optional_fields():
    entry = create_registry_entry(
        resource_id="res-test",
        resource_type="tool",
        resource_owner="operator",
        namespace_status="candidate",
        install_authority="disabled",
        invoke_authority="disabled",
        risk_class="low",
        privacy_class="public",
        receipt_required=False,
        last_reviewed_at="2026-07-04T00:00:00Z",
    )

    assert "resource_name" not in entry
    assert "source_registry" not in entry
    assert "allowed_contexts" not in entry
    assert "blocked_contexts" not in entry
    assert "rejection_reason" not in entry
    assert "admission_conditions" not in entry
    # secrets_required and network_required are always present (default False)
    assert entry["secrets_required"] is False
    assert entry["network_required"] is False


def test_seed_registry_all_entries_valid():
    """All fixture entries in the seed registry must validate."""
    seed_path = Path(__file__).parent.parent.parent / "src" / "hummbl_cognition" / "seed_registries" / "agent_resource_registry_seed.jsonl"

    entries = []
    with open(seed_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    assert len(entries) >= 4, f"expected at least 4 seed entries, got {len(entries)}"

    for entry in entries:
        valid, errors = validate_registry_entry(entry)
        assert valid, f"{entry['resource_id']}: {errors}"


def test_seed_registry_contains_vertex_ai_extensions_candidate():
    """The Vertex AI Extensions entry must be present as a candidate (migration hold)."""
    seed_path = Path(__file__).parent.parent.parent / "src" / "hummbl_cognition" / "seed_registries" / "agent_resource_registry_seed.jsonl"

    with open(seed_path) as f:
        entries = [json.loads(l.strip()) for l in f if l.strip()]

    vertex = [e for e in entries if e["resource_id"] == "res-vertex-ai-extensions"]
    assert len(vertex) == 1
    v = vertex[0]
    assert v["namespace_status"] == "candidate"
    assert v["install_authority"] == "disabled"
    assert v["invoke_authority"] == "disabled"
    assert v["migration_decision"] == "hold"
    assert v["resource_type"] == "vertex-extension"
    assert len(v["admission_conditions"]) >= 3


# --- #1687: Namespace audit batch validation tests ---

class TestValidateRegistryBatch:
    """Tests for cross-entry and cross-registry collision detection (#1687)."""

    def test_no_collisions_passes(self):
        """A batch of unique, non-colliding entries should pass."""
        entries = [
            {"resource_id": "res-github-mcp-server"},
            {"resource_id": "res-bandit-security-scanner"},
            {"resource_id": "res-vertex-ai-extensions"},
        ]
        ok, errors = validate_registry_batch(entries)
        assert ok
        assert errors == []

    def test_duplicate_resource_id_detected(self):
        """Duplicate resource_ids within a batch should be flagged."""
        entries = [
            {"resource_id": "res-github-mcp-server"},
            {"resource_id": "res-github-mcp-server"},
        ]
        ok, errors = validate_registry_batch(entries)
        assert not ok
        assert any("duplicate" in e for e in errors)

    def test_collision_with_agent_id_detected(self):
        """A resource_id that strips to a known agent ID should be flagged."""
        entries = [{"resource_id": "res-claude"}]
        ok, errors = validate_registry_batch(
            entries, known_agent_ids={"claude", "codex", "devin"}
        )
        assert not ok
        assert any("collides with agent ID" in e for e in errors)

    def test_collision_with_skill_name_detected(self):
        """A resource_id that strips to a known skill name should be flagged."""
        entries = [{"resource_id": "res-sbom-generate"}]
        ok, errors = validate_registry_batch(
            entries, known_skill_names={"sbom-generate", "threat-model"}
        )
        assert not ok
        assert any("collides with skill name" in e for e in errors)

    def test_collision_with_mcp_server_name_detected(self):
        """A resource_id that strips to a known MCP server name should be flagged."""
        entries = [{"resource_id": "res-github"}]
        ok, errors = validate_registry_batch(
            entries, known_mcp_server_names={"github", "wolfram"}
        )
        assert not ok
        assert any("collides with MCP server name" in e for e in errors)

    def test_no_collision_when_not_in_known_sets(self):
        """A resource_id that doesn't match any known set should pass."""
        entries = [{"resource_id": "res-custom-tool-xyz"}]
        ok, errors = validate_registry_batch(
            entries,
            known_agent_ids={"claude", "codex"},
            known_skill_names={"sbom-generate"},
            known_mcp_server_names={"github"},
        )
        assert ok
        assert errors == []

    def test_seed_registry_passes_batch_validation(self):
        """The 4 seed entries should pass batch validation with real agent IDs."""
        seed_path = Path(__file__).parent.parent.parent / "src" / "hummbl_cognition" / "seed_registries" / "agent_resource_registry_seed.jsonl"

        with open(seed_path) as f:
            entries = [json.loads(l.strip()) for l in f if l.strip()]

        # Use real canonical agent IDs from agent_identity.py
        known_agents = {
            "claude", "codex", "gemini", "dashboard", "human", "sov",
            "dan", "opencode", "soma", "echo", "apex", "devin",
        }
        ok, errors = validate_registry_batch(entries, known_agent_ids=known_agents)
        assert ok, f"Seed registry has collisions: {errors}"
        assert errors == []


# --- #1686: Discovery receipt schema tests ---

def _valid_receipt() -> dict:
    return create_discovery_receipt(
        receipt_id="dr-github-mcp-20260704",
        resource_id="res-github-mcp-server",
        discovery_source="mcp-server-registry",
        evidence=[
            {"kind": "url", "ref": "https://github.com/modelcontextprotocol/servers"},
            {"kind": "commit", "ref": "abc123", "note": "Initial admission"},
        ],
        admission_decision="admit",
        reviewer="trusted",
        timestamp="2026-07-04T00:00:00Z",
        notes="Admitted after security review.",
    )


class TestValidateDiscoveryReceipt:
    """Tests for the discovery receipt schema (#1686)."""

    def test_valid_receipt_passes(self):
        """A well-formed receipt should validate."""
        receipt = _valid_receipt()
        ok, errors = validate_discovery_receipt(receipt)
        assert ok, errors
        assert errors == []

    def test_missing_required_field_rejected(self):
        """Missing a required field should fail."""
        receipt = _valid_receipt()
        del receipt["receipt_id"]
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("missing required field: receipt_id" in e for e in errors)

    def test_bad_receipt_id_prefix_rejected(self):
        """receipt_id without 'dr-' prefix should fail."""
        receipt = _valid_receipt()
        receipt["receipt_id"] = "github-mcp-20260704"
        # Recompute hash since we changed a field
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("receipt_id must match" in e for e in errors)

    def test_bad_resource_id_prefix_rejected(self):
        """resource_id without 'res-' prefix should fail."""
        receipt = _valid_receipt()
        receipt["resource_id"] = "github-mcp-server"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("resource_id must match" in e for e in errors)

    def test_bad_discovery_source_rejected(self):
        """Invalid discovery_source should fail."""
        receipt = _valid_receipt()
        receipt["discovery_source"] = "random-place"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("discovery_source must be one of" in e for e in errors)

    def test_bad_admission_decision_rejected(self):
        """Invalid admission_decision should fail."""
        receipt = _valid_receipt()
        receipt["admission_decision"] = "maybe"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("admission_decision must be one of" in e for e in errors)

    def test_bad_reviewer_rejected(self):
        """Invalid reviewer should fail."""
        receipt = _valid_receipt()
        receipt["reviewer"] = "intern"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("reviewer must be one of" in e for e in errors)

    def test_empty_evidence_rejected(self):
        """Empty evidence array should fail."""
        receipt = _valid_receipt()
        receipt["evidence"] = []
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("evidence must be a non-empty array" in e for e in errors)

    def test_bad_evidence_kind_rejected(self):
        """Invalid evidence kind should fail."""
        receipt = _valid_receipt()
        receipt["evidence"][0]["kind"] = "gut-feeling"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("evidence[0].kind must be one of" in e for e in errors)

    def test_reject_decision_requires_rejection_reason(self):
        """admission_decision=reject requires rejection_reason."""
        receipt = _valid_receipt()
        receipt["admission_decision"] = "reject"
        # No rejection_reason set
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("requires a non-empty rejection_reason" in e for e in errors)

    def test_retire_decision_requires_rejection_reason(self):
        """admission_decision=retire requires rejection_reason."""
        receipt = _valid_receipt()
        receipt["admission_decision"] = "retire"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("requires a non-empty rejection_reason" in e for e in errors)

    def test_reject_with_reason_passes(self):
        """admission_decision=reject with a reason should pass."""
        receipt = create_discovery_receipt(
            receipt_id="dr-raw-shell-reject-20260704",
            resource_id="res-raw-shell-exec",
            discovery_source="internal",
            evidence=[{"kind": "doc", "ref": "security-review-2026-07"}],
            admission_decision="reject",
            reviewer="operator",
            timestamp="2026-07-04T00:00:00Z",
            rejection_reason="Unrestricted shell execution bypasses all guardrails.",
        )
        ok, errors = validate_discovery_receipt(receipt)
        assert ok, errors

    def test_bad_timestamp_rejected(self):
        """Invalid timestamp should fail."""
        receipt = _valid_receipt()
        receipt["timestamp"] = "not-a-date"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("timestamp must be a valid" in e for e in errors)

    def test_tampered_hash_rejected(self):
        """A mismatched receipt_hash should fail (tamper detection)."""
        receipt = _valid_receipt()
        receipt["receipt_hash"] = "0" * 64
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("receipt_hash does not match" in e for e in errors)

    def test_unexpected_field_rejected(self):
        """An unexpected field should fail."""
        receipt = _valid_receipt()
        receipt["sneaky_field"] = "malicious"
        receipt["receipt_hash"] = compute_receipt_hash(receipt)
        ok, errors = validate_discovery_receipt(receipt)
        assert not ok
        assert any("unexpected fields" in e for e in errors)

    def test_create_raises_on_invalid(self):
        """create_discovery_receipt should raise on invalid input."""
        with pytest.raises(AgentResourceRegistryError, match="receipt_id"):
            create_discovery_receipt(
                receipt_id="bad-id",
                resource_id="res-github-mcp-server",
                discovery_source="mcp-server-registry",
                evidence=[{"kind": "url", "ref": "https://example.com"}],
                admission_decision="admit",
                reviewer="trusted",
                timestamp="2026-07-04T00:00:00Z",
            )
