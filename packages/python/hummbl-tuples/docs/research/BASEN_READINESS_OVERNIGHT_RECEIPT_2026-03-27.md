# BaseN Readiness Overnight Receipt 2026-03-27

Status: completed longer-running strict-v2 `READINESS` key-prior sweep on Windows

## Purpose

After the earlier strict-v2 `READINESS` loop settled on:

- checkpoint family: readiness-clean and normtrim leaders
- probe mode: `candidate_plus_core`
- main bottleneck: better key discovery

the next question was whether a longer-running prior sweep could beat the standing frontier by adding:

- task-aware key priors
- history-aware key priors
- combined task+history priors

under one comparable overnight harness.

## Harness

Windows script:

- `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\basen_readiness_overnight.py`

Matrix:

- checkpoints:
  - `hummbl_basen_readiness_clean_2ep.pt`
  - `hummbl_basen_readiness_clean_1ep.pt`
  - `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- probe mode:
  - `candidate_plus_core`
- prior modes:
  - `none`
  - `task`
  - `history`
  - `task_history`
- `max_fields`:
  - `2`
  - `3`
- `min_combined_score`:
  - `0.85`
  - `0.95`

Outputs:

- `basen_readiness_overnight_full.json`
- `basen_readiness_overnight_full.tsv`

## Best Row In This Sweep

Best row produced by the overnight harness:

- checkpoint: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- probe mode: `candidate_plus_core`
- prior mode: `none`
- `max_fields = 3`
- `min_combined_score = 0.85`
- `val_bpb = 0.388272`
- `avg_keyword_hit_rate = 0.3458`
- `avg_teacher_forced_loss = 2.6395`
- `avg_field_f1 = 0.2500`
- `avg_key_f1 = 0.3750`
- `avg_value_f1 = 0.6875`
- `cases_with_projected_fields = 8/8`

Equivalent rows tied this result across:

- `prior_mode = task`
- `prior_mode = history`
- `prior_mode = task_history`
- `min_combined_score = 0.95`

So the priors did not improve the frontier. They mostly collapsed to the same outcome as the baseline candidate set on this surface.

## Comparison To Standing Strict-v2 Leader

The previously established strict-v2 `READINESS` leader remains stronger:

- checkpoint: `hummbl_basen_readiness_clean_2ep.pt`
- probe mode: `candidate_plus_core`
- metrics from prior receipt:
  - `avg_field_f1 = 0.2589`
  - `avg_key_f1 = 0.4866`
  - `avg_value_f1 = 0.7083`

So this overnight harness did **not** set a new strict-v2 record.

## What Settled

1. The longer-running prior sweep is operationally sound.
2. Task and history priors did not improve the strict-v2 frontier.
3. The best overnight rows came from the older normtrim checkpoint, but only under a weaker field/key frontier than the standing leader.
4. Extra combinatorics on the current priors are unlikely to be the next real lever.

## Interpretation

This is a useful negative result.

It means:

- the current candidate generator is not failing merely because it lacks coarse task/history bias
- better priors will likely need to be more specific than the current hand-written rules
- the next likely gains are:
  - smarter candidate generation from field/value evidence
  - better canonical micro-corpus quality
  - or extending the constrained lane to another target family rather than overfitting `READINESS`

## Current Status

- long-running harness: working
- overnight sweep: completed
- new frontier: no
- evidence gained: yes
