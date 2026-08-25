# BaseN Rubric Holdout V2 Receipt 2026-03-27

Status: stricter rebuilt rubric holdout surfaced a regression in the projected-field win  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Why This Exists

After the first projected-field win, the rubric holdout builder was patched so that:

- bare `key=value` responses are canonicalized under the active target step
- `expected_field_items` are always populated when the target text is structurally recoverable

That produced a stricter and cleaner holdout surface.

It also changed the evaluation behavior materially enough that it must be treated as a versioned
surface, not a silent replacement.

## Holdout V2 Rebuild

Builder:

- `prepare_basen_rubric_split.py`

Rebuild result:

- validated traces: `89`
- train traces: `81`
- holdout cases: `8`

## Leader Re-check On Holdout V2

Checkpoint:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`

Decode:

- `--force-prefix target_step_colon`
- `--repetition-penalty 1.30`

Result:

- `val_bpb = 0.388272`
- `avg_keyword_hit_rate = 0.3458`
- `avg_teacher_forced_loss = 2.6395`
- raw `avg_rubric_field_f1 = 0.0`
- projected `avg_rubric_field_f1 = 0.0`

Interpretation:

- the earlier projected-field win did not survive the stricter rebuilt holdout under the same
  anchored decode
- this is a real negative result, not noise to ignore

## Decode Sweep On Holdout V2

Same checkpoint, stricter holdout, multiple decode settings:

- `force-prefix=none`, `repetition-penalty=1.0`
  - `starts_with_target = 0/8`
  - `avg_keyword_hit_rate = 0.1167`
  - projected `avg_rubric_field_f1 = 0.0625`
- `force-prefix=target_step`, `repetition-penalty=1.30`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3458`
  - projected `avg_rubric_field_f1 = 0.0`
- `force-prefix=target_step_colon`, `repetition-penalty=1.0`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3208`
  - projected `avg_rubric_field_f1 = 0.0`
- `force-prefix=target_step_colon`, `repetition-penalty=1.15`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3000`
  - projected `avg_rubric_field_f1 = 0.0`
- `force-prefix=target_step_colon`, `repetition-penalty=1.30`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3458`
  - projected `avg_rubric_field_f1 = 0.0`
- `force-prefix=target_step_colon`, `repetition-penalty=1.30`, `no-repeat-ngram-size=3`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.2083`
  - projected `avg_rubric_field_f1 = 0.0`

## Best Strict-V2 Point

The best projected field recovery on the stricter rebuilt holdout is currently:

- unanchored decode
- `repetition-penalty = 1.0`
- projected `avg_rubric_field_f1 = 0.0625`

But that comes with:

- `starts_with_target = 0/8`
- poor keyword recall

So it is not a clean replacement for the anchored frontier.

## Current Read

There are now two rubric evaluation surfaces:

1. pre-rebuild holdout v1
   - still the surface on which the projected-field frontier reached `0.1000`
2. rebuilt holdout v2
   - stricter and cleaner
   - currently unresolved because the anchored decode loses projected field recovery

This is exactly the kind of divergence that should be versioned, not hand-waved.

## Next Moves

1. version the holdout explicitly as `v1` / `v2` in file names, not just docs
2. inspect why the rebuilt holdout changed the generated responses enough to erase the anchored win
3. improve strict-v2 projection so it can recover fields without abandoning section anchoring
