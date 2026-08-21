# PR Identity Integrity Gate

Status: candidate gate definition for issue #265.
Last updated: 2026-07-19.

This document is public-safe governance language. It does not encode private
topology, secrets, account internals, private host identifiers, or live
connector implementation details.

## Purpose

This gate prevents a recurring cross-repository failure mode: long-lived or
reused branches can accumulate unrelated changes while the PR title,
description, linked issue claims, and review history continue to describe an
earlier change set. Mechanical mergeability is insufficient when the current
head diff no longer represents the declared unit of work.

The gate distinguishes **mechanical mergeability** (GitHub reports the branch
is mergeable, checks pass) from **reviewable scope integrity** (the live diff,
title, body, and closure claims all describe the same unit of work).

## Invariant

Before review approval, merge recommendation, or automated action, the
reviewer or agent MUST verify all five identity-alignment conditions:

1. **Live head diff matches the PR title.** The files and semantic content of
   the diff fall within the scope the title declares.
2. **PR body accurately describes the live diff.** The body is not stale,
   referencing dropped files or removed scope.
3. **Linked issues and `Closes` claims are satisfied by the live diff.** A
   `Closes #N` claim is invalid if the satisfying changes are no longer in the
   diff.
4. **No unrelated remediation, generated files, CI migrations, or stacked
   work.** The branch carries only the declared unit of work.
5. **Validation evidence was produced against the current head SHA.** Stale
   review evidence from an earlier SHA does not satisfy the gate.

A violation of any condition is a **semantic identity failure**, not ordinary
scope creep.

## Required Controls

### Revalidation Triggers

Revalidation is required after any of the following events:

- Material branch rewrite or force-push.
- Rebase onto a moved base branch.
- Merge from another feature branch.
- Agent handoff (the receiving agent must revalidate before recommending
  merge).
- Any commit that adds or removes files outside the declared scope.
- Any commit that changes the PR head SHA, including ordinary in-scope
  commits. The reviewer must capture the head SHA before fetching the
  diff, verify it remains unchanged after diff retrieval, and record
  that exact validated SHA in the review record.

### Disposition on Mismatch

When a material mismatch is detected, the reviewer or agent MUST produce one
of the following dispositions:

| Disposition | Meaning | Required Action |
|---|---|---|
| `HOLD_RECONSTRUCT_OR_SUPERSEDE` | The PR cannot be reviewed as-is. | Close the PR or hold it open as evidence. Create a clean replacement PR from current main with a title matching the live diff. |
| `HOLD_REVIEW_BODY_UPDATE` | The diff is correct but the body/title is stale. | Update the PR title and body to match the live diff. Remove invalid `Closes` claims. Re-request review. |
| `HOLD_SPLIT_SCOPE` | The diff contains multiple unrelated units of work. | Split into separate PRs. Close the contaminated PR or hold as evidence. |

The default disposition for any mismatch is `HOLD_RECONSTRUCT_OR_SUPERSEDE`.
The less restrictive dispositions require explicit justification in the review
record.

### Contaminated PR Preservation

Contaminated PRs must NOT be force-pushed or history-rewritten to make them
appear clean. The contaminated state is evidence of the failure mode and may
be needed for:

- Postmortem analysis.
- Governance audit trails.
- Pattern detection across the fleet.

Close the PR with a supersession link and create a clean replacement. Do not
rewrite the branch.

### Supersession Links

When a stale PR is closed as superseded, the closure comment MUST include
machine-readable receipt metadata with the following fields:

| Field | Description | Required |
|---|---|---|
| `old_ref` | The superseded PR, commit, or issue reference (e.g. `#123`, `abc1234`) | yes |
| `new_ref` | The replacement PR, commit, or issue reference | yes if replacement exists |
| `relationship` | One of: `superseded_by_pr`, `superseded_by_commit`, `already_in_main`, `withdrawn` | yes |
| `reason` | One-line description of the identity failure | yes |

For replacement by a new PR:

```
Superseded by #<replacement-pr-number>.
old_ref: #<stale-pr-number>
new_ref: #<replacement-pr-number>
relationship: superseded_by_pr
reason: <one-line description of the identity failure>.
```

If no replacement is needed (the change already exists in main):

```
Superseded — change already present in main.
old_ref: #<stale-pr-number>
new_ref: <commit-sha-in-main>
relationship: already_in_main
reason: <one-line description>.
```

If the change is withdrawn without replacement:

```
Withdrawn — no replacement.
old_ref: #<stale-pr-number>
new_ref: none
relationship: withdrawn
reason: <one-line description>.
```

### Stale `Closes` Claims

A `Closes #N` claim that survives after the satisfying changes disappear from
the diff is a violation of condition 3. The claim MUST be removed or
justified before merge. If the issue is still open and the PR no longer
satisfies it, the `Closes` claim is invalid and must be dropped.

### High-Risk PR Segregation

Security-, authority-, governance-, and publication-sensitive PRs MUST NOT
mix unrelated CI migrations, infrastructure changes, or generated-file
commits. These PRs require a single, narrowly scoped diff that can be
audited independently. If a CI migration is needed alongside a security
change, it MUST be a separate PR.

## Review Template

Reviewers and agents MUST confirm the following before approving:

```
## PR Identity Integrity Check

- [ ] Head SHA reviewed: <sha>
- [ ] Title matches live diff
- [ ] Body matches live diff
- [ ] Closes/linked-issue claims satisfied by live diff
- [ ] No unrelated scope (CI migrations, generated files, stacked work)
- [ ] Validation evidence produced against current head SHA

Disposition: APPROVE | HOLD_RECONSTRUCT_OR_SUPERSEDE | HOLD_REVIEW_BODY_UPDATE | HOLD_SPLIT_SCOPE
```

## Agent Obligations

Agents performing review or merge recommendation MUST:

1. Capture the current PR head SHA (`gh pr view <number> --json headRefOid`) before fetching the diff.
2. Fetch the live diff (`gh pr diff <number>`) before recommending merge.
3. Verify the head SHA has not changed between capture and diff retrieval (race detection).
4. Compare the diff against the PR title, body, and linked issues.
5. Check for scope creep (files outside the declared unit of work).
6. Produce the disposition from the table above.
7. Post the review template with the exact validated head SHA recorded.

Agents MUST NOT:

- Recommend merge based on mechanical mergeability alone.
- Recommend merge when the title/body/diff are misaligned.
- Force-push or rewrite a contaminated branch to make it appear clean.
- Close a PR without a supersession link if the change is still needed.
- Merge a high-risk PR that mixes security/governance changes with
  infrastructure or CI migrations.

## Policy Authority

This policy does not authorize merging, closing, force-pushing, or rewriting
branches without operator or repository-authorized action. The gate produces
a disposition; the operator or authorized reviewer executes the action.

## Evidence Cases

### Case 1: hummbl-governance #1553

Declared bus-authority remediation with unrelated CI migration and workflow
rewrites in the live diff. The title and body described a bus-authority
change set, but the diff included infrastructure changes belonging to a
separate lane. Disposition: `HOLD_RECONSTRUCT_OR_SUPERSEDE`.

### Case 2: docs #9

Title and body described docs validation and stale-count correction while the
live diff was only a UTF-8 reader fix and regression test. The PR was merged
with the mismatched title. The UTF-8 fix was independently needed and is
present in main. Disposition: resolved (merged, but the identity failure is
documented here as an evidence case).

## Non-Goals

- This gate does not prescribe a specific bot or workflow implementation.
  Automation may follow only after the policy and failure classifications are
  stable.
- This gate does not replace CI status checks, branch protection, or
  code-owner review. It is a semantic layer above mechanical gates.
- This gate does not define what constitutes a "unit of work" — that is
  determined by the PR title and body, which the gate enforces as the
  declared scope.
