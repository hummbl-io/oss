# Agent Toolset Starter Pack (hummbl-governance)

Status: approved for hummbl-governance
Owner: codex
Scope: high-value `.py` utilities + CI workflows agents can run repeatedly

Use this as the first-step rollout for other repos: drop this document in the
same location, update file paths to that repo, and keep the cadence rows.

## 1) Core hummbl-governance toolset (approved)

The following files are the first wave to standardize as agent-owned telemetry:

| File | Why it is high value |
| --- | --- |
| `scripts/issue_pr_draft_coverage.py` | Issue/PR coverage + optional promotion automation |
| `scripts/pr_census.py` | PR and branch drift snapshot |
| `scripts/claim_drift.py` | Claim/lineage drift detection |
| `scripts/check-dependencies.py` | Dependency drift and pinning checks |
| `scripts/anvil_git_signing_audit.py` | Git signing/toolchain health checks |
| `scripts/audit-github-actions.py` | CI workflow health diagnostics |
| `scripts/financial_pulse.py` | Spend/usage telemetry |
| `scripts/ops/keepalive_fleet_loop.py` | Fleet liveness watchdog |
| `hummbl_governance/services/health.py` | Runtime health surface |
| `hummbl_governance/services/scheduler.py` | Scheduler wiring and state |
| `hummbl_governance/bus/bus_writer.py` | Canonical bus write path |
| `hummbl_governance/bus/bus_verifier.py` | Bus integrity checks |
| `hummbl_governance/quality/monitor.py` | Quality telemetry output |
| `hummbl_governance/quality/analyzer.py` | Quality signal generator |
| `hummbl_governance/state_authority.py` | Authority/permission checks |

## 2) Rollout order (today)

### Daily (operator handoff lane)
- `python scripts/check-dependencies.py`
- `python scripts/pr_census.py`
- `python scripts/claim_drift.py`
- `python scripts/financial_pulse.py`

### Per-PR or pre-merge checks
- `python scripts/anvil_git_signing_audit.py`
- `python scripts/audit-github-actions.py`
- `python scripts/pr_census.py`
- `python scripts/issue_pr_draft_coverage.py --repo hummbl-io/hummbl-governance --json`

### Incident / suspicious drift
- `python hummbl_governance/services/health.py` (where run target supports it)
- `python scripts/issue_pr_draft_coverage.py --repo <OWNER>/<REPO> --json`
- `python scripts/ops/keepalive_fleet_loop.py`
- `python hummbl_governance/bus/bus_verifier.py` (or the equivalent runtime entry in that repo)

## 3) Cross-repo replication template

To onboard another repo to this baseline:

1. Add the same `docs/operations/AGENT_TOOLSET_STARTER.md` file (or a tailored copy).
2. Confirm equivalent tooling paths; if a listed file is absent, replace with the
   repo-native equivalent and keep the intent in the table.
3. Add/adjust CI jobs to persist outputs under a repo-visible telemetry path
   (e.g. `_state/ci/agent-toolset-*.json|md`).
4. Start with check-mode only for any promotive actions.
5. Run the same two commands after each onboarding:
   - `python scripts/pr_census.py`
   - `python scripts/issue_pr_draft_coverage.py --json`

## 4) Copy/paste agent command list (single run)

```bash
python scripts/check-dependencies.py
python scripts/financial_pulse.py
python scripts/pr_census.py
python scripts/claim_drift.py
python scripts/issue_pr_draft_coverage.py --repo hummbl-io/hummbl-governance --json
python scripts/anvil_git_signing_audit.py
python scripts/audit-github-actions.py
```

## 4b) Repo onboarding helper

Use this when you want telemetry for another repository in the same family:

```bash
python scripts/agent_toolset_scaffold.py --repo <repo_path>
python scripts/agent_toolset_scaffold.py --repo <repo_path> --format json
python scripts/agent_toolset_scaffold.py --repo <repo_path> --copy-template
```

## 5) Repository expansion guidance

- Keep this set in phase-0 for any repo that supports GitHub issue/PR automation.
- For repos without GitHub, gate on local equivalent scripts and document the gap in
  the table entry.
- If a repo has a stricter approval model, keep dry-run/read-only equivalents as
  default and only flip to mutate mode with explicit approval in CI.

---

Last updated: 2026-07-03
