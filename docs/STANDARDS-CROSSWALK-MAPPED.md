# HUMMBL standards crosswalk — already-mapped families (EU / GDPR / ISO 27001 / NIST CSF / OWASP)

**Status:** internal engineering mapping
**Date:** 2026-08-31
**Last reviewed:** 2026-08-31
**Scope:** primitive↔family overlay for six families that already have ADR-001 coverage matrices
**Sibling:** [`docs/STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md) (IETF / NIST AI RMF / ISO 42001; may land via PR 92 — path is reserved even if that file is not on this tree)

This file does **not** replace the per-framework coverage matrices. Those remain the complete control-row workpapers. This is a second primitive-level walk: one row per inventory entry, IDs copied from the cited coverage files only.

## 1. Header — what this file is not

This document is **not** a certification, **not** a legal opinion, and **not** a public claim that HUMMBL fulfills or is certified against any standard.

- **[ADR-001](../packages/python/hummbl-governance/docs/adr/ADR-001-coverage-matrix-not-self-grade.md)** governs: no self-grades, no percentages, no letter scores, no public “fulfills ALL” headline without a complete validated matrix. This file is coarser than ADR-001 (primitive↔family, not every control row).
- **LANDING-013** still governs: technical evidence generation and engineering mappings only.
- Public product language: claim **framework-mapped evidence support**, not blanket compliance.
- **No checkmark-as-compliance.** ADR-001 glyphs (`✅` / `🟡` / `⚪` / `⛔`) belong in the per-framework matrices, not as a score here.

HUMMBL version on this tree: **hummbl-governance v1.4.2** (`packages/python/hummbl-governance/pyproject.toml`). Canonical primitive inventory: [`packages/python/hummbl-governance/PRIMITIVES.md`](../packages/python/hummbl-governance/PRIMITIVES.md) (34 entries P1–P34; 31 irreducible primitives after excluding support artifacts P23, P24, P26).

## 2. What already exists (do not fork)

| Artifact | Role | Notes |
|---|---|---|
| [`packages/python/hummbl-governance/docs/coverage/eu-ai-act.md`](../packages/python/hummbl-governance/docs/coverage/eu-ai-act.md) | Full EU AI Act article + annex rows | Last reviewed **2026-05-14**, HUMMBL v**0.8.0**, **draft**. **126 rows — not duplicated here.** |
| [`packages/python/hummbl-governance/docs/coverage/gdpr.md`](../packages/python/hummbl-governance/docs/coverage/gdpr.md) | GDPR 99 articles | Same draft caveat (2026-05-14 / v0.8.0) |
| [`packages/python/hummbl-governance/docs/coverage/iso-27001.md`](../packages/python/hummbl-governance/docs/coverage/iso-27001.md) | ISO/IEC 27001:2022 Clauses 4–10 + Annex A | Same draft caveat |
| [`packages/python/hummbl-governance/docs/coverage/nist-csf.md`](../packages/python/hummbl-governance/docs/coverage/nist-csf.md) | NIST CSF 2.0 106 subcategories | Same draft caveat |
| [`packages/python/hummbl-governance/docs/coverage/owasp-llm.md`](../packages/python/hummbl-governance/docs/coverage/owasp-llm.md) | OWASP LLM Top 10 (2025) | Last reviewed 2026-05-14; HUMMBL version field in that file is v1.2.2 |
| [`packages/python/hummbl-governance/docs/coverage/owasp-agentic.md`](../packages/python/hummbl-governance/docs/coverage/owasp-agentic.md) | OWASP Agentic Top 10 (ASI01–ASI10) | Same draft caveat (2026-05-14 / v0.8.0) |
| [`docs/STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md) | Sibling walk: IETF / NIST AI RMF / ISO 42001 | Path reserved; may exist only on PR 92 |
| [`packages/python/hummbl-governance/docs/coverage/ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md) | IETF ADR-001 matrix (PR 92) | First SCITT / RFC 9943 mapping; **not a column here** |
| [`packages/python/hummbl-governance/docs/coverage/README.md`](../packages/python/hummbl-governance/docs/coverage/README.md) | Mechanical index | Counts from `scripts/count_coverage_rows.py` only |

The six coverage files above last reviewed **2026-05-14** against hummbl-governance **v0.8.0**. This walk does **not** silently upgrade their ✅ counts or rewrite those matrices. P27–P34 were added after that review; they stay `silent` in every column because those IDs are not named in the cited files.

## 3. Family facts (2026-08-31)

IDs in §5 are copied from the cited coverage files. No control IDs are invented.

1. **EU AI Act** — Regulation (EU) 2024/1689. In-tree IDs: Art. 1–113 + Annexes I–XIII ([`eu-ai-act.md`](../packages/python/hummbl-governance/docs/coverage/eu-ai-act.md)).
2. **GDPR** — Regulation (EU) 2016/679. In-tree IDs: Art. 1–99 ([`gdpr.md`](../packages/python/hummbl-governance/docs/coverage/gdpr.md)).
3. **ISO/IEC 27001:2022** — In-tree IDs: Clauses 4–10 and Annex A.5.1–A.8.34 ([`iso-27001.md`](../packages/python/hummbl-governance/docs/coverage/iso-27001.md)).
4. **NIST CSF 2.0** (February 2024) — In-tree IDs: GV / ID / PR / DE / RS / RC subcategories ([`nist-csf.md`](../packages/python/hummbl-governance/docs/coverage/nist-csf.md)).
5. **OWASP LLM Top 10 (2025)** — In-tree IDs: LLM01:2025–LLM10:2025 ([`owasp-llm.md`](../packages/python/hummbl-governance/docs/coverage/owasp-llm.md)).
6. **OWASP Agentic Top 10 (December 2025)** — In-tree IDs: ASI01–ASI10 ([`owasp-agentic.md`](../packages/python/hummbl-governance/docs/coverage/owasp-agentic.md)).

**DCT is not IETF.** If DCT is mentioned: HUMMBL `DCT` / `DCT_SECRET` is a historical HMAC alias for delegation tokens. Google DeepMind Delegation Capability Tokens (arXiv 2602.11865) are a paper, not an Internet-Draft. IETF columns live in the sibling walk / `ietf.md`, not here.

### Foreign overlay (not a family this file owns)

**EU AI Act high-risk schedule.** Regulation (EU) 2026/1744 (Digital Omnibus on AI), Recital 40: Chapter III Sections 1–3 apply **2 December 2027** for systems high-risk under Art. 6(2) and Annex III, and **2 August 2028** for Art. 6(1) and Annex I. **Do not treat 2 August 2026 as the current Annex III / Art. 6(2) high-risk date.** Recital 40 records that the **general** application date 2 August 2026 was not moved; that is not the high-risk Chapter III §§1–3 date. Control rows remain in [`eu-ai-act.md`](../packages/python/hummbl-governance/docs/coverage/eu-ai-act.md) (last reviewed 2026-05-14, before OJ publication of 2026/1744). Art. 113 in that file still prints the pre-omnibus timeline — this walk does not rewrite that row.

## 4. Coverage legend for this file

Coarser than ADR-001 control rows. Primitive↔family only. **No checkmark-as-compliance.**

| State | Meaning |
|---|---|
| `maps` | The primitive is named in the cited coverage file as addressing that ID (engineering only) |
| `partial` | The primitive overlaps the ID; a named remainder sits on the customer, another primitive, or an unmet MUST |
| `silent` | The cited coverage file does not name this primitive against that family (or the family has no requirement the primitive addresses) |
| `conflict` | The primitive contradicts a live MUST in a named document |

A `maps` cell is **not** a claim that the article/control is fulfilled. The coverage matrix row remains the workpaper.

## 5. Primitive matrix (P1–P34)

Every inventory entry gets a row. Support artifacts P23 / P24 / P26 stay `silent`. Cells name IDs that exist in the cited coverage file.

| ID | Primitive | EU AI Act | GDPR | ISO 27001:2022 | NIST CSF 2.0 | OWASP LLM | OWASP Agentic | Notes / gap |
|---|---|---|---|---|---|---|---|---|
| P1 | `kernel` — receipts, identity, roles, laws, evidence, sequence, authority, schedule | `partial` Art. 9, Art. 12 | `partial` Art. 24, Art. 30 | `partial` Clause 7.5, A.8.15 | `partial` PR.PS-04 | `silent` | `silent` | OS substrate; cited matrices name `audit_log` / bus, not `kernel` |
| P2 | `kill_switch` — four halt modes | `maps` Art. 5, Art. 14; `partial` Art. 20, Art. 93 | `maps` Art. 22; `partial` Art. 21 | `maps` A.5.26; `partial` A.5.24 | `maps` RS.MI-01; `partial` RS.MI-02 | `maps` LLM06:2025, LLM10:2025; `partial` LLM01:2025 | `maps` ASI01, ASI10; `partial` ASI06 | Halt primitive; corrective-action / eradication policy is org |
| P3 | `circuit_breaker` | `maps` Art. 15; `partial` Art. 5, Art. 93 | `maps` Art. 32 | `partial` A.5.29, A.8.6 | `maps` PR.IR-03 | `maps` LLM10:2025 | `maps` ASI08, ASI10 | CLOSED/HALF_OPEN/OPEN; not a cert control |
| P4 | `cost_governor` — ALLOW/WARN/DENY | `partial` Art. 51 | `silent` | `partial` A.8.6 | `partial` GV.RM-02, PR.IR-04 | `maps` LLM10:2025 | `maps` ASI10 | Compute/budget caps; FLOP classification and risk appetite are org |
| P5 | `delegation` — HMAC-SHA256 capability tokens | `maps` Art. 14, Art. 86; `partial` Art. 25 | `maps` Art. 22, Art. 29; `partial` Art. 19, Art. 28 | `maps` A.5.3, A.5.15, A.5.18, A.8.2, A.8.3, A.8.5 | `maps` GV.RR-01, PR.AA-01–PR.AA-05 | `maps` LLM06:2025; `partial` LLM01:2025 | `maps` ASI03, ASI07; `partial` ASI02, ASI05 | HMAC tokens; DPA / legal contract remains org. DCT-the-paper is not IETF |
| P6 | `audit_log` | `maps` Art. 9, Art. 18, Art. 19; `partial` Art. 17 | `maps` Art. 5, Art. 7, Art. 15–Art. 17, Art. 24 | `maps` A.5.28, A.5.33, A.8.15 | `maps` PR.PS-04, DE.CM-03 | `maps` LLM02:2025, LLM09:2025 | `maps` ASI07; `partial` ASI06, ASI09 | Append-only JSONL; retention configuration is org |
| P7 | `identity` — agent registry, trust tiers | `silent` | `silent` | `partial` A.5.16 | `partial` GV.OC-02 | `silent` | `maps` ASI03, ASI10; `partial` ASI06 | EU/GDPR/LLM matrices do not name `identity.py` |
| P8 | `schema_validator` | `maps` Art. 10 | `maps` Art. 9, Art. 10, Art. 25; `partial` Art. 6, Art. 8 | `maps` A.5.12 | `maps` ID.AM-05 | `maps` LLM02:2025, LLM03:2025, LLM05:2025 | `partial` ASI02 | Structural validation; lawful-basis determination is org |
| P9 | `coordination_bus` | `maps` Art. 9, Art. 12, Art. 19, Art. 72 | `maps` Art. 5, Art. 24, Art. 30 | `maps` A.5.28, A.8.15, A.8.16 | `maps` PR.PS-04; `partial` DE.CM-01 | `maps` LLM09:2025 | `silent` | Append-only TSV + HMAC; Agentic matrix does not name the bus |
| P10 | `compliance_mapper` | `maps` Art. 8, Art. 11, Art. 13, Art. 21, Art. 47; `partial` Art. 4, Art. 6, Art. 40, Art. 43 | `maps` Art. 13–Art. 15, Art. 20, Art. 30, Art. 31 | `partial` A.5.31, A.5.36 | `partial` GV.OC-03 | `silent` | `maps` ASI01, ASI03 | Mapping mechanism; legal interpretation is org |
| P11 | `health_probe` | `partial` Art. 89 | `silent` | `partial` A.5.30 | `partial` GV.OV-03, PR.IR-04 | `silent` | `silent` | Monitoring substrate; Commission powers / BCM are org |
| P12 | `output_validator` | `silent` | `silent` | `partial` A.5.10, A.8.7, A.8.12 | `silent` | `maps` LLM05:2025 | `silent` | Named in ISO 27001 + LLM05; EU/GDPR/CSF/Agentic files do not name it |
| P13 | `capability_fence` | `silent` | `maps` Art. 10 | `partial` A.5.10, A.8.7, A.8.12 | `partial` PR.PS-05, PR.IR-01 | `silent` | `silent` | Soft sandbox; OS-level isolation is platform (ASI05 is Boundary in the Agentic matrix) |
| P14 | `stride_mapper` | `silent` | `silent` | `partial` A.5.7 | `maps` ID.RA-03; `partial` GV.RM-06, ID.RA-02 | `silent` | `maps` ASI01 | Threat categories; residual-risk acceptance is org |
| P15 | `lifecycle` — NIST-shaped orchestrator | `silent` | `silent` | `partial` A.5.30 | `partial` GV.RM-03, GV.SC-09, ID.RA-05, RC.RP-02, RC.RP-04 | `silent` | `silent` | Composes P2/P3/P4/P5/P6/P7/P11; EU/GDPR/OWASP files do not name `lifecycle.py` |
| P16 | `contract_net` | `silent` | `silent` | `silent` | `partial` GV.SC-05 | `silent` | `silent` | Task-allocation protocol; only CSF supplier-contract cell names it |
| P17 | `convergence_guard` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Not named in the six cited matrices |
| P18 | `reward_monitor` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Not named in the six cited matrices |
| P19 | `lamport_clock` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Causal order; no family MUST in the cited files |
| P20 | `reasoning` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Not named in these six files (appears in other matrices, e.g. ISO 42005) |
| P21 | `eal` — execution assurance receipts | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Not named in the six cited matrices |
| P22 | `physical_governor` | `silent` | `silent` | `silent` | `partial` PR.AA-06, DE.CM-02 | `silent` | `silent` | Kinematic/pHRI; facility physical security is org (ISO A.7.x is Boundary) |
| P23 | `errors` (support artifact) | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Error taxonomy; not a primitive under the admission criterion |
| P24 | `failure_modes` (support artifact) | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Catalog only; retained for P1–P26 numbering continuity |
| P25 | `evolution_lineage` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Not named in the six cited matrices |
| P26 | `ValidationError` (support artifact) | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Exception type exported from P8; not a primitive |
| P27 | `canon_registry` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Added after 2026-05-14 / v0.8.0 matrix review |
| P28 | `rollback` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same; not named in these six files |
| P29 | `recovery_verifier` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same |
| P30 | `receipt_integrity_monitor` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same |
| P31 | `contestability` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same (EU Art. 86 names `compliance_mapper` / bus / delegation, not this module) |
| P32 | `doctrine_amendment` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same |
| P33 | `authority_sweeper` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same |
| P34 | `trust_adjuster` | `silent` | `silent` | `silent` | `silent` | `silent` | `silent` | Same |

**Fleet-as-unit** (not a P-row): `silent` in all six families. They govern an AI system, a processing activity, an ISMS, a cybersecurity program, or a risk catalog — not a fleet of agents as the unit of control. See [`FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md).

## 6. How to read a cell

1. Open the coverage file in §2.
2. Find the named article / Annex A control / CSF subcategory / LLM or ASI ID.
3. The matrix row (✅ / 🟡 / ⚪) is the workpaper. This file only says the primitive is named there.
4. If you need IETF / NIST AI RMF / ISO 42001, use [`STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md) and [`ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md) — do not copy those IDs into this table.

## 7. Named residual gaps

1. **Cited matrices last reviewed 2026-05-14 against v0.8.0.** This walk does not rewrite them or upgrade their ✅ counts. P27–P34 stay `silent`.
2. **`eu-ai-act.md` Art. 113 / high-risk dates predates Regulation (EU) 2026/1744.** Recital 40 (2 December 2027 for Annex III / Art. 6(2) Chapter III §§1–3) is a foreign overlay here; the 126-row file is not edited.
3. **Several primitives are unnamed in one or more families** (P12/P13 in EU; P7 in EU/GDPR/LLM; P16–P21, P25, P27–P34 everywhere in this set). Unnamed ≠ “does not apply”; it means the 2026-05-14 workpaper did not cite that module.
4. **OWASP files are risk catalogs, not regulations.** `maps` means platform-layer overlap named in those files; application-layer remainder stays customer (LLM01/LLM04 🟡; ASI02/ASI06/ASI09 🟡; ASI05 ⚪).
5. **ISO 27001 certification and EU AI Act Notified Body assessment remain customer/third-party.** See each matrix header.
6. **Sibling IETF walk is out of scope.** Do not fight PR 89 (IETF rewrite) or PR 92 (IETF/NIST/ISO primitive crosswalk).
7. **2026 first-touch families** (CEN-CENELEC JTC 21, Microsoft ACS, CMMC 2.0, ISO/IEC 42006) are **not columns here**. They have new coverage files under `docs/coverage/`.

## 8. Product language

Say: HUMMBL provides **framework-mapped evidence support** for named articles/controls in the six coverage files, as enumerated there.

Do not say: HUMMBL fulfills the EU AI Act, is GDPR-certified, is ISO 27001 certified, is NIST CSF compliant, fulfills OWASP LLM/Agentic Top 10, or that a `maps` cell is a conformity assessment.

Internal engineering mappings (this file and the six matrices) stay internal until ADR-001 evidence validation plus operator/legal review.
