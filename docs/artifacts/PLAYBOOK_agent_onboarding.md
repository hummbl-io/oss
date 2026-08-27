# Playbook: Agent Onboarding

**Status:** live v1.0 (public)
**Author:** Operator, HUMMBL, LLC (drafted by Devin)
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 23)
**Reader:** agents, operators, Operator
**Purpose:** operationalize the activation of a new agent in the HUMMBL fleet

**TL;DR:** This playbook defines the 6-step protocol for onboarding a new agent (software or human) into the HUMMBL fleet. It covers: (1) identity registration, (2) guardrail definition, (3) bus identity approval, (4) model tier assignment, (5) first-task assignment, and (6) 30-day review. The playbook ensures every agent has a defined identity, scope, authority boundary, and review cadence before it operates. It is the operational counterpart to the doctrine (item 11) and charter (item 12).

---

## 1. When to use this playbook

Use this playbook when:

- A new software agent is added to the fleet (e.g., a new Claude Code session, a new Devin lane, a new Gemini route)
- A new human team member joins HUMMBL
- An existing agent's role, scope, or authority changes
- An agent is being promoted from candidate to active status

Do NOT use this playbook for:

- Routine agent sessions (an agent that is already onboarded)
- Temporary agent invocations (e.g., a one-off subagent dispatch)
- Agent retirements (use the retirement checklist in §8)

---

## 2. Roles

| Role                 | Who                             | Authority                                    |
| -------------------- | ------------------------------- | -------------------------------------------- |
| Principal Agent      | Operator                   | Final authority on all onboarding decisions  |
| Onboarding steward   | Devin (or delegated agent)      | Drafts the onboarding packet, runs the steps |
| Agent roster steward | Nexus (or delegated agent)      | Maintains the agent registry                 |
| Bus steward          | hummbl-governance bus_writer         | Maintains the coordination bus               |
| Reviewer             | Principal Agent + 1 other agent | 30-day review                                |

---

## 3. The 6-step onboarding protocol

### Step 1: Identity registration

**What:** Register the agent in the agent registry with a unique identity.

**Where:** `governance/board/registry.yaml` (for Board Directors) or `.agents/rules/agent-roster.md` (for fleet agents) or `AGENTS.md` §1.3 (for machine-global agents).

**Fields:**

- `name`: The canonical agent identity (e.g., `devin`, `codex`, `claude-code`)
- `role`: The agent's function (e.g., "primary cloud engineering lane")
- `runtime`: Where the agent runs (e.g., "Cognition cloud", "self-hosted-runner-2")
- `bus_id`: The agent's coordination bus identity (must be unique)
- `model_tier`: Data sensitivity tier (T1-BYOK, T2-ZEN, T3-FREE)
- `trust_level`: Operator confidence (TRUSTED, MEDIUM-HIGH, MEDIUM, PROBATIONARY)
- `autonomy_tier`: 0-3 (per AGENTS.md §1.3)

**Verification:** The agent's `name` and `bus_id` must be unique across the registry. No two agents share the same identity.

**Receipt:** Post a bus message: `devin -> all STATUS: Agent <name> registered in roster (role, runtime, bus_id, model_tier, trust_level)`

### Step 2: Guardrail definition

**What:** Define the agent's guardrail — the rules it must follow.

**Where:** `.agents/rules/<agent>-guardrails.md` (for fleet agents) or `governance/board/constitutions/<agent>.yaml` (for Board Directors).

**Fields:**

- Identity: who the agent is
- Bus rules: how the agent posts to the coordination bus
- Permissions: what the agent may do
- Limitations: what the agent may not do
- Escalation: when and how to escalate to the Principal Agent
- Commit cadence: how often the agent commits
- Prohibited actions: actions that are always forbidden

**Verification:** The guardrail must be reviewed and approved by the Principal Agent before the agent operates.

**Receipt:** Post a bus message: `devin -> all STATUS: Guardrail for <name> approved by Principal Agent`

### Step 3: Bus identity approval

**What:** Approve the agent's bus identity so it can post to the coordination bus.

**Where:** `hummbl_governance/services/agent_identity.py` (the identity registry that rejects messages from unapproved identities).

**Process:**

1. Add the agent's `bus_id` to the approved identities list
2. Test that the agent can post a STATUS message
3. Verify the message appears in the bus log

**Verification:** The agent posts a test STATUS message: `<bus_id> -> all STATUS: Onboarding test message from <name>`

**Receipt:** The test message itself is the receipt.

### Step 4: Model tier assignment

**What:** Assign the agent a model tier that determines what data it may process.

**Where:** `.agents/rules/model-tier-policy.md` + `MODEL_TIERS.md`.

**Tiers:**

- `T1-BYOK`: Bring-your-own-key. The agent may process sensitive data (up to the operator's trust level).
- `T2-ZEN`: Zero-egress, no-network. The agent may process sensitive data in a zero-egress environment.
- `T3-FREE`: Free-tier / cloud. The agent may NOT process sensitive data (data may be used for provider training).

**Verification:** The agent's model tier must match the data sensitivity of its assigned tasks. A T3-FREE agent must not be assigned tasks involving sensitive data.

**Receipt:** Post a bus message: `devin -> all STATUS: Model tier for <name> assigned: <tier>`

### Step 5: First-task assignment

**What:** Assign the agent its first task — a bounded, low-risk task that exercises the agent's identity, guardrail, bus identity, and model tier.

**Where:** The task is assigned by the Principal Agent or a delegated steward.

**Criteria:**

- The task is bounded (clear start and end)
- The task is low-risk (failure does not affect production)
- The task exercises the agent's identity (the agent posts to the bus)
- The task exercises the agent's guardrail (the agent follows its rules)
- The task is verifiable (the agent produces a receipt)

**Example first tasks:**

- Draft a research summary on a specific topic
- Run a health check and post the results to the bus
- Review a single artifact and post feedback to the bus

**Verification:** The agent completes the task, posts a STATUS message, and emits a KRINEIA receipt (if applicable).

**Receipt:** The agent's first STATUS message + the task completion receipt.

### Step 6: 30-day review

**What:** Review the agent's performance 30 days after onboarding.

**Where:** The review is conducted by the Principal Agent + 1 other agent.

**Criteria:**

- Did the agent follow its guardrail?
- Did the agent post to the bus correctly?
- Did the agent stay within its model tier?
- Did the agent complete its assigned tasks?
- Did the agent escalate correctly when blocked?
- Are there any guardrail violations?
- Should the agent's trust level be adjusted?

**Outcomes:**

- `CONTINUE`: The agent continues as-is
- `PROMOTE`: The agent's trust level or autonomy tier is increased
- `DEMOTE`: The agent's trust level or autonomy tier is decreased
- `PROBATION`: The agent is placed on probation (requires remediation)
- `RETIRE`: The agent is retired (use the retirement checklist in §8)

**Receipt:** Post a bus message: `devin -> all STATUS: 30-day review for <name>: <outcome>`

---

## 4. Onboarding packet

The onboarding packet is the collection of artifacts produced during onboarding:

| Artifact              | Step   | Location                                                            |
| --------------------- | ------ | ------------------------------------------------------------------- |
| Agent registry entry  | Step 1 | `governance/board/registry.yaml` or `.agents/rules/agent-roster.md` |
| Guardrail document    | Step 2 | `.agents/rules/<agent>-guardrails.md`                               |
| Bus identity approval | Step 3 | `hummbl_governance/services/agent_identity.py`                           |
| Model tier assignment | Step 4 | `.agents/rules/model-tier-policy.md`                                |
| First task assignment | Step 5 | Bus message + task artifact                                         |
| 30-day review         | Step 6 | Bus message + review notes                                          |

The packet must be complete before the agent is considered "active". An agent with a missing packet item is "provisional" — it may operate but its outputs are subject to additional review.

---

## 5. Common mistakes

### M1: Onboarding without a guardrail

**What:** An agent is registered and starts operating without a guardrail document.

**Impact:** The agent has no defined rules. It may take actions outside its scope. The agent's outputs are not accountable.

**Fix:** Stop the agent. Draft the guardrail. Get Principal Agent approval. Resume the agent.

### M2: Bus identity not approved

**What:** An agent tries to post to the bus but its identity is not in the approved list.

**Impact:** The agent's messages are rejected. The agent cannot coordinate with the fleet.

**Fix:** Add the agent's `bus_id` to the approved identities list. Test with a STATUS message.

### M3: Model tier mismatch

**What:** A T3-FREE agent is assigned a task involving sensitive data.

**Impact:** Sensitive data may be exposed to the cloud provider (used for training).

**Fix:** Reassign the task to a T1-BYOK or T2-ZEN agent. Review the T3-FREE agent's task assignments.

### M4: Skipping the 30-day review

**What:** An agent is onboarded but the 30-day review is never conducted.

**Impact:** Guardrail violations go undetected. The agent's trust level is never adjusted.

**Fix:** Schedule the 30-day review at onboarding time. Add it to the Principal Agent's calendar.

### M5: Onboarding a retired identity

**What:** A new agent is given the `bus_id` of a retired agent.

**Impact:** The new agent's messages are confused with the retired agent's history. The bus log is ambiguous.

**Fix:** Use a new `bus_id` for the new agent. The retired agent's history is preserved under its original identity.

### M6: Promote without review

**What:** An agent is promoted from candidate to active without the 30-day review.

**Impact:** The agent may not be ready for active status. Guardrail violations may occur.

**Fix:** Always conduct the 30-day review before promoting from candidate to active.

---

## 6. Verification commands

A reader can verify an agent is properly onboarded by:

1. **Agent is in the registry:** `grep "<agent-name>" .agents/rules/agent-roster.md governance/board/registry.yaml`
2. **Guardrail exists:** `ls .agents/rules/<agent>-guardrails.md`
3. **Bus identity is approved:** `python3 -c "from hummbl_governance.services.agent_identity import is_approved; print(is_approved('<bus_id>'))"`
4. **Model tier is assigned:** `grep "<agent-name>" .agents/rules/model-tier-policy.md`
5. **Agent has posted to the bus:** `grep "^<timestamp>\s*<bus_id>" hummbl_governance/_state/coordination/messages.tsv | head -5`
6. **30-day review conducted (if 30+ days old):** `grep "<agent-name>.*30-day review" hummbl_governance/_state/coordination/messages.tsv`

If any verification fails, the agent is not properly onboarded. Open an issue.

---

## 7. Retirement checklist

When an agent is retired:

1. **Post a retirement notice:** `<bus_id> -> all STATUS: Agent <name> retiring. Last day <date>.`
2. **Archive the guardrail:** Move `.agents/rules/<agent>-guardrails.md` to `.agents/_archived/`
3. **Mark the registry entry as retired:** Add `status: retired` to the registry entry
4. **Do NOT reuse the `bus_id`:** The identity is permanently retired
5. **Conduct a final review:** Post a bus message with the agent's lifetime summary
6. **Emit a KRINEIA receipt:** `governance.agent_retired` with the agent's lifetime stats

---

## 8. Boundary disclaimer

This playbook is HUMMBL's operational protocol for agent onboarding. It is not a third-party standard. The 6-step protocol is self-defined. A third-party auditor would inspect the agent registry, guardrails, and bus logs to render an independent verdict.

HUMMBL welcomes third-party audits. The agent registry and bus logs are the same evidence an auditor would inspect.

---

## 9. How to verify this playbook

A reader can re-verify this playbook's claims by:

1. **The agent registry exists:** `ls .agents/rules/agent-roster.md governance/board/registry.yaml`
2. **The guardrail directory exists:** `ls .agents/rules/ | grep guardrails`
3. **The bus identity registry exists:** `ls hummbl_governance/services/agent_identity.py`
4. **The model tier policy exists:** `ls .agents/rules/model-tier-policy.md MODEL_TIERS.md`
5. **The coordination bus exists:** `ls hummbl_governance/_state/coordination/messages.tsv`
6. **The KRINEIA receipt chain exists:** `wc -l _receipts/krineia/primary.jsonl`

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

---

## References

- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (item 11)
- Charter: `docs/artifacts/CHARTER_hri.md` (item 12)
- Evidence pack: `docs/artifacts/EVIDENCE_PACK_fleet_rollout.md` (item 13)
- Claims change playbook: `docs/artifacts/PLAYBOOK_claims_change.md` (item 14)
- Fleet rollout playbook: `docs/artifacts/PLAYBOOK_fleet_rollout.md` (item 15)
- ADR-001: `docs/adr/ADR-001-repo-governance-baseline.md` (item 21)
- ADR-004: `docs/adr/ADR-004-single-branch-workflow.md` (item 22)
- AGENTS.md §1.3: Agent Roster & Tool Matrix
- AGENTS.md §1.5: Terminology (Phase, Mode, Tier)
- Agent roster: `.agents/rules/agent-roster.md`
- Model tier policy: `.agents/rules/model-tier-policy.md`
- Bus protocol: `.agents/rules/bus-protocol.md`
- Bus lexicon: `.agents/rules/bus-lexicon.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This playbook was drafted by Devin at the direction of the Principal Agent, based on the doctrine (item 11), charter (item 12), AGENTS.md §1.3 (agent roster), and the existing guardrail pattern, and was promoted to live (public) by Principal Agent decision on 2026-06-23. This playbook is **public** — it documents the operational protocol for agent onboarding, published for transparency.
