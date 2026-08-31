# HUMMBL standards crosswalk — IETF / NIST AI RMF / ISO 42001

**Status:** internal engineering mapping
**Date:** 2026-08-31
**Scope:** IETF (named live drafts/RFCs), NIST AI RMF 1.0, ISO/IEC 42001:2023
**Supersedes:** April 2026 `STANDARDS_CROSSWALK_v0.1` (provider-governance, 8 capabilities at header level) for IETF / NIST / ISO. CMMC is out of this file.

This is the fleet-level index April asked for. It does **not** replace the per-framework coverage matrices. Those remain the complete control-row workpapers.

## 1. Header — what this file is not

This document is **not** a certification, **not** a legal opinion, and **not** a public claim that HUMMBL fulfills or is certified against any standard.

- **[ADR-001](../packages/python/hummbl-governance/docs/adr/ADR-001-coverage-matrix-not-self-grade.md)** governs: no self-grades, no percentages, no letter scores, no public “fulfills ALL” headline without a complete validated matrix. This file is coarser than ADR-001 (primitive↔family, not every control row).
- **LANDING-013** still governs: technical evidence generation and engineering mappings only.
- Public product language: claim **framework-mapped evidence support**, not blanket compliance.

HUMMBL version on this tree: **hummbl-governance v1.4.2** (`packages/python/hummbl-governance/pyproject.toml`). Canonical primitive inventory: [`packages/python/hummbl-governance/PRIMITIVES.md`](../packages/python/hummbl-governance/PRIMITIVES.md) (34 entries P1–P34; 31 irreducible primitives after excluding support artifacts P23, P24, P26). Equivalent at tag `hummbl-governance/v1.4.2`.

## 2. What already exists (do not fork)

| Artifact | Role | Notes |
|---|---|---|
| [`packages/python/hummbl-governance/docs/coverage/nist-ai-rmf.md`](../packages/python/hummbl-governance/docs/coverage/nist-ai-rmf.md) | Full NIST AI RMF 1.0 subcategory rows | Last reviewed **2026-05-14**, HUMMBL v**0.8.0**, **draft** |
| [`packages/python/hummbl-governance/docs/coverage/iso-42001.md`](../packages/python/hummbl-governance/docs/coverage/iso-42001.md) | ISO/IEC 42001:2023 clauses 4–10 + Annex A | Same draft caveat (2026-05-14 / v0.8.0) |
| [`packages/python/hummbl-governance/docs/coverage/ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md) | ADR-001 matrix: one row per named live IETF artifact | Added 2026-08-31; IETF was missing from the coverage folder |
| [`docs/DELEGATION-IETF-GAP-ANALYSIS.md`](./DELEGATION-IETF-GAP-ANALYSIS.md) | HMAC vs HDP/AAT/AIMS narrative | Use whichever copy is **on this tree**. Do not fight PR 89 if that rewrite lands later. |
| [`docs/FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md) | Fleet-as-unit positioning | This crosswalk does not rewrite it |
| [`packages/python/hummbl-governance/docs/coverage/README.md`](../packages/python/hummbl-governance/docs/coverage/README.md) | Mechanical index of all coverage matrices | Counts from `scripts/count_coverage_rows.py` only |

The coverage folder already has NIST AI RMF, ISO 42001, EU AI Act, and ~90 other matrices. **This file does not duplicate those control rows.** EU AI Act stays in its own matrix (foreign overlay below; not a family this file owns). CMMC is not added here.

## 3. Family facts (2026-08-31)

Do not invent versions or authorship.

1. **NIST AI RMF 1.0** (NIST.AI.100-1, January 2023) is the published Core. No 1.1 Core is published as of 2026-08-31. [nist.gov/itl/ai-risk-management-framework](https://www.nist.gov/itl/ai-risk-management-framework): “The AI RMF 1.0 is being revised as part of the White House AI Action Plan.” The Playbook count is **72 subcategories** (matches [`nist-ai-rmf.md`](../packages/python/hummbl-governance/docs/coverage/nist-ai-rmf.md) row count). Subcategory IDs in the matrix below match the AIRC Core (`GOVERN 2.1` = `GV-2.1`, `MANAGE 2.4` = `MG-2.4`). **NIST AI 600-1** (GenAI Profile) adds **no new Core IDs** and is not a column here. Agent-relevant *existing* Core IDs it points at: GOVERN 3.2, MAP 2.2, MAP 3.5, MANAGE 2.4, MANAGE 4.1, plus GAI risks 2.7 and 2.12. Do not treat 600-1 Action IDs as overlay controls.
2. **ISO/IEC 42001:2023** remains the only certifiable **AI management-system standard (AIMS)** (iso.org stage **60.60**). It is an **organization** AIMS, not a model certificate and not a product certificate. HUMMBL is an in-process library, not an AIMS. Official Annex A control IDs run **A.2.2–A.10.4** (38 controls; there is no A.1 control set). The official PDF is paywalled. [`iso-42001.md`](../packages/python/hummbl-governance/docs/coverage/iso-42001.md) on this tree stops at **A.10.3** (A.10.2 allocation of responsibility, A.10.3 suppliers). This file uses those in-tree IDs. **A.10.4 is unverified against the paid PDF**; no title is invented here.
3. **IETF** has **no AI-governance RFC** and **no agent working group** as of 2026-08-31. Agent-delegation work is individual Internet-Drafts (not WG-adopted). **RFC 9943** (SCITT architecture) and **RFC 9942** (COSE Receipts) are both **Proposed Standard, June 2026**. RFC 9942 header parameters: **394 `receipts` / 395 `vds` / 396 `vdp`**. They are evidence-envelope standards, not agent-authorization protocols. **`draft-ietf-oauth-identity-chaining-17`** is RFC Editor Queue, **Awaiting First editor**, with **no RFC number**. WIMSE **WIT / WIC / identifier** are identity credentials, not the agent-delegation I-Ds (HDP/AAT/asor/Liu/Sweeney).
4. The AIRC [crosswalks page](https://airc.nist.gov/airmf-resources/crosswalks/) lists a NIST AI RMF ↔ ISO/IEC 42001 walk as **Microsoft-submitted**, not NIST-authored. Inclusion “does not imply NIST endorsement.” **INCITS/AI** walks exist for **ISO/IEC 23894** and **ISO/IEC 42005**. This file does **not** repeat any claim that NIST publishes an official 42001 crosswalk.

**DCT is not IETF.** Google DeepMind's Delegation Capability Tokens (arXiv 2602.11865, cited by `draft-williams-intent-token-01`) are a paper, not an Internet-Draft. See the ⛔ row in [`ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md).

### Foreign overlays (not families this file owns)

These are citations only. They do not get columns in §5.

- **EU AI Act / Digital Omnibus (foreign).** Regulation (EU) 2026/1744 (Digital Omnibus on AI), 8 July 2026, OJ L 24.7.2026, ELI [http://data.europa.eu/eli/reg/2026/1744/oj](http://data.europa.eu/eli/reg/2026/1744/oj). **Recital 40** of that instrument (official EUR-Lex HTML) sets Chapter III Sections 1–3 application to **2 December 2027** for systems high-risk under Art. 6(2) and Annex III, and **2 August 2028** for Art. 6(1) and Annex I. The general application date **2 August 2026 was not moved**. Control rows remain in [`eu-ai-act.md`](../packages/python/hummbl-governance/docs/coverage/eu-ai-act.md) (last reviewed 2026-05-14, before OJ publication).
- **COSAiS / NISTIR 8605D.** NISTIR 8605D “Using Agentic AI: Single Agent and Multi-Agent” — series targeted to finalize in **2027**; **no overlay control IDs yet**. No 8605D numbers are invented here. Fleet-as-unit remains `silent` until that series publishes IDs.

## 4. Coverage legend for this file

Coarser than ADR-001 control rows. Primitive↔family only. **No checkmark-as-compliance.**

| State | Meaning |
|---|---|
| `maps` | The primitive implements something the family actually asks for (engineering only) |
| `partial` | The primitive overlaps the family; a named remainder sits on the customer, another primitive, or an unmet MUST |
| `silent` | The family has no requirement that this primitive addresses |
| `conflict` | The primitive contradicts a live MUST in a named document |

ADR-001 glyphs (`✅`/`🟡`/`⚪`/`⛔`) belong in the per-framework matrices, not as a score here.

## 5. Primitive matrix (P1–P34)

Every inventory entry gets a row. ISO Annex A cells are `partial` (customer AIMS boundary) when the primitive is an in-process library, not `maps`. IETF cells name a live draft/RFC or `silent`. NIST IDs are AIRC Core / `nist-ai-rmf.md`.

| ID | Primitive | IETF | NIST AI RMF | ISO 42001 | Notes / gap |
|---|---|---|---|---|---|
| P1 | `kernel` — receipts, identity, roles, laws, evidence, sequence, authority, schedule | `partial` — RFC 9943/9942 (HMAC receipts ≠ COSE) | `maps` GOVERN 4.3 (`GV-4.3`); `partial` GOVERN 1.3 (`GV-1.3`) | `partial` Clause 8 / Clause 9 | In-process OS; not an AIMS and not SCITT |
| P2 | `kill_switch` — four halt modes | `silent` | `maps` GOVERN 1.7 (`GV-1.7`), MANAGE 2.4 (`MG-2.4`); 600-1 points at this existing MANAGE 2.4 Core ID (not a new ID) | `partial` Clause 8 / A.6.2.6 | Runtime halt; decommissioning procedure authorship is org |
| P3 | `circuit_breaker` | `silent` | `maps` GOVERN 6.2 (`GV-6.2`), MANAGE 2.4 (`MG-2.4`) | `partial` Clause 8 | Third-party failure containment; not a cert control |
| P4 | `cost_governor` | `silent` | `maps` MAP 1.5 (`MP-1.5`); `partial` GOVERN 1.3 (`GV-1.3`) | `partial` Clause 6 / A.4.5 | Budget caps as risk-tolerance enforcement; tolerance setting is org |
| P5 | `delegation` — HMAC-SHA256 capability tokens | `conflict` AAT-01 / HDP-01 (HMAC-SHA256 shared-secret vs Ed25519 MUST / public verify); AAT forbids HS256 | `partial` GOVERN 2.1 (`GV-2.1`); `maps` MAP 3.5 (`MP-3.5`) (existing Core ID; 600-1 flags it as agent-relevant) | `partial` A.3.2 / A.10.2 (in-tree; A.10.4 not used) | No append-only hop chain **in the token**. `authenticate_token` does not evaluate caveats |
| P6 | `audit_log` | `partial` RFC 9943 (append-only HMAC JSONL ≠ COSE_Sign1) | `maps` GOVERN 4.2 (`GV-4.2`) | `partial` A.6.2.8 | Evidence log, not a transparency service |
| P7 | `identity` — agent registry, trust tiers | `partial` WIMSE identifier-03 / WIT/WIC (string IDs, not WIT/WIC credentials; identity, not a delegation I-D) | `partial` GOVERN 2.1 (`GV-2.1`) | `partial` A.3.2 | Org role definition remains leadership. GOVERN 3.2 is ⚪ in `nist-ai-rmf.md` (org/HR); 600-1 points at that existing Core ID but it is not mapped as `maps` here |
| P8 | `schema_validator` | `silent` | `maps` MAP 2.1 (`MP-2.1`); `partial` MAP 2.2 (`MP-2.2`) (existing Core ID; 600-1 flags it as agent-relevant) | `partial` A.6.2.2 | Structural validation only |
| P9 | `coordination_bus` — append-only TSV + HMAC | `partial` RFC 9943 / RFC 9942 at most (HMAC TSV ≠ COSE Receipts) | `maps` GOVERN 4.2 (`GV-4.2`); `partial` GOVERN 5.1 (`GV-5.1`) | `partial` Clause 7 / A.6.2.8 | Bus is not SCITT |
| P10 | `compliance_mapper` | `silent` | `partial` GOVERN 1.1 (`GV-1.1`), GOVERN 1.4 (`GV-1.4`) | `partial` A.2.3 | Mapping mechanism; legal interpretation is org |
| P11 | `health_probe` | `silent` | `maps` GOVERN 1.5 (`GV-1.5`) | `partial` Clause 9 | Monitoring substrate; review cadence is org |
| P12 | `output_validator` | `silent` | `partial` MEASURE 2.11 (`MS-2.11`) | `partial` A.9.2 | PII/injection/blocklists; fairness methodology is org |
| P13 | `capability_fence` | `partial` AAT-01 (semantic attenuation); `conflict` on HMAC vs Ed25519 MUST | `maps` MANAGE 3.2 (`MG-3.2`) | `partial` A.4.4 | **This is where caveats actually evaluate** (`CapabilityFence._resolve` + `caveat_validator`) |
| P14 | `stride_mapper` | `silent` | `partial` MAP 3.2 (`MP-3.2`), MAP 4.1 (`MP-4.1`) | `partial` Clause 6 | Threat categories; residual-risk acceptance is org |
| P15 | `lifecycle` — NIST-shaped orchestrator | `silent` | `maps` GOVERN+MAP+MEASURE+MANAGE composition (`lifecycle.py` wires GV/MP/MS/MG) | `partial` Clause 8 / A.6 | Already composes kill switch, circuit breaker, cost governor, delegation, audit, identity, health |
| P16 | `contract_net` | `silent` | `silent` | `silent` | Fleet task-allocation protocol; none of the three families require it |
| P17 | `convergence_guard` | `silent` | `partial` MEASURE 3.2 (`MS-3.2`) | `partial` Clause 10 | Emergent-pattern detector; treatment policy is org |
| P18 | `reward_monitor` | `silent` | `partial` MEASURE 3.2 (`MS-3.2`) | `partial` Clause 9 | Drift detector; measurement program is org |
| P19 | `lamport_clock` | `silent` | `silent` | `silent` | Causal order for agent events; no family MUST |
| P20 | `reasoning` | `silent` | `partial` MEASURE 2.9 (`MS-2.9`) | `partial` A.6.2.3 | Decision tracing; model-card authorship is org |
| P21 | `eal` — execution assurance receipts | `partial` RFC 9943 (HMAC execution receipts ≠ SCITT) | `partial` MEASURE 2.5 (`MS-2.5`) | `partial` A.6.2.4 | Arbiter-verified code quality in receipts |
| P22 | `physical_governor` | `silent` | `partial` MEASURE 2.6 (`MS-2.6`) | `partial` A.6.2.6 | Kinematic/pHRI constraints; safety case is org |
| P23 | `errors` (support artifact) | `silent` | `silent` | `silent` | Error taxonomy; not a primitive under the admission criterion |
| P24 | `failure_modes` (support artifact) | `silent` | `silent` | `silent` | Catalog only; retained for P1–P26 numbering continuity |
| P25 | `evolution_lineage` | `silent` | `partial` MANAGE 4.1 (`MG-4.1`) (existing Core ID; 600-1 flags it as agent-relevant) | `partial` Clause 10 | In-memory variant lineage; continual-improvement program is org |
| P26 | `ValidationError` (support artifact) | `silent` | `silent` | `silent` | Exception type exported from P8; not a primitive |
| P27 | `canon_registry` | `silent` | `partial` GOVERN 1.2 (`GV-1.2`) | `partial` A.2.2 / Clause 5 | Operator approval registry; AI policy authorship is leadership |
| P28 | `rollback` | `silent` | `partial` MANAGE 2.4 (`MG-2.4`) | `partial` Clause 10 | Reversibility checks; rollback policy is org |
| P29 | `recovery_verifier` | `silent` | `partial` GOVERN 4.3 (`GV-4.3`), MANAGE 2.4 (`MG-2.4`) | `partial` Clause 10 | Recovery verification; root-cause program is org |
| P30 | `receipt_integrity_monitor` | `partial` RFC 9942 (HMAC hash-chain ≠ COSE Receipts) | `partial` MEASURE 2.7 (`MS-2.7`) | `partial` A.6.2.8 | Sequence/hash/timestamp checks on HMAC receipts |
| P31 | `contestability` | `silent` | `partial` GOVERN 5.2 (`GV-5.2`) | `partial` A.3.3 | Contest-status tracking; external-appeal program is org |
| P32 | `doctrine_amendment` | `silent` | `partial` GOVERN 1.2 (`GV-1.2`) | `partial` A.2.2 / Clause 5 | Doctrine changes with operator approval; not an AIMS policy cycle |
| P33 | `authority_sweeper` | `silent` (HDP/AAT also specify no live revocation protocol) | `partial` GOVERN 2.1 (`GV-2.1`) | `partial` A.3.4 / A.10.2 (in-tree; A.10.4 not used) | Revocation consistency in-process; not cascade-revoke of hop chains |
| P34 | `trust_adjuster` | `partial` WIMSE identity (trust tiers ≠ WIT) | `partial` GOVERN 2.1 (`GV-2.1`) | `partial` A.3.2 | Severity-classified trust-tier changes; org authority still required |

**Fleet-as-unit** (not a P-row): `silent` in IETF, NIST AI RMF, and ISO 42001. All three govern an AI system or an organization, not a fleet of agents as the unit of control. See [`FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md).

## 6. Family-to-family (compact)

NIST function ↔ ISO 42001 clause pairing uses the existing coverage files. The AIRC Microsoft walk is cited **only as a community source, labeled Microsoft** — not as a NIST official crosswalk. IETF overlay names live drafts/RFCs from [`ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md).

| NIST AI RMF 1.0 function | ISO/IEC 42001:2023 (Microsoft AIRC walk as community source) | IETF overlay (2026-08-31 live) |
|---|---|---|
| GOVERN | Clauses 4–5, 7; Annex A.2 policies, A.3 internal organization (Microsoft: e.g. GOVERN 2.1 ↔ 5.3 / 7.1–7.4 / A.3.2) | WIMSE WIT/WIC/identifier (identity credentials, **not** agent-delegation I-Ds); `draft-klrc-aiagent-auth-03` (AIMS as a draft term, not ISO 42001) |
| MAP | Clauses 6 and 8; Annex A.5 impact assessment | `silent` — no IETF context-mapping RFC |
| MEASURE | Clause 9 performance evaluation | RFC 9943 SCITT / RFC 9942 COSE Receipts (header params 394 `receipts` / 395 `vds` / 396 `vdp`; evidence envelope, not measurement methodology) |
| MANAGE | Clauses 8 and 10; Annex A.6 lifecycle, A.9 use | HDP-01 (provenance hops); AAT-01 (attenuating JWT, Ed25519 MUST); asor-00 (`par_hash` JWT); Liu-00 (`delegation_chain` JWT, AS-mediated); Sweeney-00 (online DPoP); `draft-ietf-oauth-identity-chaining-17` (RFC Ed Queue, Awaiting First editor, **no RFC number** — **not** agent-chain tokens) |

INCITS/AI community walks (not this matrix): ISO/IEC 23894 and ISO/IEC 42005 on the same AIRC crosswalks page.

## 7. Named residual gaps

1. **HMAC vs Ed25519.** Shipped tokens and receipts are HMAC-SHA256 shared-secret. AAT-01 MUST support Ed25519 and MUST NOT use HS256/HS384/HS512. HDP-01 is Ed25519 issuer-signed hops. WIMSE WIT forbids symmetric algorithms. This is `conflict` on P5, not a documentation mismatch.
2. **No append-only hop chain in the token.** `DelegationToken` is a single JSON object. `DelegationContext` tracks in-process depth; it is not an HDP/AAT/asor hop array carried on the wire.
3. **`authenticate_token` does not evaluate caveats.** Caveats are stored on the token and evaluated by `CapabilityFence` (P13) when a `caveat_validator` is supplied. Callers that only call `authenticate_token` / `validate_token` do not enforce caveats.
4. **GAP-001** — no production-use receipt in `landing-claims.json`. Package `docs/public-claims.md` still lists production-use as “needs receipt.” This mapping does not mint that receipt.
5. **ISO 42001 certification strategy is unresolved.** This file does not decide whether to pursue registrar certification. ISO 42001 remains an organizational AIMS; the library can at most supply evidence substrate. **A.10.4** is not mapped: in-tree `iso-42001.md` stops at A.10.3; the paid PDF was not opened, so no A.10.4 title is asserted.
6. **Coverage matrices last reviewed 2026-05-14 against hummbl-governance v0.8.0.** NIST and ISO row evidence in those files may lag v1.4.2 primitives (P27–P34). `eu-ai-act.md` predates OJ publication of Regulation (EU) 2026/1744. Re-review is a follow-on; this PR does not rewrite those ~95 files.
7. **IETF agent-delegation drafts are not WG-adopted.** Treating them as ratifiable MUSTs for product crypto is premature; treating HMAC as satisfying those MUSTs is false. Both remain true. WIMSE WIT/WIC/identifier remain identity credentials, not a substitute for HDP/AAT hop protocols.
8. **COSAiS / NISTIR 8605D** has no overlay control IDs yet (series targeted to finalize in 2027). Fleet-as-unit stays `silent` in IETF, NIST AI RMF 1.0 Core, and ISO 42001 until that series publishes IDs. No 8605D numbers are invented here.

## 8. Product language (from April v0.1, still in force)

Say: HUMMBL provides **framework-mapped evidence support** for named NIST AI RMF subcategories, ISO 42001 AIMS controls (customer boundary), and named IETF documents, as enumerated in the coverage matrices.

Do not say: HUMMBL is NIST-aligned, ISO 42001 certified, IETF-compliant, DCT-compliant, or that HMAC tokens are HDP/AAT/SCITT.

Internal engineering mappings (this file, `ietf.md`, `nist-ai-rmf.md`, `iso-42001.md`) stay internal until ADR-001 evidence validation plus operator/legal review.
