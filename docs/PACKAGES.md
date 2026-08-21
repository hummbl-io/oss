# HUMMBL OSS Publishable Inventory — Polyglot Survey

**Date:** 2026-08-21
**Lane:** ops/devin/oss-polyglot-inventory-20260821
**Method:** Probed all 150+ repos in `hummbl-io` org for publishable manifests across 10+ language ecosystems. Verified live status against PyPI, npm, crates.io registries.
**Goal:** Find every single thing that can be published as OSS, across all programming languages built for or planned for the future.

## Executive Summary

| Registry | Live | Publishable (not yet live) | Needs work | Total candidates |
|----------|------|-----------------------------|------------|------------------|
| **PyPI** (Python) | 8 | ~31 | ~8 | 47 |
| **npm** (JS/TS) | 0 | ~10 | ~4 | 16 |
| **crates.io** (Rust) | 0 | 2 | 0 | 2 |
| **Go module proxy** | 0 | 1 | 0 | 1 |
| **Maven Central** (Java/Kotlin) | 0 | 2 | 0 | 2 |
| **arXiv/Zenodo** (TeX) | 0 | 4 | 0 | 4 |
| **Scoop/Winget/Homebrew** (CLI) | 0 | 4 | 4 | 8 |
| **Nix flakes** | 0 | 2 | 0 | 2 |
| **GitHub Pages** (static sites) | 0 | ~6 | 0 | 6 |
| **Mintlify docs** | 0 | 2 | 0 | 2 |
| **TOTAL** | **8** | **~64** | **~16** | **~90** |

**Polyglot packages** (same package published across multiple languages):
- `hummbl-tuples`: Python (live) + Go + Rust + TypeScript (3 not published) — the polyglot model

**Name-collision warning (PyPI + npm):** The package names `hermes-agent`, `arbiter`, `arcana`, `crab`, `randy`, and `mcp-server` are NOT HUMMBL's on either PyPI or npm — they are unrelated packages by other authors that happened to share common-word names. Verified 2026-08-21 against both registries' author/repository/maintainer fields:

| Name | PyPI owner | npm owner |
|------|-----------|-----------|
| `hermes-agent` | Nous Research | wrtensi |
| `arbiter` | R.A. Stern (`rastern/arbiter`) | skbolton (`skbolton/Arbiter`) |
| `arcana` | (arcana.readthedocs.io) | flipactual (`flipactual/arcana`) |
| `crab` | Graham Bell (`grahambell/crab`) | kossnocorp (`kossnocorp/crab`) |
| `randy` | Francis Horsman (Bitbucket `sys-git/randy`) | deestan (`deestan/randy`) |
| `mcp-server` | — | Melvin Carvalho (`sandy-mount/mcp-server`) |

This is exactly the collision risk that the scoped `@hummbl/*` naming decision (section 4.2 of MONOREPO-DESIGN.md) eliminates on npm. On PyPI, HUMMBL's packages use the `hummbl-*` prefix which is distinctive enough to avoid collisions; the colliding names above are unprefixed common words.

---

## 1. PyPI (Python) — 47 candidates

### Live (8) — verified HUMMBL-owned
| Package | Version | Repo | Ownership verified | Notes |
|---------|---------|------|--------------------|-------|
| `hummbl-governance` | 1.4.1 | hummbl-governance → oss | 2026-08-21 (published this session) | Governance primitives — kill switch, circuit breaker, etc. Links remediated to `github.com/hummbl-io/oss` in 1.4.1. |
| `hummbl-bus` | 0.1.0 | hummbl-bus | 2026-08-21 (naming + repo match) | Secure append-only TSV coordination bus. No project_urls on PyPI — needs link remediation on next publish. |
| `hummbl-cognition` | 0.1.0 | hummbl-cognition | 2026-08-21 (naming + repo match) | Cognitive Ledger Protocol + Open Brain server. No project_urls on PyPI — needs link remediation on next publish. |
| `hummbl-tuples` | 0.2.0 | hummbl-tuples | 2026-08-21 (naming + repo match) | Typed Tuples governance model (polyglot: also Go, Rust, TS). No project_urls on PyPI — needs link remediation. |
| `hummbl-bif` | 1.0.1 | bif | 2026-08-21 (naming + repo match) | Batch Ingestion Framework. README says archived into `hummbl-io/hummbl-toolkit`. No project_urls on PyPI. |
| `base120` | 3.0.0 | base120 | 2026-08-21 (repo link = hummbl.io, HUMMBL domain) | 120 reasoning operators — stdlib-only, tuple-native. Repo link = `hummbl.io` (no GitHub URL). |
| `governed-compression` | 0.1.0 | governed-compression | 2026-08-21 (operator-confirmed; naming + matching private repo) | Governed vector + KV-cache compression (ML). CPU reference implementation for quantization methods (TurboQuant-style, QJL, baselines). Runtime dep: `hummbl-governance>=1.1.0` (cross-package dependency — see MONOREPO-DESIGN.md section 7). Repo link on PyPI: none (needs remediation on next publish). |
| `OBLITERATUS` | 0.0.1 | — | 2026-08-21 (operator: NOT HUMMBL's — Pliny's) | **NOT HUMMBL's — belongs to Pliny (pliny-lab).** Reserved-name placeholder, no functionality. Listed here only to document that it is excluded from the migration. Do not migrate. |

**Name collisions (NOT HUMMBL's — do not migrate):** The following PyPI package names were previously listed as HUMMBL's in an earlier draft but are unrelated packages by other authors, verified 2026-08-21 via PyPI author/repository fields:
- `arbiter` v1.1.2 → R.A. Stern (`rastern/arbiter`)
- `arcana` v0.10.19 → `arcana.readthedocs.io`
- `crab` v0.5.1 → Graham Bell (`grahambell/crab`)
- `randy` v0.9.3 → Francis Horsman (Bitbucket `sys-git/randy`)
- `hermes-agent` v0.19.0 → Nous Research

These are unprefixed common-word names. HUMMBL's packages use the `hummbl-*` prefix, which avoids this collision class on PyPI.

### Publishable but not yet on PyPI (~31)
| Repo | Has pyproject.toml | Notes |
|------|-------------------|-------|
| `hummbl-lattice` | root | Domain-specific reasoning operator lattices |
| `hummbl-eval` | root | Model evaluation suites and benchmark runners |
| `hummbl-dashboard` | root | Fleet health, agent metrics, observability |
| `hummbl-clp` | root | Cognitive Ledger Protocol |
| `hummbl-contracts` | root | Governance contracts |
| `hummbl-content-filter` | root | Content filtering |
| `hummbl-crucible` | root | |
| `hummbl-validation` | root | Shared validation primitives |
| `hummbl-lint-config` | root | Shared ruff lint configuration |
| `hummbl-axis` | root | Ladder that selects which Atlas contradiction to act on |
| `hummbl-library` | root | |
| `hummbl-games` | root | |
| `hummbl-intel` | root | |
| `hummbl-jepa` | root | |
| `hummbl-kernel-forge` | root | |
| `hummbl-research` | root | |
| `hummbl-120-agents` | root | |
| `hummbl-iac` | root | Infrastructure-as-code |
| `hummbl-gitea-control-plane` | root | |
| `hummbl-interaction-control-plane` | root | |
| `peptide-check` | root | Peptide safety claims |
| `whether-book` | root | Governed book system |
| `scavenger-mode` | root | |
| `idp-spec` | root | Intelligent Delegation Profile |
| `model-routing-as-code` | root | Model/provider selection rules |
| `provider-governance` | root (+ subdirectory packages) | |
| `psychedelic-claim-validator` | root | |
| `general-claim-validator` | root | |
| `governance-tuple-reference` | root | DCT-signed capability tokens |
| `adversary-emulation-playbook` | root | MITRE ATT&CK adversary emulation |
| `agent-governance-demo-v2` | root | Runtime safety primitives demo |
| `agent-identity-kit` | root | |
| `artifact-compiler` | root | |
| `autoresearch-win-rtx` | root | GPU research agent |
| `foundermode-app` | root | Voice-first morning coaching app |
| `reubenos` | root | Personal governed counterpart twin (review before publishing) |
| `ST3GG` | root | |

### Multi-package repos (subdir pyproject.toml — each is a separate package)
| Repo | Subdir packages | Notes |
|------|----------------|-------|
| `mcp-server` | `packages/python/base120`, `packages/python/bif` | MCP server with embedded Python packages |
| `hummbl-toolkit` | `adversary-emulation`, `bif` | Shared utilities, multiple packages |
| `hummbl-agent` | `packages/runtime`, `skills/local-places` | Agent runtime with multiple packages |
| `hummbl-production` | `hummbl-governed-quest-sim`, `minecraft-governance` | Production infra with game governance |
| `pliny-lab` | `OBLITERATUS`, `P4RS3LT0NGV3` | Red-team lab with multiple packages |
| `apex-nexus` | root (+ embedded package subdirs) | Fleet mesh with embedded packages |

---

## 2. npm (JavaScript/TypeScript) — 16 candidates

### Live (0) — clean slate
All previously-published HUMMBL npm packages were **deprecated by the operator on 2026-08-21**:
- `@hummbl/mcp-server` v1.2.0 — deprecated ("Package no longer supported")
- `hummbl-bibliography` v1.0.0 — deprecated ("Package no longer supported")

The `@hummbl` scope still exists (operator owns it under the `hummbl-dev` npm account with `write` permission). Future HUMMBL npm packages publish fresh under `@hummbl/*` from this monorepo. No live packages to migrate — Phase 2 of the migration plan is a clean greenfield.

**Name collisions (NOT HUMMBL's — never were):** The following unscoped npm package names were previously listed as HUMMBL's in an earlier draft of this inventory but are unrelated packages by other authors, verified 2026-08-21 via the npm registry `repository` and `maintainers` fields:
- `mcp-server` v0.0.9 → Melvin Carvalho (`sandy-mount/mcp-server`)
- `hermes-agent` v0.20.4 → `wrtensi/hermes-agent-npm`
- `arbiter` v2.0.2 → `skbolton/Arbiter`
- `arcana` v0.0.2 → `flipactual/arcana`
- `crab` v1.13.0 → `kossnocorp/crab`
- `randy` v1.5.1 → `deestan/randy`

These are common-word package names squatted/published by other authors. This collision risk is the reason HUMMBL publishes under the `@hummbl/` scope going forward.

### Publishable but not yet on npm (~10)
| Repo | package.json name | Notes |
|------|-------------------|-------|
| `hummbl-agent` | `hummbl-agent` (private: true — needs flip) | Autonomous agent runtime |
| `hummbl-asi` | `hummbl-asi` v0.1.0 | Artificial Super Intelligence Framework |
| `hummbl-governance` | (has package.json) | Governance (JS binding?) |
| `hummbl-legal` | | |
| `hummbl-paralegal` | | |
| `hummbl-library` | | |
| `jsr-app` | `jsr-app` v1.0.0 | JSR web app |
| `jsr-extension` | | JSR browser extension |
| `alchemy-ai-governance-prototype` | | Workday governance prototype |
| `NATURALIS-FUTURA` | | |
| `project-audits` | | |
| `G0DM0D3` | | |

### Needs work
| Repo | Issue | Notes |
|------|-------|-------|
| `hummbl-tuples` TS ref impl | No package.json (only `tuple.ts`, `conformance_test.ts`) | Needs package.json to publish |
| `coaching-private` | | Review — may be personal |
| `hummbl-cyber` | Has `bin/` but no package.json in root | CLI tool — needs package.json |

---

## 3. crates.io (Rust) — 2 candidates

| Crate | Repo | Path | Status | Notes |
|-------|------|------|--------|-------|
| `demosmesh` | demosmesh | root Cargo.toml | Not published | Mesh networking platform — no_std core + Python via PyO3 |
| `hummbl-tuples` | hummbl-tuples | `reference_impl/rust/Cargo.toml` | Not published | Rust reference impl of tuples governance model |

---

## 4. Go module proxy — 1 candidate

| Module | Repo | Path | Status | Notes |
|--------|------|------|--------|-------|
| `hummbl.io/tuples` | hummbl-tuples | `reference_impl/go/go.mod` (Go 1.22) | Not published | Go reference impl of tuples governance model |

---

## 5. Maven Central / Gradle (Java/Kotlin) — 2 candidates

| Project | Repo | Path | Build system | Status | Notes |
|---------|------|------|--------------|--------|-------|
| `fabric-adapter` | hummbl-production | `hummbl-governed-quest-sim/fabric-adapter/` | Gradle | Not published | Java — Minecraft Fabric adapter |
| `V3SP3R` | pliny-lab | `V3SP3R/` | Gradle Kotlin | Not published | Kotlin/Android — red-team lab app |

---

## 6. arXiv / Zenodo (TeX) — 4 candidates

| Repo | Has CITATION.cff | Notes |
|------|------------------|-------|
| `hummbl-bibliography` | likely | Provenance corpus, BibTeX citations, position papers |
| `hummbl-theory` | likely | Formal definitions and proofs for Base120 |
| `krineia` | yes | Cryptographic receipt system for skill invocations |
| `coaching-private` | likely | Coaching methodology (review — may be personal) |

---

## 7. CLI tools (Scoop / Winget / Homebrew) — 8 candidates

| Repo | Target | Status | Notes |
|------|--------|--------|-------|
| `scoop-bucket` | Scoop (Windows) | Empty — no manifests yet | Bucket exists, no packages |
| `winget-manifests` | Winget (Windows) | Empty — no manifests yet | Repo exists, no manifests |
| `nix` | Nix flakes | Empty — no flakes yet | Repo exists, no actual flakes |
| `hummbl-cli` | Homebrew/Scoop/Winget | Has docs but no bin/ | Shell-based CLI for Base120 lookup |
| `hummbl-cyber` | CLI | Has `bin/` but no package.json | Cyber workbench CLI |
| `hummbl-bus` | CLI | (PyPI package has CLI) | Already installable via pip |
| `hummbl-governance` | CLI | (PyPI package has CLI) | Already installable via pip |
| `base120` | CLI | (PyPI package has CLI) | Already installable via pip |

---

## 8. Nix flakes — 2 candidates

| Repo | Has flake.nix | Status | Notes |
|------|---------------|--------|-------|
| `hermes-agent` | yes (flake.nix, flake.lock, nix/) | Not published to nixpkgs | |
| `nix` | no (empty repo) | Needs flakes | Repo exists but no actual flakes |

---

## 9. GitHub Pages (static sites) — 6 candidates

| Repo | Language | Notes |
|------|----------|-------|
| `hummbl-dev` | HTML | Org profile site |
| `hummbl-brand` | HTML | Brand site |
| `NATURALIS-FUTURA` | HTML | |
| `ST3GG` | HTML | |
| `hummbl-kernel-forge` | HTML | |
| `shared-design-systems` | HTML | Design system tokens/components |

---

## 10. Mintlify docs — 2 candidates

| Repo | Notes |
|------|-------|
| `docs` | Canonical public documentation — Mintlify-powered |
| `mintlify-docs` | Documentation portal — Mintlify-powered |

---

## NOT publishable (internal/personal — exclude from OSS)

| Repo | Reason |
|------|--------|
| `job-search-2026` | Personal job search |
| `jenna-collaboration-routing` | Private collaboration map |
| `delta-fleet` | Private workstation config |
| `professional-history` | Personal |
| `reubenos` | Personal governed twin (review carefully) |
| `meeting-archive` | Private meeting transcripts |
| `lsat-prep` | Personal study |
| `hd-ai-education-internal` | Internal |
| `hd-ai-education-research` | Internal research |
| `microsoft-locked-clients-research` | Research on vendor lock-in |
| `vault` | Secrets |
| `fleet-manifests` | Internal fleet config |
| `fleet-runbooks` | Internal runbooks |
| `vendor-skill-fleet` | Internal vendor skills |
| `anvil-bin` | Host-specific utilities |
| `delta-disaster-assessment` | Research models (review) |
| `NemoClaw` | Unclear purpose |
| `gitea-cicd-canary` | Internal CI canary |
| `github-public-surface-crawl` | Internal audit tool |
| `swarm-test-archive` | Internal test archive |
| `autoresearch-reports` | Internal reports |
| `legacy-hummbl-dev-org-profile` | Legacy profile |
| `jenna-collaboration-routing` | Private |

---

## Monorepo consolidation status

The `hummbl-io/oss` repo (created 2026-08-21) is the target monorepo. Current state:
- `packages/hummbl-governance/` already migrated (pyproject.toml present)
- README lists 5 live PyPI packages as consolidated
- `docs/MONOREPO-DESIGN.md` referenced but not yet created
- No JS/Rust/Go/Java package dirs yet

### Recommended monorepo structure (polyglot)

```
oss/
├── packages/
│   ├── python/          # PyPI packages
│   │   ├── hummbl-governance/
│   │   ├── hummbl-bus/
│   │   ├── hummbl-cognition/
│   │   ├── hummbl-tuples/
│   │   ├── hummbl-bif/
│   │   ├── base120/
│   │   ├── arbiter/
│   │   ├── arcana/
│   │   ├── crab/
│   │   └── ... (31 more)
│   ├── node/            # npm packages
│   │   ├── hummbl-agent/
│   │   ├── hummbl-asi/
│   │   ├── mcp-server/
│   │   └── ... (10 more)
│   ├── rust/            # crates.io
│   │   ├── demosmesh/
│   │   └── hummbl-tuples-rs/
│   ├── go/              # Go module proxy
│   │   └── hummbl-tuples-go/
│   ├── jvm/             # Maven Central
│   │   ├── fabric-adapter/
│   │   └── v3sp3r/
│   └── nix/             # Nix flakes
│       └── hermes-agent/
├── papers/              # arXiv/Zenodo
│   ├── hummbl-bibliography/
│   ├── hummbl-theory/
│   └── krineia/
├── docs/                # Mintlify
├── sites/               # GitHub Pages
│   ├── hummbl-dev/
│   ├── hummbl-brand/
│   └── ...
├── cli/                 # Scoop/Winget/Homebrew manifests
│   ├── scoop-bucket/
│   ├── winget-manifests/
│   └── homebrew-formula/
└── .github/workflows/   # One CI for all languages
```

### Per-language publishing workflow
- **Python**: `uv publish` / `twine upload` from `packages/python/<name>/`
- **npm**: `npm publish` from `packages/node/<name>/`
- **Rust**: `cargo publish` from `packages/rust/<name>/`
- **Go**: tag-based publishing (Go module proxy fetches from git tags)
- **JVM**: `gradle publish` to Maven Central
- **Nix**: publish flakes to FlakeHub or nixpkgs PR
- **TeX**: submit to arXiv, deposit to Zenodo with DOI
- **CLI**: auto-generate Scoop/Winget/Homebrew manifests on release

---

## Source
- Repo list: `gh repo list hummbl-io --limit 200` (150+ repos)
- Manifest probe: `gh api repos/hummbl-io/<repo>/contents` for root files, `gh api repos/hummbl-io/<repo>/git/trees/HEAD?recursive=1` for deep scan
- Live PyPI check: `https://pypi.org/pypi/<name>/json` (HTTP 200 = live, 404 = not published)
- Live npm check: `https://registry.npmjs.org/<name>` (dist-tags.latest = live, 404 = not published)
- Live crates.io check: `https://crates.io/api/v1/crates/<name>` (404 = not published)
