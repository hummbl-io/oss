# Bio Protocol 1 Run Packet

Date: 2026-03-27
Status: ready

## Protocol

`Session Fatigue Pacing`

Reference:

- [BIO_PROTOCOLS.md](/Users/others/PROJECTS/hummbl-tuples/docs/research/BIO_PROTOCOLS.md)

## Goal

Run the first real low-stakes bio-cognitive case with the minimum tuple chain and case evidence.

## Session Requirements

- 60 to 120 minute work block
- research, writing, or coordination task
- low stakes and fully reversible adaptations
- preferred control mode: `AI_PROPOSE_HUMAN_CONFIRM`

## Minimum Data To Capture

- session RPE
- self-reported eye strain or strain note
- uninterrupted focus duration
- one performance proxy:
  - error count
  - response latency
  - revision churn

## Minimum Tuple Chain

1. `BIO_SIGNAL_CAPTURED`
2. `READINESS_INFERRED` or `WORKLOAD_INFERRED`
3. `BIO_ADAPTATION_PROPOSED`
4. `BIO_ACTION_AUTHORIZED`
5. `BIO_ADAPTATION_EXECUTED`
6. `BIO_OUTCOME_OBSERVED`

Optional:

- `STRAIN_FLAGGED`
- `BIO_ACTION_BLOCKED`
- `BIO_OVERRIDE`
- `BIO_HARM_SIGNAL`

## Candidate Adaptations

- prompt short break
- reduce interface density
- slow notification cadence
- switch to review-heavy mode

## Success Criteria

- logging is complete
- adaptation is accepted or clearly rejected
- one believable outcome note is recorded

## Failure Criteria

- weak or missing signals make the inference meaningless
- adaptation is too vague to evaluate
- no outcome is recorded

## Artifacts To Produce

- one filled case log using [BIO_CASE_LOG_TEMPLATE.md](/Users/others/PROJECTS/hummbl-tuples/docs/research/BIO_CASE_LOG_TEMPLATE.md)
- tuple references or example JSONs
- one short note on whether the protocol should be reused
