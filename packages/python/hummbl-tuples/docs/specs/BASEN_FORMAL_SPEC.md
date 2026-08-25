# BaseN Formal Spec

Status: draft  
Scope: formal definition of BaseN as a governed reasoning-path system

See also:

- `docs/specs/BASEN_TUPLE_TAXONOMY.md`
- `docs/specs/REASONING_SEMANTICS.md`
- `docs/specs/HUMAN_CONTROL_GLOSSARY.md`

## 1. Purpose

Base120 is a curated reasoning profile.

BaseN is the generalized framework that emerged once the core idea was separated from the fixed `6 x 20 = 120` catalog:

- any number of transformations
- any number of mental models
- any number of protocol families
- explicit control over who chooses the path
- explicit evidence about what the path produced

BaseN is not defined by the number of transformations.

It is defined by governed path semantics.

## 2. Core Thesis

BaseN treats reasoning as an inspectable path through a governed operator space.

That path must preserve:

- what operators were available
- what operator was selected
- what alternatives were rejected
- who made the choice
- what evidence the path produced

## 3. Formal Objects

### 3.1 Problem

A `problem` is the object of reasoning.

Minimum fields:

- `problem_id`
- `problem_statement`
- `problem_class`
- `stakes_level`

### 3.2 Transformation

A `transformation` is a high-level reasoning operator class.

Examples:

- inversion
- perspective shift
- scientific method
- decomposition
- analogy

A transformation acts on a problem by changing the mode of reasoning.

### 3.3 Mental Model

A `mental_model` is a more specific operator specialization or heuristic frame within a transformation.

Examples:

- root-cause analysis under decomposition
- adversarial failure analysis under inversion
- falsification under scientific method

### 3.4 Protocol Family

A `protocol_family` is the structural template that governs the sequence and semantics of steps.

Examples:

- `PROTOCOL_TRACE`
- `RUBRIC_TRACE`
- `PATH_EVAL`
- `OVERRIDE_EVENT`

### 3.5 Reasoning Path

A `reasoning_path` is an ordered series of typed selections and executions over:

- transformations
- mental models
- protocol families
- control events

### 3.6 Control Mode

A `control_mode` defines who has authority over the path.

Allowed modes:

- `AI_AUTONOMOUS`
- `AI_PROPOSE_HUMAN_CONFIRM`
- `HITL_INFLUENCED`
- `HITL_CONTROLLED`
- `HOTL_SUPERVISED`

## 4. Layer Model

BaseN has three formal layers.

### 4.1 Registry Layer

Defines what can be chosen.

Includes:

- transformation registry
- mental model registry
- protocol registry
- rubric registry
- versioning metadata

### 4.2 Path Layer

Defines what was chosen.

Includes:

- candidate generation
- selection
- rejection
- override
- execution order

### 4.3 Evidence Layer

Defines what the chosen path produced.

Includes:

- outcome metrics
- path quality judgments
- transfer results
- failure modes
- human preference signals

## 5. Valid BaseN Run

A valid BaseN run must include:

- a declared problem
- a declared control mode
- registry versions
- at least one candidate or selected path event
- at least one evidence event or explicit failure marker

## 6. Operator Semantics

In BaseN:

- the transformation is the higher-order operator family
- the mental model is the operator specialization
- the problem and its evolving representations are the operands

This keeps BaseN from collapsing into a flat prompt catalog.

## 7. Distinctions

BaseN is not:

- just a prompt library
- just synthetic chain-of-thought
- just a governance log
- just a larger Base120

BaseN is:

- a governed reasoning-path substrate
- a mixed-control reasoning experiment surface
- an evidence-bearing path system

## 8. Minimal Strong Claim

BaseN is novel only if it preserves and evaluates reasoning-path structure in ways ordinary prompting, logging, or flat SFT do not.
