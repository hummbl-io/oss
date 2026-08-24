# HUMMBL TierShift: Governed Execution-Intensity Architecture

## Status

- **Concept status:** candidate (approved engineering work, not canon)
- **Canon status:** not canon — admitted-internal only
- **Issue:** #560
- **Approval:** Operator chat approval 2026-06-28: "All approved."
- **Namespace:** bare `TierShift` on public-use hold pending namespace/legal review (#540, PR #541)

## Purpose

Define **HUMMBL TierShift** as a governed workflow for selecting, escalating, holding, or downgrading cognitive execution intensity until the reasoning budget matches the consequence surface.

> HUMMBL TierShift is a governed workflow for selecting, escalating, holding, or downgrading cognitive execution intensity until the reasoning budget matches the consequence surface.

## Core Invariants

1. Do not describe tiers as intelligence levels
2. Prefer language: cognitive execution tier, reasoning budget, consequence surface, routing posture, execution intensity
3. XHigh is a gated posture or ceiling, not automatic execution
4. A TierShift preference is not a route card unless attached to a bounded task
5. Downgrading is precision, not failure
6. Bare `TierShift` remains on public-use hold pending namespace/legal review
7. HUMMBL TierShift remains candidate/admitted-internal until source-of-record gates close

## Vocabulary

### Canonical (admitted-internal)

| Term | Status | Description |
|------|--------|-------------|
| `HUMMBL TierShift` | admitted-internal | Governed execution-intensity architecture |
| `cognitive execution tier` | canonical | The intensity level of reasoning (Low, Medium, High, XHigh) |
| `reasoning budget` | canonical | Token/time/compute budget allocated to a task |
| `consequence surface` | canonical | The reversibility, visibility, and scope of a task's consequences |
| `routing posture` | canonical | The current stance (escalate, downgrade, hold, seal, recover) |
| `execution intensity` | canonical | The overall intensity of cognitive work |

### Noncanonical (on hold)

| Term | Status | Reason |
|------|--------|--------|
| `TierShift` (bare) | public-use hold | Pending namespace/legal review (#540) |
| `Tier Shift` (with space) | public-use hold | Pending namespace/legal review |

### Not Used

| Term | Reason |
|------|--------|
| `intelligence level` | Tiers are not intelligence levels |
| `smartness tier` | Tiers are not smartness |
| `power level` | Tiers are not power |

## Cognitive Execution Tiers

| Tier | Description | Typical Use |
|------|-------------|-------------|
| `Low` | Minimal reasoning budget | Trivial, reversible, low-consequence tasks |
| `Medium` | Standard reasoning budget | Normal development, documentation, tests |
| `High` | Elevated reasoning budget | Complex reasoning, public-surface changes, multi-step plans |
| `XHigh` | Maximum reasoning budget (gated) | Safety-critical, irreversible, fleet-wide, external-client |

**XHigh is a gated posture or ceiling, not automatic execution.** Escalation to XHigh requires operator approval, adversarial review, and CI gate pass.

## Actions

| Action | Description |
|--------|-------------|
| `escalate` | Increase cognitive execution tier |
| `downgrade` | Decrease cognitive execution tier (precision, not failure) |
| `hold` | Maintain current tier pending evidence |
| `seal` | Lock tier at current level (no further shifts) |
| `recover` | Revert from a failed/reverted shift |

## Consequence Surface

The consequence surface determines the appropriate reasoning budget:

| Dimension | Values | Description |
|-----------|--------|-------------|
| `reversibility` | reversible, partially_reversible, irreversible | Can consequences be undone |
| `visibility` | internal, team, public, external_client | Who sees the consequences |
| `scope` | single_task, multi_task, project, fleet | How far-reaching are consequences |

**Matching rule:** The reasoning budget should match the consequence surface. Higher consequence → higher tier. Lower consequence → lower tier.

## Route Card vs Preference

A TierShift **preference** is a default or suggested tier. It is not binding.

A TierShift **route card** is a preference attached to a bounded task. It is binding for that task.

**Rule:** A TierShift preference is not a route card unless attached to a bounded task.

## Architecture Lanes

| Lane | Description | Status |
|------|-------------|--------|
| 1. Agent routing primitive | Route agents to appropriate tiers | candidate schema |
| 2. Governance gate | Gate XHigh escalation | defined (required_receipts) |
| 3. Operator cockpit/UI | Operator controls tier shifts | future |
| 4. Human operating-state protocol | Human cognitive state informs tier | future |
| 5. Breath/Breathe crosswalk | Breath protocol ↔ tier | future |
| 6. Local/cloud compute router | Compute class matches tier | candidate (compute_class field) |
| 7. GitHub issue/PR workflow | CI gates for tier shifts | future |
| 8. Agent-to-agent bus protocol | Bus messages for tier shifts | candidate schema |
| 9. Ownward coaching application | Ownward uses tier shifts | future (cross-link: hummbl-governance) |
| 10. HUMMBL Sound / sonic state-change | Sound family for tier changes | future (cross-link: hummbl-music) |

## Event Schema

The `tier_shift_event` schema captures:

- `prior_tier` / `proposed_tier`: the shift
- `action`: escalate / downgrade / hold / seal / recover
- `basis`: reasons for the shift
- `required_receipts`: receipts needed before execution
- `status`: proposed / approved / rejected / executed / reverted
- `consequence_surface`: reversibility, visibility, scope
- `reasoning_budget`: token, time, compute class
- `gates_passed`: governance gates that have passed

## Required Gates

| Gate | Description |
|------|-------------|
| `G-NAMESPACE-AUDIT` | Namespace audit clearance (bare TierShift) |
| `G-SOURCE-OF-RECORD` | Source-of-record verified |
| `G-NO-ACCIDENTAL-CANONIZATION` | No accidental canonization |
| `G-PUBLIC-USE-HOLD` | Public-use hold respected |
| `G-OPERATOR-APPROVAL` | Operator approval for XHigh |
| `G-RECEIPT-EMITTED` | Receipt emitted after execution |
| `G-CI-ROUTING-BOUNDARY` | CI routing boundary respected |

## Downshift Semantics

**Downgrading is precision, not failure.**

A downgrade from High to Medium is not a failure of the task. It is a recognition that the consequence surface has contracted (e.g., scope narrowed, reversibility restored) and the reasoning budget should match.

## Hold Semantics

A `hold` maintains the current tier pending evidence. This is used when:
- Evidence is insufficient to escalate or downgrade
- An adversarial review is in progress
- The consequence surface is ambiguous

## Seal Semantics

A `seal` locks the tier at the current level. No further shifts are allowed. This is used when:
- The task is in a critical phase
- Further shifts would destabilize the workflow
- The operator has sealed the tier explicitly

## Cross-Links

- #540 — candidate namespace audit (bare `TierShift` public-use hold)
- #541 — draft PR adding source-of-record namespace audit artifacts
- hummbl-governance — Ownward application (future issue)
- hummbl-music — Sound family (future issue)
- hummbl-governance — PR/CI declaration gate (future issue)

## Acceptance Criteria

- [x] Define canonical/noncanonical vocabulary for HUMMBL TierShift
- [x] Add architecture note tying consequence surface to reasoning budget and execution intensity
- [x] Define event schema for agent-to-agent bus messages
- [x] Define route-card interaction: when TierShift is a preference vs a bounded task route
- [x] Define downshift/hold/escalate/seal semantics
- [ ] Cross-link to Ownward application issue in hummbl-governance (future)
- [ ] Cross-link to sound-family issue in hummbl-music (future)
- [ ] Cross-link to PR/CI declaration-gate issue in hummbl-governance (future)
- [x] Confirm no conflict with #540 / #541 namespace audit source-of-record
- [ ] Emit final receipt after implementation and review (after merge)

## Do Not Infer

- Do not infer that `TierShift` (bare) is cleared for public use
- Do not infer that HUMMBL TierShift is canon
- Do not infer that tiers are intelligence levels
- Do not infer that XHigh is automatic
- Do not infer that downgrading is failure
- Do not infer that all 10 architecture lanes are implemented
