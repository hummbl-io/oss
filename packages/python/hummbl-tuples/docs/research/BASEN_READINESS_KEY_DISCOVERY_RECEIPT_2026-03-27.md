# BaseN Readiness Key Discovery Receipt 2026-03-27

Status: key-discovery and pruning loop for strict holdout v2  
Scope: `C:\Users\Owner\PROJECTS\yolo-playground\autoresearch-yolo`

## Goal

After the readiness sweep, the next bottleneck was clearly key discovery.

The question was:

- can stricter ranking and pruning improve field precision without losing the best strict-v2 result?

## Ranked Probe

The probe was upgraded to:

- score each proposed field by:
  - key evidence from the raw generation
  - plus value confidence from the constrained value probe
- then keep only the highest-scoring fields

Result:

- it reduced obvious fallback overprediction
- but it did **not** beat the current strict-v2 best

### Ranked summary

For the readiness clean leader:

- field F1 `0.25`
- key F1 `0.3333`
- value F1 `0.7083`

Compared to the standing best:

- field F1 `0.2589`
- key F1 `0.4866`
- value F1 `0.7083`

So ranking alone was not enough.

## Pruning Sweep

Same readiness clean leader, same strict-v2 surface, same `candidate_plus_core` probe,
with explicit pruning sweeps:

- `max_fields=2`, threshold `0.85`
  - field F1 `0.20`
  - key F1 `0.25`
- `max_fields=2`, threshold `0.95`
  - field F1 `0.20`
  - key F1 `0.25`
- `max_fields=2`, threshold `1.05`
  - field F1 `0.15`
  - key F1 `0.20`
- `max_fields=3`, threshold `1.05`
  - field F1 `0.2083`
  - key F1 `0.25`
- `max_fields=1`, threshold `0.85`
  - field F1 `0.0625`
  - key F1 `0.125`

All of these underperformed the current default.

## Current Winner

The best strict-v2 `READINESS` probe still is:

- checkpoint: `hummbl_basen_readiness_clean_2ep.pt`
- probe mode: `candidate_plus_core`
- current default behavior:
  - no additional hard pruning beyond the existing selection logic

Metrics:

- field F1 `0.2589`
- key F1 `0.4866`
- value F1 `0.7083`

## Conclusion

What failed:

- harder caps
- higher score thresholds
- simplistic ranking-only cleanup

What survived:

- `candidate_plus_core` remains the best strict-v2 key discovery strategy so far

That means the next improvement is probably **better candidate generation**, not stronger pruning.

Likely next directions:

1. task-aware key priors
2. protocol/history-aware key suggestion
3. extending the constrained-lane method to `WICKEDNESS`
