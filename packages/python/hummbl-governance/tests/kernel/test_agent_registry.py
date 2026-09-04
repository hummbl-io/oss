"""Tests for the Agent Registry primitive (P44).

Covers: store (register/list/get/latest), lifecycle (promote/transition
validation), drift detection (roster comparison), and the .agents/
importer. Follows the test_model_registry / test_canon_registry style.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kernel.agent_registry import (
    AgentEntry,
    AgentRegistry,
    AgentStatus,
    SenderClass,
    SCHEMA_VERSION,
    default_registry_path,
    validate_agent_entry,
    validate_promotion_gate,
    validate_supersession,
    validate_transition,
)
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic
from hummbl_governance.schema_validator import ValidationError


def _valid_entry_kwargs(**overrides):
    base = {
        "agent_id": "pi",
        "display_name": "Pi CLI",
        "status": AgentStatus.ACTIVE,
        "sender_class": SenderClass.AUTONOMOUS_LLM,
        "trust_class": "medium_high",
        "role": "Ops/remediation executor",
    }
    base.update(overrides)
    return base


# ----------------------------------------------------------------------
# Schema validation
# ----------------------------------------------------------------------

class TestSchemaValidation:
    def test_valid_entry_passes(self):
        validate_agent_entry(AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(),
        ).to_dict())

    def test_missing_required_field_fails(self):
        d = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(),
        ).to_dict()
        del d["agent_id"]
        with pytest.raises(ValidationError):
            validate_agent_entry(d)

    def test_invalid_status_fails(self):
        d = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(status="unknown_status"),
        ).to_dict()
        with pytest.raises(ValidationError):
            validate_agent_entry(d)

    def test_invalid_agent_id_pattern_fails(self):
        d = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(agent_id="UPPER-CASE"),
        ).to_dict()
        with pytest.raises(ValidationError):
            validate_agent_entry(d)


# ----------------------------------------------------------------------
# Transition validation
# ----------------------------------------------------------------------

class TestTransitionValidation:
    def test_candidate_to_bootstrap_ok(self):
        validate_transition(
            AgentStatus.CANDIDATE_PENDING.value,
            AgentStatus.ACTIVE_BOOTSTRAP.value,
        )

    def test_bootstrap_to_active_ok(self):
        validate_transition(
            AgentStatus.ACTIVE_BOOTSTRAP.value,
            AgentStatus.ACTIVE.value,
        )

    def test_active_to_aip_ok(self):
        validate_transition(AgentStatus.ACTIVE.value, AgentStatus.ACTIVE_AIP.value)

    def test_aip_to_active_ok(self):
        validate_transition(AgentStatus.ACTIVE_AIP.value, AgentStatus.ACTIVE.value)

    def test_active_to_dormant_ok(self):
        validate_transition(AgentStatus.ACTIVE.value, AgentStatus.DORMANT.value)

    def test_dormant_to_active_ok(self):
        validate_transition(AgentStatus.DORMANT.value, AgentStatus.ACTIVE.value)

    def test_any_to_retired_ok(self):
        for s in (AgentStatus.CANDIDATE_PENDING, AgentStatus.ACTIVE, AgentStatus.DORMANT):
            validate_transition(s.value, AgentStatus.RETIRED.value)

    def test_any_to_superseded_ok(self):
        validate_transition(AgentStatus.ACTIVE.value, AgentStatus.SUPERSEDED.value)

    def test_skip_level_fails(self):
        with pytest.raises(ValueError, match="expected 'candidate_pending' -> 'active_bootstrap'"):
            validate_transition(
                AgentStatus.CANDIDATE_PENDING.value,
                AgentStatus.ACTIVE.value,
            )

    def test_same_status_fails(self):
        with pytest.raises(ValueError, match="both 'active'"):
            validate_transition(AgentStatus.ACTIVE.value, AgentStatus.ACTIVE.value)

    def test_terminal_no_forward_fails(self):
        with pytest.raises(ValueError, match="terminal"):
            validate_transition(AgentStatus.RETIRED.value, AgentStatus.ACTIVE.value)


# ----------------------------------------------------------------------
# Promotion gate (D5 NO_AUTO_PROMOTION)
# ----------------------------------------------------------------------

class TestPromotionGate:
    def test_approved_promotion_ok(self):
        validate_promotion_gate(
            AgentStatus.CANDIDATE_PENDING.value,
            AgentStatus.ACTIVE_BOOTSTRAP.value,
            operator_approval=True,
            approver_id="operator-001",
        )

    def test_unapproved_promotion_fails(self):
        with pytest.raises(ValueError, match="D5.*NO_AUTO_PROMOTION"):
            validate_promotion_gate(
                AgentStatus.CANDIDATE_PENDING.value,
                AgentStatus.ACTIVE_BOOTSTRAP.value,
                operator_approval=False,
                approver_id="operator-001",
            )

    def test_empty_approver_id_fails(self):
        with pytest.raises(ValueError, match="approver_id"):
            validate_promotion_gate(
                AgentStatus.CANDIDATE_PENDING.value,
                AgentStatus.ACTIVE_BOOTSTRAP.value,
                operator_approval=True,
                approver_id="",
            )

    def test_non_promotion_transition_skips_gate(self):
        # Dormant is not in the promotion gate; should pass even without approval.
        validate_promotion_gate(
            AgentStatus.ACTIVE.value,
            AgentStatus.DORMANT.value,
            operator_approval=False,
            approver_id="",
        )


# ----------------------------------------------------------------------
# Supersession validation
# ----------------------------------------------------------------------

class TestSupersession:
    def test_superseded_without_successor_fails(self):
        entry = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(status=AgentStatus.SUPERSEDED, superseded_by=""),
        )
        with pytest.raises(ValueError, match="superseded_by is empty"):
            validate_supersession(entry)

    def test_superseded_with_successor_ok(self):
        entry = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(status=AgentStatus.SUPERSEDED, superseded_by="pi-v2"),
        )
        validate_supersession(entry)

    def test_non_superseded_ignored(self):
        entry = AgentEntry(
            schema_version=SCHEMA_VERSION,
            timestamp="2026-08-24T00:00:00Z",
            **_valid_entry_kwargs(status=AgentStatus.ACTIVE),
        )
        validate_supersession(entry)


# ----------------------------------------------------------------------
# Store: register / list / get / latest / find
# ----------------------------------------------------------------------

class TestStore:
    def test_register_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            entry = reg.register(**_valid_entry_kwargs())
            assert entry.agent_id == "pi"
            assert entry.status == AgentStatus.ACTIVE.value

            agents = reg.list_agents()
            assert len(agents) == 1
            assert agents[0].agent_id == "pi"

    def test_get_returns_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(display_name="Pi v1"))
            reg.register(**_valid_entry_kwargs(display_name="Pi v2"))

            latest = reg.get("pi")
            assert latest is not None
            assert latest.display_name == "Pi v2"

    def test_get_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            assert reg.get("nonexistent") is None

    def test_latest_deduplicates_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi"))
            reg.register(**_valid_entry_kwargs(agent_id="codex", display_name="Codex"))
            reg.register(**_valid_entry_kwargs(agent_id="pi", display_name="Pi updated"))

            latest = reg.latest()
            assert len(latest) == 2
            assert latest["pi"].display_name == "Pi updated"

    def test_find_by_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi", status=AgentStatus.ACTIVE))
            reg.register(**_valid_entry_kwargs(
                agent_id="agy", status=AgentStatus.CANDIDATE_PENDING,
                sender_class=SenderClass.NON_SENDER, trust_class="probationary",
            ))

            active = reg.find(status=AgentStatus.ACTIVE)
            assert len(active) == 1
            assert active[0].agent_id == "pi"

    def test_find_by_sender_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi"))
            reg.register(**_valid_entry_kwargs(
                agent_id="purple-team", display_name="Purple Team",
                sender_class=SenderClass.SIMULATION_GATED_SERVICE,
                trust_class="medium", role="Defender",
            ))

            sims = reg.find(sender_class=SenderClass.SIMULATION_GATED_SERVICE)
            assert len(sims) == 1
            assert sims[0].agent_id == "purple-team"

    def test_find_by_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(hosts=["anvil", "hummbl_vps"]))
            reg.register(**_valid_entry_kwargs(
                agent_id="delta-only", display_name="Delta Agent",
                trust_class="medium", role="Delta runner", hosts=["delta"],
            ))

            anvil_agents = reg.find(host="anvil")
            assert len(anvil_agents) == 1
            assert anvil_agents[0].agent_id == "pi"

    def test_find_by_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(tags=["research", "ops"]))
            reg.register(**_valid_entry_kwargs(
                agent_id="codex", display_name="Codex",
                trust_class="trusted", role="Engineer", tags=["engineering"],
            ))

            research = reg.find(tag="research")
            assert len(research) == 1
            assert research[0].agent_id == "pi"

    def test_empty_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            assert reg.list_agents() == []
            assert reg.latest() == {}
            assert reg.get("anything") is None
            assert reg.stats()["count"] == 0


# ----------------------------------------------------------------------
# Lifecycle: promote
# ----------------------------------------------------------------------

class TestPromote:
    def test_valid_promotion_with_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(status=AgentStatus.CANDIDATE_PENDING))

            promoted = reg.promote(
                "pi",
                AgentStatus.ACTIVE_BOOTSTRAP,
                operator_approval=True,
                approver_id="operator-001",
            )
            assert promoted.status == AgentStatus.ACTIVE_BOOTSTRAP.value
            assert promoted.promoted_at != ""

            latest = reg.get("pi")
            assert latest.status == AgentStatus.ACTIVE_BOOTSTRAP.value

    def test_promotion_without_approval_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(status=AgentStatus.CANDIDATE_PENDING))

            with pytest.raises(ValueError, match="D5"):
                reg.promote(
                    "pi",
                    AgentStatus.ACTIVE_BOOTSTRAP,
                    operator_approval=False,
                    approver_id="operator-001",
                )

    def test_promotion_invalid_transition_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(status=AgentStatus.CANDIDATE_PENDING))

            with pytest.raises(ValueError, match="expected 'candidate_pending' -> 'active_bootstrap'"):
                reg.promote(
                    "pi",
                    AgentStatus.ACTIVE,
                    operator_approval=True,
                    approver_id="operator-001",
                )

    def test_promote_missing_agent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            with pytest.raises(ValueError, match="not found"):
                reg.promote(
                    "ghost",
                    AgentStatus.ACTIVE,
                    operator_approval=True,
                    approver_id="operator-001",
                )

    def test_supersede_with_successor(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(status=AgentStatus.ACTIVE))

            superseded = reg.promote(
                "pi",
                AgentStatus.SUPERSEDED,
                operator_approval=False,
                approver_id="operator-001",
                superseded_by="pi-v2",
            )
            assert superseded.status == AgentStatus.SUPERSEDED.value
            assert superseded.superseded_by == "pi-v2"


# ----------------------------------------------------------------------
# Lineage
# ----------------------------------------------------------------------

class TestLineage:
    def test_lineage_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="ancestor"))
            reg.register(**_valid_entry_kwargs(
                agent_id="child", display_name="Child", parent_id="ancestor",
            ))
            reg.register(**_valid_entry_kwargs(
                agent_id="grandchild", display_name="Grandchild", parent_id="child",
            ))

            chain = reg.lineage("grandchild")
            assert [e.agent_id for e in chain] == ["ancestor", "child", "grandchild"]

    def test_lineage_no_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="solo"))

            chain = reg.lineage("solo")
            assert len(chain) == 1
            assert chain[0].agent_id == "solo"


# ----------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------

class TestStats:
    def test_stats_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi", status=AgentStatus.ACTIVE))
            reg.register(**_valid_entry_kwargs(
                agent_id="codex", display_name="Codex",
                trust_class="trusted", role="Engineer", status=AgentStatus.ACTIVE,
            ))
            reg.register(**_valid_entry_kwargs(
                agent_id="agy", display_name="Agy",
                sender_class=SenderClass.NON_SENDER, trust_class="probationary",
                role="Candidate", status=AgentStatus.CANDIDATE_PENDING,
            ))

            stats = reg.stats()
            assert stats["count"] == 3
            assert stats["by_status"]["active"] == 2
            assert stats["by_status"]["candidate_pending"] == 1
            assert stats["by_sender_class"]["autonomous_llm"] == 2
            assert stats["by_sender_class"]["non_sender"] == 1


# ----------------------------------------------------------------------
# Drift detection
# ----------------------------------------------------------------------

class TestDriftDetection:
    def _roster(self, tmp, rows):
        """Build a markdown roster file from (agent_id, display, trust, status) tuples."""
        path = Path(tmp) / "ROSTER.md"
        lines = ["# Roster", "", "| Agent | Display | Trust | Status | Notes |",
                 "|---|---|---|---|---|"]
        for aid, disp, trust, status in rows:
            lines.append(f"| `{aid}` | {disp} | {trust} | {status} | - |")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def test_missing_in_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi"))
            roster = self._roster(tmp, [
                ("pi", "Pi", "MEDIUM-HIGH", "Active"),
                ("ghost", "Ghost", "LOW", "Candidate"),
            ])

            findings = reg.detect_roster_drift(roster)
            missing = [f for f in findings if f["kind"] == "missing_in_registry"]
            assert len(missing) == 1
            assert missing[0]["agent_id"] == "ghost"

    def test_missing_in_roster(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi"))
            reg.register(**_valid_entry_kwargs(
                agent_id="codex", display_name="Codex",
                trust_class="trusted", role="Engineer",
            ))
            roster = self._roster(tmp, [("pi", "Pi", "MEDIUM-HIGH", "Active")])

            findings = reg.detect_roster_drift(roster)
            missing = [f for f in findings if f["kind"] == "missing_in_roster"]
            assert len(missing) == 1
            assert missing[0]["agent_id"] == "codex"

    def test_terminal_not_flagged_missing_in_roster(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi"))
            reg.register(**_valid_entry_kwargs(
                agent_id="old-agent", display_name="Old",
                trust_class="none", role="Retired", status=AgentStatus.RETIRED,
            ))
            roster = self._roster(tmp, [("pi", "Pi", "MEDIUM-HIGH", "Active")])

            findings = reg.detect_roster_drift(roster)
            missing = [f for f in findings if f["kind"] == "missing_in_roster"]
            assert all(f["agent_id"] != "old-agent" for f in missing)

    def test_status_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi", status=AgentStatus.DORMANT))
            roster = self._roster(tmp, [("pi", "Pi", "MEDIUM-HIGH", "Active")])

            findings = reg.detect_roster_drift(roster)
            mismatches = [f for f in findings if f["kind"] == "status_mismatch"]
            assert len(mismatches) == 1
            assert "dormant" in mismatches[0]["detail"]

    def test_drift_clean_when_aligned(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            reg.register(**_valid_entry_kwargs(agent_id="pi", status=AgentStatus.ACTIVE))
            roster = self._roster(tmp, [("pi", "Pi", "MEDIUM-HIGH", "Active")])

            findings = reg.detect_roster_drift(roster)
            assert findings == []

    def test_missing_roster_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            with pytest.raises(FileNotFoundError):
                reg.detect_roster_drift(Path(tmp) / "nope.md")


# ----------------------------------------------------------------------
# Importer
# ----------------------------------------------------------------------

class TestImporter:
    def _agents_dir(self, tmp, agents):
        """Build a fake .agents/ dir from (filename, frontmatter_dict) tuples."""
        d = Path(tmp) / "agents"
        d.mkdir()
        for filename, fm in agents:
            lines = ["---"]
            for k, v in fm.items():
                lines.append(f"{k}: {v}")
            lines.extend(["---", "", f"# {fm.get('name', 'agent')}", "Body."])
            (d / filename).write_text("\n".join(lines), encoding="utf-8")
        return d

    def test_import_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            agents_dir = self._agents_dir(tmp, [
                ("pi.md", {"name": "pi", "description": "Pi CLI", "tier": "operational", "model": "nemotron"}),
                ("codex.md", {"name": "codex", "description": "Codex CLI", "tier": "trusted"}),
            ])

            entries = reg.import_from_agents_dir(agents_dir, dry_run=True)
            assert len(entries) == 2
            ids = {e.agent_id for e in entries}
            assert ids == {"pi", "codex"}
            # Dry run should not write to the registry.
            assert reg.list_agents() == []

    def test_import_writes_to_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            agents_dir = self._agents_dir(tmp, [
                ("pi.md", {"name": "pi", "description": "Pi CLI", "tier": "operational"}),
            ])

            entries = reg.import_from_agents_dir(agents_dir)
            assert len(entries) == 1
            assert reg.get("pi") is not None

    def test_import_with_status_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            agents_dir = self._agents_dir(tmp, [
                ("pi.md", {"name": "pi", "description": "Pi CLI", "tier": "operational"}),
            ])

            status_map = {"pi": (AgentStatus.ACTIVE.value, SenderClass.AUTONOMOUS_LLM.value)}
            entries = reg.import_from_agents_dir(agents_dir, status_map=status_map)
            assert entries[0].status == AgentStatus.ACTIVE.value
            assert entries[0].sender_class == SenderClass.AUTONOMOUS_LLM.value

    def test_import_skips_non_canonical_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            agents_dir = self._agents_dir(tmp, [
                ("good.md", {"name": "good-agent", "description": "Good"}),
                # Underscore is not allowed by ^[a-z][a-z0-9-]*$ even after lowercasing.
                ("bad.md", {"name": "bad_name", "description": "Bad"}),
            ])

            entries = reg.import_from_agents_dir(agents_dir, dry_run=True)
            assert len(entries) == 1
            assert entries[0].agent_id == "good-agent"

    def test_import_missing_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = AgentRegistry(registry_path=f"{tmp}/agents.jsonl")
            with pytest.raises(FileNotFoundError):
                reg.import_from_agents_dir(Path(tmp) / "nope")

    def test_tier_to_trust_mapping(self):
        from hummbl_governance.kernel.agent_registry import _tier_to_trust
        assert _tier_to_trust("operational") == "medium_high"
        assert _tier_to_trust("trusted") == "trusted"
        assert _tier_to_trust("emerging") == "probationary"
        assert _tier_to_trust("unknown") == "probationary"


# ----------------------------------------------------------------------
# Integrity (K11) — corrupted lines raise KernelPanic, not silent drop
# ----------------------------------------------------------------------

class TestIntegrity:
    def test_corrupted_line_raises_kernel_panic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agents.jsonl"
            path.write_text(
                json.dumps(AgentEntry(
                    schema_version=SCHEMA_VERSION,
                    timestamp="2026-08-24T00:00:00Z",
                    **_valid_entry_kwargs(),
                ).to_dict()) + "\n"
                "this is not valid json\n",
                encoding="utf-8",
            )
            reg = AgentRegistry(registry_path=str(path))
            with pytest.raises(KernelPanic) as exc_info:
                reg.list_agents()
            assert exc_info.value.invariant == KernelInvariant.INTEGRITY


# ----------------------------------------------------------------------
# Default registry path
# ----------------------------------------------------------------------

class TestDefaultRegistryPath:
    def test_env_var_overrides(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HUMMBL_AGENT_REGISTRY_PATH", str(tmp_path / "custom.jsonl"))
        assert default_registry_path() == tmp_path / "custom.jsonl"

    def test_kernel_state_dir(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HUMMBL_AGENT_REGISTRY_PATH", raising=False)
        monkeypatch.setenv("HUMMBL_KERNEL_STATE_DIR", str(tmp_path))
        assert default_registry_path() == (
            tmp_path / "agent_registry" / "agents.jsonl"
        )

    def test_xdg_state_home(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HUMMBL_AGENT_REGISTRY_PATH", raising=False)
        monkeypatch.delenv("HUMMBL_KERNEL_STATE_DIR", raising=False)
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert default_registry_path() == (
            tmp_path / "hummbl-governance" / "agent_registry" / "agents.jsonl"
        )


# ----------------------------------------------------------------------
# AgentEntry roundtrip
# ----------------------------------------------------------------------

class TestAgentEntry:
    def test_roundtrip(self):
        entry = AgentEntry(
            schema_version=SCHEMA_VERSION,
            agent_id="pi",
            timestamp="2026-08-24T00:00:00Z",
            display_name="Pi CLI",
            status=AgentStatus.ACTIVE.value,
            sender_class=SenderClass.AUTONOMOUS_LLM.value,
            trust_class="medium_high",
            role="Ops",
            hosts=["anvil"],
            tags=["ops"],
        )
        d = entry.to_dict()
        restored = AgentEntry.from_dict(d)
        assert restored.agent_id == entry.agent_id
        assert restored.hosts == ["anvil"]
        assert restored.tags == ["ops"]

    def test_from_dict_ignores_unknown_keys(self):
        entry = AgentEntry.from_dict({
            "agent_id": "pi",
            "display_name": "Pi",
            "status": "active",
            "sender_class": "autonomous_llm",
            "trust_class": "medium_high",
            "role": "Ops",
            "schema_version": SCHEMA_VERSION,
            "timestamp": "2026-08-24T00:00:00Z",
            "unknown_key": "should be ignored",
        })
        assert entry.agent_id == "pi"
        assert not hasattr(entry, "unknown_key")
