# Simulation Affordance Template

**Status:** PROPOSED — requires human review before making mandatory
**Origin:** hummbl-io/hummbl-governance#83
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

Every governance primitive should eventually be representable, stress-tested, measured, and played inside simulated worlds. This template provides a standard `Simulation Affordance` section for new governance doctrines, schemas, ADRs, and repo templates.

Without a standard simulation mapping, new governance work may remain abstract and fail to prepare for Minecraft, multi-game, and Unreal implementation paths.

---

## 2. Template

Copy this section into any governance doctrine, schema, or ADR:

```markdown
## Simulation Affordance

### Minecraft Object
- **Block/Entity:** <what represents this primitive in Minecraft>
- **Behavior:** <how the primitive manifests in-game>

### Unreal Object
- **Actor/Component:** <what represents this primitive in Unreal Engine>
- **Behavior:** <how the primitive manifests in-engine>

### Agent Role
- **Who acts:** <which agent or player interacts with this primitive>
- **Action model:** <what actions are available>

### World Action
- **Trigger:** <what triggers the primitive in the world>
- **Effect:** <what happens when the primitive fires>

### Receipt
- **Receipt type:** <what receipt is generated>
- **Storage:** <where the receipt is stored in the simulation>

### Failure Mode
- **Failure condition:** <what can go wrong>
- **Mitigation:** <how to recover>

### Metric
- **What to measure:** <the key metric for this primitive>
- **Baseline:** <the comparison baseline>

### Prior-Art Comparison
- **Prior art:** <named prior work that addresses this>
- **Overlap:** <full, partial, none>
- **Transfer limits:** <where this doesn't transfer>

### Promotion Status
- **Current status:** <play-generated candidate | promoted canon>
- **Review required:** <who reviews before promotion>
```

---

## 3. Sample Mappings

### 3.1 Bus / Right-of-Way

| Field | Value |
|-------|-------|
| Minecraft Object | Redstone bus line — signals travel along defined paths |
| Unreal Object | Actor channel — message passing between actors |
| Agent Role | Any agent on the bus |
| World Action | Agent posts a message → signal travels to recipients |
| Receipt | Bus message receipt (timestamp, sender, type) |
| Failure Mode | Signal collision or bus congestion |
| Metric | Message latency, throughput |
| Baseline | No-bus baseline (direct agent-to-agent) |
| Prior Art | Multi-agent communication protocols (FIPA ACL) |
| Overlap | Partial — FIPA covers message format, not right-of-way |
| Transfer Limits | Minecraft redstone is binary; real buses have typed messages |
| Promotion Status | Play-generated candidate |

### 3.2 Tunnel (Memory Civilization)

| Field | Value |
|-------|-------|
| Minecraft Object | Nether portal — connects two dimensions with gates |
| Unreal Object | Level streaming volume — loads/unloads sub-levels |
| Agent Role | Tunnel owner (trusted agent) |
| World Action | Agent enters portal → gate check → transport to target layer |
| Receipt | Tunnel traversal receipt (gate checks, timestamp) |
| Failure Mode | Gate failure → portal closes (cave-in) |
| Metric | Traversal success rate, gate check latency |
| Baseline | Surface-only travel (no tunnels) |
| Prior Art | Multi-agent spatial navigation (AI2-THOR, Habitat) |
| Overlap | Partial — spatial navigation exists, but not gated tunnels |
| Transfer Limits | Minecraft portals are binary; real tunnels have multiple gates |
| Promotion Status | Play-generated candidate |

### 3.3 Krineia Receipt

| Field | Value |
|-------|-------|
| Minecraft Object | Written book — immutable record placed in a chest |
| Unreal Object | Save game object — persistent, hash-verified state |
| Agent Role | Krineia watcher agent |
| World Action | Agent performs action → receipt generated → placed in archive chest |
| Receipt | Cryptographic receipt (hash chain, timestamp) |
| Failure Mode | Chain corruption → cave-in → rollback |
| Metric | Chain integrity, verification latency |
| Baseline | No-receipt baseline (unlogged actions) |
| Prior Art | Blockchain audit logs, append-only ledgers |
| Overlap | Full — append-only chains are well-understood |
| Transfer Limits | Minecraft books have no crypto; real receipts use SHA-256 |
| Promotion Status | Promoted canon (Krineia spec v1.0-rc2) |

---

## 4. Transfer-Limit Guidance

Simulation results must not be overclaimed. When reporting simulation results:

1. **State the transfer limits explicitly** — what works in Minecraft may not work in production
2. **Distinguish play-generated candidates from promoted canon** — simulation results are candidates until reviewed
3. **Reference prior art** — compare against named prior work before claiming novelty
4. **Use the Arbiter novelty rubric** — score claims using `arbiter.novelty_claim.arbitrate_novelty()`
5. **Require receipts** — even simulation actions need receipts for auditability

---

## 5. Play-Generated vs Promoted Canon

| Status | Meaning | Review Required |
|--------|---------|-----------------|
| `play-generated candidate` | Observed in simulation but not reviewed | Human + Arbiter review |
| `promoted canon` | Reviewed and confirmed as a governance pattern | None (already reviewed) |

A play-generated candidate can only be promoted to canon after:
1. Prior-art comparison (Arbiter novelty rubric)
2. Transfer-limit analysis
3. Human review
4. Receipt of the promotion decision

---

## 6. Cross-References

- **Simulation prior-art corpus:** hummbl-governance#1018
- **Arbiter novelty rubric:** arbiter#88
- **Memory Civilization registries:** hummbl-governance#79
- **Test-First Drill-Down protocol:** hummbl-governance#80
- **Product roadmap:** hummbl-production#408

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Review required:** Human review before making mandatory
