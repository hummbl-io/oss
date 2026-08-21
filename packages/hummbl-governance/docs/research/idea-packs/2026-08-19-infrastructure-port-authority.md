# IDEA PACK: Port Authority

| Field | Value |
|-------|-------|
| **Status** | DRAFT |
| **Author** | devin (operator-seeded) |
| **Created** | 2026-08-19 |
| **Bucket** | infrastructure |
| **Topic** | port-authority |
| **Bus seed** | POSTED/2026-08-19T21:24:10Z (STATUS — review window not yet opened; PROPOSAL deferred pending operator direction) |
| **Review ask** | ADOPT / ADAPT / AVOID — should HUMMBL build a Port Authority as a persistent fleet-wide port registry, or is the existing `port-map` skill + ad-hoc conventions sufficient? |

---

## Summary

A **Port Authority** is a persistent, authoritative registry of network port allocations across the HUMMBL fleet (Anvil, Delta, Huxley, Slate, nodezero, hummbl-vps). It owns the mapping between ports and the services/agents/repositories that claim them, detects conflicts before they happen, and survives reboots, service restarts, and machine onboarding.

This is distinct from the existing `port-map` skill, which is a point-in-time scanner that tells you what is listening *right now*. Port Authority tells you what *should* be listening, what *is allowed* to listen, and blocks collisions *before* a service starts.

## Problem

HUMMBL runs services across 6+ machines with no central port registry. The current state:

1. **No allocation authority.** When a new service needs a port, the operator or agent picks one that "seems free." There is no reservation system. The `port-map` skill can scan for conflicts *after* a collision, but cannot prevent one.

2. **Port knowledge is scattered and stale.** The `port-map` skill hardcodes an expected-service table (5 entries) that is already wrong: it references "MBP" (nodezero is dormant since 2026-07-13), lists port 3000 as "Dashboard frontend" but Gitea was on 3000 (now 3030), and does not include the bus bridge (18790), the OpenClaw gateway (18789), or any of the ~89 repos that may have their own dev servers.

3. **Cross-machine collisions are invisible.** Anvil runs Gitea on 3030. If Delta or Slate starts a service on 3030, nothing catches it until a tailnet connection goes to the wrong machine. The `protected-surfaces.md` rule says "do not bind a competing listener" on `:18790` but there is no enforcement layer.

4. **Machine onboarding has no port budget.** When a new machine joins the fleet, there is no documented port range it should use, no check that its defaults don't collide with existing services, and no registry to update.

5. **Agent-spawned services are untracked.** Agents can start dev servers (Next.js on 3000, FastAPI on 8000, etc.) without registering them. If two agents start services on the same port on the same machine, one silently fails.

## Proposal

Build a **Port Authority** with three layers:

### Layer 1: Registry (canonical state)

A single JSON/YAML file — `ports.registry.yaml` — that is the source of truth for every port allocation in the fleet. Each entry:

```yaml
- port: 3030
  machine: anvil
  service: gitea
  bind: 0.0.0.0
  owner: operator
  repo: hummbl-io/gitea-control-plane
  claimed: 2026-04-24
  notes: "Gitea web UI. Was 3000, moved to 3030 to avoid Next.js collision."

- port: 18790
  machine: hummbl-vps
  service: bus-bridge
  bind: 0.0.0.0
  owner: operator
  protected: true
  notes: "Canonical coordination bus. Do not bind competing listener."

- port: 18789
  machine: anvil
  service: openclaw-gateway
  bind: 127.0.0.1
  owner: operator
  notes: "OpenClaw local gateway."
```

Location options (Decision needed — see below).

### Layer 2: Allocator (write path)

A skill or CLI tool — `port-authority` — that:

- **Reserve**: `port-authority reserve --machine anvil --service my-new-app` → picks the next free port in the allowed range, writes it to the registry, returns the port number.
- **Release**: `port-authority release --machine anvil --port 8080` → marks the port as free.
- **Claim**: `port-authority claim --machine anvil --port 9000 --service my-app` → explicitly claims a specific port (fails if already taken).
- **Verify**: `port-authority verify` → cross-checks the registry against live `port-map` output on each machine and reports drift.

### Layer 3: Scanner (read path, extends port-map)

The existing `port-map` skill gains a `--registry` flag that compares live scan output against `ports.registry.yaml` and reports:
- **Unregistered listeners**: a port is listening but not in the registry (possible rogue service).
- **Registered but down**: a port is in the registry but nothing is listening (service died or never started).
- **Conflicts**: two entries in the registry claim the same port on the same machine (registry corruption).
- **Cross-machine collisions**: same port on different machines with different services (not necessarily wrong, but flagged for awareness).

## Decisions

### D1: Registry location

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A: `hummbl-governance/docs/ports.registry.yaml`** | Lives in the governance repo, version-controlled, PR-reviewed | Slow to update (PR per port change); but auditable and protected |
| **B: `apex-nexus/ports.registry.yaml`** | Lives in the nexus repo (already the CI/fleet hub) | Same trade-off as A; apex-nexus is already the fleet metadata home |
| **C: `.agents/state/ports.registry.yaml`** | Lives in agent state, mutable by agents without PR | Fast to update; but no review gate, drift risk, not in git history |
| **D: D1A + D1C hybrid** | Canonical registry in git (A or B), agent-writable cache in `.agents/state/` | Agents can reserve quickly; canonical copy reconciled via PR; best of both but most complex |

**Recommendation**: D1B (apex-nexus) — it is already the fleet metadata hub (agents, skills, rules mirrors), has CI gates, and port allocations are fleet-level concerns, not governance-policy concerns.

### D2: Allocation strategy

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A: Fixed ranges per machine** | Anvil: 3000-3999, Delta: 4000-4999, etc. | Simple, no cross-machine collision possible; but wastes ports and doesn't scale if one machine runs many services |
| **B: Global free-list** | Authority picks the lowest free port across the fleet | Efficient; but cross-machine awareness needed, and port numbers become non-deterministic |
| **C: Convention + override** | Default conventions (3000=web, 8000=api, 11434=ollama) with explicit override for anything else | Matches existing mental models; but conventions are implicit and can collide |
| **D: D2C + D2A fallback** | Convention first, then machine-range fallback for non-conventional services | Pragmatic; but two strategies means two code paths |

**Recommendation**: D2C — convention-first with explicit claim for anything outside convention. This matches how the fleet already works (everyone knows 11434 is Ollama, 18790 is the bus) and avoids over-engineering a free-list allocator for a 6-machine fleet.

### D3: Enforcement level

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A: Advisory only** | Registry is a reference; nothing blocks a service from binding | No runtime cost; but collisions still happen, just detected after |
| **B: Pre-start check** | Agents call `port-authority check` before starting a service; fails if port is taken | Catches most collisions; but relies on agent discipline, not enforced by OS |
| **C: OS-level enforcement** | Firewall rules or port reservation that actually blocks unregistered binds | Real enforcement; but high operational complexity, breaks ad-hoc dev work |
| **D: D3B + drift alert** | Pre-start check for agents + periodic drift scan that posts a bus ALERT on unregistered listeners | Catches collisions before start AND rogues after start; moderate complexity |

**Recommendation**: D3D — pre-start check (agent discipline) + drift scan (bus alert). This is the HUMMBL pattern: convention + observability, not hard enforcement.

### D4: Scope — what counts as a "port"

| Option | Description |
|--------|-------------|
| **A: TCP only** | Listening TCP ports (the common case) |
| **B: TCP + UDP** | Include UDP services (DNS, mDNS, Tailscale) |
| **C: TCP + UDP + Unix sockets** | Include Unix socket paths (bus bridge, Docker sockets) |
| **D: TCP + UDP + named endpoints** | TCP/UDP + logical endpoints like Tailscale URLs, Cloudflare tunnel routes |

**Recommendation**: D4A for v1 — TCP only. The vast majority of HUMMBL services are TCP. Expand later if needed.

## Pre-existing infra check

Checked 2026-08-19:

- **`~/.agents/skills/port-map/SKILL.md`** — EXISTS. Point-in-time port scanner with hardcoded expected-service table (5 entries, partially stale). This IDEA PACK extends, not replaces, this skill.
- **`~/.agents/skills/process-check/SKILL.md`** — EXISTS. Process/port/resource audit. Complementary; Port Authority would call process-check for drift investigation.
- **`~/.agents/rules/protected-surfaces.md`** lines 86-87 — EXISTS. Documents `:18790` as a protected bus bridge endpoint with "do not bind competing listener" rule. This is the only existing port-protection rule; Port Authority would generalize it.
- **`~/.agents/rules/openclaw.md`** line 65 — EXISTS. Notes port 8080 on nodezero occupied by Docker, port 8081 for signal-cli. Scattered port knowledge.
- **`~/.agents/rules/no-ollama.md`** line 9 — EXISTS. Notes port 11434 for Ollama on nodezero.
- **`~/.agents/rules/mbp-ollama-policy.md`** line 28 — EXISTS. Notes port 11434 for Ollama on nodezero (duplicate of above).
- **`hummbl-governance/hummbl_governance/`** — No port registry module found. No `port_authority.py`, no `port_registry.py`, no port allocation service.
- **`hummbl-governance/docs/`** — No port registry doc found. No `ports.yaml`, no `ports.json`, no `port-registry.md`.
- **`apex-nexus/`** — No port registry found.
- **`~/.agents/skills/`** — No `port-authority` skill found. `port-map` is the closest, but is a scanner, not a registry.

**Conclusion**: No persistent port registry exists anywhere in the fleet. Port knowledge is scattered across 4+ rule files and 1 skill, all stale or partial. The `port-map` skill is the right integration point for the scanner layer but does not own allocation.

## Non-goals

- **Not a service mesh.** Port Authority does not route traffic, do load balancing, or manage service discovery. It only owns the port-number-to-service mapping.
- **Not a firewall.** It does not block ports at the OS level (D3C is explicitly deferred).
- **Not a monitoring system.** It does not alert on service health, only on port-registry drift.
- **Not a replacement for `port-map`.** The scanner layer extends `port-map`; it does not replace it.

## Adoption criteria

This IDEA PACK is **ADOPTED** if the operator and fleet agree that:
1. A persistent port registry is worth maintaining (vs. the current ad-hoc approach).
2. The registry should live in `apex-nexus` (D1B).
3. Convention-first allocation (D2C) is the right strategy for a 6-machine fleet.
4. Advisory + drift-alert enforcement (D3D) is sufficient.

This IDEA PACK is **DROPPED** if:
- The operator determines the fleet is small enough that `port-map` + `protected-surfaces.md` is sufficient.
- The operator prefers to wait until a real collision causes an incident before building infrastructure.

## Falsification tests

- **F1**: If the `port-map` skill's expected-service table is already correct and complete for all 6 machines, the registry is redundant. → Test: run `port-map --expected` on all machines and check if any unregistered or stale entries exist. (Pre-existing infra check already shows the table is stale — F1 fails, registry is needed.)
- **F2**: If no port collision has ever occurred in the fleet, the authority is premature. → Test: search bus history for "port" + "conflict" or "address already in use". (Operator can verify.)
- **F3**: If the registry would have zero entries beyond what `port-map` already knows, it adds no value. → Test: enumerate all services in `protected-surfaces.md`, `openclaw.md`, `no-ollama.md`, `mbp-ollama-policy.md`, and the bus bridge config. If the count is ≤5, the `port-map` table can hold them. If >5, a registry is justified. (Pre-existing infra check found 7+ scattered port references — F3 fails, registry is justified.)

## Verdicts

(Not yet opened — review window starts when bus PROPOSAL is posted.)

---

## References

- `~/.agents/skills/port-map/SKILL.md` — existing point-in-time scanner
- `~/.agents/skills/process-check/SKILL.md` — process/port audit
- `~/.agents/rules/protected-surfaces.md` §86-87 — bus bridge port protection
- `~/.agents/rules/openclaw.md` §65 — nodezero port 8080/8081
- `~/.agents/rules/no-ollama.md` §9 — Ollama port 11434
- `~/.agents/rules/mbp-ollama-policy.md` §28 — Ollama port 11434 (duplicate)
