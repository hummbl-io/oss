# TurboQuant Surface MVP

Date: 2026-03-27
Status: draft

## Purpose

Define the smallest implementation scope that is worth building.

## Bottom Line

Do not start with a full inference fork.

Start with:

1. a vector-compression core
2. a benchmark harness
3. one backend
4. one adapter
5. tuple-based experiment logging

## MVP Scope

### In Scope

- CPU reference implementation
- encode / decode API
- approximate dot product
- configurable bit budgets
- distortion metrics
- retrieval-style benchmark
- one runtime-facing prototype adapter
- experiment logging

### Out Of Scope

- multi-runtime production integration
- full training-time support
- broad GUI surface
- many backends at once
- upstreaming into multiple inference projects

## MVP Components

### 1. CPU Reference Core

Why:

- easiest to validate
- simplest correctness baseline
- easiest to test on Windows

### 2. Retrieval And Vector Benchmarks

Why:

- lower friction than KV-cache integration
- still exercises the core claims
- easier to compare across implementations

### 3. Optional First Adapter

Best first adapter:

- vector search

Second-best:

- `llama.cpp` KV-cache path

The vector-search adapter should come first because it reduces integration overhead while still proving the surface.

### 4. Tuple Logging

Log at least:

- compression config
- backend
- dataset
- benchmark type
- distortion result
- latency result
- memory result

## Success Criteria

The MVP is successful if it can:

1. compress vectors with reproducible config
2. benchmark distortion and approximate dot-product quality
3. run on Windows via WSL2
4. compare at least one baseline against one improved method
5. log every run in a structured way

## Failure Criteria

The MVP is failing if it:

- becomes an inference-fork project too early
- depends on one fragile backend
- cannot produce reproducible benchmark outputs
- or cannot be run by a technically capable Windows user without heroic setup

## Recommended Order

1. CPU reference core
2. vector benchmark harness
3. tuple logging
4. QJL baseline comparison
5. only then runtime adapter exploration

## Confidence

High on this as the right narrow starting scope.
