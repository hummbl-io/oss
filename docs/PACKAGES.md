# HUMMBL OSS — Published Packages

**Scope:** Packages published (or being prepared for publication) from this
monorepo. This document describes public release state only. Internal
migration planning, unpublished-repo inventories, and org-wide scan results
are tracked privately and are not published here.

## Name-collision warning (PyPI + npm)

The package names `hermes-agent`, `<private-repo>`, `arcana`, `<private-repo>`, `<private-repo>`, and
`mcp-server` are **not HUMMBL's** — they are unrelated packages by other
authors that happen to share common-word names. Verified 2026-08-21 against
each registry's author/repository/maintainer fields.

| Name | PyPI owner | npm owner |
|------|-----------|-----------|
| `hermes-agent` | Nous Research | wrtensi |
| `<private-repo>` | R.A. Stern (`rastern/<private-repo>`) | skbolton (`skbolton/Arbiter`) |
| `arcana` | (arcana.readthedocs.io) | flipactual (`flipactual/arcana`) |
| `<private-repo>` | Graham Bell (`grahambell/<private-repo>`) | kossnocorp (`kossnocorp/<private-repo>`) |
| `<private-repo>` | Francis Horsman (Bitbucket `sys-git/<private-repo>`) | deestan (`deestan/<private-repo>`) |
| `mcp-server` | (not on PyPI) | Melvin Carvalho (`sandy-mount/mcp-server`) |

This is exactly the collision risk that the scoped `@hummbl/*` naming
decision (see `MONOREPO-DESIGN.md` section 4.2) eliminates on npm. On PyPI,
HUMMBL's packages use the `hummbl-*` prefix, which is distinctive enough to
avoid collisions; the colliding names above are unprefixed common words.

---

## 1. PyPI (Python)

### Live — verified HUMMBL-owned

| Package | Version | Notes |
|---------|---------|-------|
| `hummbl-governance` | 1.4.1 | Governance primitives — kill switch, circuit breaker, audit log, identity registry, capability fence, output validator, etc. |
| `<private-repo>` | 0.1.0 | Secure append-only TSV coordination bus. |
| `<private-repo>` | 0.1.0 | Cognitive Ledger Protocol + Open Brain server. |
| `<private-repo>` | 0.2.0 | Typed Tuples governance model (polyglot: also being ported to Go, Rust, TypeScript). |
| `<private-repo>` | 1.0.1 | Batch Ingestion Framework. |
| `<private-repo>` | 3.0.0 | 120 reasoning operators — stdlib-only, tuple-native. |
| `governed-compression` | 0.1.0 | Governed vector + KV-cache compression (ML). CPU reference implementation for quantization methods. Runtime dependency: `hummbl-governance>=1.1.0` (cross-package dependency — see `MONOREPO-DESIGN.md` section 7). |

### Excluded (not HUMMBL's)

| Package | Version | Owner | Notes |
|---------|---------|-------|-------|
| `OBLITERATUS` | 0.0.1 | Pliny (pliny-lab) | Reserved-name placeholder, no functionality. Not HUMMBL's — do not migrate. |

**Name collisions (NOT HUMMBL's — do not migrate):** the following PyPI
package names were previously listed as HUMMBL's in an earlier draft of
this document but are unrelated packages by other authors, verified
2026-08-21 via PyPI author/repository fields:

- `<private-repo>` v1.1.2 → R.A. Stern (`rastern/<private-repo>`)
- `arcana` v0.10.19 → `arcana.readthedocs.io`
- `<private-repo>` v0.5.1 → Graham Bell (`grahambell/<private-repo>`)
- `<private-repo>` v0.9.3 → Francis Horsman (Bitbucket `sys-git/<private-repo>`)
- `hermes-agent` v0.19.0 → Nous Research

These are unprefixed common-word names. HUMMBL's packages use the
`hummbl-*` prefix, which avoids this collision class on PyPI.

---

## 2. npm (JavaScript/TypeScript)

### Live: none currently

All previously-published HUMMBL npm packages were **deprecated by the
operator on 2026-08-21**:

- `@hummbl/mcp-server` v1.2.0 — deprecated ("Package no longer supported")
- `<private-repo>` v1.0.0 — deprecated ("Package no longer supported")

The `@hummbl` scope still exists (operator owns it under the `hummbl-io`
npm account with `write` permission). Future HUMMBL npm packages publish
fresh under `@hummbl/*` from this monorepo.

**Name collisions (NOT HUMMBL's — never were):** the following unscoped
npm package names were previously listed as HUMMBL's in an earlier draft
of this document but are unrelated packages by other authors, verified
2026-08-21 via the npm registry `repository` and `maintainers` fields:

- `mcp-server` v0.0.9 → Melvin Carvalho (`sandy-mount/mcp-server`)
- `hermes-agent` v0.20.4 → `wrtensi/hermes-agent-npm`
- `<private-repo>` v2.0.2 → `skbolton/Arbiter`
- `arcana` v0.0.2 → `flipactual/arcana`
- `<private-repo>` v1.13.0 → `kossnocorp/<private-repo>`
- `<private-repo>` v1.5.1 → `deestan/<private-repo>`

These are common-word package names squatted/published by other authors.
This collision risk is the reason HUMMBL publishes under the `@hummbl/`
scope going forward.

---

## Monorepo consolidation status

The `hummbl-io/oss` repo is the target monorepo for HUMMBL's published,
open-source packages. Packages are added here as they are prepared for (or
already have) public release; unpublished/internal work is not staged into
this document ahead of release.

### Recommended package layout (polyglot)

```
oss/
├── packages/
│   ├── python/          # PyPI packages
│   ├── node/             # npm packages (@hummbl/* scope)
│   ├── rust/              # crates.io
│   ├── go/                # Go module proxy
│   └── jvm/               # Maven Central
├── papers/               # arXiv/Zenodo
├── docs/                 # Mintlify
├── sites/                # GitHub Pages
├── cli/                  # Scoop/Winget/Homebrew manifests
└── .github/workflows/    # One CI for all languages
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
