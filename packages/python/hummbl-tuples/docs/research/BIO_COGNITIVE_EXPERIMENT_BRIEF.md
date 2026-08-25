# Bio-Cognitive Experiment Brief

Date: 2026-03-27
Status: draft

## Question

How should HUMMBL test bio-cognitive and bio-governance workflows without overclaiming clinical or coaching authority?

## Bottom Line

Start with low-stakes operator-performance experiments.

The first useful domain is not medicine. It is long-session knowledge work where:

- workload accumulation is real
- adaptation is reversible
- human override is easy
- and outcomes can be measured without pretending to diagnose health

## First Experiment

### Name

Readiness-aware session adaptation

### Scenario

An operator works through a long research or coordination block. The system:

1. records light bio-cognitive signals
2. infers readiness or overload risk
3. proposes pacing or interface adaptations
4. requires human authorization
5. observes short-horizon outcomes

### Example Signals

- session RPE
- self-reported eye strain
- break intervals
- continuous focus duration
- error rate
- interaction latency

### Candidate Adaptations

- suggest a short recovery break
- reduce interface density
- defer noncritical prompts
- slow notification cadence
- switch from generation-heavy to review-heavy tasks

## Control Regimes

- `AI_PROPOSE_HUMAN_CONFIRM`
- `HOTL`
- `HUMAN_CONTROLLED`

Avoid full `AI_AUTONOMOUS` control in early studies.

## Outcome Measures

- perceived workload
- task completion quality
- error rate
- interaction latency
- override frequency
- operator trust
- adaptation acceptance rate

## Risks

- weak signals may be overinterpreted
- adaptation may annoy rather than help
- human self-report may be noisy
- performance changes may be caused by confounds

## Research Value

This is a clean bridge between:

- HCI
- HFE
- fitness and readiness concepts
- human control regimes
- tuples as auditable intervention records

## Confidence

High on the suitability of this first experiment. Medium on exact signal choice.
