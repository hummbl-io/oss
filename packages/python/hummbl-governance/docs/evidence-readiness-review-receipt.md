# Evidence Readiness Review Receipt

Status: Governed (v1)
Schema: [`hummbl_governance/data/evidence_readiness_review_receipt.schema.json`](../hummbl_governance/data/evidence_readiness_review_receipt.schema.json)
`$id`: `https://hummbl.dev/schemas/evidence-readiness-review-receipt.v1.json`
Date: 2026-05-15 (draft) · 2026-06-22 (promoted to governed v1, hummbl-governance#67)

## Purpose

Map HUMMBL evidence-readiness packets to governance review receipts.

This is a review-control surface, not a legal-advice surface. It records whether
an evidence packet is safe to relay to the intended audience.

This receipt is the **governed decision surface** for evidence-readiness reviews.
Agents and operators record review dispositions here; the JSON schema is the
contract that makes a review machine-checkable.

## Review Receipt Scope

Use this receipt for:

- attorney consult packets;
- relay-safe client summaries;
- counterargument premortems;
- claim verification tables;
- public-use case-study candidates derived from matter work.

Do not store raw confidential evidence in the receipt. Store hashes, paths,
review verdicts, and evidence references.

## Verdicts

The verdict enum is **governed** by this schema. The four values map onto the
generic readiness outcomes (`ready` / `needs-revision` / `not-ready`) while
preserving the severity granularity required for relay decisions:

| Verdict | Readiness outcome | Meaning |
|---|---|---|
| `APPROVE_FOR_RELAY` | ready | No blocking defects; intended audience can receive |
| `APPROVE_WITH_P2` | needs-revision (non-blocking) | Relay allowed; important non-blocking caveats remain |
| `BLOCKED_P1` | needs-revision (blocking) | Relay blocked until significant defects are fixed |
| `BLOCKED_P0` | not-ready | Relay blocked; breach/fabrication/data exposure or equivalent |

## Finding Severities

| Severity | Meaning |
|---|---|
| `P0` | Breach, fabrication, data exposure, or irreversible high-impact defect |
| `P1` | Factual error, scope breach, legal-boundary breach, or relay-blocking inconsistency |
| `P2` | Important ambiguity, missed edge case, or incomplete operationalization |
| `P3` | Style, clarity, or low-risk cleanup |

## Required Fields

```json
{
  "schema_version": "evidence-readiness-review-receipt.v1",
  "receipt_id": "uuid",
  "created_at": "2026-05-15T00:00:00Z",
  "matter_id": "hashed-or-local-id",
  "data_classification": "CLIENT_CONFIDENTIAL",
  "intended_audience": "attorney|client|operator|internal|public",
  "packet_paths": [
    "05_attorney_packet/consult-brief.md",
    "06_relay_safe/client-summary.md"
  ],
  "source_manifest_ref": {
    "path": "01_sources/manifest.md",
    "sha256": "hex"
  },
  "reviewer": {
    "id": "codex",
    "role": "critical_peer"
  },
  "verdict": "APPROVE_WITH_P2",
  "findings": [
    {
      "severity": "P2",
      "item": "Q14",
      "status": "OPEN",
      "summary": "Demand-letter floor remains under-operationalized"
    }
  ],
  "claim_honesty": {
    "unsupported_claims": 0,
    "interpretations_labeled": true,
    "legal_questions_reserved_for_counsel": true,
    "public_use_approved": false
  },
  "relay_decision": {
    "allowed": true,
    "conditions": [
      "Do not share with opposing-side actors"
    ]
  }
}
```

## Relationship To Existing EAL Receipts

The EAL receipt schema records deterministic action execution and integrity.
Evidence-readiness review receipts record human/agent review disposition.

Mapping:

| Evidence Readiness Field | EAL Analog |
|---|---|
| `receipt_id` | `execution_id` |
| `packet_paths` | `actions[].params_evidence_id` |
| `source_manifest_ref.sha256` | `evidence[].sha256` |
| `verdict` | `actions[].boundary_assertion.decision` plus review note |
| `findings` | evidence blob referenced by hash |
| `relay_decision.allowed` | boundary assertion |

Do not force these into the EAL schema until a compatibility decision is made.
For now, use this as an adapter spec.

## Claim-Honesty Checks

Before `APPROVE_FOR_RELAY` or `APPROVE_WITH_P2`, reviewer must verify:

- every material factual claim maps to a source;
- unsupported claims are removed or marked `UNKNOWN`;
- interpretations are labeled;
- legal advice is converted into questions for counsel;
- public claims have separate consent and approval;
- no confidential content appears in bus posts, public issues, PR bodies, or
  marketing drafts.

## Public-Use Gate

Set `public_use_approved` to `false` by default.

Public use requires:

1. recorded consent;
2. redaction or synthetic rewrite;
3. claim-honesty table;
4. operator/legal approval;
5. non-author review.

## Workflow

The evidence-readiness review receipt follows a create → review → store flow:

1. **Create** — the reviewing agent (or operator) assembles an evidence-readiness
   packet and produces a review receipt. The `reviewer` field records who created
   the disposition (`critical_peer`, `attorney`, `operator`, `paralegal`, or
   `system` for automated checks). The creator must not also be the sole
   approver for `APPROVE_FOR_RELAY` when `intended_audience` is `public`; a
   non-author review is required (see Public-Use Gate).
2. **Review** — a second reviewer confirms the verdict, findings, and
   claim-honesty fields. P0/P1 findings trigger the blocking rule below. The
   receipt is validated against the governed JSON schema before it is stored.
3. **Store** — the validated receipt is stored at the matter's audit location
   (typically `99_audit/review-receipt.<receipt_id>.json`) and referenced by
   `receipt_id`. The canonical machine-readable contract is the schema at
   `hummbl_governance/data/evidence_readiness_review_receipt.schema.json`
   (`$id ...v1.json`). Raw confidential evidence is never stored in the receipt;
   only hashes, paths, verdicts, and evidence references are recorded.

### Blocking rule (P0/P1 → BLOCKED)

Any finding with severity `P0`, or any finding with severity `P1` and status
`OPEN`, **must** produce `relay_decision.allowed = false` and a verdict of
`BLOCKED_P0` or `BLOCKED_P1` respectively. A bus-safe blocked summary (verdict
+ `receipt_id` + `matter_id` only, no confidential detail) may be posted to the
bus to signal the hold; the full receipt stays in the matter audit store. This
rule is enforced by the validation tests in
`tests/test_evidence_readiness_review_receipt_schema.py`.

## Resolved Decisions

The open questions from the draft are resolved as follows (closes the open
decisions blocking promotion to a governed surface):

1. **Should the verdict enum be shared with legal/paralegal repos?**
   **Decision: No duplication.** `hummbl-governance` is the canonical source of
   the verdict enum. Legal/paralegal repos reference this schema by its `$id`
   rather than copying the enum, so the values cannot drift. A future cross-repo
   shared module would re-export from here, not redefine.

2. **Should P0/P1 findings automatically trigger a bus-safe `BLOCKED` receipt
   with no confidential details?**
   **Decision: Yes.** See the Blocking rule above. P0 or OPEN P1 findings force
   `relay_decision.allowed = false` and a `BLOCKED_*` verdict. Only a
   confidential-free summary (verdict, `receipt_id`, `matter_id`) is bus-safe;
   the full receipt remains in the matter audit store.

3. **Should public-use approval be represented as a separate receipt type?**
   **Decision: No.** Public-use approval stays inline as
   `claim_honesty.public_use_approved`. Splitting it into a separate receipt
   type would fragment the review surface and risk approving public use without
   the accompanying claim-honesty checks. The Public-Use Gate below remains the
   governing process; the boolean is the audit hook.

## Open Questions

None remaining for v1. The schema is governed. Future revisions (v2+) require a
new `$id` and a migration note here.
