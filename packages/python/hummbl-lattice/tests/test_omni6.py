# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Gold experiments for Omni6 (experimental_not_canonical)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_lattice.omni6 import (
    KINDS,
    KNOWN_CANONS,
    STOPPING_RULE,
    Canon,
    JoinError,
    Relation,
    assert_kind_matrix_closed,
    classify,
    illegal_base120_codes,
    join_canons,
    kind_matrix,
    kind_relation,
    scan_topology,
)

_TOPOLOGY = (
    Path(__file__).resolve().parents[2] / "hummbl-compass" / "hummbl-topology.json"
)


class TestKindMatrix:
    def test_closed_and_maps_to_base120_families(self):
        assert_kind_matrix_closed()
        matrix = kind_matrix()
        assert len(matrix) == 36
        assert set(KINDS) == {"FR", "BR", "BG", "PT", "SC", "GV"}

    def test_pt_gv_default_is_barrier(self):
        assert kind_relation("PT", "GV") is Relation.ORTHOGONAL
        assert kind_relation("GV", "PT") is Relation.ORTHOGONAL

    def test_gv_supersedes_bridge(self):
        assert kind_relation("GV", "BG") is Relation.SUPERSEDES
        assert kind_relation("BG", "GV") is Relation.SUPERSEDES

    def test_stopping_rule_rejects_fields(self):
        assert "not a field of study" in STOPPING_RULE.lower()
        with pytest.raises(KeyError, match="not a known canon"):
            classify("biology")


class TestGmOm000:
    """Base120 is PT; Domain120 is SC(Base120); Domain120 is not a PT of fields."""

    def test_base120_is_partition(self):
        assert classify("base120").kind == "PT"

    def test_domain120_is_scale_of_partition(self):
        d = classify("domain120")
        assert d.kind == "SC"
        assert "PT" in d.secondary

    def test_domain120_is_not_a_field_partition(self):
        assert classify("domain120").kind != "PT"
        receipt = join_canons("base120", "domain120")
        assert receipt.relation is Relation.COMPOSED
        assert not receipt.barrier


class TestGmOm001:
    """INT × ANI-ASI requires explicit ↦ and governance_delta."""

    def test_default_join_is_barrier(self):
        receipt = join_canons("int", "ani-asi")
        assert receipt.barrier
        assert receipt.relation is Relation.ORTHOGONAL

    def test_claimed_compose_is_illegal(self):
        with pytest.raises(JoinError, match="illegal"):
            join_canons("int", "ani-asi", claimed=Relation.COMPOSED)

    def test_explicit_bind_requires_governance_delta(self):
        with pytest.raises(JoinError, match="governance_delta"):
            join_canons(
                "int",
                "ani-asi",
                claimed=Relation.BOUND,
                governance_delta=False,
            )

    def test_explicit_bind_with_delta(self):
        receipt = join_canons(
            "int",
            "ani-asi",
            claimed=Relation.BOUND,
            governance_delta=True,
        )
        assert receipt.relation is Relation.BOUND
        assert receipt.governance_delta is True
        assert not receipt.barrier


class TestGmOm002:
    """IN18 ⊥ RE8 remains a barrier at Omni6 (kill-criteria ⊥ root-cause)."""

    def test_instance_barrier(self):
        receipt = join_canons("kill-criteria", "root-cause")
        assert receipt.barrier
        assert receipt.relation is Relation.ORTHOGONAL

    def test_claimed_compose_blocked(self):
        with pytest.raises(JoinError):
            join_canons("in18", "re8", claimed="∘")

    def test_reverse_also_barred(self):
        assert join_canons("root-cause", "kill-criteria").barrier


class TestGmOm003:
    """Compass topology must use real Base120 codes; GO* is illegal."""

    def test_go_codes_are_illegal(self):
        assert illegal_base120_codes(["GO1", "GO3", "SY11"]) == ["GO1", "GO3"]

    def test_topology_has_no_illegal_codes(self):
        data = json.loads(_TOPOLOGY.read_text(encoding="utf-8"))
        findings = scan_topology(data["repos"])
        assert findings == [], findings

    def test_topology_has_twenty_five_packages(self):
        data = json.loads(_TOPOLOGY.read_text(encoding="utf-8"))
        assert len(data["repos"]) == 25


class TestCanon:
    def test_rejects_unknown_kind(self):
        with pytest.raises(ValueError, match="Invalid CanonKind"):
            Canon("x", "XX")

    def test_max_two_secondaries(self):
        with pytest.raises(ValueError, match="At most two"):
            Canon("x", "PT", ("FR", "BR", "BG"))

    def test_known_canons_are_valid(self):
        for canon in KNOWN_CANONS.values():
            assert canon.kind in KINDS

    def test_receipt_dict(self):
        d = join_canons("seed20", "basen").to_dict()
        assert d["relation"] in {r.value for r in Relation}
        assert d["promotion_status"] == "experimental_not_canonical"
