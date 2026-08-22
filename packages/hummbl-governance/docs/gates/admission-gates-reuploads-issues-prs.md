# Admission Gates for Reuploads, Issues, and Draft PRs

Status: candidate gate definition for issue #150.
Last updated: 2026-07-03.

This document is public-safe governance language. It does not encode private
topology, secrets, account internals, private host identifiers, or live
connector implementation details. Gate names are candidate unless a later
namespace audit promotes them.

## Purpose

These gates protect three admission surfaces:

1. reuploaded source packs or context bundles;
2. new GitHub issue creation;
3. draft PR promotion.

The goal is to prevent stale authority, duplicate work, unsafe public leakage,
and premature PR promotion while still keeping agent execution fast.

## Opportunity Scan Routing Policy (Read-only Intake)

Opportunity scans are treated as governed proposal intake only. A scan finding
must follow this fixed path:

1. Read-only intake: collect signal and confidence context without any file
   mutation.
2. Duplicate preflight: check `G-NO-DUPLICATE-ISSUE` across open and
   relevant recently closed issues.
3. Queue handoff: create or append to hummbl-governance queue `hummbl-governance#188`.
4. Queue approval: only issues explicitly approved in `#188` may be converted
   to new issue proposals.
5. Proposal only: no direct draft-PR or branch mutation is allowed without
   explicit queue routing and issue admission completion.

Scan handoff is required as a single packet:

```yaml
scan_handoff:
  scan_id: scan-<timestamp>-<slug>
  source: github | web | adapter | local
  target_repo: hummbl-io/<repo>
  hypotheses:
    - <hypothesis-1>
    - <hypothesis-2>
  confidence_signal:
    level: low | medium | high
    basis: <command output | log excerpt | artifact>
  duplicate_preflight:
    query_examples:
      - "repo:hummbl-io/<repo> is:issue \"<signal>\" in:title,body is:open"
      - "repo:hummbl-io/<repo> is:issue \"<signal>\" in:title,body is:closed created:>=YYYY-MM-DD"
    duplicate_status: no direct overlap found
  approved_actions:
    - propose_issue
    - open_queue_comment_in_188
  queue_handoff:
    status: queued
    queue_issue: hummbl-governance#188
    review_required_before_mutation: true
```

Blocks:

- PRs or branch mutation from scan output without explicit queue approval are
  out of scope and must be rejected before mutation.
- Public claims are allowed only if a queue-approved receipt path exists.

## Namespace Audit

Lightweight audit result for this PR: no exact gate-name collisions were found
in the current issue text or docs search for the proposed gate names. The names
remain candidate because this PR does not perform a full repository-wide
namespace ratification.

## Gate Result Values

| Result | Meaning |
|---|---|
| `pass` | Gate evidence is present and reviewable. |
| `warn` | Gate can proceed only with an explicit residual-risk note. |
| `fail` | Admission is blocked until corrected. |
| `waived` | A human-authorized waiver exists with scope, reason, and expiry. |

## Reupload / Source-Pack Admission Gates

| Gate | Purpose | Pass condition | Fail condition | Required evidence | Receipt fields |
|---|---|---|---|---|---|
| `G-SOURCE-OF-RECORD` | Prevent uploaded chat or bundle state from becoming false authority. | Upload names the real upstream source of record and retrieval point. | Upload implies the reupload itself is canonical. | Source URL/path, commit/hash/date, owner of record. | `source_of_record`, `retrieved_at`, `authority_note` |
| `G-SUPERSESSION` | Avoid ambiguous replacement of older packs. | Upload states whether it supersedes, supplements, or only references prior packs. | Prior pack relationship is unstated. | Prior pack IDs or `none`. | `supersedes`, `supersession_scope`, `retained_context` |
| `G-DO-NOT-INFER` | Preserve explicit inference limits. | Upload states what must not be inferred from the pack. | Pack invites broad inference from partial context. | Do-not-infer list. | `do_not_infer`, `known_gaps` |
| `G-REDACTION` | Keep public repo safe. | Secrets, raw private topology, private host identifiers, and account-sensitive data are excluded or redacted. | Sensitive data is present or redaction basis is absent. | Redaction summary and reviewer. | `redaction_status`, `redaction_reviewer`, `sensitive_data_risk` |
| `G-HASHED-MANIFEST` | Preserve integrity and replayability. | File-level hashes or equivalent integrity receipt exist. | Bundle cannot be checked against the uploaded manifest. | Hash manifest, file list, generation command. | `manifest_path`, `hash_algorithm`, `manifest_generated_at` |

## New Issue Admission Gates

| Gate | Purpose | Pass condition | Fail condition | Required evidence | Receipt fields |
|---|---|---|---|---|---|
| `G-NO-DUPLICATE-ISSUE` | Avoid duplicate or superseded work. | Open and recently closed issues were searched with relevant terms. | Equivalent open issue exists or no dedupe search was recorded. | Search terms, repository scope, result summary. | `dedupe_terms`, `dedupe_scope`, `duplicate_status` |
| `G-REPO-OWNER-OF-RECORD` | Route work to the correct repository. | Target repo is selected intentionally and owner-of-record is stated. | Repo selected by vague semantic proximity or convenience. | Repo rationale and owner-of-record note. | `target_repo`, `owner_of_record`, `routing_reason` |
| `G-SCOPE-BOUND` | Prevent issue sprawl. | Issue has explicit in-scope and out-of-scope sections. | Issue asks for broad execution without boundaries. | Scope bullets and non-goals. | `in_scope`, `out_of_scope`, `residual_scope_risk` |
| `G-AGENT-HANDOFF-READY` | Make the issue executable. | Issue includes executor lane, acceptance criteria, and receipt path or expected receipt shape. | No clear acceptance criteria or handoff fields. | Lane, acceptance checks, receipt path. | `executor_lane`, `acceptance_checks`, `receipt_path` |
| `G-NO-SENSITIVE-DATA` | Keep issue bodies public-safe. | Issue body contains no secrets or private operational internals. | Sensitive data appears in the issue body or attachments. | Public-safety review statement. | `public_safe`, `sensitive_data_risk`, `redaction_needed` |

## Draft PR Promotion Gates

| Gate | Purpose | Pass condition | Fail condition | Required evidence | Receipt fields |
|---|---|---|---|---|---|
| `G-ISSUE-ADMITTED` | Keep PRs tied to admitted work. | PR links an admitted issue or records a no-issue exception. | PR has no linked issue and no exception. | Issue number or exception reason. | `linked_issue`, `issue_admitted`, `exception_reason` |
| `G-BRANCH-SAFETY` | Prevent direct default-branch mutation. | Work occurs on a non-default branch with bounded branch name. | Work is on `main` or an ambiguous branch. | Branch name and base. | `branch`, `base_branch`, `default_branch_mutation` |
| `G-LOCAL-VALIDATION` | Avoid review without basic checks. | Tests, lint, schema, diff check, or no-test reason is recorded. | Validation omitted without reason. | Commands and results. | `validation_commands`, `validation_result`, `no_test_reason` |
| `G-DIFF-SCOPE` | Keep review tractable. | Diff is bounded to the issue and excludes unrelated local changes. | Diff includes unrelated files or hidden scope expansion. | Changed-file list and scope note. | `changed_files`, `scope_summary`, `unrelated_changes_excluded` |
| `G-REVIEW-CAPACITY` | Prevent review queue overload. | Promotion considers current open PR and review-comment state. | PR is promoted despite known review bottleneck or unresolved blocking comments. | Queue snapshot and reviewer route. | `review_queue_snapshot`, `reviewer_route`, `capacity_risk` |
| `G-RECEIPT-WRITTEN` | Preserve auditability. | Command/result/commit/residual-risk receipt exists or is included in PR body. | No durable receipt for the promotion. | Receipt path or PR-body receipt. | `receipt_location`, `commit_sha`, `residual_risk` |

## Valid Issue Admission Packet Example

```yaml
issue_admission:
  target_repo: hummbl-io/hummbl-governance
  owner_of_record: governance
  title: Define public-safe admission gates for draft PR promotion
  dedupe_terms:
    - admission gate
    - draft PR promotion
    - reupload source pack
  duplicate_status: no direct duplicate found
  in_scope:
    - gate semantics
    - pass/fail evidence fields
    - public-safe receipt shape
  out_of_scope:
    - connector implementation
    - private topology
    - live automation enforcement
  executor_lane: docs/codex
  acceptance_checks:
    - gate table exists
    - valid and rejected fixtures exist
    - receipt records namespace status
  receipt_path: docs/receipts/admission-gates-reuploads-issues-prs-2026-07-03.md
  public_safe: true
```

Gate outcome: `pass` for issue creation.

## Rejected Packet Example

```yaml
issue_admission:
  target_repo: hummbl-io/hummbl-governance
  title: Upload the whole private machine context and make PRs
  dedupe_terms: []
  duplicate_status: not_checked
  in_scope: []
  out_of_scope: []
  executor_lane: unspecified
  acceptance_checks: []
  receipt_path: ""
  public_safe: false
  sensitive_data_risk: raw private topology and account internals included
```

Gate outcome: `fail`.

Failure reasons:

- `G-NO-DUPLICATE-ISSUE`: no dedupe evidence.
- `G-SCOPE-BOUND`: no in-scope or out-of-scope boundary.
- `G-AGENT-HANDOFF-READY`: no executor lane or acceptance checks.
- `G-NO-SENSITIVE-DATA`: private operational internals are present.

## Draft PR Promotion Receipt Shape

```yaml
draft_pr_promotion:
  linked_issue:
  branch:
  base_branch:
  changed_files:
  validation_commands:
  validation_result:
  first_review_comment:
  promoted_from_draft_at:
  reviewer_route:
  receipt_location:
  residual_risk:
```

## Residual Risks

- These gates are definitions only; this PR does not add a validator or bot.
- Review capacity remains a human and queue-management problem until automated
  queue receipts exist.
- Namespace status remains candidate until a full namespace audit is recorded.
- Private connector implementations must import these gates without copying
  sensitive private context into public repo artifacts.
