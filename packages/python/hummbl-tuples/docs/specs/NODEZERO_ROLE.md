# Nodezero Role

Status: draft  
Scope: nodezero as the meta-governor for BaseN reasoning experiments

## 1. Purpose

In the BaseN reasoning architecture, `nodezero` is not just a host.

It is the proposed coordination and governance layer above individual model sessions and desktops. Its role is to make reasoning-path experiments comparable, reproducible, and governable.

## 2. Why Nodezero Exists In This Design

Local model sessions can:

- propose transformations
- choose mental models
- execute reasoning paths
- emit evidence

But if each session uses different registries, different control assumptions, or different path semantics, the results are hard to compare.

`nodezero` solves this by acting as the authoritative issuer of:

- Base profile selection
- control regime
- registry versions
- experiment assignments
- path comparison and synthesis

## 3. Primary Responsibilities

### 3.1 Base Profile Authority

`nodezero` can issue the active Base profile for an experiment or session.

Examples:

- `Base120`
- `BaseN-small`
- `BaseN-medium`
- `BaseN-open`

### 3.2 Registry Pinning

`nodezero` can pin:

- transformation registry version
- mental model registry version
- evaluation rubric version

This keeps experiments comparable.

### 3.3 Control Mode Authority

`nodezero` can set the control regime:

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL_INFLUENCED`
- `HITL_CONTROLLED`
- `HOTL_SUPERVISED`

### 3.4 Experiment Assignment

`nodezero` can assign:

- problem
- run ID
- participant
- mode
- allowed surface

### 3.5 Path Comparison

`nodezero` can aggregate reasoning-path tuples from multiple runs and emit comparison tuples and summary evidence.

## 4. Conceptual Model

Local agents are path generators and executors.

`nodezero` is the path governor and comparison hub.

That means:

- local sessions create reasoning-path tuples
- `nodezero` creates governing tuples
- together they produce a full lifecycle record

## 5. Research Importance

This design enables a new question:

> Does a centralized meta-governor improve reasoning-path quality and comparability, or does it over-constrain discovery?

That is an empirical question, not just an architecture preference.

## 6. Candidate Nodezero Tuple Classes

- `BASE_PROFILE_ISSUED`
- `CONTROL_MODE_SET`
- `REGISTRY_VERSION_PINNED`
- `EXPERIMENT_RUN_ASSIGNED`
- `PATH_COMPARISON`

## 7. Initial Position

`nodezero` should be treated as a first-class research actor in HUMMBL’s BaseN experiments, because it determines whether reasoning-path comparisons are merely anecdotal or actually governed and reproducible.
