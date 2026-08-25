# Bio Goldset V0

Date: 2026-03-27
Status: draft

## Purpose

Create a small manual reference set for early bio-cognitive and bio-governance calibration.

## Cases

### Case 1

- name: low-fatigue research block
- expected control mode: `HUMAN_CONTROLLED`
- expected adaptation: none or optional break prompt
- expected risk: low

### Case 2

- name: moderate fatigue long writing block
- expected control mode: `AI_PROPOSE_HUMAN_CONFIRM`
- expected adaptation: break prompt or lower interface density
- expected risk: low

### Case 3

- name: overload during coordination session
- expected control mode: `HOTL`
- expected adaptation: notification throttling
- expected risk: moderate

### Case 4

- name: weak-signal false positive
- expected control mode: `AI_PROPOSE_HUMAN_CONFIRM`
- expected adaptation: blocked or overridden
- expected risk: low but noisy

### Case 5

- name: adaptation harms flow
- expected control mode: `HOTL`
- expected adaptation: overridden after annoyance or disruption
- expected risk: moderate

### Case 6

- name: high-strain signal with insufficient evidence
- expected control mode: `HUMAN_CONTROLLED`
- expected adaptation: no automatic action
- expected risk: high uncertainty

## What To Add Next

- canonical tuple chain per case
- expected acceptance or override behavior
- expected outcome notes
- one real logged case mapped back to this set
