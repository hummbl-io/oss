# ADR-006 — Rate limiting strategy (hybrid in-memory + KV)

- **Status:** accepted
- **Date:** 2026-06-24
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** none (implementation ADR)

## Context

The HUMMBL API (`api.hummbl.io`) runs on Cloudflare Workers. Every public request must be rate-limited to protect the service from abuse and to enforce fair use. The current default is **100 requests per minute per client IP**, applied to all routes before any endpoint-specific logic runs.

Cloudflare Workers present two unusual constraints for rate limiting:

1. **Ephemeral isolate memory.** A Worker isolate may be recycled at any time. An in-memory `Map` does not survive isolate restarts (cold starts), so a pure in-memory counter resets to zero whenever a new isolate spins up — an attacker can simply wait for a cold start to reset their quota.
2. **KV latency.** Cloudflare KV is eventually consistent (~60 s propagation) and adds a round-trip on every read. A pure KV counter would add latency to the hot path of every request and would still be inaccurate within the ~60 s window because concurrent isolates would race on the same key.

A naive pure-in-memory or pure-KV approach therefore either resets too aggressively (cold starts) or is too slow / too stale for the hot path.

## Decision

**Adopt a hybrid in-memory primary + KV write-through rate limiter.**

The implementation lives in `api/src/index.ts` (lines 117–184). The design:

| Layer                                       | Role                                                         | Characteristics                                       |
| ------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------- |
| In-memory `Map<string, {count, resetTime}>` | Hot path — every request reads and increments here           | Sub-millisecond, per-isolate, lost on cold start      |
| Cloudflare KV (`ANALYTICS_KV`)              | Durability — persists counts across cold starts and isolates | Eventually consistent (~60 s), 120 s TTL auto-cleanup |

### Hot path (every request)

1. Read the client IP from `CF-Connecting-IP` (fallback `X-Forwarded-For`).
2. Look up the in-memory entry for that IP.
3. If the entry exists and the window hasn't expired, increment the counter. If the counter has reached `RATE_LIMIT_MAX` (100), return `429`.
4. If there is no in-memory entry (cold start), attempt to **hydrate from KV** (`ratelimit:<ip>`). If KV has a non-expired entry, seed the in-memory map from it. If KV is empty or the read fails, start a fresh window at count 1.

### Write-through (amortized)

- On every **10th request** for an IP, the current count is written to KV with a 120 s `expirationTtl` (auto-cleanup). The write is wrapped in `waitUntil()` so it survives after the response is sent and does not block the response.
- Writing every 10th request (rather than every request) amortizes KV write cost while keeping the persisted count within ~10 requests of the true count.

### Cold-start behavior

On a cold start the in-memory map is empty. The limiter tries to hydrate from KV first, so a returning client inherits their prior count (subject to ~60 s KV freshness). A brand-new client (no KV entry) starts at count 1. This means the worst-case over-count during a cold start is bounded by the KV staleness window — a client could get slightly more than 100 requests/min if their KV entry hasn't propagated, but never an unbounded amount.

### Cleanup

Expired in-memory entries are purged probabilistically (1% of requests trigger a sweep) to avoid a growing map and to avoid a synchronous sweep on every request.

## Alternatives considered

### Alternative 1: Pure in-memory

**What:** Count only in the in-memory `Map`, no KV.

**Why rejected:** Cold starts reset every IP's counter to zero. An attacker who triggers isolate recycling (or simply waits) gets a fresh quota. There is also no cross-isolate coordination, so concurrent isolates each grant a full 100 req/min to the same IP.

### Alternative 2: Pure KV

**What:** Read and write the counter in KV on every request.

**Why rejected:** Adds a KV round-trip to the hot path of every request (latency). KV is eventually consistent (~60 s), so concurrent isolates racing on the same key would still over-count within the propagation window — the accuracy gain over the hybrid approach is marginal while the latency cost is real. KV write costs would also be 10× higher (every request vs. every 10th).

### Alternative 3: Cloudflare Rate Limiting Rules (edge)

**What:** Use Cloudflare's native edge rate limiting product instead of application-level counting.

**Why rejected:** Edge rate limiting is configured at the zone level and is less flexible for the tier-aware, per-key limits that the API key system (ADR-007) requires. The application-level limiter can share the same KV namespace and patterns with the per-key limiter. Edge rules remain a viable complementary layer for volumetric DDoS protection and may be added in a future ADR.

## Consequences

### Positive

- Hot path is sub-millisecond (in-memory read + increment).
- Counts survive cold starts via KV hydration.
- Cross-isolate coordination is eventually consistent (~60 s), which is acceptable for a 100 req/min/IP limit.
- KV write cost is amortized (every 10th request) and non-blocking (`waitUntil`).
- Auto-cleanup via 120 s TTL prevents unbounded KV growth.

### Negative

- Within the ~60 s KV propagation window, concurrent isolates can each grant up to 100 req/min to the same IP. For a 100 req/min limit this over-count is bounded and acceptable; for stricter limits it would matter more.
- On cold start with a stale KV entry, a client may receive slightly more than their quota until the next write-through refreshes KV.
- KV read failure (transient) falls through to in-memory only, effectively resetting the counter for that IP for the current window. This is a fail-open trade-off chosen to prioritize availability.

### Neutral

- The 10th-request write-through cadence is a tunable. Lowering it improves KV freshness at higher write cost; raising it does the reverse.

## Verification

A reader can verify this ADR is in effect by:

1. **The limiter exists:** `grep -n "RATE_LIMIT_MAX" api/src/index.ts` → `const RATE_LIMIT_MAX = 100;`
2. **KV hydration on cold start:** `api/src/index.ts` lines 142–155 read `ratelimit:<ip>` from KV when no in-memory entry exists.
3. **Write-through:** `api/src/index.ts` lines 174–181 write to KV every 10th request via `waitUntil`.
4. **429 response:** exceeding 100 req/min returns `{ success: false, error: "Rate limit exceeded..." }` with status 429 (lines 160–167).

## References

- Implementation: `api/src/index.ts` lines 117–184
- KV namespace binding: `api/wrangler.toml` (`ANALYTICS_KV`)
- Per-key rate limiting (companion): `api/src/auth.ts` (`checkKeyRateLimit`)
- ADR-007: `docs/adr/ADR-007-api-key-tier-system.md`

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This ADR was drafted by Devin at the direction of the Principal Agent, documenting the rate limiting strategy already implemented in `api/src/index.ts`, and was accepted by Principal Agent decision on 2026-06-24. This ADR is **public** — it documents a rate limiting design that affects how the public API enforces fair use, and is published for transparency.
