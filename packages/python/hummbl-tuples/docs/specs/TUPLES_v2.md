# TUPLES v2

Status: draft
Supersedes: TUPLES_v1
Scope: HUMMBL governance tuples across delegation, control-plane execution, evidence capture, and research instrumentation

## 1. Purpose

Tuples are typed governance records used to make agentic execution bounded and inspectable.

A tuple is not just a log line. It is a typed claim about execution state with enough structure to support:

- deterministic validation
- policy checks
- auditability
- evidence collection
- controlled delegation
- research instrumentation

## 2. Design Goals

- Small surface area per domain
- Typed semantics with layered complexity
- Explicit blast-radius bounds
- Human-readable and machine-validatable
- Stable enough for publication, flexible enough for research
- VERUM-aligned where governance applies, lightweight where it doesn't

## 3. Layered Envelope

All tuples share a universal base (Layer 1). Additional layers apply based on the tuple's domain and governance requirements.

### 3.1 Layer 1 — Universal (all tuples)

Every tuple in the HUMMBL system carries these fields in the top-level envelope:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tuple_type` | string | yes | Stable class identifier (e.g., `CONTRACT`, `MODEL_SELECTED`) |
| `id` | string | yes | Immutable record identifier (UUID or short hash) |
| `time` | string | yes | UTC ISO 8601 timestamp |
| `tuple_data` | object | yes | Type-specific payload |

Layer 1 establishes identity, temporality, and type discrimination for every record in the system.

### 3.2 Layer 2 — Governance (governed tuples only)

Tuples that represent governed decisions, delegations, or enforcement actions carry VERUM-aligned governance fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | string | yes | Outcome status: `ok`, `blocked`, `error` (VERUM node 3) |
| `drift` | number | yes | Deviation from setpoint, 0.0 to 1.0 (VERUM node 4) |
| `tier` | integer | yes | Governance tier: 0 (read), 1 (write/evidence), 2 (governed), 3 (chain) |
| `agent` | string | yes | Actor identity |
| `tool` | string | yes | Namespaced tool name |

Layer 2 applies to: CONTRACT, DCT, DCTX, SYSTEM, EVIDENCE, ATTEST.

Layer 2 does NOT apply to research/experiment tuples (BaseN, Nodezero, Bio) unless they gain governance enforcement. Research tuples are observed artifacts, not governed decisions.

### 3.3 Layer 3 — Domain-Specific

Each tuple family defines additional envelope fields specific to its domain:

**IDP envelope** (CONTRACT, DCT, DCTX, EVIDENCE, ATTEST, SYSTEM):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Execution intent lineage |
| `task_id` | string | yes | Unit-of-work lineage |

**BaseN envelope** (MODEL_CANDIDATE, MODEL_SELECTED, TRANSFORMATION_CANDIDATE, TRANSFORMATION_SELECTED, HITL_OVERRIDE, REASONING_PATH, PATH_COMPARISON, TRACE_EVIDENCE):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `problem_id` | string | yes | Problem under study |
| `run_id` | string | yes | Experiment run identifier |
| `control_mode` | string | yes | One of: AI_AUTONOMOUS, AI_PROPOSE_HUMAN_CONFIRM, HITL_INFLUENCED, HITL_CONTROLLED, HOTL_SUPERVISED |

**Nodezero envelope** (BASE_PROFILE_ISSUED, CONTROL_MODE_SET, REGISTRY_VERSION_PINNED, EXPERIMENT_RUN_ASSIGNED):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | Experiment run identifier |

EXPERIMENT_RUN_ASSIGNED additionally requires `problem_id`.

**Bio envelope** (BIO_SIGNAL_CAPTURED, BIO_HARM_SIGNAL, BIO_ACTION_BLOCKED, BIO_ACTION_AUTHORIZED, BIO_ADAPTATION_PROPOSED, BIO_ADAPTATION_EXECUTED, BIO_OUTCOME_OBSERVED, BIO_OVERRIDE, READINESS_INFERRED, STRAIN_FLAGGED, WORKLOAD_INFERRED):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject_id` | string | yes | Subject identifier |
| `run_id` | string | yes | Session or observation run |
| `control_mode` | string | yes | Governance control mode |

### 3.4 Layer 4 — Integrity (optional, any tuple)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `args_hash` | string | no | SHA-256 of canonical JSON args |
| `signature` | string | no | HMAC-SHA256 integrity marker |
| `previous_hash` | string | no | Chain link to prior tuple (Tier 3 only) |
| `contract_id` | string | no | Authority reference (Tier 2+) |
| `dct_id` | string | no | Delegation token reference (Tier 2+) |
| `dct_chain_depth` | integer | no | Delegation depth (Tier 2+) |

### 3.5 Trace Artifacts

Pretraining and posttraining trace records retain their distinct envelope (`artifact_type`, `lifecycle_stage`, `trace_source`, `trace_visibility`, `governance_status`) with Layer 1 fields added. These are observation records, not governed tuples.

## 4. Tuple Classes

### 4.1 CONTRACT (Layer 1 + 2 + 3/IDP)

Defines bounded work: objective, allowed tools, denied tools, inputs, outputs, evidence requirements, risk tier, delegation depth limits.

### 4.2 DCT (Layer 1 + 2 + 3/IDP)

Delegated capability token: issuer, subject, operations allowed, token identifier, issuance lifecycle event.

### 4.3 DCTX (Layer 1 + 2 + 3/IDP)

Delegation context: state transition, parent-child task linkage, chain depth, lifecycle status.

### 4.4 SYSTEM (Layer 1 + 2 + 3/IDP)

Runtime control-plane event: adapter invocation, capability denial, enforcement mode, runtime controls.

### 4.5 EVIDENCE (Layer 1 + 2 + 3/IDP)

Execution proof: completion outcome, evidence identifiers, duration, warnings/errors summary.

### 4.6 ATTEST (Layer 1 + 2 + 3/IDP)

Verification outcome: evidence hash reference, verifier identity, pass/fail determination, findings.

### 4.7 BaseN Research Tuples (Layer 1 + 3/BaseN)

MODEL_CANDIDATE, MODEL_SELECTED, TRANSFORMATION_CANDIDATE, TRANSFORMATION_SELECTED, HITL_OVERRIDE, REASONING_PATH, PATH_COMPARISON, TRACE_EVIDENCE.

Research instrumentation tuples. Not governed — they record experimental observations.

### 4.8 Nodezero Control Tuples (Layer 1 + 3/Nodezero)

BASE_PROFILE_ISSUED, CONTROL_MODE_SET, REGISTRY_VERSION_PINNED, EXPERIMENT_RUN_ASSIGNED.

Experiment-control tuples issued by the Nodezero meta-governor.

### 4.9 Bio-Governance Tuples (Layer 1 + 3/Bio)

BIO_SIGNAL_CAPTURED, BIO_HARM_SIGNAL, BIO_ACTION_BLOCKED, BIO_ACTION_AUTHORIZED, BIO_ADAPTATION_PROPOSED, BIO_ADAPTATION_EXECUTED, BIO_OUTCOME_OBSERVED, BIO_OVERRIDE, READINESS_INFERRED, STRAIN_FLAGGED, WORKLOAD_INFERRED.

Bio-cognitive signal tuples. Currently observation-only (no Layer 2).

## 5. Tier Model

The tier model governs what governance artifacts a tool call produces:

| Tier | Scope | Tuple output | Layer 2 required |
|------|-------|-------------|------------------|
| 0 | Reads | No tuple emitted | n/a |
| 1 | Writes | EVIDENCE only | yes |
| 2 | Governed decisions | CONTRACT + DCT + EVIDENCE | yes |
| 3 | Chains | Hash-linked sequential tuples | yes |

Tier classification is policy-as-code. See `basen_tier.py` in the runtime repo.

## 6. Validation Principles

- Unknown tuple classes fail closed unless explicitly allowed in research mode.
- Layer 1 fields (`tuple_type`, `id`, `time`, `tuple_data`) are always required.
- Layer 2 fields are required for IDP tuples, absent for research tuples.
- `tuple_data` must be schema-validated per tuple class.
- Timestamps must be UTC-normalized.
- IDP tuples must preserve lineage across `intent_id` and `task_id`.

## 7. Non-Goals

- This spec does not define transport.
- This spec does not require a single storage backend.
- This spec does not assume all tuples are security tokens.
- This spec does not claim the current taxonomy is complete.
- This spec does not require Layer 2 for research instrumentation tuples.

## 8. Relationship to VERUM

VERUM defines four node fields: `id`, `time`, `state`, `drift`. In the layered model:

- `id` and `time` are universal (Layer 1) — every record needs identity and temporality
- `state` and `drift` are governance-specific (Layer 2) — they measure outcome and deviation, which only applies to governed decisions

### 8.1 Why VERUM Fields Are Split Across Layers

The four VERUM fields decompose into two functional pairs:

| Pair | Fields | Function | Applies to |
|------|--------|----------|------------|
| **Existence** | `id`, `time` | "This record happened" | All records — universal |
| **Judgment** | `state`, `drift` | "How did it go?" | Governed decisions only |

`id` and `time` are properties of *any* record in *any* system. They are not unique to VERUM — they are prerequisites for it. A log entry, a database row, and an event all have identity and temporality.

`state` and `drift` are the fields that make a tuple *governed*. `state` records the outcome of a governed decision. `drift` quantifies deviation from a governance setpoint. These only have meaning when something was being *governed* — when a policy was being enforced, an authority was being exercised, or a boundary was being checked.

Attaching `state: "ok"` and `drift: 0.0` to a research observation tuple (e.g., `MODEL_SELECTED`) would require either:
1. Meaningless defaults that teach consumers to ignore governance fields, or
2. Forced reinterpretation where "drift" means something different per domain, undermining the term's precision.

Neither outcome serves the spec or the paper.

### 8.2 Publishable Claim

VERUM's sovereignty claim rests on `state` and `drift` — the fields that distinguish a governed tuple from a mere log entry. The layered decomposition reveals that governance is not a property of all records, but a property of records that assert a policy outcome. This distinction is the boundary between audit (Layer 1: "what happened") and governance (Layer 2: "was it within bounds").

### 8.3 Upgrade Path

If a tuple family gains governance enforcement (e.g., Bio-governance tuples begin enforcing harm-signal thresholds), it adopts Layer 2 fields. The upgrade is additive — existing Layer 1 + Layer 3 fields are unchanged. This makes the governance boundary explicit and evolvable without breaking existing consumers.
