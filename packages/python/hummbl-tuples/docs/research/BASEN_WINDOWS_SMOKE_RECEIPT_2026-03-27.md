# BaseN Windows Smoke Receipt 2026-03-27

Status: first end-to-end Windows training smoke after Codex takeover patch  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Patch Surface

Patched files:

- `basen_corpus_utils.py`
- `hummbl_sft.py`
- `hummbl_basen_sft.py`
- `hummbl_sft_dataset.py`

Key changes:

- repaired broken Windows `.venv`
- added validator-gated corpus handling
- switched both trainers to response-only masking
- preserved `history`, `task`, `protocol`, and `target_step_type` in prompts
- filtered rubric training rows to `VALIDATED` traces only

## Pre-Smoke Checks

Verified in the repaired Windows environment:

- `py_compile` passed on all patched files
- concise dataset rebuild reported:
  - `{'VALIDATED': 36, 'QUARANTINED': 0, 'REJECTED': 0}`
- rubric validator gate reported:
  - `{'QUARANTINED': 180, 'VALIDATED': 89}`

## Smoke Runs

Runner:

- `smoke_alignment.py`

### 1. Concise SFT lane

Observed result:

- samples: `180`
- losses:
  - `9.1988`
  - `9.0166`
  - `8.5804`
  - `8.4491`
  - `8.5366`
- average supervised tokens: `130.4`

Interpretation:

- path-conditioned concise samples load correctly
- response-only masking is active
- optimizer steps run end to end without environment failure

### 2. BaseN rubric lane

Observed result:

- samples: `356`
- status counts:
  - `VALIDATED`: `89`
  - `QUARANTINED`: `180`
- losses:
  - `9.1479`
  - `8.6283`
  - `8.6277`
  - `7.8853`
  - `7.6028`
- average supervised tokens: `112.2`

Interpretation:

- validator gate is active in the rubric lane
- only validated traces are converted into training samples
- the patched BaseN trainer now runs end to end in the real Windows environment

## Immediate Conclusion

This is the first concrete proof step beyond documentation:

- BaseN corpus validation is executable
- response-only masking is live
- path-conditioned inputs are live
- both concise and rubric lanes now complete real optimizer-step smoke runs remotely on Windows

## Remaining Gaps

- no post-alignment eval packet yet
- no forgetting check yet
- rubric corpus still needs cleanup, not just gating
- this receipt proves training viability, not downstream improvement
