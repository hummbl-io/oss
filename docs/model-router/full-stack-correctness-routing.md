# Model Router v2: Hardware/Runtime/Model Co-Design Scoring

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #570
- **Source:** Sequoia / Training Data episode: "Why Hardware-Software Co-Design Is AI's Real 100x: Dylan Patel of SemiAnalysis"
- **Source status:** `metadata_verified_transcript_pending`
- **Provisional name:** `Full-Stack Correctness Routing` (until audited)

## Purpose

A routing discipline where the selected model, runtime, hardware, context boundary, and governance mode are jointly optimized for correctness, cost, latency, privacy, energy, and auditability.

## Core Finding

Model selection is insufficient by itself. Routing needs to jointly evaluate:
- Model architecture
- Kernels/runtime
- Hardware substrate
- Task shape
- Privacy boundary
- Latency
- Cost
- Energy
- Correctness

## Scoring Dimensions

| Dimension | Description | Values |
|-----------|-------------|--------|
| `task_class` | Classification of the task | code_generation, summarization, reasoning, classification, embedding, multimodal_analysis |
| `correctness_requirement` | Required correctness level | low, medium, high, critical |
| `model_candidate` | Selected model identifier | string |
| `architecture_family` | Model architecture | dense, sparse_moe, ssm, low_bit_native, multimodal, hybrid |
| `runtime_affinity` | Runtime/framework | vllm, tensorrt_llm, llama_cpp_ggml, mlx, openvino, api_provider, custom |
| `kernel_stack` | Kernel optimizations | flash_attention, paged_attention_kv_cache, quantization_kernels, speculative_decoding, sparse_attention, none |
| `hardware_affinity` | Hardware target | apple_silicon, nvidia_cuda, cpu_only, cloud_gpu, tpu_api, edge_swap |
| `quality_per_dollar` | Quality score per dollar | number (higher is better) |
| `quality_per_watt` | Quality score per watt | number (higher is better) |
| `latency_class` | Latency requirement | interactive, batch, overnight, background, human_in_loop |
| `privacy_boundary` | Privacy constraint | local_private, connector_scoped, public_safe, federal_defense_sensitive, health_sensitive |
| `audit_receipt_requirement` | Audit requirement | none, summary, full_trace, cryptographic |
| `governance_mode` | Governance mode | autonomous, supervised, human_command, quarantined |

## No-Silent-Paid-Fallback Policy

When `no_silent_paid_fallback` is true, no paid API fallback is allowed without explicit approval. This prevents silent cost escalation when a local model fails or degrades.

**Rationale:** Without this policy, a routing system might silently fall back to a paid API when a local model is slow or produces lower-quality output. This creates unexpected costs and undermines the privacy boundary (local → cloud).

## Benchmark Matrix

| Task class | Correctness | Hardware | Runtime | Privacy | Latency |
|------------|-------------|----------|---------|---------|---------|
| code_generation | high | nvidia_cuda | vllm | local_private | interactive |
| summarization | medium | cloud_gpu | api_provider | public_safe | interactive |
| reasoning | critical | apple_silicon | llama_cpp_ggml | local_private | human_in_loop |
| classification | low | cpu_only | openvino | local_private | batch |
| embedding | medium | apple_silicon | mlx | local_private | batch |
| multimodal_analysis | high | nvidia_cuda | vllm | connector_scoped | interactive |

## Fixtures

| Fixture | Description |
|---------|-------------|
| `valid_local_code_routing.json` | Local code generation on NVIDIA CUDA with vLLM |
| `valid_api_summarization_routing.json` | API-based summarization (public-safe) |
| `valid_critical_reasoning_routing.json` | Critical reasoning on Apple Silicon with human-in-loop |

## Vocabulary Candidate

`hardware_software_codesign` — provisional term until audited. Describes the joint optimization of model, runtime, and hardware for a given task.

## Guardrails

- Do not represent podcast claims as independently verified until transcript and independent corroboration exist
- Treat new HUMMBL/BaseN terms as candidates until audited
- Prefer empirical receipts from local Mac mini + RTX 3080 Ti tests before promotion

## Do Not Infer

- Do not infer that the podcast source is independently verified
- Do not infer that `Full-Stack Correctness Routing` is canon HUMMBL terminology
- Do not infer that the benchmark matrix is empirically validated
- Do not infer that the scoring dimensions are final
- Do not infer that any model named in fixtures is endorsed

## Non-goals

- Not a production routing implementation
- Not a claim of empirical validation
- Not a final vocabulary decision
