# BaseN Validator Implementation Plan

Status: draft  
Scope: first executable validator for March 27 BaseN corpora

## 1. Purpose

The current BaseN work needs an actual validator, not just validation principles.

This plan defines the first implementation target for validating:

- `nodezero_hummbl_traces_v2_rubric.jsonl`
- `nodezero_hummbl_traces_concise.jsonl`
- future `BaseN` corpora before training

## 2. First Target

Build a lightweight validator that emits one record per trace:

- `trace_id` or synthetic row id
- `status`
- `protocol_family`
- `protocol_id`
- `error_codes`
- `warning_codes`

Allowed statuses:

- `VALIDATED`
- `QUARANTINED`
- `REJECTED`

## 3. Minimum Checks

### 3.1 Structure

Check:

- top-level JSON parses
- required top-level fields exist
- `steps` exists and is non-empty
- each step has:
  - `type`
  - `content`

### 3.2 Step Count

Check expected bounds:

- `ScientificMethod`: `5`
- `WickednessAudit`: `4`

Mismatch => `QUARANTINED`

### 3.3 Protocol Leakage

For `ScientificMethod`:

- flag content containing:
  - `[WICKEDNESS]`
  - `[READINESS]`
  - `[BKI]`
  - `contestation=`
  - `authority=`

For `WickednessAudit`:

- flag content containing:
  - `Observation`
  - `Hypothesis`
  - `Experiment`
  - `Result`
  - `Evaluation`

These are not perfect checks, but they are enough to catch the current failure mode.

### 3.4 Empty / Placeholder Content

Flag:

- empty strings
- `Error generating response`
- `Request error`
- fallback boilerplate

### 3.5 Duplicate Content

Within a trace:

- if multiple steps have identical `content`, flag as suspicious

### 3.6 Content Length Sanity

Flag:

- rubric fields that are too long for tuple-like output
- concise fields that are implausibly short or empty

## 4. Output Files

Recommended outputs:

- `basen_validation_report.jsonl`
- `basen_validation_summary.json`
- optional `basen_quarantine.jsonl`

## 5. Error Codes

Suggested first set:

- `MISSING_TOP_LEVEL_FIELD`
- `MISSING_STEP_FIELD`
- `STEP_COUNT_MISMATCH`
- `PROTOCOL_LEAKAGE`
- `EMPTY_CONTENT`
- `PLACEHOLDER_CONTENT`
- `DUPLICATE_STEP_CONTENT`
- `RUBRIC_TOO_VERBOSE`

## 6. Immediate Use

The validator should be run before:

- `hummbl_basen_sft.py`
- `hummbl_sft.py`
- any future corpus promotion

## 7. Strong Next Step

Once the validator exists, the rubric corpus should be split into:

- validated rows
- quarantined rows
- rejected rows

The alignment loop should consume only validated rows by default.
