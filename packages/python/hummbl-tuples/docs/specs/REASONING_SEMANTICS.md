# Reasoning Semantics

Status: draft

This document defines the core reasoning terms used in HUMMBL Base120 and BaseN:

- transformation
- mental model
- operator
- operand

It uses both mathematical and linguistic senses where useful, but it prioritizes operational clarity for HUMMBL.

## 1. Base120 And BaseN

`Base120` is a curated reasoning profile.

- It contains a fixed, curated set of transformations.
- Each transformation contains a curated set of mental models.

`BaseN` is the generalized framework.

- It allows any number of transformations.
- It allows any number of mental models within each transformation.
- It separates the profile, registries, and control regime from any one fixed library.

## 2. Transformation

Definition:

- A transformation is a reasoning operator family.
- It changes how a problem is framed, decomposed, or advanced.

In HUMMBL terms:

- a transformation is not the raw content being reasoned about
- it is the mode of reasoning applied to that content

Examples of what a transformation might do:

- decompose a problem
- invert a perspective
- shift from diagnosis to synthesis
- move from generation to evaluation
- compress many options into a decision frame

Operational role:

- a transformation defines the broad reasoning move
- mental models then instantiate more specific logic inside that move

## 3. Mental Model

Definition:

- A mental model is a specific reasoning pattern, heuristic, lens, or structure used within a transformation.

In HUMMBL terms:

- the mental model is more specific than the transformation
- it provides the concrete logic the system uses to interpret or act on the problem

Examples of what a mental model might do:

- expose tradeoffs
- reveal bottlenecks
- force a counterfactual comparison
- distinguish signal from noise
- prioritize actions under uncertainty

Operational role:

- if the transformation sets the class of move, the mental model sets the detailed logic of the move

## 4. Operator And Operand In The Mathematical Sense

### Operator

In mathematics, an operator acts on something and produces a result.

For HUMMBL:

- a transformation is best understood as the primary reasoning operator
- a mental model is usually a subordinate operator or operator parameterization within the chosen transformation

### Operand

In mathematics, an operand is the thing the operator acts on.

For HUMMBL, likely operands include:

- the problem statement
- the current state representation
- the evidence set
- the intermediate reasoning trace
- the candidate action set

So in a simplified BaseN view:

- transformation = higher-level operator
- mental model = lower-level operator or operator specialization
- problem/evidence/state = operands

## 5. Operator And Operand In The Linguistic Sense

In linguistics or grammar, an operator often modifies the interpretation of an expression.

For HUMMBL:

- a transformation operates like a discourse-level operator on the problem frame
- a mental model operates like a semantic or pragmatic operator on interpretation and inference

Examples:

- a transformation may turn "what should we do?" into "what constrains what we can do?"
- a mental model may then turn that constrained question into "which bottleneck dominates outcomes?"

This is useful because HUMMBL reasoning is not only calculation. It is often reframing, emphasis, contrast, and interpretive control.

## 6. Recommended HUMMBL Position

Use this interpretation:

- transformations are the main reasoning operators
- mental models are specialized sub-operators inside transformations
- problems, evidence, state, and candidate actions are the main operands

Avoid saying:

- "mental models are only operands"

That is usually wrong in HUMMBL, because mental models themselves act on the problem frame and evidence.

More precise alternatives:

- mental models are operator specializations
- mental models are lower-level reasoning operators
- mental models are operator instances within a transformation family

## 7. Practical Mapping For Tuples

In BaseN tuples:

- `transformation_id` identifies the higher-level operator family
- `mental_model_id` identifies the lower-level operator or specialization
- `problem_id`, evidence references, state references, and path context identify the operands

This means a reasoning path records not just what was reasoned about, but what operators were applied to which operands, under which control regime.

## 8. Why This Matters

This distinction sharpens three things:

1. It keeps BaseN from collapsing into a flat list of prompts or heuristics.
2. It gives a principled way to compare transformations and mental models.
3. It makes tuple semantics more publishable because the reasoning path can be described in operator/operand terms rather than only product vocabulary.
