# TurboQuant Repo Decision

Date: 2026-03-27
Status: draft

## Decision

Use a dedicated private implementation repo rather than building the code directly inside `hummbl-tuples`.

## Recommended Repo Name

Primary recommendation:

- `governed-compression`

Why:

- broader than one paper
- aligns with the HUMMBL thesis
- leaves room for TurboQuant, QJL, and later methods
- emphasizes experiment logging and evidence, not just compression kernels

Secondary option:

- `turboquant-surface`

Why:

- clearest short-term research framing
- tightly aligned to the immediate method target

Why it is second choice:

- too narrow if the repo grows into a broader governed quantization surface

## Recommended First Stack

### Language Split

- `Python` for the research/control plane
- `NumPy` for the CPU reference core
- optional `PyTorch` only if it materially speeds evaluation
- `C++` or `CUDA` later for acceleration

### Why

- fastest correctness loop
- easiest benchmarking
- easiest tuple logging integration
- easiest Windows via WSL2 path

### Avoid First

- Zig-first
- full native Windows CUDA-first
- full `llama.cpp` fork-first

Those are better as stage-two or stage-three moves.

## Recommended Platform Target

1. Windows via WSL2
2. Linux
3. macOS

This keeps the first implementation aligned with your actual working machine while avoiding needless native-Windows build friction.

## MVP Build Order

1. Python package scaffold
2. CPU reference encode / decode
3. approximate dot product benchmark
4. tuple-based experiment logging
5. QJL comparison harness
6. vector-search adapter

Only after that:

7. KV-cache adapter
8. accelerated backend

## Suggested Initial Layout

```text
governed-compression/
  pyproject.toml
  README.md
  governed_compression/
    core/
    bench/
    logging/
    adapters/
  examples/
  tests/
  docs/
```

## First Three Issues

### Issue 1

Bootstrap repo and benchmark contract

### Issue 2

Implement CPU reference compression path with config object

### Issue 3

Add distortion and approximate-dot-product benchmark runner with tuple logging

## Working Rule

Optimize for:

- reproducibility
- comparability
- Windows-first usability

Do not optimize first for:

- maximum kernel performance
- broad runtime integration
- paper-complete feature coverage

## Bottom Line

The cleanest first move is:

- create a private repo named `governed-compression`
- implement a Python plus NumPy reference surface
- target Windows via WSL2
- and make tuple logging part of the repo from day one
