# Memory System Registry

**Status:** PROPOSED - candidate namespace registry, not canonical yet
**Owner:** HUMMBL Research Institute
**Decision authority:** Reuben Bowlby
**Authoritative candidate:** `memory_system_registry.candidate.json`
**Candidate schema:** `memory_system_registry.schema.json`
**Validator:** `python scripts/validate_memory_system_registry.py`

---

## 1. Purpose

HUMMBL now has multiple memory-related doctrines, registries, runtime modules, skills,
and state stores. The word "memory" is no longer specific enough to safely guide repo
creation or operational authority.

This registry prevents namespace drift before dedicated Memory City / Memory
Civilization repositories are created.

The immediate rule is:

> Do not promote a `memory-*` concept into a repository until it has a declared owner,
> authority boundary, state boundary, receipt path, and migration relationship to the
> existing hummbl-governance and hummbl-governance surfaces.

---

## 2. Category Grammar

| Category | Meaning | Repo promotion implication |
| --- | --- | --- |
| `doctrine` | Conceptual or canonical design documents | Not a repo by itself |
| `registry` | Governed index of surfaces, authorities, ledgers, buses, maps, tunnels, or books | Candidate control surface |
| `runtime_surface` | Executable or operational component | Must declare state and safety boundaries |
| `state_store` | Durable memory/state location | Must declare owner, retention, and mutation rules |
| `repo_candidate` | Boundary that may deserve its own repo later | Blocked until promotion gate passes |
| `repo` | Existing top-level repository/workspace | Must have repo-standard artifacts |
| `archive` | Historical or backup memory material | Read-only unless explicitly reactivated |

---

## 3. Current State

Existence checks observed on 2026-06-25. The JSON candidate is authoritative;
this Markdown is the human-readable companion and must stay in sync with the
validator.

| Check | Result |
| --- | --- |
| `~/projects/PROJECTS/memory-city` | absent |
| `~/projects/PROJECTS/memory-civilization` | absent |
| `gh repo list hummbl-dev` for `memory|civilization|city` | no matching repos returned |
| `gh repo list foundermode-ai` for `memory|civilization|city` | no matching repos returned |

Exact evidence commands and results are recorded in
`memory_system_registry.candidate.json`.

| ID | Category | Status | Current home | Authority note |
| --- | --- | --- | --- | --- |
| `memory_city_doctrine` | `doctrine` | active doctrine corpus | `hummbl-governance/docs/architecture/memory-city/` | hummbl-governance doctrine, not a standalone repo |
| `canonical_surfaces_registry` | `registry` | active hummbl-governance registry | `hummbl-governance/docs/architecture/memory-city/doctrine/canonical-surfaces.md` | declares governed surfaces and write authority |
| `book_ledger` | `registry` | proposed hummbl-governance registry | `hummbl-governance/docs/operations/book_ledger.yaml` + `BOOK_LEDGER.md` | classifies runbooks/playbooks/books; not a repo boundary |
| `memory_civilization_registries` | `registry` | proposed hummbl-governance doctrine | `hummbl-governance/docs/MEMORY_CIVILIZATION_REGISTRIES.md` | defines bus, ground, underground, and tunnel registries |
| `memory_system_registry` | `registry` | proposed | this document + `memory_system_registry.candidate.json` | classifies memory surfaces before repo creation |
| `memory_kernel` | `doctrine` | hummbl-governance reference | `hummbl-governance/docs/reference/MEMORY_KERNEL.md` | conceptual memory kernel reference |
| `memory_reconciliation_policy` | `doctrine` | hummbl-governance policy | `hummbl-governance/docs/operations/MEMORY_RECONCILIATION_POLICY.md` | policy for reconciliation, not a runtime |
| `data_memory_corpus_inventory` | `registry` | hummbl-governance inventory | `hummbl-governance/docs/governance/data-memory-corpus-inventory.md` | corpus inventory surface |
| `memory_graph_rag_docs` | `doctrine` | hummbl-governance research | `hummbl-governance/docs/research/2026-06-07_memory-graph-rag-*.md` | research/spec material |
| `working_memory_modules` | `runtime_surface` | hummbl-governance code | `hummbl-governance/hummbl_governance/cognition/working_memory.py` + `mcp_working_memory.py` | executable memory components |
| `memory_manifest_script` | `runtime_surface` | hummbl-governance script | `hummbl-governance/hummbl_governance/scripts/memory_manifest.py` | inventory/manifest helper |
| `memory_house_service` | `runtime_surface` | hummbl-governance service | `hummbl-governance/hummbl_governance/services/memory_house/` | runtime surface; state boundary must remain explicit |
| `memory_house_state` | `state_store` | local state | `_state/memory_house/` | operational state, not source doctrine |
| `agent_memory_registry` | `state_store` | local agent state | `.agents/MEMORY.md` and related memory skill state | local agent memory, not canonical product doctrine |
| `knowledge_agent_memory` | `state_store` | local agent state | `.knowledge/agents/*/memory.jsonl` | per-agent memory log state |
| `memory_skills` | `runtime_surface` | local skills | `.agents/skills/memory-*` and related skill copies | agent capability surfaces, not Memory City repos |
| `archived_memory_material` | `archive` | archive/backups | `Archive/`, `_internal-local-mirror/`, `.claude/*.bak*`, `.agy/*.bak*` | read-only historical material unless promoted by review |

---

## 4. Repo Candidates

These names are reserved as candidates only. They are not authorized repos by this
document.

| Candidate repo | Proposed scope | Promotion status |
| --- | --- | --- |
| `memory-city` | World/city primitives: districts, roads, surfaces, blocks, ownership, maps, and visual grammar | blocked until primitives and migration plan are stable |
| `memory-civilization` | Multi-city federation: treaties, inter-city registries, cross-domain governance, civilization-level authority | blocked until Memory City contracts exist |
| `memory-ground` | Visible/ground state strata and placement model | do not split until authority boundaries are proven |
| `memory-bus` | Bus/district route model and transport registry | do not split until bus registry is canonical |
| `memory-tunnels` | Subsurface topology, tunnel gates, permits, inspection, rollback | do not split until tunnel registry is canonical |
| `memory-ledger` | Cross-system receipts and evidence ledger model | do not split until it has a stable schema and retention policy |

---

## 5. Promotion Gate

A memory surface may become a repo only when all of the following are true:

| Gate | Requirement |
| --- | --- |
| Owner | Named steward and approving human |
| Write authority | Explicit who/what can mutate source, state, and receipts |
| State authority | Declared state stores, retention, and deletion policy |
| Receipt path | Append-only evidence path or explicit reason receipts are not required |
| Source migration | Migration plan from existing hummbl-governance / hummbl-governance docs |
| Relationship map | Explicit relation to hummbl-governance, hummbl-governance, and simulation/world layers |
| Repo standard | `CONSTITUTION.md`, `KRINEIA.md`, `hummbl.repo.yaml`, `AGENTS.md`, `SECURITY.md`, and CODEOWNERS ready |
| Safety model | Failure modes and prohibited mutations declared |

---

## 6. Recommended Order

1. Keep Memory City as doctrine while this registry is reviewed.
2. Canonicalize Memory Civilization registries only after review of `BUS_REGISTRY`,
   `GROUND_REGISTRY`, `UNDERGROUND_MAP`, and `TUNNEL_REGISTRY`.
3. Create `memory-city` only after world/city primitives have stable contracts.
4. Create `memory-civilization` only after multi-city governance needs a separate
   authority boundary.
5. Keep `memory-ground`, `memory-bus`, `memory-tunnels`, and `memory-ledger` as
   reserved names until their surfaces are proven by repeated use.

---

## 7. Open Questions

| Question | Current disposition |
| --- | --- |
| Should Memory City doctrine move out of hummbl-governance? | Not yet. First declare migration paths and source-of-record rules. |
| Should Memory Civilization live in hummbl-governance? | Yes as proposed governance doctrine until it becomes a repo boundary. |
| Should local agent memory be treated as Memory City state? | No. It is a local state store unless explicitly admitted into the registry. |
| Should backups and archive memory be indexed? | Yes as archive entries, not active authority surfaces. |

---

## 8. Non-Goals

This proposal does not:

- create any new repository;
- promote any memory surface to canonical status;
- move hummbl-governance doctrine;
- change runtime memory behavior;
- alter bus, tunnel, or state-store write authority.

---

## 9. Validation

Before promotion or review, run:

```bash
python -m json.tool docs/memory_system_registry.candidate.json
python scripts/validate_memory_system_registry.py
python -m pytest tests/test_memory_system_registry.py -q
```
