# World-Model Event Tuples v0.1 — Design Note

**Status:** Candidate event semantics. Noncanonical until separately reviewed and admitted.

**Parent:** [hummbl-dev/hummbl-dev#149](https://github.com/hummbl-dev/hummbl-dev/issues/149)
**Crosswalk:** [hummbl-models#9](https://github.com/hummbl-dev/hummbl-models/issues/9) (candidate model fragment schema)

## Purpose

Extend BaseN's governed reasoning-path substrate with typed events for
operating over partial, user-owned world models.

## Key distinction

- **Mental models** are reasoning operators (Base120)
- **World models** are stateful predictive representations
- **Tuples** record who selected or changed a path/state, under what
  authority, with what evidence and receipts

## Event families

| Family | Schema | Purpose |
| ------ | ------ | ------- |
| `OBSERVATION_EVENT` | `observation_event.schema.json` | Raw observation with normalized/system/user interpretations |
| `STATE_ASSERTION` | `state_assertion.schema.json` | Assert a state at a point in time |
| `STATE_TRANSITION` | `state_transition.schema.json` | Record state change |
| `MODEL_PROPOSAL` | `model_proposal.schema.json` | Propose a candidate model from observations |
| `PREDICTION_EVENT` | `prediction_event.schema.json` | Predict outcome with horizon and evaluation method |
| `COUNTERFACTUAL_EVENT` | `counterfactual_event.schema.json` | Counterfactual reasoning |
| `CONTRADICTION_EVENT` | `contradiction_event.schema.json` | Record contradiction without forcing consensus |
| `ACTION_SELECTION` | `action_selection.schema.json` | Select action based on model |
| `OUTCOME_OBSERVATION` | `outcome_observation.schema.json` | Observe outcome of action/prediction |
| `MODEL_REVISION` | `model_revision.schema.json` | Revise model with supersession |
| `MODEL_RETRACTION` | `model_retraction.schema.json` | Retract a model |
| `CONSENT_CHANGE` | `consent_change.schema.json` | Consent state change as first-class event |
| `VISIBILITY_CHANGE` | `visibility_change.schema.json` | Visibility state change as first-class event |

## Shared minimum envelope

Every event defines or references:

- `tuple_type` — event family
- `id` — unique event ID
- `time` — event timestamp
- `actor` — who triggered the event
- `principal` — human principal on whose behalf
- `control_mode` — authority posture
- `target_model` — model reference (if applicable)
- `evidence_links` — supporting evidence
- `uncertainty_posture` — uncertainty classification
- `receipt_link` — receipt reference
- `previous_version` — prior state (if applicable)
- `next_version` — successor state (if applicable)
- `visibility_class` — privacy/visibility

## Observation semantics

Structurally separated:

1. `original_expression` — raw user expression or measurement
2. `normalized_observation` — system-normalized form
3. `system_interpretation` — AI/system interpretation
4. `user_approved_interpretation` — user-approved interpretation (if any)

## Prediction semantics

Required fields:

- `predicted_outcome` — what is predicted
- `horizon` — evaluation window
- `conditions` — assumptions
- `uncertainty_posture` — uncertainty classification
- `evaluation_method` — how to evaluate
- `related_model_version` — model used

## Contradiction semantics

Contradictions can remain unresolved:

- `competing_claims` — the competing claims/states
- `supporting_contexts` — contexts in which each is supported
- `suspected_missing_variables` — possible conditioning variables
- `resolution_posture` — `unresolved` / `partially_resolved` / `resolved`

## Revision semantics

Required:

- `prior_model_version` — what is being revised
- `triggering_evidence` — what triggered the revision
- `changed_fields` — what changed
- `user_approval_posture` — approval state
- `supersession_semantics` — how the old version is superseded

## Consent and visibility as events

Consent and visibility changes are first-class events, not mutable
hidden metadata. This ensures auditability.

## Crosswalk to BaseN

World-model event tuples use the same envelope architecture (Layer 1
universal + Layer 3 domain). They do not use Layer 2 governance fields
unless wrapped in an IDP context.

## Crosswalk to candidate model fragments

`MODEL_PROPOSAL` events reference `candidate-model-fragment.v0.1.json`
fragments via `target_model.fragment_ref`. The event records the act
of proposing; the fragment records the proposed content.

## Non-goals

- No private user database
- No application UI
- No public federation protocol
- No claim that BaseN is itself a world model
- No synthetic chain-of-thought requirement
- No unrestricted autonomous action authority
