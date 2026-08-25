"""Named Sigil Forge ritual library."""

from __future__ import annotations

from dataclasses import dataclass, field

BUILTIN_RITUALS = {
    "critique_refine": """
        GENERATE(role=oracle)
        -> CRITIQUE(role=critic)
        -> IF(score < 0.8) { REFINE(role=synthesizer, iter=2) }
        -> FORMAT(type=markdown)
    """,
    "direct": "GENERATE(role=oracle) -> FORMAT(type=text)",
    "memory_writeback": """
        GENERATE(role=operative)
        -> CRITIQUE(role=critic)
        -> STORE(memory=session)
    """,
    "policy_checked_generation": """
        POLICY_CHECK(allow=true)
        -> GENERATE(role=operative)
        -> FORMAT(type=text)
    """,
    "rag_analysis": """
        RETRIEVE(k=5)
        -> GENERATE(role=librarian, depth=high)
        -> CRITIQUE(role=critic)
        -> IF(score < 0.8) { REFINE(role=synthesizer) }
        -> FORMAT(type=markdown)
    """,
    "sigil_loop": """
        GENERATE(role=oracle)
        -> LOOP(2) {
            CRITIQUE(role=critic)
            -> REFINE(role=synthesizer)
        }
        -> FORMAT(type=markdown)
    """,
}


@dataclass
class RitualLibrary:
    rituals: dict[str, str] = field(default_factory=lambda: dict(BUILTIN_RITUALS))

    def get(self, name: str) -> str:
        try:
            return self.rituals[name]
        except KeyError as exc:
            raise KeyError(f"Unknown ritual: {name}") from exc

    def register(self, name: str, source: str) -> None:
        if not name or not name.replace("_", "").isalnum():
            raise ValueError(f"Invalid ritual name: {name!r}")
        self.rituals[name] = source

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self.rituals))
