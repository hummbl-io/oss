# Mental Models vs World Models

Date: 2026-03-27
Status: draft

## Question

How should HUMMBL relate `mental models` and `world models`?

## Bottom Line

They are not the same thing.

For HUMMBL, the cleanest distinction is:

- `mental models` are reasoning operators or interpretive lenses
- `world models` are stateful predictive representations of environments, actors, or dynamics

The strongest position is not to collapse one into the other. It is to make them composable.

## Evidence

### Mental models

Recent and adjacent literature keeps using `mental models` to mean internal interpretive structures that shape decision-making, leadership, and implementation.

Useful examples:

- `The impact of cognitive biases, mental models, and mindsets on leadership and change in the health system` (2024)  
  https://pubmed.ncbi.nlm.nih.gov/38010241/
- `An Organizational Case Study of Mental Models among Health System Leaders during Early-Stage Implementation of a Population Health Approach` (2024)  
  https://pubmed.ncbi.nlm.nih.gov/39430770/

These support the idea that mental models matter for:

- framing
- interpretation
- change
- leadership under complexity

### World models

Current AI work uses `world model` in a more predictive and planning-oriented sense.

Useful examples:

- `Embodied AI Agents: Modeling the World` (2025)  
  https://arxiv.org/abs/2506.22355
- `WorldPrediction: A Benchmark for High-level World Modeling and Long-horizon Procedural Planning` (2025)  
  https://arxiv.org/abs/2506.04363
- `SimuRA: Towards General Goal-Oriented Agent via Simulative Reasoning Architecture with LLM-Based World Model` (2025)  
  https://arxiv.org/abs/2507.23773

These support the idea that world models matter for:

- prediction
- planning
- simulation
- procedural reasoning over evolving states

### Local HUMMBL signal

Local HUMMBL material already hints at the distinction:

- Base120 is repeatedly described as a structured reasoning system of 120 mental models.
- separate founder-mode research notes already caution against claiming a fully realized hierarchical world model exists today.

Useful local anchors:

- [REASONING_SEMANTICS.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/specs/REASONING_SEMANTICS.md)
- [ambient_intelligence_reconciliation_2026-03-20.md](https://github.com/hummbl-io/oss)
- [R2_unified_world_models_bitter_lesson_2026.md](https://github.com/hummbl-io/oss)

## Recommended HUMMBL Position

### Base120 / BaseN

Treat Base120 and BaseN primarily as:

- mental-model systems
- reasoning-operator libraries
- explicit interpretive vocabularies

This is stronger and more defensible than calling them world models directly.

### World models in HUMMBL

Treat world models as a distinct layer that may include:

- environment state
- actor state
- task state
- memory and context
- predicted dynamics

This is closer to:

- RAG and retrieval state
- tool-grounded observations
- structured memory
- simulation/planning layers

## Practical Synthesis

The most useful architecture is probably:

- `mental models` choose how to reason
- `world models` represent what is currently believed about the world
- `tuples` record who chose the path, under what control regime, with what evidence

In that framing:

- Base120 is not the world model
- Base120 operates on the world model

## Why This Matters

This distinction avoids two mistakes:

1. overstating HUMMBL by claiming a full world-model capability where only reasoning structure exists
2. underselling HUMMBL by treating mental models as only generic prompts rather than operator families that can act over richer state representations

## Candidate Claim

HUMMBL may be strongest when positioned as:

- a governed mental-model layer for reasoning over partial world models

rather than:

- a world model by itself

## Open Question

Should HUMMBL eventually define typed tuples for world-model state, prediction, contradiction, and update?

That looks like a plausible next research direction, but it should remain distinct from the current mental-model and reasoning-path substrate.
