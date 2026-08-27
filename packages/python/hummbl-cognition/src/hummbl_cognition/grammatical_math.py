"""Seed20 Grammatical Math Engine.

Provides relational algebra, domain taxonomy, compatibility matrix, and explicit
subtype barriers for HUMMBL Base120/Seed20 mental models.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, NamedTuple


class Domain(str, Enum):
    """Mental model domains in HUMMBL Seed20/Base120 taxonomy."""

    IN = "IN"  # Inversion (e.g. IN18 Kill Criteria, IN7 Boundary Testing)
    RE = "RE"  # Reduction & Reasoning (e.g. RE1 First Principles, RE8 Root Cause)
    CO = "CO"  # Composition & Systems (e.g. CO5 Systems Coupling, CO7 Growth Loops)
    DE = "DE"  # Decomposition (e.g. DE5 Dimensional Reduction)
    P = "P"  # Perception & Framing (e.g. P5 User Journey, P9 Accessibility)


class Relation(str, Enum):
    """Relational operators for Grammatical Mathematics."""

    ORTHOGONAL = "⊥"  # Subtype barrier / Disjoint domains
    COMPOSED = "∘"  # Direct functional composition
    ENTAILS = "⇒"  # Logical implication / Precedence
    DUAL = "⇔"  # Epistemic duality
    BOUND = "↦"  # Contextual binding
    SUPERSEDES = "≻"  # Precedence / Hierarchy override

    def __str__(self) -> str:
        return self.value


class SubtypeBarrier(NamedTuple):
    """Represents an explicit non-interfering subtype boundary (A ⊥ B)."""

    left: str
    right: str
    relation: Relation = Relation.ORTHOGONAL
    is_barrier: bool = True


# Pre-defined explicit subtype barriers
SUBTYPE_BARRIERS: dict[tuple[str, str], SubtypeBarrier] = {
    ("IN18", "RE8"): SubtypeBarrier("IN18", "RE8"),  # Kill-Criteria ⊥ Root Cause
    ("IN18", "RE1"): SubtypeBarrier("IN18", "RE1"),  # Kill-Criteria ⊥ First Principles
    ("CO5", "IN7"): SubtypeBarrier("CO5", "IN7"),  # Systems Coupling ⊥ Boundary Testing
}


# Domain Compatibility Matrix mapping (DomainA, DomainB) -> Relation metadata
DOMAIN_MATRIX: dict[tuple[Domain, Domain], dict[str, Any]] = {
    (Domain.IN, Domain.RE): {
        "relation": Relation.ORTHOGONAL,
        "is_barrier": True,
        "compatibility": 0.0,
        "description": "Inversion and Reduction operate on orthogonal analytical axes",
    },
    (Domain.IN, Domain.CO): {
        "relation": Relation.ORTHOGONAL,
        "is_barrier": True,
        "compatibility": 0.0,
        "description": "Inversion safety boundaries are disjoint from system composition",
    },
    (Domain.RE, Domain.CO): {
        "relation": Relation.COMPOSED,
        "is_barrier": False,
        "compatibility": 0.95,
        "description": "First-principles reduction composes cleanly into system models",
    },
    (Domain.DE, Domain.CO): {
        "relation": Relation.DUAL,
        "is_barrier": False,
        "compatibility": 0.90,
        "description": "Decomposition is the structural dual of composition",
    },
    (Domain.P, Domain.CO): {
        "relation": Relation.BOUND,
        "is_barrier": False,
        "compatibility": 0.85,
        "description": "Perceptual frames bind to compositional system views",
    },
    (Domain.IN, Domain.IN): {
        "relation": Relation.ENTAILS,
        "is_barrier": False,
        "compatibility": 1.0,
        "description": "Inversion models entail self-consistent safety bounds",
    },
}


def check_subtype_barrier(left: str, right: str) -> bool:
    """Return True if (left, right) or (right, left) form an explicit subtype barrier."""
    return (left, right) in SUBTYPE_BARRIERS or (right, left) in SUBTYPE_BARRIERS


def is_domain_compatible(domain_a: Domain, domain_b: Domain) -> bool:
    """Return True if domain_a and domain_b are functionally compatible (non-barrier)."""
    if domain_a == domain_b:
        return True
    entry = DOMAIN_MATRIX.get((domain_a, domain_b)) or DOMAIN_MATRIX.get(
        (domain_b, domain_a)
    )
    if entry is None:
        return True
    return not entry.get("is_barrier", False)


def evaluate_relation(left: str, relation: Relation, right: str) -> dict[str, Any]:
    """Evaluate a relational expression between two model identifiers.

    Returns evaluation status dict including barrier enforcement.
    """
    barrier = check_subtype_barrier(left, right)
    if barrier and relation != Relation.ORTHOGONAL:
        raise ValueError(
            f"Subtype barrier violation: {left} and {right} are orthogonal ({Relation.ORTHOGONAL.value}). "
            f"Cannot evaluate relation '{relation.value}' across explicit barrier."
        )

    return {
        "left": left,
        "relation": relation,
        "right": right,
        "is_barrier": barrier,
        "evaluated": True,
    }
