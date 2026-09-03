# BaseN Frontier Leaderboard 2026-03-27

Status: canonical frontier snapshot for the current BaseN proof loop  
Scope: Windows experiments in `<local-path>/autoresearch-yolo`

This document compresses the current best-known BaseN checkpoints into one scoreboard.
It is intentionally selective.
Use the receipt docs for full run detail.

## Baselines

### Base checkpoint

- checkpoint: `checkpoint_pre_eval.pt`
- short packet `val_bpb = 0.365424`
- concise holdout teacher-forced loss: `7.1393`
- rubric holdout teacher-forced loss: `5.9876`

### Old aligned artifact

- checkpoint: `hummbl_aligned_model.pt`
- short packet `val_bpb = 0.476674`
- concise holdout teacher-forced loss: `5.6513`

Interpretation:

- learned target responses somewhat
- damaged retention too much to be the right frontier anchor

## Current Frontier

### Best concise balance point

- checkpoint: `hummbl_aligned_model_codex_split.pt`
- lane: concise
- training:
  - `lr = 5e-5`
  - `epochs = 1`
  - split-respecting train/holdout
- results:
  - `val_bpb = 0.369635`
  - concise holdout teacher-forced loss: `5.8539`

Why it matters:

- best concise tradeoff between retention and target-fit
- materially better disciplined baseline than the old aligned artifact

### Best rubric balance point

- checkpoint: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- lane: rubric / BaseN
- eval surface:
  - pre-rebuild rubric holdout v1
- training:
  - `lr = 5e-5`
  - `epochs = 2`
  - validated-only rubric traces
  - deterministic split (`81` train traces / `8` holdout cases)
  - schema-normalized and target-step-trimmed rubric targets
- anchored decoding:
  - `--force-prefix target_step_colon`
  - `--repetition-penalty 1.30`
- results:
  - `val_bpb = 0.388272`
  - rubric holdout teacher-forced loss: `2.8027`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3875`
  - raw `avg_rubric_field_f1 = 0.0`
  - projected `avg_rubric_field_f1 = 0.1000`

Why it matters:

- strongest overall BaseN balance point so far
- best current free-generation record at essentially the same retention budget as the earlier 2-epoch rubric point
- schema normalization plus colon anchoring clearly improved section-conditioned recall
- decode-time schema projection now yields the first nonzero rubric field-level score

### Best rubric free-generation record

- checkpoint: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- lane: rubric / BaseN
- eval surface:
  - pre-rebuild rubric holdout v1
- training:
  - `lr = 5e-5`
  - `epochs = 2`
  - schema-normalized and target-step-trimmed rubric targets
- anchored decoding:
  - `--force-prefix target_step_colon`
  - `--repetition-penalty 1.30`
- results:
  - `val_bpb = 0.388272`
  - rubric holdout teacher-forced loss: `2.8027`
  - `starts_with_target = 8/8`
  - `avg_keyword_hit_rate = 0.3875`
  - raw `avg_rubric_field_f1 = 0.0`
  - projected `avg_rubric_field_f1 = 0.1000`

Why it matters:

- current best rubric free-generation metric
- currently beats every prior rubric decode on keyword-hit rate
- now clears the field-level F1 barrier under explicit schema projection

### Best rubric retention point

- checkpoint: `hummbl_basen_aligned_codex_lr2e5_2ep.pt`
- lane: rubric / BaseN
- training:
  - `lr = 2e-5`
  - `epochs = 2`
- anchored decoding:
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`
- results:
  - `val_bpb = 0.376082`
  - rubric holdout teacher-forced loss: `3.7908`
  - `avg_keyword_hit_rate = 0.1417`

Why it matters:

- best rubric retention in the disciplined sweep
- useful lower-bound anchor on the tradeoff curve

### Best rubric teacher-forced fit

- checkpoint: `hummbl_basen_aligned_codex_lr1e4_2ep.pt`
- lane: rubric / BaseN
- training:
  - `lr = 1e-4`
  - `epochs = 2`
- anchored decoding:
  - `--force-prefix target_step`
  - `--repetition-penalty 1.30`
- results:
  - `val_bpb = 0.415355`
  - rubric holdout teacher-forced loss: `2.1256`
  - `avg_keyword_hit_rate = 0.2292`

Why it matters:

- best rubric target-fit under teacher forcing
- too expensive in retention to be the default frontier anchor

## Current Read

The frontier is now split cleanly:

- concise lane:
  - best for disciplined retention-sensitive alignment
- rubric lane:
  - best for BaseN-specific structure learning

And the rubric lane itself is now centered on one clear leader:

- **balance-point and free-generation champion**:
  - `hummbl_basen_aligned_codex_normtrim_2ep.pt`

Older split-only checkpoints still matter as comparison points, but they are no longer the frontier.

There is also a stricter rebuilt rubric holdout v2 now.
On that surface, the same checkpoint currently loses the anchored projected-field gain.
So v2 should be treated as an unresolved stricter eval lane, not silently merged into the frontier.

### Best strict-v2 structured decode

- checkpoint: `basen_readiness_marathon_cycle1_hummbl_basen_readiness_clean_2ep_lr5e-05_ep3.pt`
- lane: rubric / BaseN
- eval surface:
  - rebuilt rubric holdout v2
- method:
  - timed marathon candidate from small clean readiness-only fine-tuning
  - init checkpoint: `hummbl_basen_readiness_clean_2ep.pt`
  - `lr = 5e-5`
  - `epochs = 3`
  - anchored packet for candidate-key mining
  - constrained key-by-key `READINESS` value probing
  - `candidate_plus_core` probe mode
  - canonical field reassembly
- results:
  - `val_bpb = 0.396647`
  - `avg_keyword_hit_rate = 0.4208`
  - `avg_teacher_forced_loss = 2.3015`
  - `avg_field_f1 = 0.4500`
  - `avg_key_f1 = 0.4917`
  - `avg_value_f1 = 0.7292`
  - `cases_with_projected_fields = 8/8`

Why it matters:

- this is the strongest strict-v2 result so far
- it shows the model knows substantially more value structure than whole-section decoding reveals
- it materially improves constrained strict-v2 recovery beyond the earlier readiness-clean leader
- it is the cleanest next proving surface for BaseN under stricter evaluation
- leader-initialized readiness fine-tunes dominate base-initialized variants on this surface
- the caveat is procedural, not metric:
  - the candidate came from a timed marathon harness that did not yet demonstrably complete the full intended six-hour wall-clock run
  - so the checkpoint result is valid, while the marathon budget claim remains incomplete
- the longer-running prior sweep did not beat this leader
  - overnight best:
    - `hummbl_basen_aligned_codex_normtrim_2ep.pt`
    - `avg_field_f1 = 0.2500`
    - `avg_key_f1 = 0.3750`
    - `avg_value_f1 = 0.6875`
  - so the standing strict-v2 leader remains unchanged

## Suggested Default References

If another agent needs one checkpoint per purpose, use:

- safe concise baseline:
  - `hummbl_aligned_model_codex_split.pt`
- best overall BaseN balance point:
  - `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- current free-generation record:
  - `hummbl_basen_aligned_codex_normtrim_2ep.pt`

## Source Receipts

- [BASEN_CONCISE_SWEEP_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_CONCISE_SWEEP_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_SPLIT_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_SPLIT_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_DECODING_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_DECODING_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_SCHEMA_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_SCHEMA_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_LR_SWEEP_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_LR_SWEEP_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_DURATION_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_DURATION_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_PROJECTION_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_PROJECTION_RECEIPT_2026-03-27.md)
- [BASEN_RUBRIC_HOLDOUT_V2_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_RUBRIC_HOLDOUT_V2_RECEIPT_2026-03-27.md)
- [BASEN_READINESS_PROBE_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_READINESS_PROBE_RECEIPT_2026-03-27.md)
- [BASEN_READINESS_CLEAN_TRAINING_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_READINESS_CLEAN_TRAINING_RECEIPT_2026-03-27.md)
- [BASEN_READINESS_SWEEP_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_READINESS_SWEEP_RECEIPT_2026-03-27.md)
- [BASEN_READINESS_OVERNIGHT_RECEIPT_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_READINESS_OVERNIGHT_RECEIPT_2026-03-27.md)
- [BASEN_READINESS_MARATHON_RECEIPT_2026-03-28.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BASEN_READINESS_MARATHON_RECEIPT_2026-03-28.md)
