# BaseN Eval Packet Receipt 2026-03-27

Status: first executable pre/post-style eval packet on Windows  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Packet Shape

Windows-side scaffolding added:

- `basen_eval_packet.py`
- `basen_eval_holdout.jsonl`

Packet contents:

- short-run `val_bpb` retention check using the existing `prepare.py:evaluate_bpb`
- tiny held-out reasoning set with path-conditioned prompts
- simple response checks:
  - starts with target step type
  - expected-keyword hit rate
  - teacher-forced next-step loss on the expected held-out response

Prompt note:

- the first packet draft mistakenly ended prompts with `Answer:`
- the packet was corrected to end with `Reasoning:` to match the patched training surface
- held-out results remained at `0/5` after the correction

Important caveat:

- this receipt used `eval_tokens=4096` for speed
- these BPB values are useful for iteration and regression detection
- they are not leaderboard-grade benchmark receipts

## Checkpoints Evaluated

### 1. Pre-alignment checkpoint

Checkpoint:

- `checkpoint_pre_eval.pt`

Observed result:

- `val_bpb = 0.365424`
- held-out reasoning cases: `5`
- starts-with-target count: `0`
- average keyword hit rate: `0.0`
- average teacher-forced loss: `7.1393`

Observed generation pattern:

- output is still not task-grounded
- after prompt correction it produced repetitive pseudo-reasoning text like:
  - `Rezing about the last thinging...`

Interpretation:

- the base checkpoint retains strong language-model quality on the short BPB packet
- it does not transfer into usable held-out BaseN reasoning under the current prompt format

### 2. Existing aligned model

Checkpoint:

- `hummbl_aligned_model.pt`

Observed result:

- `val_bpb = 0.476674`
- held-out reasoning cases: `5`
- starts-with-target count: `0`
- average keyword hit rate: `0.0`
- average teacher-forced loss: `5.6513`

Observed generation pattern:

- output is still structurally bad
- sample completions remain repetitive and non-task-grounded

Interpretation:

- the existing aligned model degrades BPB substantially on the short packet
- it also fails the tiny held-out reasoning packet
- it does, however, reduce teacher-forced holdout loss relative to the base checkpoint
- this is evidence that it learned something about the target responses, but in a way that is too destructive to base-model quality

### 3. Codex-patched concise alignment run (full concise set)

Checkpoint:

- `hummbl_aligned_model_codex.pt`

Training provenance:

- one short real run from the patched `hummbl_sft.py`
- validator-gated concise corpus
- response-only masking
- path-conditioned prompt format

Observed result:

- `val_bpb = 0.370800`
- held-out reasoning cases: `5`
- starts-with-target count: `0`
- average keyword hit rate: `0.0`
- average teacher-forced loss: `not captured in the first packet revision`

Observed generation pattern:

- output remains unusable on the tiny held-out set
- sample completions collapse into repetitive fragments rather than valid next steps

Interpretation:

- the corrected concise pipeline is materially less damaging than the previous aligned artifact
- retention moved from `0.476674` down to `0.370800`
- held-out reasoning transfer is still absent
- this suggests the first corrected win is training hygiene, not yet reasoning capability

### 4. Codex-patched concise alignment run (true train/holdout split)

Checkpoint:

- `hummbl_aligned_model_codex_split.pt`

Training provenance:

- one short real run from the patched `hummbl_sft.py`
- deterministic concise train split:
  - train samples: `155`
  - holdout cases: `5`
- validator-gated concise corpus
- response-only masking
- path-conditioned prompt format

Observed result:

- `val_bpb = 0.369635`
- held-out reasoning cases: `5`
- starts-with-target count: `0`
- exact-match count: `0`
- average keyword hit rate: `0.0`
- average teacher-forced loss: `5.8539`

Interpretation:

- this checkpoint is still bad at free generation on the held-out reasoning set
- but it substantially improves held-out teacher-forced next-step loss relative to the base checkpoint:
  - `7.1393 -> 5.8539`
- and it preserves BPB far better than the previous aligned artifact:
  - `0.369635` versus `0.476674`
- this is the first credible BaseN-style tradeoff improvement:
  - better reasoning-target fit than the base checkpoint
  - far less retention damage than the old aligned model

## Immediate Conclusion

The first eval packet supports the peer-review concern:

- the previous alignment artifact is not yet a proof of BaseN progress
- training loss alone was not enough
- retention and held-out reasoning checks need to be mandatory before promoting future models
- the corrected concise pipeline already improves alignment hygiene and BPB retention
- the split-respecting Codex run also improves held-out teacher-forced next-step loss, even though free generation remains poor

## What This Changes

The next BaseN proof step should be:

1. train with the patched validator-gated, response-masked, path-conditioned pipeline
2. run this eval packet before and after
3. compare against:
   - `checkpoint_pre_eval.pt`
   - the existing `hummbl_aligned_model.pt`
   - `hummbl_aligned_model_codex.pt`
   - `hummbl_aligned_model_codex_split.pt`

Only then should a new alignment artifact be treated as meaningful.
