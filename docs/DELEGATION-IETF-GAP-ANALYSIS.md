# HUMMBL Delegation Tokens — IETF Standards Gap Analysis

**Status:** Audit (no code changes)
**Date:** 2026-08-21
**Auditor:** HUMMBL fleet (devin)
**HUMMBL code reviewed:** `hummbl_governance/delegation.py` (421 lines), `hummbl_governance/_types.py` (DelegationToken, TokenBinding, ResourceSelector, Caveat)
**IETF drafts reviewed:** HDP v0.1, DCT v1.0.0, OAuth Chain Delegation v0.00

## Purpose

Three concurrent IETF/standards-track drafts are standardizing cryptographic delegation chains for AI agents. HUMMBL's delegation tokens predate these drafts but align with their design principles. This audit identifies where HUMMBL's wire format diverges from the emerging standards and recommends alignment actions to avoid costly refactoring when the drafts ratify.

**No code changes are made in this audit.** This is a gap analysis only.

---

## 1. HUMMBL's current implementation

Source: `hummbl_governance/delegation.py` (read in full, 421 lines)

| Property | HUMMBL implementation |
|----------|----------------------|
| **Signing algorithm** | HMAC-SHA256 (symmetric) |
| **Key model** | Shared secret (`HUMMBL_SIGNING_SECRET` or `DCT_SECRET` env var, or ephemeral) |
| **Token format** | Custom dataclass (`DelegationToken`) serialized to JSON dict |
| **Token fields** | `token_id` (UUID v4), `issuer`, `subject`, `resource_selectors`, `ops_allowed`, `caveats`, `expiry` (ISO 8601), `binding` (task_id + contract_id), `signature` |
| **Chain structure** | None — single token, no delegation chain |
| **Verification** | HMAC-SHA256 signature check + expiry check + binding validation + least-privilege check |
| **Attenuation** | Per-token: `ops_allowed` and `resource_selectors` constrain what the subject can do. No chain-level monotonic attenuation (no chain exists). |
| **Session binding** | `binding.task_id` + `binding.contract_id` (not a session ID, but task-scoped) |
| **Offline verifiability** | Yes — HMAC verification requires only the shared secret |
| **Expiry** | ISO 8601 timestamp, default 120 minutes |
| **Revocation** | None — token expires or is invalidated by process restart (ephemeral key) |
| **Canonicalization** | `json.dumps(data, sort_keys=True, separators=(",", ":"))` — sorted-key JSON, not RFC 8785 JCS |
| **Stdlib-only** | Yes — zero third-party dependencies (HMAC, hashlib, json, uuid from stdlib) |

---

## 2. IETF drafts — comparison matrix

| Dimension | HUMMBL | HDP v0.1 | DCT v1.0.0 | OAuth Chain Delegation v0.00 |
|-----------|--------|----------|------------|------------------------------|
| **Signing algorithm** | HMAC-SHA256 (symmetric) | Ed25519 (asymmetric) | Ed25519 (asymmetric) | Algorithm-agnostic JWS (RS256, ES256, etc.) |
| **Key model** | Shared secret | Single issuer key (root + all hops) | Per-agent keys (delegator signs) | AS key (mandatory) + optional agent key |
| **Token format** | Custom dataclass/JSON | Custom JSON (6 fields, not JWT) | Custom header/payload/sig (not JWT) | JWT claim extension (RFC 7519) |
| **Chain structure** | None (single token) | Append-only array within single token | Linked tokens via parent token ID | Ordered array in JWT claim (most-recent-first) |
| **Attenuation** | Per-token ops_allowed | Fixed at issuance, no per-hop narrowing | Monotonic: child MUST have <= parent permissions | AS enforces scope subset at each hop |
| **Session binding** | task_id + contract_id | session_id (REQUIRED, >=128 bits entropy) | Not specified | Not specified (DPoP/mTLS instead) |
| **Offline verifiability** | Yes (shared secret) | Yes (issuer pubkey only) | Implied (per-token); chain traversal may need parent tokens | No (AS metadata, WIT/SPIFFE resolution) |
| **Expiry** | ISO 8601, default 120 min | Unix ms, default 24 hours | Header timestamp, no default | JWT `exp` claim, no default |
| **Revocation** | None | None (token expiry or session end) | None | Standard OAuth revocation |
| **Canonicalization** | Sorted-key JSON | RFC 8785 JCS | Not specified | RFC 8785 JCS |
| **Normative strength** | N/A (HUMMBL internal) | RFC 2119 MUST/SHOULD | Design invariants (no RFC 2119) | RFC 2119 MUST/SHOULD |
| **Standardization status** | Production (PyPI v1.2.2) | IETF Informational, expires 2027-02-04 | Zenodo working paper, not IETF | IETF Standards Track intended, expires 2026-12-08 |

---

## 3. Gaps identified

### Gap 1: Symmetric vs. asymmetric signing (CRITICAL)

**HUMMBL:** HMAC-SHA256 with shared secret.
**All three drafts:** Ed25519 or JWS asymmetric signing.

**Impact:** HUMMBL's symmetric model cannot support per-agent non-repudiation (any holder of the shared secret can forge any token). The IETF drafts require asymmetric keys so that each agent's signature is independently verifiable against that agent's public key.

**Risk if unaligned:** When the IETF drafts ratify, HUMMBL tokens will not be interoperable with any standards-compliant verifier. External systems cannot verify HUMMBL tokens without the shared secret, which defeats the purpose of a delegation chain.

**Alignment options:**
- **A (full alignment):** Migrate to Ed25519. Add `cryptography` dependency (breaks stdlib-only constraint) or use `hashlib` + manual Ed25519 (not in stdlib until Python 3.12+ `cryptography` — actually Ed25519 is NOT in stdlib). This is a breaking change.
- **B (hybrid):** Keep HMAC-SHA256 for internal fleet use; add an Ed25519-signed wrapper for external/standards-compliant interoperability. Two verification paths.
- **C (defer):** Wait for IETF ratification. The drafts may change significantly (HDP is Informational from a single author; DCT is a Zenodo paper with no IETF standing). Re-audit quarterly.

**Recommendation:** **B (hybrid).** HUMMBL's stdlib-only constraint is a competitive advantage (zero dependencies, easy audit). Breaking it for pre-ratified drafts is premature. Add an Ed25519 wrapper for external interop when the drafts are closer to ratification. Monitor quarterly.

### Gap 2: No delegation chain (CRITICAL)

**HUMMBL:** Single token, no chain. Each `create_token` call produces an independent token.
**All three drafts:** Append-only chain (HDP), linked tokens (DCT), or ordered array (OAuth).

**Impact:** HUMMBL cannot prove the full delegation path from human principal -> orchestrator -> sub-agent -> tool-executor. Each token is a point-in-time capability, not a link in a chain. This means:
- No audit trail of how a sub-agent received its authority
- No cascade revocation (revoking a parent does not revoke children)
- No `max_hops` delegation budget

**Risk if unaligned:** HUMMBL's governance primitives are positioned as fleet-scoped, but without a delegation chain, the "fleet" dimension of delegation is unprovable. The FAccT 2024 paper identifies "agent identifiers + real-time monitoring + activity logging" as the minimum visibility stack — HUMMBL has identifiers and monitoring but the activity logging is per-token, not per-chain.

**Alignment options:**
- **A (full alignment):** Add a `chain` field to `DelegationToken` (list of hop records). Each delegation appends a hop. Breaking change to the dataclass.
- **B (external chain):** Keep `DelegationToken` as-is; add a separate `DelegationChain` class that links tokens via `parent_token_id`. Non-breaking.
- **C (defer):** HUMMBL's current per-token model is sufficient for internal fleet use. Add chain support when external interop is needed.

**Recommendation:** **B (external chain).** Non-breaking, preserves the current API, and adds chain tracking as a layer. The `DelegationChain` class can reference existing tokens by `token_id` and enforce monotonic attenuation (child's `ops_allowed` must be a subset of parent's).

### Gap 3: Canonicalization (MODERATE)

**HUMMBL:** `json.dumps(data, sort_keys=True, separators=(",", ":"))`
**HDP + OAuth:** RFC 8785 JSON Canonicalization Scheme (JCS)
**DCT:** Not specified

**Impact:** HUMMBL's sorted-key JSON is close to RFC 8785 but not identical. RFC 8785 specifies additional rules for number formatting, string escaping, and key ordering that Python's `json.dumps` does not follow by default. A token signed by HUMMBL would fail RFC 8785 verification by a standards-compliant verifier.

**Risk if unaligned:** Low for internal use (HUMMBL verifies its own tokens). High for external interop (a standards-compliant verifier would reject the signature).

**Alignment options:**
- **A (full alignment):** Implement RFC 8785 JCS in stdlib. ~100 lines of Python. No third-party dependency needed.
- **B (defer):** Keep sorted-key JSON for internal use. Switch to JCS when adding the Ed25519 external wrapper (Gap 1 option B).

**Recommendation:** **A (full alignment).** RFC 8785 JCS is implementable in stdlib (~100 lines), and adopting it now means the canonicalization layer is ready when the signing layer migrates. Low cost, high readiness.

### Gap 4: Session binding (LOW)

**HUMMBL:** `binding.task_id` + `binding.contract_id`
**HDP:** `session_id` (REQUIRED, >=128 bits entropy)
**DCT + OAuth:** Not specified

**Impact:** HUMMBL's task/contract binding is stronger than HDP's session binding in some dimensions (task-scoped, not just session-scoped) but weaker in others (no entropy requirement, no replay defense across sessions with the same task ID).

**Risk if unaligned:** Low. HUMMBL's binding model is a superset of HDP's in functionality (task + contract > session alone). The gap is the entropy requirement, which is a SHOULD in HDP, not a MUST.

**Recommendation:** **No action needed.** HUMMBL's binding model is functionally adequate. If aligning with HDP for external interop, add a `session_id` field to the binding as an optional supplement to task/contract.

### Gap 5: Per-hop attenuation (LOW for now, MEDIUM if chain is added)

**HUMMBL:** Per-token `ops_allowed` (no chain, so no per-hop attenuation)
**DCT + OAuth:** Monotonic attenuation (child MUST have <= parent permissions)
**HDP:** Fixed at issuance, no per-hop narrowing

**Impact:** If HUMMBL adds a delegation chain (Gap 2), it should also add monotonic attenuation enforcement. Without it, a sub-agent could delegate more permissions than it received.

**Recommendation:** **Defer until chain is added.** If Gap 2 option B is implemented, add attenuation enforcement to the `DelegationChain` class: `child.ops_allowed` must be a subset of `parent.ops_allowed`.

### Gap 6: Expiry format (LOW)

**HUMMBL:** ISO 8601 (`2026-08-21T14:30:00Z`)
**HDP:** Unix milliseconds
**DCT:** Header timestamp (format not specified)
**OAuth:** JWT `exp` claim (NumericDate = Unix seconds)

**Impact:** Format conversion is trivial. No architectural gap.

**Recommendation:** **No action needed for internal use.** Convert to Unix milliseconds in the Ed25519 external wrapper if aligning with HDP.

---

## 4. Summary of recommendations

| Gap | Severity | Recommendation | Effort | When |
|-----|----------|----------------|--------|------|
| 1. Symmetric vs. asymmetric | CRITICAL | B: Hybrid (HMAC internal + Ed25519 wrapper) | Medium | When drafts ratify or external interop needed |
| 2. No delegation chain | CRITICAL | B: External `DelegationChain` class | Medium | When fleet audit trail is needed |
| 3. Canonicalization | MODERATE | A: Implement RFC 8785 JCS in stdlib | Low (~100 lines) | Now (readiness for Gap 1) |
| 4. Session binding | LOW | No action | None | N/A |
| 5. Per-hop attenuation | LOW/MEDIUM | Defer until chain is added | Low | With Gap 2 |
| 6. Expiry format | LOW | No action for internal; convert in wrapper | Trivial | With Gap 1 |

**Net recommendation:** Implement Gap 3 (RFC 8785 JCS) now as a low-cost readiness step. Defer Gaps 1 and 2 until the IETF drafts are closer to ratification or external interoperability is required. Monitor drafts quarterly.

---

## 5. Drafts status and monitoring schedule

| Draft | Status | Expires | Monitoring |
|-------|--------|---------|------------|
| HDP v0.1 | IETF Informational, single author (Helixar) | 2027-02-04 | Quarterly check on ietf.org. Watch for WG adoption or version bump. |
| DCT v1.0.0 | Zenodo working paper, not IETF | N/A | Check Substr8 Labs GitHub for updates. Lowest standardization tier. |
| OAuth Chain Delegation v0.00 | IETF Standards Track intended, 4 authors (Alibaba, Cisco, Okta) | 2026-12-08 | Quarterly check. Highest ratification probability. Watch for WG adoption. |

**Re-audit trigger:** Any draft reaches WG adoption, or any draft publishes a new version with breaking changes to token format or verification model.

---

## 6. What HUMMBL has that the drafts do not

HUMMBL's implementation has features the IETF drafts are silent on:

1. **Stdlib-only constraint** — HUMMBL runs with zero third-party dependencies. All three drafts require Ed25519, which is not in Python's stdlib. HUMMBL's HMAC-SHA256 approach is a deliberate engineering choice that preserves the stdlib-only invariant.

2. **Task/contract binding** — HUMMBL's `TokenBinding(task_id, contract_id)` binds tokens to specific tasks and contracts. HDP has `session_id` but no task/contract binding. DCT and OAuth have neither.

3. **Caveats** — HUMMBL's `Caveat` type supports constraints on token use (e.g., "only between 09:00-17:00"). None of the three drafts have a caveat mechanism.

4. **Resource selectors** — HUMMBL's `ResourceSelector(resource_type, resource_id, constraints)` provides fine-grained resource access control. HDP has `authorized_resources` (a flat list). DCT mentions "fine-grained permission model" but does not specify the structure. OAuth has `scope` (string) and `delegated_policy` (object).

5. **Fail-closed authentication** — HUMMBL's `authenticate_token` rejects on any anomaly (subclass detection, non-JSON values, signature mismatch). The drafts specify verification pipelines but do not mandate fail-closed behavior on unexpected input types.

These are HUMMBL design advantages that should be preserved in any alignment work.

---

*Audit basis: HUMMBL `hummbl_governance/delegation.py` (421 lines, read in full) + IETF HDP v0.1, DCT v1.0.0, OAuth Chain Delegation v0.00 (extracted via browser-scraper subagent, 2026-08-21). No code changes made.*
