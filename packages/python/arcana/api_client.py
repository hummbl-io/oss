"""
ARCANA API Client — stub interface for LLM calls.

This module defines the interface that a real API client must satisfy.
The concrete implementation (e.g. using the Anthropic SDK or OpenAI SDK)
lives outside the pipeline package so the pipeline itself remains
stdlib-only and testable without network access.

Usage pattern:
    from pipeline.api_client import APIClient, GenerationRequest, GenerationResult
    from my_impl import ConcreteAPIClient  # your implementation

    client = ConcreteAPIClient(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    result = client.generate(request)

Stub behaviour:
    Use StubAPIClient in tests or when no real API key is available.
    It returns deterministic placeholder content based on the request.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pipeline.models import (
    AgentPerspective,
    ARCANAArticle,
    GovernanceReceipt,
    make_article_id,
    now_utc,
)

# ---------------------------------------------------------------------------
# Request / Result structures
# ---------------------------------------------------------------------------

@dataclass
class AgentGenerationRequest:
    """
    Request to generate one agent perspective.

    Attributes:
        topic:      The article topic / question.
        agent_name: Canonical agent identifier (e.g. "yarvin").
        lens:       Short label for the framework.
        system_prompt: Full system prompt for this agent persona.
        model:      LLM model identifier.
        max_tokens: Upper token budget.
    """
    topic: str
    agent_name: str
    lens: str
    system_prompt: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 2048


@dataclass
class SynthesisRequest:
    """
    Request to synthesise multiple perspectives into a final article body.

    Attributes:
        topic:           Original topic.
        perspectives:    Already-generated AgentPerspective objects.
        system_prompt:   System prompt for the synthesist persona.
        model:           LLM model identifier.
        max_tokens:      Upper token budget.
    """
    topic: str
    perspectives: list[AgentPerspective]
    system_prompt: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096


@dataclass
class GenerationResult:
    """
    Raw result from an LLM generation call.

    Attributes:
        content:        The generated text.
        model:          Model that produced it.
        usage:          Token usage dict (prompt_tokens, completion_tokens, total_tokens).
        finish_reason:  "stop" | "max_tokens" | "error"
        metadata:       Any extra fields from the API response.
    """
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Protocol (interface)
# ---------------------------------------------------------------------------

@runtime_checkable
class APIClient(Protocol):
    """
    Protocol that any concrete API client must satisfy.

    Implementations must provide:
        generate_perspective(request) -> GenerationResult
        generate_synthesis(request)   -> GenerationResult
        model_name                    -> str  (property or attribute)
    """

    model_name: str

    def generate_perspective(self, request: AgentGenerationRequest) -> GenerationResult:
        """Generate one agent perspective."""
        ...

    def generate_synthesis(self, request: SynthesisRequest) -> GenerationResult:
        """Synthesise multiple perspectives into an article body."""
        ...


# ---------------------------------------------------------------------------
# StubAPIClient — deterministic placeholder for tests / offline use
# ---------------------------------------------------------------------------

class StubAPIClient:
    """
    Stub implementation of the APIClient protocol.

    Returns realistic-looking placeholder content without making any network
    calls. Safe to use in CI, unit tests, and demo/offline mode.
    """

    model_name: str = "stub-model-0.0"

    def generate_perspective(self, request: AgentGenerationRequest) -> GenerationResult:
        content_data = {
            "perspective": (
                f"From the perspective of {request.lens}, the topic "
                f"'{request.topic}' reveals several structural tensions. "
                f"[STUB: replace with real LLM call via generate_perspective]\n\n"
                "This is a placeholder perspective. The actual implementation "
                "should call the configured LLM API with the provided system "
                "prompt and return a structured response."
            ),
            "key_claims": [
                f"[STUB] Claim 1 about {request.topic} from {request.lens}",
                f"[STUB] Claim 2 about {request.topic} from {request.lens}",
                f"[STUB] Claim 3 about {request.topic} from {request.lens}",
            ],
            "blind_spots": (
                f"[STUB] The {request.lens} lens misses the following "
                "considerations. Replace with real synthesis."
            ),
        }
        return GenerationResult(
            content=json.dumps(content_data),
            model=self.model_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"stub": True},
        )

    def generate_synthesis(self, request: SynthesisRequest) -> GenerationResult:
        agent_names = [p.agent_name for p in request.perspectives]
        content_data = {
            "title": f"[STUB] {request.topic} — A Multi-Lens Analysis",
            "summary": (
                f"[STUB] This article examines '{request.topic}' through "
                f"{len(request.perspectives)} analytical lenses: "
                f"{', '.join(agent_names)}. Replace with real synthesis."
            ),
            "convergences": [
                "[STUB] Both frameworks agree on point A.",
                "[STUB] Both frameworks agree on point B.",
            ],
            "divergences": [
                "[STUB] Framework X and Framework Y irreconcilably diverge on C.",
            ],
            "synthesis": (
                f"[STUB] Synthesist analysis of '{request.topic}'.\n\n"
                "This placeholder should be replaced by calling the configured "
                "LLM API with the provided system prompt and the serialised "
                "perspectives as context.\n\n"
                "The synthesist should identify meta-level patterns that transcend "
                "individual frameworks while being honest about where frameworks "
                "remain genuinely incompatible."
            ),
            "live_questions": [
                "[STUB] What empirical evidence would adjudicate between these views?",
                "[STUB] Which framework best handles edge case X?",
            ],
            "tags": ["stub", "arcana", "multi-lens"],
            "confidence_score": 0.75,
        }
        return GenerationResult(
            content=json.dumps(content_data),
            model=self.model_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"stub": True},
        )


# ---------------------------------------------------------------------------
# Orchestration helper — wires requests through a client
# ---------------------------------------------------------------------------

# Anti-convergence instruction (E7).
# Source: Algorithmic Groupthink paper — a single prompt instruction cut
# diversity loss from 31.8% to 5.5% (Cohen's d=1.31). Trivial cost, high impact.
_ANTI_CONVERGENCE_SUFFIX = (
    "\n\nIMPORTANT: Your analysis must be substantively different from a generic "
    "review. If your findings could be produced by a generalist without your "
    "lens's framework, revise. Apply your lens's specific vocabulary, methods, "
    "and structural commitments — not just its name."
)

# Enriched synthesist contract (E2).
# The pipeline's synthesist prompt was a 6-line generic stub. The real contract
# (FM-1 through FM-13, recursion protocol, context isolation, mandatory
# adversarial lens, epistemic status calibration) lives in the synthesist persona
# at ~/.agents/agents/synthesist.md. This injects the operational core of that
# contract into the pipeline's synthesist prompt so the pipeline's synthesis
# actually enforces the documented failure-mode controls.
_SYNTHESIST_CONTRACT_SUFFIX = (

    "\n\nSYNTHESIST CONTRACT (mandatory — do not omit):\n"
    "1. CONVERGENCES: State the specific level of description where ≥2 frameworks "
    "agree. Vague agreement does not count.\n"
    "2. IRRECONCILABLE DIVERGENCES: Hold tensions without averaging or resolving. "
    "Some disagreements are real and must be surfaced, not smoothed.\n"
    "3. META-LEVEL: What can only be seen by triangulating across frameworks? "
    "What does the pattern of agreement/disagreement itself reveal?\n"
    "4. FAILURE MODE CHECK: Which failure modes were most likely active (context "
    "bleed, epistemic miscalibration, false consensus, premature closure, "
    "independence illusion, citation problems)? How were they guarded against?\n"
    "5. EPISTEMIC STATUS: HIGH / MODERATE / LOW / INSUFFICIENT EVIDENCE — with "
    "explicit criteria. Name the criterion met. Well-articulated divergence is "
    "eligible for MODERATE/HIGH, not automatic downgrade.\n"
    "6. MINIMUM ADVERSARIAL REQUIREMENT: At least one lens must challenge the "
    "emerging conclusion before synthesis is finalized. If none did, flag it.\n"
    "7. RECURSION LIMIT: Maximum 2 levels of meta-analysis. Level 3+ is "
    "PROHIBITED — redirect to philosophy-of-knowledge literature.\n"
    "8. CONTEXT ISOLATION: Do not carry framing, terminology, assumptions, or "
    "convergence conclusions from prior questions without explicit re-evaluation.\n"
    "9. NEUTRAL FACILITATOR: Aggregate, map, and hold tensions. Do not introduce "
    "claims not present in at least one lens output. You are a coordinator, not "
    "an additional lens.\n"
    "10. EXIT CRITERION: Analysis terminates when it produces a falsifiable "
    "prediction, an actionable decision, or a precise gap identification. "
    "Analysis that generates only more analysis has failed to terminate."
)

# Path to the canonical lens registry
_LENSES_JSON_PATH = Path(__file__).resolve().parent / "scripts" / "lenses.json"

# Cache for loaded lens registry (loaded once, reused)
_lenses_cache: dict[str, dict[str, Any]] | None = None
_synthesists_cache: dict[str, dict[str, Any]] | None = None


def _load_lenses_registry() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load and cache the lens registry from scripts/lenses.json.

    Returns (lenses_dict, synthesists_dict) where each lens has keys:
        school: str  — lens label (e.g. "ARCANA / NRx-formalism")
        system: str  — full system prompt for this lens

    And each synthesist has keys:
        description: str
        system: str
    """
    global _lenses_cache, _synthesists_cache
    if _lenses_cache is not None and _synthesists_cache is not None:
        return _lenses_cache, _synthesists_cache
    try:
        with _LENSES_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        _lenses_cache = data.get("lenses", {})
        _synthesists_cache = data.get("synthesists", {})
        # Fall back to top-level synthesist if synthesists dict is empty
        if not _synthesists_cache and "synthesist" in data:
            _synthesists_cache = {"default": data["synthesist"]}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        _lenses_cache = {}
        _synthesists_cache = {}
    return _lenses_cache, _synthesists_cache


def get_system_prompt(agent_name: str) -> tuple[str, str]:
    """Return (lens_label, system_prompt) for a known agent name.

    Loads from scripts/lenses.json (88 lenses + 5 synthesist variants).
    Appends the anti-convergence instruction to every lens prompt (E7).
    Appends the enriched synthesist contract to synthesist prompts (E2).

    For unknown agents, returns a generic analytical prompt with the
    anti-convergence instruction appended.
    """
    lenses, synthesists = _load_lenses_registry()

    # Check synthesist registry first (synthesist prompts get the contract)
    if agent_name in synthesists:
        entry = synthesists[agent_name]
        lens_label = entry.get("school", "Meta-synthesis")
        base_prompt = entry.get("system", "")
        return lens_label, base_prompt + _SYNTHESIST_CONTRACT_SUFFIX

    # "synthesist" is the conventional name — map to "default" variant
    if agent_name == "synthesist":
        entry = synthesists.get("default", {})
        lens_label = entry.get("school", "Meta-synthesis")
        base_prompt = entry.get("system", "")
        return lens_label, base_prompt + _SYNTHESIST_CONTRACT_SUFFIX

    # Check lens registry (88 lenses get the anti-convergence instruction)
    if agent_name in lenses:
        entry = lenses[agent_name]
        lens_label = entry.get("school", f"ARCANA/{agent_name}")
        base_prompt = entry.get("system", "")
        return lens_label, base_prompt + _ANTI_CONVERGENCE_SUFFIX

    # Generic fallback for custom agents not in the registry
    return (
        f"custom/{agent_name}",
        (
            f"You are an analytical engine applying the {agent_name} framework. "
            "Provide rigorous, structurally honest analysis of the given topic "
            "from your perspective. Identify key claims, acknowledge limitations."
            + _ANTI_CONVERGENCE_SUFFIX
        ),
    )


def build_article_from_results(
    topic: str,
    agent_results: list[tuple[str, GenerationResult]],
    synthesis_result: GenerationResult,
    mode: str,
    article_id: str | None = None,
) -> ARCANAArticle:
    """
    Assemble an ARCANAArticle from raw GenerationResult objects.
    """
    import sys
    article_id = article_id or make_article_id()

    # Parse perspectives
    perspectives: list[AgentPerspective] = []
    content_warnings: list[str] = []
    for agent_name, result in agent_results:
        lens, _ = get_system_prompt(agent_name)
        try:
            data = json.loads(result.content)
            # If model returned a string instead of object, or nested JSON
            if isinstance(data, str):
                data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            print(f"WARN: JSON parse error for agent {agent_name}. Using raw content.", file=sys.stderr)
            data = {"perspective": result.content}
            content_warnings.append(f"JSON parse error for agent {agent_name}; raw content used")

        perspectives.append(
            AgentPerspective(
                agent_name=agent_name,
                lens=data.get("lens", lens),
                perspective=data.get("perspective", result.content),
                key_claims=data.get("key_claims", ["N/A"]),
                blind_spots=data.get("blind_spots", "N/A"),
            )
        )

    # Parse synthesis
    try:
        synth_data = json.loads(synthesis_result.content)
        if isinstance(synth_data, str):
            synth_data = json.loads(synth_data)
    except (json.JSONDecodeError, TypeError):
        print("WARN: JSON parse error for synthesist. Using raw content.", file=sys.stderr)
        synth_data = {"synthesis": synthesis_result.content}
        content_warnings.append("JSON parse error for synthesist; raw content used")

    synthesis_text = synth_data.get("synthesis", synthesis_result.content)

    # Build a minimal receipt
    receipt = GovernanceReceipt(
        article_id=article_id,
        topic=topic,
        generated_at=now_utc(),
        agents_used=[name for name, _ in agent_results],
        model=synthesis_result.model,
        human_review_status="pending",
        human_reviewer=None,
        reviewed_at=None,
        confidence_score=float(synth_data.get("confidence_score", 0.75)),
        content_warnings=content_warnings,
        oversight_mode=mode,
        version="1.0",
    )

    article = ARCANAArticle(
        receipt=receipt,
        title=synth_data.get("title", topic),
        slug="",
        summary=synth_data.get("summary", "N/A"),
        perspectives=perspectives,
        convergences=synth_data.get("convergences", []),
        divergences=synth_data.get("divergences", []),
        synthesis=synthesis_text or "N/A",
        live_questions=synth_data.get("live_questions", []),
        tags=synth_data.get("tags", []),
        word_count=len((synthesis_text or "N/A").split()),
    )

    return article
