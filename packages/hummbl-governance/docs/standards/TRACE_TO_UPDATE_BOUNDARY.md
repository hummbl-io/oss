# Trace-to-Update Boundary Standard

Status: draft standard for issue #165.
Last updated: 2026-07-03.

## Purpose

Operational traces can become valuable evidence, memory, evals, adapters, or
fine-tune candidates. They also can contain private, tenant, health, mission,
or legally constrained data. Trace reuse is therefore denied by default unless
the trace passes a declared boundary model.

This standard answers:

> When, if ever, may an operational trace become a durable model or system
> update?

## Candidate Primitive: Weight-Update Boundary

The `Weight-Update Boundary` is a governance boundary that classifies an
operational trace before it moves beyond raw log status. It decides whether a
trace may be:

- retained as raw or redacted evidence,
- summarized into memory,
- converted into an eval,
- proposed as an adapter or fine-tune candidate,
- shared across users, tenants, contracts, or missions,
- discarded or made non-retainable.

Default posture: no trace may update memory, evals, adapters, fine-tunes, or
shared model behavior until the boundary emits an audit receipt.

## Candidate Doctrine: Consent-Bounded Continual Learning

Personalization may improve from user-specific experience only inside declared
user or tenant boundaries. Any transition from trace to durable learning
artifact requires:

- consent state that permits the specific reuse,
- source and tenant boundary classification,
- deletion and revocation semantics,
- privacy and health-data review where applicable,
- auditability from source trace to update candidate,
- human review when the trace is regulated, high sensitivity, cross-boundary, or
  non-replayable.

Redaction is a control, not authorization. A redacted trace still needs a
permitted lifecycle transition.

## Required Classification Fields

Every trace promotion decision must classify these axes:

| Field | Allowed values |
|---|---|
| `source_type` | `public`, `private`, `tenant`, `health`, `federal_defense`, `repo`, `synthetic`, `benchmark` |
| `consent_state` | `explicit`, `implied`, `absent`, `revoked`, `not_applicable` |
| `privacy_sensitivity` | `low`, `medium`, `high`, `regulated` |
| `tenant_boundary` | `single_user`, `org`, `cross_org`, `public` |
| `trace_state` | `raw`, `redacted`, `summarized`, `eval`, `memory`, `adapter_candidate`, `fine_tune_candidate`, `discarded` |
| `replayability` | `deterministic`, `partial`, `non_replayable`, `reset_free` |
| `deletion_obligation` | `none`, `user_delete`, `tenant_delete`, `legal_hold`, `retention_required` |
| `update_allowed` | `none`, `memory_only`, `eval_only`, `adapter_candidate`, `fine_tune_candidate`, `shared_update_candidate` |
| `human_review_required` | `true`, `false` |
| `audit_receipt_required` | `true`, `false` |

## Allowed Lifecycle Transitions

Allowed transitions are narrow and evidence-bearing:

| From | To | Minimum gate |
|---|---|---|
| `raw` | `redacted` | classification receipt and redaction method |
| `raw` | `discarded` | deletion or non-retention receipt |
| `redacted` | `summarized` | consent compatible with summary retention |
| `redacted` | `eval` | eval purpose, replayability, and boundary review |
| `summarized` | `memory` | user or tenant-scoped consent and deletion semantics |
| `eval` | `adapter_candidate` | human review, source trace lineage, and no prohibited boundary crossing |
| `eval` | `fine_tune_candidate` | explicit consent, human review, deletion plan, and release gate |
| `adapter_candidate` | `fine_tune_candidate` | separate promotion review and artifact lineage receipt |

No transition implies the next transition. For example, `redacted -> eval` does
not authorize `eval -> fine_tune_candidate`.

## Prohibited Transitions

These transitions are prohibited unless a future operator-approved standard
explicitly creates a narrower exception:

- `raw -> memory`
- `raw -> eval`
- `raw -> adapter_candidate`
- `raw -> fine_tune_candidate`
- `raw -> shared_update_candidate`
- `private -> cross_org` without explicit consent and tenant review
- `tenant -> public` without explicit release approval
- `health -> shared_update_candidate`
- `federal_defense -> cross_org`
- any trace with `consent_state=revoked` to any retained learning artifact
- any trace under `legal_hold` to mutation or deletion without legal review
- any `non_replayable` or `reset_free` trace to eval without human review

## Deletion and Revocation Behavior

Deletion and revocation must follow the artifact form:

- Raw trace: delete or quarantine the original record unless retention is
  legally required.
- Redacted trace: delete both source and derivative unless the redacted
  derivative has its own retention basis.
- Summary memory: remove the memory item, invalidate references, and preserve a
  deletion receipt.
- Eval: disable the eval case until source consent and retention are restored or
  the eval is regenerated from a permitted synthetic fixture.
- Adapter candidate: halt promotion, remove candidate artifacts, and preserve
  lineage evidence for audit.
- Fine-tune candidate: halt training/release, quarantine candidate datasets,
  and require human review before any derivative is retained.
- Published model update: this standard does not authorize rollback by itself;
  escalation must use release, legal, and incident-response governance.

Deletion receipts must identify what was deleted, what could not be deleted,
why, and which downstream artifacts were invalidated.

## Minimum Audit Receipt Fields

Any promotion beyond raw log status requires an audit receipt with:

- `trace_id`
- `source_type`
- `consent_state`
- `privacy_sensitivity`
- `tenant_boundary`
- `from_state`
- `to_state`
- `update_allowed`
- `deletion_obligation`
- `replayability`
- `human_reviewer` or `not_required_reason`
- `evidence_refs`
- `redaction_method` when applicable
- `retention_basis`
- `downstream_artifacts`
- `rollback_or_deletion_plan`
- `decision`
- `timestamp`

## Ownward Health / Executive Context Gate

Ownward executive health coaching data is sensitive by default.

Minimum gate:

- classify as `source_type=health`,
- require explicit consent for any durable memory,
- prohibit shared training, shared fine-tuning, and cross-user updates by
  default,
- require user or tenant deletion semantics before retention,
- require health-data review before eval, adapter, or fine-tune candidacy,
- keep source receipts scoped to the user or tenant boundary.

## Federal / Defense Mission Gate

Federal and defense mission traces are mission-bound by default.

Minimum gate:

- classify as `source_type=federal_defense`,
- prohibit reuse across contracts, tenants, missions, clearance boundaries, or
  public artifacts unless explicitly authorized,
- prefer synthetic or fixture alternatives for replayable evals,
- preserve evidence chains for mission/eval replay,
- require human review for any transition beyond redaction,
- require separate authorization before adapter, fine-tune, or shared update
  candidacy.

## Cross-Repository Links

- Source packet PR: `hummbl-io/<private-repo>#579`
- Model Router v2 grindability/learnability routing: `hummbl-io/<private-repo>#580`
- Founder Mode ops traces as organizational learning substrate:
  `hummbl-io/hummbl-governance#1204`
- Runtime/event-ledger adjacent lane: `hummbl-io/hummbl-governance#158`

## Non-Inference Rules

- Operational traces do not train models by default.
- Redaction alone is not sufficient for reuse.
- Context summaries do not automatically satisfy deletion rights.
- Eval conversion is not automatically safe.
- Public source-candidate analysis does not authorize private-data reuse.

