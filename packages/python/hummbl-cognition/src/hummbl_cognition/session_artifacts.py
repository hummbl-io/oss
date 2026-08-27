"""Session Artifact Register — context forwarding between skills.

Lightweight in-session registry that tracks outputs from skills so
downstream skills can reference them by name. Solves the context
forwarding gap identified in the topology hardening session (2026-04-17).

Usage:
    from hummbl_cognition.session_artifacts import register, get, list_all

    # Skill A produces output
    register("arcana_synthesis", summary="14 hypotheses from GTM preset", source_skill="/arcana")

    # Skill B consumes it
    artifact = get("arcana_synthesis")
    if artifact:
        # use artifact.summary as context for /pitch or /signal

Design:
    - In-memory only — dies with the session (not persisted to CLP or disk)
    - Append-only within session (can't update or delete — matches KRINEIA pattern)
    - Lightweight: summary string + metadata, not full output blobs
    - No file I/O, no bus dependency, no imports beyond stdlib

Topology position: Integration surface (connective tissue between L3 skills)

Stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionArtifact:
    """An artifact produced by a skill during this session."""

    name: str  # unique key (e.g., "arcana_synthesis", "dashboard_url")
    summary: str  # 1-3 sentence description of what was produced
    source_skill: str  # which skill produced this (e.g., "/arcana", "/build")
    timestamp: str = field(  # ISO 8601 UTC
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    artifact_path: Optional[str] = None  # file path if the artifact was written to disk
    artifact_type: Optional[str] = (
        None  # "synthesis", "code", "document", "deployment", "decision"
    )


# ---------------------------------------------------------------------------
# Registry (module-level singleton — one per Python process)
# ---------------------------------------------------------------------------

_registry: list[SessionArtifact] = []


def register(
    name: str,
    summary: str,
    source_skill: str,
    artifact_path: Optional[str] = None,
    artifact_type: Optional[str] = None,
) -> SessionArtifact:
    """Register a new artifact in the session registry.

    Append-only — duplicate names are allowed (later entries shadow earlier ones
    in get(), but both are preserved in list_all()).
    """
    artifact = SessionArtifact(
        name=name,
        summary=summary,
        source_skill=source_skill,
        artifact_path=artifact_path,
        artifact_type=artifact_type,
    )
    _registry.append(artifact)
    logger.debug("Session artifact registered: %s from %s", name, source_skill)
    return artifact


def get(name: str) -> Optional[SessionArtifact]:
    """Get the most recent artifact with this name, or None."""
    for artifact in reversed(_registry):
        if artifact.name == name:
            return artifact
    return None


def list_all() -> list[SessionArtifact]:
    """List all artifacts registered in this session (chronological order)."""
    return list(_registry)


def list_by_skill(skill: str) -> list[SessionArtifact]:
    """List all artifacts produced by a specific skill."""
    return [a for a in _registry if a.source_skill == skill]


def list_by_type(artifact_type: str) -> list[SessionArtifact]:
    """List all artifacts of a specific type."""
    return [a for a in _registry if a.artifact_type == artifact_type]


def has(name: str) -> bool:
    """Check if an artifact with this name exists in the session."""
    return any(a.name == name for a in _registry)


def count() -> int:
    """How many artifacts have been registered this session."""
    return len(_registry)


def summary() -> str:
    """Human-readable summary of all session artifacts."""
    if not _registry:
        return "No session artifacts registered."

    lines = [f"Session artifacts ({len(_registry)}):"]
    for a in _registry:
        path_note = f" → {a.artifact_path}" if a.artifact_path else ""
        lines.append(f"  [{a.source_skill}] {a.name}: {a.summary}{path_note}")
    return "\n".join(lines)


def clear() -> int:
    """Clear all artifacts. Returns count of cleared items.

    Use sparingly — this breaks the append-only pattern.
    Intended only for test teardown.
    """
    n = len(_registry)
    _registry.clear()
    return n
