"""Tests for HUMMBL design token loader and generators."""

import pytest

from hummbl_design_tokens.loader import TokenSystem, load_tokens
from hummbl_design_tokens.generators import (
    generate_base24,
    generate_css,
    generate_python_module,
    generate_typescript_module,
    generate_livery,
    generate_swatches_html,
)


class TestLoader:
    def test_load_default(self):
        ts = TokenSystem()
        assert ts.version == "0.1.0"
        assert ts.canonical_surface == "#0F0F12"

    def test_agents(self):
        ts = TokenSystem()
        names = ts.agent_names()
        assert "devin" in names
        assert "codex" in names
        assert len(names) == 11

    def test_agent_color(self):
        ts = TokenSystem()
        assert ts.agent_color("devin", dark=True) == "#D63041"
        assert ts.agent_color("devin", dark=False) == "#F23645"

    def test_agent_livery(self):
        ts = TokenSystem()
        livery = ts.agent_livery("devin")
        assert livery["agent"] == "devin"
        assert livery["livery"]["accent"] == "#D63041"
        assert livery["livery"]["base"] == "#0F0F12"
        assert "insignia" in livery["livery"]

    def test_bus_types(self):
        ts = TokenSystem()
        assert len(ts.bus_types) == 9
        assert ts.bus_types["PROPOSAL"]["hex"] == "#A21CAF"
        assert ts.bus_types["BLOCKED"]["hex"] == "#DC2626"

    def test_status(self):
        ts = TokenSystem()
        assert ts.status_color("HEALTHY") == "#22C55E"
        assert ts.status_color("CRITICAL") == "#FCA5A5"

    def test_trust_tiers(self):
        ts = TokenSystem()
        assert ts.trust_tier_color("OWNER") == "#1E3A8A"
        assert ts.trust_tier_color("TRUSTED") == "#15803D"


class TestBase24:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_base24(ts)
        assert "scheme: HUMMBL Fleet" in out
        assert "base00" in out
        assert "base17" in out
        assert ts.surfaces["base"] in out

    def test_has_all_24_slots(self):
        ts = TokenSystem()
        out = generate_base24(ts)
        for i in range(24):
            slot = f"base{i:02X}"
            assert slot in out, f"Missing {slot}"


class TestCSS:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_css(ts)
        assert ":root {" in out
        assert "--surface-base" in out
        assert "--agent-devin" in out
        assert "--trust-owner" in out
        assert "--bus-proposal" in out
        assert "--status-healthy" in out
        assert "--font-mono" in out

    def test_agent_keys_underscore(self):
        ts = TokenSystem()
        out = generate_css(ts)
        assert "--agent-claude_code" in out  # hyphen -> underscore


class TestPythonModule:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_python_module(ts)
        assert "AGENTS = {" in out
        assert "TRUST_TIERS = {" in out
        assert "BUS_TYPES = {" in out
        assert "STATUS = {" in out
        assert '"devin"' in out

    def test_valid_python(self):
        ts = TokenSystem()
        out = generate_python_module(ts)
        # Execute the generated code to verify it's valid Python
        ns = {}
        exec(out, ns)
        assert "devin" in ns["AGENTS"]
        assert ns["TRUST_TIERS"]["OWNER"] == "#1E3A8A"


class TestTypeScriptModule:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_typescript_module(ts)
        assert "export const SURFACES" in out
        assert "export const AGENTS" in out
        assert "export const TRUST_TIERS" in out
        assert "as const;" in out


class TestLivery:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_livery(ts, "devin")
        assert "agent: devin" in out
        assert "accent:" in out
        assert "insignia:" in out

    def test_all_agents(self):
        ts = TokenSystem()
        for name in ts.agent_names():
            out = generate_livery(ts, name)
            assert f"agent: {name}" in out


class TestSwatches:
    def test_generates(self):
        ts = TokenSystem()
        out = generate_swatches_html(ts)
        assert "<!DOCTYPE html>" in out
        assert "HUMMBL Design Token Swatches" in out
        assert "Agent Identity" in out
        assert "Trust Tier" in out
        assert "Bus Message" in out
        assert "Status" in out
        assert "Contrast Verification" in out

    def test_contains_all_agents(self):
        ts = TokenSystem()
        out = generate_swatches_html(ts)
        for name in ts.agent_names():
            assert name in out
