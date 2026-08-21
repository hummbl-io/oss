# Runner-Isolation Policy v0.1

**Status:** APPROVED by operator (2026-08-19)
**Author:** devin @ anvil
**Unblocks:** hummbl-production #857, #838, hummbl-bibliography #138

## Problem

Three P0 issues share one root cause: no approved self-hosted validation path for PR-controlled code that satisfies both the no-hosted-minutes prohibition and the runner-isolation requirement.

## Policy

All PR-triggered CI for untrusted/PR-controlled code must run on an isolated, ephemeral runner.

### Definition: untrusted/PR-controlled code

- Fork PRs (already blocked by same-repo guard)
- Dependabot PRs (currently admitted — this is the gap)
- Any PR where the head branch is not owned by an authorized fleet agent

### Approved execution topologies (priority order)

1. **Ephemeral self-hosted runner** — destroyed after each job (container-based, no persistent state). Preferred.
2. **Dedicated Dependabot runner** — separate self-hosted runner with `dependabot` label, no shared state with trusted CI. Persistent but isolated.
3. **GitHub-hosted runners with `pull_request_target`** — ONLY for read-only checks that do not execute PR-controlled code.

### Prohibited

- GitHub-hosted runners for any step that executes PR-controlled code
- Persistent self-hosted runners (Anvil, Delta) for Dependabot/fork PRs

## Implementation

1. Create `dependabot-isolated` label on repos with Dependabot enabled (DONE: hummbl-production, hummbl-bibliography)
2. Provision an ephemeral or dedicated runner with the `dependabot` label
3. Update workflow `runs-on:` for Dependabot-triggered workflows to use the isolated runner
4. Extend the fork-PR guard to route Dependabot branches to the isolated runner
5. Document in this file as the fleet-wide standard

## Current state (2026-08-19)

- Dashboard workflows (`dashboard.yml`, `dashboard-pr-check.yml`, `dashboard-build.yml`) already on `[self-hosted, Linux, hummbl-ci]` via PR #908 (merged)
- Remaining workflows still on `ubuntu-latest` — these need evaluation for whether they execute PR-controlled code
- `dependabot-isolated` label created on hummbl-production and hummbl-bibliography
- Runner provisioning: PENDING operator decision on topology (ephemeral container vs dedicated runner)

## Acceptance criteria

- [x] No PR-validation path consumes GitHub-hosted Actions minutes (for dashboard workflows)
- [ ] No Dependabot/fork PR executes on a persistent trusted runner
- [ ] Isolated runner provisioned and labeled
- [ ] Workflows updated to route untrusted PRs to isolated runner
- [x] Policy documented in hummbl-governance
