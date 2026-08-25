# Multi-Actor Epistemic Events v0.1 — Design Note

**Status:** Candidate event semantics. Noncanonical until separately reviewed and admitted.

**Parent:** [hummbl-dev/hummbl-dev#151](https://github.com/hummbl-dev/hummbl-dev/issues/151)
**Depends on:** [hummbl-tuples#84](https://github.com/hummbl-dev/hummbl-tuples/issues/84) (World-Model Event Tuples)
**Crosswalk:** [hummbl-models#10](https://github.com/hummbl-dev/hummbl-models/issues/10) (Multi-Actor Model Envelope)

## Purpose

Extend the world-model event family with explicit human/agent attribution,
delegation, dissent, ratification, coalition, and calibration events.

The event model ensures that agent inferences do not silently become user
beliefs, organization-ratified state, durable shared state, or action
authority.

## Event families (32 types)

### Agent lifecycle
- `AGENT_REGISTERED` — agent enters the system
- `AGENT_VERSION_CHANGED` — version change (may invalidate calibration)
- `AGENT_ROLE_ASSIGNED` — role assignment
- `AGENT_ROLE_EXPIRED` — role expiration
- `AGENT_QUARANTINED` — agent quarantined
- `AGENT_REBOUND` — agent returns from quarantine

### Delegation
- `DELEGATION_GRANTED` — delegation granted
- `DELEGATION_REVOKED` — delegation revoked

### Agent epistemic actions
- `AGENT_OBSERVATION` — agent observes
- `AGENT_INFERENCE` — agent infers (must not be labeled as user belief)
- `AGENT_MODEL_PROPOSAL` — agent proposes a model
- `AGENT_CHALLENGE` — agent challenges a claim
- `AGENT_DISSENT` — agent dissents (survives handoff)

### Ratification and rejection
- `USER_RATIFICATION` — user ratifies (does not imply action authorization)
- `USER_REJECTION` — user rejects
- `ORG_RATIFICATION` — organization ratifies
- `ORG_REJECTION` — organization rejects

### Model lifecycle
- `MODEL_MERGE_PROPOSAL` — propose merge (must acknowledge dissent)
- `MODEL_MERGE_ACCEPTED` — merge accepted
- `MODEL_MERGE_REJECTED` — merge rejected
- `MODEL_FORK` — fork a model

### Handoff and tools
- `HANDOFF_EVENT` — handoff between actors (dissent preserved)
- `TOOL_RESULT_PROPOSED` — tool result proposed for admission
- `TOOL_RESULT_ADMITTED` — tool result admitted

### Action authority
- `ACTION_PROPOSED` — propose an action
- `ACTION_AUTHORIZED` — authorize (separate from ratification)
- `ACTION_DENIED` — deny an action
- `ACTION_EXECUTED` — execute an authorized action

### Calibration
- `AGENT_CALIBRATION_UPDATED` — domain/task/version specific calibration

### Coalition
- `COALITION_FORMED` — coalition formed (cannot self-expand)
- `COALITION_MEMBERSHIP_CHANGED` — membership change
- `COALITION_DISSOLVED` — coalition dissolved

## Attribution envelope

Every event distinguishes:

- `authored_by` — who authored the content
- `represented_principal` — the human principal represented
- `owner` — who owns the durable state
- `approved_by` — who approved
- `challenged_by` — who challenged
- `executed_by` — who executed
- `receipted_by` — who generated the receipt
- `agent_version` — agent version (if applicable)
- `delegation_id` — delegation reference (if applicable)
- `actor_regime` — the actor regime

## Permission envelope

Every event declares:

- `epistemic_permission` — observe/infer/claim/challenge
- `durable_write_permission` — write/revise/retire/none
- `action_permission` — propose/authorize/execute/none
- `approval_requirement` — required/not_required/waived
- `authority_source` — source of authority
- `scope` — scope of authority
- `expiry` — expiry of authority
- `revocation_state` — active/revoked/expired

## Independence lineage

Events asserting corroboration, consensus, or calibration reference:

- `model_provider`
- `source_lineage`
- `retrieval_lineage`
- `tool_lineage`
- `environment_lineage`
- `evaluator_lineage`
- `independence_class` — independent/correlated/single_lineage/unknown

## Key invariants

1. **Agent inference ≠ user belief** — AGENT_INFERENCE must not be labeled as user belief
2. **Ratification ≠ action authorization** — USER_RATIFICATION does not grant action authority
3. **Dissent survives handoff** — AGENT_DISSENT remains attached after bounded action
4. **Correlated ≠ independent** — independence_class must be declared
5. **Coalition authority is bounded** — cannot self-expand mission or authority
6. **Calibration is specific** — domain/task/version specific, no universal scalar reputation
7. **Revoked delegation invalidates** — revocation_state="revoked" cannot be used
8. **Merge must acknowledge dissent** — unresolved_dissent_acknowledged required

## Adversarial checks

1. MODEL_MERGE_PROPOSAL with unresolved_dissent_acknowledged=False — rejected
2. COALITION_FORMED with action_permission != "none" — rejected
3. COALITION_FORMED with coalition_authority="unrestricted" — rejected
4. ACTION_EXECUTED with AI_AUTONOMOUS + approval_requirement="not_required" — rejected
5. Any event with revocation_state="revoked" — rejected
6. self_authorizing_agent regime — rejected

## Validation

```bash
python scripts/validate_multi_actor_events.py
```

## Non-goals

- No hidden chain-of-thought capture
- No majority-as-truth default
- No self-authorizing production agent regime
- No new event-runtime repository
- No federation protocol
