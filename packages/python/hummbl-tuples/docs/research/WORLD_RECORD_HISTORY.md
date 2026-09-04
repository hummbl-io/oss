# World Record History

> **ARCHIVED 2026-07-04**: `autoresearch-win-rtx` is now marked **historical-only**.
> The active benchmark authority is `autoresearch-pipeline`. The data below is
> preserved for historical reference. See [issue #75](https://github.com/hummbl-dev/hummbl-tuples/issues/75).

This file tracks the historical progression of HUMMBL's TinyStories BPB candidates across both:

- the historical benchmark repo (archived): `<local-path>/autoresearch-win-rtx`
- the derivative scratch workspace: `<local-path>/autoresearch-yolo`

## Benchmark Scope

Current working scope:

- dataset: `TinyStories`
- metric: `validation BPB`
- status: local tracked results plus partial raw-log receipts, external public leaderboard not yet established

## Evidence Levels

- `canonical recorded`: present in the tracked benchmark repo and/or commit history
- `raw-log-verified`: backed by a preserved raw footer receipt
- `scratch-workspace`: backed by the YOLO derivative workspace rather than the canonical repo

## Verified HUMMBL History

| Order | Run | Category | val_bpb | Budget (s) | Params (M) | Depth | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `run_600s_20260320_102106.log` | canonical archived `best_600s` | 0.425410 | 600 | 33.4 | 6 | raw-log-verified, canonical repo |
| 2 | `run_1200s_20260320_103233.log` | canonical archived `best_1200s` | 0.398497 | 1200 | 33.4 | 6 | raw-log-verified, canonical repo |
| 3 | `run_2400s_20260320_105925.log` | canonical archived `best_2400s` | 0.377572 | 2400 | 33.4 | 6 | canonical repo row with archived TSV support |
| 4 | `run_3600s_20260320_114613.log` | canonical archived `best_3600s` | 0.368805 | 3600 | 33.4 | 6 | raw-log-verified, canonical repo |
| 5 | `3600s_clean` | current canonical recorded best | 0.366786 | 3600 | 33.4 | 6 | canonical recorded, raw log still missing |
| 6 | `wra_1_record_breaker.log` | scratch-workspace `best_3600s` | 0.372437 | 3601 | 33.4 | 6 | raw-log-verified, later beaten by canonical repo |

## Reconciliation Queue

These runs exist, but should not be promoted without clarification:

| Run | Issue |
| --- | --- |
| `3600s_clean` | tracked in `results.tsv` and commit `7c59a10`, but raw preserved log not yet found |
| `hf_mix_3600s` | tracked in `results.tsv` and commit `8e8510a`, but raw preserved log not yet found |
| `pretrain_67M_1800s_final.log` | filename says `67M`, footer says `191.9M` |

## Reporting Drift Notes

Current Windows docs and earlier local summaries lag the broader canonical repo evidence:

- the earlier local ledger focused on the YOLO scratch workspace and missed the canonical repo’s `0.366786` recorded best and `0.368805` archived raw-log best
- [ASCENSION_FINAL_REPORT.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/ASCENSION_FINAL_REPORT.md) cites `0.373112`, which is now behind both the canonical archived 3600s receipt (`0.368805`) and the canonical recorded best (`0.366786`)
- [MESH_SITREP_2026-03-27.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/MESH_SITREP_2026-03-27.md) cites `0.434891`, which is behind the canonical archived 600s receipt (`0.425410`)

## Usage

Use this file for:

- narrative milestone updates
- public-claim draft hygiene
- checking whether a doc headline has gone stale

Use [TRAINING_RUN_LEDGER.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/TRAINING_RUN_LEDGER.md) for the more complete ranked receipt table.
