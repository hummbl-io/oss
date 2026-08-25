# BaseN Longer-Running Harnesses 2026-03-27

## Active Windows Harnesses

### READINESS key-prior overnight harness
- script: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\basen_readiness_overnight.py`
- purpose: sweep strict-v2 `READINESS` key-prior settings across frontier checkpoints and emit one summary JSON/TSV
- current default matrix:
  - checkpoints:
    - `hummbl_basen_readiness_clean_2ep.pt`
    - `hummbl_basen_readiness_clean_1ep.pt`
    - `hummbl_basen_aligned_codex_normtrim_2ep.pt`
  - probe mode: `candidate_plus_core`
  - prior modes:
    - `none`
    - `task`
    - `history`
    - `task_history`
  - `max_fields`: `2`, `3`
  - `min_combined_score`: `0.85`, `0.95`
- outputs:
  - `basen_readiness_overnight_full.json`
  - `basen_readiness_overnight_full.tsv`

### Supporting strict-v2 harnesses
- `basen_eval_packet.py`
  - fixed holdout eval packet writer with BPB and reasoning outputs
- `basen_readiness_probe_eval.py`
  - constrained key/value probe evaluator
  - now supports prior modes: `none`, `task`, `history`, `task_history`
- `prepare_basen_readiness_clean.py`
  - clean `READINESS` micro-corpus builder
- `hummbl_readiness_sft.py`
  - readiness-specific fine-tune surface with env overrides

## Active Nodezero Harnesses
- `~/autoresearch-worker/nodezero_trace_generator_v3.py`
- `~/autoresearch-worker/nodezero_trace_generator_v2_rubric_v3.py`

These remain the productive long-running generation lanes.
`rephrase.py` stays off until the trace lanes are stable enough and the economics materially improve.

## Current Use
The best current overnight target is still `READINESS` key discovery, not more epoch sweeps.
