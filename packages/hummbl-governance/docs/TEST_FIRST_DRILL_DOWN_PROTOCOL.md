# Test-First Drill-Down Protocol

**Status:** PROPOSED — requires human approval before adding to AGENTS or agent guardrails
**Origin:** hummbl-io/hummbl-governance#80
**Steward:** HUMMBL Research Institute

---

## 1. Purpose

The governance architecture needs a safe way to inspect hidden dependencies, stale state, underground infrastructure, and sensitive-adjacent surfaces without allowing agents to dig blindly. This protocol defines the lifecycle from hypothesis to promotion, with explicit gates, receipts, and stop lines.

**Core principle:** Do not dig without looking. Test first, then drill down.

---

## 2. Lifecycle

```
D0: Hypothesis
  → D1: Surface Survey
    → D2: Remote Sensing
      → D3: Test Pit
        → D4: Core Sample
          → D5: Sandbox Simulation
            → D6: Excavation Permit
              → D7: Pilot Tunnel
                → D8: Instrumented Tunnel
                  → D9: Promotion
```

| Stage | Name | What Happens | Write Access | Receipt Required |
|-------|------|-------------|--------------|-----------------|
| D0 | Hypothesis | Formulate what might be below the surface | None | No |
| D1 | Surface Survey | Read visible state, docs, and manifests | Read-only | No |
| D2 | Remote Sensing | Non-invasive probes (grep, search, API queries) | Read-only | Yes |
| D3 | Test Pit | Small, isolated test in sandbox | Sandbox only | Yes |
| D4 | Core Sample | Extract a representative sample | Sandbox only | Yes |
| D5 | Sandbox Simulation | Simulate the full operation in sandbox | Sandbox only | Yes |
| D6 | Excavation Permit | Operator grants permission to drill | None (permit stage) | Yes |
| D7 | Pilot Tunnel | First real-world execution with instrumentation | Production (scoped) | Yes |
| D8 | Instrumented Tunnel | Ongoing production execution with monitoring | Production (scoped) | Yes |
| D9 | Promotion | Tunnel becomes a registered, permanent path | Production | Yes |

---

## 3. Primitives

### Probe

A **Probe** is a non-invasive inspection of a surface or subsurface layer.

```yaml
probe_id: "probe-001"
probe_type: "repo"  # repo, bus, dataset, simulation-world
target: "hummbl-governance/services/"
hypothesis: "Check for deprecated imports"
stage: "D2"
access: "read-only"
receipt_required: true
result: ""
```

### Core Sample

A **Core Sample** is a representative extraction from a layer for analysis.

```yaml
sample_id: "sample-001"
probe_id: "probe-001"
target: "hummbl-governance/services/kill_switch_core.py"
sample_type: "code-snippet"
stage: "D4"
access: "sandbox"
receipt_required: true
```

### Excavation Permit

An **Excavation Permit** is operator authorization to drill into a production layer.

```yaml
permit_id: "permit-001"
requested_by: "devin"
target_layer: "production-bus"
justification: "Need to inspect bus message ordering for IssueOps #978"
stage: "D6"
scope: "read-only bus messages for 1 hour"
expires: "2026-06-23T14:00:00Z"
approved_by: "operator"
receipt_required: true
conditions:
  - "no writes to bus"
  - "no agent identity changes"
  - "results reported within 24h"
```

### Stop Line

A **Stop Line** is a hard boundary that halts drilling.

```yaml
stop_line_id: "stop-001"
trigger: "credentials detected"
action: "halt"
escalation: "operator"
```

### Backfill

A **Backfill** is the restoration of a layer after drilling.

```yaml
backfill_id: "backfill-001"
permit_id: "permit-001"
action: "restore original state"
verified_by: "krineia"
```

### Cave-In

A **Cave-In** is an unexpected failure during drilling that requires emergency response.

```yaml
cave_in_id: "cavein-001"
permit_id: "permit-001"
trigger: "production bus corruption"
response: "kill-switch HALT_ALL"
recovery: "restore from backup"
```

---

## 4. Hard Boundaries

The following are **sealed** — no drilling is permitted under any circumstances:

- **Credentials and secrets** — API keys, tokens, passwords, GPG keys
- **Production user data** — personal data, emails, messages
- **Non-authorized repos** — repos outside the authorized fleet
- **Sealed archives** — historical data marked as sealed
- **Operator-only settings** — GitHub repo settings, branch protection

A **Stop Line** is automatically triggered if any of these are encountered during drilling.

---

## 5. Default Behavior

Before an excavation permit is granted:

- **All access is read-only** — no writes, no modifications, no side effects
- **All probes require receipts** — even read-only probes must be logged
- **Sandbox simulation precedes production drilling** — D5 must pass before D6

---

## 6. Probe Templates

### GitHub Repo Probe

```yaml
probe_id: "probe-repo-001"
probe_type: "repo"
target: "hummbl-io/hummbl-governance"
hypothesis: "Check for circular imports in services/"
stage: "D2"
access: "read-only"
methods:
  - "grep for import patterns"
  - "read __init__.py files"
  - "check dependency graph"
receipt_required: true
```

### Bus Probe

```yaml
probe_id: "probe-bus-001"
probe_type: "bus"
target: "_state/coordination/messages.tsv"
hypothesis: "Check for message ordering anomalies"
stage: "D2"
access: "read-only"
methods:
  - "tail last 100 messages"
  - "check timestamp ordering"
  - "verify sender identities"
receipt_required: true
```

### Dataset Probe

```yaml
probe_id: "probe-data-001"
probe_type: "dataset"
target: "_state/cognition/ledger.jsonl"
hypothesis: "Check for ledger corruption"
stage: "D2"
access: "read-only"
methods:
  - "validate JSON on each line"
  - "check hash chain integrity"
  - "verify schema conformance"
receipt_required: true
```

### Simulation World Probe

```yaml
probe_id: "probe-sim-001"
probe_type: "simulation-world"
target: "minecraft-server-001"
hypothesis: "Check agent governance emergence patterns"
stage: "D2"
access: "read-only"
methods:
  - "observe agent interactions"
  - "log governance events"
  - "no world modifications"
receipt_required: true
```

---

## 7. Excavation Permit Template

```yaml
permit_id: "permit-001"
requested_by: "devin"
target_layer: "production-bus"
justification: "Description of why drilling is needed"
stage: "D6"
scope: "read-only | write-scoped | write-full"
expires: "ISO 8601 timestamp"
approved_by: "operator"
receipt_required: true
conditions:
  - "condition 1"
  - "condition 2"
rollback_plan: "How to restore if something goes wrong"
stop_lines:
  - trigger: "credentials detected"
    action: "halt"
  - trigger: "production error"
    action: "halt"
```

---

## 8. Receipt Requirements

Every probe, core sample, excavation permit, pilot tunnel, and promotion requires a receipt. The receipt must capture:

- `action_id` — the probe or permit ID
- `stage` — the lifecycle stage (D0-D9)
- `actor` — agent or human identity
- `target` — what was probed or drilled
- `result` — success, failure, or cave-in
- `timestamp` — when the action occurred
- `evidence_ref` — link to logs, samples, or artifacts

---

## 9. Cross-References

- **Memory Civilization registries:** hummbl-governance#79
- **IssueOps controller:** hummbl-governance#978
- **Review surface:** hummbl-governance#981
- **Right-of-way doctrine:** `hummbl-governance/docs/architecture/memory-city/doctrine/right-of-way.md`

---

**Last updated:** 2026-06-23
**Prepared by:** Devin
**Approval required:** Human approval before adding to AGENTS or agent guardrails
