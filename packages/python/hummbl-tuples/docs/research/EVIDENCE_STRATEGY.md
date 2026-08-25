# Evidence Strategy

Status: draft

## Purpose

Define how HUMMBL gathers evidence for claims in the tuples, BaseN, reasoning-trace, and control-regime research program.

## Evidence Streams

### 1. Corpus Evidence

- papers
- reports
- standards
- official guidance

Use for:

- grounding concepts
- identifying prior art
- testing novelty claims

### 2. Artifact Evidence

- specs
- schemas
- examples
- validators
- code

Use for:

- showing that a concept is executable
- distinguishing real infrastructure from prose

### 3. Calibration Evidence

- gold sets
- manual scoring
- classifier comparisons
- inter-rater checks

Use for:

- validating rubrics
- validating classifiers
- measuring agreement and drift

### 4. Operational Evidence

- real runs
- case logs
- system traces
- intervention outcomes

Use for:

- testing whether the framework works in practice

### 5. Comparative Evidence

- A/B comparisons
- regime comparisons
- Base-level comparisons
- AI vs HITL vs HOTL comparisons

Use for:

- supporting empirical claims about what is better, when, and why

### 6. Negative Evidence

- failed hypotheses
- misclassifications
- harmful interventions
- useless traces

Use for:

- honesty
- refinement
- falsifiability

## Working Rule

Every important claim should eventually point to at least one of:

- source
- artifact
- experiment
- case log
- negative result

## Priority

Highest-value next evidence:

1. gold sets
2. case logs
3. comparative runs
4. negative-result capture
