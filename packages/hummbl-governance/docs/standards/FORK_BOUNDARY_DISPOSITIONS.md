# Fork-Boundary File Dispositions

**Source audit:** `docs/standards/AUDIT_2026-06-25.md`
**Tracking issue:** #125
**Created:** 2026-06-25

## Summary

All 23 fork/import repos have `HUMMBL_FORK.md` (Phase 4 merged). All 23 are archived. Per HUMMBL Repo Standard §5.5, archived repos carry whatever they had at archival — no new required work unless still referenced as evidence.

| Artifact | Present | Missing | Required for archived? |
|----------|---------|---------|----------------------|
| HUMMBL_FORK.md | 23/23 | 0 | Yes (Phase 4 — done) |
| AGENTS.md | 5/23 | 18 | No (§5.5 — archived) |
| KRINEIA.md | 0/23 | 23 | No (§5.5 — archived) |
| hummbl.repo.yaml | 0/23 | 23 | No (§5.5 — archived) |

## Disposition: archived-no-new-work

All 23 fork repos receive the disposition **archived-no-new-work**. Rationale:

1. All 23 have `HUMMBL_FORK.md` — the primary boundary file that distinguishes upstream authority from HUMMBL authority
2. All 23 are archived — per §5.5, no new required work
3. None are referenced as evidence in compliance matrices or governance claims — they appear only in audit inventory tables
4. Public archived forks have `HUMMBL_FORK.md` visible on GitHub, satisfying the acceptance criterion: "Public archived forks cannot be mistaken for HUMMBL-maintained source-of-record code"

## Per-repo dispositions

| Repo | HUMMBL_FORK.md | AGENTS.md | Archived | Disposition | Notes |
|------|---------------|-----------|----------|-------------|-------|
| CL4R1T4S | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| G0DM0D3 | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| L1B3RT4S | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| NATURALIS-FUTURA | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| OBLITERATUS | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| Real-Time-Voice-Cloning | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| ST3GG | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| V3SP3R | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| autoresearch | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| awesome-ai-agents | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| awesome-ai-agents-1 | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| awesome-ai-agents-2026 | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| awesome-python | Y | Y | Y | archived-no-new-work | Archived fork — has AGENTS.md |
| cli | Y | N | Y | archived-no-new-work | Archived fork (HTTPie), has boundary file |
| deer-flow | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| hermes-agent | Y | Y | Y | archived-no-new-work | Archived fork — has AGENTS.md |
| markitdown | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| open_teamsuzie | Y | Y | Y | archived-no-new-work | Archived fork — has AGENTS.md |
| paramiko | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| rich | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| sint-protocol | Y | Y | Y | archived-no-new-work | Archived fork — has AGENTS.md |
| skills | Y | N | Y | archived-no-new-work | Archived fork, has boundary file |
| vllm | Y | Y | Y | archived-no-new-work | Archived fork — has AGENTS.md |

## Acceptance criteria status

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Every fork/import repo has a recorded disposition | Done | All 23 have disposition: archived-no-new-work |
| At least one real fork contains a localized HUMMBL_FORK.md | Done | All 23 have HUMMBL_FORK.md (Phase 4) |
| Arbiter/fleet_verify.py can verify fork-boundary separately | Pending | Arbiter would need a fork-specific check — deferred to Arbiter roadmap |
| Public archived forks cannot be mistaken for HUMMBL code | Done | All public forks have visible HUMMBL_FORK.md |
| Refreshed audit links to this work item | Done | AUDIT_2026-06-25.md references #125 |

## If a fork is unarchived in the future

If any fork repo is unarchived for active use, the following artifacts become required per §5.4:
1. `AGENTS.md` — agent operating contract
2. `KRINEIA.md` — repo-local receipt manifest
3. `hummbl.repo.yaml` — machine-readable registry atom

The existing `HUMMBL_FORK.md` remains valid and does not need to be re-created.

## References

- Standard: `docs/standards/HUMMBL_REPO_STANDARD.md` §5.4 (forks) and §5.5 (archived)
- Audit: `docs/standards/AUDIT_2026-06-25.md`
- Issue: #125
- Phase 4: Fork-boundary layer (merged)
