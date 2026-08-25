# TUPLES v1

Status: superseded (see TUPLES_v2.md)  
Scope: HUMMBL governance tuples across delegation, control-plane execution, and evidence capture

## 1. Purpose

Tuples are typed governance records used to make agentic execution bounded and inspectable.

A tuple is not just a log line. It is a typed claim about execution state with enough structure to support:

- deterministic validation
- policy checks
- auditability
- evidence collection
- controlled delegation

## 2. Design Goals

- Small surface area
- Typed semantics
- Explicit blast-radius bounds
- Human-readable and machine-validatable
- Stable enough for publication, flexible enough for research

## 3. Tuple Envelopes

All tuples share a common principle: a small, typed envelope wrapping a `tuple_data` (or `payload`) object that carries the domain-specific fields. Three envelope variants exist to serve different governance domains.

### 3.1 IDP Envelope

Used by delegation and execution governance tuples (CONTRACT, DCT, DCTX, EVIDENCE, ATTEST, SYSTEM).

Required:

- `tuple_type`: stable class identifier
- `timestamp`: UTC ISO 8601 timestamp
- `intent_id`: execution intent lineage
- `task_id`: unit-of-work lineage
- `tuple_data`: type-specific payload

Recommended:

- `entry_id`: immutable record identifier
- `signature`: authenticity or integrity marker

### 3.2 Nodezero Envelope

Used by experiment-control tuples issued by the Nodezero meta-governor (BASE_PROFILE_ISSUED, CONTROL_MODE_SET, REGISTRY_VERSION_PINNED, EXPERIMENT_RUN_ASSIGNED).

Required:

- `tuple_type`: stable class identifier
- `run_id`: experiment run identifier
- `tuple_data`: type-specific payload

EXPERIMENT_RUN_ASSIGNED additionally requires:

- `problem_id`: problem being assigned

### 3.3 BaseN Envelope

Used by BaseN reasoning experiment tuples (MODEL_CANDIDATE, MODEL_SELECTED, TRANSFORMATION_CANDIDATE, TRANSFORMATION_SELECTED, HITL_OVERRIDE, REASONING_PATH, PATH_COMPARISON, TRACE_EVIDENCE).

Required:

- `tuple_type`: stable class identifier
- `problem_id`: problem under study
- `run_id`: experiment run identifier
- `control_mode`: one of AI_AUTONOMOUS, AI_PROPOSE_HUMAN_CONFIRM, HITL_INFLUENCED, HITL_CONTROLLED, HOTL_SUPERVISED
- `tuple_data`: type-specific payload

### 3.4 Trace Artifacts

Pretraining and posttraining trace records use a distinct envelope (artifact_type, lifecycle_stage, trace_source, trace_visibility, governance_status) with a `payload` object instead of `tuple_data`. See `pretraining_trace.schema.json` and `posttraining_trace.schema.json`.

## 4. Tuple Classes

### 4.1 CONTRACT

Defines bounded work.

Expected responsibilities:

- objective
- allowed tools
- denied tools
- inputs
- outputs
- evidence requirements
- risk tier
- delegation depth limits

### 4.2 DCT

Delegated capability token or equivalent authority grant.

Expected responsibilities:

- issuer
- subject
- operations allowed
- token identifier
- issuance lifecycle event

### 4.3 DCTX

Delegation context and lifecycle transition.

Expected responsibilities:

- state transition
- parent-child task linkage
- chain depth
- issuance/running/completion lifecycle status

### 4.4 SYSTEM

Runtime or control-plane events emitted by infrastructure.

Expected responsibilities:

- adapter invocation
- capability denial
- enforcement mode
- runtime controls

### 4.5 EVIDENCE

Execution proof artifacts.

Expected responsibilities:

- completion outcome
- evidence identifiers
- duration or quantitative execution data
- warnings/errors summary

### 4.6 ATTEST

Verification outcome for a task against its contract.

Expected responsibilities:

- evidence hash reference
- verifier identity
- pass/fail determination
- findings

## 5. Validation Principles

- Unknown tuple classes fail closed unless explicitly allowed in research mode.
- `tuple_data` must be schema-validated per tuple class.
- Timestamps must be UTC-normalized.
- Tuple records must preserve lineage across `intent_id` and `task_id`.
- Normative schemas must distinguish required fields from optional implementation metadata.

## 6. Non-Goals

- This spec does not define transport.
- This spec does not require a single storage backend.
- This spec does not assume all tuples are security tokens.
- This spec does not claim the current taxonomy is complete.

## 7. Open Questions

- Which fields deserve canonical cross-system standardization?
- When should tuple classes branch versus extending `tuple_data`?
- What is the minimum envelope needed for interop?
