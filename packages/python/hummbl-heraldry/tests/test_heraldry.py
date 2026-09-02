"""Tests for hummbl-heraldry."""

import json
import hashlib
from pathlib import Path

import pytest

from hummbl_heraldry import (
    ArmsGenerator,
    Grammar,
    AgentArms,
    generate_all_arms,
    AGENTS,
)
from hummbl_heraldry.svg import (
    render_arms_svg,
    render_fleet_arms_svg,
    render_ics_flag_svg,
)


class TestGrammar:
    def test_shield_shapes(self):
        g = Grammar()
        assert len(g.shield_shapes()) == 7

    def test_tinctures(self):
        g = Grammar()
        assert len(g.tinctures()) == 9
        ids = [t.id for t in g.tinctures()]
        assert "or" in ids
        assert "argent" in ids
        assert "sable" in ids

    def test_divisions(self):
        g = Grammar()
        assert len(g.divisions()) == 10

    def test_ordinaries(self):
        g = Grammar()
        assert len(g.ordinaries()) == 8

    def test_charges(self):
        g = Grammar()
        assert len(g.charges()) >= 30

    def test_cadency_marks(self):
        g = Grammar()
        marks = g.cadency_marks()
        assert len(marks) == 5
        tiers = [m.trust_tier for m in marks]
        assert "OWNER" in tiers
        assert "TRUSTED" in tiers
        assert "PROBATIONARY" in tiers

    def test_role_badges(self):
        g = Grammar()
        assert len(g.role_badges()) == 6

    def test_host_patches(self):
        g = Grammar()
        assert len(g.host_patches()) == 5

    def test_ics_flags(self):
        g = Grammar()
        flags = g.ics_flags()
        assert len(flags) == 9
        types = [f.bus_type for f in flags]
        assert "PROPOSAL" in types
        assert "BLOCKED" in types

    def test_fleet_arms(self):
        g = Grammar()
        fleet = g.fleet_arms()
        assert fleet["name"] == "HUMMBL LLC"
        assert "pall reversed" in fleet["blazon"]
        assert "cogwheel" in fleet["blazon"]

    def test_find_tincture(self):
        g = Grammar()
        t = g.find_tincture("sable")
        assert t is not None
        assert t.name == "Sable"
        assert t.category == "color"

    def test_find_cadency(self):
        g = Grammar()
        c = g.find_cadency("TRUSTED")
        assert c is not None
        assert c.id == "label"

    def test_find_cadency_owner(self):
        g = Grammar()
        c = g.find_cadency("OWNER")
        assert c is not None
        assert c.id == "none"


class TestGenerator:
    def test_deterministic(self):
        gen = ArmsGenerator()
        arms1 = gen.generate("devin")
        arms2 = gen.generate("devin")
        assert arms1.hash == arms2.hash
        assert arms1.blazon == arms2.blazon
        assert arms1.shield.id == arms2.shield.id

    def test_different_agents_different_arms(self):
        gen = ArmsGenerator()
        arms_devin = gen.generate("devin")
        arms_codex = gen.generate("codex")
        assert arms_devin.hash != arms_codex.hash
        # At least one component should differ
        components_differ = (
            arms_devin.shield.id != arms_codex.shield.id or
            arms_devin.field_tincture.id != arms_codex.field_tincture.id or
            arms_devin.division.id != arms_codex.division.id or
            arms_devin.charge.id != arms_codex.charge.id
        )
        assert components_differ

    def test_hash_matches_sha256(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin")
        expected = hashlib.sha256(b"devin").hexdigest()
        assert arms.hash == expected

    def test_blazon_not_empty(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin")
        assert arms.blazon
        assert len(arms.blazon) > 10

    def test_blazon_starts_capital(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin")
        assert arms.blazon[0].isupper()

    def test_with_trust_tier(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", trust_tier="MEDIUM-HIGH")
        assert arms.cadency is not None
        assert arms.cadency.trust_tier == "MEDIUM-HIGH"
        assert arms.cadency.id == "crescent"

    def test_with_trust_tier_owner(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", trust_tier="OWNER")
        assert arms.cadency is not None
        assert arms.cadency.id == "none"

    def test_with_role(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", role="coordinator")
        assert arms.role_badge is not None
        assert arms.role_badge.role == "coordinator"
        assert arms.role_badge.icon == "★"

    def test_with_host(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", host="delta")
        assert arms.host_patch is not None
        assert arms.host_patch.id == "delta"

    def test_with_skill_tabs(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", skill_tabs=["bus-protocol", "gpg-signing"])
        assert arms.skill_tabs == ["bus-protocol", "gpg-signing"]

    def test_to_dict(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin", trust_tier="MEDIUM-HIGH", role="coordinator", host="delta")
        d = arms.to_dict()
        assert d["agent_name"] == "devin"
        assert d["hash"]
        assert d["shield"]
        assert d["field_tincture"]
        assert d["cadency"] == "crescent"
        assert d["role_badge"] == "star"
        assert d["host_patch"] == "delta"

    def test_rule_of_tincture_field_vs_charge(self):
        """Charge tincture should obey the rule of tincture vs field."""
        gen = ArmsGenerator()
        for agent_name in ["devin", "codex", "claude-code", "gemini", "hermes"]:
            arms = gen.generate(agent_name)
            if arms.charge.id != "none" and arms.charge_tincture:
                field_is_metal = arms.field_tincture.category in ("metal", "fur")
                charge_is_metal = arms.charge_tincture.category in ("metal", "fur")
                # If field is fur, charge can be anything
                if arms.field_tincture.category != "fur":
                    assert field_is_metal != charge_is_metal, (
                        f"{agent_name}: field={arms.field_tincture.id} ({arms.field_tincture.category}), "
                        f"charge={arms.charge_tincture.id} ({arms.charge_tincture.category}) — rule of tincture violated"
                    )

    def test_all_11_agents(self):
        all_arms = generate_all_arms()
        assert len(all_arms) == 11
        for name, arms in all_arms.items():
            assert arms.agent_name == name
            assert arms.blazon
            assert arms.hash

    def test_all_agents_unique_blazons(self):
        all_arms = generate_all_arms()
        blazons = [arms.blazon for arms in all_arms.values()]
        # At least some should be unique (not all, since grammar is constrained)
        unique = set(blazons)
        assert len(unique) >= 5, f"Only {len(unique)} unique blazons out of 11"


class TestSVG:
    def test_render_arms_svg(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin")
        svg = render_arms_svg(arms)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "devin" in svg

    def test_render_arms_svg_has_path(self):
        gen = ArmsGenerator()
        arms = gen.generate("devin")
        svg = render_arms_svg(arms)
        assert "<path" in svg

    def test_render_fleet_arms_svg(self):
        svg = render_fleet_arms_svg()
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "HUMMBL LLC" in svg

    def test_render_ics_flags(self):
        g = Grammar()
        for flag in g.ics_flags():
            svg = render_ics_flag_svg(flag.bus_type, flag.color_scheme)
            assert svg.startswith("<svg")
            assert svg.endswith("</svg>")

    def test_ics_flag_bravo(self):
        svg = render_ics_flag_svg("BLOCKED", "red swallowtail")
        assert "#DC2626" in svg  # red

    def test_ics_flag_quebec(self):
        svg = render_ics_flag_svg("QUESTION", "yellow")
        assert "#E6B800" in svg  # gold/yellow


class TestCLI:
    def test_info(self):
        from hummbl_heraldry.__main__ import main
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["info"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert rc == 0
        assert "HUMMBL Heraldric" in output
        assert "Combinations" in output

    def test_blazon(self):
        from hummbl_heraldry.__main__ import main
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["blazon", "devin"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert rc == 0
        assert len(output.strip()) > 10

    def test_generate_json(self):
        from hummbl_heraldry.__main__ import main
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["generate", "devin", "--json"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert rc == 0
        data = json.loads(output)
        assert data["agent_name"] == "devin"
