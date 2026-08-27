# DOCTRINE.md - base120

**Status:** v0.2
**Steward:** HUMMBL, LLC
**Amendment history:** v0.1 → v0.2 (2026-08-19): §4 amended to introduce registry/language layer distinction and reconcile §1 executability claim with §4 non-execution boundary. Operator-adjudicated, governance-review-drafted text. See ADR and KRINEIA receipt for audit trail.

## 1. Thesis

Base120 is the deterministic governance substrate for HUMMBL: 120 named,
versioned reasoning operators organized into six cognitive domains
(Perspective, Inversion, Composition, Decomposition, Recursion, Systems).
The core bet is that structured reasoning can be made *executable* -- each
operator is a primitive with a defined transformation family, a prompt
template, and a deterministic package representation that humans and AI agents
can apply identically.

The substrate is deliberately stdlib-only and registry-first. The canonical
YAML registry is the single source of truth, readable by any language; the
Python SDK is a convenience layer over it, not a dependency the registry
requires. This keeps the mental models portable across runtimes and immune to
dependency rot.

Base120 also persists governance-readable records: every operator application
can be emitted as a VERUM-aligned ledger tuple, giving reasoning a provenance
trail. The bet is that auditable reasoning is a prerequisite for trustworthy
agent fleets, not a nice-to-have.

## 2. Conceptual vocabulary

- **Operator** -- a named, versioned reasoning primitive (e.g. P1 First
  Principles, IN2 Premortem Analysis) with a transformation family and package form.
- **Cognitive domain** -- one of six transformation families (P, IN, CO, DE,
  RE, SY) that groups operators by the kind of thinking they perform.
- **Canonical registry** -- the frozen YAML artifact (`Base120_Canonical_Model_
  Registry.yaml`) that is the authoritative definition of all 120 operators.
- **Prompt** -- a generated template that instructs an agent or human to apply
  a given operator to a given question.
- **Ledger tuple** -- an append-only JSONL record of an operator application,
  VERUM-aligned for governance consumption.
- **MCP serving** -- exposing operators to AI agents via the Model Context
  Protocol so agents can retrieve and apply them at runtime.

## 3. Design principles

1. **Registry-first.** The YAML registry is the source of truth; SDKs are
   readers, not owners, of the model definitions.
2. **Stdlib-only SDK.** The Python package has zero third-party runtime
   dependencies; it runs anywhere Python 3.11+ runs.
3. **Deterministic representation.** Every operator has a stable id, version,
   and package form so applications are reproducible and comparable.
4. **Provenance by default.** Operator applications can be recorded as ledger
   tuples without extra plumbing.
5. **Human and agent parity.** The same operator produces the same prompt and
   record whether the applier is a person or an AI agent.
6. **Frozen reference artifacts.** Canonical data files are versioned and
   frozen; changes are deliberate and reviewable, not incidental.

## 4. Boundaries

Base120 has two layers, each with distinct boundaries.

**Registry layer.** The canonical registry (`Base120_Canonical_Model_Registry.yaml` v1.0.0) and the stdlib-only Python SDK that reads it define and serve reasoning operators. The registry layer does not *execute* reasoning, does not evaluate the quality of an answer, and does not choose which operator to apply to a problem -- that selection is the caller's (or a higher orchestration layer's) responsibility. It is not an LLM runtime; it produces prompts and records, and delegates generation to whatever runner the caller wires up. It does not enforce policy or block execution; it provides the vocabulary other layers govern with. It does not own the failure-mode taxonomy (FM1-FM30), which has migrated to hummbl-governance.

**Language layer.** A separate language layer (the `base120-lang` project) may define a notation and DSL that *specifies* reasoning operator composition and *delegates* execution to a pluggable runner. The language layer does not autonomously select operators, does not evaluate output quality, and does not own a runner -- it defines a runner interface (`run_step`) and ships a reference LLM runner as one implementation among possible implementations (LLM, human, deterministic). Execution of a pre-defined chain via a delegated runner is consistent with the registry layer's existing delegation boundary ("delegates generation to whatever runner the caller wires up"); autonomous operator selection and quality judgment remain prohibited at both layers.

The two layers reconcile §1's executability claim with §4's non-execution boundary: the registry is non-executing; the language is executing-by-delegation; neither is autonomous.

## 5. Open questions

- How should operator versioning handle backward-incompatible changes to a
  mental model's definition without invalidating historical ledger records?
- Is 120 the right cardinality, or should the registry grow as new reasoning
  patterns emerge -- and what is the inclusion criterion?
- How can operator selection be automated safely without reintroducing
  nondeterministic LLM-in-the-loop routing?
- Should the ledger tuple schema be standardized across HUMMBL repos, or
  remain Base120-local?
- What is the right MCP exposure granularity -- per-operator, per-domain, or a
  single unified server?
