# BaseN Training Spec

Status: draft  
Scope: how BaseN traces should become supervised learning signal

## 1. Purpose

This spec defines how BaseN traces become training examples without collapsing path structure into flat text imitation.

## 2. Training Families

BaseN training should distinguish at least:

- `PATH_CONSTRUCTION`
- `PATH_CONTINUATION`
- `RUBRIC_PREDICTION`
- `PATH_EVALUATION`
- `NEGATIVE_CORRECTION`

These should not be silently merged.

## 3. Response Masking Rule

The default rule is:

- loss applies to supervised target spans only
- prompt/system/context tokens are masked out

This is mandatory for:

- SFT over BaseN traces
- step-conditioned next-step prediction
- rubric tuple prediction

## 4. Conditioning Inputs

A path-conditioned training example should include:

- system role
- task
- protocol family
- prior validated history
- current target step type

The current Windows implementation generates some of this context but then discards it in training.

That should be corrected.

## 5. Training Example Shape

Minimum recommended shape:

- `input_context`
  - `task`
  - `problem_class`
  - `protocol_id`
  - `protocol_family`
  - `history`
  - `control_mode`
- `target`
  - exact next step content or rubric tuple

## 6. Corpus Separation

Do not train one undifferentiated objective over:

- protocol traces
- rubric traces
- path-eval traces
- negative traces

Instead declare the family for each example and choose the objective accordingly.

## 7. Provenance Requirements

Every trained artifact must declare:

- source checkpoint
- trace files used
- counts by protocol family
- masking policy
- training steps
- optimizer settings
- eval packet location

## 8. Minimum Training Claims

A BaseN training run may safely claim:

- which corpus families were used
- how many validated traces were used
- what objective was optimized

It may not safely claim reasoning improvement without the evaluation spec being satisfied.
