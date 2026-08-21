# Session Handoff: HUMMBL Cloud Mission (2026-08-19)

## Session context

This session was a continuation of a Gitea→GitHub migration session. The
operator pivoted mid-session to a new mission: UpCloud cloud
infrastructure integration. The operator's directive was "think bigger...
to the point where we will probably break stuff and then have the useful
problem of fixing it."

The operator explicitly deferred all final decisions to a future session.

---

## What was accomplished

### 1. Gitea mirror conversion completed (from prior session work)

- **89/89 mirror conversions succeeded** on Gitea (86 hummbl-io repos + 3
  foundermode-ai repos)
- **hummbl-bus fixed** — was a broken empty mirror (0 branches), deleted
  and re-migrated from GitHub, now has 13 branches and 606KB
- Bus STATUS posted at 2026-08-19T21:24:10Z

### 2. Port Authority IDEA PACK drafted

- **File**: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-port-authority.md`
- **Concept**: Persistent fleet-wide port registry with 3 layers
  (registry + allocator + scanner)
- **Extends** existing `port-map` skill (scanner) with allocation and
  drift-detection layers
- **4 decisions** for operator review: D1 registry location (recommended:
  apex-nexus), D2 allocation strategy (recommended: convention-first),
  D3 enforcement level (recommended: pre-start check + drift alert), D4
  scope (recommended: TCP only for v1)
- **Bus seed**: POSTED/2026-08-19T21:24:10Z (STATUS)
- **Pre-existing infra check**: 7+ files with scattered port knowledge,
  all stale or partial

### 3. UpCloud account explored and documented

- **API key**: 1Password item `HUMMBL-UPCLOUD-API-KEY` (id
  `imnhxfqtwa7wpatigaywmvj6xe`)
- **Auth**: Bearer token (not HTTP Basic)
- **Account data file**: `hummbl-governance/docs/research/idea-packs/2026-08-19-upcloud-account-data.md`
- **Key findings**:
  - Trial limits: 6 cores, 12GB RAM, 2 IPv4, 10TB storage, 1 managed DB,
    1 managed K8s, 0 GPUs
  - 15 zones (Chicago, NYC, San Jose, London, Frankfurt, Amsterdam,
    Helsinki x2, Copenhagen, Madrid, Warsaw, Stockholm, Stavanger,
    Sydney, Singapore)
  - **Zero-cost egress** (Fair Transfer Policy) — major advantage over
    AWS/GCP/Azure
  - Cheapest useful VM: DEV-1xCPU-1GB-10GB at $0.52/mo
  - GPU plans post-trial: L4 from $69/mo, H100 from $189/mo, B200 from
    $520/mo
  - 41 OS templates (Ubuntu 24.04, Debian 13, etc.)

### 4. Goal harness audited

- **270 total goals** | 102 done | 20 blocked | 0 active
- **0 goals mention UpCloud** — this is a greenfield mission
- **18 of 20 blocked goals** are infra-relevant and could be unblocked
  by cloud infrastructure
- **1 pending seed** (not yet goal-ified): autoresearch GPU pipeline
  followthrough with 7 goals

### 5. 7-phase cloud migration plan drafted

- **File**: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-plan.md`
- **Phases**: Beachhead VM → Bus PostgreSQL migration → Gitea migration
  → Always-on agents → GPU offload → Multi-region → Managed K8s
- **Trial cost estimate**: ~$8/mo (2 VMs + managed DB + 2 IPv4)
- **Post-trial with GPU**: ~$77/mo

### 6. Peer review completed

- **File**: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-peer-review.md`
- **Verdict**: ADAPT (not ADOPT — phase ordering wrong; not AVOID —
  direction correct)
- **3 critical findings**:
  - C1: Governance model must change BEFORE Phase 4, not during it
  - C2: Managed database constraint makes Phase 2 and 3 mutually
    exclusive (only 1 managed PostgreSQL in trial)
  - C3: No rollback plan for any phase
- **5 secondary findings**:
  - S1: Zero-cost egress is a major advantage (plan undersells it)
  - S2: Helsinki zone suboptimal for ET operator (recommend Chicago)
  - S3: Secret distribution unaddressed (recommend 1Password Connect)
  - S4: Port Authority is a dependency, not a side quest
  - S5: K8s infeasible within trial limits (post-trial only)
- **Revised phase ordering**: Phase 0 (governance ADR + Port Authority)
  → Phase 0.5 (secret distribution) → Phase 1 (beachhead) → Phase 1.5
  (cost observer) → Phase 2 (bus transport interface + dual-write) →
  Phase 2.5 (database VM) → Phase 3 (Gitea dual-running) → Phase 4
  (one-agent trial) → Phase 5 (GPU, post-trial) → Phase 6 (multi-region)
  → Phase 7 (K8s, post-trial)

### 7. 10 goals seeded into goal harness

- **Goal IDs**: `goal-20260819T220443Z-001-devin` through `-010-devin`
- **Total goals now**: 297 (was 270)
- **Goal 010** is the ratification gate — owned by the operator, must be
  completed before goals 004-009 can proceed

### 8. Bus SITREP posted

- Posted at 2026-08-19T22:05:08Z
- Request ID: `802b4b7147b44458b6d9d00d7e1303f4`
- Receipt durable: true

---

## Artifacts produced (all durable)

| Artifact | Path |
|----------|------|
| Port Authority IDEA PACK | `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-port-authority.md` |
| Cloud migration plan | `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-plan.md` |
| Peer review | `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-peer-review.md` |
| UpCloud account data | `hummbl-governance/docs/research/idea-packs/2026-08-19-upcloud-account-data.md` |
| Goal harness state | `~/.agents/goal-harness/state/state.json` (10 new goals) |
| Bus SITREP | bus request_id `802b4b7147b44458b6d9d00d7e1303f4` |

---

## What the next session needs to do

### Immediate (before any cloud provisioning)

1. **Read the four artifacts** in `hummbl-governance/docs/research/idea-packs/`
   (the four `2026-08-19-infrastructure-*` files)
2. **Present the plan and peer review to the operator** for ratification
   (goal 010)
3. **Operator decision needed**: ADOPT, ADAPT, or AVOID the revised
   phase ordering

### If operator ratifies (Phase 0)

4. **Draft async governance IDEA PACK** (goal 001) — review window
   durations, auto-promotion rules, veto-only model, rollback path
5. **Populate Port Authority registry** (goal 002) — all current fleet
   ports + planned cloud ports

### If operator ratifies (Phase 0.5)

6. **Deploy 1Password Connect** on tailnet (goal 003) — secret
   distribution for cloud VMs

### If operator ratifies (Phase 1)

7. **Provision beachhead VM** (goal 004) — us-chi1, 1xCPU-2GB, Ubuntu
   24.04, Tailscale-joined
8. **Deploy cost observer** (goal 005) — daily bus STATUS with spend

### Pending from prior session (not cloud-related)

- **Delete 7 empty repos** under hummbl-dev GitHub org (coaching,
  coaching-migrate, enterprise-group-control, enterprise-parent-control,
  lsat-prep, operator-site, operator.com) — requires
  `delete_repo` scope. The `gh auth refresh -h github.com -s delete_repo`
  was initiated but the operator had not yet authorized in the browser
  as of session end.
- **Create `Ownward` org on GitHub** — cannot be done via API, requires
  manual operator action.

---

## Key decisions the operator needs to make

| Decision | Context | Recommendation |
|----------|---------|----------------|
| Ratify cloud plan | Goal 010 | ADAPT with revised phase ordering |
| Registry location | Port Authority D1 | apex-nexus |
| Zone choice | Peer review S2 | Chicago (us-chi1) for operator-facing, Helsinki for bus |
| Database strategy | Peer review C2 | Self-hosted PostgreSQL on dedicated VM; reserve managed DB for Langfuse |
| Secret distribution | Peer review S3 | 1Password Connect on tailnet |
| Async governance | Peer review C1 | Draft IDEA PACK before any always-on agents |

---

## Session mode

- **Active skill**: goldplate-bespoke (full level) — may or may not
  persist to next session depending on operator preference
- **Active skill**: idea-pack — was invoked for the Port Authority IDEA
  PACK

---

## References

- UpCloud API docs: https://upcloud.com/docs/api/
- UpCloud pricing: https://upcloud.com/pricing/
- Zero-cost egress: https://upcloud.com/docs/products/networking/billing/
- Fair Transfer Policy: https://upcloud.com/fair-transfer-policy/
- Machine roster: `~/.agents/rules/machine-roster.md`
- Multi-step Checkpoint Protocol: `AGENTS.md` (origin: 2026-08-12 AAR)
