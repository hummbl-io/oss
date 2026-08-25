# Training Run Ledger

> **ARCHIVED 2026-07-04**: `autoresearch-win-rtx` is now marked **historical-only**.
> The active benchmark authority has moved to `autoresearch-pipeline`
> (`hummbl-dev/autoresearch-pipeline`). The benchmark data below is preserved
> for historical reference. New training run records should be tracked in the
> pipeline repo. See [issue #75](https://github.com/hummbl-dev/hummbl-tuples/issues/75).

Training run ledger assembled from Windows receipts on 2026-03-27.

This file now distinguishes between:

- `canonical recorded best`: best result recorded in the tracked benchmark repo (historical)
- `raw-log-verified best`: best result backed by a preserved raw log footer
- `scratch-workspace best`: best result found in the derivative YOLO workspace

The historical benchmark surface is `C:\Users\Owner\autoresearch-win-rtx` (archived).
The active benchmark authority is `C:\Users\Owner\autoresearch-pipeline`.
The derivative scratch workspace is `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`.

## Scoring Rules

- `canonical_recorded_best`: lowest `val_bpb` recorded in the tracked repo, even if the raw log has not yet been recovered
- `raw_log_verified_best`: lowest `val_bpb` backed by a preserved raw log footer
- `best_600s`: lowest verified `val_bpb` among runs with ~600 second budgets
- `best_3600s`: lowest verified `val_bpb` among runs with ~3600 second budgets
- `best_family`: best result within the same model family, defined here as `33.4M params / depth=6 / TinyStories`
- `needs_reconciliation`: file naming or narrative claim does not match the run footer cleanly

## Canonical Benchmark Hierarchy

| Rank | Surface | Run | val_bpb | Budget (s) | Evidence level | Notes |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `autoresearch-win-rtx` (archived) | `3600s_clean` | 0.366786 | 3600 | canonical recorded best (historical) | Present in tracked `results.tsv` and commit `7c59a10`, raw log not yet recovered |
| 2 | `autoresearch-win-rtx` (archived) | `run_3600s_20260320_114613.log` | 0.368805 | 3600 | raw-log-verified best (historical) | Preserved archived 3600s longer-budget receipt |
| 3 | `autoresearch-yolo` | `wra_1_record_breaker.log` | 0.372437 | 3601 | raw-log-verified, scratch workspace | Best run found in derivative YOLO workspace |

## Ranked Raw-Log-Verified Runs

| Rank | Run | val_bpb | Budget (s) | Params (M) | Depth | MFU % | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `run_3600s_20260320_114613.log` | 0.368805 | 3600 | 33.4 | 6 | 14.59 | Current `raw_log_verified_best`, canonical archived longer-budget receipt |
| 2 | `wra_1_record_breaker.log` | 0.372437 | 3601 | 33.4 | 6 | 24.96 | Current `scratch-workspace best`, `best_family` in YOLO workspace |
| 3 | `ascension_final_forge.log` | 0.373112 | 3600 | 33.4 | 6 | 24.87 | Prior documented headline in Windows report |
| 4 | `run_2400s_20260320_105925.log` | 0.377572 | 2400 | 33.4 | 6 | n/a | Canonical archived 2400s longer-budget receipt |
| 5 | `batch_ramp_600s_retry.log` | 0.432362 | 602 | 33.4 | 6 | n/a | Current `best_600s` in the YOLO workspace |
| 6 | `run_600s_20260320_102106.log` | 0.425410 | 600 | 33.4 | 6 | 15.08 | Canonical archived 600s longer-budget receipt |
| 7 | `pretrain_1200s.log` | 0.434510 | 600 | 33.4 | 6 | 24.83 | Same family as top YOLO runs |
| 8 | `regen_fixed.log` | 0.434891 | 601 | 33.4 | 6 | 24.81 | Metric in `MESH_SITREP_2026-03-27.md` and `BREAKTHROUGH_0.434.md` |
| 9 | `pretrain_67M_1800s_final.log` | 0.457587 | 1800 | 191.9 | 12 | 19.37 | `needs_reconciliation`: filename says `67M`, footer says `191.9M` |
| 10 | `wd_0_1.log` | 0.524536 | 180 | 33.4 | 6 | n/a | Best short hyperparameter sweep receipt found in YOLO workspace |

## Additional Verified Receipts

| Run | val_bpb | Budget (s) | Params (M) | Depth |
| --- | ---: | ---: | ---: | ---: |
| `lr_0_075.log` | 0.531386 | 180 | 33.4 | 6 |
| `lr_0_15.log` | 0.533559 | 181 | 33.4 | 6 |
| `wd_0_5.log` | 0.533808 | 181 | 33.4 | 6 |
| `lr_0_05.log` | 0.547771 | 181 | 33.4 | 6 |
| `depth_8.log` | 0.565297 | 181 | 67.1 | 8 |
| `wd_1_0.log` | 0.568618 | 181 | 33.4 | 6 |
| `curriculum_3stage.log` | 0.579316 | 181 | 33.4 | 6 |
| `lr_0_2.log` | 0.590182 | 181 | 33.4 | 6 |
| `mtp_ramp_600s_final_v2.log` | 0.817246 | 602 | 33.4 | 6 |
| `regen_checkpoint.log` | 0.817451 | 601 | 33.4 | 6 |

## Interpretation

- If `best` means tracked canonical benchmark result (historical), `3600s_clean` at `0.366786` is the historical leader in `autoresearch-win-rtx` (archived). Check `autoresearch-pipeline` for current active results.
- If `best` means preserved raw-log receipt in the canonical repo, `run_3600s_20260320_114613.log` at `0.368805` is the current leader.
- If `best` means preserved raw-log receipt in the scratch YOLO workspace, `wra_1_record_breaker.log` at `0.372437` is the current leader there.
- If `best` means best verified 600-second run, the canonical repo archived `run_600s_20260320_102106.log` at `0.425410`, which is stronger than the later YOLO scratch 600s best at `0.432362`.
- The Windows narrative docs and the earlier local ledger both lag the broader canonical repo evidence surface.

## Review Notes

- `autoresearch-win-rtx` is the tracked fork of `karpathy/autoresearch` — **archived as of 2026-07-04**. Historical benchmark data is preserved, but new benchmark claims should be tracked in `autoresearch-pipeline`.
- `autoresearch-yolo` is a derivative scratch workspace with useful receipts, but it is not the canonical tracked surface.
- `run-1774627079` is documented at the markdown layer, but the raw log receipt I found is `regen_fixed.log`. The metric is supported; the run identifier still needs direct raw-source linkage.
- `pretrain_67M_1800s_final.log` should not be treated as a clean `67M` claim until the filename/footer mismatch is resolved.
- The archived longer-budget logs are preserved for the March 20 scaling ladder, but the raw log for `3600s_clean = 0.366786` has not yet been recovered.
- `hf_mix` has more than one result family in the canonical repo:
  - baseline/frontier rows in `results.tsv`
  - later sweep rows in `sweep_hfmix_results.tsv`
