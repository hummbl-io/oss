# BaseN Strict V2 Loop Board

Status: active execution board for the stricter BaseN proof loop

## Current Objective

Beat the strict `v2` surface with durable structured recovery, not flattering decode artifacts.

## Current Bests

### Best direct strict-v2 anchored decode

- checkpoint: `hummbl_basen_aligned_codex_normtrim_2ep.pt`
- decode: anchored section decode
- result:
  - projected field F1 `0.0`

### Best strict-v2 constrained readiness probe

- checkpoint: `basen_readiness_marathon_cycle1_hummbl_basen_readiness_clean_2ep_lr5e-05_ep3.pt`
- probe mode: `candidate_plus_core`
- result:
  - field F1 `0.4500`
  - key F1 `0.4917`
  - value F1 `0.7292`

Note:

- this leader came from a timed marathon harness that produced valid candidate rows
- but the full six-hour wall-clock target was not yet proven complete
- so the model result is real, while the marathon budget claim remains incomplete

## Next Loop

1. improve key discovery
   - candidate-plus-core is now the baseline
   - explicit pruning/ranking sweeps did not beat it
   - latest answer:
     - coarse task/history/task-history priors did not beat the baseline in the overnight harness
   - next candidate:
     - smarter candidate generation from field/value evidence, not just coarse priors

2. strengthen small clean training
   - keep readiness-only training small
   - current answer:
     - init from current rubric leader beats init from base checkpoint
     - `1` epoch is enough to match the current field/key frontier
   - do not spend more time on base-init sweeps unless another hypothesis appears

3. extend constrained probing to `WICKEDNESS`
   - only after `READINESS` remains stable

4. feed nodezero a gold micro-corpus spec
   - clean upstream data is now a bigger lever than more noisy generation

## Stop Conditions

Stop a branch of work if:

- direct anchored decode still dominates but only on a weak eval surface
- a training pass improves teacher-forced loss but hurts structured recovery
- a bigger corpus adds schema drift faster than it adds recoverable structure

## Proof Conditions

This loop counts as real progress only if:

- structured metrics improve on strict `v2`
- the eval surface is versioned and stable
- the improvement is explainable
- and the result survives comparison to the previous best probe baseline

## Settled Answers

- `READINESS` is now the first official constrained lane
- `candidate_plus_core` is the current strict-v2 default probe mode
- readiness-clean training helps, but probe strategy is still the bigger lever
- start-from-leader beats start-from-base decisively
- stronger pruning does not beat the current candidate-plus-core probe
- partial marathon training found a stronger strict-v2 checkpoint:
  - `basen_readiness_marathon_cycle1_hummbl_basen_readiness_clean_2ep_lr5e-05_ep3.pt`
  - `field_f1 = 0.4500`
  - `key_f1 = 0.4917`
  - `value_f1 = 0.7292`
- the longer-running prior sweep did not produce a new frontier
  - best overnight row:
    - `hummbl_basen_aligned_codex_normtrim_2ep.pt`
    - `field_f1 = 0.2500`
    - `key_f1 = 0.3750`
    - `value_f1 = 0.6875`
  - this remains below the standing strict-v2 leader
