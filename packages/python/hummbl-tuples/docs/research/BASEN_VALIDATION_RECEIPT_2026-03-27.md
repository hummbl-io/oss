# BaseN Validation Receipt 2026-03-27

Status: first executable validator receipt  
Scope: March 27 Windows BaseN corpora

Validator:

- `reference_impl/validate_basen_corpus.py`

## Corpora Checked

### 1. Rubric corpus

Source snapshot:

- `<local-path>`

Observed result:

- total rows: `269`
- `VALIDATED`: `89`
- `QUARANTINED`: `180`

Error counts:

- `PROTOCOL_LEAKAGE`: `134`

Warning counts:

- `DUPLICATE_STEP_CONTENT`: `127`
- `RUBRIC_TOO_VERBOSE`: `11`

Interpretation:

- the rubric corpus is not training-safe as-is
- protocol-family leakage is the dominant failure mode

### 2. Concise corpus

Source snapshot:

- `<local-path>`

Observed result:

- total rows: `36`
- `VALIDATED`: `36`
- `QUARANTINED`: `0`
- `REJECTED`: `0`

Interpretation:

- the concise corpus appears structurally clean under the first validator pass

## Immediate Conclusion

The validator confirms the peer-review intuition:

- `nodezero_hummbl_traces_v2_rubric.jsonl` needs quarantine/cleanup before BaseN alignment
- `nodezero_hummbl_traces_concise.jsonl` is the safer immediate supervision surface
