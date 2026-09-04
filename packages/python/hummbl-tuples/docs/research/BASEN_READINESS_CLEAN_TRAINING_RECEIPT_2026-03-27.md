# BaseN Readiness Clean Training Receipt 2026-03-27

Status: first readiness-only clean training loop on strict holdout v2  
Scope: `<local-path>`

## Goal

After the first strict-v2 `READINESS` probe win, the next question was:

- does a small clean readiness-only fine-tune improve strict-v2 recovery beyond decode-only probing?

## Clean Training Set

Builder:

- `prepare_basen_readiness_clean.py`

Selection rules:

- source: validated rubric train split
- target step: `[READINESS]` only
- canonical keys only
- canonical values only
- `1` to `3` fields per example

Result:

- `68` readiness-clean training rows

Allowed key surface:

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

## Training

Trainer:

- `hummbl_readiness_sft.py`

Init checkpoint:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`

Config:

- `lr = 2e-5`
- `epochs = 2`
- response-only masking
- readiness-only target format

Output checkpoint:

- `hummbl_basen_readiness_clean_2ep.pt`

## Direct Anchored Eval On Holdout V2

Decode:

- `--force-prefix target_step`
- `--repetition-penalty 1.30`

Result:

- `val_bpb = 0.390373`
- `avg_keyword_hit_rate = 0.3208`
- `avg_teacher_forced_loss = 2.3918`
- raw `avg_rubric_field_f1 = 0.0`
- projected `avg_rubric_field_f1 = 0.0`

Interpretation:

- training improved teacher-forced fit
- but did not by itself solve whole-section field emission on strict v2

## Constrained Readiness Probe On Holdout V2

Probe mode:

- first pass: `candidate`
- improved pass: `candidate_plus_core`

Best result:

- `avg_field_f1 = 0.2589`
- `avg_key_f1 = 0.4866`
- `avg_value_f1 = 0.7083`
- `cases_with_projected_fields = 8/8`

Comparison to the earlier probe baseline on the same strict-v2 surface:

- prior normtrim candidate-only probe:
  - field F1 `0.2375`
  - key F1 `0.2875`
  - value F1 `0.5625`
- readiness-clean `candidate_plus_core` probe:
  - field F1 `0.2589`
  - key F1 `0.4866`
  - value F1 `0.7083`

## Current Read

This is a real improvement.

The small clean training set did not make the raw decoder good enough on its own,
but when paired with better key selection it produced the strongest strict-v2 `READINESS`
result so far.

So the path forward is:

- small clean training sets
- plus constrained probing
- plus explicit key-selection strategy

not raw section generation alone.
