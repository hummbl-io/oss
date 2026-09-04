# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Tests for AuthorityEngine + RegulatoryContext integration."""
import json
from pathlib import Path
from hummbl_governance.kernel.authority_engine import AuthorityEngine, AuthorityCheck

class TestAuthorityRegulatoryIntegration:
    def test_arcana_advisory_role_exists(self):
        with open(Path(__file__).parent.parent / "hummbl_governance" / "data" / "authority_policy.json") as f:
            p = json.load(f)
        assert "arcana-advisory" in p["roles"]
        assert p["roles"]["arcana-advisory"]["regulatory_profile"] == "high-risk"
    def test_devin_role_has_regulatory_profile(self):
        with open(Path(__file__).parent.parent / "hummbl_governance" / "data" / "authority_policy.json") as f:
            p = json.load(f)
        assert "regulatory_profile" in p["roles"]["devin"]
    def test_authority_check_includes_regulatory_fields(self):
        c = AuthorityCheck(permitted=True, reason="test")
        assert hasattr(c, "regulatory_profile") and hasattr(c, "regulatory_controls")
        assert c.regulatory_profile == "" and c.regulatory_controls is None
    def test_authority_engine_has_regulatory_method(self, tmp_path):
        e = AuthorityEngine(state_dir=tmp_path)
        assert hasattr(e, "_check_regulatory") and hasattr(e, "_regulatory_ctx")
    def test_regulatory_check_blocks_prohibited_action(self, tmp_path):
        assert not AuthorityEngine(state_dir=tmp_path)._check_regulatory("high-risk", "ungoverned_bus_writes").permitted
    def test_regulatory_check_allows_safe_action(self, tmp_path):
        assert AuthorityEngine(state_dir=tmp_path)._check_regulatory("high-risk", "read").permitted
    def test_structured_check_includes_regulatory_profile(self, tmp_path):
        e = AuthorityEngine(state_dir=tmp_path)
        p = e._load_policy()
        if p:
            r = e._check_structured(p, "devin", "bus_post", {})
            assert hasattr(r, "regulatory_profile")
            if r.permitted:
                assert r.regulatory_profile == "high-risk"
