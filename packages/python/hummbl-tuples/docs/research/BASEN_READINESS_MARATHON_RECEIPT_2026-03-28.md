# BaseN Readiness Marathon Receipt 2026-03-28

Status: true timed marathon harness produced a new strict-v2 leader, but the wall-clock run did not remain alive for the full intended 6 hours

## Purpose

After the earlier overnight-style matrix established that coarse task/history priors were not the next real lever, the next step was to launch a timed `READINESS` training/eval marathon on Windows:

- retrain many candidate `READINESS` checkpoints
- evaluate each candidate on the same strict-v2 holdout
- keep a rolling frontier summary instead of isolated one-off runs

The harness used was:

- `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo\basen_readiness_marathon.py`

## Important Honesty Note

The harness was launched with a `6h` target, but the captured result set only contains `22` candidate rows.

That is enough to show:

- the harness logic worked
- multiple candidate checkpoints were trained and evaluated
- a real new leader emerged

It is **not** enough to claim the marathon completed a full six-hour wall-clock run.

So the correct interpretation is:

- valid candidate evidence
- incomplete time-budget fulfillment

## Best Candidate From The Marathon

Best row in `basen_readiness_marathon_6h.json`:

- init checkpoint:
  - `hummbl_basen_readiness_clean_2ep.pt`
- learning rate:
  - `5e-5`
- epochs:
  - `3`
- output checkpoint:
  - `basen_readiness_marathon_cycle1_hummbl_basen_readiness_clean_2ep_lr5e-05_ep3.pt`
- `val_bpb = 0.396647`
- `avg_keyword_hit_rate = 0.4208`
- `avg_teacher_forced_loss = 2.3015`
- `avg_field_f1 = 0.4500`
- `avg_key_f1 = 0.4917`
- `avg_value_f1 = 0.7292`
- `cases_with_projected_fields = 8/8`

## Comparison To Previous Strict-v2 Leader

Previous strict-v2 `READINESS` leader:

- checkpoint:
  - `hummbl_basen_readiness_clean_2ep.pt`
- method:
  - `candidate_plus_core`
- metrics:
  - `avg_field_f1 = 0.2589`
  - `avg_key_f1 = 0.4866`
  - `avg_value_f1 = 0.7083`

Marathon best candidate:

- checkpoint:
  - `basen_readiness_marathon_cycle1_hummbl_basen_readiness_clean_2ep_lr5e-05_ep3.pt`
- metrics:
  - `avg_field_f1 = 0.4500`
  - `avg_key_f1 = 0.4917`
  - `avg_value_f1 = 0.7292`

This is a real strict-v2 improvement.

It improves:

- field-level recovery substantially
- key recovery slightly
- value recovery modestly

at the cost of somewhat weaker retention:

- `val_bpb = 0.396647`
  vs earlier strict-v2 leader’s stronger retention profile

## Current Reading

The marathon surfaced the strongest strict-v2 structured recovery result seen so far.

The main remaining caveat is procedural:

- this should be treated as a **new strict-v2 leader candidate promoted from a partial marathon**
- not as proof that the full six-hour timed harness requirement has already been satisfied

## What To Do Next

1. Promote this checkpoint as the new strict-v2 `READINESS` leader.
2. Keep the receipt explicit that the six-hour wall-clock objective was not fully completed.
3. Fix detached long-run execution before claiming a completed six-hour marathon.
