# BaseN Rubric Split Receipt 2026-03-27

Status: first disciplined rubric/BaseN split run on Windows  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Setup

Rubric lane hygiene applied:

- validator gate on `nodezero_hummbl_traces_v2_rubric.jsonl`
- only `VALIDATED` traces included
- deterministic split from validated traces
  - validated traces: `89`
  - train traces: `81`
  - holdout cases: `8`
- patched `hummbl_basen_sft.py`
  - response-only masking
  - finite epoch-based training loop
  - no blind 1000-step pass
- short eval packet using:
  - `val_bpb`
  - rubric holdout free-generation checks
  - rubric holdout teacher-forced next-step loss

## Run

Checkpoint produced:

- `hummbl_basen_aligned_codex_split.pt`

Training config:

- `SFT_EPOCHS = 1`
- `SFT_LR = 5e-5`

Training receipt:

- validation counts: `{'VALIDATED': 81}`
- training samples: `324`
- epoch average loss: `4.6559`

## Evaluation

### Base checkpoint

- checkpoint: `checkpoint_pre_eval.pt`
- holdout: `basen_rubric_eval_holdout.jsonl`
- `val_bpb = 0.365424`
- `avg_teacher_forced_loss = 5.9876`
- free-generation metrics:
  - starts-with-target: `0/8`
  - exact-match: `0/8`
  - keyword-hit rate: `0.0`

### Codex split rubric run

- checkpoint: `hummbl_basen_aligned_codex_split.pt`
- holdout: `basen_rubric_eval_holdout.jsonl`
- `val_bpb = 0.379737`
- `avg_teacher_forced_loss = 3.5694`
- free-generation metrics:
  - starts-with-target: `0/8`
  - exact-match: `0/8`
  - keyword-hit rate: `0.0`

### Codex split rubric run, 2 epochs

- checkpoint: `hummbl_basen_aligned_codex_split_2ep.pt`
- holdout: `basen_rubric_eval_holdout.jsonl`
- `val_bpb = 0.394554`
- `avg_teacher_forced_loss = 2.5600`
- free-generation metrics:
  - starts-with-target: `0/8`
  - exact-match: `0/8`
  - keyword-hit rate: `0.1375`

Qualitative note:

- this is the first rubric run to show any free-generation movement at all
- at least one holdout case now emits the right conceptual fields:
  - `contestation`
  - `uncertainty`
  - `interdependence`
- the generation still collapses afterward, so this is not yet usable output quality

## Interpretation

This is the strongest BaseN signal so far.

What improved:

- rubric holdout teacher-forced next-step loss improved materially:
  - `5.9876 -> 3.5694`
  - then to `2.5600` with a modest duration increase
- free-generation keyword hit rate finally moved above zero at `2` epochs

What it cost:

- BPB degraded from `0.365424` to `0.379737`
- and then to `0.394554` at `2` epochs

Why this matters:

- unlike the old alignment artifact pattern, this gain was achieved under:
  - validated-only traces
  - deterministic train/holdout split
  - response-only masking
  - explicit eval packet

So this is not just “loss went down.”
It is the first disciplined indication that validated BaseN/rubric traces can teach the target structure without catastrophic retention damage.

## Current Conclusion

The rubric/BaseN lane now looks more promising than the free-generation outputs suggest.

Free generation is still poor, but the teacher-forced holdout gain is large enough that the next effort should focus on:

1. improving generation decoding / prompt surface
2. deciding whether `1` or `2` epochs is the better tradeoff point
3. comparing concise and rubric lanes under the same tradeoff criteria

Current read:

- concise lane is cleaner and more retention-friendly
- rubric lane is now the best place to look for true BaseN-specific structure learning
