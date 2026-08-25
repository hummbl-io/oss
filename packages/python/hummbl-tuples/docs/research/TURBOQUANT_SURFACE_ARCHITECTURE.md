# TurboQuant Surface Architecture

Date: 2026-03-27
Status: draft

## Purpose

Describe a better implementation surface for TurboQuant-style compression than the current fragmented reference landscape.

## Problem

The current surface is split across:

- the Google paper and blog
- the adjacent official `QJL` repo
- small third-party implementations
- experimental inference forks

That is enough to study the method, but not enough to make it easy to:

- benchmark fairly
- compare backends
- plug into inference runtimes
- run on Windows or WSL cleanly
- or govern compression choices with reproducible evidence

## Design Thesis

Build one clean compression research surface with:

- one core API
- multiple backends
- one benchmark harness
- thin runtime adapters
- and tuple-based experiment logging

## Target Layers

### 1. Core Compression Library

Responsibilities:

- vector encode
- vector decode
- approximate dot product
- residual correction
- bit-budget configuration
- shape and dtype validation

Suggested modules:

- `core/rotation`
- `core/quantization`
- `core/residual`
- `core/metrics`
- `core/config`

### 2. Backend Layer

Responsibilities:

- pure CPU reference path
- accelerated CUDA path
- optional Metal path later

Suggested modules:

- `backends/cpu`
- `backends/cuda`
- `backends/metal`

Rule:

- every accelerated backend must be comparable against the CPU reference path

### 3. Runtime Adapter Layer

Responsibilities:

- integrate with inference or retrieval systems without polluting the core

Suggested adapters:

- `adapters/llama_cpp`
- `adapters/hf_kv_cache`
- `adapters/vector_search`

Rule:

- adapters should be thin and reversible

### 4. Benchmark Harness

Responsibilities:

- distortion measurement
- approximate-dot-product quality
- retrieval recall
- KV-cache task degradation
- memory savings
- latency impact

Suggested modules:

- `bench/vector_distortion`
- `bench/retrieval`
- `bench/kv_cache`
- `bench/system`

### 5. Governance And Trace Layer

Responsibilities:

- record compression settings
- benchmark runs
- observed degradation
- backend choice
- platform choice

This is the main way to surpass the current public surfaces.

Compression becomes:

- measurable
- comparable
- reproducible
- and governable

## Suggested Project Shape

```text
turboquant-surface/
  core/
  backends/
  adapters/
  bench/
  examples/
  schemas/
  docs/
  scripts/
```

## Interface Principles

- config-first API
- same benchmark inputs across backends
- explicit quality/latency/memory tradeoff reporting
- reproducible result capture
- no hidden backend magic

## Platform Priorities

1. Windows via WSL2
2. Linux
3. macOS

Rationale:

- Windows is likely the most important practical user environment here
- WSL2 is a better first target than native Windows CUDA complexity

## HUMMBL Advantage

The differentiator is not just implementation.

It is:

- tuple-based experiment tracking
- governed compression selection
- comparable operator-facing evidence
- and the ability to connect compression choices to downstream reasoning quality

## Confidence

High on this architecture shape for an MVP-to-production research surface.
