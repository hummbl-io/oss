# Nodezero Involvement 2026-03-27

This note records how `nodezero` was involved in the March 27, 2026 autoresearch work.

## Executive Summary

`nodezero` was not the main benchmark runner today.

Its primary role was:

- reasoning-trace generation
- rubric-oriented trace generation aligned to `wickedness`, `readiness`, and `BKI`
- attempted rephrase-style data augmentation
- upstream corpus production for Windows-side alignment runs

The benchmark frontier remained Windows-led.

## Primary Surfaces

| Surface | Path | Role |
| --- | --- | --- |
| Trace/data-generation workspace | `~/autoresearch-worker` | Main active same-day work surface on `nodezero` |
| MLX benchmark repo | `~/autoresearch-mlx` | Apple Silicon benchmark port; present but not the main same-day activity |
| Reports repo | `~/autoresearch-reports` | Reporting/depot surface; no meaningful same-day activity observed |

## What Was Active

Same-day activity on `nodezero` was concentrated in `~/autoresearch-worker`.

Observed active files/processes included:

- `nodezero_trace_generator.py`
- `nodezero_trace_generator_v2_rubric.py`
- `nodezero_trace_generator_concise.py`
- `nodezero_hummbl_traces_v2.jsonl`
- `nodezero_hummbl_traces_v2_rubric.jsonl`
- `nodezero_hummbl_traces_concise.jsonl`
- `rephrase.py`
- `rephrase.log`
- local `ollama serve`
- `~/autoresearch-mlx/analyze_pipeline.py --watch --mode dialectic --interval 120`

## Live Health Snapshot

At the time of review:

- `nodezero_hummbl_traces_v2.jsonl` was still growing
- `nodezero_hummbl_traces_v2_rubric.jsonl` was still growing
- `nodezero_hummbl_traces_concise.jsonl` was not moving
- two `rephrase.py --target-tokens 100000000` processes were alive
- `rephrase.log` showed very poor throughput, roughly `2 tok/s`, with an effectively unusable ETA

Operationally:

- `trace generation`: healthy
- `rubric trace generation`: healthy
- `concise trace lane`: idle
- `rephrase augmentation`: running but not practically viable

## Cross-Machine Role

The Windows YOLO workspace contains exact-copy generator scripts from `nodezero`:

- `nodezero_trace_generator.py`
- `nodezero_trace_generator_v2_rubric.py`
- `nodezero_trace_generator_concise.py`

The Windows-side trace corpora are smaller snapshots than the current `nodezero` files:

| Artifact | Windows snapshot | Nodezero live copy |
| --- | ---: | ---: |
| `nodezero_hummbl_traces_v2.jsonl` | `781,939` bytes | `6,589,797` bytes |
| `nodezero_hummbl_traces_v2_rubric.jsonl` | `223,284` bytes | `527,236` bytes |
| `nodezero_hummbl_traces_concise.jsonl` | `24,987` bytes | `52,573` bytes |

This supports the workflow:

1. generate on `nodezero`
2. snapshot/copy to Windows
3. transform/use on Windows
4. continue generation on `nodezero`

## Windows-Side Consumption

The copied `nodezero` corpora were not just archived.

They were consumed in Windows-side alignment work:

- `deep_alignment.log` reports `Loaded 269 BaseN reasoning samples.`
- `deep_alignment_final.log` saves `hummbl_basen_aligned_67M.pt`
- `sft_alignment_concise_v2.log` reports `Loaded 85 SFT reasoning samples.`
- `hummbl_sft_dataset.py` transforms `nodezero_hummbl_traces_concise.jsonl` into refined SFT data

This means `nodezero` acted as an upstream data-generation node for the alignment lane.

## What Nodezero Was Not Doing

`nodezero` was not the primary benchmark authority today.

It was not:

- advancing the canonical Windows benchmark frontier directly
- serving as the authoritative TinyStories ledger
- materially updating `autoresearch-reports`

That work remained centered on Windows, especially `C:\Users\Owner\autoresearch-win-rtx` (now archived — see [issue #75](https://github.com/hummbl-dev/hummbl-tuples/issues/75); active authority is `autoresearch-pipeline`).

## Practical Interpretation

For March 27, 2026 the clean division of labor was:

- Windows desktop:
  - benchmark frontier
  - canonical run ledger
  - alignment execution over copied corpora
- `nodezero`:
  - reasoning-trace factory
  - rubric-trace factory
  - attempted augmentation lane

## Review Rule

When evaluating same-day autoresearch work:

1. treat Windows benchmark claims as benchmark authority
2. treat `nodezero` as an upstream corpus and trace-generation authority
3. do not assume the rephrase lane is healthy just because the processes are alive
