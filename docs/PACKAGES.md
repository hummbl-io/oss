# HUMMBL OSS — Published Packages

**Scope:** Packages in this monorepo and their public release state.
Internal migration planning, unpublished-repo inventories, and org-wide
scan results stay private.

**As of:** 2026-09-02, tree `packages/python/` = 25 packages.
Versions below are `pyproject.toml` on `main`.

## Name-collision warning (PyPI + npm)

The package names `hermes-agent`, `arbiter`, `arcana`, `crab`, `randy`, and
`mcp-server` are **not HUMMBL's** — they are unrelated packages by other
authors that happen to share common-word names. Verified 2026-08-21 against
each registry's author/repository/maintainer fields.

| Name | PyPI owner | npm owner |
|------|-----------|-----------|
| `hermes-agent` | Nous Research | wrtensi |
| `arbiter` | R.A. Stern (`rastern/arbiter`) | skbolton (`skbolton/Arbiter`) |
| `arcana` | (arcana.readthedocs.io) | flipactual (`flipactual/arcana`) |
| `crab` | Graham Bell (`grahambell/crab`) | kossnocorp (`kossnocorp/crab`) |
| `randy` | Francis Horsman (Bitbucket `sys-git/randy`) | deestan (`deestan/randy`) |
| `mcp-server` | (not on PyPI) | Melvin Carvalho (`sandy-mount/mcp-server`) |

HUMMBL PyPI packages use the `hummbl-*` prefix except `base120`,
`governed-compression`, and `idp-spec`. On npm, future packages use
`@hummbl/*`. Canonical install names from this repo:

```text
pip install base120
pip install hummbl-governance
```

Do not document `pip install arbiter`, `agent-governance`, or `base120-mcp`.

---

## 1. PyPI (Python)

### Live — wheel on the registry, HUMMBL-owned

Ownership last verified in fleet audits 2026-08-30 / 2026-08-31.
Tree versions checked 2026-09-02.

| Package | Tree | PyPI | Notes |
|---------|------|------|-------|
| `hummbl-governance` | 1.4.2 | 1.4.2 | Governance primitives. |
| `base120` | 3.0.0 | 3.0.0 | 120 reasoning operators. PyPI project URL may still point at the legacy standalone repo. |
| `hummbl-bif` | 1.0.1 | 1.0.1 | Batch Ingestion Framework. |
| `hummbl-tuples` | 0.2.0 | 0.2.0 | Typed tuples. Empty `project_urls` on live metadata as of 2026-08-31. |
| `hummbl-bus` | 0.2.0 | 0.2.0 | TSV coordination bus. 0.2.0 was uploaded 2026-08-27 with **no** `python/hummbl-bus/v0.2.0` tag in this repo. Further bus publishes wait on the tag contract in `RELEASE.md`. |
| `hummbl-cognition` | 0.1.0 | 0.1.0 | CLP + Open Brain. Live license field may still say MIT vs tree Apache-2.0. |
| `governed-compression` | 0.1.0 | 0.1.0 | Compression experiments. Live summary may still say "Private research surface". |
| `hummbl` | 0.1.0 | 0.1.0 | Shipped 2026-08-25. |
| `hummbl-kernel` | 0.1.0 | 0.1.0 | Shipped 2026-08-25. |

### In-tree — not on PyPI (no trusted-publishing tag yet)

| Package | Tree | Notes |
|---------|------|-------|
| `hummbl-lattice` | 0.1.0 | Domain120 lattices |
| `hummbl-contracts` | 0.1.0 | Contract schemas + stdlib validator |
| `hummbl-axis` | 0.1.0 | Atlas contradiction ladder |
| `hummbl-intel` | 0.1.0 | INT taxonomy |
| `hummbl-lint-config` | 0.1.0 | Shared ruff config |
| `idp-spec` | 0.1.0 | Intelligent Delegation Profile |
| `hummbl-compass` | 0.1.0 | Navigation / routing |
| `hummbl-free-models` | 0.1.0 | Open-weights registry |
| `hummbl-rubric-templates` | 0.1.0 | Eval rubrics |
| `hummbl-taxonomy` | 0.1.0 | Intelligence-tier taxonomy |
| `hummbl-validation` | 0.1.0 | Invariant / schema primitives |
| `hummbl-design-tokens` | 0.1.0 | Visual identity tokens |
| `hummbl-heraldry` | 0.1.0 | Procedural heraldry |
| `hummbl-garage` | 0.1.0 | API / livery / failure aesthetics |
| `hummbl-identity` | 0.1.0 | Identity facade |
| `hummbl-validation-framework` | 0.1.0 | Design-system validation tests |

### Excluded (not HUMMBL's)

| Package | Version | Owner | Notes |
|---------|---------|-------|-------|
| `OBLITERATUS` | 0.0.1 | Pliny (pliny-lab) | Reserved-name placeholder. Not HUMMBL's. |
| `arbiter` | — | R.A. Stern | Collision. Do not `pip install arbiter` from HUMMBL docs. |
| `agent-governance` | — | not HUMMBL org | Collision / foreign owner. |

---

## 2. npm (JavaScript/TypeScript)

### Live: none

There is no `packages/node/` tree in this monorepo.

Previously published HUMMBL npm packages were **deprecated by the
operator on 2026-08-21**:

- `@hummbl/mcp-server` v1.2.0 — deprecated ("Package no longer supported")
- `hummbl-bibliography` v1.0.0 — deprecated ("Package no longer supported")

The `@hummbl` scope still exists. Future npm packages publish under
`@hummbl/*` from this monorepo **after** a `packages/node/` tree exists.

**Name collisions (NOT HUMMBL's):** `mcp-server`, `hermes-agent`,
`arbiter`, `arcana`, `crab`, `randy` on npm.

---

## 3. Other languages in this repo

| Tree | Status |
|------|--------|
| `packages/lean/hummbl-formalization` | Present. Not in Python CI. Not a PyPI package. Do not call runtime packages "formally verified". |
| `packages/node/`, `packages/rust/`, `packages/go/`, `packages/jvm/` | **Absent.** |

---

## Monorepo consolidation status

`hummbl-io/oss` is the target monorepo for public HUMMBL packages.
Recommended future layout (not current tree):

```
oss/
├── packages/
│   ├── python/          # exists
│   ├── lean/            # exists
│   ├── node/            # not present
│   ├── rust/            # not present
│   └── go/              # not present
├── docs/
└── .github/workflows/
```

### Per-language publishing (current)

- **Python**: GitHub Actions trusted publishing from
  `.github/workflows/publish-pypi.yml`. Tag shape:
  `python/<package>/v<version>`. See `RELEASE.md`.
- **npm / crates / Go / JVM / Nix**: no publish workflow in this repo yet.

Do not use local `twine upload` for packages that should come from this
repo.
