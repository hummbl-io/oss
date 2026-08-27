# Gap-7: No-Force-Push Branch Protection — Fleet-Wide Audit & Remediation

**Date:** 2026-08-27
**Agent:** devin
**Operator authorization:** Explicit request 2026-08-27
**Issue:** hummbl-io/hummbl-governance #412
**Federal standards:** NIST 800-53 CM-5 (Access Restrictions for Change), SI-7 (Software Integrity)

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Non-archived repos | 285 | 285 |
| Protected (force_push=false) | 264 | 283 |
| Unprotected | 20 | 1 |
| No main branch | 1 | 1 |
| Blocked (repo setting) | 0 | 1 |

**Result: 19/20 unprotected repos successfully protected. 1 repo requires manual investigation.**

## Audit findings

### Initial state (pre-remediation)

- 264 repos already had branch protection on main with `allow_force_pushes=false`
- 20 repos had no branch protection on main
- 1 repo has no main branch (only has a feature branch)
- 0 protected repos had `allow_force_pushes=true`

### Remediation

Enabled branch protection on 19 of 20 unprotected repos with:
- `allow_force_pushes: false`
- `allow_deletions: false`
- `enforce_admins: false` (don't lock out admins)
- `required_status_checks: null` (no CI requirement yet — gap-8 will add)
- `required_pull_request_reviews: null` (no PR review requirement yet)

### Repos protected (19)

_Redacted: repo names are fleet inventory and not publishable to the public oss repo per AGENTS.md public/private boundary. Full list retained in private governance repo._

### Manual investigation required (1)

_Redacted: repo name is fleet inventory. One private repo returned HTTP 404 "Branch protection has been disabled on this repository" on both GET and PUT. Repo is private, not archived, not disabled, has main branch. This suggests a repo-level or org-level setting that disables branch protection entirely. Requires manual investigation via GitHub UI or org settings._

### No main branch (1)

_Redacted: repo name is fleet inventory. One repo has only a feature branch, no main. Branch protection not applicable until main is created or default branch is changed._

## Force-push history audit

The issue (#412) references 87 repos with force-push history (_redacted: per-repo counts are fleet inventory_). This audit confirms that **all protected repos now have force-push disabled**, preventing future force-push events. Past force-push history cannot be undone — the audit trail impact is historical, not ongoing. A lost-commit audit of the 87 repos is deferred as a separate task (lower priority now that future force-pushes are blocked).

## Acceptance criteria status

- [x] All fleet repos (except 1 manual-investigation repo + 1 no-main-branch repo) have branch protection on main with force-push disabled
- [x] All fleet repos (except 1 manual-investigation repo + 1 no-main-branch repo) have deletion disabled
- [ ] Audit the 87 repos with force-push history for lost commits (deferred)
- [x] Establish no-force-push policy on protected branches (enforced via branch protection)

## Scripts

- `scripts/gap7-branch-protection-audit.py` — read-only fleet-wide audit
- `scripts/gap7-enable-branch-protection.py` — enables protection on unprotected repos

## Data

- `docs/research/gap7-branch-protection-audit-20260827.json` — full audit results (285 repos)
- `docs/research/gap7-branch-protection-results-20260827.json` — remediation results (20 repos)

## Pre-mutation SITREP

Posted to coordination bus before any GitHub mutation, per gap-7 operator authorization.
