# Playbook: Fleet Rollout Protocol

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 15)
**Reader:** agents, operators
**Decision:** how to roll out HUMMBL governance infrastructure across a fleet of machines and agents

**TL;DR:** This playbook is the step-by-step protocol for rolling out HUMMBL governance infrastructure (the `hummbl-governance` library, the `.agents/` rules, the coordination bus, the KRINEIA receipt chain) across a fleet of machines and agents. It covers 4 rollout scenarios (single-machine pilot, multi-machine mesh, agent-by-agent activation, customer organization rollout), the pre-flight checks, the rollout sequence, the verification steps, and the rollback procedure. Every rollout must follow this protocol; deviating from the protocol risks orphan states, broken receipts, or governance gaps.

---

## 1. When to use this playbook

Use this playbook whenever you need to:

- **Pilot HUMMBL governance on a single machine** (the hummbl-governance proving ground pattern)
- **Roll out HUMMBL governance across a multi-machine mesh** (the self-hosted-runner-2 fleet pattern)
- **Activate a new agent** in an existing HUMMBL-governed fleet (the agent onboarding pattern)
- **Roll out HUMMBL governance to a customer organization** (the enterprise deployment pattern)

Do NOT use this playbook for:

- Single-artifact promotions (use the claims change playbook, item 14)
- Single-claim changes (use the claims change playbook, item 14)
- Ad-hoc governance actions (use the doctrine, item 11)

---

## 2. Roles

| Role                 | Who                                                  | Authority                                                      |
| -------------------- | ---------------------------------------------------- | -------------------------------------------------------------- |
| **Rollout lead**     | Steward (Operator or delegated agent)                  | Plans the rollout, runs pre-flight, executes the sequence      |
| **Machine operator** | Human or agent with root/admin on the target machine | Installs the library, configures the bus, enables the receipts |
| **Agent steward**    | Steward (Operator or delegated agent)                  | Onboards agents, assigns guardrails, registers bus identities  |
| **Verifier**         | Auditor agent or human                               | Runs verification commands, confirms rollout success           |
| **Promoter**         | Principal Agent (Operator)                             | Approves the rollout for live (production)                     |

---

## 3. The 4 rollout scenarios

### 3.1 Single-machine pilot (hummbl-governance pattern)

**When:** First HUMMBL governance deployment on a machine. The hummbl-governance proving ground.

**Pre-flight:**

1. Confirm Python 3.11+ is installed
2. Confirm git is installed and authenticated
3. Confirm the machine has a stable hostname (not a DHCP rotating name)
4. Confirm the machine has a `_state/coordination/` directory (or will create one)
5. Confirm the machine has a `_receipts/krineia/` directory (or will create one)

**Rollout sequence:**

1. `pip install hummbl-governance` — install the library
2. Clone the `hummbl-governance` repo (or the customer's repo) to the machine
3. Run `python -m hummbl_governance.services.health` — confirm the health endpoint works
4. Initialize the coordination bus: `python -m hummbl_governance.bus.bus_writer <agent> all STATUS "fleet rollout: machine initialized"`
5. Initialize the KRINEIA receipt chain (if this is a new fleet) or copy the existing chain (if joining a fleet)
6. Configure the agent guardrails in `.agents/rules/<agent>-guardrails.md`
7. Register the agent identity in `.agents/rules/agent-roster.md`
8. Run the verification commands (see §6)
9. Emit a KRINEIA receipt: `governance.fleet_rollout.machine_initialized`
10. Post a bus STATUS: "fleet rollout: machine <hostname> live"

**Verification:**

- `python -m hummbl_governance.services.health` returns 8 probes green
- `cat _state/coordination/messages.tsv | tail -1` shows the initialization STATUS
- `python -c "import hummbl_governance; print(hummbl_governance.__version__)"` returns the version
- The KRINEIA receipt chain is intact (run the chain verification from the evidence pack E1)

### 3.2 Multi-machine mesh (self-hosted-runner-2 fleet pattern)

**When:** Rolling out HUMMBL governance across multiple machines (e.g., self-hosted-runner-2, self-hosted-runner-1, self-hosted-runner-3, self-hosted-runner-4).

**Pre-flight:**

1. Complete §3.1 on the first machine (the source of truth, e.g., self-hosted-runner-2)
2. Confirm Tailscale (or equivalent) is running on all machines
3. Confirm SSH (or equivalent) works between machines
4. Confirm the source machine has the canonical `.agents/` directory
5. Confirm the target machines have Python 3.11+ and git

**Rollout sequence:**

1. On the source machine: `bash ~/.agents/scripts/mesh-sync.sh --check` — confirm source is canonical
2. On each target machine: complete §3.1 steps 1-5 (install library, clone repo, init bus, init receipts)
3. From the source machine: `bash ~/.agents/scripts/mesh-sync.sh <target>` — sync `.agents/` to the target
4. On each target machine: configure the agent guardrails (machine-specific)
5. On each target machine: register the agent identity (machine-specific)
6. On each target machine: run the verification commands (see §6)
7. From the source machine: `bash ~/.agents/scripts/mesh-sync.sh --status` — confirm all targets are synced
8. Emit a KRINEIA receipt per target: `governance.fleet_rollout.machine_synced`
9. Post a bus STATUS per target: "fleet rollout: machine <hostname> synced"
10. Post a fleet-wide bus STATUS: "fleet rollout: mesh complete, N machines live"

**Verification:**

- `bash ~/.agents/scripts/mesh-sync.sh --status` shows all targets synced
- Each target machine's health endpoint returns green
- The coordination bus has entries from all target machines
- The KRINEIA receipt chain has a receipt per target machine

### 3.3 Agent activation (agent onboarding pattern)

**When:** Activating a new agent (e.g., a new Claude Code session, a new Codex instance, a new Devin session) in an existing HUMMBL-governed fleet.

**Pre-flight:**

1. Confirm the agent has a guardrail file in `.agents/rules/<agent>-guardrails.md`
2. Confirm the agent's identity is in `.agents/rules/agent-roster.md`
3. Confirm the agent's model tier is in `.agents/rules/model-tier-policy.md`
4. Confirm the agent has a bus identity (the bare canonical name)
5. Confirm the agent has read the doctrine (item 11) and the charter (item 12)

**Rollout sequence:**

1. The agent reads AGENTS.md (machine-global) and the repo-level AGENTS.md
2. The agent reads its guardrail file
3. The agent reads the doctrine and the charter
4. The agent posts a bus STATUS: "agent activation: <agent> online on <hostname>"
5. The agent emits a KRINEIA receipt: `governance.agent_activated`
6. The agent runs a smoke test (e.g., reads the claims manifest, verifies the receipt chain)
7. The agent posts a bus STATUS: "agent activation: <agent> verified, ready for work"

**Verification:**

- The agent's guardrail file exists and is readable
- The agent's identity is in the roster
- The agent has posted a bus STATUS
- The agent has emitted a KRINEIA receipt
- The agent can read the claims manifest and the receipt chain

### 3.4 Customer organization rollout (enterprise deployment pattern)

**When:** Rolling out HUMMBL governance to a customer organization.

**Pre-flight:**

1. Confirm the customer has Python 3.11+ on the target machines
2. Confirm the customer has git and a code repository
3. Confirm the customer has identified a steward (the customer's equivalent of Operator)
4. Confirm the customer has identified the agents to govern
5. Confirm the customer has read the evidence pack (item 13) and accepts the boundaries (item 13 §4)

**Rollout sequence:**

1. The customer installs `hummbl-governance` via `pip install hummbl-governance`
2. The customer creates a `_state/coordination/` directory for the coordination bus
3. The customer creates a `_receipts/krineia/` directory for the receipt chain
4. The customer initializes the receipt chain (first receipt: `governance.fleet_rollout.customer_initialized`)
5. The customer configures the agent guardrails (per the customer's agents)
6. The customer registers the agent identities (per the customer's roster)
7. The customer runs the verification commands (see §6)
8. The customer emits a KRINEIA receipt: `governance.fleet_rollout.customer_live`
9. The customer posts a bus STATUS: "fleet rollout: customer <name> live"
10. HUMMBL support reviews the rollout and confirms (or flags issues)

**Verification:**

- The customer's `pip install hummbl-governance` succeeded
- The customer's coordination bus has the initialization STATUS
- The customer's KRINEIA receipt chain has the initialization receipt
- The customer's agents have guardrails and roster entries
- The customer's health endpoint returns green

---

## 4. Pre-flight checklist (all scenarios)

Before starting any rollout, confirm:

- [ ] Python 3.11+ installed on all target machines
- [ ] git installed and authenticated on all target machines
- [ ] `pip install hummbl-governance` works on all target machines
- [ ] Stable hostnames on all target machines
- [ ] Tailscale (or equivalent) running on all target machines (for mesh scenarios)
- [ ] SSH (or equivalent) works between machines (for mesh scenarios)
- [ ] The source machine has the canonical `.agents/` directory (for mesh scenarios)
- [ ] The steward has read the doctrine (item 11) and charter (item 12)
- [ ] The agents have guardrail files and roster entries
- [ ] The customer has read the evidence pack (item 13) and accepts the boundaries (for customer scenarios)

---

## 5. Rollout sequence (all scenarios)

The generic sequence, applicable to all 4 scenarios:

1. **Install** — `pip install hummbl-governance`
2. **Initialize** — create `_state/coordination/` and `_receipts/krineia/`
3. **Configure** — agent guardrails, roster, model tiers
4. **Verify** — run the verification commands (§6)
5. **Receipt** — emit a KRINEIA receipt for the rollout event
6. **Status** — post a bus STATUS announcing the rollout
7. **Monitor** — watch the bus and the receipt chain for 24 hours for anomalies

---

## 6. Verification commands

After any rollout, run these verification commands:

### V1: Library installed

```bash
python -c "import hummbl_governance; print(hummbl_governance.__version__)"
```

Should print the version number without error.

### V2: Health endpoint

```bash
python -m hummbl_governance.services.health
```

Should return 8 probes green (or the customer's equivalent).

### V3: Coordination bus

```bash
tail -5 _state/coordination/messages.tsv
```

Should show the initialization STATUS and any subsequent messages.

### V4: KRINEIA receipt chain

```bash
python3 -c "
import json, hashlib
lines = open('_receipts/krineia/primary.jsonl', encoding='utf-8').read().strip().split('\n')
print(f'Receipts: {len(lines)}')
prev = None
for i, line in enumerate(lines):
    r = json.loads(line)
    if prev and r['prev_hash'] != prev:
        print(f'CHAIN BROKEN at receipt {i}!')
        break
    computed = hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='hash'}, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    if computed != r['hash']:
        print(f'HASH MISMATCH at receipt {i}!')
        break
    prev = r['hash']
else:
    print('Chain verified: all hashes match, all prev_hash links correct')
"
```

Should print "Chain verified" with no errors.

### V5: Claims manifest (if applicable)

```bash
python3 -c "
import json
d = json.loads(open('web/manifest/claims-provenance.json', encoding='utf-8').read())
print(f'Total claims: {d[\"summary\"][\"total_claims\"]}')
print(f'Validated: {d[\"summary\"][\"validated\"]}')
print(f'Unproven: {d[\"summary\"][\"unproven\"]}')
"
```

Should print the summary counts without error.

### V6: Mesh sync status (for mesh scenarios)

```bash
bash ~/.agents/scripts/mesh-sync.sh --status
```

Should show all targets synced.

---

## 7. Rollback procedure

If a rollout fails or causes issues, rollback:

1. **Stop the agents** — deactivate any agents that were activated in the rollout
2. **Revert the configuration** — restore the previous `.agents/` directory from backup
3. **Disable the bus** — stop writing to the coordination bus (but do not delete historical entries)
4. **Disable the receipts** — stop emitting KRINEIA receipts (but do not delete the chain)
5. **Uninstall the library** — `pip uninstall hummbl-governance` (optional; the library is non-destructive)
6. **Post a bus STATUS** — "fleet rollout: rollback on <hostname>, reason: <reason>"
7. **Emit a KRINEIA receipt** — `governance.fleet_rollout.rollback`
8. **Investigate** — identify the root cause (use the root-cause skill)
9. **Fix** — address the root cause
10. **Re-attempt** — restart the rollout from the pre-flight check

**Important:** Do NOT delete the coordination bus or the KRINEIA receipt chain during rollback. They are append-only audit trails. Rollback adds entries; it does not remove them.

---

## 8. Common mistakes (and how to avoid them)

### M1: Skipping pre-flight

**Mistake:** Starting the rollout without confirming Python 3.11+, git, or Tailscale.

**Fix:** Always run the pre-flight checklist (§4). A failed pre-flight is cheaper than a failed rollout.

### M2: Not initializing the receipt chain

**Mistake:** Installing the library and configuring agents, but not creating the KRINEIA receipt chain. Subsequent governance actions cannot emit receipts.

**Fix:** Always initialize the receipt chain as step 2 of the rollout sequence. The first receipt should be `governance.fleet_rollout.machine_initialized` or equivalent.

### M3: Deleting the bus or chain during rollback

**Mistake:** Rolling back by deleting the coordination bus or the KRINEIA receipt chain.

**Fix:** Never delete. Rollback adds entries (a rollback STATUS and receipt); it does not remove them. The audit trail must be preserved.

### M4: Activating an agent without a guardrail

**Mistake:** Activating an agent without a guardrail file or roster entry. The agent has no defined permissions or limitations.

**Fix:** Always create the guardrail file and roster entry before activating the agent (per §3.3 pre-flight).

### M5: Not verifying after rollout

**Mistake:** Completing the rollout steps but not running the verification commands. Issues go undetected.

**Fix:** Always run V1-V6 (or the applicable subset) after the rollout. A rollout is not complete until verification passes.

### M6: Customer rollout without boundary acceptance

**Mistake:** Rolling out HUMMBL governance to a customer who has not read the evidence pack or accepted the boundaries (item 13 §4). The customer later expects HUMMBL to be a Notified Body or to issue certifications.

**Fix:** Always confirm the customer has read the evidence pack and accepts the boundaries before starting the rollout. Document the acceptance in the rollout receipt.

---

## 9. Boundary disclaimer

This playbook is HUMMBL's internal protocol for fleet rollouts. It is not a regulation or a standard. Other organizations may adopt different rollout protocols. HUMMBL's protocol is designed to ensure that rollouts are verifiable, auditable, and reversible.

The playbook does not guarantee a successful rollout. It guarantees that the rollout is documented (bus + receipts), verifiable (V1-V6), and reversible (rollback procedure). A rollout that follows the protocol but fails verification should be rolled back per §7.

---

## 10. How to verify this playbook

A reader can re-verify the playbook's claims by:

1. **The library is installable** — `pip install hummbl-governance` works
2. **The mesh-sync script exists** — `ls ~/.agents/scripts/mesh-sync.sh`
3. **The health endpoint exists** — `python -m hummbl_governance.services.health --help`
4. **The bus writer exists** — `python -m hummbl_governance.bus.bus_writer --help`
5. **The KRINEIA chain is verifiable** — run V4
6. **The claims manifest is valid** — run V5
7. **The doctrine and charter exist** — `ls docs/artifacts/DOCTRINE_ai_governance.md docs/artifacts/CHARTER_hri.md`

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

---

## References

- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (10 principles)
- Charter: `docs/artifacts/CHARTER_hri.md` (HRI authority)
- Evidence pack: `docs/artifacts/EVIDENCE_PACK_fleet_rollout.md` (credibility pack)
- Claims change playbook: `docs/artifacts/PLAYBOOK_claims_change.md` (item 14)
- Wave 1 retrospective: `docs/artifacts/RETROSPECTIVE_wave_1.md`
- Wave 2 retrospective: `docs/artifacts/RETROSPECTIVE_wave_2.md`
- hummbl-governance: https://github.com/hummbl-io/hummbl-governance (Apache 2.0)
- mesh-sync skill: `~/.claude/skills/mesh-sync/SKILL.md`
- hummbl-governance: https://github.com/hummbl-io/hummbl-governance
- CONSTITUTION: `CONSTITUTION.md` (§3.6 receipt integrity, §6 receipt-triggering changes)
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`
- Coordination bus: `_state/coordination/messages.tsv`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This playbook was drafted by Devin at the direction of the Principal Agent, based on the hummbl-governance rollout pattern, the mesh-sync skill, and the wave 1 + wave 2 retrospective findings, and was promoted to live (public) by Principal Agent decision on 2026-06-23. This playbook is the canonical protocol for fleet rollouts; deviations risk orphan states, broken receipts, or governance gaps. This document is **public** — it is intended for external readers (agents, operators, customers, assessors) and may be published on hummbl.io.
