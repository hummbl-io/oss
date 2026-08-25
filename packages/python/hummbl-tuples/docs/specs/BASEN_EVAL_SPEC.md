# BaseN Eval Spec

Status: draft  
Scope: minimum evaluation packet required for BaseN claims

## 1. Purpose

BaseN should be judged on path quality and outcome quality, not just training loss.

## 2. Minimum Eval Packet

Every promoted BaseN-aligned artifact should include:

- pre-alignment baseline metric
- post-alignment metric
- held-out trace/task evaluation
- forgetting or regression check
- path-quality comparison
- qualitative sample review

## 3. Core Metric Families

### 3.1 Base Task Retention

Examples:

- TinyStories BPB before vs after alignment
- benchmark retention on the pretraining objective

### 3.2 Path Quality

Examples:

- step consistency
- protocol adherence
- human-rated coherence
- path usefulness
- error rate on held-out protocol tasks

### 3.3 Transfer

Examples:

- held-out tasks outside the generating corpus
- tasks where the correct protocol is not obvious

### 3.4 Failure Awareness

Examples:

- whether the aligned model avoids malformed paths
- whether it recognizes or repairs bad traces

## 4. Control-Regime Evaluation

BaseN is stronger if it can compare:

- AI-only path choice
- AI propose / human confirm
- HITL influenced
- HITL controlled
- HOTL supervised

These should be treated as first-class experiment axes.

## 5. Held-Out Set Requirements

Held-out eval should include:

- tasks not present in the training corpus
- at least one adversarial or protocol-confusion case
- at least one disagreement case where multiple paths are plausible

## 6. Promotion Rule

Do not promote a BaseN-aligned artifact based only on falling training loss.

Promotion requires:

- eval packet completed
- retention check completed
- at least one path-quality comparison completed

## 7. Immediate Application

The March 27 Windows alignment logs do not yet satisfy this spec.

They show optimization, not verified improvement.
