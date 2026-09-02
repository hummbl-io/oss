# Delegation IETF Gap Analysis

*Supersedes the 2026-08-21 fleet/Devin audit at this path. That audit treated DeepMind DCT and an OAuth chain-delegation draft as IETF peers; this revision uses live Datatracker status as of 2026-08-31 (HDP-01, AIMS-03, AAT-01).*

**Status:** Analysis (not a claim of alignment or certification)
**Date:** 2026-08-31
**Scope:** HMAC-SHA256 `DelegationToken` in `hummbl-governance` 1.4.2 vs live IETF/IRTF drafts for agent identity, capability attenuation, and delegation provenance
**Canonical code:** `packages/python/hummbl-governance/hummbl_governance/delegation.py` and `_types.py` in [hummbl-io/oss](https://github.com/hummbl-io/oss) (tag `hummbl-governance/v1.4.2`)
**Why this file exists:** `docs/FLEET-GOVERNANCE-MAPPING.md` (2026-08-21) cited this path. It was not in the org.

## Do not infer

- This is not IETF alignment, RFC compliance, or a wire-format commitment.
- LANDING-008 already bounds the public claim: HMAC verifies integrity and authenticity inside a shared-secret trust domain. It is not public-key attribution, public verifiability, or non-repudiation.
- LANDING-013 already bounds certification: HUMMBL does not determine legal applicability or confer compliance.
- Internet-Drafts are works in progress. They expire. Citing them as "the standard" is false.

## 1. What HUMMBL actually ships

`DelegationToken` is a frozen dataclass signed with HMAC-SHA256 over `json.dumps(..., sort_keys=True, separators=(",", ":"))`. Canonicalization is sorted-key JSON, not RFC 8785 JCS and not JWS.

| Field | Role |
| --- | --- |
| `token_id` | UUID |
| `issuer` / `subject` | Granting agent / receiving agent (opaque strings) |
| `ops_allowed` | Exact-string operations |
| `resource_selectors` | `resource_type`, `resource_id`, free-form `constraints` |
| `caveats` | `TIME_BOUND`, `RATE_LIMIT`, `APPROVAL_REQUIRED`, `AUDIT_REQUIRED` |
| `expiry` | ISO-8601; default 120 minutes; `None` = no expiry |
| `binding` | `TokenBinding(task_id, contract_id)` |
| `signature` | HMAC-SHA256 hex digest |

Behavior that is real in code:

- Fail-closed authentication (`authenticate_token` returns a detached snapshot; callers must enforce the snapshot).
- Least-privilege check (`check_least_privilege`) against `ops_allowed`.
- Binding check against task, contract, and subject.
- Stdlib-only. Secret from constructor, `HUMMBL_SIGNING_SECRET`, `DCT_SECRET`, or an ephemeral key with a warning.
- Error code `E_DCT_VIOLATION` (`HummblError.DCT_VIOLATION`).

Behavior that is not in this module:

- No `chain` / hop array.
- No parent-token hash.
- No derive/attenuate API (a holder cannot mint a narrower child offline).
- No proof-of-possession of a holder key.
- No WIMSE, SPIFFE, OAuth, or JWT encoding.
- Caveats are stored and serialized; `check_least_privilege` does not evaluate them.

Naming note: the code already calls this a "delegation capability token" and uses `DCT_SECRET` / `DCT_VIOLATION`. That name tracks the DeepMind DCT paper, not an IETF draft.

## 2. Live documents as of 2026-08-31

| Document | Kind | Date | Status | Expires | What it actually specifies |
| --- | --- | --- | --- | --- | --- |
| [draft-helixar-hdp-agentic-delegation-01](https://datatracker.ietf.org/doc/html/draft-helixar-hdp-agentic-delegation-01) | IETF I-D, Informational, Network WG (individual) | 2026-08-03 | Active | 2027-02-04 | Human Delegation Provenance v0.1. Append-only hop chain. Ed25519. Offline verify with issuer public key + `session_id`. Explicitly **not** runtime enforcement. |
| [draft-klrc-aiagent-auth-03](https://datatracker.ietf.org/doc/html/draft-klrc-aiagent-auth-03) | IETF I-D, Informational | 2026-07-06 | Active | 2027-01-07 | AIMS: a **framework**, not a token format. Compose WIMSE, SPIFFE, OAuth 2.0, SSF. Static API keys are an antipattern. |
| [draft-niyikiza-oauth-attenuating-agent-tokens-01](https://datatracker.ietf.org/doc/html/draft-niyikiza-oauth-attenuating-agent-tokens-01) | IETF I-D, **Standards Track**, OAuth | 2026-06-15 | Active | 2026-12-17 | Attenuating Authorization Tokens (AAT). JWT/JWS. Ed25519 MUST. Per-holder `cnf.jwk`. Offline derive. PoP JWT. HMAC/HS256 **MUST NOT**. |
| [draft-asor-wimse-agent-delegation-chain-00](https://datatracker.ietf.org/doc/draft-asor-wimse-agent-delegation-chain/) | IETF I-D, **Standards Track** in header, individual (not WG-adopted) | 2026-08-27 | Active | 2027-02-28 | JWT [RFC 9068] + RAR. Ed25519 MUST; ES256 and ML-DSA MAY. `par_hash` chain. Offline public verify. Companion to AIMS, intends to converge with AAT. |
| [draft-liu-oauth-chain-delegation-00](https://datatracker.ietf.org/doc/draft-liu-oauth-chain-delegation/) | IETF I-D, **Standards Track** in header, individual | 2026-06-06/08 | Active | 2026-12-08 | Authors Liu/Zhu (Alibaba), Krishnan (Cisco), Parecki (Okta). IANA request: JWT claim `delegation_chain`. Detached JWS (RS256/ES256) over RFC 8785 JCS. AS-mediated, not offline holder-derive. Dual signature RECOMMENDED not MUST. |
| [draft-haberkamp-ipp-01](https://datatracker.ietf.org/doc/html/draft-haberkamp-ipp-01) | IETF I-D | 2026-07 | Active | | Intent Provenance Protocol. HDP §1.3: same problem space, **not interoperable** with HDP. |
| Tomasev et al., Delegation Capability Tokens | arXiv **2602.11865** | 2026-02-12 | Paper | n/a | **Not IETF.** Cited by Intent Token and AAT drafts as independent prior art. |

Related: [`draft-sweeney-wimse-credential-delegation-00`](https://datatracker.ietf.org/doc/draft-sweeney-wimse-credential-delegation/) is DS-mediated DPoP JWT (online), not an offline chain. [`draft-ietf-oauth-identity-chaining-17`](https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-chaining/) is in RFC Editor Queue (Proposed Standard) but does not define agent-chain tokens. [`draft-messous-eat-ai-01`](https://datatracker.ietf.org/doc/draft-messous-eat-ai/) is Expired.

### Correction to the Aug 21 mapping

`docs/FLEET-GOVERNANCE-MAPPING.md` listed "IETF HDP, DCT, `delegation_chain` JWT" as one emerging-standards cell. That collapses three layers and one non-IETF paper:

- **HDP** is IETF, and it is provenance, not capability.
- **DCT** is DeepMind, February 2026. HUMMBL borrowed the name.
- **AAT / WIMSE agent-delegation-chain** are the IETF capability-chain drafts. They did not exist as cited "DCT."

## 3. Three layers, not one gap

| Layer | Question | IETF home | HUMMBL today |
| --- | --- | --- | --- |
| Identity | Who is this agent, cryptographically? | AIMS + WIMSE/SPIFFE (WIT, WIC, SVID) | Opaque `issuer` / `subject` strings |
| Capability | What may it do, and can that shrink at each hop? | AAT (and WIMSE delegation-chain) | Single HMAC token; `ops_allowed` + selectors; no derive |
| Provenance | Who authorized this hop, under what intent, in an offline-verifiable chain? | HDP (and IPP) | No hop chain. Receipts (separate primitive) record evidence after the fact |

The Aug 21 doc treated HMAC vs Ed25519 as the whole gap. Crypto is one row. The larger miss is that HDP refuses to be a capability system (HDP §10.1, §12.4) and AAT refuses HMAC (AAT §8.13: symmetric algorithms MUST NOT, because they cannot provide per-holder PoP).

## 4. Gap register

IDs are this analysis's, not GAP-001 (that is the landing-page production-use receipt).

### G-IETF-1 — No append-only hop chain

HDP `chain[]` records `seq`, `agent_id`, `action_summary`, `parent_hop`, `hop_signature`. AAT records `del_depth`, `par_hash`, per-holder keys. HUMMBL has one signed blob. A multi-agent path is not reconstructable from the token.

### G-IETF-2 — Shared secret vs public verification

HDP and AAT verify with an Ed25519 public key. HUMMBL verify requires the HMAC secret. Anyone who can verify can also mint. LANDING-008 already says this. Cross-organization verify is out of scope for the current primitive.

### G-IETF-3 — No holder proof-of-possession

AAT §5: presentation without PoP is replayable because tokens flow through model context. HUMMBL tokens are bearer-with-HMAC inside the trust domain. Possession of the token bytes plus the shared secret is enough. There is no `cnf.jwk`.

### G-IETF-4 — No offline attenuation

AAT §6: a holder derives a child with `tools(child) ⊆ tools(parent)`, tighter TTL, and `par_hash`. HUMMBL `create_token` always mints from the manager's secret. A worker cannot pass a narrower token onward without the issuer secret. Caveats exist on the object but are not a derivation protocol.

### G-IETF-5 — No workload identifier

AIMS §6: agents MUST have a WIMSE identifier (MAY be a SPIFFE ID). HUMMBL `issuer`/`subject` have no URI scheme, no trust domain, no key binding.

### G-IETF-6 — Canonicalization and encoding

HDP signs RFC 8785 JCS. AAT is JWS compact serialization; PoP payload is JCS. HUMMBL is `sort_keys` JSON + hex HMAC. Not interchangeable. A naive "wrap our dict in a JWT" would still fail AAT's algorithm and `cnf` rules.

### G-IETF-7 — Replay surface

HDP: `expires_at` (24h default) + unguessable `session_id` (≥128 bits entropy). AAT: TTL monotonicity + PoP `jti` (stateful for side-effecting tools). HUMMBL: expiry (default 120 min, or none) + task/contract binding if the caller passes expected IDs. No session identifier. `expiry=None` is a protocol hole relative to every draft.

### G-IETF-8 — Mapping error (documentation)

Citing DCT as IETF, and citing a missing analysis file, overstated the standards position. This file closes the second; the mapping table still needs a one-line fix.

### G-IETF-9 — HDP v0.1 is closer than the mapping claimed

HDP §4.2: in v0.1 **the issuer produces every hop signature with a single key**. Per-agent hop signing is "planned for a future version." That is a single trust-domain signer, like HUMMBL's single secret, plus public verify. The Ed25519 swap is smaller than "append-only chain + public verify + later per-agent keys." Do not collapse those.

### G-IETF-10 — HDP is evidence, not a gate

HDP §10.1: "An agent that exceeds its declared scope is still a bad actor; HDP creates an evidence trail, not a capability boundary." HUMMBL `check_least_privilege` **is** a capability boundary (inside the secret domain). Complement, not substitute. HDP §10.4 (chain truncation / omitted hops) is the hole HUMMBL receipts could fill if they bound hop count. They do not, today, bind to an HDP token.

## 5. What HUMMBL has that the drafts do not require

- Runtime deny on `ops_allowed` (AAT requires an enforcement point; HDP refuses to be one).
- Fail-closed exact-type snapshots before verify (defense against container subclasses).
- Task/contract binding as a first-class field.
- Stdlib-only, Alpha, zero Core runtime deps (LANDING-005).
- Default lifetime 120 minutes, tighter than HDP's 24h example.

These are product facts, not IETF credits.

## 6. Decisions this analysis supports (and does not make)

Supported without further research:

1. Stop saying "IETF DCT." Say DeepMind DCT (paper) vs HUMMBL HMAC DCT (code) vs IETF AAT (draft).
2. Do not claim wire compatibility with HDP, AAT, or AIMS.
3. Keep LANDING-008 language. If we add Ed25519 later, that is a new claim with a new receipt.

Not decided here (product / BETS):

- Whether to implement an HDP **profile** as an export (provenance wrapper around an existing HMAC token) vs native Ed25519 HDP.
- Whether AAT is a 2026 engineering target. It is Standards Track and expires 2026-12-17; ignoring it is a choice, not an accident.
- Whether `expiry=None` should be removed from the public API.

## 7. Recommended next engineering (ordered)

1. **Fix the mapping citation** in `docs/FLEET-GOVERNANCE-MAPPING.md`: point here; split HDP / AAT / DCT-paper.
2. **Ban `expiry=None` on issued tokens** or document it as a non-interop mode. Every live draft requires `exp`.
3. **If cross-org verify is a 2026 goal:** Ed25519 root signature on an otherwise unchanged token is the smallest HDP-shaped step. It does not give hop chains or PoP.
4. **If multi-hop least privilege is a 2026 goal:** that is AAT, not HDP. HMAC cannot grow into AAT without replacing the crypto and adding derive + `par_hash` + PoP.
5. **Receipts vs HDP hops:** decide which primitive is the execution audit trail. HDP wants `action_summary` per hop in the token. HUMMBL currently splits capability (token) and evidence (receipt). Mixing them in marketing is G-IETF-10.

## 8. Sources

Primary:

- HUMMBL `delegation.py` / `_types.py` as fetched from `hummbl-io/oss` on 2026-08-31
- [LANDING-008 / LANDING-009 / LANDING-013](https://hummbl.io/manifest/landing-claims.json) (`as_of` 2026-08-26)
- HDP-01, AIMS-03, AAT-01 as fetched from IETF Datatracker on 2026-08-31

Secondary:

- `docs/FLEET-GOVERNANCE-MAPPING.md` (2026-08-21)
- `founder-mode/docs/research/gaas_compliance_landscape_2026.md` (2026-03-22; stale vs current draft revs)
