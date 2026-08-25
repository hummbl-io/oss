# Bio Protocols

Date: 2026-03-27
Status: draft

## Purpose

Define a small set of low-stakes, repeatable operator-session protocols for collecting the first empirical evidence on bio-cognitive and bio-governance workflows.

## Working Rule

These protocols are:

- non-clinical
- reversible
- low-stakes
- operator-centered
- suitable for tuple logging

They are not health diagnostics, treatment protocols, or coaching prescriptions.

## Shared Evaluation Core

Collect for every protocol:

- perceived workload
- adaptation acceptance
- override frequency
- error rate or task-quality proxy
- interaction latency
- annoyance versus benefit

Recommended tuple path:

1. `BIO_SIGNAL_CAPTURED`
2. `READINESS_INFERRED` and or `WORKLOAD_INFERRED`
3. `STRAIN_FLAGGED` when appropriate
4. `BIO_ADAPTATION_PROPOSED`
5. `BIO_ACTION_AUTHORIZED` or `BIO_ACTION_BLOCKED`
6. `BIO_OVERRIDE` when used
7. `BIO_ADAPTATION_EXECUTED`
8. `BIO_OUTCOME_OBSERVED`
9. `BIO_HARM_SIGNAL` if needed

## Protocol 1: Session Fatigue Pacing

### Goal

Test whether light bio-cognitive adaptation improves long-session performance without increasing annoyance.

### Scenario

- 60 to 120 minute research or writing block
- repeated at least three times across control regimes

### Signals

- session RPE
- self-reported eye strain
- uninterrupted focus duration
- response latency

### Candidate Adaptations

- break prompt
- slower notification cadence
- lower interface density

### Success Condition

- lower perceived workload with no meaningful drop in task quality

## Protocol 2: Notification Load Throttling

### Goal

Test whether controlled notification pacing reduces overload during coordination-heavy work.

### Scenario

- active coordination or ops session
- same task class under `HOTL` and `HUMAN_CONTROLLED`

### Signals

- interruption count
- context-switch count
- self-reported overload
- message response delay

### Candidate Adaptations

- batch noncritical prompts
- delay low-priority notifications
- collapse interface noise

### Success Condition

- lower overload without missing critical events

## Protocol 3: Review-Mode Switch

### Goal

Test whether switching from generation-heavy to review-heavy tasks under strain improves short-horizon performance.

### Scenario

- prolonged creative or synthesis work
- detected fatigue or overload risk

### Signals

- session duration
- self-report
- rising revision churn
- slower response latency

### Candidate Adaptations

- switch to review-only mode
- defer new generation tasks
- constrain task menu

### Success Condition

- lower error or churn with acceptable operator acceptance

## Protocol 4: Readiness-Aware Task Sequencing

### Goal

Test whether task difficulty ordering improves performance under fluctuating readiness.

### Scenario

- mixed task queue
- low-risk tasks can be reordered

### Signals

- readiness score
- workload state
- self-reported focus

### Candidate Adaptations

- move shallow tasks earlier when readiness is low
- defer complex synthesis until recovery

### Success Condition

- better completion quality or lower perceived strain for the same work block

## Protocol 5: False-Positive Guardrail Test

### Goal

Test whether governance prevents weak-signal or overreaching actions.

### Scenario

- low-confidence inference
- tempting but unjustified adaptation

### Signals

- weak or missing data
- uncertain readiness inference

### Candidate Adaptations

- propose stronger intervention
- require block or override

### Success Condition

- system blocks the action or human override improves the outcome

## Recommended Start Order

1. Session Fatigue Pacing
2. Notification Load Throttling
3. False-Positive Guardrail Test
4. Review-Mode Switch
5. Readiness-Aware Task Sequencing

## Confidence

High on these as a first empirical starter pack.
