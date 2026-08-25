# BaseN READINESS Constrained Lane

Status: first official constrained BaseN lane

## Purpose

`READINESS` is now the first official constrained lane for BaseN proof work.

Reason:

- it has enough recurring structure to evaluate rigorously
- it is narrower than the full rubric surface
- and it is now the strongest path for proving that BaseN preserves governed reasoning structure
  rather than just generating rubric-like prose

## Canonical Eval Priority

Primary proving surface:

- `basen_rubric_eval_holdout_v2.jsonl`

Primary model family:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- `hummbl_basen_readiness_clean_2ep.pt`

Primary decode family:

- constrained `READINESS` key/value probing

Secondary surface:

- pre-rebuild holdout v1 for continuity with earlier frontier claims

## Core Task

Given:

- task
- protocol
- prior history
- target step `[READINESS]`

The lane should recover canonical `READINESS` fields and values.

## Canonical READINESS Keys

- `authority`
- `capacity`
- `necessity`
- `adaptability`
- `resilience`
- `robustness`
- `complexity`
- `predictability`
- `contestation`
- `interdependence`
- `uncertainty`

## Current Default Probe Mode

Default strict-v2 probe mode:

- `candidate_plus_core`

Where:

- candidate keys come from the raw generation
- core keys are always eligible fallbacks:
  - `authority`
  - `capacity`
  - `contestation`
  - `interdependence`
  - `uncertainty`

## Primary Metrics

- field F1
- key F1
- value F1
- cases with projected fields
- teacher-forced loss
- `val_bpb`

## Current Frontier

Best strict-v2 `READINESS` result so far:

- field F1 `0.2589`
- key F1 `0.4866`
- value F1 `0.7083`

This is currently the sharpest proof surface for BaseN.

## Design Rule

Do not judge `READINESS` progress only by:

- keyword hit rate
- raw whole-section generations

Judge it by:

- structured recovery under constrained probing
- stability on strict-v2
- and whether improvements survive versioned eval surfaces
