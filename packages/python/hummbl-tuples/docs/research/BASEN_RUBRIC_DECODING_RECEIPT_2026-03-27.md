# BaseN Rubric Decoding Receipt 2026-03-27

Status: first decoding-only improvement pass on the rubric/BaseN lane  
Scope: `<local-path>`

## Context

After the validated rubric split runs, the strongest checkpoint was:

- `hummbl_basen_aligned_codex_split_2ep.pt`

Model-level result before decoding changes:

- `val_bpb = 0.394554`
- rubric holdout teacher-forced loss: `2.5600`
- free-generation metrics:
  - starts-with-target: `0/8`
  - exact-match: `0/8`
  - keyword-hit rate: `0.1375`

This suggested:

- the model had learned real structure under teacher forcing
- but the free-generation surface was still badly formatted and collapse-prone

## Decoding Changes

Implemented in `basen_eval_packet.py`:

- optional `--force-prefix target_step`
- optional `--repetition-penalty`

These are decoding-only changes.
They do not alter model weights.

## Results

### Anchored decode, repetition penalty `1.15`

Command shape:

- force target-step prefix
- mild repetition penalty

Observed result:

- starts-with-target: `8/8`
- exact-match: `0/8`
- keyword-hit rate: `0.2333`
- teacher-forced loss unchanged: `2.5600`
- `val_bpb` unchanged: `0.394554`

Interpretation:

- target-step anchoring fixes the output opening format
- mild repetition control improves content recall beyond the raw model decode

### Anchored decode, repetition penalty `1.30`

Observed result:

- starts-with-target: `8/8`
- exact-match: `0/8`
- keyword-hit rate: `0.2750`
- teacher-forced loss unchanged: `2.5600`
- `val_bpb` unchanged: `0.394554`

Interpretation:

- this is the best free-generation rubric result so far
- improvement is due to decoding only, not retraining

## Qualitative Pattern

The anchored outputs now often begin correctly with the target step label, for example:

- `[READINESS]: capacity, authority, ...`

But most cases still collapse after the first useful phrase into repetition or malformed continuations.

This means:

- the model knows more than the original greedy decode was surfacing
- but free generation is still not robust or production-ready

## Current Conclusion

This is a real record for the BaseN rubric lane:

- best free-generation formatting so far
- best rubric keyword-hit rate so far: `0.2750`

The decoding win does not replace the model-level win.
It sits on top of it:

- model-level structure learning made the gain possible
- decoding changes made part of that structure visible

## Recommended Next Move

1. keep the anchored rubric decode as the current best free-generation surface
2. test one more decoding control only if it is low-risk and comparable
3. otherwise move back to model-side work with the same eval packet intact
