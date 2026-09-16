# hummbl-io PR Audit — 2026-09-15

**Scope:** all open pull requests across the `hummbl-io` GitHub organization.
**Repositories audited:** `hummbl-io/oss` (HUMMBL open-source monorepo), `hummbl-io/nakedagent`.
**Method:** each open PR inspected for title, body, diff, commits, CI check runs, combined commit status, and mergeable state.
**Author of audit:** Vibe Code agent.
**Tracking issues opened:** hummbl-io/oss#239, #240, #241.
**Review comments posted:** one per audited PR (oss#233, #234, #235, #236, #237, #225; nakedagent#1).

---

## 1. Summary

The org has **7 open PRs** across 2 repositories. All are authored by `hummbl-dev` except two Dependabot dependency bumps.

| # | Repo | Title | Author | State | CI (`ci-ok`) | Mergeable | Risk |
|---|------|-------|--------|-------|-------------|-----------|------|
| 233 | oss | chore(deps): ruff 0.16.6 → 0.16.7 | dependabot | open | green | behind | Low |
| 234 | oss | chore(deps): codeql-action 4.37.9 → 4.38.0 | dependabot | open | green | blocked | Low |
| 235 | oss | ci: gate test-preview to push-only (−46 jobs/PR) | hummbl-dev | open | green | behind | Low-Med |
| 236 | oss | feat(cognition): enforce SKILL_INVOKE provenance at ledger write path | hummbl-dev | open | green (249 checks) | behind | **Med** |
| 237 | oss | Promote all bus agents to TRUSTED in authority_policy.json | hummbl-dev | open | green (248 checks) | behind | **Med-High** |
| 225 | oss | fix(hummbl-mcp-utf): align embedded operator table with Base120 registry | hummbl-dev | open | stale | dirty | Low-Med |
| 1 | nakedagent | fix: disable Ollama thinking, isolate plugin tests, correct license docs | hummbl-dev | open | no checks | dirty | Low-Med |

**Headline findings:**

1. **No recorded non-author reviews on any PR** — see issue #239. The org's own PR review protocol mandates non-author review for foundation/policy/security changes; several PRs explicitly request it.
2. **The Devin "Review" status is non-functional** — see issue #240. Every PR's combined commit *status* is just the Devin bot reporting "trial expired, no credits remaining". The real test signal lives in *check runs* (`ci-ok`), which are green for the PRs that have CI. Branch protection should depend on `ci-ok`, not the Devin status.
3. **#236 bundles unrelated commits** — see issue #241. The provenance-enforcement PR carries two separate feature commits that should be split out.

---

## 2. Per-PR findings

### 2.1 oss#233 — ruff dependency bump (Low)

**PR:** https://github.com/hummbl-io/oss/pull/233
**Diff:** `governed-compression/pyproject.toml` (`ruff>=0.16.6` → `ruff>=0.16.7`) + regenerated `requirements-build.lock`. +28/−87, 2 files.

Trivial test-dependency version bump. The lockfile diff also drops many `# via` provenance comments — incidental lockfile-tooling churn, not a blocker, but it enlarges the diff. `mergeable_state: behind`.

**Recommendation:** rebase + merge. Safe.

### 2.2 oss#234 — codeql-action bump (Low)

**PR:** https://github.com/hummbl-io/oss/pull/234
**Diff:** `.github/workflows/codeql.yml` — bumps `github/codeql-action/init` and `analyze` from SHA `cdf488f…` (v4.37.9) to `b96794f…` (v4.38.0). +2/−2, 1 file.

Correct SHA-pinning pattern, consistent with the repo's existing security-tooling conventions. The new SHA matches the upstream v4.38.0 release tag. `mergeable_state: blocked`.

**Recommendation:** resolve the blocker (likely overlap with the `ci.yml` change in #235; land #235 first then rebase), then merge. Safe security-tooling update.

### 2.3 oss#235 — gate test-preview to push-only (Low-Med)

**PR:** https://github.com/hummbl-io/oss/pull/235
**Diff:** `.github/workflows/ci.yml` — adds `if: github.event_name != 'pull_request'` to the `test-preview` job. +3, 1 file.

The change is sound: `test-preview` (Python 3.15-dev matrix, ~46 jobs) is `continue-on-error: true` and `ci-ok` already skips checking its result, so it was 46 informational jobs running on every PR that never block merges. Gating to push-only preserves full preview coverage on `main` while cutting per-PR fan-out.

**Tradeoff:** Python 3.15-dev breakages will now surface only on push-to-main, not in PR feedback. Acceptable, but worth a scheduled `workflow_dispatch` run to keep 3.15-dev coverage visible between pushes. Body claim (~245 → ~199 jobs/PR) is plausible. `mergeable_state: behind`.

**Recommendation:** rebase + merge. Consider adding a scheduled `workflow_dispatch` cadence for `test-preview`.

### 2.4 oss#236 — cognition provenance enforcement (Med) ⚠️

**PR:** https://github.com/hummbl-io/oss/pull/236
**Commits:** 6 (4 provenance + 2 unrelated — see below). +865/−4, 8 files.

**Core change:** `ledger_writer.append_entry` now enforces that a `SKILL_INVOKE` bus receipt from the same agent exists within a 300-second window, **default-on**. The CLI flag flips from opt-in `--require-skill-invoke` to opt-out `--no-skill-invoke-check`; `--agent` is now required (no silent `unknown` default). 8 new tests added; full `hummbl-governance` suite reports 3499–3500 passed.

This is a **behavioral default-change** on a governance write path. Even with the backward-compat escape hatch and passing tests, flipping an enforcement gate from opt-in to default-on can break existing callers that don't emit `SKILL_INVOKE` before writing.

**Scope creep (issue #241):** the branch carries two commits that are not part of the provenance work and will merge alongside it:
- `b8128b6` — feat(hummbl-governance): add cogstate, health CLI, and google_calendar stub (3 new stdlib modules referenced by ~21 skills)
- `1c3017e` — feat(hummbl-cognition): add repair_chain script for hash chain repair (reduces a 2003-entry ledger's errors from 1816 to 14)

These are independent features with their own rationale (memory-infrastructure P0 #1 and #2). Bundling them obscures the diff and ties their fate to the riskier provenance change.

**Recommendation:**
1. Request the non-author review the body explicitly asks for.
2. Split `b8128b6` and `1c3017e` onto fresh branches as separate PRs, leaving #236 with only the 4 provenance commits.
3. Confirm no production ledger writer relies on the old default-off behavior; add a migration note if any does.
4. Rebase (`mergeable_state: behind`), then merge.

### 2.5 oss#237 — trust promotion (Med-High) ⚠️

**PR:** https://github.com/hummbl-io/oss/pull/237
**Diff:** `authority_policy.json` + `docs/artifacts/PLAYBOOK_agent_onboarding.md`. +22/−23, 2 files.

**Change:** promotes 8 bus agents to **TRUSTED** in `authority_policy.json`, per the 2026-09-15 operator directive:
- `devin`, `opencode`, `apex`, `nexus`, `pi`: MEDIUM-HIGH → TRUSTED
- `kai`, `agy`: MEDIUM → TRUSTED
- `gemini`: PROBATIONARY → TRUSTED

Revocation language is updated ("AIP strips scope, not trust; trust remains TRUSTED for bus agents"). Companion PRs: `hummbl-io/agents#259`, `hummbl-io/hummbl-production#1261`.

**Assessment:**
- Diff is clean and scoped: tier values + revocation wording + onboarding playbook. The general-purpose tier ladder in `identity_engine.py` / `trust_adjuster.py` / `trust_adjuster.schema.json` is intentionally left intact — correct.
- `arcana-advisory` correctly stays MEDIUM (not a bus agent) — correct.
- 248 checks green, `ci-ok` success.
- Non-normative whitespace/quote normalization in the JSON is incidental.

**Risk to verify before merge:** the `auto_revocation` triggers still reference tier-stepping ("HIGH severity violation → 3 trust tier steps down"). For agents whose only tier is now TRUSTED, there is no MEDIUM-HIGH/MEDIUM to step through — confirm the revocation path behaves as intended (likely jumps straight to RETIRED) rather than no-opping. A regression test is warranted.

**Recommendation:** do not merge until (1) non-author review is recorded (body flags it pending), (2) the two companion PRs are aligned, and (3) the auto-revocation tier-step behavior for TRUSTED-only agents is confirmed. Rebase (`mergeable_state: behind`).

### 2.6 oss#225 — mcp-utf operator table (Low-Med)

**PR:** https://github.com/hummbl-io/oss/pull/225
**Diff:** `packages/python/hummbl-mcp-utf/mcp_server.py` — regenerates the embedded `FAMILIES`/`models` table (120 entries) from the canonical `base120/data/operators.json`, and renames the SY family `Meta-Systems` → `Systems`. +123/−123, 1 file.

The embedded table had a pre-canonicalization model list under canonical operator codes — only ~6/120 entries matched the frozen Base120 registry (e.g. `P3` was "Mental Models" vs canonical "Identity Stack"; `RE17` "Circular Causality" vs "Versioning & Diff"). Regeneration fixes this.

**Concerns:**
- `mergeable_state: dirty` — conflicts with main; needs a rebase.
- Test plan only runs `test_import` (1/1 pass); the "6/120 matched before" claim isn't verified by CI. **A canonical-equivalence test** that asserts the embedded table equals `operators.json` would prevent silent future drift.
- CI is stale (last activity 2026-09-12, ~3 days old).

**Recommendation:** rebase, add a canonical-equivalence test, re-run CI, then re-request review.

### 2.7 nakedagent#1 — Ollama/license fixes (Low-Med)

**PR:** https://github.com/hummbl-io/nakedagent/pull/1
**Diff:** 8 files, +414/−3, 4 commits.

Three fixes in one PR:
1. `"think": false` in `llm.chat` to fix empty replies from thinking-capable Ollama models (e.g. `qwen3.5:9b` returned empty `content`).
2. Plugin test isolation via `Path.home` patching (tests were reading the developer's real `~/.nakedagent/plugins/`).
3. License doc correction: `AGENTS.md` / `SECURITY.md` said Apache 2.0; `LICENSE` / `pyproject.toml` / `README.md` are MIT → corrected to MIT.

Body reports 60 tests pass, including a new `TestThinkingDisabled` regression test.

**Concerns:**
- **No CI runs** — combined status is `pending` with 0 checks. The repo appears to have no CI workflow, so nothing automated validates the PR. A CI workflow (even a single `pytest` job) should be added.
- `mergeable_state: dirty` — rebase needed.
- Body asks for non-author review on the `llm.py` foundation change. The license-doc fix and test isolation are safe; the `llm.py` `"think": false` change deserves the review.

**Recommendation:** rebase, add CI, get non-author review on `llm.py`, then merge.

---

## 3. Cross-cutting issues

Three issues were opened in `hummbl-io/oss` to track findings that span multiple PRs.

### #239 — Non-author reviews missing on open PRs

None of the open PRs have a recorded non-author review approval, despite the org's PR review protocol mandating one for foundation/policy/security changes. PRs #1, #225, #236, #237 explicitly request it. The lower-risk PRs (#233, #234 deps; #235 CI) are low-stakes, but the four flagged PRs are exactly the class the protocol was written for.

**Suggested fix:** block merge on the four flagged PRs until a non-author review is logged; consider a branch-protection rule requiring review approval for paths touching `authority_policy.json`, `ledger_writer.py`, and `llm.py` even when authored by an OWNER.

### #240 — Devin Review CI status is non-functional

Every open PR's combined commit **status** is solely the "Devin Review" bot reporting `Full review skipped: trial expired and no credits remaining` and skipping review. The actual test signal lives in **check runs** (`ci-ok`), which are green — but the status API gives a misleading "success" that could mask a broken state. `nakedagent` has zero checks.

Two risks: (1) if branch protection is configured against statuses rather than required checks, a "Devin success" can satisfy it without the suite running; (2) `nakedagent` has nothing automated at all.

**Suggested fix:** renew Devin credits or remove the Devin status check; configure branch protection on required check runs (`ci-ok`, plus per-package `test (...)` jobs); add a CI workflow to `nakedagent`.

### #241 — #236 bundles unrelated commits

See §2.4. Cherry-pick `b8128b6` and `1c3017e` onto fresh branches as separate PRs, leaving #236 with only the 4 provenance commits.

---

## 4. Recommended merge order

After the reviews, rebases, and splits above:

1. **oss#233, oss#234** — deps, low risk.
2. **oss#225** — after adding a canonical-equivalence test.
3. **oss#235** — CI change, self-contained.
4. **nakedagent#1** — after CI is added.
5. **oss#236** — after splitting out the cogstate/repair_chain commits and non-author review.
6. **oss#237** — after companion PRs align, non-author review, and auto-revocation behavior is confirmed; highest blast radius, merge last.

---

## 5. Audit automation proposal

This audit was performed manually in response to a request. To make it recurring, three options exist — ranked by reliability.

### 5.1 Recommended: GitHub Actions cron workflow (true recurring automation)

A scheduled workflow in `hummbl-io/oss` that re-runs the open-PR audit on a cadence and posts a digest. This runs in GitHub's infrastructure, not in the Vibe Code session, so it works even when no one is talking to the agent.

**Cadence:** daily at 09:00 UTC (`0 9 * * *`), plus `workflow_dispatch` for on-demand runs.

**What it checks** (all via `gh` / GitHub CLI against the org's open PRs):
- list open PRs across `hummbl-io/*` (`gh search prs --state open --owner hummbl-io`)
- for each: `mergeable_state`, presence of a review approval, `ci-ok` check conclusion, last-updated staleness, and whether it is behind/dirty
- post a digest comment to a tracking issue or Slack, and open/close tracking issues for newly-merged or newly-stale PRs

A starter workflow is provided in Appendix A. It requires a `GITHUB_TOKEN` with `pull-requests:read` and `issues:write` (the default `GITHUB_TOKEN` in public repos has these for the repo it runs in; for cross-org listing, a PAT or App token with org read scope is needed).

### 5.2 Alternative: Google Calendar recurring reminder (nudge only)

A Google Calendar event with an RRULE recurrence (e.g. daily or weekly) titled "Re-audit hummbl-io PRs" that reminds a human to ask the agent to re-run the audit. This does not run the audit; it only prompts a person to invoke it. Useful if you want a human in the loop each time.

### 5.3 Alternative: Slack scheduled message (one-shot, ≤120 days)

A single scheduled Slack message (up to 120 days out) summarizing the current audit and reminding the channel to re-request an audit. One-shot only — not recurring. Useful for a single follow-up nudge, not for ongoing monitoring.

### 5.4 What Vibe Code itself cannot do

Vibe Code runs in response to user messages, not on a timer. There is no native "scheduled task" primitive in the agent that would re-run code on a recurring schedule without an external trigger. True recurring automation must live in GitHub Actions (or another scheduler), not in the agent session.

---

## Appendix A — Starter audit workflow

```yaml
# .github/workflows/pr-audit.yml
name: PR Audit
on:
  schedule:
    - cron: '0 9 * * *'      # daily 09:00 UTC
  workflow_dispatch:           # on-demand
permissions:
  pull-requests: read
  issues: write
  contents: read
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Audit open PRs in hummbl-io
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set -euo pipefail
          # List open PRs across the org (requires a token with org read scope;
          # the default GITHUB_TOKEN only covers the repo it runs in, so for a
          # cross-org sweep, replace with a PAT/App secret named AUDIT_TOKEN).
          gh search prs --state open --owner hummbl-io \
            --json repository,number,title,author,updatedAt,url \
            --limit 100 > prs.json

          {
            echo "## hummbl-io PR audit — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
            echo
            echo "| Repo | PR | Title | Author | Updated | Review | ci-ok | State |"
            echo "|------|----|-------|--------|---------|--------|-------|-------|"
            jq -r '.[] | "\(.repository.nameWithOwner)|\(.number)|\(.title)|\(.author.login)|\(.updatedAt)|\(.url)"' prs.json | while IFS='|' read -r repo num title author updated url; do
              review=$(gh pr view "$num" --repo "$repo" --json reviews --jq '[.reviews[] | select(.state=="APPROVED")] | length')
              ciok=$(gh pr checks "$num" --repo "$repo" --json name,conclusion 2>/dev/null | jq -r 'map(select(.name=="ci-ok")) | .[0].conclusion // "n/a"')
              state=$(gh pr view "$num" --repo "$repo" --json mergeable --jq '.mergeable')
              echo "| $repo | [#$num]($url) | $title | $author | $updated | $review | $ciok | $state |"
            done
          } > digest.md

          # Post the digest as a comment on a tracking issue (create one first,
          # or adapt to post to Slack via a webhook).
          TRACKING_ISSUE=239   # the "non-author reviews missing" issue
          gh issue comment "$TRACKING_ISSUE" --repo hummbl-io/oss --body-file digest.md
```

Notes:
- For a true cross-org sweep, `gh search prs --owner hummbl-io` needs a token with org read scope; the default `GITHUB_TOKEN` in a public repo may not list other org repos. Use a PAT or GitHub App secret (`AUDIT_TOKEN`) with `read:org` + `pull_requests:read`.
- The workflow posts the digest as a comment on issue #239; change `TRACKING_ISSUE` or swap the final step for a Slack webhook (`curl` to an incoming webhook URL) if you prefer a Slack digest.
- This is a starter; extend it to open/close tracking issues for newly-stale or newly-merged PRs as desired.

---

## Appendix B — Scheduling options comparison

| Option | Recurring? | Runs the audit? | Max horizon | Setup effort |
|--------|-----------|-----------------|-------------|--------------|
| GitHub Actions cron | Yes (cron + dispatch) | Yes (full automation) | indefinite | Medium (workflow + token) |
| Google Calendar RRULE | Yes (calendar-managed) | No (nudge only) | indefinite | Low |
| Slack scheduled message | No (one-shot) | No (nudge only) | 120 days | Low |
| Vibe Code native | No | — (runs on request only) | — | n/a |

**Recommendation:** GitHub Actions cron for true automation; Google Calendar as a lightweight human-in-the-loop alternative if you don't want a workflow running unattended.

---

*Audit and document prepared by Vibe Code. Review comments posted to each audited PR; tracking issues #239, #240, #241 opened in hummbl-io/oss.*
