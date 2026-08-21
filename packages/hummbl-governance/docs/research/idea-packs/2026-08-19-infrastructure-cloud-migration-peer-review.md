# Peer Review: HUMMBL Cloud Migration Plan (7-Phase)

| Field | Value |
|-------|-------|
| **Reviewer** | devin (self-review under goldplate-bespoke mode) |
| **Date** | 2026-08-19 |
| **Plan reviewed** | `2026-08-19-infrastructure-cloud-migration-plan.md` |
| **Verdict** | ADAPT — not ADOPT (phase ordering wrong), not AVOID (direction correct) |

---

## Executive Summary

The plan proposes a seven-phase migration of HUMMBL's infrastructure from
a desktop-centric model to a multi-region cloud architecture spanning
UpCloud, Hetzner, and Cloudflare. The plan is ambitious, honest about
breakage, and correctly identifies the cultural and governance shifts
that cloud adoption forces. However, the review finds **three critical
findings** that, if unaddressed, will cause the migration to stall or
reverse at Phase 2 or Phase 4, and **five secondary findings** that
represent missing abstractions, unhandled edge cases, or factual errors
in the cost model. A revised phase ordering is proposed at the end.

The plan's greatest strength — its willingness to name what breaks — is
also its greatest risk: the named breakages are treated as inevitable
consequences rather than design constraints that should shape the phase
ordering itself. A plan that says "this will break the bus protocol" and
then places that breakage at Phase 2, without first preparing the
governance model that the broken protocol will need, is a plan that
optimizes for infrastructure momentum over operational safety.

---

## Strengths Worth Acknowledging

1. **Honest breakage inventory.** The plan names seven specific things
   that break. This is more honest than most migration plans, which
   typically discover breakage during execution.

2. **Concrete cost estimates with plan names.** The cost table cites
   specific UpCloud plan names and dollar amounts sourced from the API
   price endpoint. This is verifiable.

3. **Phased approach with dependency ordering.** Each phase has a clear
   deliverable.

4. **Recognition that the operator's desktop becomes the control plane.**
   This is the correct mental model for the end state.

---

## Critical Findings

### C1: Governance model must change BEFORE Phase 4, not during it

**Finding**: The plan places "always-on agents" at Phase 4 and
acknowledges that this "breaks the current Multi-step Checkpoint
Protocol which assumes synchronous operator presence." However, the plan
proposes no solution and treats it as a Phase 4 problem. This is a
sequencing error. The governance change is a **dependency** of Phase 4,
not a **consequence** of it.

**Evidence**: The AGENTS.md Multi-step Checkpoint Protocol (origin:
2026-08-12 AAR) states: "pause after each step for operator ACK before
starting the next step... Do not auto-proceed to the next step based on
a green CI check alone." This protocol is **synchronous by
construction**. If agents run 24/7 on cloud VMs, they will post
PROPOSALs and then block indefinitely waiting for an ACK that may not
come for 8 hours (operator sleep) or 3 days (operator travel).

**Caveat**: One might argue that the operator can ACK asynchronously via
the bus, and that the protocol already accommodates this ("If the
operator does not ACK, hold at the checkpoint"). But the protocol says
"hold" — it does not say "auto-promote after N hours." The protocol has
no timeout-based escalation path. Adding one is a governance change that
requires an ADR.

**Implication**: The governance change (async ACK with timeout-based
escalation) should be a **Phase 0** — a documentation and protocol
change that precedes any infrastructure work. If we deploy always-on
agents (Phase 4) without the governance model in place, we will either
violate the protocol (erosion of governance authority) or deadlock the
agents (waste of cloud spend).

**Recommended action**: Draft an IDEA PACK for async governance before
provisioning any VM. The IDEA PACK should propose: (a) a review window
duration (e.g., 4 hours for STATUS, 24 hours for PROPOSAL, 72 hours for
DECISION), (b) an auto-promotion rule for non-privileged types, (c) a
veto-only model for the operator (silence = consent, not silence =
block), and (d) a rollback path for auto-promoted decisions that the
operator disagrees with retroactively.

### C2: The managed database constraint makes Phase 2 and Phase 3 mutually exclusive

**Finding**: The plan assigns the single managed PostgreSQL instance to
the bus (Phase 2) and then proposes Gitea migration with a PostgreSQL
backend (Phase 3). The UpCloud trial resource limits, verified via the
API on 2026-08-19, show `managed_databases: 1` and
`managed_databases_dev: 1`. This means the account gets **one** managed
PostgreSQL instance. If it is used for the bus, Gitea cannot use it. If
it is used for Gitea, the bus cannot use it.

**Evidence**: The API response (verified 2026-08-19 from `GET /account`)
shows `"managed_databases": 1, "managed_databases_dev": 1`. The cheapest
managed PostgreSQL plan (1x1xCPU-1GB-10GB) costs $1.11/mo. The plan's
cost table includes this line item once. There is no second managed
database in the cost estimate.

**Caveat**: It may be argued that Gitea can use SQLite (which it
supports) or that a self-hosted PostgreSQL instance can run on the Gitea
VM alongside Gitea itself. Both are technically possible. However,
SQLite for Gitea in production is explicitly discouraged by the Gitea
project for multi-user scenarios, and self-hosted PostgreSQL on a
2xCPU-4GB VM running Gitea simultaneously is a resource contention risk
that defeats the purpose of using a managed database for the bus.

**Implication**: The plan must make an explicit choice: (a) the managed
database goes to the bus, and Gitea runs on self-hosted PostgreSQL on
its own VM; (b) the managed database goes to Gitea, and the bus runs on
self-hosted PostgreSQL on the bus VM; or (c) both run on self-hosted
PostgreSQL on a single "database VM," and the managed database is
reserved for a future service (e.g., Langfuse). Option (c) is the most
architecturally sound because it keeps the database layer separate from
the application layer, but it adds a VM to the cost estimate.

**Recommended action**: Revise the cost table to include a dedicated
database VM (1xCPU-2GB, $1.93/mo) running self-hosted PostgreSQL for
both the bus and Gitea. Reserve the managed database for Langfuse or a
future managed service. This adds $1.93/mo to the trial cost (from ~$8/mo
to ~$10/mo) but eliminates the mutual exclusivity.

### C3: No rollback plan for any phase

**Finding**: The plan is entirely forward-moving. Every phase describes
what to build and what breaks, but no phase describes how to retreat if
the migration fails. This is a critical omission for a plan that
explicitly says "we will probably break stuff." Breaking stuff without a
retreat path is not engineering; it is gambling.

**Evidence**: The plan contains zero instances of the words "rollback,"
"revert," "retreat," "cutover," or "dual-running." The closest it comes
is "Anvil Gitea becomes a mirror, not the primary" (Phase 3), which
implies a one-way cutover with no described path back.

**Caveat**: One might argue that the GitHub mirrors (which already exist
for all 102 repos) serve as a rollback path for Gitea. This is partially
true — the git data is safe. But the Gitea metadata (issues, PRs, users,
webhooks, CI configs) is not in the GitHub mirrors. A Gitea rollback
without metadata is a partial rollback at best.

**Implication**: Every phase needs a rollback plan. At minimum:
- **Phase 2 (bus migration)**: Dual-write period where both TSV and
  PostgreSQL are written simultaneously. Reads come from PostgreSQL. If
  PostgreSQL fails, reads fall back to TSV. After N days of stable
  dual-write, cut over to PostgreSQL-only. Keep TSV as a cold backup for
  30 days.
- **Phase 3 (Gitea migration)**: Dual-running period where both Anvil
  Gitea and UpCloud Gitea are active. Webhooks fire to both. New commits
  go to both (via mirror push). After N days, cut webhooks to UpCloud
  only. Keep Anvil Gitea as a cold standby for 30 days.
- **Phase 4 (always-on agents)**: Start with one agent on one VM. If the
  agent makes a bad autonomous decision, the blast radius is one VM, not
  the whole fleet. Scale up only after the one-agent trial is stable.

**Recommended action**: Add a "Rollback plan" subsection to each phase.
The rollback plan must specify: (a) the dual-running period, (b) the
cutover trigger, (c) the retreat trigger, (d) the data preservation
strategy during retreat.

---

## Secondary Findings

### S1: Traffic/egress cost concern is invalidated — zero-cost egress is a major advantage

The plan does not mention traffic/egress costs. I initially flagged this
as a missing cost. However, verified research (UpCloud documentation,
2026-08-19) confirms that UpCloud has **zero-cost egress** under their
Fair Transfer Policy. Even if the fair transfer limit is exceeded, there
are no excess fees — bandwidth is throttled to 100 Mbps for the remainder
of the month. Optional unlimited egress is available at $0.01/GB.

This is a significant competitive advantage over AWS/GCP/Azure (which
typically charge $0.08-0.12/GB for egress) and should be explicitly
called out in the plan as a reason to prefer UpCloud for bus and API
workloads that generate high egress. The plan undersells this advantage.

### S2: Helsinki zone choice is politically convenient but operationally suboptimal for the operator

The plan proposes Helsinki for all Phase 1-3 VMs, citing proximity to
the existing Hetzner VPS (also Europe). This is reasonable for
inter-server latency (Helsinki ↔ Hetzner Frankfurt is ~20ms). However,
the operator is in Eastern Time (established by the AGENTS.md PowerShell
UTC bug, which notes a 4-hour offset from UTC, consistent with ET). The
operator-to-Helsinki latency is approximately 90-110ms, compared to
approximately 15-25ms to Chicago (us-chi1) or New York (us-nyc1).

For the bus (which the operator interacts with via `bus-post.ps1` and
`bus-global.py`), this latency is negligible — the bus is not
interactive. But for Gitea (which the operator browses via web UI) and
for SSH sessions (which the operator uses for debugging), 100ms vs 20ms
is the difference between "feels local" and "feels slow."

**Recommended action**: Split the deployment across two zones from the
start. Bus and database in Helsinki (close to Hetzner, low inter-server
latency). Gitea and agent VMs in Chicago or New York (close to operator,
low interactive latency). This also prepares the architecture for Phase
6 (multi-region) without requiring a later migration.

### S3: Secret distribution to cloud VMs is unaddressed

The current model has 1Password on the operator's machine (Anvil). Cloud
VMs need secrets: the UpCloud API key, Gitea token, GitHub token, bus
bridge token, Tailscale auth key. The plan does not describe how cloud
VMs obtain these secrets.

Options that should be evaluated:
- **1Password CLI on cloud VMs**: Requires 1Password account credentials
  on the VM, which creates a chicken-and-egg problem.
- **Environment variables via cloud-init**: Secrets are passed in the VM
  creation request's user-data. Simple but secrets are visible in the
  UpCloud API to anyone with API access.
- **Tailscale SSH + 1Password Connect**: 1Password Connect is a
  self-hosted secrets broker that runs on the tailnet. VMs authenticate
  via Tailscale identity and fetch secrets from Connect. Most secure but
  adds infrastructure.
- **HashiCorp Vault**: Overkill for a 6-machine fleet, but the pattern is
  correct.

**Recommended action**: Add a Phase 1.5: "Deploy secret distribution."
The recommended approach is 1Password Connect on the beachhead VM,
accessible via Tailscale. All subsequent VMs fetch secrets from Connect
rather than receiving them via cloud-init.

### S4: Port Authority IDEA PACK is a dependency, not a side quest

The plan does not mention the Port Authority IDEA PACK that was drafted
earlier in this session. However, the cloud migration makes Port
Authority **more** urgent, not less. Cloud VMs introduce: public IPs (2
IPv4, 3 IPv6 in trial), firewall rules, security groups, SDN private
networks, load balancer ports, managed database ports, and Kubernetes
NodePorts/LoadBalancers. The port collision surface area increases by an
order of magnitude.

**Recommended action**: Port Authority should be Phase 0.5 — after the
async governance ADR (Phase 0) and before the beachhead VM (Phase 1).
The registry should be populated with the planned cloud port assignments
before any VM is provisioned.

### S5: Phase 7 (managed Kubernetes) is infeasible within trial limits

The plan places managed Kubernetes at Phase 7. The UpCloud trial allows
`managed_kubernetes: 1` — one K8s cluster. However, a functional K8s
cluster requires at least 1 control plane node and 1-2 worker nodes. The
trial's total resource limit is 6 cores and 12GB RAM. A minimal K8s
cluster (1 control plane + 2 workers) consumes at minimum 3 cores and
6GB RAM, leaving 3 cores and 6GB for everything else — which is not
enough to run the bus, Gitea, agents, and the database.

**Recommended action**: Phase 7 should be explicitly marked as
**post-trial**. The trial phases are 1-6. Phase 7 begins when the trial
converts to a paid account or when the operator explicitly authorizes
exceeding trial limits.

---

## Missing Abstractions (Bespoke Lens)

### A1: Bus transport interface (Strategy pattern)

The bus migration from TSV to PostgreSQL is described as a rewrite of
`bus-global.py`. This is the wrong abstraction level. The correct
approach is to extract a `BusTransport` interface with two
implementations: `TSVTransport` (current) and `PostgreSQLTransport`
(new). The `bus-global.py` CLI becomes a thin client that selects the
transport via configuration.

```
bespoke: The second transport (PostgreSQL) is coming in Phase 2.
The third transport (gRPC for cross-region) is coming in Phase 6.
The interface must be defined before the first transport is replaced.
```

This abstraction earns its test: a `BusTransportContractTest` that
verifies any transport implementation can post, read, tail, and search
messages.

### A2: VM provisioning as code (Factory pattern)

The plan describes VM provisioning as manual API calls. For a 6-VM
deployment, manual provisioning is acceptable. For a multi-region
deployment with rollback capability, it is not. The plan should specify
a `VMFactory` that takes a VM spec (zone, plan, OS, Tailscale auth key,
cloud-init script) and returns a provisioned VM.

### A3: Cost monitoring (Observer pattern)

The plan mentions FinOps as a Phase 4+ concern. But cost monitoring
should be deployed with the first VM (Phase 1). A daily cost observer
that posts a bus STATUS with the current spend (queried from UpCloud API)
would catch runaway costs before they become a trial-limit problem.

---

## Revised Phase Ordering

| Phase | Content | Rationale |
|-------|---------|-----------|
| **Phase 0** | Async governance ADR + Port Authority registry | Governance must precede always-on agents; port registry must precede cloud ports |
| **Phase 0.5** | Secret distribution design (1Password Connect on tailnet) | Cloud VMs need secrets before they can do anything |
| **Phase 1** | Beachhead VM (Chicago, close to operator) + Tailscale join + 1Password Connect | Foundation for all subsequent VMs |
| **Phase 1.5** | Cost observer (daily bus STATUS with spend) | Catch runaway costs early |
| **Phase 2** | Bus transport interface + PostgreSQL transport (dual-write with TSV) | Highest-risk change; needs rollback path |
| **Phase 2.5** | Database VM (self-hosted PostgreSQL for Gitea) | Resolves managed-DB mutual exclusivity (C2) |
| **Phase 3** | Gitea migration (dual-running with Anvil, webhook cutover) | Needs database VM from 2.5 |
| **Phase 4** | One always-on agent on beachhead VM (trial run) | Governance model from Phase 0 governs this |
| **Phase 5** | GPU offload (post-trial) | Trial limits don't include GPUs |
| **Phase 6** | Multi-region (Helsinki bus + Chicago Gitea) | Needs bus transport interface from Phase 2 |
| **Phase 7** | Managed Kubernetes (post-trial) | Trial limits can't run K8s + services |

---

## Falsification Tests for the Plan

- **F1**: If the operator can ACK bus PROPOSALs within 4 hours of
  posting, on average, for the next 30 days, then the async governance
  change (Phase 0) is unnecessary. If the operator cannot, Phase 0 is
  required before Phase 4. → Testable by measuring bus ACK latency over
  the next 30 days.

- **F2**: If the bus TSV file has fewer than 10,000 messages, the
  PostgreSQL migration is premature. If it has more than 50,000, the
  migration is justified. → Testable by counting lines in the current
  TSV.

- **F3**: If the operator's round-trip latency to Helsinki is less than
  50ms, the Helsinki-first zone choice is fine. If it is more than 80ms,
  the split-zone recommendation (S2) is justified. → Testable by
  `ping api.upcloud.com` from Anvil.

- **F4**: If no port collision has ever occurred in the fleet (search bus
  history for "address already in use" or "port already in use"), Port
  Authority is premature. If one has occurred, it is justified. →
  Testable by grepping bus history.

---

## Verdict

The plan is **ADAPT** — not ADOPT (the phase ordering is wrong and will
cause stalls) and not AVOID (the direction is correct and the cost model
is viable). The three critical findings (governance sequencing, managed
database exclusivity, missing rollback plans) must be addressed before
Phase 1 begins. The five secondary findings should be addressed in the
revised plan but are not blocking.

The plan's greatest risk is not technical — it is the governance model.
Infrastructure can be rolled back; governance precedents cannot. If
always-on agents begin operating under a synchronous governance model
that they cannot satisfy, the resulting governance violations will erode
the authority structure that makes HUMMBL safe. Fix the governance
first, then build the cloud.
