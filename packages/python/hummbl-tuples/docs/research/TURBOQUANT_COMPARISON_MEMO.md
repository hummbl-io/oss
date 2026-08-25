# TurboQuant Comparison Memo

Date: 2026-03-27
Status: draft

## Question

What currently available approaches are most comparable to TurboQuant, especially from NVIDIA and other major stacks?

## Bottom Line

The strongest practical comparison set is:

1. `TurboQuant`
2. `NVIDIA FP8 / NVFP4 KV cache`
3. `KIVI`
4. `KVQuant`
5. `AMD ROCm / vLLM FP8 KV cache`

These are not identical.

The clean split is:

- `TurboQuant`: paper-first research method for extreme vector and KV-cache compression
- `NVIDIA FP8 / NVFP4`: production-oriented vendor quantization surface
- `KIVI` and `KVQuant`: open research baselines for KV-cache compression
- `AMD ROCm / vLLM FP8`: deployment-oriented alternative path on non-NVIDIA hardware

## Comparison Table

| Approach | Type | Main Target | Strength | Weakness |
| --- | --- | --- | --- | --- |
| `TurboQuant` | research method | vector compression, KV cache | strongest novelty and compression story | weak implementation surface |
| `NVIDIA FP8` | vendor production feature | KV cache | mature deployment path | less novel, less extreme compression |
| `NVIDIA NVFP4` | vendor production feature | KV cache | strong long-context memory savings | tied to NVIDIA stack |
| `KIVI` | research method | 2-bit KV cache | very strong open baseline | not a broad implementation surface |
| `KVQuant` | open implementation | KV cache | practical baseline repo | narrower scope than a governed surface |
| `AMD FP8 via vLLM` | deployment path | KV cache | alternative hardware path | not a distinctive method like TurboQuant |

## TurboQuant

Official sources:

- Google Research blog  
  https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- paper  
  https://arxiv.org/abs/2504.19874

Best understood as:

- a research method
- not a product
- not a vendor-supported deployment layer

Main value:

- stronger compression narrative
- interesting theoretical and empirical claims
- useful for both vector search and KV cache

Main weakness:

- no official Google implementation surface
- fragmented open-source options

## NVIDIA FP8 And NVFP4

Official sources:

- TensorRT-LLM quantization docs  
  https://nvidia.github.io/TensorRT-LLM/1.2.0rc5/features/quantization.html
- TensorRT-LLM precision reference  
  https://nvidia.github.io/TensorRT-LLM/reference/precision.html
- NVFP4 KV cache blog  
  https://developer.nvidia.com/blog/optimizing-inference-for-long-context-and-large-batch-sizes-with-nvfp4-kv-cache/

Best understood as:

- practical inference engineering
- vendor-optimized KV-cache reduction
- stronger product surface than TurboQuant

Main value:

- deployability
- vendor support
- inference-stack integration

Main weakness:

- tied to NVIDIA ecosystem
- less interesting as a general research surface
- not the same kind of method as TurboQuant

## KIVI

Source:

- paper  
  https://arxiv.org/abs/2402.02750

Best understood as:

- a very strong open KV-cache research baseline
- especially relevant because it targets very low-bit KV compression directly

Main value:

- simple and important comparison point
- open paper-backed baseline

Main weakness:

- not a full implementation platform
- narrower than a broader governed compression surface

## KVQuant

Source:

- repo  
  https://github.com/SqueezeAILab/KVQuant

Best understood as:

- a practical open implementation baseline for KV quantization

Main value:

- concrete code
- useful for comparison and benchmarking

Main weakness:

- less conceptually broad than TurboQuant
- not built as a general governed experiment surface

## AMD ROCm / vLLM FP8 KV Cache

Source:

- ROCm inference optimization docs  
  https://rocmdocs.amd.com/en/develop/how-to/rocm-for-ai/inference-optimization/vllm-optimization.html

Best understood as:

- an alternative deployment path
- not a distinct research method comparable to TurboQuant in the same way KIVI is

Main value:

- non-NVIDIA deployment
- practical interest for Windows and Linux users on AMD hardware

Main weakness:

- mostly a platform path, not a method identity

## What This Means For You

If your goal is:

### Best Production Surface

Use NVIDIA FP8 / NVFP4 as the main comparison anchor.

### Best Open Research Baselines

Use:

- KIVI
- KVQuant
- QJL

### Best Opportunity To Build Something Better

Build the missing layer above all of them:

- a governed compression surface
- one benchmark harness
- one tuple logging model
- multiple method and backend comparisons

That is the real white space.

## Recommendation

When you frame the project, say:

- not "we implemented TurboQuant"
- but "we built a governed compression surface that can compare TurboQuant, vendor KV-cache quantization, and open low-bit baselines"

That is a much stronger and more durable framing.

## Confidence

High on NVIDIA as the strongest practical comparison. High on KIVI and KVQuant as the right open baseline set.
