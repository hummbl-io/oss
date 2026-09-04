# BaseN Rubric Schema Receipt 2026-03-27

Status: first schema-normalized rubric target pass  
Scope: `<local-path>/autoresearch-yolo`

## Goal

The field-level scorer exposed a core limitation:

- the rubric lane was learning concepts
- but not emitting canonical `key=value` structure

To reduce ambiguity, rubric target prep was changed to:

1. normalize section ordering and field ordering
2. trim each training/eval target to the active target step when possible
   - for example, a `[READINESS]` step now teaches only `[READINESS]: ...`
   - instead of mixing `[WICKEDNESS]` + `[READINESS]` into the same target

## Normalized-Trimmed Checkpoint

Checkpoint:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`

Training:

- `lr = 5e-5`
- `epochs = 2`
- validated rubric train split

## Evaluation

### Anchored decode with `target_step`

- decode:
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`
- result:
  - `val_bpb = 0.394567`
  - `avg_teacher_forced_loss = 2.7779`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.2958`
  - `avg_rubric_field_f1 = 0.0`

Interpretation:

- schema-normalized training improved free-generation recall over the prior rubric record
- but still did not produce valid canonical field emissions

### Anchored decode with `target_step_colon`

- decode:
  - `--force-prefix target_step_colon`
  - `--repetition-penalty 1.30`
- result:
  - `val_bpb = 0.394567`
  - `avg_teacher_forced_loss = 2.7779`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3375`
  - `avg_rubric_field_f1 = 0.0`

Interpretation:

- this is the new best rubric free-generation record
- the colon-anchored section label materially improves structured recall
- field-level correctness is still zero, so the model remains pre-schema-compliant

### Colon anchor plus no-repeat ngram blocking

- decode:
  - `--force-prefix target_step_colon`
  - `--repetition-penalty 1.30`
  - `--no-repeat-ngram-size 3`
  - `--stop-on-repeat`
- result:
  - `avg_keyword_hit_rate = 0.2792`
  - `avg_rubric_field_f1 = 0.0`

Interpretation:

- extra decode constraints reduced quality here
- the simpler colon-anchor decode remains the best normalized-schema surface

## Current Conclusion

Schema normalization was worth doing.

It produced:

- a new rubric free-generation record:
  - `avg_keyword_hit_rate = 0.3375`
- at essentially the same retention budget as the prior 2-epoch balance point

But it did **not** yet produce nonzero field-level F1.

So the frontier moved from:

- concept recall under loose formatting

toward:

- stronger section-conditioned output

but not yet to:

- reliable canonical `key=value` generation
