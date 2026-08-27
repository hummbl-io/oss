# ADR-008 — Open Brain integration failure mode (fail-open fallback)

- **Status:** accepted
- **Date:** 2026-06-24
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** none (implementation ADR)

## Context

The HUMMBL API integrates with **Open Brain**, an internal AI service, in three places:

1. **Model recommendation** (`POST /v1/recommend`) — Open Brain provides CLP (Cognitive Layer Protocol) ranked model codes to boost recommendation quality.
2. **Operation governance** (`POST /v1/arbiter`) — Open Brain's Arbiter evaluates operations and returns an ALLOW/DENY verdict.
3. **Semantic search embeddings** (`POST /v1/semantic-search`) — Open Brain provides query embeddings as a fallback when Cloudflare Workers AI is unavailable.

Open Brain is an internal service that may be unavailable (deployment, network partition, incident). The API must decide what happens when Open Brain is unreachable. The chosen behavior is **fail-open**: the API continues serving requests using a local fallback algorithm, never blocking the user on an internal dependency.

## Decision

**Adopt fail-open behavior for all Open Brain integrations. When Open Brain is unavailable, fall back to a local algorithm and continue serving the request.**

### 1. Model recommendation (`/v1/recommend`)

Implementation: `api/src/index.ts` lines 901–983.

- The endpoint reads `OPEN_BRAIN_URL` and `OPEN_BRAIN_TOKEN` from env bindings.
- **If `OPEN_BRAIN_URL` is set**, it calls `${OPEN_BRAIN_URL}/base120/recommend` with the sanitized problem and a 5-second timeout (`AbortSignal.timeout(5_000)`).
  - On success (`clpResp.ok`), it extracts ranked model codes and re-ranks the in-memory model list by CLP order. The response includes `meta.clp_boosted: true`.
  - **On any failure** (non-OK response, network error, timeout, `OPEN_BRAIN_URL` not set), execution falls through to the **local BM25 recommendation algorithm** (`recommendModels()`). The response includes `meta.clp_boosted: false`.
- **If `OPEN_BRAIN_URL` is not set**, the Open Brain call is skipped entirely and the local algorithm runs directly.

**Expected latency:** The Open Brain call is bounded at 5 s by `AbortSignal.timeout`. The local BM25 fallback is sub-millisecond (in-memory). So the worst-case added latency from an Open Brain outage is 5 s (the timeout) on the first failing request; subsequent requests in the same isolate skip the call only if the URL is unset — if the URL is set but the service is down, each request pays the timeout. Operators should unset `OPEN_BRAIN_URL` (or point it at a healthy instance) during a known outage to avoid the per-request timeout cost.

### 2. Operation governance (`/v1/arbiter`)

Implementation: `api/src/index.ts` lines 643–670.

- The endpoint reads `OPEN_BRAIN_URL` and `OPEN_BRAIN_TOKEN`.
- It initializes a default decision of `{ verdict: 'ALLOW', score: 0, allow: true, reason: 'arbiter unavailable — fail-open', arbiter_enabled: false }`.
- **If `OPEN_BRAIN_URL` is set**, it calls `${OPEN_BRAIN_URL}/arbiter/evaluate` with a 5-second timeout.
  - On success, the real Arbiter decision is used.
  - **On any failure** (including `OPEN_BRAIN_URL` not set, which throws and is caught), the default fail-open decision is used — the operation is **allowed**.
- The response tags the fallback with `arbiter_enabled: false` so callers and monitors can detect that the Arbiter did not actually evaluate the operation.

### 3. Semantic search embeddings (`/v1/semantic-search`)

Implementation: `api/src/vectorize.ts` lines 200–237.

- The embedding step tries **Workers AI first** (Cloudflare-native, lowest latency).
- If Workers AI is unavailable or fails, it tries **Open Brain embeddings** (`embedViaOpenBrain`) as a fallback.
- If neither produces a query vector, the semantic search returns `null` and the caller falls back to the BM25 keyword recommendation path.
- Open Brain here is a **secondary** embedding provider, not the primary — so an Open Brain outage only matters when Workers AI is also down. The result is tagged `source: 'open-brain'` when Open Brain embeddings were used.

### Detection: how to know Open Brain failed

| Signal                                                        | Where                          | Meaning                                               |
| ------------------------------------------------------------- | ------------------------------ | ----------------------------------------------------- |
| `meta.clp_boosted: false`                                     | `/v1/recommend` response       | Local BM25 was used, not CLP                          |
| `arbiter_enabled: false`                                      | `/v1/arbiter` response         | Arbiter did not evaluate; fail-open ALLOW was used    |
| `source: 'open-brain'`                                        | `/v1/semantic-search` response | Open Brain embeddings were used (Workers AI was down) |
| Absence of `source: 'open-brain'` with a null semantic result | caller                         | Both embedding providers failed; BM25 fallback used   |

### Monitoring guidance

- **Alert on `clp_boosted: false` ratio.** A sudden increase in the proportion of `/v1/recommend` responses with `clp_boosted: false` indicates Open Brain is down or slow (timing out). Baseline the normal ratio (when Open Brain is healthy, most requests with a set URL should be `true`).
- **Alert on `arbiter_enabled: false`.** Any `/v1/arbiter` response with `arbiter_enabled: false` means governance was bypassed. This should be rare; a spike indicates an Open Brain outage. Because the fail-open default is ALLOW, a sustained `arbiter_enabled: false` condition means operations are running without governance review — escalate.
- **Watch for 5 s latency spikes on `/v1/recommend` and `/v1/arbiter`.** These indicate the Open Brain call is timing out (the `AbortSignal.timeout(5_000)` is firing). If this is sustained, unset `OPEN_BRAIN_URL` to skip the call and eliminate the timeout cost until Open Brain recovers.
- **Log the fallback events.** The catch blocks for Open Brain failures are currently silent (no log emission). A future enhancement should emit a structured log / analytics event on each fallback so monitoring can aggregate without inspecting response bodies.

## Alternatives considered

### Alternative 1: Fail-closed (block requests when Open Brain is down)

**What:** Return a `503` or `502` when Open Brain is unreachable.

**Why rejected:** Open Brain is an internal optimization layer, not a source of truth for the model catalog. The local BM25 algorithm and the in-memory model list are sufficient to serve correct (if less personalized) recommendations. Blocking users on an internal dependency degrades availability for no correctness gain. For the Arbiter path, fail-closed would block all operations during an outage — unacceptable for an internal governance tool that must stay available.

### Alternative 2: Cache Open Brain responses and serve stale

**What:** Cache the last successful CLP / Arbiter response and serve it when Open Brain is down.

**Why rejected:** Recommendations are query-specific (caching a stale response for one query and serving it for another degrades quality). Arbiter decisions are operation-specific (a stale ALLOW for a different operation is unsafe). The local BM25 fallback is query-correct and safer than stale cache serving.

### Alternative 3: Retry with backoff before falling back

**What:** Retry the Open Brain call 2–3 times with backoff before falling back.

**Why rejected:** Adds latency (multiple round-trips + backoff) to every request during an outage. The 5 s timeout already gives Open Brain a generous window; retrying extends the worst case to 15–20 s. The local fallback is good enough that a single attempt + fallback is the right latency/quality trade-off.

## Consequences

### Positive

- The API stays available during Open Brain outages — no user-facing downtime.
- Recommendations degrade gracefully (BM25 instead of CLP) rather than failing.
- The Arbiter stays available (fail-open ALLOW) so operations are not blocked.
- Fallback is detectable via response metadata (`clp_boosted`, `arbiter_enabled`, `source`).

### Negative

- **Arbiter fail-open means governance is bypassed during outages.** Operations are allowed without review. This is a deliberate availability/correctness trade-off: blocking all operations during an internal outage is worse than allowing unreviewed operations temporarily. The `arbiter_enabled: false` signal makes this visible.
- **Silent catch blocks.** Open Brain failures are caught and swallowed without logging. Monitoring must rely on response metadata rather than log streams. (Future enhancement: emit a structured event on fallback.)
- **Per-request timeout cost during outage.** If `OPEN_BRAIN_URL` is set but the service is down, each `/v1/recommend` and `/v1/arbiter` request pays up to 5 s waiting for the timeout. Operators must manually unset `OPEN_BRAIN_URL` to avoid this.

### Neutral

- The 5 s timeout is a tunable. Lowering it reduces outage latency but increases false failures on slow-but-healthy responses.

## Verification

A reader can verify this ADR is in effect by:

1. **Recommend fail-open:** `api/src/index.ts` lines 906–924 — the Open Brain call is wrapped in try/catch; the catch at line 921 falls through to the local BM25 algorithm at line 940.
2. **Arbiter fail-open:** `api/src/index.ts` lines 646–670 — the default decision is `ALLOW` with `arbiter_enabled: false`; the catch at line 668 preserves it.
3. **Semantic search embedding fallback:** `api/src/vectorize.ts` lines 206–216 — Workers AI is tried first, Open Brain second, and a null vector causes the caller to fall back to BM25.
4. **Timeout:** `AbortSignal.timeout(5_000)` at `api/src/index.ts` line 915 and line 663.

## References

- Recommend endpoint: `api/src/index.ts` lines 901–983
- Arbiter endpoint: `api/src/index.ts` lines 643–670
- Semantic search embeddings: `api/src/vectorize.ts` lines 200–237
- Local BM25 algorithm: `api/src/recommend.ts` (`recommendModels`)
- Env bindings: `OPEN_BRAIN_URL`, `OPEN_BRAIN_TOKEN` (see ADR-009 / env var docs)

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This ADR was drafted by Devin at the direction of the Principal Agent, documenting the fail-open behavior already implemented in `api/src/index.ts` and `api/src/vectorize.ts`, and was accepted by Principal Agent decision on 2026-06-24. This ADR is **public** — it documents the failure mode of an internal integration that affects public API availability, and is published for transparency.
