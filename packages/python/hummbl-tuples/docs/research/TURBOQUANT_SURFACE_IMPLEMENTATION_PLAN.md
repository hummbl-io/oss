# TurboQuant Surface Implementation Plan

Date: 2026-03-27
Status: draft

## Purpose

Lay out a staged implementation plan for a better TurboQuant-style surface.

## Stage 0: Research Lock

Deliverables:

- paper reading memo
- method decomposition
- baseline list
- target platform decision

Outputs:

- [TURBOQUANT_ACCESS_AND_IMPLEMENTATION_MEMO.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/TURBOQUANT_ACCESS_AND_IMPLEMENTATION_MEMO.md)
- this implementation plan

Exit condition:

- the method and target runtime are clear enough that coding will not thrash

## Stage 1: CPU Reference Core

Deliverables:

- vector encode path
- vector decode path
- approximate dot product
- config object
- unit tests

Recommended language:

- Python plus NumPy for the fastest research start

Alternative:

- Zig or C++ if the goal is implementation purity first

Recommendation:

- start in Python for correctness
- only optimize after the metrics and API stabilize

Exit condition:

- core functions produce repeatable outputs and can be benchmarked

## Stage 2: Benchmark Harness

Deliverables:

- distortion benchmark
- approximate-dot-product benchmark
- memory accounting
- runtime accounting
- CLI runner

Output format:

- machine-readable result files
- human-readable summary table

Exit condition:

- benchmark runs are repeatable and comparable across configs

## Stage 3: Tuple Logging

Deliverables:

- compression-config tuple
- benchmark-run tuple
- performance-evidence tuple
- degradation-signal tuple

Why:

- this is the HUMMBL-native differentiator
- it turns compression experiments into governed evidence

Exit condition:

- every benchmark run emits structured experiment artifacts

## Stage 4: Baseline Comparison

Deliverables:

- compare CPU reference against:
  - QJL baseline
  - naive scalar quantization baseline
  - one TurboQuant-style implementation path

Exit condition:

- you can say whether the new surface is faithful, competitive, or not yet ready

## Stage 5: First Adapter

Preferred first adapter:

- vector-search path

Why:

- lower friction
- easier benchmarking
- less runtime entanglement

Second adapter:

- `llama.cpp` or equivalent KV-cache integration

Exit condition:

- one real downstream consumer uses the surface without forking the core

## Stage 6: Windows-First Distribution

Deliverables:

- WSL2 setup doc
- reproducible environment
- smoke tests
- benchmark sample run

Rule:

- Windows-first means Windows users can actually run it, not just read about it

Exit condition:

- the Windows path is documented and tested

## Recommended Repo Split

### If Kept As Research

- keep the plan in `hummbl-tuples`

### If Promoted To Code

Create a dedicated private repo for the implementation surface.

Why:

- cleaner build tooling
- clearer ownership
- avoids mixing research docs and implementation churn

## Naming

Possible names:

- `turboquant-surface`
- `governed-compression`
- `traceable-quant`
- `hummbl-quant`

Best neutral name:

- `turboquant-surface`

Best HUMMBL-native name:

- `governed-compression`

## Confidence

High on the staged order. Medium on language choice because that depends on whether speed of research or systems polish matters more in the first month.
