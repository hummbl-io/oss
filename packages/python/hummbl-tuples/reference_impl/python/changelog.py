"""
HUMMBL Domain120 Changelog System

A tuple-based changelog for tracking Domain120 lattice state transitions.
Uses canonical serialization (CANONICAL_SERIALIZATION_v1.md) for cross-language
hash compatibility.

Each changelog entry is a TypedTuple with:
- tuple_type: one of CHANGEOLOG_OPERATION_TYPES
- tuple_data: operation-specific fields

The changelog is append-only JSONL. Semantic versioning is derived from the
tuple stream, not manually assigned.

Operation types:
  GENERATE     — a new operator was generated (Candidate state)
  PROMOTE      — an operator was promoted (e.g., Candidate → Curated)
  DEMOTE       — an operator was demoted (e.g., Ratified → Regressed)
  LINK         — a cross_map was created between two operators
  UNLINK       — a cross_map was removed
  RATIFY       — an operator was ratified (highest promotion)
  DEPRECATE    — an operator was deprecated
  RESTORE      — a deprecated operator was restored
  LATTICE_INIT — a new Domain120 lattice was initialized
  LATTICE_FROZEN — a lattice was frozen (no more changes)
  COMPOSITION_ADMIT — a composition cell was marked admissible
  COMPOSITION_REJECT — a composition cell was marked inadmissible

Semantic versioning derived from changelog:
  MAJOR — LATTICE_INIT or LATTICE_FROZEN (structural change)
  MINOR — RATIFY or DEPRECATE (content change at highest gate)
  PATCH — PROMOTE, DEMOTE, LINK, UNLINK (content change below ratification)
  BUILD — GENERATE, COMPOSITION_ADMIT, COMPOSITION_REJECT (intermediate state)
"""

from __future__ import annotations

import json

# Add parent dir to path for canonical serialization
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).parent))
from canonical_serialization import canonical_hash, canonical_json

# ---------------------------------------------------------------------------
# Operation types
# ---------------------------------------------------------------------------

CHANGELOG_OPERATION_TYPES = frozenset(
    {
        "GENERATE",
        "PROMOTE",
        "DEMOTE",
        "LINK",
        "UNLINK",
        "RATIFY",
        "DEPRECATE",
        "RESTORE",
        "LATTICE_INIT",
        "LATTICE_FROZEN",
        "COMPOSITION_ADMIT",
        "COMPOSITION_REJECT",
    }
)

# Semantic versioning impact per operation type
VERSION_IMPACT = {
    "LATTICE_INIT": "MAJOR",
    "LATTICE_FROZEN": "MAJOR",
    "RATIFY": "MINOR",
    "DEPRECATE": "MINOR",
    "RESTORE": "MINOR",
    "PROMOTE": "PATCH",
    "DEMOTE": "PATCH",
    "LINK": "PATCH",
    "UNLINK": "PATCH",
    "GENERATE": "BUILD",
    "COMPOSITION_ADMIT": "BUILD",
    "COMPOSITION_REJECT": "BUILD",
}


# ---------------------------------------------------------------------------
# Changelog entry
# ---------------------------------------------------------------------------


@dataclass
class ChangelogEntry:
    """A single changelog entry as a canonical tuple."""

    operation: str  # one of CHANGELOG_OPERATION_TYPES
    lattice_id: str  # e.g., "Domain120:Architecture"
    operator_id: str | None  # operator UUID, or None for lattice-level ops
    agent: str  # who/what performed the operation
    timestamp: str  # ISO 8601 UTC
    evidence: dict[str, Any] = field(default_factory=dict)  # operation-specific evidence
    previous_hash: str | None = None  # hash chain link
    metadata: dict[str, Any] = field(default_factory=dict)  # optional extra data

    def to_tuple(self) -> dict[str, Any]:
        """Convert to TypedTuple dict format."""
        tuple_data: dict[str, Any] = {
            "operation": self.operation,
            "lattice_id": self.lattice_id,
            "agent": self.agent,
            "evidence": self.evidence,
        }
        if self.operator_id is not None:
            tuple_data["operator_id"] = self.operator_id
        if self.previous_hash is not None:
            tuple_data["previous_hash"] = self.previous_hash
        if self.metadata:
            tuple_data["metadata"] = self.metadata
        return {
            "tuple_type": "SYSTEM",
            "id": f"changelog-{self.lattice_id}-{self.timestamp}",
            "time": self.timestamp,
            "tuple_data": tuple_data,
        }

    def to_canonical_json(self) -> str:
        """Serialize to canonical JSON per CANONICAL_SERIALIZATION_v1.md."""
        return canonical_json(self.to_tuple())

    def content_hash(self) -> str:
        """Compute SHA-256 content hash (excludes integrity fields)."""
        return canonical_hash(self.to_tuple())


# ---------------------------------------------------------------------------
# Changelog (append-only JSONL)
# ---------------------------------------------------------------------------


class Changelog:
    """Append-only JSONL changelog for a Domain120 lattice.

    The changelog is the source of truth for lattice state.
    Semantic versioning is derived from the entry stream.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._entries: list[ChangelogEntry] = []
        self._last_hash: str | None = None
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        """Load existing entries from the JSONL file."""
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                td = d.get("tuple_data", {})
                entry = ChangelogEntry(
                    operation=td["operation"],
                    lattice_id=td["lattice_id"],
                    operator_id=td.get("operator_id"),
                    agent=td["agent"],
                    timestamp=d["time"],
                    evidence=td.get("evidence", {}),
                    previous_hash=td.get("previous_hash"),
                    metadata=td.get("metadata", {}),
                )
                self._entries.append(entry)
                self._last_hash = entry.content_hash()

    def append(self, entry: ChangelogEntry) -> str:
        """Append a new entry to the changelog.

        Returns the content hash of the appended entry.
        The entry's previous_hash is set to the last entry's hash (chain link).
        """
        # Set chain link
        entry.previous_hash = self._last_hash
        # Compute hash after setting chain link
        h = entry.content_hash()
        # Append to file
        canonical = entry.to_canonical_json()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical + "\n")
        # Update state
        self._entries.append(entry)
        self._last_hash = h
        return h

    def derive_version(self) -> tuple[int, int, int, int]:
        """Derive semantic version from the changelog stream.

        Returns (major, minor, patch, build).
        """
        major = minor = patch = build = 0
        for entry in self._entries:
            impact = VERSION_IMPACT.get(entry.operation, "BUILD")
            if impact == "MAJOR":
                major += 1
                minor = patch = build = 0  # reset lower components on major
            elif impact == "MINOR":
                minor += 1
                patch = build = 0
            elif impact == "PATCH":
                patch += 1
                build = 0
            elif impact == "BUILD":
                build += 1
        return (major, minor, patch, build)

    def version_string(self) -> str:
        """Return semantic version string (e.g., '1.2.3+4')."""
        major, minor, patch, build = self.derive_version()
        if build > 0:
            return f"{major}.{minor}.{patch}+{build}"
        return f"{major}.{minor}.{patch}"

    def entries(self) -> Iterator[ChangelogEntry]:
        """Iterate over all entries in order."""
        yield from self._entries

    def entries_for_operator(self, operator_id: str) -> list[ChangelogEntry]:
        """Get all entries for a specific operator."""
        return [e for e in self._entries if e.operator_id == operator_id]

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity."""
        expected_prev = None
        for entry in self._entries:
            if entry.previous_hash != expected_prev:
                return False
            expected_prev = entry.content_hash()
        return True

    @property
    def last_hash(self) -> str | None:
        """Hash of the most recent entry."""
        return self._last_hash

    def __len__(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def now_utc() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(
    lattice_id: str,
    operator_id: str,
    agent: str,
    family: str,
    name: str,
    definition: str,
    base120_ancestor: str | None = None,
) -> ChangelogEntry:
    """Create a GENERATE entry (operator generated at Candidate state)."""
    evidence = {
        "family": family,
        "name": name,
        "definition": definition,
        "state": "Candidate",
    }
    if base120_ancestor:
        evidence["base120_ancestor"] = base120_ancestor
    return ChangelogEntry(
        operation="GENERATE",
        lattice_id=lattice_id,
        operator_id=operator_id,
        agent=agent,
        timestamp=now_utc(),
        evidence=evidence,
    )


def promote(
    lattice_id: str,
    operator_id: str,
    agent: str,
    from_state: str,
    to_state: str,
    evidence_refs: list[str] | None = None,
) -> ChangelogEntry:
    """Create a PROMOTE entry."""
    evidence: dict[str, Any] = {
        "from_state": from_state,
        "to_state": to_state,
    }
    if evidence_refs:
        evidence["evidence_refs"] = evidence_refs
    return ChangelogEntry(
        operation="PROMOTE",
        lattice_id=lattice_id,
        operator_id=operator_id,
        agent=agent,
        timestamp=now_utc(),
        evidence=evidence,
    )


def link(
    lattice_id: str,
    operator_id: str,
    target_operator_id: str,
    target_lattice_id: str,
    agent: str,
    composition_type: str = "cross_map",
) -> ChangelogEntry:
    """Create a LINK entry (cross_map between operators)."""
    return ChangelogEntry(
        operation="LINK",
        lattice_id=lattice_id,
        operator_id=operator_id,
        agent=agent,
        timestamp=now_utc(),
        evidence={
            "target_operator_id": target_operator_id,
            "target_lattice_id": target_lattice_id,
            "composition_type": composition_type,
        },
    )


def lattice_init(
    lattice_id: str,
    agent: str,
    domain_pillar: str,
    dimensions: list[str],
) -> ChangelogEntry:
    """Create a LATTICE_INIT entry."""
    return ChangelogEntry(
        operation="LATTICE_INIT",
        lattice_id=lattice_id,
        operator_id=None,
        agent=agent,
        timestamp=now_utc(),
        evidence={
            "domain_pillar": domain_pillar,
            "dimensions": dimensions,
            "capacity": 120,
        },
    )
