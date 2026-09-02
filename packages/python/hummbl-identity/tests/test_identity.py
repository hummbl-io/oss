"""Tests for hummbl-identity."""

import pytest
from hummbl_identity import IdentitySystem, AgentIdentity


class TestIdentitySystem:
    def test_creates_without_dependencies(self):
        assert IdentitySystem() is not None

    def test_agent_names(self):
        identity = IdentitySystem()
        names = identity.agent_names()
        assert "devin" in names
        assert len(names) >= 11

    def test_get_agent_devin(self):
        identity = IdentitySystem()
        devin = identity.get_agent("devin")
        assert devin.name == "devin"
        assert devin.color
        assert devin.role
        assert devin.trust_tier

    def test_get_agent_unknown(self):
        identity = IdentitySystem()
        unknown = identity.get_agent("nonexistent")
        assert unknown.name == "nonexistent"
        assert unknown.trust_tier == "PROBATIONARY"

    def test_all_agents(self):
        identity = IdentitySystem()
        agents = identity.all_agents()
        assert len(agents) >= 11
        assert all(isinstance(a, AgentIdentity) for a in agents)

    def test_agent_color(self):
        identity = IdentitySystem()
        color = identity.agent_color("devin")
        assert color.startswith("#")
        assert len(color) == 7

    def test_trust_tier_color(self):
        identity = IdentitySystem()
        assert identity.trust_tier_color("TRUSTED").startswith("#")

    def test_trust_tier_color_unknown(self):
        identity = IdentitySystem()
        assert identity.trust_tier_color("UNKNOWN") == "#6B7280"

    def test_to_json(self):
        import json
        identity = IdentitySystem()
        data = json.loads(identity.to_json())
        assert isinstance(data, list)
        assert len(data) >= 11

    def test_integration_status(self):
        identity = IdentitySystem()
        status = identity.integration_status
        assert "design_tokens" in status
        assert "heraldry" in status
        assert "garage" in status


class TestAgentIdentity:
    def test_to_dict(self):
        agent = AgentIdentity(name="devin", color="#D63041", role="Primary", trust_tier="MEDIUM-HIGH")
        d = agent.to_dict()
        assert d["name"] == "devin"
        assert d["color"] == "#D63041"

    def test_defaults(self):
        agent = AgentIdentity(name="test")
        assert agent.color == ""
        assert agent.monaspace_voice == "Neon"
        assert agent.watch_state == "idle"


class TestIntegrationWithTokens:
    def test_colors_match_tokens(self):
        identity = IdentitySystem()
        if not identity.has_tokens:
            pytest.skip("design-tokens not installed")
        devin = identity.get_agent("devin")
        assert devin.color == "#D63041"

    def test_trust_tiers_match_tokens(self):
        identity = IdentitySystem()
        if not identity.has_tokens:
            pytest.skip("design-tokens not installed")
        assert identity.get_agent("devin").trust_tier == "MEDIUM-HIGH"
        assert identity.get_agent("codex").trust_tier == "TRUSTED"


class TestIntegrationWithHeraldry:
    def test_blazon_populated(self):
        identity = IdentitySystem()
        if not identity.has_heraldry:
            pytest.skip("heraldry not installed")
        devin = identity.get_agent("devin")
        assert devin.blazon
        assert len(devin.blazon) > 10

    def test_shield_shape_populated(self):
        identity = IdentitySystem()
        if not identity.has_heraldry:
            pytest.skip("heraldry not installed")
        devin = identity.get_agent("devin")
        assert devin.shield_shape

    def test_blazons_differ(self):
        identity = IdentitySystem()
        if not identity.has_heraldry:
            pytest.skip("heraldry not installed")
        assert identity.get_agent("devin").blazon != identity.get_agent("codex").blazon


class TestIntegrationWithGarage:
    def test_dial_finish_from_trust(self):
        identity = IdentitySystem()
        if not identity.has_garage:
            pytest.skip("garage not installed")
        assert identity.get_agent("devin").dial_finish == "guilloche"
        assert identity.get_agent("codex").dial_finish == "enamel"

    def test_performance_scoring(self):
        identity = IdentitySystem()
        if not identity.has_garage:
            pytest.skip("garage not installed")
        devin = identity.get_agent_with_performance(
            "devin", reasoning_speed=8.5, tool_accuracy=9.0,
            context_efficiency=7.5, latency=8.0, safety=9.5, composite=8.0,
        )
        assert devin.api_score > 0
        assert devin.api_class
