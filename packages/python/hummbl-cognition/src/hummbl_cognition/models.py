"""Data models for the Cognitive Ledger Protocol.

Defines LedgerEntry (append-only shared memory) and SharedState (mutable snapshot).
All models use stdlib dataclasses only -- zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LedgerEntryType(str, Enum):
    """Type of knowledge being recorded."""

    LESSON = "lesson"  # Earned understanding from experience
    DECISION = "decision"  # Architectural or process decision with reasoning
    DISCOVERY = "discovery"  # New finding about the codebase or domain
    CORRECTION = "correction"  # Fixes a previous entry (uses supersedes)
    CONVENTION = "convention"  # Established pattern or rule
    # Historical aliases — valid for existing entries, not recommended for new writes
    INFERENCE = "inference"  # Deprecated: use DISCOVERY
    HULE = "HULE"  # HRSI biocognitive entries
    SYNTHESIS = "synthesis"  # Session summary entries
    MILESTONE = "MILESTONE"  # Coordination bus milestone entries
    # Historical aliases — valid for existing entries, not recommended for new writes
    ATTESTATION = "attestation"  # Schema waiver / ratification entries


class LedgerScope(str, Enum):
    """Scope of the knowledge entry."""

    PROJECT = "project"  # Project-wide knowledge
    MODULE = "module"  # Specific module or package
    FILE = "file"  # Specific file
    CONVENTION = "convention"  # Coding/process convention
    PROCESS = "process"  # Operational process
    # Historical aliases — valid for existing entries, not recommended for new writes
    COMPETITIVE_INTELLIGENCE = "competitive-intelligence"  # Deprecated: use PROJECT
    HUMMBL_STRATEGY = "hummbl-strategy"  # Deprecated: use PROJECT
    DREAM = "dream"  # HRSI dream entries
    SESSION = "session"  # Session summary entries
    SKILL_SYSTEM = "skill-system"  # Skill system milestone entries


# Canonical values for new writes (pre-append lint uses these).
# Historical aliases are accepted during read via from_dict normalizations
# but rejected for new entries to prevent schema drift accumulation.
CANONICAL_LEDGER_TYPES: frozenset[str] = frozenset({
    LedgerEntryType.LESSON.value,
    LedgerEntryType.DECISION.value,
    LedgerEntryType.DISCOVERY.value,
    LedgerEntryType.CORRECTION.value,
    LedgerEntryType.CONVENTION.value,
})

CANONICAL_LEDGER_SCOPES: frozenset[str] = frozenset({
    LedgerScope.PROJECT.value,
    LedgerScope.MODULE.value,
    LedgerScope.FILE.value,
    LedgerScope.CONVENTION.value,
    LedgerScope.PROCESS.value,
})


class AssuranceLevel(str, Enum):
    """Trust level of the entry."""

    SELF = "SELF"  # Agent asserts its own learning
    PEER = "PEER"  # Another agent reviewed and confirmed
    VERIFIED = "VERIFIED"  # Human or governance process verified
    # Historical / legacy values — valid for existing entries, not recommended for new writes
    SWARM = "SWARM"  # Deprecated: codex steward loop legacy value
    AUDIT = "AUDIT"  # Deprecated: codex governance audit legacy value


class ColorTeam(str, Enum):
    """Security exercise color team that produced this entry.

    See: ~/.agents/skills/color-team-engine/color-registry.yaml
    Extended color wheel: ~/.agents/state/findings/2026-07-12T2200Z-security-color-wheel-complete-reference.md
    """

    # Primary (3)
    RED = "red"  # The Breakers — offensive security
    BLUE = "blue"  # The Defenders — defensive security
    YELLOW = "yellow"  # The Builders — secure development
    # Secondary (6)
    PURPLE = "purple"  # Red+Blue — collaboration/synthesis
    ORANGE = "orange"  # Red+Yellow — education
    GREEN = "green"  # Blue+Yellow — DevSecOps
    CRIMSON = "crimson"  # Red+Red — APT simulation
    NAVY = "navy"  # Blue+Blue — deep defense / SOC architecture
    AMBER = "amber"  # Yellow+Yellow — supply chain security
    # Tertiary (6)
    TEAL = "teal"  # Blue+Green — defensive automation
    CORAL = "coral"  # Red+Green — chaos engineering
    LIME = "lime"  # Yellow+Orange — security education platform
    INDIGO = "indigo"  # Blue+Purple — threat intel integration
    MAGENTA = "magenta"  # Red+Purple — novel attack research
    VIOLET = "violet"  # Purple+Purple — strategic synthesis
    # Specialized (8)
    SILVER = "silver"  # Compliance & audit
    GRAY = "gray"  # SOC operations
    LAVENDER = "lavender"  # AI/ML security
    PINK = "pink"  # Social engineering
    BRONZE = "bronze"  # Hardware security
    CHARCOAL = "charcoal"  # Dark web monitoring
    SLATE = "slate"  # Policy & governance
    TAN = "tan"  # Field security ops
    # Meta (3)
    WHITE = "white"  # Exercise referee
    IRIDESCENT = "iridescent"  # Adversary emulation
    PLAID = "plaid"  # Multi-team coordinator
    # Industry-additional (3)
    BLACK = "black"  # Physical adversary
    GOLD = "gold"  # Tabletop crisis
    CLEAR = "clear"  # Silent observer


class IntelType(str, Enum):
    """Intelligence type consumed or produced by a color team.

    See: ~/.agents/skills/intel-ingest/SKILL.md
    """

    HUMINT = "HUMINT"  # Human-source intelligence
    OSINT = "OSINT"  # Open-source intelligence
    MASINT = "MASINT"  # Measurement and signature intelligence
    IMINT = "IMINT"  # Imagery intelligence
    GEOINT = "GEOINT"  # Geospatial intelligence
    FININT = "FININT"  # Financial intelligence
    TECHINT = "TECHINT"  # Technical intelligence
    CYBINT = "CYBINT"  # Cyber intelligence
    GITINT = "GITINT"  # Git intelligence
    BUSINT = "BUSINT"  # Bus intelligence
    OPSINT = "OPSINT"  # Operational intelligence
    CODEINT = "CODEINT"  # Code intelligence
    LOGINT = "LOGINT"  # Log intelligence
    REGINT = "REGINT"  # Regulatory intelligence
    TOPOINT = "TOPOINT"  # Topology intelligence


# Allowed vendor identifiers
VALID_VENDORS = frozenset({
    "anthropic", "openai", "google", "moonshot", "local", "human",
})

# Valid color team names (from ColorTeam enum)
VALID_COLOR_TEAMS = frozenset({e.value for e in ColorTeam})

# Valid INT type names (from IntelType enum)
VALID_INTEL_TYPES = frozenset({e.value for e in IntelType})


def _generate_entry_id() -> str:
    """Generate a CLP entry ID: clp-<12 hex chars>."""
    return f"clp-{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_valid_id(entry_id: str) -> bool:
    """Check if an entry ID is valid (standard or known legacy format)."""
    # Standard format: clp-<12 hex chars> (16 chars total)
    if entry_id.startswith("clp-") and len(entry_id) == 16:
        return True
    # Legacy UUID format (session synthesis entries)
    if len(entry_id) == 36 and entry_id.count("-") == 4:
        return True
    # Legacy thoth-prefixed format
    if entry_id.startswith("thoth-"):
        return True
    # Legacy shortened clp format (e.g. clp-c86ca7a0)
    if entry_id.startswith("clp-"):
        return True
    return False


def compute_content_hash(
    *,
    agent: str,
    vendor: str,
    model: str,
    entry_type: str,
    scope: str,
    content: str,
) -> str:
    """Compute SHA-256 hash of canonical entry content.

    The hash covers the immutable semantic identity fields (v1):
        agent, content, model, scope, type, vendor

    Fields NOT covered by the v1 hash (by design — they are metadata, not
    semantic identity):
        id, timestamp, signature, evidence, confidence, supersedes,
        tags, assurance_level, links, claim,
        color_team, intel_types_consumed, intel_types_produced, exercise_role

    This means color team and intel type fields can be modified without
    invalidating the hash. This is an explicit architectural decision
    (see ADR-FM-055): the hash protects "what was learned" (identity),
    not "how it was categorized" (provenance metadata). Tampering with
    color team attribution is undetectable via content_hash alone —
    use the optional HMAC signature for full-record integrity if needed.
    """
    canonical = json.dumps(
        {
            "agent": agent,
            "content": content,
            "model": model,
            "scope": scope,
            "type": entry_type,
            "vendor": vendor,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEntry:
    """Single entry in the cognitive ledger (append-only shared memory).

    Each entry represents a piece of earned understanding -- a lesson learned,
    a decision made, a discovery, or a correction to prior knowledge.
    """

    # Identity
    id: str  # clp-<12 hex chars>
    timestamp: str  # ISO 8601 UTC with Z suffix

    # Provenance
    agent: str  # Agent identifier (e.g., "claude-code (god-mode)")
    vendor: str  # Vendor identifier (anthropic, openai, google, etc.)
    model: str  # Model identifier (e.g., "claude-opus-4-6")

    # Content
    type: str  # LedgerEntryType value
    scope: str  # LedgerScope value
    content: str  # The actual knowledge (max 4096 chars)

    # Integrity
    content_hash: str  # SHA-256 hex of canonical content fields

    # Optional metadata
    evidence: str | None = None  # Link to supporting artifact
    confidence: float = 0.9  # 0.0 to 1.0
    supersedes: str | None = None  # ID of entry this corrects
    tags: tuple[str, ...] = ()  # Categorization tags (max 10)
    assurance_level: str | None = None  # SELF, PEER, or VERIFIED
    signature: str | None = None  # HMAC-SHA256 hex (optional)
    links: tuple[str, ...] = ()  # Related entry IDs (max 20, Zettelkasten-style)
    claim: dict[str, Any] | None = None  # Optional JSON-LD schema:Claim (ADR-FM-048 Phase 0)
    # Color team extension (v1.1.0 — see color-team-engine registry)
    color_team: str | None = None  # ColorTeam value (e.g., "red", "lavender", "amber")
    intel_types_consumed: tuple[str, ...] = ()  # IntelType values consumed during exercise
    intel_types_produced: tuple[str, ...] = ()  # IntelType values produced as findings
    exercise_role: str | None = None  # Role from color registry (e.g., "offense", "defense", "referee")
    # CLP v1.1 extensions (v1.1.1 — hash-chaining, bi-temporal, belief-DAG)
    previous_hash: str | None = None  # SHA-256 of preceding ledger entry line (cryptographic chain)
    valid_time: str | None = None  # ISO 8601 UTC when fact was valid in reality
    contests: str | None = None  # ID of entry this disputes/contests

    def __post_init__(self) -> None:
        """Validate entry fields."""
        if not _is_valid_id(self.id):
            raise ValueError(
                f"Invalid entry ID format: {self.id!r} "
                "(expected clp-<12 hex chars>)"
            )
        if self.vendor not in VALID_VENDORS:
            raise ValueError(
                f"Invalid vendor: {self.vendor!r} "
                f"(expected one of {sorted(VALID_VENDORS)})"
            )
        if self.type not in {e.value for e in LedgerEntryType}:
            raise ValueError(
                f"Invalid type: {self.type!r} "
                f"(expected one of {[e.value for e in LedgerEntryType]})"
            )
        if self.scope not in {e.value for e in LedgerScope}:
            raise ValueError(
                f"Invalid scope: {self.scope!r} "
                f"(expected one of {[e.value for e in LedgerScope]})"
            )
        if not self.content or len(self.content) > 4096:
            raise ValueError(
                f"Content must be 1-4096 chars, got {len(self.content)}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be 0.0-1.0, got {self.confidence}"
            )
        if len(self.tags) > 10:
            raise ValueError(f"Maximum 10 tags, got {len(self.tags)}")
        if self.assurance_level is not None:
            if self.assurance_level not in {e.value for e in AssuranceLevel}:
                raise ValueError(
                    f"Invalid assurance_level: {self.assurance_level!r}"
                )
        if self.supersedes is not None and not self.supersedes.startswith("clp-"):
            raise ValueError(
                f"supersedes must be a valid CLP ID: {self.supersedes!r}"
            )
        if len(self.links) > 20:
            raise ValueError(f"Maximum 20 links, got {len(self.links)}")
        for link_id in self.links:
            if not link_id.startswith("clp-") or len(link_id) != 16:
                raise ValueError(
                    f"Invalid link ID format: {link_id!r} "
                    "(expected clp-<12 hex chars>)"
                )
        if self.contests is not None and not _is_valid_id(self.contests):
            raise ValueError(
                f"contests must be a valid CLP ID: {self.contests!r}"
            )
        if self.valid_time is not None:
            if not self.valid_time.endswith("Z") or "T" not in self.valid_time:
                raise ValueError(
                    f"valid_time must be ISO 8601 UTC with Z suffix: {self.valid_time!r}"
                )
        if self.previous_hash is not None:
            if len(self.previous_hash) != 64 or not all(c in "0123456789abcdef" for c in self.previous_hash.lower()):
                raise ValueError(
                    f"previous_hash must be 64 hex chars SHA-256 digest: {self.previous_hash!r}"
                )
        # Color team validation (v1.1.0)
        if self.color_team is not None:
            if self.color_team not in VALID_COLOR_TEAMS:
                raise ValueError(
                    f"Invalid color_team: {self.color_team!r} "
                    f"(expected one of {sorted(VALID_COLOR_TEAMS)})"
                )
        for intel_type in self.intel_types_consumed:
            if intel_type not in VALID_INTEL_TYPES:
                raise ValueError(
                    f"Invalid intel_types_consumed entry: {intel_type!r} "
                    f"(expected one of {sorted(VALID_INTEL_TYPES)})"
                )
        for intel_type in self.intel_types_produced:
            if intel_type not in VALID_INTEL_TYPES:
                raise ValueError(
                    f"Invalid intel_types_produced entry: {intel_type!r} "
                    f"(expected one of {sorted(VALID_INTEL_TYPES)})"
                )
        if self.exercise_role is not None:
            if len(self.exercise_role) > 64:
                raise ValueError(
                    f"exercise_role must be <= 64 chars, got {len(self.exercise_role)}"
                )
            if not all(c.isalnum() or c in "-_" for c in self.exercise_role):
                raise ValueError(
                    f"exercise_role must be alphanumeric + dash/underscore only: "
                    f"{self.exercise_role!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        d: dict[str, Any] = {
            "id": self.id,
            "timestamp": self.timestamp,
            "agent": self.agent,
            "vendor": self.vendor,
            "model": self.model,
            "type": self.type,
            "scope": self.scope,
            "content": self.content,
            "content_hash": self.content_hash,
        }
        if self.evidence is not None:
            d["evidence"] = self.evidence
        d["confidence"] = self.confidence
        if self.supersedes is not None:
            d["supersedes"] = self.supersedes
        if self.tags:
            d["tags"] = list(self.tags)
        if self.assurance_level is not None:
            d["assurance_level"] = self.assurance_level
        if self.signature is not None:
            d["signature"] = self.signature
        if self.links:
            d["links"] = list(self.links)
        if self.claim is not None:
            d["claim"] = self.claim
        # Color team extension (v1.1.0)
        if self.color_team is not None:
            d["color_team"] = self.color_team
        if self.intel_types_consumed:
            d["intel_types_consumed"] = list(self.intel_types_consumed)
        if self.intel_types_produced:
            d["intel_types_produced"] = list(self.intel_types_produced)
        if self.exercise_role is not None:
            d["exercise_role"] = self.exercise_role
        # CLP v1.1 extensions
        if self.previous_hash is not None:
            d["previous_hash"] = self.previous_hash
        if self.valid_time is not None:
            d["valid_time"] = self.valid_time
        if self.contests is not None:
            d["contests"] = self.contests
        return d

    def to_jsonl(self) -> str:
        """Serialize to compact JSON line."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerEntry:
        """Deserialize from dictionary.

        Normalizes known legacy field aliases so historical entries parse
        without mutating the append-only ledger.
        """
        # Field name normalization for historical entries
        if "entry_id" in data and "id" not in data:
            data = {**data, "id": data.pop("entry_id")}
        if "ts" in data and "timestamp" not in data:
            data = {**data, "timestamp": data.pop("ts")}
        if "timestamp_utc" in data and "timestamp" not in data:
            data = {**data, "timestamp": data.pop("timestamp_utc")}
        if "hash" in data and "content_hash" not in data:
            data = {**data, "content_hash": data.pop("hash")}
        # Provide defaults for missing required fields in cross-system entries
        if "vendor" not in data:
            data = {**data, "vendor": "human"}
        if "model" not in data:
            data = {**data, "model": "unknown"}
        if "content_hash" not in data:
            data = {**data, "content_hash": ""}

        tags = data.get("tags", [])
        if isinstance(tags, list):
            tags = tuple(tags)
        links = data.get("links", [])
        if isinstance(links, list):
            links = tuple(links)
        # Color team extension (v1.1.0)
        intel_consumed = data.get("intel_types_consumed") or []
        if isinstance(intel_consumed, list):
            intel_consumed = tuple(intel_consumed)
        intel_produced = data.get("intel_types_produced") or []
        if isinstance(intel_produced, list):
            intel_produced = tuple(intel_produced)
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            agent=data["agent"],
            vendor=data["vendor"],
            model=data["model"],
            type=data["type"],
            scope=data["scope"],
            content=data["content"],
            content_hash=data["content_hash"],
            evidence=data.get("evidence"),
            confidence=data.get("confidence", 0.9),
            supersedes=data.get("supersedes"),
            tags=tags,
            assurance_level=data.get("assurance_level"),
            signature=data.get("signature"),
            links=links,
            claim=data.get("claim"),
            color_team=data.get("color_team"),
            intel_types_consumed=intel_consumed,
            intel_types_produced=intel_produced,
            exercise_role=data.get("exercise_role"),
            previous_hash=data.get("previous_hash"),
            valid_time=data.get("valid_time"),
            contests=data.get("contests"),
        )

    def verify_hash(self) -> bool:
        """Verify that content_hash matches the canonical content fields."""
        expected = compute_content_hash(
            agent=self.agent,
            vendor=self.vendor,
            model=self.model,
            entry_type=self.type,
            scope=self.scope,
            content=self.content,
        )
        return self.content_hash == expected

    @classmethod
    def create(
        cls,
        *,
        agent: str,
        vendor: str,
        model: str,
        entry_type: str | LedgerEntryType,
        scope: str | LedgerScope,
        content: str,
        evidence: str | None = None,
        confidence: float = 0.9,
        supersedes: str | None = None,
        tags: tuple[str, ...] | list[str] = (),
        assurance_level: str | None = None,
        links: tuple[str, ...] | list[str] = (),
        claim: dict[str, Any] | None = None,
        color_team: str | None = None,
        intel_types_consumed: tuple[str, ...] | list[str] = (),
        intel_types_produced: tuple[str, ...] | list[str] = (),
        exercise_role: str | None = None,
        previous_hash: str | None = None,
        valid_time: str | None = None,
        contests: str | None = None,
    ) -> LedgerEntry:
        """Factory method to create a new ledger entry with auto-generated ID,
        timestamp, and content hash.
        """
        if isinstance(entry_type, LedgerEntryType):
            entry_type = entry_type.value
        if isinstance(scope, LedgerScope):
            scope = scope.value
        if isinstance(tags, list):
            tags = tuple(tags)
        if isinstance(links, list):
            links = tuple(links)
        if isinstance(intel_types_consumed, list):
            intel_types_consumed = tuple(intel_types_consumed)
        if isinstance(intel_types_produced, list):
            intel_types_produced = tuple(intel_types_produced)

        entry_id = _generate_entry_id()
        timestamp = _utc_now_iso()
        content_hash = compute_content_hash(
            agent=agent,
            vendor=vendor,
            model=model,
            entry_type=entry_type,
            scope=scope,
            content=content,
        )
        return cls(
            id=entry_id,
            timestamp=timestamp,
            agent=agent,
            vendor=vendor,
            model=model,
            type=entry_type,
            scope=scope,
            content=content,
            content_hash=content_hash,
            evidence=evidence,
            confidence=confidence,
            supersedes=supersedes,
            tags=tags,
            assurance_level=assurance_level,
            links=links,
            claim=claim,
            color_team=color_team,
            intel_types_consumed=intel_types_consumed,
            intel_types_produced=intel_types_produced,
            exercise_role=exercise_role,
            previous_hash=previous_hash,
            valid_time=valid_time,
            contests=contests,
        )


@dataclass
class SharedState:
    """Mutable snapshot of multi-agent coordination state (Layer 1).

    Unlike the append-only ledger, this file is overwritten atomically.
    Uses optimistic concurrency via the version field.
    """

    version: int = 0
    updated_at: str = ""
    updated_by: str = ""
    active_agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    claimed_files: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_decisions: list[dict[str, Any]] = field(default_factory=list)
    sprint: dict[str, Any] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)

    def increment_version(self, updated_by: str) -> None:
        """Bump version and update metadata."""
        self.version += 1
        self.updated_at = _utc_now_iso()
        self.updated_by = updated_by

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "active_agents": self.active_agents,
            "claimed_files": self.claimed_files,
            "active_decisions": self.active_decisions,
            "sprint": self.sprint,
            "flags": self.flags,
        }

    def to_json(self) -> str:
        """Serialize to pretty JSON."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SharedState:
        """Deserialize from dictionary."""
        return cls(
            version=data.get("version", 0),
            updated_at=data.get("updated_at", ""),
            updated_by=data.get("updated_by", ""),
            active_agents=data.get("active_agents", {}),
            claimed_files=data.get("claimed_files", {}),
            active_decisions=data.get("active_decisions", []),
            sprint=data.get("sprint", {}),
            flags=data.get("flags", {}),
        )

    @classmethod
    def from_json(cls, text: str) -> SharedState:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(text))
