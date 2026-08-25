# Autoresearch Run Receipt Template

Use this template immediately after a run finishes.

```md
# Run Receipt

## Identity

- run_name:
- run_category:
- authoritative_surface:
- repo_path:
- branch:
- commit:
- dirty_state:

## Benchmark Context

- dataset:
- tokenizer:
- benchmark_class:
- baseline_to_beat:
- frontier_to_beat:

## Hardware Context

- machine:
- gpu:
- vram_gb:
- background_load:
- thermal_notes:

## Footer Metrics

- val_bpb:
- training_seconds:
- total_seconds:
- peak_vram_mb:
- mfu_percent:
- total_tokens_M:
- num_steps:
- num_params_M:
- depth:
- train_batch_size:
- eval_batch_size:
- activation_checkpointing:
- time_budget_s:

## Artifact Paths

- raw_log:
- json_sidecar:
- scoreboard_row_location:
- related_note:

## Result Classification

- status:
- evidence_level:
- promoted_claim_category:

## Short Interpretation

- what_changed:
- why_it_might_have_helped:
- confounders:
- follow_up:
```

## Recommended Values

For `evidence_level`, use one of:

- `canonical_recorded`
- `raw_log_verified`
- `scratch_workspace_verified`
- `needs_reconciliation`

For `promoted_claim_category`, use one of:

- `best_300s`
- `best_600s`
- `best_1200s`
- `best_1800s`
- `best_3600s`
- `best_hf_mix`
- `best_absolute`
- `none`
