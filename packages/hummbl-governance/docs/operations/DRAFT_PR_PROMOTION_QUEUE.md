# Draft PR Promotion Queue

Status: active operations policy
Source issue: https://github.com/hummbl-io/hummbl-governance/issues/188
Last updated: 2026-07-04

## Purpose

The Draft PR Promotion Queue controls when open HUMMBL public-repo issues may
be converted into draft pull requests. It prevents draft creation from becoming
review debt, public-claim drift, or premature canonization.

Issue #188 remains the live queue ledger for dated promotion passes. This file
is the stable policy and template artifact for agents and reviewers.

## Scope

Use this policy for public or write-safe HUMMBL repositories when an issue may
be promoted into a draft PR. Private repositories may be considered only with
explicit authorization, and private details must not be copied into public queue
comments.

Initial public/write-safe repositories:

- `hummbl-io/hummbl-governance`
- `hummbl-io/hummbl-agent`
- `hummbl-io/arbiter`
- `hummbl-io/mcp-server`

## Daily Limits

- Open at most 2 new draft PRs per calendar day.
- Add PR-ready packet comments to at most 3 issues per promotion pass.
- Score at most 5 candidate issues per promotion pass.
- Move 0-1 existing draft PRs to ready for review only after scope, checks, and
  receipts are clean.
- Merge 0-1 PRs only after normal review, CI, and governance gates pass.

A new draft PR counts against the daily cap when it is opened, regardless of
whether it is docs-only, schema-only, fixture-only, CI-only, or runtime-facing.

## Promotion Rhythm

Each promotion pass should:

1. Review candidate open issues across confirmed write-safe repositories.
2. Run a duplicate and supersession check before creating a PR.
3. Score at most 5 issues with the rubric below.
4. Add PR-ready packet comments to at most 3 issues.
5. Open at most 2 new draft PRs.
6. Leave broad issues open unless a PR fully satisfies all acceptance criteria.
7. Record the pass as a comment on issue #188.

## Readiness Scoring

| Factor | Weight | Good signal |
|---|---:|---|
| Acceptance criteria clarity | 25 | Exact files, tests, or outcomes are named |
| Public-safety / privacy boundary | 20 | No secrets, private topology, raw account data, or private paths |
| Reversibility | 15 | Docs, schemas, fixtures, or tests before runtime mutation |
| Blast radius | 15 | Small diff; no release, deploy, or CI mutation unless explicitly approved |
| Validation path | 15 | Test, lint, grep, or review command is named |
| Review capacity | 10 | Reviewer, bot, human, or peer-review lane is identified |

Promotion thresholds:

- `80-100`: ready for a draft PR.
- `60-79`: add or refine the PR-ready packet; keep the issue open.
- `<60`: refine the issue before PR work.

## PR-Ready Packet

Before opening a draft PR, post a comment on the source issue using this shape:

```md
## PR-ready packet

Promotion status: READY_FOR_DRAFT_PR
Promotion date:
Promoter:
Readiness score:

Scope:
- Files expected to change:
- Files explicitly out of scope:
- Change class: docs / schema / fixture / test / CI / runtime
- Public/private boundary:
- Canon status:
- Human approval required before:

Acceptance checks:
- [ ] Duplicate/supersession check complete
- [ ] Redaction/sensitive-info check complete
- [ ] Local validation command listed
- [ ] PR body must link this issue
- [ ] PR must open as draft
```

## Draft Defaults

Default to draft PRs for issues touching:

- governance
- public claims
- schemas
- source-candidate handling
- issue or PR templates
- package metadata
- security posture
- CI or release surfaces
- agent runtime or tool execution
- Arbiter scoring behavior
- canon-adjacent language

Tiny docs hygiene fixes may skip draft only when they are explicitly small,
reversible, and non-canon.

## Closing Discipline

Use `Refs #issue` for partial PRs.

Use `Closes #issue` only when the PR satisfies the full acceptance criteria of
the issue.

For broad issues, prefer sliced PRs:

1. docs scaffold
2. source packet
3. schema
4. fixtures
5. tests
6. integration
7. public-surface update after receipts

## Queue Entry Template

Add one comment per daily promotion pass on issue #188:

```md
## Draft PR Promotion Queue -- YYYY-MM-DD

Daily cap: 0/2 new draft PRs opened

### Candidates scored

| Repo | Issue | Score | Decision | Notes |
|---|---:|---:|---|---|
| owner/repo | #123 | 85 | READY_FOR_DRAFT_PR | small docs/schema slice |

### PR-ready packets added

- [ ] owner/repo#123

### Draft PRs opened today

- [ ] owner/repo#456 -- draft -- refs #123

### Blocked / defer

- owner/repo#789 -- blocked by scope / missing validation / review capacity / private-boundary risk

### Carry forward

- owner/repo#...
```

## Guardrails

- Do not open more than 2 new draft PRs per calendar day unless Reuben
  explicitly overrides the cap.
- Do not treat draft PR creation as approval to merge.
- Do not treat issue approval as canonization.
- Do not publish or strengthen public claims without receipts.
- Do not include secrets, private topology, account details, private repo
  contents, or private health/operator details in public issues or PRs.
- Do not assign reviewers reflexively; request review only when the PR is ready
  for that reviewer lane.
- Do not move a promotion packet PR to ready for review unless it has been
  replaced by the actual implementation or queue artifact.

## Validation

For docs-only queue updates, use:

```bash
python scripts/issue_pr_draft_coverage.py --repo hummbl-io/hummbl-governance --json
python scripts/pr_census.py
```

For PR body or template edits, also verify GitHub rendering and public/private
boundary language before requesting review.
