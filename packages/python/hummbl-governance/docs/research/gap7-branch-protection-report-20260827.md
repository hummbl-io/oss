# Gap-7: No-Force-Push Branch Protection ΓÇö Fleet-Wide Audit & Remediation

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

**Result: 19/20 unprotected repos successfully protected. 1 repo (base120-internal) requires manual investigation.**

## Audit findings

### Initial state (pre-remediation)

- 264 repos already had branch protection on main with `allow_force_pushes=false`
- 20 repos had no branch protection on main
- 1 repo (ai-factory) has no main branch (only has `fix/devin/correct-entity-name`)
- 0 protected repos had `allow_force_pushes=true`

### Remediation

Enabled branch protection on 19 of 20 unprotected repos with:
- `allow_force_pushes: false`
- `allow_deletions: false`
- `enforce_admins: false` (don't lock out admins)
- `required_status_checks: null` (no CI requirement yet ΓÇö gap-8 will add)
- `required_pull_request_reviews: null` (no PR review requirement yet)

### Repos protected (19)

CODES, _between, agent-identity-kit, awesome-stdlib, community-resource-hub-studio, cyber, delta-agents, dirty-runtime-agent, evidence-gate, founder-mode-showcase, grounding, hummbl-120-agents, hummbl-content-filter, hummbl-formalization, hummbl-interaction-control-plane, lejepa, search-space-lab, vendor-skill-fleet, wags

### Manual investigation required (1)

**base120-internal** ΓÇö API returns HTTP 404 "Branch protection has been disabled on this repository" on both GET and PUT. Repo is private, not archived, not disabled, has main branch. This suggests a repo-level or org-level setting that disables branch protection entirely. Requires manual investigation via GitHub UI or org settings.

### No main branch (1)

**ai-factory** ΓÇö only has branch `fix/devin/correct-entity-name`, no main. Branch protection not applicable until main is created or default branch is changed.

## Force-push history audit

The issue (#412) references 87 repos with force-push history (hummbl-production=45, hummbl-governance=31, hummbl-bus=26, hummbl-bibliography=24). This audit confirms that **all protected repos now have force-push disabled**, preventing future force-push events. Past force-push history cannot be undone ΓÇö the audit trail impact is historical, not ongoing. A lost-commit audit of the 87 repos is deferred as a separate task (lower priority now that future force-pushes are blocked).

## Acceptance criteria status

- [x] All fleet repos (except base120-internal + ai-factory) have branch protection on main with force-push disabled
- [x] All fleet repos (except base120-internal + ai-factory) have deletion disabled
- [ ] Audit the 87 repos with force-push history for lost commits (deferred)
- [x] Establish no-force-push policy on protected branches (enforced via branch protection)

## Scripts

- `scripts/gap7-branch-protection-audit.py` ΓÇö read-only fleet-wide audit
- `scripts/gap7-enable-branch-protection.py` ΓÇö enables protection on unprotected repos

## Data

- `docs/research/gap7-branch-protection-audit-20260827.json` ΓÇö full audit results (285 repos)
- `docs/research/gap7-branch-protection-results-20260827.json` ΓÇö remediation results (20 repos)

## Pre-mutation SITREP

Posted to bus 2026-08-27T10:36:47Z before any GitHub mutation, per gap-7 operator authorization. Delta devin was watching (session started 10:18:46Z).
