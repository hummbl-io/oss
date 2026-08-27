# Bio Empirical Starter Pack

Date: 2026-03-27
Status: draft

## Purpose

Provide the minimum kit needed to begin collecting evidence for the bio-cognitive and bio-governance lane.

## Included Components

- [BIO_GOVERNANCE_INDEX.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/specs/BIO_GOVERNANCE_INDEX.md)
- [BIO_GOVERNANCE_TUPLE_TAXONOMY.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/specs/BIO_GOVERNANCE_TUPLE_TAXONOMY.md)
- [BIO_CONTROL_EXPERIMENT_MATRIX.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_CONTROL_EXPERIMENT_MATRIX.md)
- [BIO_PROTOCOLS.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_PROTOCOLS.md)
- [BIO_CASE_LOG_TEMPLATE.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_CASE_LOG_TEMPLATE.md)

## First Recommended Run

Start with:

- `Protocol 1: Session Fatigue Pacing`
- `AI_PROPOSE_HUMAN_CONFIRM`

Why:

- low risk
- easy to log
- easy to compare against a human-controlled baseline
- directly exercises the tuple chain

## Minimum Logging Standard

For each run, produce:

- one signal tuple
- one readiness or workload inference tuple
- one proposed adaptation tuple
- one authority tuple
- one outcome tuple

If anything goes wrong:

- add `BIO_ACTION_BLOCKED`, `BIO_OVERRIDE`, or `BIO_HARM_SIGNAL`

## Evidence Goal

The initial goal is not to prove a universal theory.

It is to answer:

- can these workflows be logged cleanly?
- do low-risk adaptations help often enough to justify the lane?
- where does governance add value?

## Confidence

High on this as a practical starting bundle.
