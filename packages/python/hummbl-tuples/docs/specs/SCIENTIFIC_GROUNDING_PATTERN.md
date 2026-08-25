# Scientific Grounding Evidence Tuple Pattern

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #22
- **Date:** 2026-07-01

## Purpose

Document the tuple pattern for Scientific Grounding evidence. Make `hummbl-tuples` provide the governance/evidence primitive interface needed by Scientific Grounding workflows.

## Problem

The fleet needs to record scientific grounding as auditable evidence tuples. Current EVIDENCE and ATTEST tuple families can support this, but the specific pattern for scientific grounding (source grounding vs. receipt/attestation) is not documented.

## Pattern

Scientific Grounding evidence uses two tuple classes in sequence:

1. **EVIDENCE** — records the source grounding (what was claimed, by whom, where)
2. **ATTEST** — records the verification outcome (was the evidence checked, what was the verdict)

### Source Grounding (EVIDENCE)

```json
{
  "tuple_type": "EVIDENCE",
  "id": "evidence-sg-001",
  "time": "2026-07-01T00:00:00Z",
  "state": "ok",
  "agent": "agent-research",
  "tool": "scientific-grounding-collector",
  "intent_id": "intent-sg-001",
  "task_id": "task-sg-001",
  "evidence_type": "scientific_grounding",
  "evidence_data": {
    "claim": "Mitochondrial function affects executive performance under stress.",
    "source_type": "peer_reviewed_article",
    "source_citation": "Picard et al., 2018",
    "source_url": "https://doi.org/10.1016/j.bbi.2018.01.010",
    "claim_class": "physiological_hypothesis",
    "population_scope": "adults with chronic stress",
    "transcript_status": "not_applicable"
  },
  "tuple_data": {}
}
```

### Receipt/Attestation (ATTEST)

```json
{
  "tuple_type": "ATTEST",
  "id": "attest-sg-001",
  "time": "2026-07-01T00:01:00Z",
  "state": "ok",
  "agent": "agent-verifier",
  "tool": "scientific-grounding-verifier",
  "intent_id": "intent-sg-001",
  "task_id": "task-sg-001",
  "attestation_type": "source_verification",
  "verdict": "verified",
  "tuple_data": {
    "evidence_id": "evidence-sg-001",
    "verification_method": "citation_check",
    "verifier_notes": "Citation confirmed in PubMed. Source type matches."
  }
}
```

## Distinguishing Source Grounding from Receipt/Attestation

| Dimension | EVIDENCE (Source Grounding) | ATTEST (Receipt/Attestation) |
|-----------|-----------------------------|------------------------------|
| What it records | What was claimed and where it came from | Whether the evidence was verified |
| Who creates it | The collecting agent | The verifying agent |
| When it's created | At evidence collection time | At verification time |
| Key field | `evidence_data` (claim + source) | `verdict` (verified/rejected/pending) |
| Links to | The task/intent | The EVIDENCE tuple it verifies |

## Schema Gaps

Current schemas (`evidence.schema.json`, `attest.schema.json`) support this pattern without modification. The `evidence_data` field is flexible enough to hold scientific grounding metadata.

**No schema changes are needed for this pattern.** If future requirements need stricter validation of scientific grounding fields within `evidence_data`, a domain-specific schema extension can be proposed via ADR.

## Validation

Validate the example tuples against existing schemas:

```bash
# Validate EVIDENCE tuple
python reference_impl/validate_examples.py examples/scientific_grounding/evidence_sg.json

# Validate ATTEST tuple
python reference_impl/validate_examples.py examples/scientific_grounding/attest_sg.json
```

## Do Not Infer

- Do not infer that this pattern is canon (it's a documented candidate pattern)
- Do not infer that schema changes are needed (existing schemas support this)
- Do not infer that this pattern covers all scientific grounding scenarios
- Do not infer that the example tuples represent real evidence (they are synthetic)

## Non-goals

- Not a schema change proposal
- Not a protocol specification
- Not a verification method specification
