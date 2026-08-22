# The Full Menu

**Origin:** "Full Menu" notates the comprehensive spread — not minimal, not
a la carte, but the complete offering. This document applies that principle
to HUMMBL's open-source publishing: not the minimum viable package, but the
complete spread of everything the world deserves to install.

**Status:** Active
**Date:** 2026-08-22
**Authors:** Reuben Bowlby, HUMMBL fleet

---

## What is the Full Menu?

The Full Menu is the comprehensive public OSS offering from `hummbl-io/oss`.
Every HUMMBL package that can be `pip install`ed, `npm install`ed,
`cargo add`ed, or `go get`ted by anyone in the world lives here or links
here. The oss monorepo is the restaurant; the packages are the menu.

The menu has three sections:

| Section | Meaning | Decision gate |
|---------|---------|---------------|
| **CAN** | Technically publishable — has a manifest, tests, no blocking technical issues | Mechanical: does it build, test, and install? |
| **SHOULD** | Strategically aligned — stable enough, public-facing, adds value to the ecosystem, not private/internal | Judgment: does the world benefit from this being public? |
| **SHOULD NOT (yet)** | Not ready for public release — private data, internal infrastructure, needs review, or not stable enough | Temporary: can graduate to SHOULD when the blocker is resolved |

CAN is about capability. SHOULD is about judgment. A package can be CAN
without being SHOULD (technically publishable but strategically premature),
and SHOULD without being CAN (strategically ready but technically blocked).
The Full Menu lists only packages that are **both CAN and SHOULD**.

---

## The Full Menu — PyPI (Python)

### Already served (7 live)

| Package | Version | What it is | Install |
|---------|---------|-----------|---------|
| `hummbl-governance` | 1.4.1 | Governance primitives — kill switch, circuit breaker, cost governor, delegation tokens, audit log, identity registry, schema validation | `pip install hummbl-governance` |
| `hummbl-bus` | 0.1.0 | Secure append-only TSV coordination bus for multi-agent systems | `pip install hummbl-bus` |
| `hummbl-cognition` | 0.1.0 | Cognitive Ledger Protocol and Open Brain server | `pip install hummbl-cognition` |
| `hummbl-tuples` | 0.2.0 | HUMMBL Typed Tuples governance model (polyglot: also Go, Rust, TS) | `pip install hummbl-tuples` |
| `hummbl-bif` | 1.0.1 | Batch Ingestion Framework | `pip install hummbl-bif` |
| `base120` | 3.0.0 | 120 reasoning operators for structured thinking — stdlib-only, tuple-native | `pip install base120` |
| `governed-compression` | 0.1.0 | Governed vector + KV-cache compression (ML) — CPU reference for quantization methods | `pip install governed-compression` |

### Next to be served (2 ready for first release)

| Package | Version | What it is | Install | Status |
|---------|---------|-----------|---------|--------|
| `hummbl` | 0.1.0 | Structured reasoning framework for AI agents — plans, hypotheses, observations, evaluations, decisions, reflections as durable artifacts | `pip install hummbl` | **Release-ready after metadata fix** |
| `hummbl-kernel` | 0.1.0 | HUMMBL orchestration kernel — workflow execution, capability admission, fleet health, audit trail | `pip install hummbl-kernel` | **Release-ready after license + CHANGELOG fix** |

These two are the focus of the current release cycle. `hummbl` is the
reasoning library (the "thinking" layer). `hummbl-kernel` is the runtime
kernel (the "doing" layer). Together they form the core of the HUMMBL
stack: **reason about it, then execute it.**

### On deck (CAN + SHOULD, pending release prep)

These are technically publishable and strategically aligned. They enter the
Full Menu as each is prepared, audited, and tagged.

| Package | Repo | What it is | Priority | Blocker |
|---------|------|-----------|----------|---------|
| `hummbl-clp` | hummbl-clp (private) | Cognitive Ledger Protocol — persistent memory for agents | HIGH | Needs migration into oss, metadata audit |
| `hummbl-axis` | hummbl-axis (private) | The ladder that selects which Atlas contradiction to act on | MED | Needs migration, metadata audit |
| `hummbl-validation` | hummbl-validation (private) | Shared validation primitives | MED | Needs migration, metadata audit |
| `hummbl-lint-config` | hummbl-lint-config (private) | Shared ruff lint configuration | LOW | Needs migration, metadata audit |
| `hummbl-eval` | hummbl-eval (private) | Model evaluation suites and benchmark runners | MED | Needs migration, metadata audit |
| `hummbl-dashboard` | hummbl-dashboard (private) | Fleet health, agent metrics, observability | MED | Needs migration, metadata audit |
| `hummbl-contracts` | hummbl-contracts (private) | Governance contracts | MED | Needs migration, metadata audit |
| `hummbl-lattice` | hummbl-lattice (private) | Domain-specific reasoning operator lattices | LOW | Needs migration, metadata audit |
| `peptide-check` | peptide-check (private) | Peptide safety claims validation | LOW | Needs migration, metadata audit |
| `demosmesh` | demosmesh (private) | Mesh networking platform (Rust no_std + Python via PyO3) | LOW | Rust crate, different registry |
| `tributary` | tributary (private) | Real-time observability platform with typed stream-query language | LOW | Already on PyPI v0.2.1; needs link remediation |

### CAN but not SHOULD (yet)

Technically publishable but strategically premature — needs review,
stability validation, or doctrinal alignment before joining the Full Menu.

| Package | Repo | Why CAN | Why not SHOULD (yet) |
|---------|------|---------|---------------------|
| `hummbl-agent` | hummbl-agent (private) | Has pyproject.toml, package.json | Autonomous agent runtime — may contain internal fleet URLs; needs security review |
| `hummbl-iac` | hummbl-iac (private) | Has pyproject.toml | Infrastructure-as-code — may expose internal infra topology; needs review |
| `hummbl-production` | hummbl-production (private) | Has subdir pyproject.toml | Production infra — may contain internal fleet URLs; needs review |
| `hummbl-research` | hummbl-research (private) | Has pyproject.toml | Research code — may not be stable enough for public consumers |
| `hummbl-games` | hummbl-games (private) | Has pyproject.toml | Unclear public value; needs doctrinal review |
| `hummbl-intel` | hummbl-intel (private) | Has pyproject.toml | Intelligence-related; needs review for sensitive content |
| `hummbl-jepa` | hummbl-jepa (private) | Has pyproject.toml | Joint-Embedding Predictive Architecture — research code, may not be stable |
| `hummbl-120-agents` | hummbl-120-agents (private) | Has pyproject.toml | Agent definitions; may be internal-only |
| `hummbl-crucible` | hummbl-crucible (private) | Has pyproject.toml | Unclear scope; needs review |
| `hummbl-library` | hummbl-library (private) | Has pyproject.toml | Unclear scope; needs review |
| `hummbl-kernel-forge` | hummbl-kernel-forge (private) | Has pyproject.toml | Hardware compute kernels — different domain; needs review |
| `hummbl-gitea-control-plane` | hummbl-gitea-control-plane (private) | Has pyproject.toml | Internal infra control plane; needs review |
| `hummbl-interaction-control-plane` | hummbl-interaction-control-plane (private) | Has pyproject.toml | Internal infra; needs review |
| `scavenger-mode` | scavenger-mode (private) | Has pyproject.toml | Internal fleet tool; needs review |
| `adversary-emulation-playbook` | adversary-emulation-playbook (private) | Has pyproject.toml | MITRE ATT&CK adversary emulation — may be sensitive; needs review |
| `agent-governance-demo-v2` | agent-governance-demo-v2 (private) | Has pyproject.toml | Demo code; may not be production-quality |
| `model-routing-as-code` | model-routing-as-code (private) | Has pyproject.toml | May expose internal model routing; needs review |
| `provider-governance` | provider-governance (private) | Has pyproject.toml | Founder-mode infra; needs review |
| `idp-spec` | idp-spec (private) | Has pyproject.toml | Intelligent Delegation Profile — needs review |
| `whether-book` | whether-book (private) | Has pyproject.toml | Governed book system; needs review |
| `governance-tuple-reference` | governance-tuple-reference (private) | Has pyproject.toml | DCT-signed capability tokens; needs review |
| `artifact-compiler` | artifact-compiler (private) | Has pyproject.toml | Needs review |
| `autoresearch-win-rtx` | autoresearch-win-rtx (private) | Has pyproject.toml | GPU research agent; needs review |
| `foundermode-app` | foundermode-app (private) | Has pyproject.toml | Voice-first morning coaching app; needs review |
| `reubenos` | reubenos (private) | Has pyproject.toml | **Personal governed counterpart twin — review for personal data before any publication** |
| `ST3GG` | ST3GG (private) | Has pyproject.toml | Needs review |
| `psychedelic-claim-validator` | psychedelic-claim-validator (private) | Has pyproject.toml | Needs review |
| `general-claim-validator` | general-claim-validator (private) | Has pyproject.toml | Needs review |
| `hummbl-content-filter` | hummbl-content-filter (private) | Has pyproject.toml | Needs review |

### SHOULD NOT (not for the Full Menu)

These are excluded from the Full Menu by design — they are private
infrastructure, personal data, or internal-only surfaces that should never
be public. This category is intentionally not enumerated in detail (see
PACKAGES.md "Excluded from OSS migration").

---

## The Full Menu — Other registries

### npm (JavaScript/TypeScript)

All previously-published HUMMBL npm packages were deprecated 2026-08-21.
The `@hummbl` scope is clean. Future npm packages publish fresh under
`@hummbl/*` from this monorepo.

| Package | Status | Notes |
|---------|--------|-------|
| `@hummbl/mcp-server` | Greenfield | MCP server — needs package.json, scope flip |
| `@hummbl/agent` | Greenfield | Autonomous agent runtime — needs review |
| `@hummbl/asi` | Greenfield | Artificial Super Intelligence Framework |
| `@hummbl/tuples` | Greenfield | TS reference impl of tuples governance model |

### crates.io (Rust)

| Crate | Status | Notes |
|-------|--------|-------|
| `demosmesh` | Not published | Mesh networking — no_std core + Python via PyO3 |
| `hummbl-tuples` | Not published | Rust reference impl of tuples governance model |

### Go module proxy

| Module | Status | Notes |
|--------|--------|-------|
| `hummbl.io/tuples` | Not published | Go reference impl (tag-based publishing) |

### arXiv / Zenodo (papers)

| Paper | Status | Notes |
|-------|--------|-------|
| `hummbl-bibliography` | Not deposited | Provenance corpus, BibTeX citations |
| `hummbl-theory` | Not deposited | Formal definitions and proofs for Base120 |
| `krineia` | Not deposited | Cryptographic receipt system for skill invocations |

---

## Full Menu ordering philosophy

The Full Menu is comprehensive, but it is not unordered. The serving
sequence reflects the HUMMBL stack from the inside out:

1. **Core reasoning** — `hummbl` (thinking primitives)
2. **Core orchestration** — `hummbl-kernel` (execution primitives)
3. **Governance layer** — `hummbl-governance` (already live), `hummbl-contracts`
4. **Coordination layer** — `hummbl-bus` (already live), `hummbl-clp`
5. **Cognitive layer** — `hummbl-cognition` (already live), `hummbl-tuples` (already live)
6. **Evaluation layer** — `hummbl-eval`, `base120` (already live)
7. **Tooling layer** — `hummbl-lint-config`, `hummbl-validation`, `hummbl-bif` (already live)
8. **Application layer** — `hummbl-axis`, `hummbl-dashboard`, `hummbl-lattice`
9. **Domain layer** — `peptide-check`, `hummbl-content-filter`, domain-specific packages
10. **Polyglot layer** — `@hummbl/*` (npm), `demosmesh` (crates.io), `hummbl.io/tuples` (Go)

Each layer builds on the one before. A consumer can install just the core
(`pip install hummbl`), add orchestration (`pip install hummbl-kernel`),
add governance (`pip install hummbl-governance`), and so on — composing
their own meal from the Full Menu.

---

## Release readiness criteria

Every package on the Full Menu must pass this checklist before its first
release:

- [ ] `pyproject.toml` with: name, version, description, authors, license, keywords, classifiers, project.urls
- [ ] `LICENSE` file (Apache-2.0 for all HUMMBL packages)
- [ ] `NOTICE` file (attribution chain)
- [ ] `README.md` with install instructions (`pip install <name>`, not `git clone`)
- [ ] `CHANGELOG.md` with at least one released version section
- [ ] Tests pass (`pytest -q`)
- [ ] No secrets, internal fleet URLs, or personal data in the source
- [ ] Source migrated into `oss/packages/<name>/` (the public surface)
- [ ] Trusted publisher configured on pypi.org (owner: hummbl-io, repo: oss, workflow: publish-pypi.yml, environment: pypi)
- [ ] Tag pattern added to `.github/workflows/publish-pypi.yml`
- [ ] README packages table in oss root updated

---

## See also

- [PACKAGES.md](./PACKAGES.md) — the full technical inventory (~90 candidates across 10 registries)
- [MONOREPO-DESIGN.md](./MONOREPO-DESIGN.md) — the directory structure and migration plan
- [RELEASE.md](../RELEASE.md) — the release discipline (trusted publishing, no manual uploads)
