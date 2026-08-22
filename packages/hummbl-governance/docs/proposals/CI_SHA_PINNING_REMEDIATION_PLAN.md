---
expires_for_review: 2026-11-16
last_reviewed: 2026-08-18
---

# Plan: Remediate hummbl-io CI Startup Failures (Actions SHA-Pinning Policy)

**Status:** DRAFT — awaiting operator decision on policy posture (Decision A, §4)
**Date:** 2026-08-18
**Author:** pi session (scan receipt: bus STATUS `CI_SCAN` @ 2026-08-18T15:22:27Z, request `459bffe6`)
**Steward:** HUMMBL Research Institute
**Scope:** GitHub org `hummbl-io` (204 active repos, 7 archived excluded)

## 1. Problem Statement

61 of 204 active `hummbl-io` repos have failing CI on their default branch as of 2026-08-18T15:15Z. 47 of these fail with `startup_failure` — a single shared, mechanical root cause that began between 2026-08-17T23:23Z and 2026-08-18T01:44Z and is still active. The remaining 14 are ordinary hard failures (test/lint/dependabot) unrelated to the systemic cause.

## 2. Current State (Scan Results)

Scan method: `gh repo list hummbl-io` (214 repos, 7 archived excluded) → latest run on each default branch via `gh run list --branch <default> --limit 1`. Artifact: `/tmp/ci-scan/results.tsv` on <machine>.

| Conclusion | Count | Class |
|---|---|---|
| success | 120 | healthy |
| startup_failure | 47 | **systemic — policy-caused** |
| failure | 14 | hard failures (per-repo triage) |
| queued (no conclusion yet) | 8 | suspected casualty of same class; some queued 14+ h |
| in_progress | 8 | pending |
| none (no runs ever) | 15 | out of scope |

Flagship repos affected by the systemic class: `hummbl`, `hummbl-governance`, `agents`, `knowledge-as-code`, `hummbl-production`, `hummbl-iac`, `protocol-as-code`, `hummbl-dashboard`, `arcana`, `platform`, `idp-spec`, `hummbl-agent-sdk` (full list in Appendix A).

## 3. Root Cause Analysis

### 3.1 Evidence chain

1. **Org Actions policy** (`GET /repos/hummbl-io/hummbl/actions/permissions`):
   - `allowed_actions: "selected"`
   - `sha_pinning_required: true`
   - selected-actions: `github_owned_allowed: true`, `verified_allowed: false`, patterns allowed only: `codecov/codecov-action`, `softprops/action-gh-release`, `gitleaks/gitleaks-action`
2. **Failing workflows reference actions by tag**: e.g. `hummbl`'s `ci.yml` uses `actions/checkout@v7`; `agents` also uses `gaurav-nelson/github-action-markdown-link-check@v1` (third-party, not on allowlist).
3. **Zero jobs created** on startup_failed runs (`.../runs/<id>/jobs` returns empty). GitHub reports "This run likely failed because of a workflow file issue." No runner, test, or code defect involved.
4. **Differential proof**: SHA-pinned repos (`apex-nexus`, `foundermode-app`, `bif`, `mcp-server`) ran green at 14:54–15:12Z — mid-outage. Their workflows pin full SHAs (e.g. `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7`).
5. **Timeline**: last tag-ref success 2026-08-17T23:23Z (`agents`); first mass startup_failures 2026-08-18T01:44Z. Policy was tightened in that window.

### 3.2 Failure mechanism

`sha_pinning_required: true` rejects workflow-level `uses:` refs that are mutable tags. Combined with `allowed_actions: selected` + `verified_allowed: false`, any use of (a) a tag ref to a github-owned action, or (b) any third-party action outside the three allowlisted patterns, causes the run to fail before job scheduling — `startup_failure`, zero jobs, no logs.

### 3.3 Refuted hypotheses

- Not a GitHub incident (differential: SHA-pinned repos pass concurrently).
- Not a workflow syntax error (files parse cleanly; jobs list is simply empty).
- Not runner starvation (failures are `completed/startup_failure`, not `queued`).

## 4. Decision Needed (gates the plan)

**Decision A — policy posture.** Who set `sha_pinning_required` + selected-actions between 17T23:23Z and 18T01:44Z, and was it intentional?

- **A1 (assumed): Keep the policy.** It is genuine supply-chain hardening (tag refs are mutable; the org pinned SHAs in flagship repos months ago). Proceed with Phase 1–3.
- **A2: Rollback the policy.** If the flip was accidental, one org-settings change restores 47 repos instantly. Then this plan reduces to prevention only (Phase 4).

Verification step (requires org admin): GitHub → org Settings → Actions → General → audit log, filter `actions_policy` / `actions_allowed_actions` events in the 17T23:00Z–18T02:00Z window.

## 5. Remediation Plan (phased, assumes A1)

### Phase 0 — Verify policy provenance (ops, org admin, 15 min)
- Pull org audit log entry for the policy change; record actor + timestamp in this doc.
- If actor is unknown/unauthorized → treat as security event, not remediation (escalate to redteam/silverteam posture).

### Phase 1 — Mechanical repin of github-owned actions (agent-executable, ~47 repos)
1. Inventory: for each Appendix A repo, parse all `.github/workflows/*.yml` for `uses: <owner>/<action>@<tag>` where owner ∈ {`actions`, `github`}.
2. Resolve each tag → commit SHA via `gh api repos/<owner>/<action>/git/ref/tags/<tag>` (strip `refs/tags/`); for annotated tags follow the peeled object.
3. Rewrite `uses: actions/checkout@v7` → `uses: actions/checkout@<full-sha> # v7` (matches apex-nexus house style).
4. One branch per repo: `fix/ci-sha-pin` — conventional commit `fix(ci): pin action refs to SHAs for org sha_pinning_required policy`.
5. Use `[org-mutation-precheck]` first: classify repos as API-safe / needs-signed-commit / needs-PR before bulk PRs. Do not bypass branch protection.
6. Verify: `gh run watch` each repo's CI post-merge; expect `success` or transition to a real (Class 2) failure.

### Phase 2 — Third-party actions off the allowlist (agent-executable after operator picks per-action)
Inventory first: any `uses:` whose owner is not `actions`/`github` and not in the three allowed patterns (known instance: `gaurav-nelson/github-action-markdown-link-check@v1` in `agents`). For each:
- **B1:** add pattern to org allowlist (one-line org change, weakest control), or
- **B2:** vendor the action's logic as an inline `run:` step (markdown-link-check via npx), or
- **B3:** replace with an allowed equivalent or drop the job.

### Phase 3 — Rerun + verify
- Rerun or push-trigger CI on all 47 repos; confirm conclusion flips from `startup_failure`.
- Re-scan org-wide with the §2 method; target: startup_failure count = 0.
- Check the 8 long-queued runs clear once their repos are repinned (they may be blocked on the same policy evaluation).

### Phase 4 — Prevention (make the class un-regressable)
- Add a fleet lint gate: reject `uses:` tag refs in `.github/workflows/` (actionlint rule or simple grep check in each repo's CI — note the bootstrap problem: the check itself must be SHA-pinned).
- Record the org policy in `docs/runbooks/` (new: `github-actions-policy.md`): current settings, allowlist, repin convention, who may change org Actions policy.
- Add `[workflow-lint]` to repo-scaffold defaults for new repos.

### Phase 5 — Class 2 triage (separate track, per-repo)
The 14 hard failures predate/parallel the policy event and need normal `[debug-test]` flows. Priority order by recency and role:

| Repo | Workflow | Last fail | Note |
|---|---|---|---|
| hummbl-voice | ci.yml | 18T12:20Z | active repo, same-day pushes |
| hummbl-security-auditor | ci.yml | 18T11:46Z | same-day pushes |
| claude-config | Validate Claude config | 18T00:31Z | |
| awesome-python-reasoning | CI | 18T00:23Z | |
| research-source-packets | CI | 18T00:13Z | |
| microsoft-locked-clients-research | CI | 17T23:58Z | |
| jsr-extension | CI | 17T23:30Z | |
| project-audits | CI | 17T23:26Z | |
| hummbl-corporate | CI | 17T23:24Z | |
| hummbl-axis | CI | 17T24:28Z→17T23:24Z | |
| demosmesh | CI | 15T23:24Z | stale 3 days |
| hummbl-security | Dependabot Updates | 13T10:35Z | dependabot-fail class |
| hummbl-py | Dependabot Updates | 13T10:35Z | dependabot-fail class |
| hummbl-scheduler | Dependabot Updates | 13T10:35Z | dependabot-fail class |

## 6. Risks & Rollback

- **Risk:** SHA resolution pins to a malicious tag move (tag mutated between resolution and merge). Mitigate by resolving from the action's upstream repo and cross-checking the tag's publish date; github-owned actions are low-risk.
- **Risk:** Repinned SHA versions differ semantically from the tag the workflow was tested against (e.g. `@v7` moved). Mitigate by watching first post-merge run per repo (Phase 3).
- **Rollback:** per-repo `git revert` of the pin commit, or org-level policy relaxation (A2) at any time.

## 7. Effort Estimate

| Phase | Executor | Estimate |
|---|---|---|
| 0 policy provenance | operator/org admin | 15 min |
| 1 repin github-owned | agent | 2–4 h wall (47 repos, PR-gated) |
| 2 third-party actions | agent + operator decisions | 1 h + per-action decision |
| 3 rerun/verify | agent | 1 h |
| 4 prevention gates | agent | 2 h |
| 5 Class 2 triage | agent, per-repo | out of band |

## Appendix A — startup_failure repos (47, as of 2026-08-18T15:15Z)

hummbl-governance (CodeQL Advanced), hummbl, hummbl-iac, protocol-as-code, hummbl-dashboard, swarm-test-archive, unified-frameworks (Schema Check), tandem-trade, autoresearch-pipeline, arcana-platform, arcana, agents, agent-tools, agent-governance-demo-v2, corpus, axis, ollama-mon, coaching-private (master), scavenger-mode, frontier-lab-readiness, hummbl-research (Python Lint), hummbl-toolkit, reubenos, psychedelic-claim-validator, knowledge-as-code, hummbl-cognition, hummbl-bus, hummbl-quality (governance-validation), platform, hummbl-tuples (Validate), crab-incubator, hummbl-kernel-factory, governed-counterpart, hummbl-intel-atlas, hummbl-interaction-control-plane, governance-bench, idp-spec, hummbl-transparency, hummbl-agent-sdk, hummbl-admission-controlled-state (validate), agent-runtime-governance, model-routing-as-code, observability-as-code, execution-receipts, compendium-as-code, agent-handoffs, hummbl-production (Route Health Probes, schedule-triggered).

## Appendix B — Reproduction

```bash
gh repo list hummbl-io --limit 1000 --json name,isArchived,defaultBranchRef \
  --jq '.[] | select(.isArchived|not) | [.name, .defaultBranchRef.name] | @tsv' > repos.tsv
while IFS=$'\t' read -r repo branch; do
  gh run list -R "hummbl-io/$repo" --branch "$branch" --limit 1 \
    --json status,conclusion,workflowName,createdAt \
    --jq '.[0] | [.status, .conclusion // "-", .workflowName, .createdAt] | @tsv'
done < repos.tsv
# Policy: gh api repos/hummbl-io/hummbl/actions/permissions (+ /selected-actions)
```
