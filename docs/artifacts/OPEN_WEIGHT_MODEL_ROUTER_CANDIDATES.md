# Open-Weight Model Router Candidates (Draft)

**Status:** candidate registry for issue `#566`  
**Scope:** routing candidate set only; not a performance or safety claim  
**Canon status:** candidate, not canonized  
**Last reviewed:** 2026-07-03

## Objective

Capture a bounded routing candidate list for June 2026 open-weight models so routing experiments
can distinguish between candidate support, provider policy constraints, and production approval needs.

This is an internal candidate register, not a public commercial or certification statement.

## Candidate model entries

| Model | model_id | provider_surface | open_weight_status | release_date | context_window | parameter_profile | recommended_lanes | non_goals | sensitivity_allowed | provider_policy_required | no_train_required_available | region_allowed | cost_profile | latency_profile | eval_status | receipt_refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | `deepseek-v4-flash` | OpenRouter + upstream host | `yes` | `2026-06` | `unknown (issue-scoped)` | `open-weight`, family profile not yet normalized | `low-cost coding`, `safe test loops`, `router baseline experiments` | `no production autonomy`, `no sensitive-domain final claims` | `internal`, `regulated with explicit routing boundary` | `required` | `not automatic; consent + policy review first` | `US-first + region checks` | `low` | `low-to-medium` | `source-only packet drafted; no live benchmark` | `docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md` |
| GLM 5.2 | `glm-5-2` | OpenRouter + upstream host | `yes` | `2026-06` | `unknown (issue-scoped)` | `large` | `repo-scale planning`, `longer-context coding`, `architecture-to-implementation` | `no regulated production`, `no safety-critical medical/legal claims` | `internal`, `public-safe` | `required` | `not automatic; human ack` | `US-first + region checks` | `medium` | `medium` | `candidate only` | `docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md` |
| MiniMax M3 | `minimax-m3` | OpenRouter + upstream host | `yes` | `2026-06` | `unknown (issue-scoped)` | `open multi-modal route candidate` | `multimodal reasoning`, `UI/document review`, `long context review` | `no medical/financial legal judgement` | `context-specific`, `public-safe` | `required` | `not automatic; consent + governance` | `US + select partners` | `medium-to-high` | `medium-to-high` | `candidate only` | `docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md` |
| NVIDIA Nemotron 3 Ultra | `nemotron-3-ultra` | OpenRouter + upstream host | `yes` | `2026-06` | `unknown (issue-scoped)` | `very large` | `enterprise-style routing experiments`, `batch eval for heavy-context tasks` | `no local-only production claim`, `no guaranteed enterprise parity` | `internal`, `enterprise gating required` | `required` | `not automatic; enterprise policy required` | `US + enterprise region policy` | `high` | `high` | `candidate only` | `docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md` |

## Cross-model routing constraints

- No model from this list may be used for medical, legal, or high-risk security claims
  without explicit operator/legal/operations routing.
- No model from this list may be routed without policy checks when sensitive data is present.
- No paid fallback may be implicit; all fallback paths require operator acknowledgment when
  sensitivity or spend changes the trust boundary.

## Field definitions

- `provider_surface`: source surface and access mechanism.
- `open_weight_status`: public, open-weight status from source packet.
- `license`: legal/commercial constraint pending provider policy read.
- `no_train_required_available`: whether there is a no-training-by-default posture available.
- `eval_status`: whether HUMBL-specific eval fixtures exist.
- `receipt_refs`: canonical evidence path for future migration.

## Do not infer

- This draft does not assert that any candidate outperforms others.
- This draft does not claim model capability for high-stakes or regulated output.
- This draft does not approve production routing without explicit governance tests.
- This draft does not assert that open-weight status alone satisfies privacy, cost, or legal boundaries.
