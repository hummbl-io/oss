# BaseN Validation Rules

Status: draft  
Scope: rules for validating BaseN traces before training or promotion

## 1. Purpose

BaseN traces must pass validation before they are treated as evidence-bearing or training-worthy artifacts.

## 2. Structural Rules

Reject a trace if:

- required top-level fields are missing
- `steps` is empty
- any step is missing `step_index`, `step_type`, or `content`
- step indices are duplicated or out of order

## 3. Protocol Consistency Rules

Reject or quarantine a trace if:

- a `ScientificMethod` trace contains `WICKEDNESS`/`READINESS` rubric output in step content
- a `WickednessAudit` trace emits protocol-step text instead of rubric tuples
- step count falls outside the bounds for the declared protocol
- step types do not match the declared protocol order

## 4. Content Quality Rules

Reject or quarantine a trace if:

- content is empty
- content is duplicated across multiple steps without explanation
- content is placeholder text only
- content is obviously malformed JSON or prompt leakage
- content repeats the wrong protocol family

## 5. Family-Separation Rules

Quarantine a trace if:

- `PROTOCOL_TRACE` behaves like `RUBRIC_TRACE`
- `RUBRIC_TRACE` behaves like `PROTOCOL_TRACE`
- `PATH_EVAL` is mixed into path-construction data

## 6. Negative Trace Rules

Do not silently discard failures.

Instead:

- relabel malformed or bad-but-informative traces as `NEGATIVE_TRACE`
- capture the failure reason
- separate them from the positive corpus by policy

## 7. Promotion Rules

A trace may be promoted from `UNREVIEWED` to `VALIDATED` only if:

- structure passes
- protocol consistency passes
- content quality passes
- provenance fields are present

## 8. Minimum Validator Outputs

The validator should emit:

- pass/fail
- rejection reason
- quarantine reason
- protocol-family mismatch counts
- duplicate or malformed trace counts

## 9. Immediate Application

The current March 27 rubric corpus should be treated as:

- `UNREVIEWED` at best
- and partially `QUARANTINED` once protocol-family leakage is checked programmatically
