# Bio-Governance Tuple Taxonomy

Date: 2026-03-27
Status: draft

## Purpose

Define a first tuple taxonomy for bio-cognitive and bio-governance workflows.

The intent is to govern systems that:

- observe human physical or physiological state
- infer readiness, workload, or strain
- adapt tasks, interfaces, or training
- record the authority and evidence behind those adaptations

## Design Principle

Do not treat biometric or fitness data as self-justifying.

Every action should distinguish:

- raw signal
- interpreted state
- recommended intervention
- authorized intervention
- observed outcome

## Tuple Families

### 1. Signal Tuples

Record incoming measurements or derived physical-activity facts.

#### `BIO_SIGNAL_CAPTURED`

Use when a raw or normalized signal is recorded.

Examples:

- heart rate
- heart-rate variability
- step count
- accelerometer-derived workload
- session RPE
- MET-coded activity estimate

Core fields:

- `subject_id`
- `signal_type`
- `value`
- `unit`
- `source`
- `timestamp`
- `quality_score`

#### `ACTIVITY_CLASSIFIED`

Use when an activity is mapped to a standardized activity class such as a Compendium code.

Core fields:

- `subject_id`
- `activity_code`
- `activity_label`
- `estimated_intensity`
- `classification_method`
- `confidence`

### 2. State Inference Tuples

Record interpretations about human state.

#### `READINESS_INFERRED`

Use when the system infers readiness for work, training, or decision load.

Core fields:

- `subject_id`
- `readiness_score`
- `inference_basis`
- `time_horizon`
- `confidence`

#### `WORKLOAD_INFERRED`

Use when the system infers overload, underload, or sustainable load.

Core fields:

- `subject_id`
- `workload_state`
- `drivers`
- `confidence`
- `review_required`

#### `STRAIN_FLAGGED`

Use when the system detects a risk threshold or abnormal state.

Core fields:

- `subject_id`
- `flag_type`
- `severity`
- `threshold_basis`
- `recommended_response`

### 3. Recommendation Tuples

Record proposed system actions before they are accepted.

#### `BIO_ADAPTATION_PROPOSED`

Use when the system proposes a change based on inferred state.

Examples:

- reduce task load
- change pacing
- prompt a break
- alter interface density
- reduce training load

Core fields:

- `subject_id`
- `proposed_action`
- `target_context`
- `reasoning_basis`
- `selector`
- `confidence`

### 4. Authority And Governance Tuples

Record who may act and under what rules.

#### `BIO_ACTION_AUTHORIZED`

Use when a proposed action is approved by an allowed authority.

Core fields:

- `subject_id`
- `action_id`
- `authorized_by`
- `authority_type`
- `control_mode`
- `policy_basis`

#### `BIO_ACTION_BLOCKED`

Use when governance prevents the action.

Core fields:

- `subject_id`
- `action_id`
- `blocked_by`
- `block_reason`
- `policy_basis`

#### `BIO_OVERRIDE`

Use when a human overrides an AI recommendation or when a higher authority overrides a lower one.

Core fields:

- `subject_id`
- `target_action_id`
- `override_actor`
- `override_reason`
- `replacement_action`

### 5. Execution Tuples

Record what actually happened.

#### `BIO_ADAPTATION_EXECUTED`

Use when the system or operator carries out the action.

Core fields:

- `subject_id`
- `executed_action`
- `execution_actor`
- `execution_time`
- `expected_effect`

### 6. Outcome Tuples

Record effects and evidence after action.

#### `BIO_OUTCOME_OBSERVED`

Use when there is evidence of effect.

Core fields:

- `subject_id`
- `outcome_type`
- `observed_change`
- `measurement_basis`
- `confidence`

#### `BIO_HARM_SIGNAL`

Use when the action or inference appears to have produced harm, excessive burden, or unsafe conditions.

Core fields:

- `subject_id`
- `harm_type`
- `severity`
- `triggering_action_id`
- `escalation_required`

## Human Control Modes

This taxonomy should use the existing control language:

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL`
- `HOTL`
- `HUMAN_CONTROLLED`

Bio-governance workflows should default away from full autonomy in any high-stakes setting.

## Suggested First Use Cases

- adaptive pacing for long operator sessions
- readiness-aware coaching suggestions
- ergonomic workload flags
- recovery-aware task scheduling
- logged human overrides on bio-derived recommendations

## Confidence

High on usefulness as a first taxonomy. Medium on field names because implementation details will depend on the exact signal stack.
