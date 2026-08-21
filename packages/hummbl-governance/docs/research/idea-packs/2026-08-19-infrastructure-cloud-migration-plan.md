# HUMMBL Cloud Migration Plan (7-Phase)

| Field | Value |
|-------|-------|
| **Status** | DRAFT — not yet ratified |
| **Author** | devin (operator-seeded) |
| **Created** | 2026-08-19 |
| **Session** | continuation of Gitea→GitHub migration session |
| **Peer review** | see `2026-08-19-infrastructure-cloud-migration-peer-review.md` |
| **Decisions pending** | operator has explicitly deferred final decisions to a future session |

---

## Context

The operator signed up for an UpCloud free trial and added the API key to
1Password (`HUMMBL-UPCLOUD-API-KEY`, id `imnhxfqtwa7wpatigaywmvj6xe`).
This plan describes how HUMMBL could migrate from a desktop-centric
architecture to a multi-region cloud architecture using UpCloud, Hetzner,
and Cloudflare.

The operator's directive: "think bigger... to the point where we will
probably break stuff and then have the useful problem of fixing it."

---

## Current State (verified 2026-08-19)

HUMMBL is a **desktop-centric system**:

- **Anvil** (Windows): Gitea production (:3030), GitHub Actions runner,
  GPU inference (RTX 3080 Ti), agent configs, GPG keys, 1Password
- **hummbl-vps** (Ubuntu, Hetzner): bus bridge (:18790), bus state TSV
- **Delta** (Windows): secondary desktop, GPG key, agent configs
- **slate** (Ubuntu): mobile ops, fleet SSH
- **nodezero**: DORMANT since 2026-07-13
- **huxley**: RETIRED 2026-08-09

Source: `~/.agents/rules/machine-roster.md`

### What runs where today

| Service | Location | Limitation |
|---------|----------|------------|
| Bus (TSV) | hummbl-vps | Single-writer, no concurrency, no queries |
| Gitea | Anvil :3030 | Windows, dies when Anvil reboots |
| CI runner | Anvil (Windows) | WSL-based, keeps breaking |
| GPU inference | Anvil RTX 3080 Ti | VRAM ceiling, competes with desktop work |
| MCP servers | Anvil | Die on reboot |
| Agent runtimes | Anvil (session-only) | Ephemeral — exist only during sessions |
| Governance primitives | Python library (PyPI) | Not deployed as a service |

---

## UpCloud Account (verified 2026-08-19 via API)

**Account**: `hummbl` | **Credits**: 50,000

### Trial resource limits

| Resource | Limit |
|----------|-------|
| CPU cores (total) | 6 |
| RAM (total) | 12 GB |
| Public IPv4 | 2 |
| Public IPv6 | 3 |
| Storage (any tier) | 10 TB |
| Networks | 3 |
| Managed databases | 1 |
| Managed databases (dev) | 1 |
| Managed Kubernetes | 1 |
| Load balancers | 1 |
| GPUs | 0 (trial doesn't include GPU plans) |

### Zones (15 available)

us-chi1, us-nyc1, us-sjo1, uk-lon1, de-fra1, nl-ams1, fi-hel1, fi-hel2,
dk-cph1, es-mad1, pl-waw1, se-sto1, no-svg1, au-syd1, sg-sin1

### Key pricing (verified from `/price` API endpoint)

| Resource | Price/mo |
|----------|----------|
| 1xCPU-1GB (MaxIOPS, 25GB) | $0.97 |
| 1xCPU-2GB (MaxIOPS, 50GB) | $1.93 |
| 2xCPU-4GB (MaxIOPS, 80GB) | $3.87 |
| 4xCPU-8GB | $7.74 |
| Managed PostgreSQL (1x1xCPU-1GB-10GB) | $1.11 |
| IPv4 address | $0.53 |
| IPv6 address | $0.00 (free) |
| Egress traffic | $0.00 (zero-cost egress, Fair Transfer Policy) |
| Firewall | $0.00 (free) |
| SDN Private Network | $0.00 (free) |

### GPU pricing (post-trial)

| GPU plan | Price/mo |
|----------|----------|
| 1x L4 (12xCPU-128GB) | $69 |
| 1x L40S (12xCPU-128GB) | $142.50 |
| 1x H100 (12xCPU-240GB) | $189 |
| 2x H100 (24xCPU-480GB) | $378 |
| 1x B200 (24xCPU-240GB) | $520 |
| 8x H100 (96xCPU-1920GB) | $1,512 |
| 8x B200 (192xCPU-1920GB) | $4,160 |

### Egress policy

UpCloud has **zero-cost egress** under their Fair Transfer Policy. Even
if the fair transfer limit is exceeded, there are no excess fees —
bandwidth is throttled to 100 Mbps for the remainder of the month.
Optional unlimited egress at $0.01/GB.

This is a significant advantage over AWS/GCP/Azure ($0.08-0.12/GB egress).

### OS templates (41 available)

Ubuntu 24.04/22.04, Debian 12/13, Fedora 42/43, AlmaLinux 9/10,
Rocky 9/10, CentOS Stream 9/10, Ubuntu 24.04 with NVIDIA drivers.

---

## What Changes (Today vs After)

| Today | After |
|-------|-------|
| Bus is a TSV file on one VPS | Bus is a distributed service backed by PostgreSQL |
| Agents run when operator is at keyboard | Agents run 24/7 on cloud VMs as always-on services |
| Gitea on Anvil:3030 (Windows) | Gitea on UpCloud VM (Linux), PostgreSQL backend |
| CI on Windows self-hosted runners | CI on Linux runners in UpCloud + Windows runner for Windows tests |
| GPU inference on Anvil RTX 3080 Ti | GPU inference on UpCloud GPU plans — no VRAM ceiling |
| MCP servers die when Anvil reboots | MCP servers run as managed services with auto-restart |
| Governance primitives are a Python library | Governance primitives are a deployed API with web UI |
| Operator's desktop is the data plane | Operator's desktop is the control plane |
| Port knowledge scattered across 7 files | Port Authority registry |

---

## What Breaks (the useful problems)

1. **All PowerShell tooling** — cloud VMs are Linux. Every `bus-post.ps1`,
   `check-runner-health.ps1`, `disk-pressure-scan.ps1` needs a Python/bash
   equivalent.

2. **The file-based bus** — moving from TSV to PostgreSQL breaks every
   `bus-global.py` assumption. The bus becomes a real database with
   queries, indexes, and consistency guarantees. But now we can do bus
   replay, time-range queries, and multi-writer concurrency.

3. **The human-in-the-loop timing** — if agents run 24/7, they can't wait
   for synchronous ACKs. We need async governance: agents post PROPOSALs,
   a review window opens, and if no human vetoes within N hours, it
   auto-promotes. This breaks the current Multi-step Checkpoint Protocol.

4. **Cost** — cloud VMs cost money every hour. We need FinOps:
   auto-shutdown for dev VMs, spot pricing for batch jobs, cost alerts.

5. **The Windows/Linux split** — half the fleet is Windows, half is Linux.
   The skill portability standard already says "no hardcoded
   machine-specific paths" but we've been violating it with PowerShell
   scripts. Going cloud forces compliance.

6. **Single-region → multi-region** — if we deploy in Helsinki + Chicago,
   the bus needs to handle cross-region latency. The current single-writer
   TSV model breaks.

7. **Security surface** — cloud VMs have public IPs. Tailscale mesh helps,
   but we need firewall rules, SSH key management, and the UpCloud
   firewall service.

---

## The 7-Phase Build Plan

### Phase 1: Cloud foundation (beachhead)
- Provision first UpCloud VM (1xCPU-2GB, Ubuntu 24.04, ~$1.93/mo)
- Join to Tailscale mesh
- Install Python, git, bus-global.py
- This is the beachhead — everything else deploys from here

### Phase 2: Bus migration (breaks the TSV)
- Provision UpCloud managed PostgreSQL (1x1xCPU-1GB-10GB, $1.11/mo)
  OR self-hosted PostgreSQL on a database VM
- Migrate bus state from TSV → PostgreSQL
- Rewrite bus-global.py to use PostgreSQL (with TSV fallback for local dev)
- **Highest-risk change — the bus is the spine of everything**

### Phase 3: Gitea migration (breaks the Windows dependency)
- Provision UpCloud VM (2xCPU-4GB, $3.87/mo)
- Install Gitea with PostgreSQL backend
- Migrate all 102 repos from Anvil Gitea → UpCloud Gitea
- Anvil Gitea becomes a mirror, not the primary
- Breaks: all Gitea webhook URLs, all CI runner configs, the `tea` CLI hostname

### Phase 4: Always-on agents (breaks the session model)
- Deploy agent runtimes on UpCloud VMs as systemd services
- Agents poll the bus for work, execute, post results
- No operator needed for routine tasks
- Breaks: the "agent runs during session" model, the cost model, the governance timing

### Phase 5: GPU inference offload (breaks the API dependency)
- Provision UpCloud GPU VM (1xL4, $69/mo) — post-trial
- Self-host Qwen, Llama, DeepSeek models
- Route agent inference to self-hosted models first, API providers as fallback
- Breaks: the API cost model, the model-tier-policy.md assumptions

### Phase 6: Multi-region (breaks single-region assumptions)
- Deploy second bus node in a different zone
- PostgreSQL primary/replica across regions
- Breaks: latency assumptions, consistency model, the single-writer bus protocol

### Phase 7: Managed Kubernetes (breaks the VM model)
- Containerize all HUMMBL services
- Deploy on UpCloud managed K8s
- Auto-scaling, self-healing, rolling updates
- Breaks: the "SSH into a VM" ops model, the systemd service files
- **Note: infeasible within trial limits — post-trial only**

---

## Trial-Phase Cost Estimate

| Resource | Plan | Cost/mo |
|----------|------|---------|
| VM 1: Bus + agent host | 1xCPU-2GB | $1.93 |
| VM 2: Gitea | 2xCPU-4GB | $3.87 |
| Managed PostgreSQL | 1x1xCPU-1GB-10GB | $1.11 |
| IPv4 ×2 | | $1.07 |
| **Trial total** | | **~$8/mo** |

Post-trial with GPU:
| GPU VM (1xL4) | $69 |
| **Full stack** | **~$77/mo** |

---

## References

- UpCloud API key: 1Password item `HUMMBL-UPCLOUD-API-KEY` (id `imnhxfqtwa7wpatigaywmvj6xe`)
- UpCloud API: `https://api.upcloud.com/1.3` (Bearer token auth)
- Machine roster: `~/.agents/rules/machine-roster.md`
- Port Authority IDEA PACK: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-port-authority.md`
- Peer review: `hummbl-governance/docs/research/idea-packs/2026-08-19-infrastructure-cloud-migration-peer-review.md`
- UpCloud account data: `hummbl-governance/docs/research/idea-packs/2026-08-19-upcloud-account-data.md`
- Zero-cost egress docs: https://upcloud.com/docs/products/networking/billing/
- Fair Transfer Policy: https://upcloud.com/fair-transfer-policy/
