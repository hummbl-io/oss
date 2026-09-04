# BaseN Peer Review 2026-03-27

Status: review memo  
Scope: Windows-side BaseN trace generation, SFT dataset construction, and alignment scripts observed on 2026-03-27

Primary review targets:

- `<local-path>`
- `<local-path>`
- `<local-path>`
- `<local-path>`
- `<local-path>`

## Findings

### 1. The rubric corpus is semantically inconsistent

The current `nodezero_hummbl_traces_v2_rubric.jsonl` corpus mixes labels and protocols in ways that should fail quality control.

Observed issues:

- `ScientificMethod` rows contain `[WICKEDNESS]` / `[READINESS]` payloads
- `WickednessAudit` rows duplicate or leak labels across step fields
- some `content` values restate the wrong tuple or protocol family

This is not a minor formatting problem. It means the alignment layer is learning against mislabeled supervision.

Implication:

- corpus cleaning and validation should happen before more BaseN alignment runs

### 2. Loss is applied to prompt tokens, not just response tokens

Both alignment scripts train over the full concatenated sequence.

In practice this means they optimize:

- system prompt tokens
- task framing
- protocol framing
- instruction scaffolding
- response tokens

Instead of only optimizing the reasoning continuation.

Relevant code:

- `hummbl_basen_sft.py`
  - prompt/response concatenation around lines `42-50`
  - full-sequence `x`/`y` construction around lines `62-69`
- `hummbl_sft.py`
  - prompt/response concatenation around lines `44-45`
  - full-sequence `x`/`y` construction around lines `62-70`

Implication:

- training signal is diluted
- the model is rewarded for reproducing scaffolding
- small data runs will overfit to formatting instead of reasoning behavior

### 3. The dataset builder preserves history, but the trainer discards it

`hummbl_sft_dataset.py` produces a richer step-conditioned structure:

- `instruction`
- `context.system`
- `context.history`
- `context.task`
- `context.protocol`
- `response`

But `hummbl_sft.py` only consumes:

- `system`
- `instruction`
- `response`

It ignores:

- `history`
- `task`
- `protocol` as explicit fields

This collapses a path-conditioned supervision format into a much weaker imitation surface.

Implication:

- the implementation underuses the very structure BaseN is supposed to make valuable

### 4. Model-family provenance is inconsistent

The BaseN alignment script presents itself as `67M`, but the configuration points elsewhere.

Relevant code:

- `hummbl_basen_sft.py:10`
  - comment says `67M config`
- `hummbl_basen_sft.py:21`
  - output name `hummbl_basen_aligned_67M.pt`
- `hummbl_basen_sft.py:22`
  - `DEPTH = 6`, explicitly described as matching the `33M` Ascension baseline

Implication:

- alignment artifacts cannot be compared cleanly
- downstream claims about BaseN-aligned model size are not trustworthy until naming and config lineage are reconciled

### 5. The alignment receipts show optimization, not improvement

The logs show loss decreasing:

- `deep_alignment_final.log`
- `sft_alignment_concise_v2.log`

That is useful, but it is not enough.

What is missing:

- post-alignment TinyStories BPB
- held-out trace evaluation
- pre/post comparison on the same prompt set
- forgetting check
- challenge-task eval

Implication:

- current BaseN work has proof of training activity
- it does not yet have proof that BaseN alignment improved anything important

## Assessment

The BaseN direction is real.

The current implementation is not yet strong enough to support strong claims about:

- reasoning improvement
- alignment quality
- path-conditioned learning
- model-family advancement

The main problems are:

- upstream data quality
- response-masking absence
- discarded conditioning context
- provenance drift
- lack of evaluation discipline

## Recommended Next Fix Order

1. Add corpus validation and reject malformed rubric traces.
2. Train on response spans only.
3. Feed history/task/protocol into the trainer explicitly.
4. Reconcile 33M vs 67M naming and checkpoint provenance.
5. Add a mandatory post-alignment evaluation packet before saving/promoting artifacts.

## Immediate Safe Claim

The safe current claim is:

- BaseN alignment infrastructure exists
- Nodezero-generated reasoning traces were consumed on Windows
- alignment loss fell during training

The unsafe current claim is:

- BaseN alignment has already improved model reasoning quality in a verified way
