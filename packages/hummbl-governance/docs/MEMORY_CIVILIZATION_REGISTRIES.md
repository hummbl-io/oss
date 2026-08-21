# Memory Civilization Registries

**Status:** PROPOSED — requires human approval before canonization
**Origin:** hummbl-io/hummbl-governance#79
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

As Memory City scales toward Memory Civilization, the system needs canonical registries for bus districts, ground strata, underground maps, and tunnel registries. Without explicit registries, scaling from one hummbl-governance bus to many domain/district surfaces risks creating hidden authority paths, unregistered tunnels, and unclear ownership of cross-layer state.

---

## 2. Registry Family

Four registries govern the Memory Civilization subsurface:

| Registry | Scope | Purpose |
|----------|-------|---------|
| `BUS_REGISTRY` | Surface | Registers all coordination buses and their districts |
| `GROUND_REGISTRY` | Surface | Registers ground strata (visible state layers) |
| `UNDERGROUND_MAP` | Subsurface | Maps the topology of tunnels, vaults, and mines |
| `TUNNEL_REGISTRY` | Subsurface | Registers each tunnel with owner, gates, and rollback |

---

## 3. BUS_REGISTRY Schema

```yaml
bus_id: "bus-001"
bus_name: "hummbl-governance-coordination"
owner: "HUMMBL Research Institute"
authority: "operator-only"
transport: "tsv"  # tsv, jsonl, grpc, http
location: "_state/coordination/messages.tsv"
districts:
  - district_id: "district-001"
    name: "core-ops"
    bus_path: "_state/coordination/messages.tsv"
    owner: "claude-code"
    authority: "steward"
allowed_payloads:
  - "PROPOSAL"
  - "ACK"
  - "STATUS"
  - "SITREP"
  - "BLOCKED"
  - "DECISION"
  - "QUESTION"
  - "MILESTONE"
forbidden_payloads:
  - "SECRET"
  - "CREDENTIAL"
  - "PERSONAL_DATA"
receipt_rules:
  required: true
  storage: "_receipts/bus/"
closure_conditions:
  - "all agents acknowledged shutdown"
  - "no pending PROPOSAL or BLOCKED"
rollback_conditions:
  - "bus corruption detected"
  - "operator override"
```

---

## 4. GROUND_REGISTRY Schema

```yaml
stratum_id: "ground-001"
stratum_name: "briefing-state"
owner: "HUMMBL Research Institute"
authority: "steward"
layer_type: "visible"  # visible, state, archive
location: "state/briefings/"
contents:
  - "daily briefing outputs"
  - "historical briefings"
access_policy:
  read: "active"
  write: "steward"
  delete: "operator-only"
receipt_rules:
  required: false
  storage: "_receipts/ground/"
closure_conditions:
  - "stratum superseded by new layer"
rollback_conditions:
  - "data corruption detected"
```

---

## 5. UNDERGROUND_MAP Schema

```yaml
map_id: "map-001"
map_name: "hummbl-governance-subsurface"
owner: "HUMMBL Research Institute"
authority: "operator-only"
topology:
  tunnels:
    - tunnel_id: "tunnel-001"
      name: "issueops-dispatch"
      from_layer: "surface"
      to_layer: "cognition"
      owner: "devin"
      gates: ["auth-check", "write-boundary", "receipt"]
  vaults:
    - vault_id: "vault-001"
      name: "credentials-vault"
      owner: "operator"
      access: "operator-only"
      sealed: true
  mines:
    - mine_id: "mine-001"
      name: "research-corpus-mine"
      owner: "gemini"
      active: true
  sewers:
    - sewer_id: "sewer-001"
      name: "deprecated-logs"
      owner: "system"
      active: false
  archives:
    - archive_id: "archive-001"
      name: "historical-bus"
      owner: "archivist"
      sealed: true
  recovery_paths:
    - recovery_id: "recovery-001"
      name: "kill-switch-recovery"
      owner: "operator"
      trigger: "EMERGENCY"
```

---

## 6. TUNNEL_REGISTRY Schema

```yaml
tunnel_id: "tunnel-001"
tunnel_name: "issueops-dispatch"
owner: "devin"
authority: "trusted"
from_layer: "surface"
to_layer: "cognition"
gates:
  - gate_id: "gate-001"
    name: "auth-check"
    type: "identity"
    required: true
  - gate_id: "gate-002"
    name: "write-boundary"
    type: "scope"
    required: true
  - gate_id: "gate-003"
    name: "receipt"
    type: "audit"
    required: true
inspection:
  frequency: "per-use"
  last_inspected: "2026-06-23T00:00:00Z"
  inspector: "krineia"
allowed_payloads:
  - "dispatch-pod-claim"
  - "dispatch-pod-release"
forbidden_payloads:
  - "raw-credentials"
  - "unencrypted-secrets"
receipt_rules:
  required: true
  storage: "_receipts/tunnels/tunnel-001/"
rollback_conditions:
  - "gate failure detected"
  - "owner revoked"
  - "tunnel compromised"
closure_conditions:
  - "tunnel superseded"
  - "owner retired"
```

---

## 7. Layer Types

The Memory Civilization subsurface distinguishes:

| Layer | Description | Example |
|-------|-------------|---------|
| **Roads** | Surface-level coordination paths | Bus, GitHub issues |
| **Tunnels** | Drilled connections between layers | IssueOps dispatch tunnel |
| **Vaults** | Sealed storage for sensitive data | Credentials vault |
| **Mines** | Active extraction sites | Research corpus mine |
| **Sewers** | Deprecated or waste channels | Old log paths |
| **Archives** | Sealed historical storage | Historical bus messages |
| **Recovery paths** | Emergency routes | Kill switch recovery |

---

## 8. Invariant: No Tunnel Without Gates

**No tunnel exists without gates, owner, inspection, receipt, and rollback.**

Every tunnel in the `TUNNEL_REGISTRY` must declare:
1. **Gates** — at least one gate (auth, scope, or audit)
2. **Owner** — a named agent or operator with authority
3. **Inspection** — frequency and last-inspected timestamp
4. **Receipt** — receipt rules for all traffic through the tunnel
5. **Rollback** — conditions under which the tunnel is closed

A tunnel missing any of these is a **cave-in risk** and must be sealed immediately.

---

## 9. Right-of-Way Alignment

This registry family aligns with the existing right-of-way doctrine (`hummbl-governance/docs/architecture/memory-city/doctrine/right-of-way.md`):

- **Surface traffic** (roads) has default right-of-way
- **Subsurface traffic** (tunnels) requires explicit permit
- **Cross-layer traffic** requires gate validation at both ends
- **Recovery traffic** has priority over all other traffic

---

## 10. Examples

### IssueOps Bus
- Bus: `hummbl-governance-coordination` (BUS_REGISTRY)
- Tunnel: `issueops-dispatch` (TUNNEL_REGISTRY) — surface → cognition
- Ground: `briefing-state` (GROUND_REGISTRY) — visible state layer

### Evidence/Corpus Tunnel
- Tunnel: `research-ingest` — surface → archive
- Owner: `gemini`
- Gates: `source-validation`, `evidence-grade`, `receipt`

### Simulation Tunnel
- Tunnel: `simulation-dispatch` — surface → simulation layer
- Owner: `simulation-agent`
- Gates: `sandbox-boundary`, `isolation-check`, `receipt`

### Recovery Tunnel
- Tunnel: `kill-switch-recovery` — any layer → surface
- Owner: `operator`
- Gates: `emergency-trigger`, `auth-override`
- Trigger: `EMERGENCY` kill switch mode

---

## 11. Cross-References

- **Memory City doctrine:** `hummbl-governance/docs/architecture/memory-city/doctrine/README.md`
- **Right-of-way doctrine:** `hummbl-governance/docs/architecture/memory-city/doctrine/right-of-way.md`
- **Memory System Registry (proposed):** `hummbl-governance/docs/MEMORY_SYSTEM_REGISTRY.md`
- **IssueOps controller:** hummbl-governance#978
- **Review surface:** hummbl-governance#981
- **Test-First Drill-Down protocol:** hummbl-governance#80

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Approval required:** Human approval before canonization
