# Nodezero BaseN Gold Micro-Corpus Requirements

Status: upstream requirements for the next clean BaseN data harvest  
Target node: `nodezero`

## Goal

Nodezero should stop optimizing for large noisy corpus volume on this lane.

The next useful upstream contribution is a small gold-quality micro-corpus that strengthens the
official constrained `READINESS` lane first, then `WICKEDNESS`.

## Priority Order

1. `READINESS`
2. `WICKEDNESS`
3. only later: multi-section mixed rubric traces

## Required Corpus Sizes

### READINESS gold set

- target: `25` to `50` traces
- each trace should contain at least one `[READINESS]` step

### WICKEDNESS gold set

- target: `25` to `50` traces
- each trace should contain at least one `[WICKEDNESS]` step

## Hard Requirements

Every target step must satisfy all of these:

1. exactly one target section
   - no mixed `[WICKEDNESS]` + `[READINESS]` output in one target

2. canonical `key=value` format
   - comma-separated
   - no prose

3. canonical key vocabulary only

4. canonical value vocabulary only

5. no protocol leakage
   - a `[READINESS]` target must not emit a `[WICKEDNESS]` section

6. short targets
   - ideally `2` to `3` fields
   - max `4`

7. coherent history
   - prior steps should support the target step semantically

## Preferred READINESS Key Surface

Nodezero should bias toward these keys first:

- `authority`
- `capacity`
- `contestation`
- `interdependence`
- `uncertainty`

Secondary keys are allowed, but only after the core set is clean:

- `necessity`
- `adaptability`
- `resilience`
- `robustness`
- `complexity`
- `predictability`

## Required Metadata

Each example should carry:

- `task`
- `protocol`
- `history`
- `target_step_type`
- `response`
- `source_model`
- `generator_version`
- `quality_status`

## Quality Labels

Each candidate row should be manually or semi-manually marked:

- `gold`
- `usable`
- `reject`

Only `gold` should enter the micro-corpus.

## Explicitly Avoid

- freeform explanatory prose
- synonym drift like `moderate` vs `medium` unless canonically normalized
- mixed-section targets
- vague labels like `needs`, `not`, or partial broken values
- giant augmentation passes that produce thousands of weak rows

## Success Condition

Nodezero has succeeded when the micro-corpus:

- can be read by a human in one sitting
- contains almost no schema surprises
- and materially improves strict-v2 structured recovery when used for a small clean fine-tune
