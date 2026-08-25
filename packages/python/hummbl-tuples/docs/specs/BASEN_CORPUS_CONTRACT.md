# BaseN Corpus Contract

Status: draft  
Scope: required fields and structural guarantees for BaseN trace corpora

## 1. Purpose

The BaseN corpus contract defines what a trace must contain before it is eligible for:

- storage
- comparison
- training
- evaluation

## 2. Required Top-Level Fields

Every BaseN trace must include:

- `trace_id`
- `task_id`
- `task`
- `problem_class`
- `protocol_id`
- `protocol_family`
- `control_mode`
- `generator_identity`
- `generator_model`
- `registry_version`
- `rubric_version` or `null`
- `quality_status`
- `steps`

## 3. Allowed Protocol Families

Allowed `protocol_family` values:

- `PROTOCOL_TRACE`
- `RUBRIC_TRACE`
- `PATH_EVAL`
- `OVERRIDE_EVENT`
- `NEGATIVE_TRACE`

## 4. Step Contract

Every step must include:

- `step_index`
- `step_type`
- `step_family`
- `content`

Optional but recommended:

- `upstream_step_refs`
- `selector_identity`
- `confidence`

## 5. Provenance Fields

Every training-eligible trace must declare:

- `source_host`
- `source_file`
- `created_at`
- `generator_prompt_family`
- `generator_version`

## 6. Quality Status

Allowed `quality_status` values:

- `UNREVIEWED`
- `VALIDATED`
- `QUARANTINED`
- `REJECTED`
- `NEGATIVE_EXAMPLE`

Training should exclude:

- `QUARANTINED`
- `REJECTED`

Unless a deliberate negative-trace curriculum is being run.

## 7. Family Separation Rules

`PROTOCOL_TRACE` must not contain rubric-labeled content as its primary supervision target.

`RUBRIC_TRACE` must not leak protocol-step content into rubric slots.

`PATH_EVAL` must not be stored as if it were a path-construction trace.

`NEGATIVE_TRACE` must be explicitly labeled rather than silently mixed into valid traces.

## 8. Training Eligibility

A trace is training-eligible only if:

- all required fields are present
- `quality_status = VALIDATED` or intentionally `NEGATIVE_EXAMPLE`
- step order matches the declared protocol
- the protocol family is semantically consistent
- no empty content fields exist

## 9. Immediate Need

The March 27 Windows rubric corpus would fail this contract because protocol families and step semantics are mixed.
