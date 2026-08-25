# Scientific Grounding Tuple Pattern

## Purpose

`hummbl-tuples` provides the auditable tuple pattern for scientific grounding.
The key boundary is:

- `EVIDENCE` records that a source-grounding event or claim-linkage event
  happened
- `ATTEST` records that a verifier reviewed that evidence and passed or failed it
- `PROMOTION_RECEIPT` records a governed promotion decision

These are not interchangeable.

## Boundary Rule

Do not use:

- `EVIDENCE` as if it were independent verification
- `ATTEST` as if it were the source evidence itself
- `PROMOTION_RECEIPT` as if it created scientific truth

Scientific grounding needs at least:

1. a source-grounding `EVIDENCE` tuple
2. optionally, a claim-linkage `EVIDENCE` tuple
3. an `ATTEST` tuple by a distinct verifier if the claim is being reviewed

## Minimal Pattern

### 1. Source grounding event

Use `EVIDENCE` to record that a claim was linked to an external source or
bibliography key.

Required practical fields inside `tuple_data`:

- `event`
- `evidence_id`
- `source_kind`
- `source_ref`
- `claim_ref`
- `grounding_status`

### 2. Claim attestation event

Use `ATTEST` to record the verifier outcome over the evidence artifact.

Required practical fields inside `tuple_data`:

- `event`
- `evidence_hash`
- `verifier_id`
- `passed`
- `claim_ref`
- `attestation_scope`

## Distinction From Promotion

`PROMOTION_RECEIPT` belongs later in the chain. It answers:

- may this artifact move to a new environment, trust rung, or publication rung?

It does not answer:

- was the source real?
- was the claim well-grounded?
- did the verifier independently confirm the evidence?

## Examples

- `examples/evidence.scientific-source-grounded.json`
- `examples/attest.scientific-source-grounded.json`

These examples distinguish source grounding from attestation without adding new
schema families.
