# BaseN Windows Delta Plan

Status: draft  
Scope: exact code-level changes needed in the March 27 Windows BaseN alignment stack

Primary Windows targets:

- `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\hummbl_basen_sft.py`
- `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\hummbl_sft.py`
- `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\hummbl_sft_dataset.py`

## 1. Delta 1: Add corpus validation gate

Before loading samples:

- run a BaseN validator over the input trace file
- reject or quarantine bad rows
- train only on `VALIDATED` rows

Minimum behavior:

- if no validated rows remain, abort
- print counts:
  - validated
  - quarantined
  - rejected

## 2. Delta 2: Train on response spans only

Current behavior:

- model predicts over the whole prompt + response sequence

Required change:

- build `x` over full sequence
- build `y` as `-1` for prompt/context tokens
- populate `y` only for the target response span

This applies to:

- `hummbl_basen_sft.py`
- `hummbl_sft.py`

## 3. Delta 3: Preserve path context in training input

Current behavior:

- `history`, `task`, and `protocol` are constructed in the dataset builder
- the trainer discards most of them

Required change:

- serialize `history`
- include explicit `task`
- include explicit `protocol`
- include current `target_step_type`

The training input should represent:

- current task
- prior validated path state
- exact next step to predict

## 4. Delta 4: Separate training families

Do not train rubric traces and protocol traces through the exact same path without declaring the family.

Minimum required split:

- `RUBRIC_TRACE`
- `PROTOCOL_TRACE`

Future split:

- `PATH_EVAL`
- `NEGATIVE_TRACE`

## 5. Delta 5: Fix provenance naming

Current issue:

- file and comments say `67M`
- config points to a `DEPTH = 6` lineage associated with the `33M` family

Required change:

- either rename artifacts to the real family
- or point the script at the true `67M` config/checkpoint

Do not leave ambiguous naming in place.

## 6. Delta 6: Add post-alignment eval packet

Before saving a promoted aligned model:

- run TinyStories BPB eval
- run held-out BaseN prompt eval
- record pre/post comparison
- record forgetting/regression check

Output:

- `*_eval_packet.json`
- `*_eval_summary.md`

## 7. Delta 7: Emit training receipts with corpus details

Every aligned artifact should declare:

- source checkpoint
- source trace file(s)
- validated row count
- quarantined row count
- protocol family
- masking policy
- training steps
- batch size

## 8. Suggested Implementation Order

1. validator gate
2. response masking
3. explicit path-conditioned training input
4. provenance cleanup
5. post-alignment eval packet

## 9. Immediate Win

Even without redesigning the whole stack, the combination of:

- validator gate
- response masking
- post-alignment eval

would make the current BaseN work materially more defensible.
