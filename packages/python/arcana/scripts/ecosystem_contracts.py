"""Cross-module contracts for ARCANA ecosystem.

Centralized canonical references for ARCANA, PRAXIS, POIESIS, PAIDEIA and the
newly authorized sibling modules. The goal is to keep term sets, axis order,
version labels, and module contracts synchronized across scripts and docs.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict


class SiblingModuleSpec(TypedDict):
    version: str
    status: str
    role: str
    purpose: str
    boundary: str
    contract_focus: str
    terms: tuple[str, ...]

# ---- ARCANA -> PRAXIS / POIESIS -------------------------------------------------

ARCANA_WAVES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Wave 1 — Core (NRx / Geopolitics)",
     ("yarvin", "dugin", "land", "strauss", "synthesist")),
    ("Wave 1 — Philosophical Foundations",
     ("nietzsche", "machiavelli", "weber")),
    ("Wave 1 — Left Mirror", ("gramsci", "foucault", "chomsky")),
    ("Wave 1 — Sovereignty", ("schmitt", "kissinger")),
    ("Wave 1 — AI / Tech / Surveillance", ("bostrom", "mcluhan", "zuboff")),
    ("Wave 1 — Econ / Tradition", ("burnham", "evola", "luhmann")),
    ("Wave 2 — Cybernetics / Decolonial / Measurement",
     ("ashby", "fanon", "measurement")),
    ("Wave 3 — Historical / Economic / Epistemic",
     ("marx", "pareto", "popper", "veblen", "bateson", "baudrillard", "guenon")),
    ("Wave 4 — Continental / Critical Theory",
     ("heidegger", "habermas", "bourdieu", "derrida")),
    ("Extended Wave — History / Risk / Belonging / Mimetic",
     ("ibn_khaldun", "taleb", "arendt", "bki", "girard")),
)

PRAXIS_VERSION = "v0.3"
PRAXIS_ARCHETYPES: Mapping[str, str] = {
    "mond": "The Soft Sovereign — shapes what is thinkable; soft power over epistemic frames",
    "aurelius": "The Self-Auditor — radical self-discipline; internal governance before external authority",
    "prospero": "The Information Asymmetrist — controls the frame; orchestrates knowledge differentials",
    "cincinnatus": "The Bounded Executor — accepts temporary authority, returns it; anti-accumulation posture",
    "janus": "The Threshold Guardian — manages transitions and boundary states; liminal authority",
    "demerzel": "The Hidden Sovereign — exercises real power without visibility; long-horizon stewardship",
    "sekhmet": "The Enforcer — controlled destruction as governance; prevents worse outcomes through decisive force",
    "solon": "The System Designer — builds constitutional frameworks; encodes values into structural rules",
    "leto_ii": "The Long Game Strategist — accepts present constraint for multigenerational outcome; Golden Path thinking",
    "picard": "The Ethical Commander — holds the line on principle under operational pressure",
    "oracle": "The Probabilist — governance through foresight; sees around corners; manages uncertainty as resource",
}

POIESIS_VERSION = "v0.2"
POIESIS_STAGES: Mapping[str, str] = {
    "seed": "Emergence — the generative impulse before form; raw potential, creative tension",
    "demiurge": "Imposition of Form — the craftsman gives shape to raw material; agent orchestration",
    "crucible": "Stress-Testing — evaluation under pressure; what survives becomes canon",
    "loom": "Integration of Threads — weaving disparate elements into coherent whole",
    "threshold": "Transformation — passage to a new order; the point of no return",
}

PRAXIS_CANONICAL_NOTE = (
    "CANONICAL PRAXIS ARCHETYPES (use ONLY these names — never substitute "
    "real-world politicians or other figures):"
)
POIESIS_CANONICAL_NOTE = "CANONICAL POIESIS STAGES (use ONLY these names):"


def canonical_praxis_note() -> str:
    return PRAXIS_CANONICAL_NOTE + "\n" + _bullets(PRAXIS_ARCHETYPES)


def canonical_poiesis_note() -> str:
    return POIESIS_CANONICAL_NOTE + "\n" + _bullets(POIESIS_STAGES)


# ---- PRAWN — governed operational cycle -----------------------------------------
#
# PRAWN is the temporal spine the taxonomies (ARCANA / PRAXIS / POIESIS) hang on.
# It answers "in what order does a governed agent move through time?" — distinct
# from the taxonomies, which answer "what / who / what-stage".
#
# Structural innovations vs. OODA / PDCA:
#   1. Account sits between Reason and Work — governance is pre-action, not post.
#   2. Notate feeds Perceive — the cycle is closed by persistence; the agent's own
#      history becomes part of its next perceptual field.
#
# Account has two enforcement shapes, mirroring the existing HITL/HOTL oversight
# modes in models.py:
#   - Checkpoint (HOTL): the empirically validated DEFAULT (Ostrom). Work may
#     proceed, unaccounted work triggers post-hoc reckoning with escalating
#     consequences. Higher variety (Ashby) — reckons with actual outcome, not
#     just narrated intent.
#   - Gate (HITL): the EXCEPTION-triggered shape, reserved for high-irreversibility
#     actions where post-hoc reckoning cannot restore the prior state. Stronger
#     governance, slower emergencies.
#
# Pressure-test findings absorbed:
#   Account stage (docs/pressure-test-prawn-account.md):
#   - Account must sometimes block; zero block-rate over a long run is a red flag
#     (Foucault — theater detection).
#   - Account must be narration + material stake, not narration alone (Yarvin —
#     speech-code detection). The agent stakes something forfeited on misaccounting.
#   - The EMERGENCY bypass of Account is a sovereign decision (Schmitt); the
#     kill-switch operator is subject to post-hoc Account they cannot gate.
#   - Account trades false-negative reduction for false-positive introduction;
#     gate sensitivity is a tunable parameter, not a fixed virtue (Ashby).
#
#   Work stage (docs/pressure-test-prawn-work.md):
#   - Work must be decomposed internally into write-authorization and
#     write-execution (Schneier — privilege separation inside the privileged stage).
#   - Work lacks requisite variety over the external world; every write is a bet
#     under uncertainty; feedback loop is the variety-recovery mechanism (Ashby).
#   - A cycle that terminates without Work (a notated decision to refrain) is a
#     complete cycle, not a failed one (Illich — prevent structural bias toward action).

PRAWN_VERSION = "v0.1-draft"
PRAWN_STAGES: Mapping[str, str] = {
    "perceive": (
        "Intake — active sensing of world-state with named framing; "
        "perception is never raw, always already framed"
    ),
    "reason": (
        "Inference — drawing intent from perception via mental models; "
        "separable from acting so it can be audited independently"
    ),
    "account": (
        "Reckoning — narrate intent, accept attribution, cost the action, "
        "AND stake something material (trust score, delegation token, budget) "
        "forfeited on misaccounting; the gate between thought and effect. "
        "An Account that has never blocked an action is structurally suspect "
        "(theater detection)."
    ),
    "work": (
        "Execution — the only stage with external write authority; "
        "all other stages operate on internal state or the audit record. "
        "Concentration makes the blast radius auditable, but Work must be "
        "decomposed internally into write-authorization and write-execution "
        "(Schneier — privilege separation inside the privileged stage). "
        "Every write is a bet under uncertainty; Work lacks requisite variety "
        "over the external world, and the feedback loop (Work -> Notate -> "
        "Perceive) is the variety-recovery mechanism — safety depends on "
        "feedback latency being shorter than time-to-irreversibility (Ashby)."
    ),
    "notate": (
        "Persistence — write the cycle's history so the next Perceive can "
        "read it; if it isn't notated, it didn't happen. A cycle that "
        "terminates without Work (a notated decision to refrain) is a "
        "complete cycle, not a failed one — Notate must record refrain-"
        "decisions with equal weight to Work-decisions (Illich — prevent "
        "structural bias toward action)."
    ),
}

# Account enforcement shapes — mirrors HITL/HOTL in models.py.
# Checkpoint is the empirically validated default (Ostrom); gate is the
# exception-triggered shape for high-irreversibility actions.
PRAWN_ACCOUNT_SHAPES: Mapping[str, str] = {
    "checkpoint": (
        "Soft account (DEFAULT) — Work may proceed, unaccounted work triggers "
        "post-hoc reckoning with escalating consequences. Maps to HOTL. "
        "Higher variety (reckons with actual outcome). Empirically validated "
        "for commons governance (Ostrom)."
    ),
    "gate": (
        "Hard account (EXCEPTION) — no Work without prior Account. Maps to HITL. "
        "Reserved for high-irreversibility actions where post-hoc reckoning "
        "cannot restore the prior state. Trades false-negative reduction for "
        "false-positive introduction (Ashby); sensitivity is tunable."
    ),
}

PRAWN_CANONICAL_NOTE = "CANONICAL PRAWN STAGES (the governed operational cycle):"
PRAWN_ACCOUNT_NOTE = "CANONICAL PRAWN ACCOUNT ENFORCEMENT SHAPES:"


def canonical_prawn_note() -> str:
    return PRAWN_CANONICAL_NOTE + "\n" + _bullets(PRAWN_STAGES)


def canonical_prawn_account_note() -> str:
    return PRAWN_ACCOUNT_NOTE + "\n" + _bullets(PRAWN_ACCOUNT_SHAPES)


# ---- PAIDEIA --------------------------------------------------------------------

PAIDEIA_VERSION = "v0.2-draft"
PAIDEIA_AXES = ("M", "D", "E", "V", "C", "L", "S", "P", "A", "Em")
PAIDEIA_AXIS_NAMES = {
    "M": "MODALITY",
    "D": "DEPTH",
    "E": "ENGAGEMENT",
    "V": "MOTIVATION",
    "C": "METACOGNITION",
    "L": "LOAD",
    "S": "SCAFFOLD",
    "P": "PRACTICE",
    "A": "AUTHENTICITY",
    "Em": "EMOTION",
}
PAIDEIA_REFERENTS = ("artifact", "reader_state", "reader_demand")

# v0.1 axis order (9 axes, no Em). Kept for version-aware parsing of legacy
# v0.1 signatures/plans/scores (docs/paideia-9-v0.2-draft.md: "v0.1
# signatures become shorter strings for compatibility comparisons").
PAIDEIA_AXES_V0_1 = ("M", "D", "E", "V", "C", "L", "S", "P", "A")

# v0.2 intent polarity (Proposal C). Additive per-axis field on plans; entries
# without it default to DEFAULT_INTENT (v0.1 behavior).
PAIDEIA_INTENT_VALUES = ("required", "deliberate_absent", "n_a")
PAIDEIA_DEFAULT_INTENT = "required"


def paideia_signature(vec: Mapping[str, object]) -> str:
    """Build a canonical PAIDEIA signature string (v0.2: 10 axes, Em last)."""
    return "-".join(str(vec[a]) for a in PAIDEIA_AXES)


def paideia_signature_v0_1(vec: Mapping[str, object]) -> str:
    """Build a v0.1 (9-axis) signature for legacy comparisons."""
    return "-".join(str(vec[a]) for a in PAIDEIA_AXES_V0_1)


# ---- Sibling Modules -------------------------------------------------------------

# Additional canonical sibling modules around ARCANA, in a contract-first structure.
SIBLING_MODULES: Mapping[str, SiblingModuleSpec] = {
    "NOMOS": {
        "version": "v0.1",
        "status": "AUTHORIZED",
        "role": "normative-standards",
        "purpose": "Normative mapping across policy and compliance frameworks.",
        "boundary": (
            "NOMOS receives governance artifacts and produces evidence-backed normative "
            "alignment outputs; it does not publish content or execute bus routing."
        ),
        "contract_focus": (
            "policy-alignment mappings for NIST AI RMF, EU AI Act, ISO 42001, "
            "risk-classification receipts, and compliance-justification evidence."
        ),
        "terms": (
            "policy-mapping",
            "exception-receipts",
            "compliance-evidence",
        ),
    },
    "EVIDENCE": {
        "version": "v0.1",
        "status": "AUTHORIZED",
        "role": "observability",
        "purpose": "Capture, retain, and audit evidence from generation and scoring.",
        "boundary": (
            "EVIDENCE owns telemetry and quality records only; it does not alter "
            "content generation or release gate decisions."
        ),
        "contract_focus": (
            "quality telemetry, drift detection, error taxonomies, and confidence "
            "trend reporting for all content and governance outcomes."
        ),
        "terms": (
            "quality-telemetry",
            "drift-detection",
            "audit-packaging",
        ),
    },
    "RELEASE": {
        "version": "v0.1",
        "status": "AUTHORIZED",
        "role": "distribution-gating",
        "purpose": "Governed rollout and publication gate control.",
        "boundary": (
            "RELEASE manages outbound distribution permissions and receipts; it does not "
            "perform content synthesis."
        ),
        "contract_focus": (
            "publication and rollout controls, release receipts, rollback plans, "
            "and external channel handoff rules."
        ),
        "terms": (
            "pre-release-gates",
            "publication-receipts",
            "rollback-conditions",
        ),
    },
    "LINGUA": {
        "version": "v0.1",
        "status": "AUTHORIZED",
        "role": "editorial-engineering",
        "purpose": "Narrative, style, and editorial variant governance.",
        "boundary": (
            "LINGUA controls language variant policies and safety checks; it does not "
            "set standards mapping or distribution authority."
        ),
        "contract_focus": (
            "narrative systems, variant routing, citation integrity checks, and "
            "style/intent alignment for publication channels."
        ),
        "terms": (
            "variant-routing",
            "editorial-integrity",
            "citation-safety",
        ),
    },
    "SYNTHESIS": {
        "version": "v0.1-draft",
        "status": "RUNTIME-DEBUT",
        "role": "runtime-orchestration",
        "purpose": (
            "Runtime orchestration surface for ARCANA run pipelines: "
            "lens/stage selection, sequencing, and receipt assembly. "
            "First executable workflow (paideia-review) landed in "
            "SYNTHESIS/runtime.py; broader orchestration still ROADMAP."
        ),
        "boundary": (
            "SYNTHESIS orchestrates the run pipeline and routes work; it does "
            "not generate content, score artifacts, or publish."
        ),
        "contract_focus": (
            "run orchestration, lens/stage dispatch, run-state monitoring, "
            "and receipt bundle assembly across sibling modules."
        ),
        "terms": (
            "run-orchestration",
            "stage-dispatch",
            "receipt-assembly",
        ),
    },
    "CANON": {
        "version": "v0.1-draft",
        "status": "ROADMAP",
        "role": "artifact-registry",
        "purpose": (
            "Public artifact registry and policy baseline mirror: the "
            "canonical record of published artifacts and the normative "
            "baseline."
        ),
        "boundary": (
            "CANON indexes and mirrors; it does not generate content, score "
            "artifacts, or gate publication (that is RELEASE)."
        ),
        "contract_focus": (
            "artifact registration and indexing, policy baseline mirroring, "
            "and provenance/lineage tracking for published artifacts."
        ),
        "terms": (
            "artifact-registry",
            "baseline-mirror",
            "provenance-tracking",
        ),
    },
}

SIBLING_NAMES = tuple(SIBLING_MODULES.keys())


# Canonical rosters for the roadmap siblings (SYNTHESIS, CANON). Each entry
# is a runnable lens persona in scripts/lenses.json (school 'SYNTHESIS / ...'
# or 'CANON / ...'). Drift is caught by the test_synthesis_roles_have_prompts
# and test_canon_stages_have_prompts coverage tests.
SYNTHESIS_ROLES: Mapping[str, str] = {
    "conductor": (
        "Orchestrates the full run: selects lenses, sequences stages, and "
        "assembles the article family from per-lens outputs."
    ),
    "dispatcher": (
        "Routes sub-tasks to the right lens or stage and manages "
        "parallelism, dependencies, and the reason-act separation."
    ),
    "monitor": (
        "Tracks run state, surfaces drift between plan and execution, and "
        "emits per-step receipts for EVIDENCE."
    ),
}

CANON_STAGES: Mapping[str, str] = {
    "registrar": (
        "Indexes and registers published artifacts as the canonical, "
        "deduplicated record."
    ),
    "baseline": (
        "Mirrors the policy baseline (NOMOS standards, PAIDEIA rubrics) as "
        "the normative reference artifacts are measured against."
    ),
    "provenance": (
        "Tracks lineage and provenance of artifacts: what generated what, "
        "from which inputs, under which contract version."
    ),
}


def sibling_contract_paths() -> dict[str, tuple[str, str]]:
    """Return canonical contract module path and expected module constant for each sibling."""
    return {
        name: (f"{name}/contracts.py", f"{name}_contracts")
        for name in SIBLING_NAMES
    }


def sibling_contract_spec(name: str) -> SiblingModuleSpec:
    """Return the canonical metadata contract for a sibling module."""
    return SIBLING_MODULES[name]


def sibling_contract_manifest() -> dict[str, dict[str, object]]:
    """Return JSON-serializable sibling contract metadata for tools and docs."""
    paths = sibling_contract_paths()
    return {
        name: {
            "name": name,
            "contract_path": paths[name][0],
            "import_name": f"{name}.contracts",
            **SIBLING_MODULES[name],
        }
        for name in SIBLING_NAMES
    }


def _bullets(items: Mapping[str, str]) -> str:
    return "\n".join(f"  • {k}: {v}" for k, v in items.items())
