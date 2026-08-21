# Source Ingestion and Claim Governance Crosswalk

Status: draft advisory
Date: 2026-06-30
Scope: Workstream 10, source-ingestion and claim-governance convention mapping
Authority: advisory only under `hummbl-io/hummbl-governance#158` and `hummbl-io/hummbl-governance#1190`

This document maps existing conventions observed in live repo files and issue
text. It does not create canon, new governance primitives, new canon levels,
CI gates, production behavior, public claims, MCP/server changes, release
authority, merge authority, or repo-setting authority.

The context artifact that triggered this pass was used only to choose search
direction. It is not evidence for any statement below.

## Issue Boundary

`hummbl-io/hummbl-governance#158` requests advisory schemas, fixtures, docs,
crosswalks, and receipts only. It explicitly keeps production/security/server,
CI/CD, public-claim, canonization, release, deployment, merge, and repo-setting
changes out of scope.

`hummbl-io/hummbl-governance#1190` is the controller issue for the governed agent
runtime packet. It allows schema proposals, docs, fixtures, non-production
tests, crosswalks, and receipts. It does not authorize production/security
changes, connector expansion, CI/CD mutation, repo settings, public claims,
canonization, release, deployment, or merge.

The spike-rule comments on those issues allow draft PR work for schemas,
fixtures, tests, docs, and receipts only. They keep merge, release, production
runtime changes, MCP server changes, CI behavior changes, repo setting changes,
public claims, and canonization behind a separate human gate.

## Evidence Inspected

Local files:

- `hummbl-governance/PRIMITIVES.md`
- `hummbl-governance/hummbl_governance/kernel/canon_registry.py`
- `hummbl-governance/hummbl_governance/data/canon_registry.schema.json`
- `hummbl-governance/docs/ecosystem/HUMMBL_CHRONOLOGY_TO_NARRATIVE_MAP.md`
- `hummbl-governance/docs/ecosystem/VALIDATION_PASS_1_SUMMARY_2026-06-24.md`
- `hummbl-governance/CANONICAL.md`
- `hummbl-governance/hummbl-governance/docs/blog/agent-governance-gap-2026-05-06.md`
- `hummbl-governance/hummbl-governance/docs/proposals/CONTENT_EXECUTION_PACKET_2026-05-06.md`
- `hummbl-governance/hummbl-governance/docs/research/claim-radar/2026-05-26/CLAIM_RADAR_OPERATING_MODEL.md`
- `hummbl-governance/hummbl-governance/docs/research/evidence/2026-06-06_opus_devin_medical_claim_registry.md`
- `arbiter/src/arbiter/promotion_safety.py`
- `arbiter/tests/test_promotion_safety.py`

Issues:

- `https://github.com/hummbl-io/hummbl-governance/issues/158`
- `https://github.com/hummbl-io/hummbl-governance/issues/1190`

## Status Families Must Stay Separate

The inspected material uses at least four different status families. They are
related, but they are not interchangeable.

### Source Evidence Status

Source evidence status describes the evidence basis behind a claim or narrative
candidate. The clearest current vocabulary appears in
`docs/ecosystem/HUMMBL_CHRONOLOGY_TO_NARRATIVE_MAP.md`:

- `validator_backed`
- `source_backed`
- `repo_local_observed`
- `internally_estimated`
- `unproven`
- `quarantined`
- `stale_or_time_sensitive`
- `private_requires_authorization`
- `scratch_context`

These labels control evidence posture and public-use risk. They do not by
themselves promote a term or artifact to canon.

### Claim Reuse Status

Claim reuse status describes whether a claim may be reused internally or
externally. The clearest current vocabulary appears in
`hummbl-governance/hummbl-governance/docs/research/evidence/2026-06-06_opus_devin_medical_claim_registry.md`:

- `usable`
- `internal-only`
- `quarantined`
- `retired`

This family is claim-specific and publication-oriented. It is not the same as
canon promotion status.

### Canon Promotion Status

Canon promotion status describes artifact movement through the CanonRegistry
pipeline in `hummbl-governance`:

- `draft`
- `reviewed`
- `validated`
- `adopted`
- `canonical`
- `deprecated`

`hummbl_governance/kernel/canon_registry.py` enforces D5
`NO_AUTO_PROMOTION` through explicit operator approval. The schema requires
`current_canon_level`, `proposed_canon_level`, `authority`, `evidence`, and
`receipt`.

### Publication / Artifact Promotion Safety Verdict

Publication or artifact promotion safety describes whether an example,
receipt, handoff, issue, PR trace, or workflow can be reused or elevated as an
example. The clearest current vocabulary appears in
`arbiter/src/arbiter/promotion_safety.py`:

- `private`
- `internal-only`
- `redacted-ok`
- `synthetic-required`
- `public-example`
- `canonical-pattern`
- `rejected`

This Arbiter verdict family is not a HUMMBL canon-level family. In particular,
`canonical-pattern` is an artifact-promotion verdict and must not be treated as
equivalent to CanonRegistry `canonical` without explicit review.

## Convention Matrix

| Convention | Repo | Evidence | Current Language | Lifecycle / Status Model | Required Fields | Gates | Safety Stops | Gap / Inconsistency | Candidate Unification Path |
|---|---|---|---|---|---|---|---|---|---|
| Canon promotion registry | `hummbl-governance` | `PRIMITIVES.md`, `canon_registry.py`, `canon_registry.schema.json` | `CanonRegistry`, `NO_AUTO_PROMOTION`, `operator_approval` | `draft`, `reviewed`, `validated`, `adopted`, `canonical`, `deprecated` | `artifact_id`, `artifact_type`, `current_canon_level`, `proposed_canon_level`, `authority`, `evidence`, `receipt` | Sequential transition, operator approval, review for higher levels | Reject D5 violations, missing approver, skipped levels | Schema description says candidate/proposed while `PRIMITIVES.md` says P27 is implemented | Treat as canon-promotion vocabulary, but audit schema/doc status drift before relying on it |
| Source evidence labels | `hummbl-governance` | `HUMMBL_CHRONOLOGY_TO_NARRATIVE_MAP.md` | `validator_backed`, `source_backed`, `repo_local_observed`, `unproven`, `quarantined`, etc. | Evidence posture and public-risk labels | Evidence label, basis, public-claim risk in examples | Public use requires evidence freshness, citation, review, and wording caveats | `unproven`, `quarantined`, stale/time-sensitive, private/consent-gated claims | Labels are advisory prose, not a shared schema | Map to claim-ledger fields without replacing CanonRegistry levels |
| Public-claim validation blockers | `hummbl-governance` | `VALIDATION_PASS_1_SUMMARY_2026-06-24.md` | `over-promoted`, `unproven`, `quarantined`, public-claim ledger | Validation-pass findings and blocker list | Claim IDs, evidence status, remediation requirements | Relabeling, source refresh, stronger evidence, or new source packet | Invalid public copy, unsupported certification/compliance/partner claims | Refers to a public-claim ledger but this pass did not identify one central enforced schema | Convert recurring blocker patterns into advisory checklist first |
| Cross-repo canonical claims registry | `hummbl-governance` | `CANONICAL.md` | `Canonical Claims Registry`, `source`, `appears_in`, `forbidden_pattern` | Active claim drift registry | `id`, `source.repo`, `source.kind`, `source.path`, `source.selector`, `appears_in` | Source-derived values must match referenced appearances | Forbidden phrasings fail regardless of canonical value | Narrow to cross-repo facts and drift checks; not full claim evidence | Reuse for drift checks; do not stretch into full source-ingestion schema |
| Source packet and publication claim ledger | `hummbl-governance` | `agent-governance-gap-2026-05-06.md`, `CONTENT_EXECUTION_PACKET_2026-05-06.md` | `source_packet`, `claim_status`, every external content piece gets a claim ledger | Draft publication readiness and claim refresh windows | Claim, source, status before publication; source class; claim type | External use requires current claim ledger and source refresh | Repo/package/bus/vendor/model/product metrics expire after seven days; regulatory claims expire after 30 days or rulemaking milestone | Strong convention, but implemented as docs/prose rather than reusable schema | Derive advisory minimum fields for source packets and claim ledgers |
| Claim Radar schema | `hummbl-governance` | `CLAIM_RADAR_OPERATING_MODEL.md` | `Claim Ledger Schema` | Source triage and research claim lifecycle | `claim_id`, `source_url`, `source_type`, `speaker_or_author`, `timestamp_or_location`, `hypothesis`, `falsifiable`, `evidence_needed`, `status`, `next_review_date`, `decision` | Required fields before adoption or promotion | Reject low-value candidates with no mechanism, falsifiability, or evidence path | Prose schema; no JSON schema or validator inspected | Use as the best current field source for advisory ledger shape |
| Quarantined claim registry | `hummbl-governance` | `2026-06-06_opus_devin_medical_claim_registry.md` | `usable`, `internal-only`, `quarantined`, `retired` | Claim-specific reuse status | Claim ID, status, claim, source, allowed use, caveat | Quarantined claims require new source packet before promotion | Do not use quarantined claims as assertions | Vocabulary differs from governance evidence labels | Map `quarantined` consistently; preserve repo-specific labels until approved |
| Promotion safety rubric | `arbiter` | `promotion_safety.py`, `test_promotion_safety.py` | `PromotionVerdict`, `HARD_STOP_DIMENSIONS`, `PUBLIC_EXAMPLE`, `CANONICAL_PATTERN` | Publication/artifact promotion verdicts | Artifact ID/type, dimension scores, redactions, notes, reviewer | Complete hard-stop coverage before public/canonical verdicts | Secrets and personal data are hard stops; hard-stop failures reject | `canonical-pattern` can be confused with CanonRegistry `canonical` | Treat as publication-safety overlay, not canon promotion |
| Advisory issue scope | `hummbl-governance`, `hummbl-governance` | `hummbl-governance#158`, `hummbl-governance#1190` | advisory schemas, fixtures, docs, crosswalks, receipts | Issue-scoped advisory / fixture-only lane | Verified facts, hypotheses, residual risk, next gate | Separate human gate before promotion or implementation | No production, MCP/server, CI behavior, repo settings, public claims, canonization, release, merge | Authorizes docs, but not durable canon | Keep this document advisory until explicit promotion review |

## Do Not Introduce Without Approval

Do not introduce any of the following as repo conventions, schema fields,
approved labels, or canonical vocabulary without explicit operator approval and
the appropriate repo-local governance path:

- Exact snake_case aliases such as `do_not_infer` or `sealed_canon`.
- New CanonRegistry levels beyond the inspected set:
  `draft`, `reviewed`, `validated`, `adopted`, `canonical`, `deprecated`.
- New HUMMBL governance primitive names or primitive IDs.
- New public or canonical terminology that appears to ratify external source
  vocabulary, product claims, model claims, medical/health claims, compliance
  claims, partner/customer claims, production status, certification status, or
  release status.
- Treating Arbiter `canonical-pattern` as equivalent to CanonRegistry
  `canonical`.
- Treating issue-body "Do not infer" text as a machine-schema field name.

## Known Gaps

1. The preferred advisory path `docs/advisory/` does not currently exist in
   `hummbl-governance`; this draft lives under `docs/ecosystem/` as the nearest
   inspected docs directory for source/evidence convention material.
2. `hummbl_governance/data/canon_registry.schema.json` describes P27 as
   proposed/not-yet-implemented, while `PRIMITIVES.md` describes P27 as
   implemented. That status drift should be reconciled before relying on the
   schema description as current truth.
3. Source evidence status, claim reuse status, canon promotion status, and
   publication/artifact promotion verdicts are all useful, but currently live
   in separate repos and are not unified by one schema.
4. `hummbl-governance` claim-ledger conventions are rich but mostly prose or
   document-frontmatter conventions in the inspected material.
5. `arbiter` promotion safety is implemented as code and tests, but it governs
   artifact reuse/publication safety, not source-ingestion evidence maturity.
6. This pass inspected `hummbl-governance#158` and `hummbl-governance#1190`; it did
   not separately verify `hummbl-agent#219` because this document is scoped to
   source-ingestion and claim-governance conventions.
7. No central `source_packet` JSON schema, claim-ledger JSON schema, or
   cross-repo source-ingestion validator was identified in this pass.

## Candidate Future Work

This section is non-authoritative and does not approve implementation.

1. Draft a shared, advisory-only field map that links source evidence labels,
   claim reuse statuses, CanonRegistry levels, and Arbiter publication verdicts
   without collapsing them into one enum.
2. Create sample fixtures only after explicit approval, with one valid source
   packet, one valid claim ledger row, and one adversarial example for
   quarantined or stale claims.
3. Reconcile CanonRegistry schema-description status with `PRIMITIVES.md`.
4. Evaluate whether `hummbl-governance` Claim Radar fields should become a reusable
   schema, remain prose guidance, or be mirrored into `hummbl-governance`.
5. Evaluate whether Arbiter promotion safety should consume claim-ledger status
   as an input dimension rather than defining source maturity itself.
6. If a machine-readable convention is later approved, keep it additive and
   advisory first; do not wire it into CI, MCP servers, production behavior, or
   canon gates without a separate human gate.

## Next Gate

Review this advisory map against `hummbl-governance#158` acceptance criteria.
Any schema edit, code edit, test edit, CI enforcement, issue comment, PR,
MCP/server change, public claim, durable canonization, release, deployment,
merge, or repo setting change requires separate operator approval.
