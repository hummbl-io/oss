# World Record Baselines

This memo defines the external reference surface for HUMMBL's TinyStories record attempts.

## Purpose

The phrase `world record` is too loose unless the benchmark category is explicit.

For TinyStories, there does not appear to be a canonical public leaderboard for `validation BPB` comparable to the FineWeb speedrun format maintained by Keller Jordan's `modded-nanogpt`.

That means HUMMBL must distinguish:

- public prior art
- informative but non-comparable reports
- our own internal verified record ledger

## Public Reference Points

### 1. TinyStories paper

Primary source:
- https://arxiv.org/abs/2305.07759

What it gives us:
- official dataset framing
- official model family references
- evaluation methodology

What it does **not** give us:
- a canonical public `validation BPB` leaderboard
- a stable public record table for lowest TinyStories BPB

Important note:
- The paper emphasizes GPT-4-based evaluation of generated stories, not a community-maintained BPB leaderboard.

### 2. Official TinyStories model family

Primary reference family:
- official HF TinyStories models referenced in the paper, such as `TinyStories-33M`, `TinyStories-28M`, and smaller variants

Usefulness:
- establishes a recognizable architecture family
- gives model-size reference points for comparisons

Limitation:
- model cards and ecosystem references do not constitute a formal BPB record surface by themselves

### 3. Keller Jordan record discipline

Primary reference:
- https://github.com/KellerJordan/modded-nanogpt

Usefulness:
- shows how to define a public competitive benchmark rigorously:
  - explicit task
  - explicit metric threshold
  - explicit hardware class
  - linked logs
  - historical progression table

Limitation:
- it is a FineWeb speedrun benchmark, not TinyStories BPB

## Informative But Not Automatically Comparable

These are useful context, but should not be treated as direct baselines unless tokenizer, split, metric, parameter count, and evaluation protocol match closely.

- Hugging Face TinyStories derivatives reporting loss or perplexity rather than BPB
- community repos using different tokenizers or reduced vocabularies
- reports using different validation splits
- reports using GPT-Eval only

## Current HUMMBL Claim Surface

At present, the strongest defensible categories are:

- `best_verified_absolute_tinystories_bpb`
- `best_verified_600s_tinystories_bpb`
- `best_verified_3600s_tinystories_bpb`
- `best_verified_same_family_tinystories_bpb`

Those are grounded by local receipts in:
- [TRAINING_RUN_LEDGER.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/TRAINING_RUN_LEDGER.md)

## What We Still Need

To make a stronger external claim, we need:

1. a precise BPB definition memo
2. tokenizer and vocabulary comparability notes
3. split comparability notes
4. parameter-class definitions
5. a public or at least stable historical record table
6. explicit citation of the best public TinyStories baselines we can locate

## Working Conclusion

Right now, HUMMBL can credibly claim:

- `best verified result in our TinyStories run corpus`
- `candidate unofficial record in a narrowly defined TinyStories BPB category`

It cannot yet rigorously claim:

- `unqualified TinyStories world record`

without a tighter public comparison framework.
