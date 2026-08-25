# Autoresearch Surface Map

> **ARCHIVED 2026-07-04**: `autoresearch-win-rtx` is now marked **historical-only**.
> The active benchmark authority has moved to `autoresearch-pipeline`
> (`hummbl-dev/autoresearch-pipeline`). The data below is preserved for
> historical reference. New benchmark claims should cite the pipeline repo,
> not `autoresearch-win-rtx`. See [issue #75](https://github.com/hummbl-dev/hummbl-tuples/issues/75).

This note records the Windows-side autoresearch surface split as observed on 2026-03-27.

## Primary Surfaces

| Surface | Path | Role | Authority level |
| --- | --- | --- | --- |
| ~~Canonical benchmark repo~~ | `C:\Users\Owner\autoresearch-win-rtx` | ~~Tracked fork of `karpathy/autoresearch`; benchmark canon, results ledger, long-budget scaling, dataset expansions~~ **ARCHIVED — historical only** | ~~Highest~~ Historical |
| Active benchmark authority | `C:\Users\Owner\autoresearch-pipeline` | Orchestration, supervisor/worker surface, and active benchmark canon | Highest (active) |
| Scratch forge | `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo` | Derivative experimental workspace with additional logs, overnight scripts, and HUMMBL-specific exploratory changes | Secondary |
| Pipeline repo | `C:\Users\Owner\autoresearch-pipeline` | Orchestration and supervisor/worker surface | Active authority |
| Reports repo | `C:\Users\Owner\autoresearch-reports` | Distillation, proposals, and downstream reporting depot | Supporting |
| Upstream trace factory | `nodezero:~/autoresearch-worker` | Local Ollama-driven trace generation, rubric-trace generation, and upstream corpus production for Windows alignment | Supporting |

## Key Distinctions

- `autoresearch-win-rtx` is a **historical** git repo with:
  - `origin = hummbl-dev/autoresearch-win-rtx`
  - `upstream = karpathy/autoresearch`
  - **Status: archived.** Do not use as the live canonical source for new benchmark claims.
- `autoresearch-pipeline` is the **active** benchmark authority:
  - `origin = hummbl-dev/autoresearch-pipeline`
  - New benchmark results, results ledgers, and scaling experiments should be tracked here.
- `autoresearch-yolo` is not the benchmark canon.
  - it has a placeholder local git history only
  - it is best treated as a branchless derivative workspace
- benchmark conclusions should default to `autoresearch-pipeline` unless a scratch-only experiment is being discussed explicitly

## Benchmark Evidence Levels

| Level | Meaning |
| --- | --- |
| `canonical recorded` | Present in the tracked benchmark repo, `results.tsv`, and/or commit history |
| `raw-log-verified` | Backed by a preserved raw training log footer |
| `scratch-workspace verified` | Backed by raw logs in `autoresearch-yolo`, but not canonical unless ported back |

## Current TinyStories Hierarchy

| Category | Value | Source |
| --- | ---: | --- |
| Canonical recorded best (historical) | `0.366786` | `autoresearch-win-rtx/results.tsv` row `3600s_clean` — **archived repo** |
| Canonical raw-log-verified best (historical) | `0.368805` | `autoresearch-win-rtx/results/longer_budget/run_3600s_20260320_114613.log` — **archived repo** |
| Scratch-workspace raw-log-verified best | `0.372437` | `autoresearch-yolo/wra_1_record_breaker.log` |

## Dataset/Approach Notes

- Completed canonical TinyStories scaling receipts exist at:
  - `600s`
  - `1200s`
  - `2400s`
  - `3600s`
- Canonical `hf_mix` results exist in at least two families (historical, in archived `autoresearch-win-rtx`):
  - baseline/frontier rows in `autoresearch-win-rtx/results.tsv`
  - later sweep rows in `autoresearch-win-rtx/sweep_hfmix_results.tsv`
- `autoresearch-yolo` also contains:
  - BaseN alignment logs
  - SFT alignment logs
  - alternate dataset support in code
- `nodezero:~/autoresearch-worker` is the upstream trace-generation lane for the March 27 Windows alignment work.
  - it generated larger live corpora than the Windows snapshots
  - the copied corpora were then transformed into Windows-side SFT/BaseN alignment datasets

## Practical Review Rule

When a Windows-side report claims a benchmark milestone:

1. check `autoresearch-pipeline` for the current active benchmark results
2. check `autoresearch-win-rtx/results.tsv` (historical archive only)
3. check `autoresearch-win-rtx/results/longer_budget/` for preserved receipts (historical archive only)
4. use `autoresearch-yolo` only for derivative experiments or extra logs not yet ported back
