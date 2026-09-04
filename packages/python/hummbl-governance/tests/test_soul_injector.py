# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Tests for hummbl_governance.soul_injector.

These are integration tests that require fleet SOUL.md files at
``~/.agents/agents/souls/``. They are skipped on CI runners where
those files are not present (e.g. the Windows self-hosted runner).
"""
import pytest
from pathlib import Path
from hummbl_governance.soul_injector import SoulInjector

FOUCAULT_SOUL = Path.home() / ".agents" / "agents" / "souls" / "foucault" / "SOUL.md"
GODMODE_SOUL = Path.home() / ".agents" / "agents" / "souls" / "god-mode" / "SOUL.md"

skip_if_no_souls = pytest.mark.skipif(
    not FOUCAULT_SOUL.exists() or not GODMODE_SOUL.exists(),
    reason="Fleet SOUL.md files not present (integration test requires ~/.agents/agents/souls/)",
)

@pytest.fixture
def injector():
    return SoulInjector()

class TestSoulInjectorParse:
    @skip_if_no_souls
    def test_parse_foucault(self, injector):
        fm, body = injector._parse_soul(FOUCAULT_SOUL)
        assert fm["name"] == "foucault"
        assert "Archaeologist" in fm["description"]
        assert len(body) > 50
    @skip_if_no_souls
    def test_parse_god_mode(self, injector):
        fm, body = injector._parse_soul(GODMODE_SOUL)
        assert fm["name"] == "god-mode"
        assert "autonomous" in fm["description"]
        assert len(body) > 100

class TestSoulInjectorResolve:
    @skip_if_no_souls
    def test_resolve_foucault_has_governance(self, injector):
        gov = injector.get_resolved(FOUCAULT_SOUL).get("governance", {})
        assert isinstance(gov, dict)
        assert gov.get("trust_tier") == "MEDIUM"
        assert gov.get("regulatory_profile") == "high-risk"
        assert gov.get("authority_scope") == "advisory"
    @skip_if_no_souls
    def test_resolve_foucault_inherits_from_base(self, injector):
        gov = injector.get_resolved(FOUCAULT_SOUL).get("governance", {})
        assert gov.get("delegation_required") is True
    @skip_if_no_souls
    def test_resolve_god_mode(self, injector):
        gov = injector.get_resolved(GODMODE_SOUL).get("governance", {})
        assert gov.get("trust_tier") == "HIGH"
        assert gov.get("authority_scope") == "executive"
        assert gov.get("regulatory_profile") == "high-risk"

class TestSoulInjectorInject:
    @skip_if_no_souls
    def test_inject_foucault_contains_persona(self, injector):
        p = injector.inject(FOUCAULT_SOUL)
        assert "FOUCAULT" in p and "Archaeologist" in p
    @skip_if_no_souls
    def test_inject_foucault_contains_regulatory(self, injector):
        p = injector.inject(FOUCAULT_SOUL)
        assert "Regulatory Context" in p and "high-risk" in p and "EU AI Act" in p
    @skip_if_no_souls
    def test_inject_foucault_contains_identity(self, injector):
        p = injector.inject(FOUCAULT_SOUL)
        assert "Agent Identity" in p and "foucault" in p and "MEDIUM" in p and "advisory" in p
    @skip_if_no_souls
    def test_inject_persona_only(self, injector):
        p = injector.inject_persona_only(FOUCAULT_SOUL)
        assert "FOUCAULT" in p and "Regulatory Context" not in p
    @skip_if_no_souls
    def test_inject_regulatory_only(self, injector):
        p = injector.inject_regulatory_only(FOUCAULT_SOUL)
        assert "Regulatory Context" in p
    @skip_if_no_souls
    def test_inject_god_mode(self, injector):
        p = injector.inject(GODMODE_SOUL)
        assert "god-mode" in p or "God Mode" in p
        assert "Regulatory Context" in p and "HIGH" in p

class TestSoulInjectorIdentitySummary:
    @skip_if_no_souls
    def test_identity_summary_foucault(self, injector):
        s = injector._generate_identity_summary(injector.get_resolved(FOUCAULT_SOUL))
        assert "foucault" in s and "MEDIUM" in s and "advisory" in s
        assert "high-risk" in s and "Delegation required" in s
