# HUMMBL API Reference

**HUMMBL** = **H**ighly **U**seful **M**ental **M**odel **B**ase **L**anguage.

Base URL: `https://api.hummbl.io`
OpenAPI spec: [`api/openapi.yaml`](https://github.com/hummbl-io/oss)
MCP server: `npm install -g @hummbl/mcp-server`

HUMMBL APIs are organized into four families plus a resources layer. Every
request flows through edge safety middleware (CAES validation + kill switch),
error sanitization, and governance proof generation. Fail-closed on safety
engine errors.

## Authentication

| Scheme        | Header                                   | Scope                                                                                                   |
| ------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `ApiKey`      | `X-API-Key` (or `Authorization: Bearer`) | Tiered (free / pro / enterprise) for `/v1/*` endpoints                                                  |
| `AdminApiKey` | `X-API-Key`                              | Admin-gated surfaces: `/security/*`, `/metrics/*`, `/analytics/*`, `/agents/*`, `/tasks/*`, `/safety/*` |

Anonymous calls to `/v1/*` are allowed at free-tier IP rate limits (100
req/min). `POST /v1/validate` is fully public. Admin endpoints fail-closed
(503) when `ADMIN_API_KEY` is not configured.

## Rate limiting

100 requests / minute per client IP (in-memory + KV write-through). 1 MB max
request body. 429 on exceedance.

---

## HUMMBL Governed APIs (HGA)

The core reasoning surface: 120 governed mental models with semantic search,
recommendation, and multi-step workflow matching.

### Mental Models API

Programmable access to the full Base120 mental model catalog and transformations.

#### `GET /v1/models`

List all 120 Base120 mental models.

- Auth: `ApiKey` (anonymous allowed at free tier)
- Response `200`: `{ success, count, data: Model[] }`
- `403` CAES validation failed / insufficient tier · `503` kill switch engaged

#### `GET /v1/models/{code}`

Get a single model by code.

- Path: `code` (string, e.g. `P01`, `DE05`, `SY18`)
- Response `200`: `{ success, data: Model }` · `404` not found

#### `GET /v1/transformations`

List all model transformations.

- Response `200`: `{ success, count, data: object[] }`

**Model schema:** `{ code, name, family (P|IN|CO|DE|RE|SY), family_name, description, when_to_use, examples[] }`

### Recommendation API

#### `POST /v1/recommend`

Get the mental models most relevant to a problem.

- Auth: `ApiKey`
- Body: `{ problem: string (required), limit?: int (default five; max 20) }`
- Response `200`: `{ success, data: Recommendation[], count, algorithm }`
- `400` invalid input · `403` CAES failed · `503` kill switch

**Recommendation schema:** `{ code, name, relevance_score, reason }`

### Semantic Search API

#### `POST /v1/semantic-search`

3-tier search: Workers AI + Vectorize -> D1 cosine similarity -> BM25 keyword
fallback. Always returns results; check `meta.source` for which tier served
the response.

- Auth: `ApiKey`
- Body: `{ query: string (required), limit?: int (default 10, max 20) }`
- Response `200`: matched models (from `vectorize`, `d1-cosine`, or
  `bm25-fallback`) · `400` invalid input

### Workflows API

#### `GET /v1/workflows`

List all reasoning workflows. Response `200`: `{ success, data: Workflow[], count }`

#### `GET /v1/workflows/{id}`

Get a specific workflow. `200` details · `404` not found

#### `POST /v1/workflows/match`

Match workflows to a problem.

- Body: `{ problem: string (required), limit?: int (default 3) }`
- Response `200` matched workflows · `400` invalid input

**Workflow schema:** `{ id, name, description, steps[] }`

### Validation API

#### `POST /v1/validate`

Public text validation and sanitization with PII detection. No API key
required.

- Body: `{ input: string (required) }`
- Response `200`: `{ success, validation, sanitized, pii }` · `400` invalid body

---

## Compliance &amp; Assessment APIs

### Compliance Analysis API

Score governance evidence against the EU AI Act.

#### `POST /v1/compliance/analyze`

- Body: `{ system_name (required), system_description?, risk_level?: minimal|limited|high|unacceptable, governance_evidence: { risk_management, data_governance, transparency, human_oversight, accuracy, post_market, record_keeping } }`
- Response `200`: `{ success, system_name, overall_score (0-100), grade (A-F), risk_level, article_scores[], critical_gaps[], recommendations[], estimated_remediation_effort, disclaimer, analyzed_at }` · `400` invalid request

#### `GET /v1/compliance/frameworks`

List supported compliance frameworks. Response `200`: `{ success, frameworks[] }`
where each framework is `{ id, name, reference, status, annex_iii_enforcement, articles_mapped[] }`

#### `GET /v1/compliance/articles/{framework}`

Get article definitions for a framework (e.g. `eu_ai_act`).
Response `200`: `{ success, framework, articles[] }` · `404` framework not supported

### Assessment API

Capture AI governance assessments and drive the nurture + scorecard checkout
loop. Public (no admin auth).

#### `POST /assessment/capture`

Receive assessment results + email; sends Email 1 and queues Email 2 (day 3)
and Email 3 (day seven) in KV.

- Body: `{ email, grade, score, categories: { risk, transparency, oversight, data, agent, compliance }, top_gaps[] }`
- Response `200`: capture receipt · `400` invalid body

#### `POST /assessment/process-queue`

Cron-triggered: sends due Email 2 / Email 3 from the KV queue.

#### `POST /assessment/checkout`

Initiate Stripe checkout for a scorecard purchase.

#### `POST /assessment/calcom-webhook`

Cal.com booking webhook for assessment scheduling.

#### `POST /assessment/reports/request-access-link`

Request a time-limited access link to a report.

#### `GET /assessment/reports/access`

Redeem a report access link.

---

## Agent Control Plane APIs

Admin-gated. Operate a fleet of agents: heartbeat registration, tiered API key
management, and a priority task queue with long-polling.

### Agent Registry API

#### `POST /agents/heartbeat`

Agent phone-home. Body: `AgentHeartbeat` (must include `agentId`, alphanumeric

- hyphens + underscores, 1-64 chars). Response `200`: `{ success, received }`

#### `GET /agents/status`

All agent statuses.

#### `POST /agents/api-keys`

Create a new API key (shown once).

- Body: `{ name (required), tier?: free|pro|enterprise (default free), email? }`
- Response `200`: `{ success, key, id, prefix, tier, limits }`

#### `GET /agents/api-keys`

List all API keys without secrets. Response `200`: `{ success, count, data[] }`

#### `DELETE /agents/api-keys/{id}`

Revoke an API key. `200` revoked · `404` not found or already revoked

### Task Queue API

#### `POST /tasks/enqueue`

Submit a task to the queue.

- Body: `{ type (required), payload?: object, priority?: int (default five), maxRetries?: int (default 3), timeoutMs?: int (default 120000) }`
- Response `200`: `{ success, task }`

#### `GET /tasks/poll`

Long-poll for the next task (agent calls this).

#### `POST /tasks/:id/complete`

Mark a task done.

#### `GET /tasks/stats`

Queue stats for the dashboard.

---

## Safety &amp; Observability APIs

Admin-gated operational spine.

### Safety API

#### `GET /safety/kill-switch`

Current kill switch state. Response `200`: `{ state: DISENGAGED|HALT_NONCRITICAL|HALT_ALL|EMERGENCY, last_updated, reason }`

#### `POST /safety/kill-switch`

Update kill switch state.

- Body: `{ state (required), reason? }`
- Response `200` updated · `400` invalid state · `401` unauthorized

#### `GET /safety/governance-proofs`

List recent governance proofs.

- Query: `limit?` (default 50, max 500), `path?` (filter by API path)
- Response `200`: `{ count, proofs: GovernanceProof[] }`

**GovernanceProof schema:** `{ timestamp, path, method, clientIp, userAgent, safetyValidated }`

### Security API

#### `POST /security/validate`

Dual-mode: `{ operation, agent_id?, context? }` -> Arbiter governance decision
(Open Brain); `{ input }` -> legacy text injection / PII check.

- Body (governance): `{ operation (required), agent_id (required), context? }`
- Response `200`: `{ verdict: ALLOW|WARN|BLOCK, score, reason }`

#### `GET /security/events`

Security event log. Query: `type?`, `severity?` (LOW|MEDIUM|HIGH|CRITICAL),
`agent_id?`, `limit?` (default 100). Response `200`: `{ success, count, events[] }`

#### `GET /security/stats`

Security statistics. Response `200`: `{ success, stats }`

### Observability API

#### `GET /`

API info and endpoint directory.

#### `GET /health`

System health: `{ status: healthy|degraded|critical, version, timestamp, uptime_ms, models_count, rate_limit_status, security, reliability, alerts? }`

#### `GET /metrics`

Detailed request metrics and alerts. Response `200`: `{ success, timestamp, metrics, alerts[] }`

#### `GET /metrics/errors`

Recent errors. Query: `limit?` (default 50). Response `200`: `{ success, count, errors[] }`

#### `GET /metrics/slow`

Slow requests. Query: `threshold?` ms (default 1000), `limit?` (default 50).
Response `200`: `{ success, threshold_ms, count, requests[] }`

#### `GET /analytics`

Usage analytics summary. Response `200`: `{ success, timestamp, ...summary }` · `503` not configured

#### `POST /analytics/event`

Lightweight funnel event tracking (no PII). Body: `{ event: string }`
(alphanumeric + hyphens + underscores, max 64). Response `200`: `{ success }`

#### `GET /analytics/funnel`

Funnel stats for the assessment / report loop across a 7-day window.
Response `200`: `{ success, stats }`

---

## Resources

### Webhooks

Inbound webhook handlers for external service integrations.

#### `POST /webhooks/cal`

Cal.com booking webhook. Sends a booking alert email via Resend. Verified
via `CAL_WEBHOOK_SECRET`.

#### `POST /webhooks/stripe`

Stripe payment webhook. 5-minute timestamp tolerance, 1 MB max payload.
Verified via `STRIPE_WEBHOOK_SECRET`.

#### `POST /webhooks/resend`

Resend delivery webhook. Verified via `RESEND_WEBHOOK_SECRET`.

### Error codes

All errors return a sanitized `ErrorResponse` (no internal details):

```json
{ "success": false, "error": "<sanitized message>", "code": "<code>" }
```

| `code`                   | Meaning                                 |
| ------------------------ | --------------------------------------- |
| `INTERNAL_ERROR`         | Unexpected server error                 |
| `EXTERNAL_SERVICE_ERROR` | Upstream dependency failure             |
| `REQUEST_ERROR`          | Malformed request                       |
| `CAES_VALIDATION_FAILED` | Edge safety CAES validation failed      |
| `KILL_SWITCH_ENGAGED`    | Kill switch is halting traffic          |
| `SAFETY_ENGINE_ERROR`    | Safety engine unavailable (fail-closed) |
| `INSUFFICIENT_TIER`      | API key tier too low for endpoint       |
| `RATE_LIMIT_EXCEEDED`    | Auth-tier rate limit hit                |

### See also

- [APIs hub](https://hummbl.io/apis) - the card-based documentation index
- [OpenAPI 3.1 spec](https://github.com/hummbl-io/oss) - machine-readable surface
- [MCP server](https://github.com/hummbl-io/oss) - HUMMBL as Model Context Protocol tools
