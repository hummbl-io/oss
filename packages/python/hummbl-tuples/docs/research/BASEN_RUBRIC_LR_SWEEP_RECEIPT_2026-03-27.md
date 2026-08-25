# BaseN Rubric LR Sweep Receipt 2026-03-27

Status: first small LR bracket on the disciplined rubric/BaseN lane  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Fixed Setup

Shared across all runs:

- validated rubric traces only
- deterministic split:
  - `81` train traces
  - `8` holdout cases
- `SFT_EPOCHS = 2`
- anchored decoding for evaluation:
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`

Metrics tracked:

- `val_bpb`
- rubric holdout teacher-forced next-step loss
- free-generation keyword-hit rate
- `starts_with_target`

## Results

### `lr = 2e-5`

- checkpoint: `hummbl_basen_aligned_codex_lr2e5_2ep.pt`
- `val_bpb = 0.376082`
- `avg_teacher_forced_loss = 3.7908`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.1417`

Interpretation:

- strongest retention in the sweep
- weakest structure-learning signal of the three

### `lr = 5e-5`

- checkpoint: `hummbl_basen_aligned_codex_split_2ep.pt`
- `val_bpb = 0.394554`
- `avg_teacher_forced_loss = 2.5600`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.2750`

Interpretation:

- best overall tradeoff in the sweep
- best free-generation rubric record so far

### `lr = 1e-4`

- checkpoint: `hummbl_basen_aligned_codex_lr1e4_2ep.pt`
- `val_bpb = 0.415355`
- `avg_teacher_forced_loss = 2.1256`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.2292`

Interpretation:

- best teacher-forced loss in the sweep
- but retention degrades too far
- free-generation quality does not beat the `5e-5` point

## Current Record Table

Best rubric free-generation record:

- checkpoint: `hummbl_basen_aligned_codex_split_2ep.pt`
- `lr = 5e-5`
- `epochs = 2`
- anchored decode with repetition penalty `1.30`
- `starts_with_target = 8/8`
- `avg_keyword_hit_rate = 0.2750`

Best rubric teacher-forced fit:

- checkpoint: `hummbl_basen_aligned_codex_lr1e4_2ep.pt`
- `avg_teacher_forced_loss = 2.1256`

Best rubric retention:

- checkpoint: `hummbl_basen_aligned_codex_lr2e5_2ep.pt`
- `val_bpb = 0.376082`

## Conclusion

The LR sweep makes the tradeoff explicit:

- `2e-5` preserves the base model best
- `1e-4` learns the rubric targets best under teacher forcing
- `5e-5` is the current record-setting balance point

That means the current best rubric checkpoint remains:

- `hummbl_basen_aligned_codex_split_2ep.pt`

under anchored decoding with:

- `--force-prefix target_step`
- `--repetition-penalty 1.30`
