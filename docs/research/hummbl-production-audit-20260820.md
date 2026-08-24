# hummbl-production Full Audit Report

**Date**: 2026-08-20  
**Auditor**: devin (GLM-5.2 High)  
**Repo**: hummbl-io/hummbl-production (private, 14.2 MB, default branch: main)

---

## 1. CI/CD Workflow Health

### Summary

| Metric                         | Value                         |
| ------------------------------ | ----------------------------- |
| Total workflows (active)       | 26 (1 disabled during audit)  |
| Workflows with recent failures | 5                             |
| Workflows passing              | 18                            |
| Orphaned workflows             | 1 (Workflow Debug — disabled) |

### Workflow Status Detail

| Workflow                        | Recent Status       | Notes                                                                                                                                                                  |
| ------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Test Workflow                   | **FAILING**         | startup_failure fixed (org verified_allowed=true). Now fails at "Triage public claim-risk queues" step — stale JSON/MD reports. 20+ consecutive failures since Aug 18. |
| Public Surface Smoke            | **PASSING**         | Fixed this session (duplicate timeout-minutes removed, commit 274afdb)                                                                                                 |
| Fabric Adapter Build Gate       | **startup_failure** | 3 consecutive startup_failures. Likely same org action allowlist issue — check if workflow uses non-allowed actions.                                                   |
| Deploy Dashboard                | **startup_failure** | 1 startup_failure. Same suspected cause.                                                                                                                               |
| KRINEIA Chain Validation        | **failure**         | 2 failures. Needs investigation.                                                                                                                                       |
| Landing Release Receipt         | **failure**         | 1 failure. Needs investigation.                                                                                                                                        |
| Public Surface Smoke (old runs) | **failure**         | 4 failures before fix. Now passing.                                                                                                                                    |
| Route Health Probes             | **PASSING**         | 9/9 success                                                                                                                                                            |
| No Vendor Attribution           | **PASSING**         | 5/6 success (1 anomaly)                                                                                                                                                |
| All others                      | **PASSING**         | Artifact Manifest, Brand Asset, Claims, Dashboard PR Build, Public Release State, Public Surface Parity, Public-Claim Evidence Gate                                    |

### Critical Finding

**Test Workflow** — the primary CI gate — has been failing since Aug 18. The startup_failure was caused by org-level `verified_allowed: false` blocking `cloudflare/wrangler-action`. That was fixed this session. The remaining failure is a stale report issue: `docs/reports/wave4-public-claim-risk-triage.json` and `.md` are stale and need regeneration.

**Fabric Adapter Build Gate** and **Deploy Dashboard** still show startup_failure — likely the same allowlist issue or a different disallowed action. Needs investigation.

---

## 2. Branch Health

### Summary

| Metric                                | Value                         |
| ------------------------------------- | ----------------------------- |
| Total remote branches                 | 21 (including main)           |
| Stale branches (>30 days no activity) | 0 (all created in Aug 2026)   |
| Backup branches                       | 2 (backup/codex/pr581, pr582) |
| Revert branches                       | 1 (revert-907)                |
| Dependabot branches                   | 2 (hono, wrangler bumps)      |
| Feature/fix branches                  | 15                            |

### Stale Branch Candidates (for cleanup)

| Branch                                          | Last commit | Status | Recommendation                          |
| ----------------------------------------------- | ----------- | ------ | --------------------------------------- |
| backup/codex/pr581-pre-clean-20260702           | Jul 2       | Backup | Delete if PR was merged                 |
| backup/codex/pr582-pre-main-rebase-20260702     | Jul 2       | Backup | Delete if PR was merged                 |
| revert-907-fix/codex/landing-ci-evidence        | Aug 15      | Revert | Delete if not needed                    |
| chore/codex/public-validation-preflight         | Aug ?       | Stale  | Check if PR exists                      |
| chore/codex/refresh-wave4-claimrisk-triage      | Aug ?       | Stale  | Check if PR exists                      |
| content/codex/retinal-biomarkers-outreach       | Aug ?       | Stale  | Check if PR exists                      |
| docs/cline/peer-review-audit-2026-07-26         | Jul 26      | Old    | Delete if merged                        |
| docs/codex/governed-superuser-enclave           | Aug ?       | Stale  | Check if PR exists                      |
| docs/conflation-control-ratification-859        | Aug ?       | Stale  | Check if PR exists                      |
| feat/devin/homepage-redesign                    | Aug ?       | Stale  | Check if PR exists                      |
| fix/codex/landing-ci-evidence                   | Aug ?       | Stale  | Check if PR exists (PR #907 was merged) |
| fix/devin/brace-expansion-vuln                  | Aug ?       | Stale  | Check if PR exists                      |
| fix/devin/monitoring-silent-catch               | Aug ?       | Stale  | Check if PR exists                      |
| fix/devin/stale-report-and-brace-expansion-vuln | Aug ?       | Stale  | Check if PR exists                      |
| research/opencode/seed20-grammatical-math       | Aug ?       | Stale  | Check if PR exists                      |

### Open PRs

| PR   | Title                                                         | State             | Age |
| ---- | ------------------------------------------------------------- | ----------------- | --- |
| #935 | docs(agents): restore subagent dispatch rules (clobbered x2)  | OPEN              | 0d  |
| #931 | fix: update R2 bucket reference from deleted phase0b-mike-lab | OPEN              | 0d  |
| #922 | chore(deps-dev): bump hono from 4.13.1 to 4.13.2              | OPEN (dependabot) | 4d  |
| #921 | chore(deps-dev): bump wrangler from 4.121.0 to 4.122.0        | OPEN (dependabot) | 4d  |

### Open Issues

| Metric            | Value                            |
| ----------------- | -------------------------------- |
| Total open issues | 32                               |
| P0 issues         | 2 (#857, #838)                   |
| P1 issues         | 5 (#836, #835, #834, #832, #830) |
| Feature requests  | 4 (#852, #851, #850, #849)       |
| Other             | 21                               |

**Note**: Issues #857 and #838 are P0 and have been open since Aug 3 and Jul 27 respectively. These are the highest-priority items.

---

## 3. Dependency Health

### npm audit (api/)

| Severity | Count |
| -------- | ----- |
| Critical | 0     |
| High     | 0     |
| Moderate | 0     |
| Low      | 0     |

**Result**: 0 vulnerabilities. Clean.

### npm outdated

No outdated packages returned. All dependencies at latest.

### Dependabot PRs

- PR #922: bump hono 4.13.1 → 4.13.2 (4 days old, needs review/merge)
- PR #921: bump wrangler 4.121.0 → 4.122.0 (4 days old, needs review/merge)

### Install warnings

2 packages had install scripts blocked by npm allowScripts policy:

- esbuild@0.28.1 (postinstall: node install.js)
- workerd@1.20260804.1 (postinstall: node install.js)

These are expected for Cloudflare Workers development and are safe to approve if needed for local dev.

---

## 4. Security

### GitHub Security Features

| Feature                               | Status       |
| ------------------------------------- | ------------ |
| Secret scanning                       | **enabled**  |
| Secret scanning push protection       | **enabled**  |
| Dependabot security updates           | **enabled**  |
| Code security (CodeQL)                | **disabled** |
| Secret scanning AI detection          | **disabled** |
| Secret scanning non-provider patterns | **disabled** |
| Secret scanning validity checks       | **disabled** |

### Action Allowlist (org-level)

| Setting              | Value                                                                         |
| -------------------- | ----------------------------------------------------------------------------- |
| allowed_actions      | selected                                                                      |
| github_owned_allowed | true                                                                          |
| verified_allowed     | true (was false — fixed this session)                                         |
| patterns_allowed     | codecov/codecov-action, softprops/action-gh-release, gitleaks/gitleaks-action |

**Finding**: `cloudflare/wrangler-action` is a verified creator action and should now work with `verified_allowed: true`. However, `Fabric Adapter Build Gate` and `Deploy Dashboard` still show startup_failure — may need investigation for other disallowed actions.

**Recommendation**: Enable CodeQL code security analysis. It's disabled and the repo has significant TypeScript codebase.

### Action SHA Pinning

All 4 actions in test.yml are pinned to commit SHAs:

- actions/checkout@11d5960 (verified valid)
- actions/setup-node@49933ea (verified valid)
- codecov/codecov-action@fb8b358 (verified valid)
- cloudflare/wrangler-action@ebbaa15 (verified valid)

### License

- License: NOASSERTION (LICENSE file exists but GitHub can't detect the SPDX ID)
- This may need fixing if the repo is intended to have a specific license

---

## 5. Code Quality

### Test Results (api/)

| Metric       | Value  |
| ------------ | ------ |
| Test files   | 33     |
| Tests passed | 538    |
| Tests failed | 0      |
| Duration     | 13.62s |

**Result**: All tests pass. Clean.

### Lint (api/)

**Result**: ESLint passes with no errors.

### Format Check (api/)

**Result**: **78 files have formatting issues**. Prettier `--check` fails.

### Format Check (web/)

**Result**: **122 HTML files have formatting issues**. Prettier `--check` fails.

### Validation Scripts

| Script                        | Result                               |
| ----------------------------- | ------------------------------------ |
| validate_web_html.py          | PASS (126 pages, 0 failures)         |
| validate_api_routes.py        | PASS                                 |
| validate-base120-refs.js      | PASS                                 |
| validate_compliance_claims.py | PASS (skipped — no compliance pages) |
| sync_cloudflare_surfaces.py   | PASS                                 |
| normalize_web_hosts.py        | PASS                                 |
| triage_public_claim_risks.py  | **FAIL** — stale JSON/MD reports     |

### Critical Finding

**200 files have formatting issues** (78 in api/, 122 in web/). This means `npm run format:check` and `npx prettier --check "web/**/*.html"` both fail in CI. This is a pre-existing issue that contributes to the Test Workflow failure.

**The triage report staleness** is the other contributing factor to the Test Workflow failure. The JSON and MD reports need regeneration.

---

## 6. Documentation

### AGENTS.md

- Present and comprehensive (610 lines)
- Covers GitHub CLI ops, pre-commit checks, PR workflow, subagent fallback, CI response, naming collisions, JSON encoding, and more
- **Issue**: Subagent dispatch rules (pre-flight quota check, prompt saving) have been clobbered twice by concurrent agents doing "self-hosted-runner-5 sweeps". PR #935 open to restore them. The operator confirmed both times this was not their action.
- **Issue**: The `host=self-hosted-runner-5` tag is used by agents on this machine but is not in the AAR spec's allowed list (`self-hosted-runner-2|self-hosted-runner-3|self-hosted-runner-1|unknown`). bus-global.py now warns on invalid host tags (fixed this session).

### README.md

- Present (not reviewed in detail this audit)

### Other docs

- 30+ files in repo root (CHANGELOG, CODE_OF_CONDUCT, CONSTITUTION, CONTRIBUTING, DEPLOYMENT, DOCTRINE, LICENSE, METRICS, MONITORING, ROADMAP, SECURITY, etc.)
- `docs/` directory with adr/, artifacts/, enterprise/, fleet-digest, ops/, planning/, product/, reports/, research/, sources/, tiershift/ subdirectories
- `_internal/` directory with board/, forensics/, handoffs/, hackernews/, substack/
- `_receipts/` directory with krineia/ evidence

### Workflow Debug file

- `.github/workflows/workflow-debug.yml` was deleted from working tree (by operator) and does not exist on remote. The workflow was disabled via API during audit. No residual impact.

---

## 7. Infrastructure

### Cloudflare Workers

4 worker directories:

- contact-form
- email-gateway
- inbound-email
- site-chat

### R2 Bucket Issue

PR #931 is open to fix R2 bucket references. The workers reference `phase0b-mike-lab` bucket (deleted) but should reference `hummbl-storage`. The operator made changes to the wrangler.toml files to revert back to `phase0b-mike-lab` — this needs clarification.

**Note**: The operator's user_actions show they changed email-gateway and inbound-email wrangler.toml back to `phase0b-mike-lab`. This contradicts PR #931 which changes them to `hummbl-storage`. The operator may have a different R2 bucket strategy in mind.

### Cloudflare Surface Manifest

- `sync_cloudflare_surfaces.py --check` passes
- `validate_cloudflare_operations.py` passes

### Web Host Normalization

- `normalize_web_hosts.py --check` passes

---

## 8. Summary of Findings

### Critical (P0)

1. **Test Workflow failing** — stale triage reports (`wave4-public-claim-risk-triage.json/.md`) + 200 unformatted files. This has been failing since Aug 18 and blocks all PRs.
2. **Fabric Adapter Build Gate startup_failure** — 3 consecutive startup_failures. Likely action allowlist issue.
3. **Deploy Dashboard startup_failure** — 1 startup_failure. Same suspected cause.

### High (P1)

4. **200 files with formatting issues** — 78 in api/, 122 in web/. Both `prettier --check` commands fail.
5. **15 stale branches** — backup, revert, and old fix/feature branches that may be deletable.
6. **2 dependabot PRs stale** — #921 and #922 are 4 days old, need review/merge.
7. **2 P0 issues open** — #857 (CI containment) and #838 (dashboard validation) have been open for 18+ and 24+ days.
8. **Concurrent agent clobbering** — agents on self-hosted-runner-2 are resetting self-hosted-runner-5's working tree, causing loss of uncommitted changes. This happened twice this session.

### Medium (P2)

9. **CodeQL disabled** — code security analysis is off.
10. **License NOASSERTION** — GitHub can't detect the SPDX ID from the LICENSE file.
11. **KRINEIA Chain Validation failing** — 2 recent failures, needs investigation.
12. **Landing Release Receipt failing** — 1 recent failure, needs investigation.
13. **R2 bucket reference confusion** — PR #931 says `hummbl-storage`, operator reverted to `phase0b-mike-lab`. Needs clarification.
14. **Orphaned Workflow Debug** — disabled during audit, but the workflow entry was still active until manually disabled.

### Low (P3)

15. **32 open issues** — many are old feature requests or gaps that may be stale.
16. **npm install-scripts blocked** — esbuild and workerd postinstall scripts blocked. Expected but may confuse new developers.

---

## 9. Recommended Actions (Prioritized)

1. **[P0]** Regenerate stale triage reports: `python3 scripts/triage_public_claim_risks.py` (without `--check`) to update JSON/MD
2. **[P0]** Run `npx prettier --write` on api/ and web/ to fix all 200 formatting issues
3. **[P0]** Investigate Fabric Adapter Build Gate and Deploy Dashboard startup_failures — check if they use disallowed actions
4. **[P1]** Merge or close dependabot PRs #921 and #922
5. **[P1]** Clean up 15 stale branches (delete merged/abandoned ones)
6. **[P1]** Enable CodeQL code security analysis
7. **[P1]** Fix LICENSE file to use a detectable SPDX identifier
8. **[P1]** Investigate concurrent agent clobbering — agents on self-hosted-runner-2 should not reset self-hosted-runner-5's working tree
9. **[P2]** Investigate KRINEIA Chain Validation and Landing Release Receipt failures
10. **[P2]** Clarify R2 bucket strategy — is it `hummbl-storage` or `phase0b-mike-lab`?
11. **[P2]** Triage 32 open issues — close stale ones, prioritize P0s
12. **[P3]** Approve esbuild and workerd install scripts for local dev convenience

---

## Evidence

- `gh workflow list` (26 active workflows, 1 disabled during audit)
- `gh run list --limit 50` (Test Workflow: 20+ startup_failures, now runs but fails on triage step)
- `gh pr list --state all --limit 30` (4 open PRs, 26 merged/closed)
- `gh issue list --state all --limit 20` (32 open issues, 2 P0)
- `gh api repos/hummbl-io/hummbl-production` (private, 14.2 MB, 21 branches)
- `gh api repos/hummbl-io/hummbl-production/actions/permissions/selected-actions` (org: verified_allowed=true, repo: verified_allowed=true)
- `gh api repos/hummbl-io/hummbl-production --jq '.security_and_analysis'` (secret scanning enabled, CodeQL disabled)
- `npm audit` (0 vulnerabilities)
- `npx vitest run` (538 passed, 0 failed, 33 files)
- `npm run lint` (pass)
- `npm run format:check` (78 files with issues)
- `npx prettier --check "web/**/*.html"` (122 files with issues)
- `python3 scripts/triage_public_claim_risks.py --check` (FAIL — stale reports)
- `python3 scripts/validate_web_html.py --quiet` (126 pages, 0 failures)
- All other validation scripts: PASS
- `gh api repos/hummbl-io/hummbl-production/branches` (21 branches, 15 stale candidates)
