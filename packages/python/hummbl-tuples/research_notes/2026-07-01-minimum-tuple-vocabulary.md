# Minimum Tuple Vocabulary for Agent Governance

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #27 (A1: Investigate minimum tuple vocabulary for agent governance)
- **Date:** 2026-07-01

## Purpose

Analyze which of the current 21+ tuple types are truly necessary vs. which could be consolidated. Run via empirical corpus (existing examples + simulation outputs).

## Methodology

1. Enumerate all current tuple types from `schemas/` and `docs/specs/TYPED_TUPLE_TAXONOMY.md`
2. Classify each as: essential, consolidable, or experimental
3. Identify consolidation candidates
4. Propose minimum vocabulary
5. Document trade-offs

## Current Tuple Types (21 core + 11 experimental)

### Core 6 IDP Tuples

| Tuple | Role | Essential? | Rationale |
|-------|------|------------|-----------|
| CONTRACT | Bounded work definition | YES | Cannot delegate without a contract |
| DCT | Delegated capability token | YES | Cannot grant capabilities without DCT |
| DCTX | Delegation context | CONDITIONAL | Could be folded into CONTRACT or DCT as a field |
| SYSTEM | Runtime control-plane event | YES | Cannot record runtime events without SYSTEM |
| EVIDENCE | Proof of execution | YES | Cannot audit without evidence |
| ATTEST | Verification outcome | YES | Cannot verify without attestation (see #30) |

### Experimental 11 Bio-governance Tuples

| Tuple | Role | Essential? | Rationale |
|-------|------|------------|-----------|
| BIO_SIGNAL | Bio-cognitive signal | EXPERIMENTAL | Not yet promoted from experimental |
| BIO_DRIFT | Bio-cognitive drift | EXPERIMENTAL | Not yet promoted |
| BIO_RECOVERY | Recovery event | EXPERIMENTAL | Not yet promoted |
| BIO_ENGAGEMENT | Engagement event | EXPERIMENTAL | Not yet promoted |
| BIO_BASELINE | Baseline measurement | EXPERIMENTAL | Not yet promoted |
| BIO_TRIGGER | Trigger event | EXPERIMENTAL | Not yet promoted |
| BIO_CONTEXT | Bio context | EXPERIMENTAL | Not yet promoted |
| BIO_RELATION | Bio relation | EXPERIMENTAL | Not yet promoted |
| BIO_EVOLUTION | Evolution event | EXPERIMENTAL | Not yet promoted |
| BIO_RECEIPT | Bio receipt | EXPERIMENTAL | Not yet promoted |
| BIO_ATTEST | Bio attestation | EXPERIMENTAL | Not yet promoted |

### BaseN (8 types) and Nodezero (4 types)

These are research instrumentation tuples, not governance tuples. They are out of scope for minimum agent governance vocabulary.

## Consolidation Analysis

### DCTX → CONTRACT or DCT?

**Current state:** DCTX is a separate tuple class for delegation context and lifecycle.

**Consolidation option:** Fold DCTX into CONTRACT or DCT as a `context` field.

**Arguments for consolidation:**
- DCTX has low standalone value — context is always associated with a contract or capability
- Reduces tuple type count by 1
- Simplifies consumer code (no need to join DCTX with parent)

**Arguments against consolidation:**
- DCTX has its own lifecycle (can be updated without modifying parent)
- Separation allows context updates without contract/capability reissuance
- Audit trail is cleaner with separate DCTX tuples

**Recommendation:** KEEP SEPARATE. The lifecycle argument is strong — context updates are common and should not require contract reissuance.

### BIO_ATTEST → ATTEST?

**Current state:** BIO_ATTEST is a separate experimental tuple for bio-cognitive attestation.

**Consolidation option:** Fold BIO_ATTEST into ATTEST with a `domain: bio` field.

**Arguments for consolidation:**
- ATTEST already handles verification outcomes
- Bio attestation is semantically the same (verify a claim)
- Reduces experimental tuple count by 1

**Arguments against consolidation:**
- Bio attestation has different verification methods
- Bio domain is experimental and should not pollute core ATTEST

**Recommendation:** CONSOLIDATE when bio tuples are promoted. Until then, keep separate as experimental.

### BIO_RECEIPT → EVIDENCE?

**Current state:** BIO_RECEIPT is a separate experimental tuple for bio-cognitive receipts.

**Consolidation option:** Fold BIO_RECEIPT into EVIDENCE with a `domain: bio` field.

**Arguments for consolidation:**
- EVIDENCE already handles proof of execution
- Bio receipts are semantically evidence
- Reduces experimental tuple count by 1

**Arguments against consolidation:**
- Bio receipts have different metadata (physiological signals, timestamps)
- Bio domain is experimental

**Recommendation:** CONSOLIDATE when bio tuples are promoted. Until then, keep separate as experimental.

## Proposed Minimum Vocabulary

### Tier 1: Essential (6 types)

The minimum vocabulary for agent governance:

| Tuple | Role |
|-------|------|
| CONTRACT | Bounded work definition |
| DCT | Delegated capability token |
| DCTX | Delegation context and lifecycle |
| SYSTEM | Runtime control-plane event |
| EVIDENCE | Proof of execution |
| ATTEST | Verification outcome |

### Tier 2: Research Instrumentation (12 types)

Not part of minimum governance vocabulary, but needed for research:

- BaseN (8 types): Research instrumentation
- Nodezero (4 types): Experiment control

### Tier 3: Experimental (11 types, consolidable to ~3)

Bio-governance tuples, not yet promoted. When promoted, consolidate to:
- BIO_SIGNAL (merged with BIO_DRIFT, BIO_BASELINE, BIO_TRIGGER)
- BIO_CONTEXT (merged with BIO_RELATION, BIO_EVOLUTION)
- BIO_RECEIPT → EVIDENCE (consolidated)

## Trade-offs

### Fewer types (aggressive consolidation)
- **Pro**: Simpler consumer code, smaller schema surface
- **Con**: Loss of semantic precision, harder to query specific tuple types

### More types (current approach)
- **Pro**: Semantic precision, clear query patterns
- **Con**: Larger schema surface, more consumer code

### Recommended: 6 essential + 12 research + 3 consolidated bio = 21
This matches the current count but with clearer tiering.

## Novelty Quest Entry

**Question:** Can agent governance be achieved with fewer than 6 tuple types?

**Hypothesis:** No — each of the 6 essential types addresses a distinct governance concern (delegation, capability, context, runtime, evidence, verification).

**Falsifier:** Find a governance scenario that can be fully audited with fewer than 6 types.

**Status:** Open. No falsifier found in current corpus.

## Do Not Infer

- Do not infer that the minimum vocabulary is final (empirical testing may change it)
- Do not infer that experimental tuples should be dropped (they may be promoted)
- Do not infer that consolidation is always beneficial (context matters)
- Do not infer that this analysis constitutes a schema change (it's a recommendation)

## Non-goals

- Not a schema change proposal
- Not a deprecation of experimental tuples
- Not a final taxonomy decision
