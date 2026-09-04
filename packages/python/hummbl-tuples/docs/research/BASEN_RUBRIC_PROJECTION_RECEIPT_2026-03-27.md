# BaseN Rubric Projection Receipt 2026-03-27

Status: first nonzero rubric field-level score via decode-time schema projection  
Scope: `<local-path>/autoresearch-yolo`

## Goal

The schema-normalized rubric leader had reached:

- strong section anchoring
- improved keyword recall
- but `avg_rubric_field_f1 = 0.0`

The next step was to keep the model weights fixed and improve only the eval/decode surface.

Two fixes were added:

1. target-label-aware expected-field canonicalization
   - malformed holdout rows like `Output: contestation=high, uncertainty=medium, interdependence=high`
     are now scored under the active target step instead of collapsing to empty truth
2. decode-time schema projection
   - generated rubric text is projected into one canonical target-step section using the
     observed label-specific key/value vocabulary

This is intentionally a decode/eval-side improvement, not a new training claim.

## Leader Re-evaluation

Checkpoint:

- `hummbl_basen_aligned_codex_normtrim_2ep.pt`

Decode:

- `--force-prefix target_step_colon`
- `--repetition-penalty 1.30`

Result:

- `val_bpb = 0.388272`
- `avg_keyword_hit_rate = 0.3875`
- `avg_teacher_forced_loss = 2.8027`
- raw `avg_rubric_field_f1 = 0.0`
- projected `avg_rubric_field_f1 = 0.1000`

Interpretation:

- this is the first nonzero field-level rubric score in the BaseN proof loop
- the signal comes from schema projection recovering one correct canonical field from a malformed
  generation, not from exact raw emission
- the leader remains the same checkpoint as the schema-normalized frontier

## Winning Case

Case:

- `rubric_0260_step_01`

Expected canonical fields:

- `READINESS:contestation=high`
- `READINESS:interdependence=high`
- `READINESS:uncertainty=medium`

Raw generation:

```text
[READINESS]: contestationmigh, interdependence-toise, uncertaintymummedium, ...
```

Projected canonical response:

```text
[READINESS]: contestation=high, uncertainty=medium
```

Projected score:

- precision `1.0`
- recall `0.6667`
- F1 `0.8`

This is narrow, but real. The field scorer is no longer completely blind to recoverable structure.

## Comparison Against Prior Rubric Leaders

Same projected scorer, same decode family:

- `hummbl_basen_aligned_codex_split_2ep.pt`
  - `val_bpb = 0.388315`
  - `avg_keyword_hit_rate = 0.2750`
  - projected `avg_rubric_field_f1 = 0.0`
- `hummbl_basen_aligned_codex_split_3ep.pt`
  - `val_bpb = 0.397973`
  - `avg_keyword_hit_rate = 0.2917`
  - projected `avg_rubric_field_f1 = 0.0`
- `hummbl_basen_aligned_codex_normtrim_2ep.pt`
  - `val_bpb = 0.388272`
  - `avg_keyword_hit_rate = 0.3875`
  - projected `avg_rubric_field_f1 = 0.1000`

So the normalized/trimmed leader remains the strongest overall rubric checkpoint even under the
stricter projected-field view.

## Current Read

The frontier has now crossed a meaningful threshold:

- from pure keyword recall
- to first recoverable canonical field emission

That is still early and decode-assisted, but it is a better proof step than raw keyword hits alone.

## Next Moves

1. improve projection for key recovery, not just value recovery
2. patch the rubric holdout builder so every expected row is canonically populated at write time
3. move projected field F1 from “one rescued field” to multi-field matches without giving back too
   much retention
