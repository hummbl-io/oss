# Model Router v2: Full-Stack Correctness Routing

Issue: #570

Status: candidate primitive, source status `metadata_verified_transcript_pending`

## Claim Boundary

This is a router schema and benchmark draft, not adopted doctrine. The Sequoia / Training Data episode is treated as a source candidate until transcript notes and independent corroboration are attached. Do not quote or promote hardware/software co-design claims from the episode as verified HUMMBL doctrine.

## Primitive Candidate

`Full-Stack Correctness Routing` scores the full execution path before a route is selected:

> Cheapest correct model wins only after the model, runtime, kernel stack, hardware substrate, privacy boundary, latency class, energy profile, and audit receipt requirement are jointly acceptable.

This extends Model Router v2 beyond model-only selection. A route is a tuple:

```json
{
  "schema": "hummbl.model_router_v2.full_stack_correctness_route",
  "version": "0.1.0-candidate",
  "route_id": "public-claim-risk-triage.local-scan.small-model.v1",
  "task_id": "issue-588-wave4-claim-risk-retirement",
  "task_class": "public_surface_claim_review",
  "correctness_requirement": "high",
  "model_candidate": "local_open_weight_or_api_model",
  "architecture_family": "dense|moe|ssm|low_bit_native|multimodal|unknown",
  "runtime_affinity": "vllm|tensorrt_llm|llama_cpp|mlx|openvino|api_provider|browser|unknown",
  "kernel_stack": ["flash_attention", "paged_attention", "kv_cache", "quantization", "speculative_decoding", "sparse_attention"],
  "hardware_affinity": "apple_silicon|nvidia_cuda|cpu_only|cloud_gpu|tpu_api|edge_swap|unknown",
  "quality_per_dollar": "unknown|low|medium|high",
  "quality_per_watt": "unknown|low|medium|high",
  "correctness_score": 0.0,
  "correctness_threshold": 0.0,
  "latency_budget_ms": null,
  "estimated_cost_usd": 0.0,
  "estimated_energy_wh": null,
  "latency_class": "interactive|human_in_loop|batch|overnight|background",
  "privacy_boundary": "local_private|connector_scoped|public_safe|federal_sensitive|health_sensitive",
  "audit_receipt_requirement": "none|summary|full_trace|replayable_trace",
  "paid_fallback_policy": "forbidden_without_operator_ack",
  "evidence_refs": [],
  "rejection_reasons": [],
  "route_decision": "allow|defer|block|needs_benchmark"
}
```

Field semantics:

- `correctness_score` is route-local and cannot be compared across task classes unless the benchmark fixture and metric are identical.
- `correctness_threshold`, `latency_budget_ms`, `estimated_cost_usd`, and `estimated_energy_wh` are admission checks, not marketing claims.
- `evidence_refs` points to benchmark receipts, source bundles, or validation artifacts used for the route decision.
- `rejection_reasons` must be non-empty when `route_decision` is `defer`, `block`, or `needs_benchmark`.

## Scoring Gates

| Gate | Question | Blocks route when |
|---|---|---|
| Correctness | Can this model class satisfy the task risk? | Required reasoning, tool use, or domain reliability is below threshold. |
| Runtime fit | Does the runtime support the model and task shape without brittle glue? | Required kernels, context length, tool support, or streaming mode are missing. |
| Hardware fit | Does the substrate match latency, memory, and throughput needs? | VRAM/RAM, CPU, accelerator, or deployment boundary is incompatible. |
| Privacy | Can data stay inside the required boundary? | The route would move sensitive data into a broader provider/API boundary. |
| Cost | Is spend bounded and visible? | Route silently escalates to a paid API, cloud GPU, or long-running job. |
| Energy | Is the watt budget acceptable for the work class? | Local or cloud compute cost is disproportionate to task value. |
| Auditability | Can the route produce the required receipt? | No trace, replay, source bundle, or decision receipt can be produced. |
| Grindability | Can the task teach future routing safely? | Trace cannot be stored safely or replayed without leaking sensitive context. |

## Benchmark Plan

This is a benchmark plan, not completed benchmark evidence. Promotion requires receipts for at least one representative fixture per task class.

| Representative HUMMBL task | Fixture | Route A | Route B | Route C | Metrics | Admission threshold |
|---|---|---|---|---|---|---|
| Public claim-risk triage | Static queue report with known dispositions | CPU-only deterministic scan | Local open-weight classifier | API model with no private context | disposition accuracy, false-negative rate, reproducible manifest, cost | 0 unresolved unclassified candidates; false-negative rate acceptable to reviewer |
| Privacy-policy data-flow review | Assessment and scheduling flow map | Local grep/static scan | Long-context review over source bundle | Human/legal review packet | missed data touches, legal-boundary flags, receipt completeness | human/legal owner required before policy sufficiency claim |
| Runtime snippet validation | Public snippets inventory | Offline shell/browser validation | Auth-disabled integration harness | Provider/API route with explicit ack | pass/fail, auth-boundary violations, latency, cost | no credentialed/network route without explicit authorization |
| Source-packet novelty review | Source packet plus candidate schema | CPU/local extraction | Long-context source summarizer | Human novelty review | source coverage, hallucinated citations, schema completeness | no canon promotion from one model answer |
| Federal/security claim review | Public federal/security claim grep set | Local grep and manifest scan | Security-owner review packet | External validation only with owner proof | unsupported claim count, proof links, residual risk | block external validation claims without owner-approved evidence |
| High-volume artifact clustering | Artifact corpus with seed labels | CPU batch route | Local GPU/open-weight route | API embedding route with spend cap | cluster quality, energy, cost, replayability | traces exclude secrets; cost/energy within declared budget |
| Interactive operator triage | Live issue queue sample | Fast local model | API model with receipt summary | Human-only triage | latency, correctness, operator interruption rate, cost | paid fallback visible and ack-scoped |

Hardware comparison targets:

- Apple Silicon local route: MLX or llama.cpp where available.
- NVIDIA CUDA route: vLLM or TensorRT-LLM where available, using RTX 3080 Ti-class constraints as the initial local target.
- CPU-only route: deterministic scripts and small local models where latency class permits.
- API/provider route: only when privacy boundary and paid-fallback policy allow it.

## No-Silent-Paid-Fallback Policy

Routes must not silently escalate from local/free execution to paid API, paid cloud GPU, or provider-hosted long-context inference.

Required receipt fields:

```json
{
  "route_id": "public-claim-risk-triage.local.scan.v1",
  "selected_runtime": "local",
  "fallback_provider": null,
  "paid_fallback_available": true,
  "paid_fallback_used": false,
  "operator_ack_required_before_paid_fallback": true,
  "operator_ack_id": null,
  "operator_ack_scope": null,
  "operator_ack_expires_at": null,
  "max_spend_usd": 0.0,
  "fallback_reason": null,
  "estimated_cost_usd": 0.0
}
```

If a paid fallback is needed, the router must emit `needs_operator_ack` and stop before spend unless the operator has already authorized that route class. Prior authorization must be narrow: provider, task class, maximum spend, expiry, and privacy boundary must all be explicit in the receipt.

## Vocabulary Candidate

`hardware_software_codesign`

Definition candidate:

> A routing lens that evaluates model architecture, inference runtime, kernel stack, and hardware substrate as one decision surface instead of treating model choice as independent from execution cost, latency, privacy, and auditability.

Status: candidate vocabulary. Do not add to canonical glossary until transcript/source review and at least one empirical benchmark receipt exist.

## Integration With Grindability Gate

The co-design score runs before cost-only optimization and after basic safety/privacy gating:

1. Safety/privacy eligibility.
2. Full-stack correctness route score.
3. Grindability/learnability score.
4. Cost and latency tie-break.
5. Receipt emission.

This avoids the failure mode where a cheap route wins even though it cannot produce replayable evidence or runs on a runtime/hardware path that changes task behavior.

## Open Evidence Needed

- Transcript or bounded notes for the source episode.
- Independent corroboration for any broad hardware/software co-design claims.
- Local benchmark receipts from representative Apple Silicon, NVIDIA CUDA, and CPU-only routes.
- Route examples that prove paid fallback is explicit and auditable.
