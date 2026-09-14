"""
ARCANA data models — stdlib only (dataclasses + json).

All models serialize to/from JSON cleanly via to_dict() / from_dict() methods.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# AgentPerspective
# ---------------------------------------------------------------------------

@dataclass
class AgentPerspective:
    """
    One analytical lens applied to the article topic by a named agent persona.

    Attributes:
        agent_name:   Canonical name of the agent (e.g. "yarvin", "gramsci").
        lens:         Short label for the interpretive framework
                      (e.g. "NRx/formalism", "Hegemony/left-mirror").
        perspective:  Full prose analysis, 2-4 paragraphs.
        key_claims:   3-5 distilled bullet-point claims.
        blind_spots:  What this lens structurally fails to see.
    """

    agent_name: str
    lens: str
    perspective: str
    key_claims: list[str]
    blind_spots: str

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.agent_name or not self.agent_name.strip():
            raise ValueError("agent_name must not be empty")
        if not (1 <= len(self.key_claims) <= 10):
            raise ValueError(
                f"key_claims must have 1-10 items; got {len(self.key_claims)}"
            )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentPerspective:
        return cls(
            agent_name=data["agent_name"],
            lens=data["lens"],
            perspective=data["perspective"],
            key_claims=list(data["key_claims"]),
            blind_spots=data["blind_spots"],
        )


# ---------------------------------------------------------------------------
# GovernanceReceipt
# ---------------------------------------------------------------------------

VALID_REVIEW_STATUSES = {"pending", "approved", "rejected"}
VALID_OVERSIGHT_MODES = {"HITL", "HOTL"}


@dataclass
class GovernanceReceipt:
    """
    Immutable audit record attached to every generated article.

    HITL = Human In The Loop  (human approves before publication)
    HOTL = Human On The Loop  (human can intervene; auto-publishes after timeout)

    Attributes:
        article_id:           UUID4 string.
        topic:                The original generation prompt topic.
        generated_at:         ISO 8601 UTC timestamp of generation.
        agents_used:          Names of agent personas that contributed.
        model:                LLM model identifier used for synthesis.
        human_review_status:  "pending" | "approved" | "rejected"
        human_reviewer:       Reviewer identifier or None.
        reviewed_at:          ISO 8601 UTC timestamp of review or None.
        confidence_score:     Synthesist-assigned confidence in 0.0-1.0.
        content_warnings:     Flags raised by governance.check_content().
        oversight_mode:       "HITL" | "HOTL"
        version:              Schema version string (current: "1.0").
    """

    article_id: str
    topic: str
    generated_at: str
    agents_used: list[str]
    model: str
    human_review_status: str
    human_reviewer: str | None
    reviewed_at: str | None
    confidence_score: float
    content_warnings: list[str]
    oversight_mode: str
    version: str = "1.0"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if self.human_review_status not in VALID_REVIEW_STATUSES:
            raise ValueError(
                f"human_review_status must be one of {VALID_REVIEW_STATUSES}; "
                f"got '{self.human_review_status}'"
            )
        if self.oversight_mode not in VALID_OVERSIGHT_MODES:
            raise ValueError(
                f"oversight_mode must be one of {VALID_OVERSIGHT_MODES}; "
                f"got '{self.oversight_mode}'"
            )
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(
                f"confidence_score must be in [0.0, 1.0]; got {self.confidence_score}"
            )
        # Validate UUID4 format loosely
        uuid4_re = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid4_re.match(self.article_id):
            raise ValueError(
                f"article_id does not look like a UUID4: '{self.article_id}'"
            )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GovernanceReceipt:
        return cls(
            article_id=data["article_id"],
            topic=data["topic"],
            generated_at=data["generated_at"],
            agents_used=list(data["agents_used"]),
            model=data["model"],
            human_review_status=data["human_review_status"],
            human_reviewer=data.get("human_reviewer"),
            reviewed_at=data.get("reviewed_at"),
            confidence_score=float(data["confidence_score"]),
            content_warnings=list(data.get("content_warnings", [])),
            oversight_mode=data["oversight_mode"],
            version=data.get("version", "1.0"),
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_publishable(self) -> bool:
        """True if this article may be published per oversight rules."""
        if self.oversight_mode == "HITL":
            return self.human_review_status == "approved"
        # HOTL: approved OR still pending (auto-publishes)
        return self.human_review_status != "rejected"


# ---------------------------------------------------------------------------
# ARCANAArticle
# ---------------------------------------------------------------------------

@dataclass
class ARCANAArticle:
    """
    A fully synthesised governed blog article.

    Attributes:
        receipt:        Governance receipt (audit trail).
        title:          Article headline.
        slug:           URL-safe identifier (auto-derived if empty).
        summary:        2-3 sentence abstract.
        perspectives:   One AgentPerspective per contributing agent.
        convergences:   Points where ≥2 frameworks agree.
        divergences:    Irreconcilable tensions between frameworks.
        synthesis:      Synthesist's meta-analysis (the article body).
        live_questions: Open questions left deliberately unresolved.
        tags:           Topic tags for indexing / search.
        word_count:     Character-split word count of the synthesis body.
    """

    receipt: GovernanceReceipt
    title: str
    slug: str
    summary: str
    perspectives: list[AgentPerspective]
    convergences: list[str]
    divergences: list[str]
    synthesis: str
    live_questions: list[str]
    tags: list[str]
    word_count: int

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.synthesis or not self.synthesis.strip():
            raise ValueError("synthesis must not be empty")
        if not self.slug:
            self.slug = self._derive_slug(self.title)
        # Recompute word_count if it looks wrong (0 or mismatched)
        computed = len(self.synthesis.split())
        if self.word_count == 0:
            self.word_count = computed

    @staticmethod
    def _derive_slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:80]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # receipt and perspectives are nested dataclasses — asdict handles them
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ARCANAArticle:
        receipt = GovernanceReceipt.from_dict(data["receipt"])
        perspectives = [
            AgentPerspective.from_dict(p) for p in data.get("perspectives", [])
        ]
        return cls(
            receipt=receipt,
            title=data["title"],
            slug=data.get("slug", ""),
            summary=data["summary"],
            perspectives=perspectives,
            convergences=list(data.get("convergences", [])),
            divergences=list(data.get("divergences", [])),
            synthesis=data["synthesis"],
            live_questions=list(data.get("live_questions", [])),
            tags=list(data.get("tags", [])),
            word_count=int(data.get("word_count", 0)),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> ARCANAArticle:
        return cls.from_dict(json.loads(raw))

    # ------------------------------------------------------------------
    # Rendering helpers (delegated to renderer.py for full output)
    # ------------------------------------------------------------------

    def to_markdown(self) -> str:
        """Render as Markdown with YAML frontmatter governance receipt."""
        from pipeline.renderer import render_article  # lazy import avoids circularity
        return render_article(self)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def agent_names(self) -> list[str]:
        return [p.agent_name for p in self.perspectives]

    def get_perspective(self, agent_name: str) -> AgentPerspective | None:
        for p in self.perspectives:
            if p.agent_name == agent_name:
                return p
        return None

    def recompute_word_count(self) -> int:
        self.word_count = len(self.synthesis.split())
        return self.word_count


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_article_id() -> str:
    """Generate a UUID4 article_id using only stdlib."""
    import uuid
    return str(uuid.uuid4())
