# Decision Record: Should ATTEST Be Its Own Tuple Class?

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #30 (A4: Evaluate whether ATTEST should be its own tuple class)
- **Date:** 2026-07-01
- **Decision:** KEEP ATTEST AS SEPARATE CLASS

## Context

Currently ATTEST is implied inside EVIDENCE in some implementations. The question is whether separating ATTEST into its own tuple class improves clarity, or whether it adds unnecessary complexity.

## Current State

- `schemas/attest.schema.json` exists as a separate schema
- `schemas/evidence.schema.json` exists as a separate schema
- Some examples conflate evidence and attestation (evidence includes a "verified" field)
- The taxonomy document lists ATTEST as a separate class

## Analysis

### Option A: Keep ATTEST as Separate Class

**Arguments for:**
1. **Separation of concerns**: Evidence records what happened; attestation records whether it was verified. These are different acts by different agents at different times.
2. **Audit clarity**: Auditors can query for attestations independently of evidence. "Show me all verifications" is a distinct query from "Show me all evidence."
3. **Lifecycle independence**: Evidence is created once; attestations can be created, updated, or revoked over time as verification methods evolve.
4. **Agent separation**: The agent that produces evidence may differ from the agent that verifies it. Separate tuples make this explicit.
5. **Multiple attestations**: One piece of evidence may have multiple attestations (e.g., verified by different methods). This is awkward to model inside EVIDENCE.
6. **Consistency with governance model**: The 6 essential types (CONTRACT, DCT, DCTX, SYSTEM, EVIDENCE, ATTEST) each address a distinct governance concern. Merging ATTEST into EVIDENCE would reduce this to 5, losing the verification dimension.

**Arguments against:**
1. **Complexity**: More tuple types means more consumer code.
2. **Joining**: Consumers must join EVIDENCE and ATTEST to get the full picture.
3. **Redundancy**: Some attestations are trivial (e.g., "evidence was collected") and don't need a separate tuple.

### Option B: Merge ATTEST into EVIDENCE

**Arguments for:**
1. **Simplicity**: Fewer tuple types.
2. **No joining**: All information in one tuple.
3. **Trivial attestations**: Simple "verified" flag inside EVIDENCE.

**Arguments against:**
1. **Loss of audit clarity**: Cannot query for verifications independently.
2. **Lifecycle coupling**: Evidence and attestation have different lifecycles.
3. **Agent conflation**: Cannot distinguish who produced evidence vs. who verified it.
4. **Multiple verifications**: Cannot model multiple attestations for one piece of evidence.
5. **Governance gap**: Loses the verification dimension from the governance model.

### Empirical Comparison

#### Model 1: Separate ATTEST

```json
// Evidence
{"tuple_type": "EVIDENCE", "id": "ev-001", "evidence_type": "execution_log", ...}

// Attestation (by different agent, at different time)
{"tuple_type": "ATTEST", "id": "at-001", "attestation_type": "source_verification", "verdict": "verified", "tuple_data": {"evidence_id": "ev-001"}}
```

Trace readability: **HIGH** — clear separation of collection and verification.
Semantic clarity: **HIGH** — each tuple has one meaning.

#### Model 2: Merged into EVIDENCE

```json
// Evidence with embedded attestation
{"tuple_type": "EVIDENCE", "id": "ev-001", "evidence_type": "execution_log", "verified": true, "verified_by": "agent-verifier", "verified_at": "2026-07-01T00:01:00Z", ...}
```

Trace readability: **MEDIUM** — attestation fields are mixed with evidence fields.
Semantic clarity: **MEDIUM** — tuple has two meanings (evidence + verification).

#### Model 3: Merged with Multiple Attestations

```json
// Evidence with multiple embedded attestations (awkward)
{"tuple_type": "EVIDENCE", "id": "ev-001", "evidence_type": "execution_log", "attestations": [
  {"verified_by": "agent-a", "verdict": "verified", "method": "citation_check"},
  {"verified_by": "agent-b", "verdict": "verified", "method": "cross_reference"}
], ...}
```

Trace readability: **LOW** — nested array of attestations is hard to read.
Semantic clarity: **LOW** — tuple has complex nested structure.

## Decision

**KEEP ATTEST AS A SEPARATE TUPLE CLASS.**

The separation of concerns, audit clarity, lifecycle independence, and agent separation arguments outweigh the complexity cost. The empirical comparison shows that separate ATTEST provides better trace readability and semantic clarity, especially when multiple attestations exist for one piece of evidence.

## Consequences

1. **No schema changes needed**: `attest.schema.json` already exists as a separate schema.
2. **Documentation update needed**: Examples that conflate evidence and attestation should be updated.
3. **Consumer code**: Consumers must handle both EVIDENCE and ATTEST tuples.
4. **Query patterns**: Auditors can query for attestations independently.

## Do Not Infer

- Do not infer that this decision is final (new evidence may change it)
- Do not infer that all attestations must be separate tuples (trivial attestations can still be inline)
- Do not infer that this decision applies to experimental tuples (BIO_ATTEST is separate)
- Do not infer that merging was never considered (it was, and rejected)

## Non-goals

- Not a schema change proposal
- Not a deprecation of inline verification fields
- Not a mandate that all evidence must have separate attestations
