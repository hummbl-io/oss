# HUMMBL Primitive Expansion v0.1 — HUAOMP x MTSMU Analysis

> **⚠️ HISTORICAL RESEARCH ARTIFACT.** This document was the analysis that proposed P27-P40 and K9-K11/D6-D7. It reflects the codebase state as of 2026-06-25 (8 kernel invariants, 5 doctrine invariants, proposed primitives not yet implemented). It has been **superseded by `PRIMITIVES.md` v1.2.0** for current implementation status. Do not use this file as current primitive-state authority. The analysis content remains valid as research background; the implementation claims are stale.

**Status:** DRAFT_RESEARCH_ARTIFACT
**Promotion posture:** ADAPT_REQUIRED
**Canonical status:** NOT_CANON
**Origin:** HUAOMP 6-lens analysis + MTSMU evidence-first rigor, 2026-06-25
**Steward:** HUMMBL Research Institute
**Validated scope:** analysis grounded in live codebase evidence (48 modules, 87 exports, 8 kernel invariants, 5 doctrine invariants, 20 Set Grammar object types, 5 schema files) — **as of 2026-06-25; see `PRIMITIVES.md` v1.2.0 for current state (K1-K11, D1-D7, 8 implemented expansion primitives)**
**Unvalidated scope:** proposed primitives were candidates only at time of writing — 8 have since been implemented (P27-P31, P34, P36, P38); see `PRIMITIVES.md` v1.2.0
**Companion artifacts:** `ai-framework-taxonomy-v0.1.md`, `ai-governance-framework-inventory.md`, **`PRIMITIVES.md` v1.2.0 (canonical implementation status)**

---

## Verification Checklist (before promotion)

- [x] Current primitive set audited from live codebase (48 modules, 87 exports)
- [x] Kernel invariants (K1-K8) and doctrine invariants (D1-D5) read from source
- [x] Set Grammar object types (20) read from object-envelope schema
- [x] Existing gaps identified from codebase (CanonRegistry, dispute resolution, succession, rollback, archive)
- [x] HUAOMP 6-lens analysis completed
- [ ] New primitive candidates reviewed by operator
- [ ] Invariant and variant tables validated against primitive implementations
- [ ] Proposed primitives scoped for implementation priority
- [ ] Schema candidates drafted for new primitives

---

## Evidence base

### Current primitive inventory (from live codebase)

| Layer | Count | Examples |
|---|---|---|
| **Main package modules** | 31 | kill_switch, circuit_breaker, capability_fence, cost_governor, identity, delegation, audit_log, compliance_mapper, stride_mapper, reasoning, contract_net, schema_validator, coordination_bus, lamport_clock, convergence_guard, reward_monitor, health_probe, lifecycle, physical_governor, eal, errors, failure_modes, evolution_lineage, output_validator, corpus_adapter, benchmark, statistical_framework, reasoning, _types, seed_registry |
| **Kernel modules** | 17 | kernel, invariants, receipt_engine, law_engine, identity_engine, sequence_engine, evidence_engine, authority_engine, doctrine_engine, schedule_engine, admission_control, model_registry, model_registry_cli, training_receipt, cli, __main__, __init__ |
| **Public exports** | 87 | (see __init__.py) |
| **Schema files** | 5 | admission_control, compat_report, evidence_readiness_review_receipt, receipt, validation_report |
| **Set Grammar object types** | 20 | ClaimSet, EvidenceSet, DecisionLedger, GateSet, ReceiptBundle, ProblemGraph, ProblemConstellation, QuestionSet, ContextPack, AssumptionSet, TaskSet, PromptPack, EvalSuite, RiskRegister, ArtifactRegistry, UncertaintyMap, OntologySet, AgentRegistry, CapabilityRegistry, CanonRegistry |

### Existing invariants (from source code)

**Kernel invariants (K1-K8)** — `hummbl_governance/kernel/invariants.py`:

| ID | Name | Invariant |
|---|---|---|
| K1 | RECEIPT | Every action that affects shared state produces a structured, signed receipt |
| K2 | LAW | Every receipt is evaluated against at least one scaling law |
| K3 | IDENTITY | Every agent has a single canonical identity, trust tier, and capability vector |
| K4 | TEMPORAL | Every receipt has a sequence_id for total ordering within its agent context |
| K5 | EVIDENCE | Every claim in a receipt is graded or marked speculative |
| K6 | AUTHORITY | Every authority exercise is scoped, limited, and leaves a receipt |
| K7 | ROLE | Every role is a runtime claim, not a static assignment |
| K8 | DOCTRINE | Every fleet artifact respects the doctrine invariants D1-D5 |

**Doctrine invariants (D1-D5)** — `hummbl_governance/kernel/doctrine_engine.py`:

| ID | Name | Invariant |
|---|---|---|
| D1 | ZERO_TRUST | Playground is zero-trust: no playground artifact influences fleet state without passing the Seed gate |
| D2 | FALSIFIABILITY | A hypothesis without a falsifier is not a seed. It is philosophy. |
| D3 | NO_INHERITED_AUTHORITY | Credibility is earned per artifact, not borrowed from lineage |
| D4 | DIVERGENCE_CONTAINED | Novelty generation must not destabilize convergent operations |
| D5 | NO_AUTO_PROMOTION | No stage promotes itself. Every gate requires operator approval |

**Problem Grammar invariants** — `docs/ecosystem/HUMMBL_PROBLEM_GRAMMAR.md`:

1. Agents cannot self-approve consequential work
2. Evidence precedes conclusion
3. Append-only logs are immutable
4. Missing tools degrade to SKIPPED, not FAIL
5. Secrets live in env vars, never in code
6. Contracts are canonical — breaking changes require SemVer major
7. Zero third-party runtime deps in core primitives

### Identified gaps (from codebase evidence)

| Gap | Source | Priority |
|---|---|---|
| CanonRegistry | ai-framework-taxonomy-v0.1.md:686 | HIGH |
| Dispute Resolution | government-corpus/README.md:11 | MEDIUM |
| Succession | government-corpus/README.md:11 | MEDIUM |
| Distributed Identity | DOCTRINE.md:73 | MEDIUM |
| Revocation Cascades | DOCTRINE.md:81 | MEDIUM |
| Rollback | HUMMBL_PROBLEM_GRAMMAR.md:254 | MEDIUM |
| Archive Management | Multiple docs | LOW |
| Memory Registries | MEMORY_SYSTEM_REGISTRY.md | LOW (blocked) |

---

## HUAOMP Spec | "Expand HUMMBL primitives, invariants, and variants of invariants"

**Intent:** Use HUAOMP's 6 lenses to surface new primitive candidates, identify invariants for each, and define context-dependent variants — all grounded in live codebase evidence with MTSMU confidence scoring.

### H (Holistic) — Trace feedback loops, find leverage points

**Findings:**

1. **Broken feedback loop at CanonRegistry.** The governance loop is: admission -> authority -> execution -> receipt -> evidence -> (promotion). The promotion step is broken — receipts accumulate but no primitive promotes from draft to canon. `evolution_lineage` tracks lineage but doesn't promote. The object-envelope has `canon_level` but no runtime enforcer. This is the highest leverage point: closing this loop makes the entire governance cycle self-completing.
   - **Spec constraint:** A CanonRegistry primitive must close the promotion loop: draft -> reviewed -> validated -> adopted -> canonical, with operator approval at each transition (per D5).

2. **Open feedback loop: compliance findings do not adjust trust tiers.** `compliance_mapper` produces findings, `audit_log` stores them, but no primitive feeds compliance results back into `identity` trust tier adjustments. An agent that repeatedly violates controls keeps its trust tier. The loop is open.
   - **Spec constraint:** A TrustAdjuster mechanism (primitive or wiring) must close the compliance-to-identity loop: repeated violations reduce trust tier; sustained compliance increases it.

3. **Missing recovery verification loop.** `kill_switch` halts, `circuit_breaker` opens, `health_probe` checks — but no primitive verifies that recovery is safe before re-engagement. The loop: halt -> fix -> ??? -> re-engage. The "???" is unguarded.
   - **Spec constraint:** A RecoveryVerifier primitive must gate re-engagement after any halt: verify root cause is addressed, evidence is collected, and operator approves re-engagement.

**Blind spots caught:** Without the holistic lens, each primitive looks sufficient in isolation. The gaps only appear when tracing the full feedback loop.

**Base120:** SY1 (Leverage Points), RE2 (Feedback Loops), SY6 (Feedback Structure Mapping)

---

### U (Universal) — Extract context-free invariants

**Findings:**

1. **Reversibility is a universal governance invariant.** Every governed action must be reversible or explicitly marked irreversible with accepted residual risk. Currently no primitive enforces this. `kill_switch` can halt but not undo. `circuit_breaker` can open but not rollback. The Problem Grammar mentions Rollback as required for governable action but no runtime primitive implements it.
   - **Spec constraint:** A Rollback primitive must exist: every governed action declares a rollback path or is explicitly marked irreversible with a recorded risk acceptance.

2. **Every authority grant must expire or be renewed.** Delegation tokens have expiry, but there's no sweep primitive that revokes expired grants or forces renewal. Expired tokens may persist in practice.
   - **Spec constraint:** An AuthoritySweeper primitive must periodically sweep for expired authority grants, revoke them, and notify the grantee and grantor.

3. **Every governed entity has a lifecycle.** Admission, operation, retirement. The `lifecycle` primitive exists but is NIST AI RMF-specific (Govern/Map/Measure/Manage). A universal lifecycle primitive would be domain-agnostic: admit -> operate -> monitor -> change -> retire.
   - **Spec constraint:** The lifecycle primitive should be generalized beyond NIST AI RMF to a universal governed-entity lifecycle.

**Blind spots caught:** Without the universal lens, primitives look domain-specific (AI agent orchestration) rather than what they actually are: instances of universal governance patterns.

**Base120:** SY1 (Leverage Points), CO2 (Chunking), CO9 (Interface Contracts)

---

### A (Absolute) — Draw hard boundaries

**Findings:**

1. **What must NEVER happen: receipt deletion.** Append-only logs are immutable (Problem Grammar invariant 3). But no primitive detects receipt deletion or gap in receipt sequence. A compromised agent could delete receipts and no alarm would fire.
   - **Spec constraint:** A ReceiptIntegrityMonitor must detect gaps in receipt sequences (K4 violation), hash chain breaks, and missing receipts — and raise KernelPanic.

2. **What must NEVER happen: agent self-promotion to canon.** D5 says "no auto-promotion." But there's no primitive that enforces this at the canon level. An agent could set `canon_level: "binding"` on an object and no alarm would fire.
   - **Spec constraint:** CanonRegistry must enforce D5: no agent can promote an artifact to canonical status without operator approval.

3. **What must EVENTUALLY happen: every draft must be promoted or deprecated.** Currently drafts can persist indefinitely. No primitive enforces a maximum draft age or mandatory review cycle.
   - **Spec constraint:** A DraftSweeper primitive must track draft age and flag drafts exceeding a configurable maximum age for mandatory review (promote or deprecate).

**Blind spots caught:** Without the absolute lens, "should" and "must" blur. The absolute lens forces explicit never/eventually boundaries.

**Base120:** P1 (First Principles), IN7 (Boundary Testing), DE13 (FMEA)

---

### O (Omni) — Rotate through all perspectives

**Findings:**

1. **Attacker perspective: retroactive receipt insertion.** `lamport_clock` provides ordering, but no primitive detects retroactive insertion of receipts with backdated timestamps. An attacker could insert a receipt "in the past" to justify an action.
   - **Spec constraint:** A TimelineIntegrityMonitor must detect receipts with timestamps inconsistent with their sequence_id position in the hash chain.

2. **Affected party perspective: no contestability primitive.** When an AI system makes a decision affecting a person, that person has no primitive-level mechanism to contest the decision. The taxonomy identifies contestability as a control surface (family 21), but no primitive implements it.
   - **Spec constraint:** A Contestability primitive must allow affected parties to flag a decision for human review, suspending the decision's effects until review completes.

3. **Regulator perspective: no regulator-facing export primitive.** `compliance_mapper` maps controls, but there's no primitive that produces a regulator-ready evidence export (audit packet, technical file, incident report) in a standard format.
   - **Spec constraint:** A RegulatorExport primitive must produce compliance evidence in regulator-accepted formats (e.g., EU AI Act technical file, SOC 2 audit packet).

**Blind spots caught:** Without the omni lens, the primitive set is agent-and-operator centric. The attacker, affected party, and regulator perspectives reveal entirely missing control surfaces.

**Base120:** P2 (Stakeholder Mapping), P7 (Perspective Switching), IN10 (Red Teaming)

---

### M (Meta) — Step up one abstraction level

**Findings:**

1. **The primitive set is "governance as enforcement."** Most primitives enforce rules (kill_switch, capability_fence, output_validator). Only `contract_net` hints at "governance as negotiation." The missing paradigm is "governance as ecology" — managing relationships between governed entities, not just individual agents.
   - **Spec constraint:** Consider a Treaty primitive for inter-agent agreements: multi-agent contracts with shared authority, mutual obligations, and dispute resolution.

2. **Who governs the governors?** K1-K8 govern agent actions. D1-D5 govern fleet artifacts. But who governs changes to K1-K8 and D1-D5? There's no primitive for doctrine amendment. This is an infinite regress that needs a bounded answer: operator authority + receipt + review.
   - **Spec constraint:** A DoctrineAmendment primitive must govern changes to invariants themselves: proposed change -> operator review -> evidence -> receipt -> promotion. This is meta-governance.

3. **The library split question.** DOCTRINE.md asks: "As the primitive count grows beyond 26, should the library split into core-governance and domain-specific extensions?" The answer from the meta lens: yes, but the split should be along the control-layer stack (L-1 through L10), not along primitive categories. Core = L-1 Admission + L3 Governance + L10 Receipts. Extensions = L8 Security, L7 Engineering, L15 Safety, etc.
   - **Spec constraint:** Plan library split along control-layer boundaries, not category boundaries. Core package = admission + authority + receipt + identity + evidence. Extension packages = security, safety, physical, compliance, reasoning.

**Blind spots caught:** Without the meta lens, the primitive set grows horizontally (more primitives of the same kind) instead of vertically (new abstraction levels).

**Base120:** P4 (Lens Shifting), P10 (Context Windowing), RE2 (Feedback Loops)

---

### P (Paradigmatic) — Name the paradigm, imagine alternatives

**Findings:**

1. **Current paradigm: governance as enforcement.** Primitives enforce rules, detect violations, and halt bad behavior. This is necessary but insufficient.
2. **Alternative paradigm: governance as evolution.** Primitives would track and guide system evolution over time. `evolution_lineage` hints at this but is narrow (variant tracking). A full "governance as evolution" paradigm would need: fitness functions for governance patterns, selection pressure toward safer patterns, and mutation tracking for governance rule changes.
   - **Spec constraint:** Consider a GovernanceFitness primitive that evaluates the effectiveness of governance patterns over time, not just their compliance.
3. **Alternative paradigm: governance as ecology.** Primitives would manage inter-agent relationships: resource sharing, conflict resolution, collective decision-making, boundary negotiation. The `contract_net` primitive is the seed of this paradigm.
   - **Spec constraint:** Consider ecological primitives: Treaty (inter-agent agreements), DisputeResolution (conflict resolution), ResourceArbitration (shared resource allocation).
4. **What would make this approach obsolete?** Hardware-level governance encoded in AI chips. Not imminent. The software governance paradigm holds.
   - **Spec constraint:** No action needed — but monitor for hardware-level governance developments.

**Blind spots caught:** Without the paradigmatic lens, the primitive set ossifies around one paradigm (enforcement) and misses entire control surfaces (evolution, ecology).

**Base120:** P15 (Assumption Surfacing), IN1 (Subtractive Thinking), IN3 (Problem Reversal)

---

## Generated spec: new primitive candidates

### Tier 1: Close existing feedback loops (HIGH priority)

| # | Primitive | Lens | Invariant it enforces | Confidence | Evidence |
|---|---|---|---|---|---|
| P27 | **CanonRegistry** | H, A | D5 (no auto-promotion) | 0.9 | Explicitly flagged in taxonomy crosswalk; object-envelope has CanonRegistry type but no runtime primitive |
| P28 | **Rollback** | U, A | "Every governed action is reversible or explicitly marked irreversible" | 0.8 | Problem Grammar lists Rollback as required for governable action; no runtime implementation |
| P29 | **RecoveryVerifier** | H | "Re-engagement requires root-cause verification + operator approval" | 0.7 | kill_switch/circuit_breaker can halt but no primitive gates re-engagement |
| P30 | **ReceiptIntegrityMonitor** | A, O | K1/K4 (receipt integrity + temporal ordering) | 0.8 | No primitive detects receipt gaps, hash chain breaks, or retroactive insertion |

### Tier 2: New control surfaces from missing perspectives (MEDIUM priority)

| # | Primitive | Lens | Invariant it enforces | Confidence | Evidence |
|---|---|---|---|---|---|
| P31 | **Contestability** | O | "Affected parties can flag decisions for human review" | 0.6 | Taxonomy family 21 identifies contestability; no primitive implements it |
| P32 | **DisputeResolution** | M, P | "Inter-agent conflicts have a resolution path" | 0.6 | Government corpus doctrine lists dispute resolution as primitive to extract |
| P33 | **Succession** | M, P | "Authority transfer is governed" | 0.6 | Government corpus doctrine lists succession as primitive to extract |
| P34 | **AuthoritySweeper** | U | "Every authority grant expires or is renewed" | 0.7 | Delegation tokens have expiry but no sweep mechanism enforces revocation |
| P35 | **RegulatorExport** | O | "Regulator-facing evidence is producible in standard formats" | 0.6 | compliance_mapper maps controls but produces no regulator-ready export |
| P36 | **TrustAdjuster** | H | "Compliance findings adjust trust tiers" | 0.7 | compliance_mapper produces findings; identity has trust tiers; no wiring between them |

### Tier 3: Paradigmatic expansion (LOWER priority, research-grade)

| # | Primitive | Lens | Invariant it enforces | Confidence | Evidence |
|---|---|---|---|---|---|
| P37 | **Treaty** | M, P | "Inter-agent agreements are governed" | 0.4 | contract_net is the seed; ecological paradigm needs multi-agent agreement primitive |
| P38 | **DoctrineAmendment** | M | "Invariant changes are governed" | 0.5 | No primitive governs changes to K1-K8 or D1-D5; infinite regress needs bounded answer |
| P39 | **GovernanceFitness** | P | "Governance patterns are evaluated for effectiveness" | 0.4 | Evolution paradigm needs fitness functions for governance, not just compliance |
| P40 | **DraftSweeper** | A | "Every draft is eventually promoted or deprecated" | 0.6 | No primitive enforces maximum draft age or mandatory review cycle |

---

## Invariants and variants for existing primitives

### Format

For each existing primitive:
- **Invariant:** the unbreakable rule it enforces
- **Variants:** context-dependent forms of the invariant (same rule, different manifestation)

### Safety primitives

#### kill_switch (KILL)

| | |
|---|---|
| **Invariant** | Any agent or operator can halt AI activity in graduated steps (DISENGAGED -> HALT_NONCRITICAL -> HALT_ALL -> EMERGENCY) |
| **Variant: partial** | Halt only non-critical agents, preserve critical infrastructure |
| **Variant: scoped** | Halt only agents in a specific trust tier or capability domain |
| **Variant: temporal** | Halt for a fixed duration, then auto-re-engage (with RecoveryVerifier gate) |
| **Variant: cascading** | Halt propagates to dependent agents (agent A halted -> agents depending on A also halt) |
| **Confidence** | 0.95 — directly verified from source (`kill_switch.py`, 4 modes confirmed) |

#### circuit_breaker (CB)

| | |
|---|---|
| **Invariant** | Repeated failures trigger automatic disconnection from an external dependency (CLOSED -> HALF_OPEN -> OPEN) |
| **Variant: threshold** | Break after N failures in window T |
| **Variant: latency** | Break after response time exceeds threshold L |
| **Variant: error-rate** | Break after error rate exceeds ratio R |
| **Variant: cascading** | Break in one breaker triggers dependent breakers (circuit cascade) |
| **Variant: half-open probe** | Allow one test request through before full re-engagement |
| **Confidence** | 0.95 — directly verified from source (`circuit_breaker.py`, 3 states confirmed) |

#### output_validator (OV)

| | |
|---|---|
| **Invariant** | Agent outputs are validated against content rules before release |
| **Variant: PII** | Detect and block personally identifiable information |
| **Variant: injection** | Detect prompt injection in outputs |
| **Variant: length** | Enforce minimum/maximum output length |
| **Variant: blocklist** | Block outputs containing blocklisted terms |
| **Variant: schema** | Validate output structure against JSON schema |
| **Confidence** | 0.9 — verified from source (`output_validator.py`, PIIDetector + InjectionDetector + LengthBounds + BlocklistFilter) |

#### capability_fence (CF)

| | |
|---|---|
| **Invariant** | An agent cannot access capabilities not granted by its delegation token |
| **Variant: tool-level** | Fence at tool granularity (can call tool X, cannot call tool Y) |
| **Variant: parameter-level** | Fence at parameter granularity (can call tool X with param A, not with param B) |
| **Variant: time-bounded** | Capability expires after duration D |
| **Variant: rate-limited** | Capability limited to N calls per window T |
| **Confidence** | 0.9 — verified from source (`capability_fence.py`, extends delegation tokens) |

### Cost & Budget

#### cost_governor (CG)

| | |
|---|---|
| **Invariant** | API spend cannot exceed the hard cap without triggering halt |
| **Variant: per-agent** | Each agent has its own budget |
| **Variant: per-service** | Each external service has its own budget |
| **Variant: per-task** | Each task has a budget allocation |
| **Variant: soft-warn** | Soft cap triggers warning but not halt |
| **Variant: rolling-window** | Budget resets on rolling window (daily, weekly, monthly) |
| **Confidence** | 0.9 — verified from source (`cost_governor.py`, SQLite-backed, soft/hard caps) |

### Identity & Auth

#### identity (ID)

| | |
|---|---|
| **Invariant** | Every agent has a single canonical identity with a trust tier and capability vector (K3) |
| **Variant: human** | Human operators have identity with elevated trust tier |
| **Variant: service** | Service accounts have identity with scoped capabilities |
| **Variant: ephemeral** | Short-lived agents have ephemeral identity with auto-expiry |
| **Variant: federated** | Identity federated across multiple systems (open question per DOCTRINE.md) |
| **Confidence** | 0.95 — verified from source (`identity.py`, AgentRegistry with trust tiers) |

#### delegation (DEL)

| | |
|---|---|
| **Invariant** | Authority delegation is cryptographically signed, scoped, and time-limited (K6) |
| **Variant: chain** | Delegatee can further delegate (with reduced scope and shorter expiry) |
| **Variant: revocable** | Grantor can revoke delegation before expiry (open question: cascade revocation) |
| **Variant: conditional** | Delegation valid only under condition C (e.g., "only during business hours") |
| **Variant: scoped** | Delegation limited to specific action type or resource |
| **Confidence** | 0.9 — verified from source (`delegation.py`, HMAC-SHA256, scope/expiry/chain-depth) |

### Audit & Compliance

#### audit_log (AL)

| | |
|---|---|
| **Invariant** | All governance events are recorded in an append-only log (K1) |
| **Variant: daily-rotation** | Log files rotate daily |
| **Variant: signed** | Each entry is cryptographically signed |
| **Variant: chained** | Entries are hash-chained for tamper detection |
| **Variant: indexed** | Entries indexed by agent, action type, timestamp for query |
| **Confidence** | 0.95 — verified from source (`audit_log.py`, append-only JSONL, daily rotation) |

#### compliance_mapper (CM)

| | |
|---|---|
| **Invariant** | Governance traces can be mapped to standard compliance frameworks |
| **Variant: NIST AI RMF** | Map to Govern/Map/Measure/Manage |
| **Variant: SOC 2** | Map to trust service criteria |
| **Variant: ISO 27001** | Map to ISO controls |
| **Variant: EU AI Act** | Map to risk classifications |
| **Confidence** | 0.85 — verified from source (`compliance_mapper.py`, parses bus JSONL) |

#### stride_mapper (SM)

| | |
|---|---|
| **Invariant** | Agent interactions can be decomposed into STRIDE threat categories |
| **Variant: Spoofing** | Identity spoofing detection |
| **Variant: Tampering** | Data tampering detection |
| **Variant: Repudiation** | Action repudiation detection |
| **Variant: Info Disclosure** | Information disclosure detection |
| **Variant: DoS** | Denial of service detection |
| **Variant: Elevation** | Privilege escalation detection |
| **Confidence** | 0.85 — verified from source (`stride_mapper.py`, 6 STRIDE categories) |

### Coordination

#### coordination_bus (BUS)

| | |
|---|---|
| **Invariant** | Agent coordination messages are append-only, ordered, and policy-leveled |
| **Variant: TSV** | Tab-separated format with flock-based locking |
| **Variant: HMAC-signed** | Messages signed with HMAC for integrity |
| **Variant: policy-leveled** | Messages classified by policy level (PUBLIC, INTERNAL, CONFIDENTIAL) |
| **Variant: broadcast** | Messages to `all` agents |
| **Variant: targeted** | Messages to specific agent |
| **Confidence** | 0.95 — verified from source (`coordination_bus.py`, TSV + flock + HMAC) |

#### lamport_clock (LC)

| | |
|---|---|
| **Invariant** | Events are totally ordered within an agent context (K4) |
| **Variant: per-agent** | Each agent has its own logical clock |
| **Variant: cross-agent** | Clocks synchronize on message exchange |
| **Variant: vector** | Vector clock for partial ordering across agents |
| **Confidence** | 0.9 — verified from source (`lamport_clock.py`) |

#### contract_net (CN)

| | |
|---|---|
| **Invariant** | Task allocation follows market-based bidding (announce -> bid -> award -> execute) |
| **Variant: sealed-bid** | Bids are hidden until deadline |
| **Variant: open-bid** | Bids are visible to all agents |
| **Variant: iterative** | Multiple rounds of bidding |
| **Variant: constrained** | Only agents with specific capabilities may bid |
| **Confidence** | 0.85 — verified from source (`contract_net.py`, Smith 1980 protocol) |

#### convergence_guard (CVG)

| | |
|---|---|
| **Invariant** | Instrumental convergence in agent behavior is detected and flagged |
| **Variant: goal-convergence** | Detect agents converging on same instrumental goal |
| **Variant: resource-convergence** | Detect agents competing for same resource |
| **Variant: behavior-convergence** | Detect agents adopting same behavior pattern |
| **Confidence** | 0.8 — verified from source (`convergence_guard.py`) |

### Behavior & Health

#### reward_monitor (RM)

| | |
|---|---|
| **Invariant** | Reward hacking and specification gaming are detected |
| **Variant: drift** | Detect behavioral drift from expected reward patterns |
| **Variant: gaming** | Detect specification gaming (reward without task completion) |
| **Variant: hacking** | Detect direct reward channel manipulation |
| **Confidence** | 0.8 — verified from source (`reward_monitor.py`, Leike et al. 2018) |

#### health_probe (HP)

| | |
|---|---|
| **Invariant** | System health is continuously checkable via probes |
| **Variant: liveness** | Is the system running? |
| **Variant: readiness** | Is the system ready to accept work? |
| **Variant: dependency** | Are external dependencies reachable? |
| **Variant: custom** | Custom probes for domain-specific health |
| **Confidence** | 0.9 — verified from source (`health_probe.py`, generic probe framework) |

#### lifecycle (LCY)

| | |
|---|---|
| **Invariant** | AI system lifecycle follows defined phases with gates between them |
| **Variant: NIST AI RMF** | Govern -> Map -> Measure -> Manage |
| **Variant: admission-first** | Admit -> Design -> Build -> Test -> Deploy -> Monitor -> Change -> Incident -> Retire |
| **Variant: continuous** | Lifecycle is continuous, not waterfall (phases repeat) |
| **Confidence** | 0.85 — verified from source (`lifecycle.py`, NIST AI RMF orchestrator) |

### Reasoning & Validation

#### reasoning (RE)

| | |
|---|---|
| **Invariant** | Mental models can be applied to problem statements to produce structured analysis |
| **Variant: Base120** | Apply 120 mental models across 6 transformations |
| **Variant: single-model** | Apply one specific model |
| **Variant: chained** | Chain multiple models in sequence |
| **Confidence** | 0.8 — verified from source (`reasoning.py`, Base120 Reasoning Kernel) |

#### schema_validator (SV)

| | |
|---|---|
| **Invariant** | Data structures conform to declared JSON Schema (Draft 2020-12 subset) |
| **Variant: strict** | No additional properties allowed |
| **Variant: lenient** | Additional properties allowed |
| **Variant: conditional** | Validation depends on field values |
| **Confidence** | 0.95 — verified from source (`schema_validator.py`, stdlib-only) |

### Physical AI

#### physical_governor (PG)

| | |
|---|---|
| **Invariant** | Physical AI systems operate within kinematic and safety constraints |
| **Variant: pHRI** | Physical human-robot interaction safety |
| **Variant: kinematic** | Joint angle and velocity limits |
| **Variant: force** | Force and torque limits |
| **Variant: proximity** | Minimum distance to humans |
| **Confidence** | 0.8 — verified from source (`physical_governor.py`, KinematicGovernor + pHRISafetyMonitor) |

### Execution Assurance

#### eal (EAL)

| | |
|---|---|
| **Invariant** | Execution Assurance Level is deterministically verifiable |
| **Variant: validate** | Validate conformance to contract |
| **Variant: revalidate** | Re-validate after change |
| **Variant: compat** | Check backward compatibility between contracts |
| **Confidence** | 0.85 — verified from source (`eal.py`, deterministic evaluators) |

### Error Taxonomy

#### errors (ERR)

| | |
|---|---|
| **Invariant** | All errors are classified into a unified taxonomy |
| **Variant: governance** | Errors from governance primitive violations |
| **Variant: operational** | Errors from operational failures |
| **Variant: external** | Errors from external dependencies |
| **Confidence** | 0.85 — verified from source (`errors.py`, 3-layer taxonomy) |

#### failure_modes (FM)

| | |
|---|---|
| **Invariant** | All failure modes are registered and classifiable |
| **Variant: known** | Registered failure modes with mitigation |
| **Variant: novel** | Unregistered failure modes requiring analysis |
| **Variant: cascading** | Failure modes that trigger other failure modes |
| **Confidence** | 0.8 — verified from source (`failure_modes.py`, fm.json registry) |

#### evolution_lineage (EL)

| | |
|---|---|
| **Invariant** | Variant ancestry and self-modification records are tracked |
| **Variant: parent-child** | Track parent-to-child variant relationships |
| **Variant: fitness** | Track fitness changes across generations |
| **Variant: drift** | Detect drift from original specification |
| **Confidence** | 0.8 — verified from source (`evolution_lineage.py`) |

### Kernel primitives

#### admission_control (AC)

| | |
|---|---|
| **Invariant** | Admission is governed permission for state transition under authority, executor, scope, evidence, and receipt |
| **Variant: use-case** | Admit a new AI use case |
| **Variant: model** | Admit a new model for deployment |
| **Variant: agent** | Admit a new agent to the fleet |
| **Variant: tool** | Admit a new tool for agent use |
| **Variant: data** | Admit a new dataset for training/inference |
| **Variant: memory** | Admit a new memory entry |
| **Variant: state-transition** | Admit a durable state transition |
| **Confidence** | 0.9 — verified from source (`kernel/admission_control.py`, 5 gates) |

#### receipt_engine (RE)

| | |
|---|---|
| **Invariant** | Every action affecting shared state produces a structured, signed, hash-chained receipt (K1) |
| **Variant: agent-scoped** | Receipts stored per-agent |
| **Variant: chained** | SHA-256 hash chain for tamper detection |
| **Variant: signed** | Cryptographic signature per receipt |
| **Confidence** | 0.95 — verified from source (`kernel/receipt_engine.py`) |

#### authority_engine (AE)

| | |
|---|---|
| **Invariant** | Every authority exercise is scoped, limited, and leaves a receipt (K6) |
| **Variant: scoped** | Authority limited to specific scope |
| **Variant: time-limited** | Authority expires after duration |
| **Variant: delegated** | Authority delegated from another authority |
| **Confidence** | 0.9 — verified from source (`kernel/authority_engine.py`) |

---

## Proposed new invariants

### K9: REVERSIBILITY

> Every governed action declares a rollback path or is explicitly marked irreversible with a recorded risk acceptance.

**Source lens:** Universal (U), Absolute (A)
**Enforcing primitive:** P28 Rollback
**Confidence:** 0.8 — derived from Problem Grammar invariant + universal governance pattern

### K10: RECOVERY

> Re-engagement after halt requires root-cause verification, evidence collection, and operator approval.

**Source lens:** Holistic (H)
**Enforcing primitive:** P29 RecoveryVerifier
**Confidence:** 0.7 — derived from feedback loop analysis

### K11: INTEGRITY

> Receipt sequences are complete and unbroken. Gaps, hash chain breaks, and retroactive insertions are detected and raise KernelPanic.

**Source lens:** Absolute (A), Omni (O)
**Enforcing primitive:** P30 ReceiptIntegrityMonitor
**Confidence:** 0.8 — derived from K1/K4 enforcement gap

### D6: CONTESTABILITY

> Affected parties can flag AI-mediated decisions for human review, suspending the decision's effects until review completes.

**Source lens:** Omni (O)
**Enforcing primitive:** P31 Contestability
**Confidence:** 0.6 — derived from affected-party perspective

### D7: DOCTRINE_AMENDMENT

> Changes to invariants themselves are governed: proposed change -> operator review -> evidence -> receipt -> promotion.

**Source lens:** Meta (M)
**Enforcing primitive:** P38 DoctrineAmendment
**Confidence:** 0.5 — derived from infinite regress analysis

---

## Variant patterns across invariants

### Pattern 1: Scope variants

Most invariants have a scope dimension: the invariant applies at a specific granularity.

| Invariant | Global | Per-agent | Per-task | Per-resource |
|---|---|---|---|---|
| K1 (Receipt) | All shared state | Agent's receipts | Task's receipts | Resource access receipts |
| K6 (Authority) | All authority | Agent's authority | Task-scoped authority | Resource-specific authority |
| K9 (Reversibility) | All actions | Agent's actions | Task's actions | Resource mutations |

### Pattern 2: Temporal variants

Most invariants have a temporal dimension: the invariant applies at a specific time scale.

| Invariant | Immediate | Window | Lifecycle | Eternal |
|---|---|---|---|---|
| K1 (Receipt) | Receipt at action time | Receipts within window | All receipts for lifecycle | Immutable receipt history |
| K6 (Authority) | Authority at exercise time | Authority within window | Authority for lifecycle | Authority record persists |
| K10 (Recovery) | Verify before re-engage | Verify within window | Verify across lifecycle | Recovery record persists |

### Pattern 3: Severity variants

Most invariants have a severity dimension: violations can be handled at different severity levels.

| Invariant | Warning | Halt | Quarantine | Panic |
|---|---|---|---|---|
| K1 (Receipt) | Missing receipt logged | Agent halted | Agent quarantined | KernelPanic |
| K11 (Integrity) | Gap detected | Agent halted | Agent quarantined | KernelPanic |
| D6 (Contestability) | Decision flagged | Decision suspended | Decision reversed | Operator review required |

---

## MTSMU confidence summary

| Claim | Confidence | Evidence basis |
|---|---|---|
| 48 modules exist in codebase | 0.95 | Direct file listing |
| 87 public exports | 0.95 | __init__.py read |
| 8 kernel invariants (K1-K8) | 0.95 | invariants.py read |
| 5 doctrine invariants (D1-D5) | 0.95 | doctrine_engine.py read |
| 20 Set Grammar object types | 0.95 | object-envelope schema read |
| CanonRegistry is a gap | 0.9 | Taxonomy crosswalk + object-envelope has type but no primitive |
| Rollback is missing as runtime primitive | 0.8 | Problem Grammar lists it; no implementation found |
| Recovery verification is missing | 0.7 | Inferred from feedback loop analysis; no primitive found |
| Receipt integrity monitoring is missing | 0.8 | No primitive detects gaps or chain breaks |
| Contestability is missing | 0.6 | Taxonomy identifies it; no primitive; lower confidence on universal need |
| Dispute resolution is missing | 0.6 | Government corpus mentions it; no primitive |
| Succession is missing | 0.6 | Government corpus mentions it; no primitive |
| Library should split along control layers | 0.5 | Meta-lens inference; architectural recommendation |
| Governance-as-ecology paradigm is valuable | 0.4 | Paradigmatic lens; speculative; needs validation |

---

## Open questions requiring human judgment

1. **Should CanonRegistry be a standalone primitive or a kernel engine?** The object-envelope has it as a type, but enforcement could be in the kernel (like doctrine_engine) or as a standalone module (like audit_log).
2. **Should Rollback be a primitive or a contract requirement?** Every action declaring a rollback path could be a schema field rather than a runtime primitive. The tradeoff: schema-only is simpler but unenforced.
3. **How many of the Tier 2/3 primitives should be in hummbl-governance vs. a future extension package?** The library split question from DOCTRINE.md is directly relevant.
4. **Should new invariants (K9-K11, D6-D7) be added to the enum or kept as doctrine-level guidance?** Adding to the enum means KernelPanic on violation; keeping as doctrine means softer enforcement.
5. **Is the GovernanceFitness paradigm (P39) worth pursuing now, or is it research-grade?** Confidence 0.4 — needs operator judgment on whether to invest.

---

## Receipt

```yaml
analysis_receipt:
  artifact: hummbl-primitive-expansion-v0.1.md
  method: HUAOMP 6-lens + MTSMU evidence-first
  evidence_source: live codebase (48 modules, 87 exports, 8+5 invariants, 20 object types)
  primitives_analyzed: 26 existing
  new_primitives_proposed: 14 (P27-P40)
  new_invariants_proposed: 5 (K9-K11, D6-D7)
  variant_patterns_identified: 3 (scope, temporal, severity)
  confidence_range: 0.4-0.95
  high_confidence_findings: 4 (>=0.9)
  medium_confidence_findings: 8 (0.6-0.89)
  speculative_findings: 2 (<0.6)
  date: 2026-06-25
  status: DRAFT_RESEARCH_ARTIFACT
```
