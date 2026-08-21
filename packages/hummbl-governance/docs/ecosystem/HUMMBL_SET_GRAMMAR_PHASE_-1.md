# HUMMBL Set Grammar — Phase -1 Admission

```yaml
phase: -1
name: HUMMBL Set Grammar Admission
status: PHASE_-1_OPEN
canon_level: candidate_only
date: 2026-06-25
promotion_allowed: false
next_phase: Phase 0 schema-seed design
primary_rule: "Nothing admitted here is canon yet. This phase collects, names,
  separates, and stress-tests candidate object families before schema or promotion."
```

> **Primary thesis:** HUMMBL needs a governed object grammar where Problem,
> Question, Claim, Evidence, Decision, Task, Prompt, Gate, Receipt, Artifact,
> Protocol, and Canon remain **distinct but composable**. Prompts are invocation
> artifacts, not sources of truth. Evidence grounds. Decisions authorize.
> Receipts attest. Canon is promoted governed knowledge.

---

## 1. Phase -1 Objective

> What reusable object types does HUMMBL need in order to govern interdisciplinary
> problems, questions, tasks, prompts, evidence, decisions, gates, and receipts
> without collapsing them into one vague "knowledge pack"?

This is an **admission/discovery phase**, not an implementation phase. The goal
is to prevent premature schema lock-in.

---

## 2. Core Finding

The original four object types are necessary but incomplete:

| Object   | Function                                                         |
|----------|------------------------------------------------------------------|
| Problem  | Names a gap, tension, harm, opportunity, or unresolved condition |
| Question | Converts problem-space into inquiry                              |
| Task     | Converts decision into execution                                 |
| Prompt   | Invokes a model/agent/tool                                       |

They cover inquiry and execution but lack governance, evidence, evaluation,
semantic, context, and output layers. Without those, prompts and tasks become
overloaded with governance responsibility they should not carry.

---

## 3. Form Distinction: Set vs Pack vs Registry vs Ledger vs Graph

| Form         | Meaning                                                              |
|--------------|----------------------------------------------------------------------|
| **Set**      | Curated group of related objects                                     |
| **Pack**     | Portable/use-ready bundle, usually for reuse or distribution         |
| **Registry** | Authoritative index of entities, capabilities, artifacts, or records |
| **Ledger**   | Chronological or decision-bearing record                             |
| **Library**  | Reusable patterns, templates, primitives, or procedures              |
| **Suite**    | Evaluation/test collection                                           |
| **Bundle**   | Receipt/evidence/document collection tied to a process               |
| **Graph**    | Network of entities and relationships                                |

> **Implication:** HUMMBL Problem Sets may not be enough. Interdisciplinary
> problem work likely needs **Problem Graphs** or **Problem Constellations**,
> because the problems intersect, depend on, amplify, and constrain each other.

---

## 4. Candidate Top-Level Object Families

### A. Inquiry Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Problem Set         | Group related problems                                |
| Problem Graph       | Interdisciplinary, mutually entangled problems        |
| Question Set        | Organize inquiry                                      |
| Hypothesis Set      | Possible explanations or solution theories            |
| Claim Set           | Answers are made of claims — mandatory                |
| Assumption Set      | Prevent hidden beliefs from becoming invisible doctrine|

### B. Evidence Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Source Pack         | Curated sources for reuse                             |
| Evidence Set        | Grounds claims with verified evidence                 |
| Corpus Set          | Body of text/data for analysis                        |
| Reference Set       | Citations and cross-references                        |
| Receipt Bundle      | Attestation collection tied to a process              |
| Observation Log     | Chronological record of observed events               |

> **Critical:** Prompt Pack ≠ Evidence Pack. A prompt can generate analysis.
> Evidence grounds the analysis. These must remain distinct.

### C. Governance Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Gate Set            | Validation checkpoints                                |
| Decision Ledger     | Chronological record of authoritative decisions       |
| Risk Register       | Tracked risks with likelihood, impact, mitigation     |
| Constraint Set      | Hard limits on what may be done                       |
| Policy Set          | Rules governing behavior                              |
| Authority Map       | Who/what has permission to do what                    |
| Exception Set       | Documented deviations from policy                     |
| Invariant Set       | Non-negotiable conditions that must always hold       |

> **This is the highest-priority missing layer.** A HUMMBL system without
> these collapses into "smart productivity." A HUMMBL system with these
> becomes governable.
>
> Core chain: `Authority → Gate → Decision → Task → Receipt`

### D. Execution Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Task Set            | Convert decisions into execution                      |
| Workflow Set        | Multi-step procedures                                 |
| Protocol Set        | Standardized interaction patterns                     |
| Prompt Pack         | Invocation artifacts for models/agents/tools          |
| Agent Pack          | Agent configurations and rosters                      |
| Tool Set            | Available tools and their capabilities                |
| Capability Registry | What agents/tools/humans can do                       |
| Delegation Set      | Delegated authority and scope                         |

> **Prompt Packs belong here, not at the center.** Prompts are invocation
> artifacts. They are not truth, authority, or evidence.

### E. Evaluation Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Metric Set          | Quantitative measures                                 |
| Eval Suite          | Evaluation test collection                            |
| Benchmark Set       | Performance comparisons                               |
| Test Fixture Set    | Input/output pairs for testing                        |
| Validation Set      | Checks that something meets its spec                  |
| Failure Mode Set    | Known ways the system can fail                        |
| Adversarial Set     | Red-team / attack test cases                          |

> Every reusable pack should eventually have an eval surface.
> Prompt Packs without evals are just reusable incantations.
> Task Sets without receipts are unverified work queues.
> Claim Sets without evidence are belief clusters.

### F. Semantic Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Definition Set      | Governed term definitions                             |
| Ontology Set        | Entity types and their relationships                  |
| Glossary Set        | Plain-language term reference                         |
| Taxonomy Set        | Classification hierarchy                              |
| Pattern Library     | Reusable solution patterns                            |
| Primitive Library   | Atomic building blocks                                |
| Transformation Map  | How one object type transforms into another           |

> This is where HUMMBL protects against semantic drift. Definitions should
> not be buried inside prompts, tasks, or markdown essays.

### G. Context Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Context Pack        | Scope and environment for a work unit                 |
| Domain Set          | Subject-matter domains                                |
| Stakeholder Map     | Who cares, why, and with what authority               |
| Scenario Set        | Possible futures or situations                        |
| Use-Case Set        | Concrete usage scenarios                              |
| Environment Set     | Runtime/deployment environment                        |
| Market/Opportunity  | Market context and opportunity mapping                |

> Problems and questions change depending on context. The same question
> asked in AI governance vs coaching vs bioinformatics may require different
> evidence, gates, risks, claims, and tasks.

### H. Output Objects

| Object              | Function                                              |
|---------------------|-------------------------------------------------------|
| Artifact Registry   | Durable products of work                              |
| Document Set        | Written outputs                                       |
| Schema Set          | Machine-readable structure definitions                |
| Report Set          | Periodic or event-driven reports                      |
| Diagram Set         | Visual representations                                |
| Product Spec Set    | Product specifications                                |
| PRD Set             | Product requirements documents                        |
| Public Claim Set    | Claims made publicly (stricter promotion)             |
| Publication Pack    | Ready-to-publish bundles                              |

> Artifacts should carry: identity, status, version, source inputs, claims
> made, evidence used, gates passed, receipts produced, canon level.

---

## 5. Candidate Master Chain

### Inquiry-forward version

```
Context → Problem → Question → Hypothesis → Claim → Evidence
→ Decision → Task → Artifact → Gate → Receipt → Pattern → Protocol → Canon
```

### Governance-forward version

```
Context → Problem Graph → Question Set → Claim Set → Evidence Set
→ Risk Register → Decision Ledger → Task Set → Artifact Registry
→ Gate Set → Receipt Bundle → Canon
```

---

## 6. Relationship Grammar

Each object defines upstream and downstream relations:

```
Problem       → generates →  Question
Question      → elicits  →   Claim
Claim         → requires →   Evidence
Evidence      → grounds  →   Claim
Decision      → authorizes → Task
Task          → produces →   Artifact
Gate          → evaluates →  Artifact or Action
Receipt       → attests  →   Action or Validation
Pattern       → abstracts →  repeated Solution
Protocol      → standardizes → Interaction
Canon         → promotes →   validated Knowledge
```

### Cardinality rules

```
Problem       1:N  Questions
Question      1:N  Claims
Claim         1:N  Evidence
Decision      1:N  Tasks
Task          1:1  Receipt (mandatory)
Gate          1:N  Artifacts (evaluates)
Receipt       1:1  Action (attests)
Context       1:N  Problems (scopes)
```

---

## 7. Overlap / Failure-Mode Warnings

| Overload                                    | Failure Mode                                    |
|---------------------------------------------|-------------------------------------------------|
| Prompt Pack pretending to be Evidence Set   | Unfounded claims appear grounded                |
| Task Set pretending to be Decision Ledger   | Work appears authorized without authority       |
| Problem Set pretending to be Ontology       | Definitions drift, terms become ambiguous       |
| Receipt Bundle pretending to prove truth    | Process correctness mistaken for factual truth  |
| Claim Set without Evidence Set              | Belief cluster — assertions without grounding   |
| Gate Set without Risk Register              | Validation without threat model                 |
| Prompt Pack without Eval Suite              | Reusable incantation — no quality signal        |
| Decision Ledger without Authority Map       | Decisions appear authoritative but aren't       |

---

## 8. Full Admission List (65 candidate object types)

```
01.  Problem              34. Protocol
02.  Problem Set          35. Protocol Set
03.  Problem Graph        36. Prompt
04.  Question             37. Prompt Pack
05.  Question Set         38. Agent
06.  Hypothesis           39. Agent Registry
07.  Hypothesis Set       40. Capability
08.  Claim                41. Capability Registry
09.  Claim Set            42. Tool
10.  Assumption           43. Tool Set
11.  Assumption Set       44. Artifact
12.  Source               45. Artifact Registry
13.  Source Pack          46. Receipt
14.  Evidence             47. Receipt Bundle
15.  Evidence Set         48. Metric
16.  Context              49. Metric Set
17.  Context Pack         50. Eval
18.  Stakeholder          51. Eval Suite
19.  Stakeholder Map      52. Test Fixture
20.  Constraint           53. Fixture Set
21.  Constraint Set       54. Failure Mode
22.  Invariant            55. Failure Mode Set
23.  Invariant Set        56. Pattern
24.  Risk                 57. Pattern Library
25.  Risk Register        58. Definition
26.  Gate                 59. Definition Set
27.  Gate Set             60. Ontology
28.  Decision             61. Ontology Set
29.  Decision Ledger      62. Public Claim
30.  Task                 63. Publication Pack
31.  Task Set             64. Canon Entry
32.  Workflow             65. Canon Registry
33.  Workflow Set
```

Too many for immediate implementation. Useful for discovery.

---

## 9. Priority Admission Classes (12 for next phase)

```
Problem Graph       — interdisciplinary entangled problems
Question Set        — organized inquiry
Claim Set           — answers as governed claims
Evidence Set        — grounded evidence
Assumption Set      — surfaced hidden beliefs
Decision Ledger     — authoritative decisions
Gate Set            — validation checkpoints
Receipt Bundle      — process attestation
Risk Register       — tracked risks
Task Set            — execution units
Prompt Pack         — invocation artifacts (demoted from center)
Artifact Registry   — durable outputs
```

These give the minimum viable governed object grammar.

---

## 10. What Was Missing From the Original List

Original: `Problem Sets, Question Sets, Task Sets, Prompt Packs`

Most important missing five:

```
Claim Sets          — without these, answers are ungrounded assertions
Evidence Sets       — without these, claims are beliefs
Decision Ledgers    — without these, tasks appear authorized but aren't
Gate Sets           — without these, nothing validates
Receipt Bundles     — without these, actions didn't happen
```

These are the objects that keep the system from becoming prompt-centric.

---

## 11. Candidate Object Status Model

```
seed → candidate → draft → reviewed → validated → adopted → canonical
                                                          ↓
                                              deprecated → retired
                                              rejected
```

Phase -1 default for all objects:

```yaml
status: candidate
canon_level: non_authoritative
promotion_allowed: false
```

---

## 12. Candidate Schema Fields (universal)

```yaml
id:
name:
object_type:
status:
canon_level:
version:
owner:
created_at:
updated_at:
scope:
description:
inputs:           # what this object consumes
outputs:          # what this object produces
dependencies:     # what this object requires
related_objects:  # upstream/downstream relations
claims:           # claims this object makes
evidence:         # evidence supporting those claims
assumptions:      # assumptions this object depends on
risks:            # risks this object carries
gates:            # gates this object must pass
receipts:         # receipts this object has produced
authority_required:  # what authority is needed to use this
verification_method: # how to verify this object is correct
promotion_criteria:  # what's needed to promote this object
residual_risk:    # risk that remains after mitigation
```

Not every field is required for every object. These are candidate universal fields.

---

## 13. Phase -1 Gates

### G1 — Object Separation Gate

Each object type must answer:

```
What is this?
What is it not?
What does it govern?
What governs it?
What can it produce?
What can it not produce?
```

### G2 — Overlap Gate

Detect overloaded objects (see §7).

### G3 — Relationship Gate

Each object must define upstream and downstream relations (see §6).

### G4 — Promotion Gate

No object becomes canonical without:

```
definition
schema
example
counterexample
evidence requirement
validation method
receipt requirement
```

### G5 — Prompt-Centrism Gate

```
Prompt = invocation
Evidence = grounding
Decision = authority
Receipt = attestation
Canon = promoted governed knowledge
```

Prompts must not be treated as source of truth.

---

## 14. Recommended Phase 0 Target

Do **not** implement all 65 admitted objects. Phase 0 should create a small
canonical seed:

### Core (10)

```
ProblemGraph
QuestionSet
ClaimSet
EvidenceSet
DecisionLedger
TaskSet
PromptPack
GateSet
ReceiptBundle
ArtifactRegistry
```

### Support (5)

```
ContextPack
RiskRegister
AssumptionSet
EvalSuite
OntologySet
```

**Total: 15 object families** — enough to govern real work without exploding scope.

> **Updated by operator decision (OQ-10):** v0.1 minimum expanded to 20 objects
> in 4 tiers of 5. See §14.1 below for the revised Phase 0 target.

---

## 14.1 Revised Phase 0 Target (20 Objects, 4 Tiers of 5)

Operator decision: 20 object types organized as 4 tiers of 5, with clear
priority ordering and governance-forward design.

### Tier 1: Governance Core (the convergence target)

These 5 objects directly implement the GovernableFleetAction conditions
from HUMMBL_PROBLEM_GRAMMAR.md §2.1.

| # | Object | Convergence Condition | Notes |
|---|--------|----------------------|-------|
| 1 | **ClaimSet** | Evidence (grounded assertions) | Bridge between QuestionSet and EvidenceSet; each Claim tagged with epistemic quadrant (OQ-2) |
| 2 | **EvidenceSet** | Evidence (grounds claims) | Distinct from ReceiptBundle — evidence grounds, receipts attest |
| 3 | **DecisionLedger** | Authority | 4-layer scope matching Graph of Graphs (OQ-4): L1 Artifact, L2 Category, L3 Tier, L4 Fleet |
| 4 | **GateSet** | ExceptionPath + Rollback | Both templates AND instances (OQ-5): GateTemplate (reusable) + GateInstance (artifact-specific) |
| 5 | **ReceiptBundle** | AuditReceipt | Regeneratable from underlying receipts, but regeneration produces a meta-receipt (OQ-6) |

### Tier 2: Inquiry & Context

These 5 objects wrap the governance core with problem-finding and context-setting.

| # | Object | Function | Notes |
|---|--------|----------|-------|
| 6 | **ProblemGraph** | Interdisciplinary entangled problems | Typed edges (depends-on, amplifies, constrains) — OQ-1 |
| 7 | **ProblemConstellation** | Loosely coupled problem clusters | Untyped edges — distinct from ProblemGraph (OQ-1) |
| 8 | **QuestionSet** | Organized inquiry | Converts problem-space into questions |
| 9 | **ContextPack** | Scope and environment | Required before any Problem Set can be promoted (OQ-7) |
| 10 | **AssumptionSet** | Surface hidden beliefs | Co-bridge with ClaimSet; every Claim has an AssumptionSet (OQ-2) |

### Tier 3: Execution & Evaluation

These 5 objects convert decisions into action and evaluate results.

| # | Object | Function | Notes |
|---|--------|----------|-------|
| 11 | **TaskSet** | Convert decisions to execution | Each Task requires a Receipt (convergence target) |
| 12 | **PromptPack** | Invocation artifacts | Requires attached EvalSuite before reuse at scale (OQ-3); demoted from center |
| 13 | **EvalSuite** | Evaluation surface | Mandatory for PromptPack promotion beyond 'draft' (OQ-3) |
| 14 | **RiskRegister** | Tracked risks + exception paths | Maps to ExceptionPath in convergence target |
| 15 | **ArtifactRegistry** | Durable outputs | Carries identity, status, version, claims, evidence, gates, receipts |

### Tier 4: Semantic & Identity

These 5 objects define meaning, identity, and canonical knowledge.

| # | Object | Function | Notes |
|---|--------|----------|-------|
| 16 | **UncertaintyMap** | First-class epistemic state object | Generates Claim/Assumption/Discovery/Probe sub-sets from known/unknown quadrants (OQ-2); integrates uncertainty-map skill |
| 17 | **OntologySet** | Governed definitions | Prevents semantic drift; definitions not buried in prompts |
| 18 | **AgentRegistry** | Agent identity taxonomy | Levin-inspired cognitive light cone taxonomy (OQ-9); see §14.2 |
| 19 | **CapabilityRegistry** | What agents/tools/humans can do | Tied to AgentRegistry; all holder types with cognitive light cone framing (OQ-9) |
| 20 | **CanonRegistry** | Promoted governed knowledge | Terminal object — the canon that validated knowledge enters |

### Tier Priority Rule

```
Tier 1 (Governance Core) > Tier 2 (Inquiry) > Tier 3 (Execution) > Tier 4 (Semantic)
```

Tier 1 objects must exist before Tier 2 objects can be promoted.
Tier 2 objects must exist before Tier 3 objects can be promoted.
Tier 4 objects are cross-cutting — they serve all tiers but are not blocking.

This prevents building execution (Tier 3) without governance (Tier 1) or
inquiry (Tier 2) — the failure mode of prompt-centric systems.

---

## 14.2 Agent Registry: Levin-Inspired Cognitive Light Cone Taxonomy

> **OQ-9 operator decision:** Capability Registries must be tied to an updated
> and canonized version of HUMMBL's HUAOMP × MTSMU definitions of HUMMBL Agents,
> inspired by Dr. Michael Levin's tiered and taxonomic approach to defining
> "agent" and his concept of cognitive light cones.

### Background

Dr. Michael Levin's work on basal cognition and cognitive light cones provides
a framework for defining agents beyond the human/AI binary. His key insights:

1. **Agency is a spectrum, not a binary** — all matter has some form of
   cognition/consciousness; the question is the size of the cognitive light cone
   (the set of possible futures the agent can perceive and act toward).
2. **Cognitive light cones define agent scope** — an agent's light cone
   determines what it can perceive, what it can act on, and what futures it
   can work toward.
3. **Agents are defined by their competencies, not their substrate** —
   biological, digital, organizational, and hybrid agents all have cognitive
   light cones; the substrate matters less than the competency space.

### HUMMBL Agent Taxonomy (Candidate)

```
AgentCognitiveLightCone ::=
  Level    ::= the agent's perception/action horizon
  Competencies ::= what the agent can perceive and act on
  Substrate    ::= biological | digital | hybrid | organizational | material
  Autonomy     ::= the degree of self-directed action within the light cone
  Falsifiability ::= how to test the agent's claimed competencies

AgentTier ::=
  L0_MINIMAL    ::= "substrate-level agency (e.g., a single tool, a file, a sensor)"
  L1_REACTIVE   ::= "responds to stimuli but no internal model (e.g., a circuit breaker)"
  L2_DELIBERATIVE ::= "has internal model, plans within scope (e.g., a coding agent)"
  L3_META       ::= "models other agents, coordinates (e.g., a fleet coordinator)"
  L4_REFLECTIVE ::= "models itself, improves own light cone (e.g., recursive governance)"
```

### Integration with Capability Registry

```
CapabilityRegistry ::=
  Capability ::=
    Name          ::= what the capability is
    AgentRef      ::= reference to AgentRegistry entry
    LightConeLevel ::= L0_MINIMAL | L1_REACTIVE | L2_DELIBERATIVE | L3_META | L4_REFLECTIVE
    Competency    ::= what this capability enables the agent to perceive/do
    Falsifiability ::= how to test this capability claim
    Evidence      ::= EvidenceSet reference proving the capability exists
```

### Open Sub-Question

> "All matter is conscious in some way — we just still need to generate the
> new lexicon for the world." — operator

This is a Phase -1 observation, not a Phase 0 implementation target. The
lexicon for substrate-level agency (L0_MINIMAL) is a candidate research
question for the OntologySet (Tier 4, object 17). The HUMMBL Set Grammar
admits the possibility but does not canonize it yet.

---

## 15. Resolved Questions (Operator + Fleet Review)

All 10 open questions resolved through operator decisions, fleet architecture
review (ADR-FM-057, ADR-FM-038, uncertainty-map skill), and HUAOMP × MTSMU
synthesis. Binary-first approach used throughout: start with a binary
distinction, then add dimensions with bounded scope and governance rules to
mitigate infinite regress.

### OQ-1: Problem Graphs vs Constellations

**Decision:** Both — distinct object types.
- **Problem Graph**: typed edges (depends-on, amplifies, constrains). For
  interdisciplinary problems with known relationship types.
- **Problem Constellation**: loosely coupled cluster without typed edges. For
  problems that co-occur but whose relationships are not yet typed.
- A Constellation can promote to a Graph when edges are typed.

### OQ-2: Claim Set as bridge + Uncertainty Map as first-class object

**Decision:** Both (layered). Binary first, then add dimensions.
- **Layer 1 (binary):** Claim Set is the bridge between Question Set and
  Evidence Set. Each Claim carries an epistemic quadrant tag
  (known-known / known-unknown / unknown-known / unknown-unknown) from the
  uncertainty-map skill. Assumption Set is the co-bridge — every Claim has
  an Assumption Set surfacing what's taken for granted.
- **Layer 2 (generative):** Uncertainty Map is a first-class HUMMBL object
  (Tier 4, #16) that generates four sub-sets:
  - known-knowns → ClaimSet (verified claims)
  - known-unknowns → DiscoveryAgenda (research tasks)
  - unknown-knowns → AssumptionSet (surface latent knowledge)
  - unknown-unknowns → ProbeSet (adversarial/monitoring tasks)
- **Bounded scope rule:** Claims inherit their quadrant from the parent
  Uncertainty Map. If no Uncertainty Map exists, Claims default to
  `unknown-known` (conservative — assume latent knowledge).
- **Infinite regress mitigation:** Uncertainty Maps cannot be nested beyond
  depth 2 (an Uncertainty Map about an Uncertainty Map is allowed; depth 3
  is prohibited). This prevents epistemic infinite regress.

### OQ-3: Prompt Pack requires Eval Suite for scale

**Decision:** Yes, mandatory for scale.
- Prompt Packs at `draft` or `candidate` status can exist without Eval Suites.
- Prompt Packs promoted to `adopted` or higher (i.e., reused at fleet scale
  or across multiple agents) MUST have an attached Eval Suite.
- This is a hard gate, not a recommendation. The GateSet (Tier 1, #4)
  enforces this: `PromptPackPromotionGate` checks for EvalSuite reference
  before allowing status promotion beyond `draft`.

### OQ-4: Decision Ledger scope — 4-layer (matches Graph of Graphs)

**Decision:** 4-layer, matching ADR-FM-057's Graph of Graphs topology.
- **L1 Artifact-level:** implementation decisions (e.g., "merge this PR",
  "use this library"). Repo-local.
- **L2 Category-level:** architecture decisions (e.g., "adopt this pattern",
  "this is a Goal/Task/Quest/Mission"). Project-local. Maps to ADRs.
- **L3 Tier-level:** fleet-wide tier escalations (e.g., "promote this from
  P2 to P1"). Cross-project. Operator-approved.
- **L4 Fleet-level:** global governance decisions (e.g., "adopt this as
  canon", "promote this agent's trust tier"). Fleet-wide. Maps to
  Constitution/Krineia.
- Cross-layer edges (from ADR-FM-057's 11 edge types) connect decisions
  across layers: `artifact_has_tier`, `tier_escalates_to`, etc.

### OQ-5: Gate Sets — both templates and instances

**Decision:** Both. Additional sub-documents created if needed.
- **GateTemplate:** reusable gate definition (e.g., "Promotion Gate",
  "Merge Gate", "Security Gate", "Prompt-Centrism Gate"). Defines the check
  type and required parameters.
- **GateInstance:** artifact-specific gate, parameterized from a template.
  Binds the template to a specific artifact with concrete values.
- The 5 Phase -1 gates (G1 Separation, G2 Overlap, G3 Relationship, G4
  Promotion, G5 Prompt-Centrism) are GateTemplates.
- Each artifact promotion creates GateInstances from these templates.
- **Sub-document needed:** Gate Template Catalog (candidate doc for Phase 0).

### OQ-6: Receipt Bundles — regeneratable with meta-receipt

**Decision:** Regeneratable, but regeneration produces a meta-receipt.
- Individual receipts are immutable (append-only, never edited or deleted).
- Receipt Bundles are collections/views of underlying receipts.
- If a Bundle is regenerated (e.g., after data loss, or to include
  additional receipts discovered later), the regeneration itself produces
  a **meta-receipt** that records:
  - What was regenerated
  - When
  - By whom (which agent/operator)
  - What source receipts were used
  - SHA-256 fingerprint of the original bundle (if known)
- This preserves audit trail integrity while allowing reconstruction.
- **Invariant:** The meta-receipt is itself a receipt and enters the
  append-only audit trail. Regeneration without a meta-receipt is a
  MustNever violation.

### OQ-7: Context Pack required for promotion

**Decision:** Yes, required before any Problem Set can be promoted.
- Problems without context are ungrounded — the same problem in different
  contexts requires different evidence, gates, and risks.
- Matches ADR-FM-057's Category system where every artifact declares its
  category (which is a form of context).
- **Gate:** `ProblemSetPromotionGate` checks for ContextPack reference
  before allowing status promotion beyond `candidate`.
- A Problem Set at `seed` or `candidate` status can exist without a
  ContextPack, but cannot be promoted to `draft` or higher without one.

### OQ-8: Public Claim Sets — stricter promotion path

**Decision:** Yes, stricter path.
- Public Claim Sets carry reputational, legal, and disclosure risks that
  internal Claim Sets do not.
- **Stricter path requires:**
  1. Independent review (non-actor, different trust tier)
  2. Evidence verification (all claims must be `verified` status)
  3. Disclosure handling plan (what happens if a claim is challenged publicly)
  4. Operator approval (explicit human sign-off)
- **Additional tie-in:** Public Claim Sets that reference security findings
  must reference a Disclosure-Producing Scan authorization (from the Scan
  Taxonomy in HUMMBL_PROBLEM_GRAMMAR.md §3.DE) before promotion.
- Internal Claim Sets follow the standard promotion path (seed → candidate
  → draft → reviewed → validated → adopted → canonical).

### OQ-9: Capability Registries — Levin-inspired cognitive light cone taxonomy

**Decision:** Tie to updated HUAOMP × MTSMU agent definitions, inspired by
Dr. Michael Levin's cognitive light cone taxonomy.
- AgentRegistry (Tier 4, #18) uses a 5-level cognitive light cone taxonomy:
  L0_MINIMAL → L1_REACTIVE → L2_DELIBERATIVE → L3_META → L4_REFLECTIVE
- CapabilityRegistry (Tier 4, #19) is tied to AgentRegistry — every
  Capability references an Agent and its LightConeLevel.
- All holder types (agents, tools, humans) are covered: tools are
  L0_MINIMAL agents, humans are typically L3_META or L4_REFLECTIVE,
  AI agents range from L1_REACTIVE to L4_REFLECTIVE.
- **Substrate-independent:** biological, digital, hybrid, organizational,
  and material agents all have cognitive light cones.
- **Open sub-question:** "All matter is conscious in some way" — the lexicon
  for L0_MINIMAL agency is a candidate research question for OntologySet.
  Admitted as possibility, not canonized yet. See §14.2.

### OQ-10: Minimum v0.1 — 20 objects, 4 tiers of 5

**Decision:** 20 object types in 4 tiers of 5.
- **Tier 1 (Governance Core, 5):** ClaimSet, EvidenceSet, DecisionLedger,
  GateSet, ReceiptBundle — directly implement convergence target.
- **Tier 2 (Inquiry & Context, 5):** ProblemGraph, ProblemConstellation,
  QuestionSet, ContextPack, AssumptionSet — wrap governance with
  problem-finding and context-setting.
- **Tier 3 (Execution & Evaluation, 5):** TaskSet, PromptPack, EvalSuite,
  RiskRegister, ArtifactRegistry — convert decisions to action and evaluate.
- **Tier 4 (Semantic & Identity, 5):** UncertaintyMap, OntologySet,
  AgentRegistry, CapabilityRegistry, CanonRegistry — define meaning,
  identity, and canonical knowledge.
- **Tier priority rule:** Tier 1 > Tier 2 > Tier 3. Tier 4 is cross-cutting.
  This prevents building execution without governance — the failure mode
  of prompt-centric systems.
- See §14.1 for full table.

---

## 16. Confidence Assessment

```yaml
claim: "The HUMMBL Set Grammar candidate object families are well-defined for Phase -1 admission"
semantic_confidence: 0.85
confidence_kind: synthesis_judgment
calibration_status: uncalibrated
basis: "operator decisions on all 10 open questions + existing fleet architecture review (ADR-FM-057, ADR-FM-038, uncertainty-map skill) + HUAOMP × MTSMU synthesis"
independent_verification: pending

evidence:
  - claim: "original 4 object types are incomplete"
    source: "operator analysis + comparison against implemented governance primitives"
    verification_status: internally_cross_referenced
    cross_reference: "HUMMBL_PROBLEM_GRAMMAR.md §2.1 convergence target lists 7 conditions; original 4 types cover <half"
  - claim: "65 candidate object types cover the necessary space"
    source: "operator-provided list + cross-reference with HUMMBL_PROBLEM_GRAMMAR families"
    verification_status: reported
  - claim: "20 object families in 4 tiers of 5 are sufficient for v0.1"
    source: "operator decision (OQ-10) + alignment with convergence target (§2.1)"
    verification_status: internally_cross_referenced
    cross_reference: "Tier 1 objects map 1:1 to convergence conditions; Tier 2-4 fill inquiry/execution/semantic gaps"
  - claim: "4-layer Decision Ledger matches existing Graph of Graphs topology"
    source: "ADR-FM-057 Decision 3: 4-layer topology with 11 edge types"
    verification_status: internally_cross_referenced
    cross_reference: "hummbl-governance/docs/adr/research/ADR-FM-057-kernel-doctrine-tier-graph-scavenger-integration.md lines 107-145"
  - claim: "Uncertainty Map integrates existing uncertainty-map skill"
    source: "apex-nexus/skills/uncertainty-map/SKILL.md — 4-quadrant Rumsfeld matrix"
    verification_status: internally_cross_referenced
    cross_reference: ".claude/skills/uncertainty-map/SKILL.md defines known/unknown quadrant framework"
  - claim: "Levin cognitive light cone taxonomy provides agent definition framework"
    source: "operator reference to Dr. Michael Levin's basal cognition work"
    verification_status: reported
  - claim: "all 10 open questions resolved"
    source: "operator decisions recorded in §15"
    verification_status: verified_direct
    cross_reference: "§15 of this document contains all 10 decisions with rationale"

uncertainties:
  - "Levin cognitive light cone taxonomy is referenced but not yet formalized in HUMMBL terms"
  - "L0_MINIMAL agency lexicon ('all matter is conscious') is an open research question, not canon"
  - "Gate Template Catalog sub-document is needed but not yet created"
  - "relationship grammar is directional but not yet typed (composition vs aggregation vs reference)"
  - "no schema exists yet for the 20 v0.1 objects — structural validation is impossible"
  - "overlap between EvidenceSet and ReceiptBundle is resolved in principle but not in schema"
  - "UncertaintyMap depth-2 nesting limit requires validation language"
  - "CanonRegistry requires strict anti-laundering promotion criteria"

next_lanes:
  - "create Phase 0 schema seed (envelope + Tier 1 schemas) — see §18"
  - "formalize Levin cognitive light cone taxonomy in HUMMBL terms (research)"
  - "create Gate Template Catalog sub-document"
  - "stress-test 20 objects against a real HUMMBL scenario"
  - "define cross-object relationship types (composition vs aggregation vs reference)"
  - "create overlap detection rules for G2 gate"
  - "route to fleet review for Phase 0 promotion"
```

### Evidence State Definitions

Per ChatGPT review, evidence states are tightened. `verified` is reserved for
direct inspection of concrete artifacts (repo paths, commits, docs, schemas,
tests, validation output). Cross-reference against architecture docs is
`internally_cross_referenced`, not absolute verified.

```yaml
evidence_states:
  verified_direct: "tied to concrete repo paths, commits, docs, schemas, tests, or validation output"
  internally_cross_referenced: "cross-referenced against existing architecture docs, not directly inspected"
  reported: "stated by operator or agent, not independently checked"
  inferred: "derived from other evidence, not directly observed"
  speculative: "proposed without evidence"
  unimplemented: "designed but not yet built"
```

---

## 17. Phase -1 Closeout Receipt

```yaml
phase: -1
status: closeout_candidate
branch: fix/devin/grammar-patch-schema-evidence
pr: 131
commits:
  - 58ce841  # Problem Grammar schema + evidence ledger + operator decisions
  - 6382542  # Phase -1 Set Grammar admission (65 candidate objects)
  - 5c904b6  # Resolve all 10 open questions + 20-object v0.1 target
promotion_status: not_canon
phase_0_authorized: schema_seed_design_only
remaining_uncertainties:
  - Levin taxonomy not yet formalized in HUMMBL terms
  - L0_MINIMAL agency lexicon remains open research
  - no schemas exist yet for the 20 object families
  - UncertaintyMap depth-2 nesting limit requires validation language
  - CanonRegistry requires strict anti-laundering promotion criteria
  - Gate Template Catalog sub-document not yet created
  - cross-object relationship types not yet defined
  - EvidenceSet vs ReceiptBundle overlap resolved in principle but not in schema
```

---

## 18. Phase 0 Schema-Seed Plan

Per ChatGPT review: do not create 20 independent schemas yet. Build the
shared envelope first, then Tier 1 Governance Core schemas, then register
the remaining 15 object families as registry entries with examples and
counterexamples until promoted.

### Phase 0 Schema Seed (6 files)

```text
schemas/hummbl_object_envelope.schema.json   # shared envelope all objects inherit
schemas/claim_set.schema.json                 # Tier 1: Evidence (grounded assertions)
schemas/evidence_set.schema.json              # Tier 1: Evidence (grounds claims)
schemas/decision_ledger.schema.json           # Tier 1: Authority
schemas/gate_set.schema.json                  # Tier 1: ExceptionPath + Rollback
schemas/receipt_bundle.schema.json            # Tier 1: AuditReceipt
```

### Remaining 15 Object Families (Registry Entries)

Tier 2, 3, and 4 objects are registered as entries with examples and
counterexamples. They are not promoted to schema until they pass Phase 0
gates (see §19).

```text
Tier 2 (Inquiry & Context):
  ProblemGraph          — registry entry + example + counterexample
  ProblemConstellation  — registry entry + example + counterexample
  QuestionSet           — registry entry + example + counterexample
  ContextPack           — registry entry + example + counterexample
  AssumptionSet         — registry entry + example + counterexample

Tier 3 (Execution & Evaluation):
  TaskSet               — registry entry + example + counterexample
  PromptPack            — registry entry + example + counterexample
  EvalSuite             — registry entry + example + counterexample
  RiskRegister          — registry entry + example + counterexample
  ArtifactRegistry      — registry entry + example + counterexample

Tier 4 (Semantic & Identity):
  UncertaintyMap        — registry entry + example + counterexample
  OntologySet           — registry entry + example + counterexample
  AgentRegistry         — registry entry + example + counterexample
  CapabilityRegistry    — registry entry + example + counterexample
  CanonRegistry         — registry entry + example + counterexample
```

### Governance Distinction (Explicit)

Per ChatGPT review, the governance distinction between object families is
made explicit to prevent conflation:

```text
PromptPack      = invocation          (how agents are called)
EvidenceSet     = grounding           (what substantiates claims)
DecisionLedger  = authority           (who decided what, when, why)
GateSet         = evaluation/permission (what checks must pass)
ReceiptBundle   = attestation         (proof that something happened)
CanonRegistry   = promoted governed knowledge (what is accepted as canon)
```

---

## 19. Phase 0 Hard Gates

Per ChatGPT review, these hard gates govern Phase 0 promotion. No exceptions.

```text
G-P0-1: No object family promoted to canon without schema, example,
        counterexample, evidence requirement, validation rule, and receipt
        requirement.

G-P0-2: No PromptPack admitted for scale without attached EvalSuite.
        (Reinforces OQ-3 decision as a Phase 0 hard gate.)

G-P0-3: No PublicClaimSet path without stricter authorization and
        disclosure-producing scan classification.
        (Reinforces OQ-8 decision as a Phase 0 hard gate.)

G-P0-4: No Arbiter/self-scoring loop introduced through DecisionLedger or
        CanonRegistry. Independent review required for canon promotion.
        (Prevents self-promotion laundering.)

G-P0-5: No collapse of ProblemGraph and ProblemConstellation. Typed vs
        untyped edge distinction is preserved.
        (Reinforces OQ-1 decision as a Phase 0 hard gate.)

G-P0-6: No schema promotion without validation output. Schemas must pass
        structural validation (e.g., jsonschema validation against fixtures)
        before promotion from draft to candidate.
```
