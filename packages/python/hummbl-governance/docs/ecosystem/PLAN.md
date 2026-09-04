# HUMMBL Ecosystem — Master Plan
**Version**: 0.1.0  
**Date**: 2026-05-04  
**Author**: HUMMBL operator / claude-code
**Status**: ACTIVE — drives Q2 2026 roadmap

---

## 1. Situation

The HUMMBL, LLC maintains 35 repositories under the `hummbl-*` namespace on Gitea.
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

## 5.3 krineia — Krineia governance receipt chain (SPEC — May 15 gate)

**Gap analysis**:
- `RECEIPT_SCHEMA.md` is v0.1 DRAFT — near-complete, covers all event types
- Reference daemon at `<local-path>` — not yet committed
- `tools/verify_chain.py` — planned but not written
- `INVARIANTS.md` — planned but not written
