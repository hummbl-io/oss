# HUMMBL Governance Primitives — Complete Reference

**Version:** v1.4.1
**Existing primitives:** 26 (P1-P26)
**Implemented expansion primitives:** 10 (P27-P31, P34-P35, P36-P38) — schemas, modules, and tests
**Implemented post-v1.2 primitives:** 9 (P44-P52) — modules and tests, shipped v1.3-v1.4
**Proposed primitives:** 4 (P32-P33, P39-P40) — not yet started
**Total implemented:** 45 (P1-P26, P27-P31, P34-P35, P36-P38, P44-P52)
**Kernel invariants:** K1-K14 (K1-K8 enforced on every receipt path; K9-K11 enum-defined, schema-backed, tested, and exposed through Kernel validation methods; K12-K14 added 2026-09-02 for safety, convergence, and physical-AI safety — closing the primitive-invariant pairing gap)
**Doctrine invariants:** D1-D7 (D1-D5 enforced on every promotion path; D6 enforced via contestability primitive; D7 enforced via `assert_invariant_change_gated()` using multi-signal detection — see D7 enforcement note below)
**Severity tiers:** Each invariant has a default severity (CRITICAL → HIGH → MEDIUM → LOW) that determines the response on violation. See `Severity` enum in `kernel/invariants.py`.
**Family codes:** Each primitive has a two-letter family code (e.g., SF-1 for P1 KillSwitch) alongside its P-number. See Family Codes section below.
**Primitive registry:** Runtime-queryable inventory at `hummbl_governance.primitive_registry.PrimitiveRegistry`.

This document is the canonical reference for all HUMMBL governance primitives. For the research analysis behind the proposed primitives, see `docs/research/hummbl-primitive-expansion-v0.1.md` and `docs/research/hummbl-primitive-matrix-v0.1.md`.

---

## Invariants

### Kernel invariants (K1-K14) — enforced by `kernel/invariants.py`

| ID | Name | Invariant | Severity | Enforcing engine |
|---|---|---|---|---|
| K1 | RECEIPT | Every action that affects shared state produces a structured, signed receipt | CRITICAL | `ReceiptEngine` |
| K2 | LAW | Every receipt is evaluated against at least one scaling law | HIGH | `LawEngine` |
| K3 | IDENTITY | Every agent has a single canonical identity, trust tier, and capability vector | CRITICAL | `IdentityEngine` |
| K4 | TEMPORAL | Every receipt has a sequence_id for total ordering within its agent context | MEDIUM | `SequenceEngine` |
| K5 | EVIDENCE | Every claim in a receipt is graded or marked speculative | HIGH | `EvidenceEngine` |
| K6 | AUTHORITY | Every authority exercise is scoped, limited, and leaves a receipt | CRITICAL | `AuthorityEngine` |
| K7 | ROLE | Every role is a runtime claim, not a static assignment | MEDIUM | `IdentityEngine` |
| K8 | DOCTRINE | Every fleet artifact respects the doctrine invariants D1-D7 | HIGH | `DoctrineEngine` |
| K9 | REVERSIBILITY | Every governed durable-state mutation or irreversible external side effect declares a rollback path or is explicitly marked irreversible with a recorded risk acceptance | HIGH | `Kernel.validate_rollback()` → `rollback.py` |
| K10 | RECOVERY | Re-engagement after halt, quarantine, or open breaker requires root-cause verification, evidence collection, and operator approval | HIGH | `Kernel.validate_recovery()` → `recovery_verifier.py` |
| K11 | INTEGRITY | Receipt sequences are complete and unbroken. Sequence gaps and hash-chain breaks trigger KernelPanic | CRITICAL | `Kernel.check_receipt_integrity()` → `receipt_integrity_monitor.py` |
| K12 | SAFETY | Emergency halt and failure detection capabilities are always available and operational. Kill switch and circuit breaker must be reachable and responsive | MEDIUM | P1 `kill_switch`, P2 `circuit_breaker` |
| K13 | CONVERGENCE | Instrumental convergence patterns in agent behavior are detected and flagged. Agents that appear to optimize for unintended instrumental goals are identified before harm occurs | LOW | P16 `convergence_guard` |
| K14 | PHYSICAL_SAFETY | Physical-AI actions respect kinematic constraints and pHRI safety modes. Robot actions must stay within declared speed, force, and proximity limits | CRITICAL | P20 `physical_governor` |

### Doctrine invariants (D1-D7) — enforced by `kernel/doctrine_engine.py`

| ID | Name | Invariant |
|---|---|---|
| D1 | ZERO_TRUST | Playground is zero-trust: no playground artifact influences fleet state without passing the Seed gate |
| D2 | FALSIFIABILITY | A hypothesis without a falsifier is not a seed. It is philosophy. |
| D3 | NO_INHERITED_AUTHORITY | Credibility is earned per artifact, not borrowed from lineage |
| D4 | DIVERGENCE_CONTAINED | Novelty generation must not destabilize convergent operations |
| D5 | NO_AUTO_PROMOTION | No stage promotes itself. Every gate requires operator approval. |
| D6 | CONTESTABILITY | Affected parties can flag AI-mediated decisions for human review, suspending the decision's effects until review completes. Requires evidence or justification, not just a bare flag. |
| D7 | DOCTRINE_AMENDMENT | No invariant or doctrine amendment may take effect without operator approval and a recorded receipt. Ungated amendments are blocked. |

> **D7 enforcement note:** D7 enforcement in `DoctrineEngine.promote()` uses multi-signal detection (fixed 2026-09-02). The `_is_invariant_amendment()` method detects invariant amendments via three signals: (1) field-triggered (`amendment_type` present), (2) content-based (`target_invariant`, `invariant_change`, `invariant_id`, `doctrine_change`, `amended_invariant`, `amended_doctrine` fields), and (3) path-based (`target_path`/`file_path`/`path` matching invariant surface files like `invariants.py`, `doctrine_engine.py`, `doctrine_amendment.py`). This closes the previous bypassability gap where a malformed invariant-change artifact could skip the D7 gate by omitting `amendment_type`.

---

## Existing primitives (P1-P26)

### Governance Kernel (P25-P26)

| ID | Module | Description | Invariant enforced |
|---|---|---|---|
| P25 | `kernel/admission_control` | Bounded admission-control for governed permission of state transitions. 5 gates: authority, executor, scope, evidence, receipt | D5 (NO_AUTO_PROMOTION) |
| P26 | `kernel/receipt_engine` | SHA-256 hash-chained receipts with agent-scoped storage. Every action affecting shared state produces a signed receipt | K1 (RECEIPT) |

### Safety (P1-P4)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P1 | SF-1 | `kill_switch` | Emergency halt system with 4 graduated modes (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY) | K12 (SAFETY) | Containment |
| P2 | SF-2 | `circuit_breaker` | Automatic failure detection and recovery across 3 states (CLOSED, HALF_OPEN, OPEN) | K12 (SAFETY) | Containment |
| P3 | SF-3 | `output_validator` | Rule-based content validation: PII detection, injection detection, blocklists, length bounds | — (infrastructure) | Infrastructure |
| P4 | SF-4 | `capability_fence` | Soft sandbox enforcing capability boundaries per agent role. Extends delegation tokens | K6 (AUTHORITY) | Containment |

### Cost & Budget (P5)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P5 | CB-1 | `cost_governor` | Budget tracking with soft/hard caps and ALLOW/WARN/DENY decisions. SQLite-backed | K6 (AUTHORITY) | Containment |

### Identity & Auth (P6-P7)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P6 | IA-1 | `identity` | Agent registry with configurable aliases, trust tiers, and canonicalization | K3 (IDENTITY) | Authority |
| P7 | IA-2 | `delegation` | HMAC-SHA256 or Ed25519 signed capability tokens for agent delegation chains with scope, expiry, chain-depth | K6 (AUTHORITY) | Authority |

### Audit & Compliance (P8-P10)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P8 | AC-1 | `audit_log` | Append-only JSONL governance audit log with daily rotation and retention | K1 (RECEIPT) | Evidence |
| P9 | AC-2 | `compliance_mapper` | Map governance traces to SOC2, GDPR, NIST AI RMF, ISO 27001, ISO 42001 controls | — (infrastructure) | Infrastructure |
| P10 | AC-3 | `stride_mapper` | Map agent interactions to STRIDE threat categories with mitigation suggestions | — (infrastructure) | Infrastructure |

### Reasoning & Contract (P11-P13)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P11 | RC-1 | `reasoning` | Structured governance reasoning engine with rule application, conflict detection, and decision tracing. Base120 mental models | — (infrastructure) | Infrastructure |
| P12 | RC-2 | `contract_net` | Market-based task allocation protocol for multi-agent systems (Smith 1980) | — (infrastructure) | Infrastructure |
| P13 | RC-3 | `schema_validator` | Stdlib-only JSON Schema validator (Draft 2020-12 subset) | — (infrastructure) | Infrastructure |

### Coordination (P14-P16)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P14 | CO-1 | `coordination_bus` | Append-only TSV message bus with flock locking and HMAC signing | — (infrastructure) | Infrastructure |
| P15 | CO-2 | `lamport_clock` | Hardened logical clock for causal ordering of distributed agent events | K4 (TEMPORAL) | Evidence |
| P16 | CO-3 | `convergence_guard` | Detect instrumental convergence patterns in agent behavior | K13 (CONVERGENCE) | Containment |

### Behavior & Health (P17-P19)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P17 | BH-1 | `reward_monitor` | Behavioral drift and reward gaming detector (Leike et al. 2018) | D4 (DIVERGENCE_CONTAINED) | Containment |
| P18 | BH-2 | `health_probe` | Composable health probe framework with latency tracking | — (infrastructure) | Infrastructure |
| P19 | BH-3 | `lifecycle` | NIST AI RMF orchestrator composing kill switch, circuit breaker, cost governor, and audit log | — (infrastructure) | Infrastructure |

### Physical AI (P20)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P20 | PA-1 | `physical_governor` | Kinematic constraints and pHRI safety modes for physical-AI deployments | K14 (PHYSICAL_SAFETY) | Containment |

### Execution Assurance (P21)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P21 | EA-1 | `eal` | Execution Assurance Layer — Arbiter-verified code quality in execution receipts | — (evidence-layer) | Evidence |

### Error Taxonomy (P22-P24)

| ID | Family | Module | Description | Invariant enforced | Layer |
|---|---|---|---|---|---|
| P22 | ET-1 | `errors` | `HummblError`, `FailureMode`, and `fm_to_errors()` — typed error taxonomy (3 layers) | — (infrastructure) | Infrastructure |
| P23 | ET-2 | `failure_modes` | Structured failure mode catalog with classification and error cross-reference | — (infrastructure) | Infrastructure |
| P24 | ET-3 | `evolution_lineage` | In-memory lineage tracking for eAI variants with drift detection | — (infrastructure) | Infrastructure |

---

## Expansion primitives (P27-P40)

### Implemented (P27-P31, P34-P35, P36-P38)

| ID | Name | Description | Invariant | Module | Schema | Status |
|---|---|---|---|---|---|---|
| P27 | CanonRegistry | Governs promotion from draft to canonical status. 6 levels: draft, reviewed, validated, adopted, canonical, deprecated | D5 | `kernel/canon_registry.py` | `canon_registry.schema.json` | ✅ Implemented |
| P28 | Rollback | Enforces reversibility: every governed action declares a rollback path or is marked irreversible with risk acceptance | K9 | `kernel/rollback.py` | `rollback.schema.json` | ✅ Implemented; Kernel API exposed (mandatory at call sites that invoke `validate_rollback()`) |
| P29 | RecoveryVerifier | Gates re-engagement after halt with root-cause verification, evidence, and operator approval | K10 | `kernel/recovery_verifier.py` | `recovery_verifier.schema.json` | ✅ Implemented; Kernel API exposed (mandatory at call sites that invoke `validate_recovery()`) |
| P30 | ReceiptIntegrityMonitor | Detects receipt sequence gaps, hash chain breaks, retroactive insertion, and invalid signatures. Raises KernelPanic | K11 | `kernel/receipt_integrity_monitor.py` | `receipt_integrity_monitor.schema.json` | ✅ Implemented; Kernel API exposed (mandatory at call sites that invoke `check_receipt_integrity()`) |
| P31 | Contestability | Allows affected parties to flag AI-mediated decisions for human review, suspending effects until review completes | D6 | `kernel/contestability.py` | `contestability.schema.json` | ✅ Implemented |
| P34 | AuthoritySweeper | Provides callable sweep validation/build/run functions for expired authority grants. Finds expired grants, builds revocation records, validates them. No scheduler integration — callers must invoke `run_sweep()` periodically | K6 | `kernel/authority_sweeper.py` | `authority_sweeper.schema.json` | ✅ Implemented (callable, not scheduled) |
| P35 | RegulatorExport | Produces compliance evidence in regulator-accepted formats (EU AI Act technical file per Annex IV, EU declaration of conformity per Annex V, GPAI documentation per Annex XI, SOC 2 audit packet, ISO 42001 AIMS evidence, NIST AI RMF evidence package). Wraps ComplianceMapper reports with operator approval (D5), hash-chained integrity, and statutory boundary disclaimers. Closes GAP-E1 and partially GAP-E4 from the 2026-09-04 governance assessment | D5 | `regulator_export.py` | `regulator_export.schema.json` | ✅ Implemented (7 formats, 8 frameworks, 40 tests) |
| P36 | TrustAdjuster | Handles evidence-backed trust-tier reductions based on compliance violations. Severity maps to tier reduction (low=1, medium=2, high=3, critical=REVOKED). Only reduces tiers — promotions must go through IdentityEngine's promotion path | K3 | `kernel/trust_adjuster.py` | `trust_adjuster.schema.json` | ✅ Implemented (reduction only) |
| P37 | ApprovalManager | Human-in-the-loop approval gate with risk tiers (LOW/MEDIUM/HIGH/CRITICAL), notifications (webhook/Slack/email), persistence, expiration, background stale-request sweeper, audit integration. Repurposed from Treaty (commit 2e1ba7f) | D6 | `approval.py` | — | ✅ Implemented (repurposed from Treaty) |
| P38 | DoctrineAmendment | Governs changes to invariants themselves: proposed change -> operator review -> evidence -> receipt -> promotion | D7 | `kernel/doctrine_amendment.py` | `doctrine_amendment.schema.json` | ✅ Implemented; wired into `DoctrineEngine.promote()` (field-triggered on `amendment_type` — see D7 bypassability note) |

### Not yet started (P32-P33, P39-P40)

| ID | Name | Description | Invariant | Status |
|---|---|---|---|---|
| P32 | DisputeResolution | Inter-agent conflict resolution primitive (from government corpus doctrine) | — | Not started |
| P33 | Succession | Authority transfer primitive for governance continuity (from government corpus doctrine) | — | Not started |
| P39 | GovernanceFitness | Evaluates governance pattern effectiveness over time, not just compliance | — | Not started |
| P40 | DraftSweeper | Tracks draft age and flags drafts exceeding configurable maximum age for mandatory review | — | Not started |

### Candidates under consideration (P41-P43)

| ID | Name | Description | Source |
|---|---|---|---|
| P41 | Retirement | Governs decommissioning: verify no dependents, archive state, transfer authority, notify stakeholders | Matrix Part 2: Phi6 Retire gap |
| P42 | ConceptRegistry | Governs terminology: ensures terms in receipts/admissions have canonical definitions | Matrix Part 1: full-gap family 1 |
| P43 | RiskRegister | Dedicated risk-register primitive (family 9 is weak, only stride_mapper/failure_modes adjacent) | Matrix Part 1: weak-coverage family 9 |

### Implemented post-v1.2 (P44-P52)

These primitives shipped in v1.3-v1.4 but were not tracked in PRIMITIVES.md until this update. All have modules, tests, and are importable from the package root.

| ID | Name | Description | Module | Status |
|---|---|---|---|---|
| P44 | Attest | MCP server identity attestation and policy compliance verification | `attest.py` | ✅ Implemented |
| P45 | ContractEnforcement | Cross-repo contract enforcement layer — validates contract terms at runtime | `contract_enforcement.py` | ✅ Implemented |
| P46 | CrossRepoContract | Cross-repository contract validation standard (v0.1) | `cross_repo_contract.py` | ✅ Implemented |
| P47 | CorpusAdapter | Bridges hummbl-governance receipts to unified-framework corpus formats | `corpus_adapter.py` | ✅ Implemented |
| P48 | DelegationContext | Immutable delegation context with depth and scope attenuation — extends P7 Delegation | `delegation_context.py` | ✅ Implemented |
| P49 | SovereignCryptosystem | Hardened cryptographic sync router (GFSCR) envelope for sovereign key management | `sovereign_cryptosystem.py` | ✅ Implemented |
| P50 | MerkleAnchor | CT-style Merkle anchoring for governance tuple logs — signed tree heads with witness cosignature | `primitives/merkle_anchor.py` | ✅ Implemented |
| P51 | TransitionReceipt | Transition receipts for governed agent/tool execution — tracks tool handoff state | `transition_receipt.py` | ✅ Implemented |
| P52 | ToolAudit | Tool-call audit hook for AI agent integrations — records and validates tool invocations | `tool_audit.py` | ✅ Implemented |

---

## Primitive categories (P1-P52)

| Category | Existing | Implemented expansion | Post-v1.2 | Proposed | Total |
|---|---|---|---|---|---|
| Governance Kernel | 2 (P25, P26) | 4 (P27-P30) | 0 | 1 (P40) | 7 |
| Safety | 4 (P1-P4) | 0 | 0 | 0 | 4 |
| Cost & Budget | 1 (P5) | 0 | 0 | 0 | 1 |
| Identity & Auth | 2 (P6, P7) | 2 (P34, P36) | 1 (P48) | 0 | 5 |
| Audit & Compliance | 3 (P8-P10) | 1 (P35) | 2 (P51, P52) | 0 | 6 |
| Reasoning & Contract | 3 (P11-P13) | 0 | 2 (P45, P46) | 0 | 5 |
| Coordination | 3 (P14-P16) | 0 | 0 | 1 (P32) | 4 |
| Behavior & Health | 3 (P17-P19) | 0 | 0 | 1 (P39) | 4 |
| Physical AI | 1 (P20) | 0 | 0 | 0 | 1 |
| Execution Assurance | 1 (P21) | 0 | 1 (P50) | 0 | 2 |
| Error Taxonomy | 3 (P22-P24) | 0 | 0 | 0 | 3 |
| Governance Ecology | 0 | 3 (P31, P37, P38) | 0 | 1 (P33) | 4 |
| Cryptography | 0 | 0 | 2 (P44, P49) | 0 | 2 |
| Corpus Integration | 0 | 0 | 1 (P47) | 0 | 1 |
| **Total (P1-P52)** | **26** | **10** | **9** | **4** | **49** |

> **Note:** P37 (ApprovalManager, repurposed from Treaty) appears in the Governance Ecology category. Some primitives span multiple categories (e.g., P38 DoctrineAmendment is both Governance Ecology and Governance Kernel), but each primitive is counted once in its primary category. P44-P52 are post-v1.2 additions not counted in the original P1-P40 roadmap numbering.

### Candidates under consideration (P41-P43, not counted in P1-P52 total)

| Category | Candidates |
|---|---|
| Lifecycle Hygiene | 1 (P41) |
| Concept Layer | 1 (P42) |
| Risk Management | 1 (P43) |
| **Candidates total** | **3** |

---

## MCP Server exposure

| Server | Tools | Primitives exposed |
|---|---|---|
| `mcp_server` | 10 | KillSwitch, CircuitBreaker, CostGovernor, AuditLog, ComplianceMapper, HealthProbe |
| `mcp_compliance` | 5 | NIST AI RMF, SOC2, ISO crosswalk, STRIDE, evidence export |
| `mcp_sandbox` | 5 | CapabilityFence, OutputValidator |
| `mcp_identity` | 10 | AgentRegistry, DelegationTokenManager, LamportClock |
| `mcp_agent_monitor` | 11 | BehaviorMonitor, ConvergenceDetector, GovernanceLifecycle, EvolutionLineage |
| `mcp_reasoning` | 10 | ReasoningEngine, SchemaValidator, ContractNetManager |
| `mcp_physical` | 6 | KinematicGovernor, pHRISafetyMonitor |
| **Total** | **57** | — |

---

## See also

- `docs/research/hummbl-primitive-expansion-v0.1.md` — HUAOMP x MTSMU analysis proposing P27-P40
- `docs/research/hummbl-primitive-matrix-v0.1.md` — framework coverage, lifecycle, relationships, admission sub-taxonomy
- `docs/research/ai-framework-taxonomy-v0.1.md` — 26 framework families, 498-framework inventory
- `docs/research/hummbl-primitive-invariant-assessment-2026-09-02.md` — novelty/org/op assessment that motivated K12-K14, family codes, severity tiers, and D7 bypassability fix
- `hummbl_governance/data/*.schema.json` — JSON Schema files for all governed objects
- `hummbl_governance/kernel/invariants.py` — K1-K14 enum definitions, Severity enum, default_severity()
- `hummbl_governance/kernel/doctrine_engine.py` — D1-D7 enum definitions, _is_invariant_amendment() multi-signal detection
- `hummbl_governance/primitive_registry.py` — PrimitiveRegistry (runtime-queryable inventory, O7)
- `hummbl_governance/external_monitor.py` — ExternalMonitor (runtime verification stub, E3)
- `scripts/check_layer_dependencies.py` — layer dependency lint script (O1 enforcement)

---

## Family Codes

Each primitive has a two-letter family code alongside its P-number, implementing organizational pattern O2 (Family-Based Catalog). The family code encodes the category and provides a stable identifier that survives renumbering.

| Code | Category | Example |
|---|---|---|
| GK | Governance Kernel | GK-1 (P25 AdmissionControl) |
| SF | Safety | SF-1 (P1 KillSwitch) |
| CB | Cost & Budget | CB-1 (P5 CostGovernor) |
| IA | Identity & Auth | IA-1 (P6 IdentityRegistry) |
| AC | Audit & Compliance | AC-1 (P8 AuditLog) |
| RC | Reasoning & Contract | RC-1 (P11 ReasoningEngine) |
| CO | Coordination | CO-1 (P14 CoordinationBus) |
| BH | Behavior & Health | BH-1 (P17 RewardMonitor) |
| PA | Physical AI | PA-1 (P20 PhysicalGovernor) |
| EA | Execution Assurance | EA-1 (P21 EAL) |
| ET | Error Taxonomy | ET-1 (P22 Errors) |
| GE | Governance Ecology | GE-1 (P37 ApprovalManager) |
| CR | Cryptography | CR-1 (P44 Attest) |
| CI | Corpus Integration | CI-1 (P47 CorpusAdapter) |
| LH | Lifecycle Hygiene | LH-1 (P41 Retirement, candidate) |
| CL | Concept Layer | CL-1 (P42 ConceptRegistry, candidate) |
| RM | Risk Management | RM-1 (P43 RiskRegister, candidate) |

Family codes are available at runtime via `PrimitiveRegistry().family_codes()`.

---

## Severity Tiers

Each invariant has a default severity tier that determines the response on violation. This implements organizational pattern O5 (Severity-Tiered Catalog) and replaces the previous binary CRITICAL/non-CRITICAL classification.

| Severity | Response | Invariants |
|---|---|---|
| CRITICAL | KernelPanic, immediate halt | K1, K3, K6, K11, K14 |
| HIGH | KernelPanic, halt or quarantine | K2, K5, K8, K9, K10 |
| MEDIUM | Warning, operator review required | K4, K7, K12 |
| LOW | Log entry, informational | K13 |

Severity can be overridden per-call-site via `KernelPanic(severity=...)`. The default is looked up via `default_severity(invariant)`.

---

## Organizational Layers

Primitives are organized into five layers (organizational pattern O1, Layered Architecture). Import direction flows downward: Infrastructure can import from any layer; Authority can import from Foundation but not from Containment, Evidence, or Infrastructure. Foundation is importable by all layers.

| Layer | Description | Primitives |
|---|---|---|
| Foundation | Shared base modules (errors, schema_validator, _types) — not governance primitives | `errors.py`, `schema_validator.py`, `_types.py` |
| Authority | Primitives that scope what an agent can do | P6, P7, P25, P27, P31, P34, P36, P37, P38, P44, P45, P46, P48, P49 |
| Containment | Primitives that bound what happens when things go wrong | P1, P2, P4, P5, P16, P17, P20, P28, P29 |
| Evidence | Primitives that prove what actually happened | P8, P15, P21, P26, P30, P50, P51, P52 |
| Infrastructure | Utility primitives that support the above | P3, P9, P10, P11, P12, P13, P14, P18, P19, P22, P23, P24, P47 |

Layer dependencies are enforced by `scripts/check_layer_dependencies.py`. The FOUNDATION layer was added 2026-09-02 to resolve 13 cross-layer import violations where authority/containment/evidence modules needed `schema_validator` and `errors` (previously misclassified as infrastructure).
