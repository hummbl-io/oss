# BaseN Readiness Probe Receipt 2026-03-27

Status: constrained key-by-key `READINESS` probing establishes the first strong win on strict holdout v2  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Goal

Strict rubric holdout v2 exposed a real problem:

- anchored section decoding preserved task shape
- but projected field recovery collapsed back to `0.0`

So the next step was to stop asking the model for a whole canonical section at once.

Instead:

1. mine likely `READINESS` keys from the anchored raw generation
2. prompt the model one key at a time with a constrained prefix:
   - `[READINESS]: <key>=`
3. map the short completion back into the allowed value vocabulary
4. render a canonical `[READINESS]` section from the recovered fields

This keeps the model weights fixed and directly tests whether the model knows field values better
than it can format a whole section.

## Eval Surface

Holdout:

- `basen_rubric_eval_holdout_v2.jsonl`

Source packet for candidate-key mining:

- `sweep_step_r130.eval_packet.json`

Checkpoint:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`

## Result

Summary:

- `cases = 8`
- `avg_field_f1 = 0.2375`
- `avg_key_f1 = 0.2875`
- `avg_value_f1 = 0.5625`
- `cases_with_candidate_keys = 7`
- `cases_with_projected_fields = 7`

This is a major improvement over the direct strict-v2 anchored decode path, which had:

- projected `avg_rubric_field_f1 = 0.0`

## What This Means

The bottleneck on strict v2 is not just semantic ignorance.

The model knows more than the whole-section decoder can reliably surface.

Specifically:

- value recovery is much stronger than whole-section raw emission
- key recovery is weaker than value recovery, but nontrivial
- canonical field assembly is now materially possible on strict v2 without retraining

## Best Cases

### Perfect case

Case:

- `rubric_0266_step_01`

Recovered fields:

- `contestation=high`
- `interdependence=high`
- `uncertainty=high`

Score:

- field F1 `1.0`
- key F1 `1.0`
- value F1 `1.0`

### Partial but strong case

Case:

- `rubric_0260_step_01`

Expected:

- `contestation=high`
- `interdependence=high`
- `uncertainty=medium`

Recovered:

- `contestation=high`
- `uncertainty=high`

Score:

- field F1 `0.4`
- key F1 `0.8`
- value F1 `0.6667`

### Another partial win

Case:

- `rubric_0252_step_01`

Recovered:

- `uncertainty=high`

Score:

- field F1 `0.5`

## Current Read

This is the best strict-v2 result so far.

And it changes the interpretation of the frontier:

- the model is not merely emitting noisy rubric words
- it can often supply correct `READINESS` values when the decoding problem is decomposed properly

So the next work should focus on:

- better key discovery
- better value probing
- and then canonical field assembly

not blind retraining first.

## Next Moves

1. make the key-mining step more deliberate instead of relying only on substring detection
2. probe keys in a fixed canonical order even when the raw generation is incomplete
3. extend the same constrained probe method to `WICKEDNESS`
4. compare probe-decoded strict-v2 performance against future retrained checkpoints
