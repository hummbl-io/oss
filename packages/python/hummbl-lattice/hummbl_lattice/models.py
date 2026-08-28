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

"""Domain120 lattice data models.

Lattice          — a complete Domain120 lattice for one domain.
LatticeOperator  — a single domain-specific reasoning operator.
CompositionMatrix — the 6x6 family-pair admissibility structure.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

FAMILIES: tuple[str, ...] = ("P", "IN", "CO", "DE", "RE", "SY")

FAMILY_NAMES: dict[str, str] = {
    "P":  "Perspective",
    "IN": "Inversion",
    "CO": "Composition",
    "DE": "Decomposition",
    "RE": "Recursion",
    "SY": "Synthesis",
}

# Valid Base120 ancestor codes (30 generic operators: 5 per family)
BASE120_ANCESTORS: frozenset[str] = frozenset(
    f"{f}{n}" for f in FAMILIES for n in range(1, 21)
)


@dataclass(frozen=True, slots=True)
class LatticeOperator:
    """A single domain-specific reasoning operator.

    code             e.g. "IN01" (domain-specific numbering)
    name             e.g. "Seismic Load Path Inversion"
    family           one of P, IN, CO, DE, RE, SY
    definition       1-2 sentences describing how to think
    base120_ancestor the generic Base120 operator this specializes (e.g. "IN3")
    status           promotion state: draft | candidate | curated | ratified | deprecated
    """

    code: str
    name: str
    family: str
    definition: str
    base120_ancestor: str
    status: str = "draft"

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(
                f"Invalid family {self.family!r}. Must be one of {FAMILIES}."
            )
        if self.base120_ancestor not in BASE120_ANCESTORS:
            raise ValueError(
                f"Invalid base120_ancestor {self.base120_ancestor!r}. "
                f"Must be one of {sorted(BASE120_ANCESTORS)[:10]}..."
            )
        if self.status not in ("draft", "candidate", "curated", "ratified", "deprecated"):
            raise ValueError(
                f"Invalid status {self.status!r}. "
                f"Must be draft, candidate, curated, ratified, or deprecated."
            )

    @property
    def family_name(self) -> str:
        """Human-readable family name."""
        return FAMILY_NAMES[self.family]

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "code": self.code,
            "name": self.name,
            "family": self.family,
            "definition": self.definition,
            "base120_ancestor": self.base120_ancestor,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LatticeOperator":
        """Deserialize from a dict."""
        return cls(
            code=data["code"],
            name=data["name"],
            family=data["family"],
            definition=data["definition"],
            base120_ancestor=data["base120_ancestor"],
            status=data.get("status", "draft"),
        )


@dataclass
class CompositionMatrix:
    """6x6 composition admissibility matrix.

    Records whether operators from family A can compose with operators
    from family B. States: undefined | admissible | inadmissible | deprecated.
    """

    cells: dict[tuple[str, str], str] = field(default_factory=dict)

    def get(self, family_a: str, family_b: str) -> str:
        """Get the admissibility state for (A, B)."""
        return self.cells.get((family_a, family_b), "undefined")

    def set(self, family_a: str, family_b: str, state: str) -> None:
        """Set the admissibility state for (A, B)."""
        if state not in ("undefined", "admissible", "inadmissible", "deprecated"):
            raise ValueError(f"Invalid state {state!r}.")
        if family_a not in FAMILIES or family_b not in FAMILIES:
            raise ValueError(f"Families must be one of {FAMILIES}.")
        self.cells[(family_a, family_b)] = state

    @property
    def admissible_count(self) -> int:
        """Number of admissible family-pairs."""
        return sum(1 for s in self.cells.values() if s == "admissible")

    def to_dict(self) -> dict:
        """Serialize to a nested dict {family_a: {family_b: state}}."""
        result: dict[str, dict[str, str]] = {}
        for (a, b), state in self.cells.items():
            if a not in result:
                result[a] = {}
            result[a][b] = state
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CompositionMatrix":
        """Deserialize from a nested dict."""
        matrix = cls()
        if isinstance(data, dict):
            for a, row in data.items():
                if isinstance(row, dict):
                    for b, state in row.items():
                        matrix.set(a, b, state)
        return matrix


@dataclass
class Lattice:
    """A complete Domain120 lattice for one domain.

    domain             e.g. "Structural Engineering"
    version            semantic version string
    operators          list of LatticeOperator
    composition_matrix 6x6 family-pair admissibility structure
    cross_maps         cross-domain operator mappings
    author             attribution (for published lattices)
    language           ISO 639-1 code (for polyglot track)
    """

    domain: str
    version: str = "0.1.0"
    operators: list[LatticeOperator] = field(default_factory=list)
    composition_matrix: CompositionMatrix = field(default_factory=CompositionMatrix)
    cross_maps: list[dict] = field(default_factory=list)
    author: str = ""
    language: str = "en"

    @property
    def operator_count(self) -> int:
        return len(self.operators)

    @property
    def family_counts(self) -> dict[str, int]:
        """Count of operators per family."""
        counts = {f: 0 for f in FAMILIES}
        for op in self.operators:
            counts[op.family] = counts.get(op.family, 0) + 1
        return counts

    @property
    def missing_families(self) -> list[str]:
        """Families with zero operators."""
        return [f for f in FAMILIES if self.family_counts.get(f, 0) == 0]

    @property
    def lattice_hash(self) -> str:
        """SHA-256 hash of the canonical serialization."""
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def add_operator(self, op: LatticeOperator) -> None:
        """Add an operator to the lattice."""
        self.operators.append(op)

    def get_operator(self, code: str) -> LatticeOperator | None:
        """Look up an operator by code."""
        for op in self.operators:
            if op.code == code:
                return op
        return None

    def list_by_family(self, family: str) -> list[LatticeOperator]:
        """List operators filtered by family."""
        return [op for op in self.operators if op.family == family]

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "lattice_id": self.domain.lower().replace(" ", "-"),
            "domain": self.domain,
            "version": self.version,
            "author": self.author,
            "language": self.language,
            "operators": [op.to_dict() for op in self.operators],
            "composition_matrix": self.composition_matrix.to_dict(),
            "cross_maps": self.cross_maps,
        }

    def to_json(self, path: str | Path) -> None:
        """Write the lattice to a JSON file."""
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Lattice":
        """Deserialize from a dict."""
        operators = [LatticeOperator.from_dict(op) for op in data.get("operators", [])]
        matrix = CompositionMatrix.from_dict(data.get("composition_matrix", {}))
        return cls(
            domain=data.get("domain", ""),
            version=data.get("version", "0.1.0"),
            operators=operators,
            composition_matrix=matrix,
            cross_maps=data.get("cross_maps", []),
            author=data.get("author", ""),
            language=data.get("language", "en"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "Lattice":
        """Load a lattice from a JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)
