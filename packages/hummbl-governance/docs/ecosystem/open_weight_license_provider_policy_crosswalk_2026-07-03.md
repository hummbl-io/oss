# Open-Weight License And Provider-Policy Crosswalk

Status: candidate research crosswalk
Date: 2026-07-03
Scope: `hummbl-io/hummbl-governance#157`
Related routing issues: `hummbl-io/hummbl-production#566`,
`hummbl-io/hummbl-governance#1189`, `hummbl-io/hummbl-governance#1125`

This document governs routing review for open-weight model candidates. It does
not approve production routing, client use, sensitive-data use, public claims,
provider spend, model deployment, release, CI, or canon promotion.

## Source Receipts

All source anchors were retrieved on 2026-07-03.

| Surface | Receipt URL | Use in this crosswalk |
|---|---|---|
| OpenRouter June 2026 open-weight article | https://openrouter.ai/blog/insights/the-open-weight-models-that-matter-june-2026/ | Seed list, model positioning, provider-policy caveats, and OpenRouter weighted-average context. |
| OpenRouter MCP announcement | https://openrouter.ai/blog/announcements/openrouter-mcp-server/ | Routing-tool context for live model/provider lookup; not production approval. |
| OpenRouter provider logging | https://openrouter.ai/docs/guides/privacy/provider-logging | Evidence that each OpenRouter endpoint has provider-specific data handling policy. |
| OpenRouter data collection | https://openrouter.ai/docs/guides/privacy/data-collection | Evidence that OpenRouter prompt retention is separately controlled from downstream provider policy. |
| OpenRouter provider routing | https://openrouter.ai/docs/guides/routing/provider-selection | Evidence that routing can change providers unless constrained. |
| OpenRouter terms | https://openrouter.ai/terms | Evidence that users remain responsible for business, legal, security, privacy, and compliance review. |
| DeepSeek V4 Flash model card | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | Weight availability and MIT license receipt. |
| GLM 5.2 model card | https://huggingface.co/zai-org/GLM-5.2 | Weight availability and MIT license receipt. |
| MiniMax M3 model card | https://huggingface.co/MiniMaxAI/MiniMax-M3 | Weight availability and model-card receipt. |
| MiniMax M3 license | https://huggingface.co/MiniMaxAI/MiniMax-M3/blob/main/LICENSE | MiniMax Community License receipt. |
| NVIDIA Nemotron 3 Ultra model card | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16 | Weight availability, model-card receipt, OpenMDW receipt, and commercial-use card statement. |

## Required Separation

Keep these axes separate in every routing decision:

1. model weights and model-card license;
2. model owner or first-party hosted policy;
3. third-party provider hosted policy;
4. OpenRouter routing/provider policy;
5. HUMMBL internal routing policy;
6. task sensitivity and data class.

Open weights do not imply acceptable hosted use. MIT weights do not imply a
no-train hosted endpoint. OpenRouter availability does not imply provider
equivalence across endpoints.

## Routing Status Vocabulary

- `allowed`: source receipts support the route and HUMMBL review approved it.
- `blocked`: source receipts or HUMMBL policy prohibit the route.
- `provisional`: candidate may be tested with stated constraints and receipts.
- `unknown`: missing license, provider, retention, region, or data-class proof;
  production is blocked until resolved or explicitly risk-accepted.

## Data Classes

| Data class | Description | Default posture |
|---|---|---|
| `public` | Public repo/docs/test prompts with no secrets, personal data, or client data. | May be provisional if license/provider receipts exist. |
| `internal` | HUMMBL private planning, internal docs, non-secret work context. | Requires no-train/no-retention or local route receipt. |
| `sensitive` | Secrets, credentials, personal data, private customer/client data, health/financial/legal context. | Block unless local or verified ZDR/no-retention route with explicit approval. |
| `regulated` | Export-controlled, medical, legal, financial, employment, insurance, child-safety, biometric, or jurisdiction-sensitive work. | Block pending human/legal/security approval. |

## Model And License Crosswalk

| Candidate | Weight availability | License receipt | Commercial status | Redistribution / derivative notes | Attribution / notice | Acceptable-use notes | First-party hosted policy | OpenRouter / third-party delta |
|---|---|---|---|---|---|---|---|---|
| DeepSeek V4 Flash | Hugging Face weights available. | MIT on model card. | MIT weights are permissive; hosted use still separate. | MIT license is permissive for weights/repo; verify files before redistribution. | MIT copyright/license notice. | Acceptable-use restrictions not established by this pass beyond license/source review. | OpenRouter article states first-party API retains and trains on data and routes through China. | Western/no-train hosts may exist, but each endpoint needs provider receipt. |
| GLM 5.2 | Hugging Face weights available. | MIT on model card. | MIT weights are permissive; hosted use still separate. | MIT license is permissive for weights/repo; verify files before redistribution. | MIT copyright/license notice. | Acceptable-use restrictions not established by this pass beyond license/source review. | First-party hosted policy not resolved in this pass. | OpenRouter/third-party endpoints require provider-specific data and region receipts. |
| MiniMax M3 | Hugging Face weights available. | MiniMax Community License. | Commercial use has conditions; larger commercial products require prior written authorization per license receipt. | Not a standard permissive license; derivatives and commercial products need license review. | License requires notice/attribution for commercial use. | Must review license before Ownward, client, or revenue use. | First-party hosted policy not resolved in this pass. | OpenRouter/third-party endpoints require provider-specific data and region receipts; license obligations still apply. |
| NVIDIA Nemotron 3 Ultra | Hugging Face weights available. | OpenMDW 1.1 via model card. | Model card states commercial and non-commercial use; OpenMDW terms still control. | Redistribution/derivative review must follow OpenMDW terms. | OpenMDW terms and NVIDIA model-card requirements must be preserved. | Model card describes high-stakes RAG/agentic workflows, but this is not HUMMBL approval for high-stakes use. | First-party hosted policy not resolved in this pass. | OpenRouter/third-party/free routes require provider-specific data, SLA, and region receipts. |

## Routing Matrix By Data Class

| Candidate route | Public | Internal | Sensitive | Regulated | Required receipt before use |
|---|---|---|---|---|---|
| DeepSeek V4 Flash local/self-host | provisional | provisional | provisional only after local security review | blocked | MIT license snapshot, model hash, local deployment receipt, data-class approval. |
| DeepSeek V4 Flash first-party API | provisional | blocked | blocked | blocked | First-party ToS/privacy receipt and explicit risk acceptance; OpenRouter article currently flags training/data route risk. |
| DeepSeek V4 Flash OpenRouter no-train provider | provisional | provisional | unknown | blocked | OpenRouter endpoint/provider receipt showing no training, retention, region, provider name, and route pinning. |
| GLM 5.2 local/self-host | provisional | provisional | provisional only after local security review | blocked | MIT license snapshot, model hash, local deployment receipt, data-class approval. |
| GLM 5.2 hosted provider | provisional | unknown | blocked | blocked | First-party or third-party provider data, retention, training, region, and acceptable-use receipt. |
| MiniMax M3 local/self-host | provisional | unknown | blocked | blocked | MiniMax Community License review, commercial notice/authorization status, model hash, local deployment receipt. |
| MiniMax M3 hosted provider | provisional | unknown | blocked | blocked | Provider data policy, MiniMax license compliance receipt, commercial notice/authorization status. |
| NVIDIA Nemotron 3 Ultra local/self-host | provisional | provisional | provisional only after local security review | blocked | OpenMDW review, model hash, local deployment receipt, data-class approval. |
| NVIDIA Nemotron 3 Ultra OpenRouter/free route | provisional | unknown | blocked | blocked | Provider-specific retention/training/region/SLA receipt; free route is not production SLA evidence. |

## Gates

- `G-WEIGHTS-NOT-POLICY`: open weights do not imply acceptable provider policy.
- `G-LICENSE-NOT-COMMERCIAL-SAFE`: license must be reviewed before commercial
  or client use.
- `G-PROVIDER-SPECIFIC`: each provider surface gets its own policy receipt.
- `G-SENSITIVE-DATA-CLASS`: sensitive routing depends on task/data class, not
  only model quality.
- `G-UNKNOWN-BLOCKS-PRODUCTION`: unknown license/policy fields block production
  until resolved or explicitly risk-accepted.
- `G-CITABLE-RECEIPTS`: each claim links to a preserved source receipt.

## Required Route Receipt

Before any route leaves evaluation, record:

1. model slug and version;
2. weight source and hash or hosted endpoint ID;
3. license name and retrieval URL;
4. provider name and country/region posture;
5. training-on-user-data policy;
6. prompt/completion retention policy;
7. sensitive-data status;
8. commercial-use status;
9. redistribution/derivative restrictions;
10. attribution or notice requirements;
11. OpenRouter routing controls if applicable;
12. task/data class;
13. reviewer and approval/risk-acceptance receipt;
14. next review date.

## Do Not Infer

- MIT license on weights means first-party hosted use is no-train or
  privacy-preserving.
- Community-license weights are safe for Ownward, client, or revenue use.
- U.S.-based provider posture makes every model/data class acceptable.
- OpenRouter availability means provider-policy equivalence across endpoints.
- Free routes are production SLA evidence.
- Provider no-train claims remove HUMMBL data-class review.

## Recommendation

Use these models only as evaluated candidates until route receipts are complete.

- Best low-risk starting point: local/self-host evaluation with public or
  non-sensitive internal prompts, model hashes, and license snapshots.
- Best OpenRouter pattern: pin providers and require no-training/no-retention
  and region receipts per endpoint; do not rely on default routing.
- Production posture: `unknown` blocks production for every route until license,
  provider, retention, region, and task data class are all resolved.
- Sensitive or regulated posture: blocked unless separately approved with local
  deployment or verified no-retention/provider route plus human/legal/security
  review.

## Next Gate

Review this crosswalk for `hummbl-governance#157`, then feed explicit route
statuses into `hummbl-production#566` and `hummbl-governance#1189`. Any live router
change, provider spend, endpoint pin, public claim, sensitive-data use, client
use, release, or canon promotion requires a separate human-approved PR.
