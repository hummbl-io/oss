# Manifest Policy-Envelope Rollout Plan

**Status:** PROPOSED — requires human approval before execution
**Origin:** hummbl-io/hummbl-governance#112
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

The repo manifest schema now includes a `repository_settings` section for expected GitHub repo configuration, but governed manifests do not yet use that section. This document defines the rollout plan to make the schema addition operational across current repos.

---

## 2. First-Wave Fields

The first wave of `repository_settings` adoption covers these fields:

| Field | Description | Default |
|-------|-------------|---------|
| `default_branch` | Expected default branch name | `main` |
| `visibility` | Expected repo visibility | per repo |
| `merge_methods.squash` | Squash merge allowed | `true` |
| `merge_methods.merge` | Merge commit allowed | `false` |
| `merge_methods.rebase` | Rebase merge allowed | `false` |
| `delete_branch_on_merge` | Delete head branches after merge | `true` |
| `allow_auto_merge` | Auto-merge allowed | `false` |
| `allow_update_branch` | Branch update allowed | `false` |

Fields not in the first wave (branch protection details, required status checks) will be added in wave 2 after the first wave is validated.

---

## 3. Canonical Example Snippet

Add this to `hummbl.repo.yaml` under the existing `validation` block:

```yaml
repository_settings:
  default_branch: "main"
  visibility: "public"  # or "private" per repo
  merge_methods:
    merge: false
    squash: true
    rebase: false
  delete_branch_on_merge: true
  allow_auto_merge: false
  allow_update_branch: false
```

---

## 4. Rollout Plan

### Wave 1: Foundation Repos (Single PR)

| Repo | Visibility | Notes |
|------|-----------|-------|
| `hummbl-governance` | public | Schema owner — adopt first |
| `arbiter` | public | Audit repo — adopt for self-compliance |
| `krineia` | public | Spec repo — simple settings |
| `base120` | public | Library repo — simple settings |

### Wave 2: Application Repos

| Repo | Visibility | Notes |
|------|-----------|-------|
| `hummbl-governance` | public | Internal ops — may have different merge policy |
| `hummbl-agent` | public | Agent runtime — may have different auto-merge |
| `hummbl-production` | private | Production — strictest settings |

### Wave 3: Branch Protection Details

Add `branch_protection` sub-section with:
- `protected_branches`: `["main"]`
- `required_status_checks`: per repo CI config
- `enforce_admins`: `true`
- `require_code_owner_reviews`: `true` (where CODEOWNERS exists)

---

## 5. Implementation Path

**Decision:** One PR per repo (not a single mega-PR).

Rationale:
- Each repo has different visibility and merge settings
- Per-repo PRs are smaller and easier to review
- CI runs independently per repo
- Failures in one repo don't block others

### Implementation Steps

1. Add `repository_settings` block to `hummbl.repo.yaml` in each repo
2. Validate manifest against `hummbl-repo-manifest@0.1` schema
3. Cross-check declared settings against actual GitHub repo settings
4. Document any discrepancies as follow-up issues
5. Arbiter audit can then compare declared vs. observed settings

---

## 6. Audit Integration

Once manifests declare `repository_settings`, the Arbiter repo-standard audit can:

1. **Load** the `repository_settings` block from `hummbl.repo.yaml`
2. **Compare** declared settings against live GitHub repo settings (via `gh` CLI)
3. **Report** drift as `settings-drift` findings
4. **Score** settings compliance as part of the repo-standard score

This is a follow-up to the manifest path checks already implemented in `arbiter/src/arbiter/repo_standard_audit.py`.

---

## 7. Cross-References

- **Schema definition:** `hummbl-governance/schemas/hummbl-repo-manifest.schema.json` (lines 105+)
- **Arbiter manifest path checks:** arbiter#92
- **Repository settings envelope issue:** hummbl-governance#102 (closed)

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Approval required:** Human approval before execution
