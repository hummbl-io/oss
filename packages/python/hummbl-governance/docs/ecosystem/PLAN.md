# HUMMBL Ecosystem — Master Plan
**Version**: 0.1.0  
**Date**: 2026-05-04  
**Author**: HUMMBL operator / claude-code
**Status**: ACTIVE — drives Q2 2026 roadmap

---

## 1. Situation

The HUMMBL Research Institute maintains 35 repositories under the `hummbl-*` namespace on Gitea.
Six of those repos contain production-quality source code that is currently either unexported,
under-tested, or not yet published to PyPI. The remainder are research documents, scaffolds, or
experimental notebooks. This plan covers the next two quarters of ecosystem work.

### 1.1 Inventory by tier

| Tier | Repos | Status |
|------|-------|--------|
| **SHIPPED** | hummbl-governance 1.2.2 | PyPI live, 2027 tests |
| **READY TO EXTRACT** | hummbl-crucible, hummbl-bus | Source extracted, tests empty |
| **SPEC COMPLETE** | krineia (Krineia receipt chain), hummbl-contracts, hummbl-tuples | Schemas done, impl missing |
| **SCAFFOLD** | hummbl-caes, hummbl-compliance, hummbl-mtsmu, hummbl-gaas, hummbl-rsi | README only |
| **RESEARCH** | hummbl-clp, hummbl-bki, hummbl-huaomp, hummbl-legal, hummbl-agi, ... | Docs/notebooks |

### 1.2 Why act now

- `hummbl-governance` is on PyPI and generating adoption signals.
- `hummbl-crucible` trust-scorer and router are the #1 requested extension by downstream consumers (legal AI, agentic SaaS).
- `hummbl-bus` bridge-server enables cross-machine coordination and is blocking the Chief-of-Staff agent.
- `krineia` (Krineia governance receipt chain) schema has a **May 15 LOI gate** (v1.0 frozen).
- `hummbl-legal` governance receipt integration is blocked on `SchemaValidator` already in `hummbl-governance` — the plumbing gap is documentation.
- `hummbl-compliance` crosswalks are needed for the first governance audit deliverable (June 2026).

---

## 2. North Star

**By end of Q2 2026**, every HUMMBL governance primitive is independently installable from PyPI,
independently testable, and covered by a public spec frozen under a SemVer tag. The CAES
framework (Coordination, Autonomy, Evidence, Safety) is the architectural umbrella, each repo
maps to exactly one CAES pillar.

---

## 3. Architecture overview

```
CAES Framework (hummbl-caes — specification layer)
│
├── C — Coordination
│   ├── hummbl-bus          (TSV coordination bus, signing, bridge, MCP)
│   ├── hummbl-clp          (Cognitive Ledger Protocol, shared memory)
│   └── hummbl-contracts    (versioned JSON schemas, stdlib validator)
│
├── A — Autonomy
│   ├── hummbl-crucible     (trust scoring, tier routing, identity registry)
│   └── hummbl-governance   (kill switch, circuit breaker, delegation token, ...)
│
├── E — Evidence
│   ├── krineia        (Krineia governance receipt chain, append-only JSONL)
│   ├── hummbl-mtsmu        (evidence methodology, debugging protocol)
│   └── hummbl-tuples       (typed governance tuples, BaseN reasoning artifacts)
│
└── S — Safety
    ├── hummbl-governance   (capability fence, output validator, stride mapper)
    ├── hummbl-compliance   (NIST/ISO/EU framework crosswalks)
    └── hummbl-rsi          (recursive self-improvement detection & control)

Vertical applications (use the above):
    hummbl-legal            (legal AI governance pilot)
    hummbl-gaas             (Governance-as-a-Service API)
```

### 3.1 Dependency graph

```
hummbl-contracts (no deps)
       ↓
krineia (no deps — plain JSONL + hashlib)  ← Krineia receipt chain impl
       ↓
hummbl-governance (no deps — 1.2.2, PyPI)
       ↓
hummbl-bus (optional dep: hummbl-governance for identity registry)
       ↓
hummbl-crucible (deps: hummbl-bus for TSV parsing)
       ↓
hummbl-clp (optional deps: hummbl-bus, hummbl-crucible)
       ↓
hummbl-compliance (depends on hummbl-governance, hummbl-contracts)
       ↓
hummbl-gaas (depends on most of the above)
```

---

## 4. Release plan

### 4.1 Q2 2026 milestones

| Date | Milestone | Deliverable | Status |
|------|-----------|-------------|--------|
| 2026-05-15 | krineia v1.0 | Frozen Krineia governance receipt schema (LOI gate) | ❌ MISSED — schema still FREEZE PENDING as of 2026-05-31 |
| 2026-05-31 | hummbl-crucible v0.2.0 | Tests written, PyPI published | ⏳ Status unknown — verify against Gitea repo |
| 2026-05-31 | hummbl-bus v0.2.0 | Tests written, PyPI published | ⏳ Status unknown — verify against Gitea repo |
| 2026-06-15 | hummbl-compliance v0.1.0 | NIST AI RMF + ISO 42001 crosswalks live | 📋 Upcoming |
| 2026-06-30 | hummbl-caes v0.1.0 | Framework specification frozen | 📋 Upcoming |
| 2026-06-30 | hummbl-legal v0.5.0 | Provider evidence gate; SchemaValidator wired | 📋 Upcoming |

### 4.2 Q3 2026 milestones (planned)

| Date | Milestone | Deliverable |
|------|-----------|-------------|
| 2026-07-31 | hummbl-clp v0.2.0 | Decoupled from hummbl-governance, standalone tests |
| 2026-08-31 | hummbl-tuples v0.1.0 | Typed tuple taxonomy frozen, reference impl |
| 2026-09-30 | hummbl-gaas v0.1.0 | REST API wrapping hummbl-governance primitives |

---

## 5. Per-repo execution plans

### 5.1 hummbl-crucible (READY — Q2 priority)

**Goal**: Publish hummbl-crucible 0.2.0 to PyPI with full test coverage.

**Gap analysis**:
- `src/` has 3 modules (identity.py, trust_scorer.py, trust_router.py) — production quality
- `tests/` is empty (`.gitkeep`)
- `pyproject.toml` wires `hummbl_crucible = "src"` — valid
- No CLI entry points defined

**Work items**:
1. Write `tests/test_identity.py` — canonicalize(), is_valid_sender(), is_deprecated()
2. Write `tests/test_trust_scorer.py` — BusMessage parsing, AgentStats accumulation, factor computation
3. Write `tests/test_trust_router.py` — tier mapping, scope compliance, signal recording, persistence
4. Add `__main__.py` to `src/` with CLI entry points (`hummbl-crucible`, `hummbl-trust-scorer`)
5. Bump version to 0.2.0
6. Publish to PyPI

**ADR**: See `docs/adr/ADR-001-public-api-surface.md` in hummbl-crucible.

### 5.2 hummbl-bus (READY — Q2 priority)

**Goal**: Publish hummbl-bus 0.2.0 to PyPI with full test coverage.

**Gap analysis**:
- `src/` has 13 modules — production quality (extracted from hummbl-governance)
- `tests/` is empty
- Bridge server/client and MCP server are novel additions beyond hummbl-governance
- CLI entry points defined in pyproject.toml

**Work items**:
1. Write `tests/test_bus_writer.py` — field escaping, TSV validation, HMAC signing
2. Write `tests/test_secure_tsv.py` — encode/decode, injection prevention
3. Write `tests/test_bus_verifier.py` — audit report generation, anomaly detection
4. Write `tests/test_bus_security.py` — nonce tracking, replay prevention
5. Write `tests/test_bridge_client.py` — HTTP client mocking
6. Bump version to 0.2.0
7. Publish to PyPI

**ADR**: See `docs/adr/ADR-001-extraction-and-bridge-protocol.md` in hummbl-bus.

### 5.3 krineia — Krineia governance receipt chain (SPEC — May 15 gate)

**Goal**: Freeze v1.0 Krineia governance receipt schema; ship `tools/verify_chain.py`.

**Naming note**: The repo is `krineia` (renamed from `hummbl-verum` 2026-05-04). The public
product language is **Krineia governance receipt chain** / **governance receipt**. "VERUM" is
retired as a public brand name per the namespace audit. Internal daemon filenames
(`verum_daemon.py`) are migration debt to be renamed in a later PR — do not rename this sprint.

**Gap analysis**:
- `RECEIPT_SCHEMA.md` is v0.1 DRAFT — near-complete, covers all event types
- Reference daemon at `C:/Users/Owner/overnight/verum_daemon.py` — not yet committed
- `tools/verify_chain.py` — planned but not written
- `INVARIANTS.md` — planned but not written

**Work items**:
1. Write `tools/verify_chain.py` — standalone SHA-256 chain validator (stdlib-only)
2. Write `INVARIANTS.md` — the four governing invariants (formal language)
3. Commit daemon code to `daemon/verum_daemon.py` and `daemon/orchestrator.py`
   (filenames unchanged for now — migration debt, rename in a future PR)
4. Bump RECEIPT_SCHEMA.md status from DRAFT to v1.0; update its header to say
   "Krineia Governance Receipt Chain" not "VERUM"
5. Tag `v1.0.0` by May 15

**ADR**: See `docs/adr/ADR-001-receipt-chain-standard.md` in krineia.

### 5.4 hummbl-compliance (SCAFFOLD — Q2)

**Goal**: Ship NIST AI RMF and ISO 42001 crosswalks as structured JSON; wire gap_analyzer.py.

**Gap analysis**:
- `src/` is empty
- `schemas/` is empty
- Mapping logic exists in Claude Code skills (`/nist-map`, `/iso-crosswalk`)
- hummbl-governance compliance_mapper.py already maps traces to NIST AI RMF — reuse this

**Work items**:
1. Extract NIST AI RMF crosswalk from governance skills → `schemas/crosswalks/nist-ai-rmf.json`
2. Extract ISO 42001 crosswalk → `schemas/crosswalks/iso-42001.json`
3. Extract SOC 2 Type II crosswalk → `schemas/crosswalks/soc2-type-ii.json`
4. Write `src/crosswalk_engine.py` — loads crosswalk JSON, returns matching controls
5. Write `src/gap_analyzer.py` — compares active controls to framework requirements
6. Write `src/report_generator.py` — produces markdown + JSON gap report
7. Write tests for all three modules
8. Publish v0.1.0

**ADR**: See `docs/adr/ADR-001-crosswalk-data-model.md` in hummbl-compliance (to be written).

### 5.5 hummbl-caes (SCAFFOLD — Q2)

**Goal**: Freeze CAES framework specification v0.1.0; no implementation required this quarter.

**Gap analysis**:
- README has the four pillars — solid conceptual foundation
- `docs/` is empty

**Work items**:
1. Write `docs/framework.md` — CAES four-pillar specification with invariants
2. Write `docs/coordination.md` — Bus protocol, CLP contract, message type taxonomy
3. Write `docs/autonomy.md` — Trust tier table, delegation depth policy, tempo modes
4. Write `docs/evidence.md` — MTSMU evidence tags, receipt protocol, audit log format
5. Write `docs/safety.md` — Kill switch modes, circuit breaker wiring, guardrail layers
6. Write `docs/mapping.md` — Maps each CAES control to its canonical hummbl-* module
7. Tag `v0.1.0-spec`

### 5.6 hummbl-legal (ACTIVE PILOT — Q2)

**Goal**: Close 4 of 10 ML-BLOCK items; wire hummbl-governance SchemaValidator.

**Current state**:
- 10 open blockers, decision: BLOCK
- High-priority scenarios (A1, B2, C1, C2, D1, D2) not yet run/scored
- Governance receipts use hand-rolled PowerShell validator instead of `SchemaValidator`

**Work items**:
1. Replace `test-matter-ai-use-receipt.ps1` with Python validation using `hummbl_governance.SchemaValidator`
2. Run synthetic scenarios A1, B2, C1 (these don't require Mike deployment)
3. Close ML-BLOCK-001 (content log removal) and ML-BLOCK-003 (API key storage) with specific test evidence
4. Wire provider evidence gate (Anthropic API ZDR/retention/DPA check)
5. Advance decision from BLOCK → SYNTHETIC_ONLY

**Tech spec**: See `docs/ecosystem/TECH-SPEC-legal-governance-integration.md` in hummbl-governance.

---

## 6. Cross-cutting concerns

### 6.1 Naming and identity

- All repos use `CANONICAL_AGENTS` from `hummbl-crucible` as the identity registry
- `hummbl-bus` imports `canonicalize()` from `hummbl-crucible` (v0.2.0+)
- `hummbl-governance` `identity.py` is a superset; it will be refactored to delegate to hummbl-crucible in v0.9.0

### 6.2 Schema validator

- `hummbl-contracts` `schema_validator.py` and `hummbl-governance` `schema_validator.py` are near-identical
- Canonical copy is in `hummbl-contracts`; all other repos should import it
- Migration plan: v0.9.0 hummbl-governance depends on hummbl-contracts for schema validation

### 6.3 Receipts

- Coordination bus uses HMAC-signed TSV receipts (hummbl-bus)
- Governance audit log uses JSONL receipts (hummbl-governance AuditLog)
- Agent governance actions use SHA-256 chain receipts (krineia — Krineia receipt chain)
- Legal AI uses matter-scoped receipts (hummbl-legal)
- All four formats are DIFFERENT and intentional — they serve different audit contexts
- `hummbl-tuples` EVIDENCE class is the abstract type unifying all of them

### 6.4 Stdlib-only constraint

All runtime code across all repos is stdlib-only. This is a hard constraint. Test dependencies
(pytest, pytest-cov) are in `[test]` extras only. No exceptions without an ADR.

### 6.5 Versioning policy

- `0.x.y` — pre-stable, breaking changes allowed between minors
- `1.0.0` — API frozen; breaking changes require major bump + ADR
- Only krineia (Krineia receipt chain) has a hard external deadline (May 15 v1.0)
- All others target 0.x until governance audit deliverable (June 2026)

---

## 7. Definition of done (per repo)

A repo is considered **shipped** when:
- [ ] `pyproject.toml` has a version ≥ 0.2.0
- [ ] Test suite exists with ≥ 50 tests
- [ ] CI passes (ruff, pytest)
- [ ] README reflects current state (not scaffold language)
- [ ] Published to PyPI OR tagged with explicit "internal-only" rationale
- [ ] At least one ADR documents key architectural decisions

---

## 8. Owner assignments

| Repo | Owner | Next action |
|------|-------|-------------|
| hummbl-governance | operator / claude-code | v0.9.0 ecosystem adapters |
| hummbl-crucible | operator / claude-code | Write tests (est: 1 session) |
| hummbl-bus | operator / claude-code | Write tests (est: 2 sessions) |
| krineia (Krineia receipt chain) | operator | Commit daemon code, write verify_chain.py |
| hummbl-compliance | operator / claude-code | Extract crosswalk JSONs (est: 1 session) |
| hummbl-caes | operator | Write framework docs (est: 1 session) |
| hummbl-legal | operator | Close ML-BLOCK-001, ML-BLOCK-003; wire SchemaValidator |
| hummbl-clp | operator / claude-code | Decouple from hummbl-governance (Q3) |
| hummbl-tuples | operator | Run BASEN_AI_VS_HITL experiment (Q3) |
| hummbl-gaas | operator | Design REST API (Q3) |

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Krineia receipt chain v1.0 deadline slips (May 15) | Low | High | verify_chain.py is ~100 LOC; commit daemon first |
| hummbl-bus bridge unstable on Windows | Medium | Medium | Test suite covers platform-specific fcntl/msvcrt paths |
| hummbl-crucible import path breaks after extract | Low | Low | pyproject.toml `package-dir` already correct |
| Schema validator duplication causes drift | Medium | Medium | Tracked — consolidate in v0.9.0 hummbl-governance |
| hummbl-legal pilot generates real client data | Low | Critical | CI FORBIDDEN marker scan prevents any real data commit |

---

## 10. Appendix: repo status matrix

| Repo | Has src? | Has tests? | PyPI? | ADR? | PRD? |
|------|----------|------------|-------|------|------|
| hummbl-governance | ✅ | ✅ 2027 | ✅ 1.2.2 | — | — |
| hummbl-crucible | ✅ | ❌ | ❌ | ❌ | 📋 this plan |
| hummbl-bus | ✅ | ❌ | ❌ | ❌ | 📋 this plan |
| krineia (Krineia receipt chain) | spec only | — | ❌ | ❌ | 📋 this plan |
| hummbl-contracts | ✅ | ❌ | ❌ | — | — |
| hummbl-tuples | ✅ partial | ❌ | ❌ | ✅ 2 ADRs | — |
| hummbl-clp | ✅ | ❌ | ❌ | — | — |
| hummbl-compliance | ❌ | ❌ | ❌ | ❌ | 📋 this plan |
| hummbl-caes | ❌ | — | ❌ | ❌ | 📋 this plan |
| hummbl-mtsmu | ❌ | — | ❌ | — | — |
| hummbl-legal | N/A | — | N/A | — | — |
| hummbl-gaas | ❌ | — | ❌ | — | — |
| hummbl-rsi | ❌ | — | ❌ | — | — |
