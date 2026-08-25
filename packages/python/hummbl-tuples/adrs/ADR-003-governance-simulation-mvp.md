# ADR-003: Governance Simulation MVP (Prototype)

Date: 2026-04-10
Status: accepted
Amends: ADR-002

## Context

The 2026-04-10 research handoff from Claude.ai (strategy) recommends an LLM-augmented ABM governance simulator as the MVP direction, grounded in Park et al. (2023) *Generative Agents*, with the EU AI Act (Aug 2, 2026) deadline as the demand catalyst. HUMMBL's Gemini Probation Incident is identified as a unique empirical corpus for validation.

ADR-002 explicitly scopes this repo away from "a full runtime, a workflow engine, a duplicate of `hummbl-agent` or `hummbl-governance`." A production simulator belongs in `hummbl-governance`. However, the strategy handoff converges on building a **prototype here first**, so that the tuple schemas in this repo get exercised as the canonical event surface of the simulator, and so that the research artifact (staged validation, sensitivity analysis, uncertainty quantification) can evolve in the repo that is already set up for publication-oriented work.

## Decision

Build a bounded governance simulation prototype in `hummbl_tuples/simulation/` under the following constraints. This amends ADR-002 to permit simulation work under an explicit carve-out, not to broaden repo scope in general.

### Scope (staged)

1. **Stage 1 — Demonstrable sim (this ADR).**
   - Deterministic rule-based core.
   - One synthetic scenario modeled on the Gemini Probation Incident shape.
   - Trace = list of tuple dicts that validate against the existing `schemas/`.
   - CLI runner + regression test (schema validation + determinism).
2. **Stage 2 — Research instrument (follow-up).**
   - Validation harness that compares traces against empirical incident logs
     (corpus held by a separate HUMMBL session, not yet in this repo).
   - Sensitivity analysis (Morris or Sobol) over `TrustModel` /
     `ProbationPolicy` parameters via seed/parameter sweeps.
   - Uncertainty quantification: distributions over scalar observables
     extracted by `trace_summary`, not point estimates.

### Architecture

Hybrid: rule-based core is the scientific instrument; LLM-backed agents are a
pluggable wrapper. Concretely:

- `Environment`, `TrustModel`, `ProbationPolicy`, and the scripted scenario are
  the deterministic core. All validation runs against this core.
- `LLMAdapter` is a `typing.Protocol` (no implementation). When a Stage 2
  iteration adds an LLM-backed agent, it must propose actions that still flow
  through the same enforcement pipeline — the pipeline cannot be bypassed by
  the adapter.
- No external dependencies. Stdlib only. Matches the existing
  `reference_impl/` posture and keeps the migration target (`hummbl-governance`)
  free to pick its own packaging.

### Deliverable posture

This package is flagged as a **prototype for hummbl-governance**. Code is
organized so that the transplant is mechanical:

- Module boundaries match the eventual hummbl-governance layout
  (`events` / `trust` / `core` / `scenarios` / `cli`).
- No cross-imports from other `hummbl_tuples` submodules.
- No dataclass shims — events are plain dicts conforming to the JSON Schemas,
  which are the authoritative wire format.

### Validation data

The Gemini Probation Incident logs are not in this repo. The Stage 1 scenario
is synthetic and is structured so that real logs drop in via
`Scenario.metadata['source'] = 'empirical'` plus an `empirical_trace` metadata
slot. The structural fields (contract shape, allowed_tools, action sequence
categories) are the migration contract.

## Consequences

- The tuple schemas in this repo are now exercised as an execution surface,
  not just a spec surface. Any schema drift will immediately break the
  regression test.
- The repo now contains code that ADR-002 would otherwise disallow. This is
  bounded by the "prototype for hummbl-governance" framing: if Stage 2
  grows beyond what this repo should host, the carve-out ends and the
  package moves.
- The Stage 2 validation / sensitivity / uncertainty work is **not yet
  implemented**. The research note
  `research_notes/2026-04-10-simulation-mvp-design.md` records the gap
  explicitly and names the interface point (`trace_summary`).
- Known limitations (LLM hallucination propagation, sim-to-real gap,
  unsolved plain-language → config reliability) are recorded in the research
  note and must be re-stated in any external writeup that cites this work.
