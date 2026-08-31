# Rumsfeld Map — HUMMBL standards surface (2026-08-31)

**Status:** internal engineering map  
**As of:** 2026-08-31  
**Scope:** organizing index for this PR’s mapped walk + first-touch coverage files, and for `STANDARDS-CROSSWALK*.md`  
**Governs / governed by:** [ADR-001](../packages/python/hummbl-governance/docs/adr/ADR-001-coverage-matrix-not-self-grade.md) · LANDING-013  

This file is **not** a score, **not** a certification, **not** a legal opinion, and **not** a public “fulfills ALL” claim. It is a discipline for sorting confidence, flagged gaps, disavowed knowledge, and blind-spot *shapes*. It does **not** replace [`STANDARDS-CROSSWALK-MAPPED.md`](./STANDARDS-CROSSWALK-MAPPED.md), [`STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md), or any `coverage/*.md` workpaper.

House style: [`docs/research/agentic-work-definitions/01-RUMSFELD-MAP.md`](https://github.com/hummbl-io/hummbl-governance/blob/main/docs/research/agentic-work-definitions/01-RUMSFELD-MAP.md) (quadrants + actions) and [`docs/research/rumsfeld-crosswalk/README.md`](https://github.com/hummbl-io/hummbl-governance/blob/main/docs/research/rumsfeld-crosswalk/README.md) (evidence grades A–D). Those files live in the archived `hummbl-governance` research tree, not on this public checkout.

Each quadrant demands a different response:

- **Known knowns (KK)** → codify, build on
- **Known unknowns (KU)** → research, instrument, bound
- **Unknown knowns (UK)** → surface, name, decide whether to keep or discard (Žižek: tacit / *disavowed*, not merely forgotten)
- **Unknown unknowns (UU)** → resilience, scenario, watch — *shapes of blind spots*, not invented document names

**ISO/IEC 42004 does not exist.** Do not invent it. AIMS guidance work item AWI **42003** has no confirmed public text on this review and is not a file in this PR.

---

## 2×2 — Known / Unknown × Known / Unknown

|  | **Known to this tree / evidence** | **Unknown to this tree / evidence** |
|---|---|---|
| **Known as a category** | **KK** — verified in-tree facts. Codify. | **UK** — tacit or disavowed. Surface and name. Keep or discard. |
| **Unknown as a value / text / ID** | **KU** — flagged gaps with a measurement path. Research, instrument, bound. | **UU** — blind-spot shapes. Watch. Do not mint fake standard names. |

```
                    ┌──────────────────────────┬──────────────────────────┐
                    │   KNOWN TO THIS TREE      │   UNKNOWN TO THIS TREE    │
  ──────────────────┼──────────────────────────┼──────────────────────────┤
   KNOWN AS         │   KK  Known knowns        │   UK  Unknown knowns      │
   A CATEGORY       │   Verified. Cited.        │   Tacit / disavowed       │
                    │   Codify & build on.      │   Surface, keep/discard.  │
  ──────────────────┼──────────────────────────┼──────────────────────────┤
   UNKNOWN AS       │   KU  Known unknowns      │   UU  Unknown unknowns    │
   VALUE / TEXT     │   Flagged gaps.           │   Blind-spot shapes.      │
                    │   Research & instrument.  │   Resilience & watch.     │
                    └──────────────────────────┴──────────────────────────┘
```

---

## Pointers (this surface)

| Artifact | Role |
|---|---|
| This file | Organizing map. Not a replacement for the walks or matrices. |
| [`STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md) | IETF / NIST AI RMF / ISO 42001 primitive walk. **404 on `main`**; exists on PR 92 only. Path reserved. Do not fight PR 92. |
| [`STANDARDS-CROSSWALK-MAPPED.md`](./STANDARDS-CROSSWALK-MAPPED.md) | This PR. Primitive overlay for six already-mapped families. Landing path while the IETF sibling 404s. |
| [`packages/python/hummbl-governance/docs/coverage/`](../packages/python/hummbl-governance/docs/coverage/) | ADR-001 control-row workpapers. Mechanical index: [`README.md`](../packages/python/hummbl-governance/docs/coverage/README.md). |
| [`packages/python/hummbl-governance/docs/coverage/ietf.md`](../packages/python/hummbl-governance/docs/coverage/ietf.md) | IETF matrix on PR 92. RFC 8693 `act` / `may_act` is a **follow-on**, not this PR. |
| [`DELEGATION-IETF-GAP-ANALYSIS.md`](./DELEGATION-IETF-GAP-ANALYSIS.md) | 2026-08-21 HMAC / no-chain / JCS audit. No product-code change then or in this PR. |
| [`FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md) | Fleet-as-unit mapping. Open question 4 (ACS verdicts) remains open. |

---

## Quadrant I: Known knowns

> Verified on this tree or against a primary text opened this session. Codify and build on.

### KK-1: ADR-001 and LANDING-013 bind the public claim surface

No self-grades, no letter scores, no public “fulfills ALL” without a complete validated matrix. Product language is **framework-mapped evidence support**. This map inherits that.

**Evidence grade:** A (in-tree ADR).  
**Action:** Codify. Do not reopen as a score.

### KK-2: The primitive inventory is 34 entries (P1–P34)

Canonical list: [`PRIMITIVES.md`](../packages/python/hummbl-governance/PRIMITIVES.md). Support artifacts P23 / P24 / P26 stay silent on the mapped walk. Package on this tree: hummbl-governance **v1.4.2**.

**Evidence grade:** A (in-tree inventory + `pyproject.toml`).

### KK-3: Six families already have complete ADR-001 matrices with real IDs

EU AI Act, GDPR, ISO/IEC 27001:2022, NIST CSF 2.0, OWASP LLM Top 10, OWASP Agentic Top 10. Those files last reviewed **2026-05-14** (four of six at v**0.8.0**; `owasp-llm.md` header **v1.2.2**). This PR does **not** upgrade their ✅ counts or versions.

**Evidence grade:** A (file headers + mapped-walk honesty pass).

### KK-4: The mapped walk copies primitive↔article links; it does not invent them

[`STANDARDS-CROSSWALK-MAPPED.md`](./STANDARDS-CROSSWALK-MAPPED.md): `maps` / `partial` / `silent` / `conflict`. P13 `capability_fence` is silent on EU (not in `eu-ai-act.md`). P15 `lifecycle` is silent on GDPR and OWASP Agentic (those files do not name `lifecycle.py`). P4 `cost_governor` is silent on Agentic. P12 LLM05 evidence is `schema_validator`, not `output_validator`.

**Evidence grade:** A (co-occurrence check against the six files, 2026-08-31).  
**Highest-leverage KK.**

### KK-5: Recital 40 moves Annex III / Art. 6(2) Chapter III §§1–3 to 2 December 2027

Regulation (EU) 2026/1744. General application 2 August 2026 was **not** moved. That is not the current high-risk Chapter III §§1–3 date. Named as a foreign overlay on the mapped walk; `eu-ai-act.md` Art. 113 is **not** rewritten in this PR (see UK-4).

**Evidence grade:** B (named from the mapped walk / operator brief; OJ text not re-fetched as a blob here).

### KK-6: Seven first-touch coverage files exist on this PR

[`cen-clc-jtc21.md`](../packages/python/hummbl-governance/docs/coverage/cen-clc-jtc21.md) · [`microsoft-acs.md`](../packages/python/hummbl-governance/docs/coverage/microsoft-acs.md) · [`cmmc-2.md`](../packages/python/hummbl-governance/docs/coverage/cmmc-2.md) · [`iso-42006.md`](../packages/python/hummbl-governance/docs/coverage/iso-42006.md) · [`mcp-authorization.md`](../packages/python/hummbl-governance/docs/coverage/mcp-authorization.md) · [`etsi-en-304-223.md`](../packages/python/hummbl-governance/docs/coverage/etsi-en-304-223.md) · [`nistir-8605.md`](../packages/python/hummbl-governance/docs/coverage/nistir-8605.md). None claims public fulfillment. None is a mapped-walk column.

**Evidence grade:** A (files on this branch).

### KK-7: Fleet counts are mechanical

`scripts/count_coverage_rows.py` after the seven files: **102** matrices / **2965** data rows; ✅ **1520** (existing-matrix fulfilled **not** upgraded); 🟡 **679**; ⚪ **764**; unmarked **1**.

**Evidence grade:** A (script output, 2026-08-31).

### KK-8: DCT-the-token is not IETF

HUMMBL `DCT` / `DCT_SECRET` is a historical HMAC alias. Google DeepMind Delegation Capability Tokens (arXiv 2602.11865) are a paper, not an Internet-Draft. IETF columns live on PR 92 / `ietf.md`, not on the mapped walk.

**Evidence grade:** A (mapped-walk header + [`DELEGATION-IETF-GAP-ANALYSIS.md`](./DELEGATION-IETF-GAP-ANALYSIS.md)).

### KK-9: Shipped MCP servers are STDIO, not HTTP resource servers

Governance, bif, cognition, bus, and `base120-mcp` take env credentials. MCP Authorization **2026-07-28**: HTTP SHOULD conform; STDIO SHOULD NOT. No MCP conformance claim.

**Evidence grade:** A (in-tree `mcp_server.py` files + spec page opened this session).

### KK-10: ISO 42006 is a certification-body standard; ISO 42004 is not a standard

42006 = additional requirements to ISO/IEC 17021-1 for bodies that certify ISO 42001 AIMS. Almost all rows Boundary. **No ISO 42004.** Do not collapse 42006 with 42001 or 42005.

**Evidence grade:** A (ISO page + `iso-42006.md`).

---

## Quadrant II: Known unknowns

> Gaps we can name. Research, instrument, bound. Mapping work that lands a verified ID list moves **KU → KK**.

### KU-1: P27–P34 have no cells in the six 2026-05-14 matrices

`canon_registry`, `rollback`, `recovery_verifier`, `receipt_integrity_monitor`, `contestability`, `doctrine_amendment`, `authority_sweeper`, `trust_adjuster` stay `silent` because those modules were added after the last review of the six column files.

**Bound:** do not invent `maps` cells.  
**Instrument:** re-review those six files against v1.4.2 (a later PR).  
**Evidence grade:** B.

### KU-2: CMMC Level 2 practice IDs were not copied

[`cmmc-2.md`](../packages/python/hummbl-governance/docs/coverage/cmmc-2.md) is domain-level (AC, AU, CM, …) plus programme rows. No invented `3.1.1`-style numbers. Official 800-171 / CMMC assessment-guide ID list is a follow-on after a verified in-tree copy.

**Evidence grade:** B.

### KU-3: COSAiS / NISTIR 8605A–D have no overlay control IDs

Series targeted to finalize **2027**. Jan 2026 outline examples (AC-06 structure; AC-03, AC-22, AU-02, …) are **not** Fulfilled IDs. Do not promote AC-2 examples. No separate FedRAMP / DoD AI overlay outside this series was found.

**Evidence grade:** A for “no IPD on the project page / outline says examples”; B for 2027 finalize language (outline).  
**Highest-risk KU** (a later overlay could invalidate every 8605 row overnight).

### KU-4: JTC 21 draft clause numbers are unpublished

[`cen-clc-jtc21.md`](../packages/python/hummbl-governance/docs/coverage/cen-clc-jtc21.md) is document-level. EN 18286:2026 has **no OJ citation** → no Art. 40 presumption. prEN 18228 / 18282 / 18229-* are drafts. Complements ETSI EN 304 223; do not collapse with prEN 18282.

**Evidence grade:** B.

### KU-5: Microsoft ACS verdicts on the circuit breaker are undecided

FLEET open question 4: adopt ACS `allow` / `warn` / `deny` / `escalate` / `transform`? [`microsoft-acs.md`](../packages/python/hummbl-governance/docs/coverage/microsoft-acs.md) names it. This PR does **not** decide it. `cost_governor` ALLOW/WARN/DENY is not ACS.

**Evidence grade:** B (in-tree open question).

### KU-6: RFC 8693 token-exchange (`act` / `may_act`) is missing from PR 92 `ietf.md`

Follow-on only. One sentence in the coverage README. Do not fight PR 92.

**Evidence grade:** B (operator brief + README pointer).

### KU-7: The IETF / NIST AI RMF / ISO 42001 primitive walk is not on `main`

[`STANDARDS-CROSSWALK.md`](./STANDARDS-CROSSWALK.md) 404s on `main`. This map points at the reserved path. Completeness of that walk is PR 92’s problem.

**Evidence grade:** A (path absent on this `main`).

### KU-8: HTTP MCP resource-server profile is unimplemented

PRM, CIMD, DCR, `resource`, audience, 401/403 `insufficient_scope`, step-up: all Boundary in [`mcp-authorization.md`](../packages/python/hummbl-governance/docs/coverage/mcp-authorization.md). Whether HUMMBL should grow an HTTP RS is a product decision, not a mapping decision.

**Evidence grade:** B.

### KU-9: EN 304 223 sub-provisions and TS 104 158 field IDs are not exploded

Thirteen principle titles from the opened EN PDF. TS 104 158-1 / 158-2 are document-level. National endorsement (dop/e) **30 September 2026**. Clause-level SHALL/SHOULD lists are a later bound.

**Evidence grade:** A for titles and dop/e (EN PDF opened); B for “not exploded.”

### KU-10: SOC 2 / ISO 23894 / 42005 / 5338 stay out of the primitive table this PR

Coverage files already exist (`soc2.md` v1.2.2; the three ISO files last reviewed **2026-06-25**). Whether they become mapped-walk columns is a later KU→KK move after an honesty pass like P13/P15.

**Evidence grade:** B.

---

## Quadrant III: Unknown knowns

> Tacit or **disavowed**. Žižek (2001): knowledge we have and will not acknowledge — not a memory lapse. **Surface and name. This PR does not resolve these.** Keep or discard is a later decision.

### UK-1: DCT-as-IETF

Coverage prose and `eu-ai-act.md` still say `DCT` as if it were a standards token. We also write “DCT is not IETF.” Both are on the same tree. The disavowal is the IETF-shaped name plus `DCT_SECRET` while [`DELEGATION-IETF-GAP-ANALYSIS.md`](./DELEGATION-IETF-GAP-ANALYSIS.md) records HMAC, no chain, not JCS.

**Named, not resolved.**  
**Evidence grade:** C (surfacing).  
**Highest-leverage UK** (every Art. 14 / delegation cell inherits the alias).

### UK-2: ~95 coverage files unused as a primitive overlay

The mapped walk uses **six** columns. The folder had ~95 matrices before this PR; it now has **102**. We treat the unused files as “already mapped” (fleet totals, README index) while refusing to put them on the primitive table or to re-review them. That is tacit completeness: a score-shaped index sitting next to an honest six-column walk.

**Named, not resolved.**  
**Evidence grade:** C.

### UK-3: Certification-strategy contradiction

[`FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md) (2026-08-21) records “Pursue ISO 42001 + NIST AI RMF dual adoption” and “Official crosswalk enables dual **compliance**.” ADR-001, LANDING-013, every new matrix header, and the mapped-walk product-language section forbid a public fulfillment / certification claim. The engineering surface says evidence; the decision log says compliance.

**Named, not resolved.**  
**Evidence grade:** C.

### UK-4: Stale 2 August 2026 high-risk date still printed as current

`eu-ai-act.md` Art. 113 still lists high-risk Chapter III Section 2 from **2 August 2026**. KK-5 names Recital 40 / **2 December 2027**. This PR adds a foreign overlay on the mapped walk and **does not edit** the 126-row file (operator: do not silently upgrade existing matrices). We know the row is stale and we keep shipping it as the workpaper.

**Named, not resolved.**  
**Evidence grade:** C (the contradiction is documented; the OJ row is not rewritten).  
**Highest-risk UK** (a reader of `eu-ai-act.md` alone still sees August 2026).

### UK-5: Fleet ✅ 1520 looks like a grade

ADR-001 forbids self-grades. The coverage README still prints **1520 ✅** next to 102 frameworks. The mechanical-count footnote is there; the glance-test is a score. We know this Goodhart channel (PR #28) and we keep the glyph totals.

**Named, not resolved.**  
**Evidence grade:** C.

### UK-6: “Lifecycle” in OWASP Agentic is INTENT-tuple narrative, not `lifecycle.py`

The Agentic file uses “lifecycle” in ASI01 prose. The mapped walk correctly stays `silent` for P15. The word still invites a false link.

**Named, not resolved.**  
**Evidence grade:** C.

### UK-7: Fleet-as-unit is how we talk and not how the six families govern

[`FLEET-GOVERNANCE-MAPPING.md`](./FLEET-GOVERNANCE-MAPPING.md) is the differentiator. The six mapped families govern a system, a processing activity, an ISMS, a program, or a risk catalog. The mapped walk marks fleet-as-unit `silent`. We still title work “fleet governance.”

**Named, not resolved.**  
**Evidence grade:** C.

---

## Quadrant IV: Unknown unknowns

> Blind-spot **shapes**. The research cannot name the document that is not here. **Do not invent standards.** ISO 42004 is not a UU item — it is a non-existent ID (KK-10).

### UU-1: A binding instrument that keys obligations to *fleet-as-unit*

Shape: a later Act, overlay, or insurer form that treats a multi-agent fleet as the regulated object. Today’s six families do not. Resilience: keep fleet mapping explicit and dated; do not back-port invented fleet IDs into EU/GDPR/ISO rows.

**Highest-risk UU.**  
**Evidence grade:** D (horizon).

### UU-2: A transport or runtime that is neither STDIO MCP nor ACS-host nor in-process library

Shape: a mandatory HTTP RS, a sidecar policy engine, or a non-LLM agent substrate that makes `mcp_server.py` / ACS-Q4 / HMAC DCT the wrong unit. Watch: MCP Authorization revisions; ACS 1.x; post-LLM runtimes.

**Evidence grade:** D.

### UU-3: An overlay ID list that arrives already selected (COSAiS, national 800-53, or a buyer baseline)

Shape: NISTIR 8605A–D IPD, or a FedRAMP/DoD AI overlay that *does* appear despite KK-3/KU-3. Resilience: keep 8605 as watch-only; refuse to promote outline examples.

**Evidence grade:** D.

### UU-4: National endorsement of EN 304 223 that is not the ETSI text

Shape: a Member-State standard that adds, drops, or renumbers principles after 30 September 2026. Resilience: principle IDs stay bound to the opened EN PDF; national texts get new rows, not silent aliases.

**Evidence grade:** D.

### UU-5: AIMS guidance published under a number people will call “42004”

Shape: ISO AWI **42003** (or another number) becoming a public text while buyers ask for “42004.” Resilience: do not create `iso-42004.md`; when a public text exists, use its real number.

**Evidence grade:** D.

### UU-6: This map treating a value conflict as a knowledge gap

Shape: UK-3 (cert vs evidence) is axiological. More research will not pick a public claim language. Resilience: keep ADR-001 as the claim-surface rule until an operator decision discards UK-3 one way or the other.

**Evidence grade:** D (the Rumsfeld map’s own failure mode; see house-style UU-8).

---

## Cross-quadrant

Mapping work **moves KU → KK** when a verified ID list lands in-tree (CMMC practices, COSAiS overlay tables, JTC 21 clauses, EN 304 223 SHALLs, HTTP MCP profile, P27–P34 named in a re-reviewed matrix). Until then those items stay KU.

**UK items are named, not resolved:** UK-1 DCT-as-IETF · UK-2 ~95 files unused as primitive columns · UK-3 cert-strategy contradiction · UK-4 stale August 2026 high-risk date.

| Quadrant | Count | Action |
|---|---|---|
| KK | 10 | Codify in the mapped walk + first-touch files (already done this PR) |
| KU | 10 | Bound (no invented IDs); instrument later |
| UK | 7 | Surface here; keep-or-discard is not this PR |
| UU | 6 | Watch; no fake document names |

### Highest leverage / highest risk

| | Item | Why |
|---|---|---|
| **Highest-leverage KK** | KK-4 | Honesty rule is the only thing that keeps the mapped walk from becoming a second self-grade |
| **Highest-risk KU** | KU-3 | Overlay IDs can appear and obsolete the watch matrix |
| **Highest-leverage UK** | UK-1 | The DCT alias structures every delegation cell |
| **Highest-risk UK** | UK-4 | `eu-ai-act.md` Art. 113 still teaches the pre-omnibus high-risk date |
| **Highest-risk UU** | UU-1 | Fleet-as-unit becoming the legal object |

### What this PR already moved

| Move | From → to |
|---|---|
| Six-family primitive overlay exists and is honesty-checked | KU (no walk) → **KK-4** |
| CMMC / ACS / JTC 21 / 42006 / MCP auth / EN 304 223 / 8605 first files | silent → **KK-6** (still KU at clause/practice grain) |
| Recital 40 named on the mapped walk | unknown-to-the-126-row-file → **KK-5** + **UK-4** (file not edited) |
| DCT-is-not-IETF written down | tacit → **KK-8** + **UK-1** (alias remains) |

---

## Evidence grades (do not fake A on synthesis)

From the rumsfeld-crosswalk README:

| Grade | Meaning |
|---|---|
| **A** | Direct measurement / primary text / in-tree file header |
| **B** | Identified gap with a measurement path |
| **C** | Expert elicitation / surfacing / **this map’s synthesis** |
| **D** | Horizon scanning only |

This document’s quadrant assignment, “highest-leverage” picks, and UU shapes are **grade C synthesis** (map) or **D** (UU). They are not A-grade facts. Primary citations (EN PDF, MCP 2026-07-28 page, COSAiS outline, in-tree matrices) stay A/B on the **claims those files make**, not on this arrangement.

---

## Recommended actions (index only)

| Priority | Item | Quadrant | Action this PR | Later |
|---|---|---|---|---|
| 1 | Keep mapped walk + seven files as the workpapers | KK | Done | Re-review six column files (KU-1) |
| 2 | Name UK-1…UK-4 | UK | This file | Keep or discard |
| 3 | Do not invent 42004 / CMMC 3.1.1 / COSAiS AC-2 / JTC clauses | KU | Done | Copy IDs when public text is in-tree |
| 4 | Leave FLEET Q4 and RFC 8693 open | KU-5, KU-6 | Named | Decide Q4; follow-on `ietf.md` |
| 5 | Watch fleet-as-unit regulation and COSAiS IPD | UU-1, UU-3 | Watch | New rows, not back-ported IDs |
| 6 | Art. 113 date | UK-4 | Named, file not edited | Edit `eu-ai-act.md` only as a deliberate review |

---

*Rumsfeld map produced 2026-08-31 from this PR’s mapped walk, seven first-touch coverage files, `DELEGATION-IETF-GAP-ANALYSIS.md`, and FLEET open questions. Revisit when a KU item gains a verified ID list (KU→KK) or when an operator keep-or-discard lands on UK-1…UK-4.*
