# Bio Control Experiment Matrix

Date: 2026-03-27
Status: draft

## Question

How should HUMMBL compare AI and human control regimes for bio-cognitive adaptations?

## Bottom Line

The first useful comparison is not between many adaptation models. It is between control regimes over the same small set of low-risk interventions.

That means holding:

- signals
- inference logic
- adaptation candidates
- and outcome measures

as fixed as possible while varying authority and approval structure.

## Recommended Regimes

### `AI_PROPOSE_HUMAN_CONFIRM`

Use when the system may recommend but a human must approve each action.

Best for:

- early studies
- low-risk pacing changes
- trust calibration

### `HOTL`

Use when the system may act within narrow policy bounds while the human supervises and can override.

Best for:

- notification pacing
- interface-density changes
- reminder timing

### `HUMAN_CONTROLLED`

Use when the human chooses all actions and the system only supplies state summaries or ranked options.

Best for:

- baseline comparison
- high-trust calibration
- operator preference studies

## Avoid Early

### `AI_AUTONOMOUS`

Avoid in the first wave except for toy or fully reversible interface-only actions.

## Experimental Table

| Regime | Who selects action | Who authorizes | Best early actions | Main risk | Main value |
| --- | --- | --- | --- | --- | --- |
| `AI_PROPOSE_HUMAN_CONFIRM` | AI | human | break prompt, pacing change, lower interface density | confirmation burden | clean audit and trust calibration |
| `HOTL` | AI within policy | policy plus supervising human | reversible interface and pacing actions | overreach from weak signals | realistic assisted-operation model |
| `HUMAN_CONTROLLED` | human | human | all actions | low automation benefit | best baseline for acceptance and judgment quality |

## Fixed Inputs

Keep fixed across runs:

- signal set
- inference thresholds
- adaptation menu
- task block length
- evaluation rubric

## Core Outcome Measures

- perceived workload
- error rate
- interaction latency
- override rate
- action acceptance rate
- trust in adaptation
- measured benefit versus annoyance

## Suggested Negative Cases

- false overload signal
- weak-confidence readiness inference
- adaptation that hurts flow
- blocked action due to insufficient evidence
- human override that improves the outcome

## HUMMBL Relevance

This matrix makes the bio lane comparable with the existing BaseN control-regime work.

It also gives the system a disciplined way to study:

- when AI should only suggest
- when HOTL is enough
- and when human control is still necessary

## Confidence

High on the structure. Medium on the exact thresholds and metrics.
