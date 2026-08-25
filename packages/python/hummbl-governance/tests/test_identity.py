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

"""Tests for hummbl_governance.identity."""


from hummbl_governance.identity import AgentRegistry


class TestAgentRegistration:
    """Test agent registration."""

    def test_register_agent(self):
        reg = AgentRegistry()
        reg.register_agent("orchestrator", display="Orchestrator", trust="high")
        agents = reg.get_agents()
        assert "orchestrator" in agents
        assert agents["orchestrator"]["trust"] == "high"

    def test_register_default_display(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        assert reg.get_agents()["worker"]["display"] == "Worker"

    def test_unregister_agent(self):
        reg = AgentRegistry()
        reg.register_agent("temp")
        reg.unregister_agent("temp")
        assert "temp" not in reg.get_agents()


class TestAliases:
    """Test alias resolution."""

    def test_add_alias(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        reg.add_alias("worker-1", "worker")
        assert reg.canonicalize("worker-1") == "worker"

    def test_multiple_aliases(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        reg.add_alias("worker-1", "worker")
        reg.add_alias("worker-2", "worker")
        assert reg.canonicalize("worker-1") == "worker"
        assert reg.canonicalize("worker-2") == "worker"

    def test_case_insensitive_alias(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        reg.add_alias("Worker-1", "worker")
        assert reg.canonicalize("worker-1") == "worker"

    def test_parenthetical_stripping(self):
        reg = AgentRegistry()
        reg.register_agent("claude")
        reg.add_alias("claude-code", "claude")
        assert reg.canonicalize("claude-code (terminal)") == "claude"

    def test_remove_alias(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        reg.add_alias("w1", "worker")
        reg.remove_alias("w1")
        # Should return original since alias removed
        assert reg.canonicalize("w1") == "w1"

    def test_unknown_sender_passthrough(self):
        reg = AgentRegistry()
        assert reg.canonicalize("unknown-agent") == "unknown-agent"

    def test_empty_sender(self):
        reg = AgentRegistry()
        assert reg.canonicalize("") == ""
        assert reg.canonicalize("  ") == ""


class TestServices:
    """Test autonomous service registration."""

    def test_add_service(self):
        reg = AgentRegistry()
        reg.add_service("scheduler")
        assert reg.is_valid_sender("scheduler")

    def test_service_canonicalize(self):
        reg = AgentRegistry()
        reg.add_service("scheduler")
        assert reg.canonicalize("scheduler") == "scheduler"

    def test_remove_service(self):
        reg = AgentRegistry()
        reg.add_service("scheduler")
        reg.remove_service("scheduler")
        assert not reg.is_valid_sender("scheduler")


class TestTrustTiers:
    """Test trust tier lookup."""

    def test_agent_trust(self):
        reg = AgentRegistry()
        reg.register_agent("admin", trust="owner")
        assert reg.get_trust_tier("admin") == "owner"

    def test_alias_trust(self):
        reg = AgentRegistry()
        reg.register_agent("worker", trust="medium")
        reg.add_alias("w1", "worker")
        assert reg.get_trust_tier("w1") == "medium"

    def test_service_trust(self):
        reg = AgentRegistry()
        reg.add_service("scheduler")
        assert reg.get_trust_tier("scheduler") == "system"

    def test_unknown_trust(self):
        reg = AgentRegistry()
        assert reg.get_trust_tier("stranger") == "unknown"


class TestStatus:
    """Test status lookup."""

    def test_active_agent(self):
        reg = AgentRegistry()
        reg.register_agent("worker", status="active")
        assert reg.get_status("worker") == "active"

    def test_probation_status(self):
        reg = AgentRegistry()
        reg.register_agent("risky", status="probation")
        assert reg.get_status("risky") == "probation"

    def test_retired_status(self):
        reg = AgentRegistry()
        reg.retire_agent("old-agent", "No longer needed")
        assert reg.get_status("old-agent") == "retired"

    def test_deprecated_status(self):
        reg = AgentRegistry()
        reg.add_deprecated("junk-identity")
        assert reg.get_status("junk-identity") == "deprecated"
        assert reg.is_deprecated("junk-identity")

    def test_unknown_status(self):
        reg = AgentRegistry()
        assert reg.get_status("nobody") == "unknown"


class TestSerialization:
    """Test registry serialization."""

    def test_round_trip(self):
        reg = AgentRegistry()
        reg.register_agent("worker", trust="medium", status="active")
        reg.add_alias("w1", "worker")
        reg.add_service("scheduler")
        reg.add_deprecated("junk")
        reg.retire_agent("old", "gone")

        data = reg.to_dict()
        restored = AgentRegistry.from_dict(data)

        assert restored.canonicalize("w1") == "worker"
        assert restored.get_trust_tier("worker") == "medium"
        assert restored.is_valid_sender("scheduler")
        assert restored.is_deprecated("junk")
        assert restored.get_status("old") == "retired"

    def test_from_dict_empty(self):
        reg = AgentRegistry.from_dict({})
        assert reg.get_agents() == {}


class TestKnownSenders:
    """Test get_known_senders."""

    def test_includes_all_types(self):
        reg = AgentRegistry()
        reg.register_agent("worker")
        reg.add_alias("w1", "worker")
        reg.add_service("scheduler")
        reg.retire_agent("old", "gone")

        known = reg.get_known_senders()
        assert "worker" in known
        assert "w1" in known
        assert "scheduler" in known
        assert "old" in known


class TestConstructorInit:
    """Test initialization from constructor args."""

    def test_init_with_agents(self):
        reg = AgentRegistry(
            agents={"bot": {"display": "Bot", "trust": "low", "status": "active"}},
            aliases={"bot-1": "bot"},
        )
        assert reg.canonicalize("bot-1") == "bot"
        assert reg.get_trust_tier("bot") == "low"
