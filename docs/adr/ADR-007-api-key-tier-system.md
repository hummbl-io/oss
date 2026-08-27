# ADR-007 — API key tier system (free / pro / enterprise)

- **Status:** accepted
- **Date:** 2026-06-24
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** none (implementation ADR)

## Context

The HUMMBL API (`api.hummbl.io`) exposes a set of `/v1/*` endpoints. Some endpoints (models, transformations, recommendations) are broadly useful; others (semantic search, validation) are higher-value and should be gated behind paid tiers. The API needs:

1. **Anonymous access** — unauthenticated requests should still work, so developers can try the API without signing up. These get free-tier limits enforced by the IP-based rate limiter (ADR-006).
2. **Authenticated access with tiers** — registered API keys get higher limits and access to gated endpoint groups, scaled by plan.
3. **A permission model** — which tier can access which endpoint group.
4. **An upgrade path** — how a user moves from free → pro → enterprise.

The implementation spans `api/src/auth.ts` (key storage, tier limits, permission checks, per-key rate limiting) and `api/src/index.ts` (the `/v1/*` auth middleware that wires keys to endpoints).

## Decision

**Adopt a three-tier API key system: free, pro, enterprise.**

### Key format and storage

- Keys are generated with a `hummbl_` prefix followed by 32 random hex bytes: `hummbl_<64 hex chars>`.
- Keys are stored in D1 (`api_keys` table) as **SHA-256 hashes** — the raw key is returned to the user exactly once at creation time and is never retrievable thereafter. The table stores `key_hash`, `key_prefix` (first 15 chars, for display), `tier`, `name`, `owner_email`, `is_active`, `usage_count`, `last_used`, `created_at`, `revoked_at`.
- Authentication reads the key from the `X-API-Key` header (or `Authorization: Bearer <key>`), hashes it, and looks up the hash in D1.

### Tier limits

Per-key rate limits are enforced via KV-backed counters (`ANALYTICS_KV`), with an in-memory fallback for test environments. The limits are defined in `api/src/auth.ts`:

| Tier       | Requests / hour | Requests / day |
| ---------- | --------------- | -------------- |
| free       | 100             | 1,000          |
| pro        | 1,000           | 10,000         |
| enterprise | 10,000          | 100,000        |

When a limit is exceeded the API returns `429` with `code: RATE_LIMIT_EXCEEDED` and a message naming the tier and the exceeded window (hourly or daily). Per-key rate limiting **fails open** on KV errors: a transient KV read/write failure allows the current request through rather than blocking it, prioritizing availability.

### Permission model

Each tier is granted access to a set of **endpoint groups**. The mapping is defined in `TIER_PERMISSIONS` (`api/src/auth.ts`) and enforced by `hasPermission(tier, endpointGroup)`:

| Endpoint group    | free | pro | enterprise |
| ----------------- | ---- | --- | ---------- |
| `models`          | ✓    | ✓   | ✓          |
| `transformations` | ✓    | ✓   | ✓          |
| `recommend`       | ✓    | ✓   | ✓          |
| `workflows`       | ✓    | ✓   | ✓          |
| `semantic-search` | —    | ✓   | ✓          |
| `validate`        | —    | —   | ✓          |

The `/v1/*` auth middleware (`api/src/index.ts` lines 272–328) maps the request path to an endpoint group and calls `hasPermission()`. If the caller's tier lacks permission, the API returns `403` with `code: INSUFFICIENT_TIER`, the caller's current `tier`, and a message indicating the required tier:

- A `free` caller hitting a `pro`-gated group gets `"semantic-search requires pro tier"`.
- A `pro` caller hitting an `enterprise`-gated group gets `"validate requires enterprise tier"`.

### Anonymous access

If no API key is provided on a `/v1/*` request, the middleware allows the request through (`return await next()`) without authenticating. The anonymous caller is still subject to the IP-based rate limiter (ADR-006, 100 req/min per IP). This lets developers try the public endpoints without registering.

### Auth failure modes

| Error type                 | HTTP status | Cause                                                                                                                        |
| -------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `MISSING_AUTH`             | 401         | Key required but not provided (only returned when a key is present but empty)                                                |
| `INVALID_FORMAT`           | 401         | Key doesn't start with `hummbl_` or is too short                                                                             |
| `KEY_NOT_FOUND`            | 401         | Key hash not in D1                                                                                                           |
| `KEY_INACTIVE`             | 403         | Key has been revoked (`is_active = 0`)                                                                                       |
| `RATE_LIMIT_EXCEEDED`      | 429         | Per-key hourly or daily limit exceeded                                                                                       |
| `AUTH_SERVICE_UNAVAILABLE` | 503         | D1 binding missing — **fail closed** (a provided key must not bypass auth when the backing store is misconfigured, see #431) |
| `INSUFFICIENT_TIER`        | 403         | Key is valid but its tier lacks permission for the endpoint group                                                            |

### Key lifecycle

- **Create:** `createApiKey(db, { name, tier?, ownerEmail? })` generates a key, hashes it, and inserts a row. Default tier is `free`. The raw key is returned once.
- **List:** `listApiKeys(db)` returns all keys without hashes (prefix only).
- **Revoke:** `revokeApiKey(db, keyId)` sets `is_active = 0` and `revoked_at`. Subsequent requests with that key return `KEY_INACTIVE` (403).
- **Usage tracking:** every successful authentication increments `usage_count` and updates `last_used` (fire-and-forget D1 write).

### Upgrade path

Tiers are stored as a column on the `api_keys` row. Upgrading a user from free → pro or pro → enterprise is an administrative operation that updates the `tier` column for that key (or issues a new key at the new tier). There is no self-service upgrade endpoint in the current implementation; tier changes are operator-managed. The `getTierLimits(tier)` helper returns the limits and permissions for a tier for display purposes.

## Alternatives considered

### Alternative 1: Single tier (all-or-nothing)

**What:** One tier for all authenticated keys; anonymous requests blocked.

**Why rejected:** Prevents try-before-you-sign-up (anonymous access is a deliberate product choice) and provides no way to monetize higher-value endpoints like semantic search and validation.

### Alternative 2: Scope-based permissions (OAuth-style scopes)

**What:** Each key carries a set of scopes (e.g., `models:read`, `semantic-search:read`) rather than a tier.

**Why rejected:** Adds configuration complexity for the user (they must choose scopes at key creation). The tier model is simpler to communicate and sell (three plans vs. N scope permutations). Scopes remain a viable future extension if finer-grained access control is needed.

### Alternative 3: Per-endpoint rate limits instead of tier-wide limits

**What:** Each endpoint has its own rate limit independent of tier.

**Why rejected:** Couples limits to endpoints rather than to the customer relationship. Tier-wide limits (hour + day) map cleanly to plan pricing and are easier to reason about for both users and operators.

## Consequences

### Positive

- Three tiers map directly to product pricing (free / pro / enterprise).
- Anonymous access lets developers try the API without friction.
- Keys are stored as hashes — a database leak does not expose usable keys.
- Fail-closed on missing D1 (`AUTH_SERVICE_UNAVAILABLE`) prevents a misconfigured binding from bypassing auth.
- Per-key rate limits share the KV namespace and patterns with the IP limiter (ADR-006), keeping the infrastructure uniform.

### Negative

- Tier upgrades are operator-managed (no self-service). This is acceptable today but will need a self-service path as the user base grows.
- Per-key rate limiting fails open on KV errors (a transient KV failure lets a request through). This prioritizes availability over strict limit enforcement; for paid tiers this means a brief over-allow during KV incidents.
- The endpoint-group mapping in the middleware is path-substring based (`path.includes('semantic-search')`, etc.). A new endpoint group requires a code change in both `TIER_PERMISSIONS` and the middleware mapping.

### Neutral

- The `api_keys` schema is owned by D1 migrations; adding a new tier is a data change (new tier string) plus a code change (extend `TIER_LIMITS` and `TIER_PERMISSIONS`).

## Verification

A reader can verify this ADR is in effect by:

1. **Tier limits:** `api/src/auth.ts` lines 16–20 define `TIER_LIMITS` with the three tiers and their hour/day limits.
2. **Permissions:** `api/src/auth.ts` lines 23–34 define `TIER_PERMISSIONS`; `hasPermission()` at lines 265–267 checks membership.
3. **Auth middleware:** `api/src/index.ts` lines 272–328 authenticate `/v1/*` requests, map the path to an endpoint group, and enforce `hasPermission()`.
4. **Key hashing:** `api/src/auth.ts` `hashApiKey()` (lines 51–58) uses Web Crypto SHA-256.
5. **Fail-closed on missing D1:** `api/src/auth.ts` lines 97–110 return `AUTH_SERVICE_UNAVAILABLE` when `db` is undefined.

## References

- Tier limits and permissions: `api/src/auth.ts` lines 16–34
- `hasPermission()`: `api/src/auth.ts` lines 265–267
- Auth middleware: `api/src/index.ts` lines 272–328
- Key lifecycle: `api/src/auth.ts` (`createApiKey`, `listApiKeys`, `revokeApiKey`)
- IP rate limiting (companion): ADR-006 `docs/adr/ADR-006-rate-limiting-strategy.md`
- Fail-closed auth fix: issue #431

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This ADR was drafted by Devin at the direction of the Principal Agent, documenting the tier-based API key system already implemented in `api/src/auth.ts` and `api/src/index.ts`, and was accepted by Principal Agent decision on 2026-06-24. This ADR is **public** — it documents the access control model for the public API, and is published for transparency.
