# GitHub Surface Map Doctrine

**Status:** PROPOSED — requires human review for authority boundaries
**Origin:** hummbl-io/hummbl-governance#93
**Schema:** `schemas/github_surface_map.schema.json`

---

## 1. Purpose

The GitHub Surface Map is a canonical model of every perspective a human or agent can have while operating through GitHub: repository page tabs, issues, pull requests, Actions, Projects, Security, Insights, Settings, `gh` CLI, APIs, TUIs, and IDE integrations.

Without a canonical surface map, agents reason from partial UI memories and unstructured workflow habits instead of a governed model of available actions, authorities, receipts, and failure modes.

---

## 2. Surfaces

### 2.1 Code (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-code-ui` |
| `channel` | `ui` |
| `human_role` | Browse, read, and navigate source code |
| `agent_role` | Read code for analysis, review, and audit |
| `high_risk` | false |

**Key actions:**
- `browse-files` — active, agent_eligible: true, gh: `gh repo clone`
- `view-file` — active, agent_eligible: true, gh: N/A (web only)
- `search-code` — active, agent_eligible: true, gh: `gh search code`

### 2.2 Issues (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-issues-ui` |
| `channel` | `ui` |
| `human_role` | Create, label, assign, comment, close, reopen issues |
| `agent_role` | Create issues from audits, comment with findings, close resolved |
| `high_risk` | false |

**Key actions:**
- `create-issue` — active, agent_eligible: true, gh: `gh issue create`
- `label-issue` — trusted, agent_eligible: true, gh: `gh issue edit --add-label`
- `assign-issue` — trusted, agent_eligible: true, gh: `gh issue edit --add-assignee`
- `comment-issue` — active, agent_eligible: true, gh: `gh issue comment`
- `close-issue` — trusted, agent_eligible: true, gh: `gh issue close`
- `reopen-issue` — trusted, agent_eligible: true, gh: `gh issue reopen`

### 2.3 Pull Requests (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-pr-ui` |
| `channel` | `ui` |
| `human_role` | Create, review, approve, merge, close PRs |
| `agent_role` | Create PRs, review diffs, comment, request changes |
| `high_risk` | true (merge is high-risk) |

**Key actions:**
- `create-pr` — active, agent_eligible: true, gh: `gh pr create`
- `review-pr` — trusted, agent_eligible: true, gh: `gh pr review`
- `approve-pr` — steward, agent_eligible: false (human only), gh: `gh pr review --approve`
- `merge-pr` — operator-only, agent_eligible: false, gh: `gh pr merge`
- `close-pr` — trusted, agent_eligible: true, gh: `gh pr close`
- `reopen-pr` — trusted, agent_eligible: true, gh: `gh pr reopen`

### 2.4 Actions (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-actions-ui` |
| `channel` | `ui` |
| `human_role` | View CI runs, rerun workflows, manage secrets |
| `agent_role` | View CI status, rerun failed jobs |
| `high_risk` | true (secrets management) |

**Key actions:**
- `view-runs` — active, agent_eligible: true, gh: `gh run list`
- `view-run-logs` — active, agent_eligible: true, gh: `gh run view --log`
- `rerun-failed` — trusted, agent_eligible: true, gh: `gh run rerun --failed`
- `rerun-all` — steward, agent_eligible: false, gh: `gh run rerun`
- `manage-secrets` — operator-only, agent_eligible: false, gh: `gh secret set`

### 2.5 Projects (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-projects-ui` |
| `channel` | `ui` |
| `human_role` | Manage project boards, columns, cards |
| `agent_role` | Read project status (limited) |
| `high_risk` | false |

### 2.6 Security and Quality (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-security-ui` |
| `channel` | `ui` |
| `human_role` | Manage advisories, alerts, code scanning, Dependabot |
| `agent_role` | Read security alerts (read-only) |
| `high_risk` | true |

**Key actions:**
- `view-alerts` — active, agent_eligible: true, gh: `gh api /repos/{owner}/{repo}/alerts`
- `manage-alerts` — operator-only, agent_eligible: false
- `manage-advisories` — operator-only, agent_eligible: false

### 2.7 Insights (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-insights-ui` |
| `channel` | `ui` |
| `human_role` | View repo analytics, traffic, contributors, dependency graph |
| `agent_role` | Read insights for audit |
| `high_risk` | false |

### 2.8 Settings (UI)

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-settings-ui` |
| `channel` | `ui` |
| `human_role` | Configure repo settings, branches, rules, webhooks, secrets |
| `agent_role` | None — settings are operator-only |
| `high_risk` | true |

**All actions are operator-only, agent_eligible: false.**

### 2.9 gh CLI

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-cli` |
| `channel` | `cli` |
| `human_role` | Execute GitHub operations from terminal |
| `agent_role` | Primary agent surface for GitHub operations |
| `high_risk` | false (commands inherit authority from target surface) |

**Sub-surfaces:**
- `gh issue` — maps to Issues UI
- `gh pr` — maps to Pull Requests UI
- `gh run` — maps to Actions UI
- `gh repo` — maps to Code/Settings UI
- `gh api` — raw API access (authority depends on endpoint)

### 2.10 API

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-api` |
| `channel` | `api` |
| `human_role` | Programmatic access for automation |
| `agent_role` | Programmatic access behind authority gates |
| `high_risk` | true (raw API can access anything) |

### 2.11 TUI

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-tui` |
| `channel` | `tui` |
| `human_role` | Terminal UI for GitHub (e.g., lazygit, gh-dash) |
| `agent_role` | Limited — TUIs are primarily human surfaces |
| `high_risk` | false |

### 2.12 IDE

| Field | Value |
|-------|-------|
| `surface_id` | `gh-surface-ide` |
| `channel` | `ide` |
| `human_role` | GitHub integration in VS Code, JetBrains, etc. |
| `agent_role` | Limited — IDE surfaces are primarily human |
| `high_risk` | false |

---

## 3. Authority Levels

| Level | Who | Can Do |
|-------|-----|--------|
| `operator-only` | Human operator only | Settings, secrets, merge, delete |
| `steward` | Steward agents | Approve PRs, rerun all CI, manage labels |
| `trusted` | Trusted agents | Close issues, review PRs, rerun failed CI |
| `active` | Active agents | Create issues, comment, view runs |
| `probationary` | Probationary agents | Read-only + create issues in authorized repos |
| `candidate` | Candidate agents | Read-only only |

---

## 4. High-Risk Actions (Operator-Only)

These actions are **never** agent-eligible:

- Merging PRs (`gh pr merge`)
- Managing repo secrets (`gh secret set`)
- Managing repo settings (visibility, deletion, transfer)
- Managing branch protection rules
- Managing webhooks
- Managing Dependabot settings
- Dismissing security alerts
- Publishing GitHub Pages
- Creating/updating GitHub Actions workflows (requires `workflow` scope)

---

## 5. Receipt Fields

Every action receipt captures:

- `action_id` — the surface action performed
- `surface_id` — which surface was used
- `actor` — agent or human identity
- `authority_level` — authority level at time of action
- `timestamp` — when the action occurred
- `result` — success/failure
- `evidence_ref` — link to PR, issue, or run

---

## 6. Failure Modes

| Mode | Mitigation |
|------|-----------|
| `auth-failure` | Check `gh auth status` and required scopes |
| `rate-limit` | Exponential backoff + jitter |
| `permission-denied` | Verify actor authority level |
| `merge-conflict` | Rebase on target branch before retry |
| `ci-failure` | Investigate logs before rerun |
| `secret-leak` | Revoke secret, audit access, post incident |

---

## 7. Cross-References

- **IssueOps controller:** hummbl-governance#978
- **Review surface and write boundary:** hummbl-governance#981
- **hummbl-issueops repo packet:** hummbl-governance#1021
- **MPS doctrine:** hummbl-governance#92
- **Promotion-safety rubric:** arbiter#89
- **Agentic GitHub Actions vocabulary:** hummbl-governance#196

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Review required:** Human review for authority boundaries
