# BaseN Concise Sweep Receipt 2026-03-27

Status: first small parameterized concise-lane sweep on Windows  
Scope: `<local-path>`

## Setup

Shared setup across all runs:

- patched `hummbl_sft.py`
- validator-gated concise corpus
- deterministic train/holdout split
  - train samples: `155`
  - holdout cases: `5`
- response-only masking
- path-conditioned prompts
- `SFT_EPOCHS = 1`
- short eval packet with:
  - `val_bpb`
  - held-out free-generation checks
  - held-out teacher-forced next-step loss

Important caveat:

- free generation remained poor in all runs
- the useful comparison signal here is the tradeoff between:
  - retention (`val_bpb`)
  - teacher-forced holdout loss

## Results

### Base checkpoint

- checkpoint: `checkpoint_pre_eval.pt`
- `val_bpb = 0.365424`
- `avg_teacher_forced_loss = 7.1393`

### Old aligned artifact

- checkpoint: `hummbl_aligned_model.pt`
- `val_bpb = 0.476674`
- `avg_teacher_forced_loss = 5.6513`

Interpretation:

- strong target-fit gain
- unacceptable retention damage

### Codex split run, `lr = 2e-5`

- checkpoint: `hummbl_aligned_model_codex_lr2e5.pt`
- `val_bpb = 0.365963`
- `avg_teacher_forced_loss = 6.4247`

Interpretation:

- retention is nearly identical to the base checkpoint
- reasoning-target fit improves, but only modestly
- this is the conservative end of the tradeoff curve

### Codex split run, `lr = 5e-5`

- checkpoint: `hummbl_aligned_model_codex_split.pt`
- `val_bpb = 0.369635`
- `avg_teacher_forced_loss = 5.8539`

Interpretation:

- materially better target-fit than the base checkpoint
- far better retention than the old aligned artifact
- this is the strongest current Pareto point

### Codex split run, `lr = 1e-4`

- checkpoint: `hummbl_aligned_model_codex_lr1e4.pt`
- `val_bpb = 0.380486`
- `avg_teacher_forced_loss = 5.2217`

Interpretation:

- best teacher-forced holdout loss in the Codex concise sweep
- but noticeably worse retention than the `5e-5` run
- this starts moving back toward the old artifact’s failure mode

## Current Conclusion

The concise lane now has a real measurable tradeoff curve:

- lower LR preserves the base model better
- higher LR fits the held-out reasoning targets better
- `5e-5` is the best current compromise

This is the first useful optimization result for the patched BaseN pipeline:

- not “generation is fixed”
- but “we can now tune a visible retention-vs-reasoning tradeoff instead of flying blind”

## Recommended Next Move

Use the `5e-5` split-respecting concise run as the current baseline and next:

1. increase training duration slightly without changing the eval packet
2. improve held-out prompt/response formatting further
3. only then try to transfer the same discipline to the rubric/BaseN lane
