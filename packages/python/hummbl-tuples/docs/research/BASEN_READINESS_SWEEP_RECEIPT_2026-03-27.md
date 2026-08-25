# BaseN Readiness Sweep Receipt 2026-03-27

Status: initialization and epoch sweep for the readiness-only clean lane  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Goal

After the first readiness-only clean checkpoint became the strict-v2 leader, the next question was:

- is the gain coming from the clean readiness subset itself,
- or from the fact that it starts from the stronger rubric leader?

This sweep compared:

- `leader-init` vs `base-init`
- `1` epoch vs `2` epochs

All comparisons use the same strict-v2 constrained probe:

- `candidate_plus_core`

## Compared Variants

### `leader_1ep`

- init: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- epochs: `1`
- output: `hummbl_basen_readiness_clean_1ep.pt`

Result:

- `val_bpb = 0.388941`
- `avg_teacher_forced_loss = 2.4635`
- strict-v2 probe:
  - field F1 `0.2589`
  - key F1 `0.4866`
  - value F1 `0.6875`

### `leader_2ep`

- init: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- epochs: `2`
- output: `hummbl_basen_readiness_clean_2epb.pt`

Result:

- `val_bpb = 0.390224`
- `avg_teacher_forced_loss = 2.3910`
- strict-v2 probe:
  - field F1 `0.2589`
  - key F1 `0.4866`
  - value F1 `0.6875`

### `base_1ep`

- init: `checkpoint_pre_eval.pt`
- epochs: `1`
- output: `hummbl_basen_readiness_base_1ep.pt`

Result:

- `val_bpb = 0.361898`
- `avg_teacher_forced_loss = 5.8682`
- strict-v2 probe:
  - field F1 `0.1250`
  - key F1 `0.1250`
  - value F1 `0.4583`

### `base_2ep`

- init: `checkpoint_pre_eval.pt`
- epochs: `2`
- output: `hummbl_basen_readiness_base_2ep.pt`

Result:

- `val_bpb = 0.362329`
- `avg_teacher_forced_loss = 5.3719`
- strict-v2 probe:
  - field F1 `0.1625`
  - key F1 `0.2625`
  - value F1 `0.5417`

## Current Read

The answer is clear:

1. start-from-leader matters
   - `leader-init` substantially outperforms `base-init` on strict-v2 structured recovery

2. the main readiness gain is not coming from more epochs
   - `leader_1ep` and `leader_2ep` tie on field/key metrics
   - `2` epochs only improves teacher-forced loss slightly

3. the strict-v2 frontier is still dominated by probe strategy
   - `candidate_plus_core` is doing more work than extra small-lane training epochs

## Practical Conclusion

Use this as the current readiness default:

- init from the rubric leader
- keep the readiness clean fine-tune short
- invest effort into better key discovery and value probing before longer training sweeps

## Best Current Preference

Preferred checkpoint family:

- `leader-init`

Preferred duration:

- `1` epoch is sufficient unless a later metric justifies `2`

Reason:

- it matches the current strict-v2 field/key frontier
- while spending slightly less retention budget than the longer version
