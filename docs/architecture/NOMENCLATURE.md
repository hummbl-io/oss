# HUMMBL OSS Canonical Nomenclature & Versioned Counts

**Status:** Canonical reference for `hummbl-io/oss`
**Last verified:** 2026-11-23
**Tracking issue:** `hummbl-io/oss#518`

This document defines authoritative expansions, scope boundaries, and versioned
counts for terms that have drifted across public surfaces. It governs `hummbl-io/oss`
documentation; external or personal web surfaces must be coordinated with their
owning repositories rather than modified from this repo.

---

## 1. DCT — Delegation Capability Token

| Term | Canonical Expansion | Scope & Authoritative Source |
|---|---|---|
| **DCT** | **Delegation Capability Token** | HMAC-SHA256 signed, time-bounded, scope-limited authorization token in IDP v0.1. Authoritative sources: [`packages/python/idp-spec/idp_spec/delegation_token.py`](../../packages/python/idp-spec/idp_spec/delegation_token.py), [`packages/python/idp-spec/README.md`](../../packages/python/idp-spec/README.md), [`packages/python/hummbl-contracts/schemas/idp/idp.schema.json`](../../packages/python/hummbl-contracts/schemas/idp/idp.schema.json), and [`packages/python/hummbl-tuples/governance/lexicon/acronyms.v0.2.json`](../../packages/python/hummbl-tuples/governance/lexicon/acronyms.v0.2.json) (migrated `2026-03-03`). |
| **DCTX** | **Delegation Context** | Immutable delegation context tuple (`intent_id`, `task_id`, `delegator_id`, `delegatee_id`, `contract_id`). Distinct from `DCT`. |

**Disambiguation rules:**
- Do **not** expand `DCT` as *"Delegation Context Token"*. That phrasing conflates `DCTX` (Delegation Context) with `DCT` (Delegation Capability Token).
- **Not IETF / distinct from prior art:** As documented in [`packages/python/hummbl-governance/docs/coverage/ietf.md`](../../packages/python/hummbl-governance/docs/coverage/ietf.md) and [`docs/research/DELEGATION-IETF-GAP-ANALYSIS.md`](../research/DELEGATION-IETF-GAP-ANALYSIS.md), HUMMBL's HMAC-SHA256 `DCT` is an internal library/IDP primitive, distinct from Google DeepMind's Delegation Capability Tokens paper (Tomasev et al., arXiv `2602.11865`, `2026-02-12`) and not an IETF Internet-Draft.

---

## 2. CRAB — Scoped Conventions (Do Not Silently Merge)

Two expansions of `CRAB` exist across HUMMBL operational and public methods surfaces:

| Convention | Expansion | Scope | Status |
|---|---|---|---|
| **CRAB (turn-execution protocol)** | **Check (CRAWL) → Reason → Act → Bus** | Mandatory multi-agent turn-execution protocol defined in HUMMBL fleet governance rules (`~/.agents/rules/crab-protocol.md`) and referenced in OSS ecosystem tables. | Active fleet protocol |
| **CRAB (public methods lifecycle)** | **Commit / Receipt / Audit / Broadcast** | Appears on external public methods surfaces as an evidence/broadcast lifecycle convention. | Distinct convention — **do not merge with turn-execution CRAB without an explicit owner decision** |

**Usage rules in `hummbl-io/oss`:**
- Always qualify `CRAB` with its scope on first use (for example: `CRAB turn-execution protocol (Check, Reason, Act, Bus)`).
- Do not silently overwrite or conflate the two conventions.
- **Registry collision note:** The unscoped package name `crab` on PyPI and npm belongs to unrelated third-party authors (see [`docs/architecture/PACKAGES.md`](PACKAGES.md)).

---

## 3. `hummbl-governance` Primitive Count (Versioned & Scoped)

**Canonical sources of truth:**
- Runtime inventory: `hummbl_governance.primitive_registry.PrimitiveRegistry().implemented_primitives()`
- Reference document: [`packages/python/hummbl-governance/PRIMITIVES.md`](../../packages/python/hummbl-governance/PRIMITIVES.md)
- Public claim ledger & provenance: [`packages/python/hummbl-governance/docs/public-claims.md`](../../packages/python/hummbl-governance/docs/public-claims.md)

| Count | Version / Date Scope | Status | Notes |
|---|---|---|---|
| **51 implemented governance primitives** | `v1.5.1` (tree & PyPI live, verified `2026-09-11` and re-verified `2026-11-23`) | **Current** | 58 tracked total in `PrimitiveRegistry`: 51 implemented (`P1–P26`, `P27–P31`, `P34–P35`, `P36–P38`, `P44–P58`), 4 proposed/not-started (`P32–P33`, `P39–P40`), 3 candidate. |
| **34** | Historical `v1.2.2`–`v1.4.2` era (superseded `2026-09-11`) | **Historical only** | Former count (`26` core + `8` expansion; omitted `P35`, `P37`, and post-v1.2 `P44–P58`). Do not use as a current count. |
| **26** | Core baseline (`P1–P26`) | **Core / historical scope only** | Valid only when explicitly scoped to the original `P1–P26` core set. |

**Consumer rule:**
- Cross-package READMEs and ecosystem tables must link to [`PRIMITIVES.md`](../../packages/python/hummbl-governance/PRIMITIVES.md) and [`public-claims.md`](../../packages/python/hummbl-governance/docs/public-claims.md) rather than hard-coding unscoped totals.
- Automated enforcement runs in CI via [`packages/python/hummbl-governance/scripts/check_public_count_claims.py`](../../packages/python/hummbl-governance/scripts/check_public_count_claims.py).

---

## 4. External / Personal-Site Coordination

This file and its companion PR only govern `hummbl-io/oss`. Aligning external
personal methods/systems pages (such as replacing *"Delegation Context Token"*
or clarifying the external `CRAB` expansion) must be coordinated separately in
the owning web repository.
