# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0

"""Omni6 — taxonomy of taxonomies (experimental, not Base120 canon).

A CanonKind names how a classification cuts, not a field of study.
Joins use Seed20 relation vocabulary. Status: experimental_not_canonical.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from hummbl_lattice.models import BASE120_ANCESTORS, FAMILIES

KINDS: tuple[str, ...] = ("FR", "BR", "BG", "PT", "SC", "GV")

KIND_FAMILY: dict[str, str] = {
    "FR": "P",
    "BR": "IN",
    "BG": "CO",
    "PT": "DE",
    "SC": "RE",
    "GV": "SY",
}

KIND_NAMES: dict[str, str] = {
    "FR": "Frame-canon",
    "BR": "Barrier-canon",
    "BG": "Bridge-canon",
    "PT": "Partition-canon",
    "SC": "Scale-canon",
    "GV": "Governance-canon",
}

STOPPING_RULE = (
    "An Omni6 code names how a classification cuts, not a field of study. "
    "Biology is Domain120. Object-partition is Omni6."
)


class Relation(str, Enum):
    """Seed20 join vocabulary."""

    ORTHOGONAL = "⊥"
    COMPOSED = "∘"
    PARALLEL = "⊗"
    ENTAILS = "⇒"
    DUAL = "⇔"
    BOUND = "↦"
    SUPERSEDES = "≻"


# Kind × kind default relation. Instance barriers can still force ⊥.
_KIND_MATRIX: dict[tuple[str, str], Relation] = {
    ("FR", "FR"): Relation.DUAL,
    ("FR", "BR"): Relation.BOUND,
    ("FR", "BG"): Relation.COMPOSED,
    ("FR", "PT"): Relation.COMPOSED,
    ("FR", "SC"): Relation.COMPOSED,
    ("FR", "GV"): Relation.BOUND,
    ("BR", "FR"): Relation.BOUND,
    ("BR", "BR"): Relation.DUAL,
    ("BR", "BG"): Relation.PARALLEL,
    ("BR", "PT"): Relation.COMPOSED,
    ("BR", "SC"): Relation.COMPOSED,
    ("BR", "GV"): Relation.ENTAILS,
    ("BG", "FR"): Relation.COMPOSED,
    ("BG", "BR"): Relation.PARALLEL,
    ("BG", "BG"): Relation.COMPOSED,
    ("BG", "PT"): Relation.COMPOSED,
    ("BG", "SC"): Relation.COMPOSED,
    ("BG", "GV"): Relation.SUPERSEDES,
    ("PT", "FR"): Relation.COMPOSED,
    ("PT", "BR"): Relation.COMPOSED,
    ("PT", "BG"): Relation.COMPOSED,
    ("PT", "PT"): Relation.DUAL,
    ("PT", "SC"): Relation.COMPOSED,
    ("PT", "GV"): Relation.ORTHOGONAL,
    ("SC", "FR"): Relation.COMPOSED,
    ("SC", "BR"): Relation.COMPOSED,
    ("SC", "BG"): Relation.COMPOSED,
    ("SC", "PT"): Relation.COMPOSED,
    ("SC", "SC"): Relation.COMPOSED,
    ("SC", "GV"): Relation.BOUND,
    ("GV", "FR"): Relation.BOUND,
    ("GV", "BR"): Relation.ENTAILS,
    ("GV", "BG"): Relation.SUPERSEDES,
    ("GV", "PT"): Relation.ORTHOGONAL,
    ("GV", "SC"): Relation.BOUND,
    ("GV", "GV"): Relation.ENTAILS,
}


@dataclass(frozen=True, slots=True)
class Canon:
    """A named classification with one primary Omni6 kind."""

    name: str
    kind: str
    secondary: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"Invalid CanonKind {self.kind!r}. Must be one of {KINDS}.")
        extra = tuple(k for k in self.secondary if k not in KINDS)
        if extra:
            raise ValueError(f"Invalid secondary kinds {extra}. Must be one of {KINDS}.")
        if len(self.secondary) > 2:
            raise ValueError("At most two secondary kinds (compass rule).")
        if self.kind in self.secondary:
            raise ValueError("Secondary kinds must not repeat the primary.")


@dataclass(frozen=True, slots=True)
class JoinReceipt:
    """Typed join of two canons."""

    left: str
    left_kind: str
    right: str
    right_kind: str
    relation: Relation
    governance_delta: bool
    barrier: bool
    notes: str = ""
    promotion_status: str = "experimental_not_canonical"

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left,
            "left_kind": self.left_kind,
            "right": self.right,
            "right_kind": self.right_kind,
            "relation": self.relation.value,
            "governance_delta": self.governance_delta,
            "barrier": self.barrier,
            "notes": self.notes,
            "promotion_status": self.promotion_status,
        }


KNOWN_CANONS: dict[str, Canon] = {
    "base120": Canon("base120", "PT", ("FR",)),
    "domain120": Canon("domain120", "SC", ("PT",)),
    "basen": Canon("basen", "BG"),
    "seed20": Canon("seed20", "BR", ("BG",)),
    "compass-layers": Canon("compass-layers", "SC"),
    "int": Canon("int", "PT"),
    "ani-asi": Canon("ani-asi", "GV"),
    "trust-tiers": Canon("trust-tiers", "GV"),
    "promotion-ladder": Canon("promotion-ladder", "SC"),
    "kill-criteria": Canon("kill-criteria", "BR", ("GV",)),
    "root-cause": Canon("root-cause", "PT"),
    "in18": Canon("in18", "BR", ("GV",)),
    "re8": Canon("re8", "PT"),
}

# Instance-level barriers (Seed20 IN18 ⊥ RE8).
INSTANCE_BARRIERS: frozenset[tuple[str, str]] = frozenset(
    {
        ("kill-criteria", "root-cause"),
        ("root-cause", "kill-criteria"),
        ("in18", "re8"),
        ("re8", "in18"),
    }
)


class JoinError(ValueError):
    """Raised when a claimed join violates Omni6."""


def kind_relation(left_kind: str, right_kind: str) -> Relation:
    """Return the default kind×kind relation."""
    if left_kind not in KINDS or right_kind not in KINDS:
        raise ValueError(f"Kinds must be in {KINDS}")
    return _KIND_MATRIX[(left_kind, right_kind)]


def kind_matrix() -> dict[tuple[str, str], str]:
    """Closed 6×6 matrix as kind-pair → symbol."""
    return {pair: rel.value for pair, rel in _KIND_MATRIX.items()}


def classify(name: str) -> Canon:
    """Look up a known canon. Unknown names are not silently framed as fields."""
    key = name.strip().lower()
    if key not in KNOWN_CANONS:
        raise KeyError(
            f"{name!r} is not a known canon. Register a CanonKind; "
            "do not treat a field of study as Omni6."
        )
    return KNOWN_CANONS[key]


def join_canons(
    left: Canon | str,
    right: Canon | str,
    *,
    claimed: Relation | str | None = None,
    governance_delta: bool | None = None,
) -> JoinReceipt:
    """Typed join. Barriers win. GV requires an explicit governance delta."""
    left_c = classify(left) if isinstance(left, str) else left
    right_c = classify(right) if isinstance(right, str) else right
    pair = (left_c.name.lower(), right_c.name.lower())
    instance_barrier = pair in INSTANCE_BARRIERS
    relation = (
        Relation.ORTHOGONAL
        if instance_barrier
        else kind_relation(left_c.kind, right_c.kind)
    )
    claimed_rel = None
    if claimed is not None:
        claimed_rel = claimed if isinstance(claimed, Relation) else Relation(claimed)
        pt_gv = {left_c.kind, right_c.kind} == {"PT", "GV"}
        # PT ⟂ GV by default. Explicit ↦ with governance_delta is the only legal bind.
        if (
            relation is Relation.ORTHOGONAL
            and claimed_rel is Relation.BOUND
            and pt_gv
            and not instance_barrier
        ):
            relation = Relation.BOUND
        elif relation is Relation.ORTHOGONAL and claimed_rel is not Relation.ORTHOGONAL:
            raise JoinError(
                f"{left_c.name} ⊥ {right_c.name}: claimed {claimed_rel.value} is illegal"
            )
    gv_involved = left_c.kind == "GV" or right_c.kind == "GV" or "GV" in left_c.secondary or "GV" in right_c.secondary
    if gv_involved and relation is not Relation.ORTHOGONAL:
        if governance_delta is False:
            raise JoinError(
                f"{left_c.name} × {right_c.name} involves GV; "
                "governance_delta must be true or the join is vocabulary-only"
            )
        if governance_delta is None:
            governance_delta = True
    elif governance_delta is None:
        governance_delta = False
    barrier = relation is Relation.ORTHOGONAL
    notes = ""
    if barrier:
        notes = "barrier: do not mash; receipt IN18/IN7"
    elif gv_involved:
        notes = "GV join: may_act must change"
    return JoinReceipt(
        left=left_c.name,
        left_kind=left_c.kind,
        right=right_c.name,
        right_kind=right_c.kind,
        relation=relation,
        governance_delta=bool(governance_delta),
        barrier=barrier,
        notes=notes,
    )


def illegal_base120_codes(codes: Iterable[str]) -> list[str]:
    """Return codes that are not in the Base120 6×20 set (e.g. GO1)."""
    bad: list[str] = []
    for raw in codes:
        code = str(raw).strip()
        if not code:
            continue
        if code not in BASE120_ANCESTORS:
            bad.append(code)
    return bad


def scan_topology(repos: Iterable[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Return (package, field, illegal_code) triples from a compass topology."""
    findings: list[tuple[str, str, str]] = []
    for repo in repos:
        name = str(repo.get("name", ""))
        primary = repo.get("primary_base120")
        if primary is not None:
            for bad in illegal_base120_codes([primary]):
                findings.append((name, "primary_base120", bad))
        for code in repo.get("secondary_base120s") or []:
            for bad in illegal_base120_codes([code]):
                findings.append((name, "secondary_base120s", bad))
    return findings


def assert_kind_matrix_closed() -> None:
    """Every ordered kind pair has exactly one relation."""
    expected = {(a, b) for a in KINDS for b in KINDS}
    if set(_KIND_MATRIX) != expected:
        missing = expected - set(_KIND_MATRIX)
        extra = set(_KIND_MATRIX) - expected
        raise AssertionError(f"kind matrix not closed: missing={missing} extra={extra}")
    if set(KIND_FAMILY.values()) != set(FAMILIES):
        raise AssertionError("Omni6 kinds must map 1:1 onto Base120 families")
