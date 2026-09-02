# IETF live-document coverage matrix — HUMMBL

**Standard**: IETF is not one AI-governance standard. This matrix enumerates the **live 2026-08-31 documents** named below so completeness = every named artifact has a row. There is no IETF AI-governance RFC and no IETF agent working group as of this review.
**Sources (Datatracker, retrieved 2026-08-31)**:
- Individual I-Ds: [draft-helixar-hdp-agentic-delegation-01](https://datatracker.ietf.org/doc/draft-helixar-hdp-agentic-delegation/), [draft-niyikiza-oauth-attenuating-agent-tokens-01](https://datatracker.ietf.org/doc/draft-niyikiza-oauth-attenuating-agent-tokens/), [draft-asor-wimse-agent-delegation-chain-00](https://datatracker.ietf.org/doc/draft-asor-wimse-agent-delegation-chain/), [draft-liu-oauth-chain-delegation-00](https://datatracker.ietf.org/doc/draft-liu-oauth-chain-delegation/), [draft-sweeney-wimse-credential-delegation-00](https://datatracker.ietf.org/doc/draft-sweeney-wimse-credential-delegation/), [draft-klrc-aiagent-auth-03](https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/), [draft-messous-eat-ai-01](https://datatracker.ietf.org/doc/draft-messous-eat-ai/) (Expired)
- WIMSE WG: [draft-ietf-wimse-arch-08](https://datatracker.ietf.org/doc/draft-ietf-wimse-arch/), [draft-ietf-wimse-identifier-03](https://datatracker.ietf.org/doc/draft-ietf-wimse-identifier/), [draft-ietf-wimse-workload-creds-02](https://datatracker.ietf.org/doc/draft-ietf-wimse-workload-creds/), [draft-ietf-wimse-wpt-02](https://datatracker.ietf.org/doc/draft-ietf-wimse-wpt/)
- OAuth WG: [draft-ietf-oauth-identity-chaining-17](https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-chaining/) (RFC Ed Queue, **Awaiting First editor**; intended Proposed Standard; **no RFC number**)
- Proposed Standards (June 2026): [RFC 9943](https://datatracker.ietf.org/doc/rfc9943/) SCITT, [RFC 9942](https://datatracker.ietf.org/doc/rfc9942/) COSE Receipts (header params **394 `receipts` / 395 `vds` / 396 `vdp`**)
**Effective date / timeline**: Internet-Drafts are working documents (BCP 78/79), not RFCs. RFC 9943 and RFC 9942 are Proposed Standards as of June 2026. Individual agent-delegation drafts are not WG-adopted as of 2026-08-31. WIMSE **WIT / WIC / identifier** are identity credentials; they are not the agent-delegation I-Ds (HDP/AAT/asor/Liu/Sweeney).
**Last reviewed**: 2026-08-31
**Reviewer**: HUMMBL fleet engineering mapping per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.4.2 (`packages/python/hummbl-governance/pyproject.toml`)

## Boundary disclaimer

HUMMBL is **not** an IETF working group, RFC author, or certification body. This matrix is an internal engineering mapping of named live documents to in-process library primitives. It is not a claim that HUMMBL implements, interoperates with, or is certified against any IETF RFC or Internet-Draft. Individual I-Ds have no formal standing until WG adoption and RFC publication. Where a live MUST (Ed25519, JWT, `cnf.jwk` PoP, COSE_Sign1) is unmet, the row is Partial or Out of scope — never Fulfilled.

**DCT is not IETF.** Google DeepMind's Delegation Capability Tokens (cited by `draft-williams-intent-token-01`; paper: arXiv 2602.11865) are listed as an explicit ⛔ row so the name is not silent. HUMMBL's historical `DCT_SECRET` / `E_DCT_VIOLATION` identifiers name HMAC capability tokens in this library; they are not the DeepMind paper and not an IETF I-D.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| Fulfilled | ✅ | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| Partial | 🟡 | HUMMBL primitive provides part of the control; the unmet MUST or customer/protocol remainder is named |
| Boundary | ⚪ | Control is organizational, a different protocol class, or otherwise outside what this library implements |
| Out of scope | ⛔ | Artifact is not an IETF requirement on this library, or does not apply (retained so the name is not silent) |

## Summary (mechanical glyphs only; not a score)

| Surface | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---|---|---|---|---|
| Named live IETF artifacts + explicit DCT out-of-scope row | 15 | 0 | 7 | 6 | 2 |

Draft coverage intent (not public claim): every named artifact has a row. Load-bearing observation: HMAC-SHA256 shared-secret tokens plus `CapabilityFence` are closest to AAT **attenuation semantics** and furthest from AAT/HDP **cryptography** (Ed25519 MUST; AAT forbids HS256/HS384/HS512).

---

## Documents — control-by-control

| Artifact / Control | Requirement (≤1 line) | HUMMBL coverage | Evidence artifact |
|---|---|---|---|
| draft-helixar-hdp-agentic-delegation-01 | Informational HDP: Ed25519 issuer-signed append-only hops recording provenance, not capability | 🟡 Partial: HMAC-SHA256 capability tokens exist; no Ed25519 hops, no append-only provenance chain in the token | `hummbl_governance/delegation.py` |
| draft-niyikiza-oauth-attenuating-agent-tokens-01 | Standards Track header AAT: Ed25519 MUST, JWT + `cnf.jwk` PoP; HS256/HS384/HS512 MUST NOT; hop chain with monotonic attenuation | 🟡 Partial: `ops_allowed` / caveats / `CapabilityFence` attenuate at runtime; HMAC shared-secret contradicts Ed25519 MUST and HMAC-chaining forbid; no JWT hop chain | `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |
| draft-asor-wimse-agent-delegation-chain-00 | Standards Track header: Ed25519 MUST, JWT RFC 9068, `par_hash` parent binding | 🟡 Partial: in-process `DelegationContext` depth/scope exists; token is HMAC JSON, not JWT/`par_hash`/Ed25519 | `hummbl_governance/delegation_context.py`, `hummbl_governance/delegation.py` |
| draft-liu-oauth-chain-delegation-00 | IANA JWT claim `delegation_chain`; AS-mediated; detached JWS | ⚪ Boundary: no JWT claim, no authorization server, no detached JWS in this library | `hummbl_governance/delegation.py` |
| draft-sweeney-wimse-credential-delegation-00 | DS-mediated online DPoP JWT credential delegation | ⚪ Boundary: HUMMBL tokens verify offline with a shared secret; no DPoP, no delegation service | `hummbl_governance/delegation.py` |
| draft-klrc-aiagent-auth-03 | Framework-only AIMS term and WIMSE/OAuth best-practice sketch; not a token format | ⚪ Boundary: AIMS here is a draft term, not ISO 42001 and not a HUMMBL wire format | `hummbl_governance/identity.py` |
| draft-ietf-wimse-arch-08 | WIMSE architecture: workload identity across systems; WIT/WIC/identifier are identity credentials, not an agent-chain protocol | ⚪ Boundary: identity registry is in-process agent aliases/trust tiers, not WIMSE architecture | `hummbl_governance/identity.py` |
| draft-ietf-wimse-identifier-03 | Canonical workload identifier URI in a trust domain (identity credential, not a delegation I-D) | 🟡 Partial: `AgentRegistry` stores string agent IDs; not WIMSE URI identifiers | `hummbl_governance/identity.py` |
| draft-ietf-wimse-workload-creds-02 | WIT/WIC workload credentials; algorithms used with symmetric keys MUST NOT be used | 🟡 Partial: HMAC-SHA256 tokens exist and are the shipped signing model; they are not WIT/WIC and contradict the symmetric-alg forbid | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| draft-ietf-wimse-wpt-02 | Workload Proof Token for presenting workload credentials (identity presentation, not agent-delegation hops) | ⚪ Boundary: no WPT issuer or verifier in this library | n/a — boundary row |
| draft-ietf-oauth-identity-chaining-17 | RFC Ed Queue, Awaiting First editor, no RFC number: OAuth identity/authorization chaining across domains — not agent-chain tokens | ⚪ Boundary: different problem (cross-domain OAuth grants), not HUMMBL agent capability tokens | n/a — boundary row |
| RFC 9943 SCITT | Proposed Standard (June 2026): COSE_Sign1 signed statements + transparency-service receipts | 🟡 Partial: append-only HMAC JSONL/TSV receipts exist; they are not SCITT Signed Statements or transparency-service COSE receipts | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| RFC 9942 COSE Receipts | Proposed Standard (June 2026): COSE receipts proving VDS inclusion/consistency; header params 394 `receipts` / 395 `vds` / 396 `vdp` | 🟡 Partial: HMAC-SHA256 receipt signatures and hash-chain monitors exist; they are not COSE Receipts (not labels 394/395/396) | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/receipt_integrity_monitor.py` |
| DCT / DeepMind (arXiv 2602.11865) | Not an IETF I-D; DeepMind delegation-capability paper cited by `draft-williams-intent-token-01` | ⛔ Out of scope: not IETF; do not treat HUMMBL HMAC tokens or `DCT_SECRET` as this paper | n/a — out-of-scope row |
| draft-messous-eat-ai-01 | Expired EAT profile for AI-agent appraisal / remote attestation; not human→agent authorization | ⛔ Out of scope: expired; appraisal delegation is a different control class than HUMMBL capability tokens | n/a — out-of-scope row |

---

## Code facts used in the rows (not a claim of IETF alignment)

Investigated on this tree (hummbl-governance v1.4.2):

1. **`DelegationTokenManager.authenticate_token`** (`hummbl_governance/delegation.py`) verifies HMAC-SHA256, expiry, and optional binding. It does **not** evaluate `caveats`.
2. **Caveats evaluate in `CapabilityFence._resolve`** (`hummbl_governance/capability_fence.py`) via a caller-supplied `caveat_validator`. A token with caveats cannot construct a fence without that validator.
3. **No hop array on the token.** `DelegationToken` is a single HMAC JSON object. `DelegationContext` tracks in-process depth/scope; it is not an append-only hop chain carried in the token (HDP/AAT/asor).
4. **Signing is HMAC-SHA256 with a shared secret** (`HUMMBL_SIGNING_SECRET` or `DCT_SECRET`). AAT-01: "Symmetric algorithms (HS256, HS384, HS512) MUST NOT be used for AAT". WIMSE workload-creds-02: algorithms used with symmetric keys MUST NOT be used on WIT. Those MUSTs are unmet.
5. **Receipts are HMAC JSON/TSV**, not COSE_Sign1 and not RFC 9942 receipts (not header params 394 `receipts` / 395 `vds` / 396 `vdp`).

This matrix is the **first SCITT / RFC 9943 mapping in this corpus** (none existed in `docs/coverage/` before 2026-08-31). HMAC receipts remain Partial, not Fulfilled.

This matrix does not enumerate EU AI Act / Regulation (EU) 2026/1744, NIST AI 600-1 Action IDs, or NISTIR 8605D. Those are foreign overlays on [`docs/STANDARDS-CROSSWALK.md`](../../../../../docs/STANDARDS-CROSSWALK.md). COSAiS 8605D has no overlay control IDs yet (targeted 2027); no numbers are invented here. Annex III / Art. 6(2) Chapter III §§1–3 high-risk application is **2 December 2027** per Recital 40; this file does not treat 2 August 2026 as the current high-risk date.

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills any IETF RFC or Internet-Draft until row counts, evidence commands, artifact paths, and boundary classifications are validated plus operator/legal review.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Fleet index (primitive↔family, coarser than this file): [`docs/STANDARDS-CROSSWALK.md`](../../../../../docs/STANDARDS-CROSSWALK.md)
- HMAC vs HDP/AAT/AIMS narrative: [`docs/DELEGATION-IETF-GAP-ANALYSIS.md`](../../../../../docs/DELEGATION-IETF-GAP-ANALYSIS.md) (use the copy on this tree; do not fork PR 89)
- Canonical primitives: [`PRIMITIVES.md`](../../PRIMITIVES.md)
