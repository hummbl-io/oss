# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Tests for hummbl_governance.regulatory_context."""
import pytest
from hummbl_governance.regulatory_context import (
    ControlSet, RegulatoryContext,
    RegulatoryProfile,
)

class TestRegulatoryProfile:
    def test_from_str_high_risk(self):
        assert RegulatoryProfile.from_str("high-risk") == RegulatoryProfile.HIGH_RISK
    def test_from_str_limited_risk(self):
        assert RegulatoryProfile.from_str("limited-risk") == RegulatoryProfile.LIMITED_RISK
    def test_from_str_minimal_risk(self):
        assert RegulatoryProfile.from_str("minimal-risk") == RegulatoryProfile.MINIMAL_RISK
    def test_from_str_non_ai(self):
        assert RegulatoryProfile.from_str("non-ai") == RegulatoryProfile.NON_AI
    def test_from_str_case_insensitive(self):
        assert RegulatoryProfile.from_str("High-Risk") == RegulatoryProfile.HIGH_RISK
    def test_from_str_underscore_normalized(self):
        assert RegulatoryProfile.from_str("high_risk") == RegulatoryProfile.HIGH_RISK
    def test_from_str_invalid(self):
        with pytest.raises(ValueError, match="Invalid regulatory profile"):
            RegulatoryProfile.from_str("unknown-risk")

class TestControlSet:
    def test_empty_control_set(self):
        cs = ControlSet()
        assert cs.total == 0
        assert cs.to_dict() == {"eu_ai_act": [], "nist_ai_rmf": [], "soc2": [], "gdpr": [], "owasp_asi": []}
    def test_total_counts_all_frameworks(self):
        cs = ControlSet(eu_ai_act=["a","b"], nist_ai_rmf=["c"], soc2=["d"], gdpr=["e"], owasp_asi=["f","g"])
        assert cs.total == 7

class TestRegulatoryContextCheck:
    def test_high_risk_prohibited_action(self):
        assert not RegulatoryContext().check("high-risk", "ungoverned_bus_writes").permitted
    def test_high_risk_consequential_action_permitted_with_requirements(self):
        r = RegulatoryContext().check("high-risk", "file_write")
        assert r.permitted and r.requires_audit_log and r.requires_delegation_token and r.requires_receipt
    def test_high_risk_non_consequential_action_permitted(self):
        r = RegulatoryContext().check("high-risk", "read")
        assert r.permitted and not r.requires_audit_log and not r.requires_delegation_token
    def test_high_risk_requires_human_oversight_for_consequential(self):
        r = RegulatoryContext().check("high-risk", "exec")
        assert r.permitted and r.requires_human_oversight
    def test_limited_risk_no_human_oversight(self):
        r = RegulatoryContext().check("limited-risk", "file_write")
        assert r.permitted and not r.requires_human_oversight and r.requires_audit_log
    def test_minimal_risk_no_requirements(self):
        r = RegulatoryContext().check("minimal-risk", "file_write")
        assert r.permitted and not r.requires_human_oversight and not r.requires_audit_log
    def test_non_ai_no_controls(self):
        r = RegulatoryContext().check("non-ai", "anything")
        assert r.permitted and r.applicable_controls is not None and r.applicable_controls.total == 0
    def test_check_with_enum_profile(self):
        r = RegulatoryContext().check(RegulatoryProfile.HIGH_RISK, "read")
        assert r.permitted and r.profile == RegulatoryProfile.HIGH_RISK
    def test_check_unknown_profile_string(self):
        with pytest.raises(ValueError):
            RegulatoryContext().check("unknown-profile", "read")
    def test_high_risk_bypassing_human_oversight_prohibited(self):
        assert not RegulatoryContext().check("high-risk", "bypassing_human_oversight").permitted
    def test_high_risk_unauthorized_data_processing_prohibited(self):
        assert not RegulatoryContext().check("high-risk", "unauthorized_data_processing").permitted

class TestRegulatoryContextGetControls:
    def test_high_risk_controls(self):
        c = RegulatoryContext().get_controls("high-risk")
        assert "art_14_human_oversight" in c.eu_ai_act
        assert "GOVERN_1_1" in c.nist_ai_rmf
        assert "CC6_1" in c.soc2
        assert "ASI01" in c.owasp_asi
        assert c.total > 10
    def test_limited_risk_controls(self):
        c = RegulatoryContext().get_controls("limited-risk")
        assert "art_50_transparency" in c.eu_ai_act
        assert len(c.nist_ai_rmf) == 2
    def test_minimal_risk_controls(self):
        c = RegulatoryContext().get_controls("minimal-risk")
        assert c.eu_ai_act == [] and c.nist_ai_rmf == ["GOVERN_1_1"]
    def test_non_ai_controls_empty(self):
        assert RegulatoryContext().get_controls("non-ai").total == 0

class TestRegulatoryContextGetConfig:
    def test_high_risk_config(self):
        c = RegulatoryContext().get_config("high-risk")
        assert c.requires_human_oversight and c.requires_audit_log and c.requires_transparency_disclosure
        assert "ungoverned_bus_writes" in c.prohibited_actions
    def test_minimal_risk_config(self):
        c = RegulatoryContext().get_config("minimal-risk")
        assert not c.requires_human_oversight and not c.requires_audit_log
    def test_get_config_invalid_profile(self):
        with pytest.raises(ValueError):
            RegulatoryContext().get_config("nonexistent")

class TestAwarenessBlock:
    def test_high_risk_block_contains_profile(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "high-risk" in b and "Regulatory Context" in b
    def test_high_risk_block_contains_eu_ai_act(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "EU AI Act" in b and "art_14_human_oversight" in b
    def test_high_risk_block_contains_nist(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "NIST AI RMF" in b and "GOVERN_1_1" in b
    def test_high_risk_block_contains_human_oversight(self):
        assert "Human oversight required" in RegulatoryContext().awareness_block("high-risk")
    def test_high_risk_block_contains_prohibited(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "Prohibited actions" in b and "ungoverned_bus_writes" in b
    def test_block_with_agent_name(self):
        assert "foucault" in RegulatoryContext().awareness_block("high-risk", agent_name="foucault")
    def test_minimal_risk_block_minimal(self):
        b = RegulatoryContext().awareness_block("minimal-risk")
        assert "minimal-risk" in b and "Human oversight" not in b
    def test_non_ai_block_empty_controls(self):
        assert "non-ai" in RegulatoryContext().awareness_block("non-ai")
    def test_block_contains_required_steps(self):
        b = RegulatoryContext().awareness_block("high-risk")
        for s in ["AuthorityEngine", "DelegationTokenManager", "ReceiptEngine", "AuditLog"]:
            assert s in b
    def test_block_contains_owasp_asi(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "OWASP ASI" in b and "ASI01" in b
    def test_block_contains_soc2(self):
        assert "SOC 2" in RegulatoryContext().awareness_block("high-risk")
    def test_block_contains_gdpr(self):
        b = RegulatoryContext().awareness_block("high-risk")
        assert "GDPR" in b
