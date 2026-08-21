# HUMMBL OSS Monorepo Design

**Status:** Proposed
**Date:** 2026-08-21
**Authors:** HUMMBL fleet (devin, operator)

## Purpose

One repo, one CI, one source of truth for every HUMMBL package that can be
published as open source — across every programming language we have built
for or plan to build for. This document defines the directory structure,
tag conventions, per-language publishing workflows, and migration path.

The inventory of publishable packages lives in
[`PACKAGES.md`](./PACKAGES.md) (~100 candidates across 10 registries).
This document defines the container they live in.

---

## 1. Directory structure

### Target layout

```
oss/
├── packages/
│   ├── python/              # PyPI
│   │   ├── hummbl-governance/
│   │   ├── hummbl-bus/
│   │   ├── hummbl-cognition/
│   │   ├── hummbl-tuples/
│   │   ├── hummbl-bif/
│   │   ├── base120/
│   │   ├── arbiter/
│   │   └── …
│   ├── node/                # npm
│   │   ├── hummbl-agent/
│   │   ├── hummbl-asi/
│   │   ├── mcp-server/
│   │   ├── hummbl-tuples/   # TS reference impl
│   │   └── …
│   ├── rust/                # crates.io
│   │   ├── demosmesh/
│   │   └── hummbl-tuples/   # Rust reference impl
│   ├── go/                  # Go module proxy
│   │   └── hummbl-tuples/   # Go reference impl
│   ├── jvm/                 # Maven Central
│   │   ├── fabric-adapter/
│   │   └── v3sp3r/
│   └── nix/                 # Nix flake registry
│       └── hermes-agent/
├── papers/                  # arXiv / Zenodo (TeX)
│   ├── hummbl-bibliography/
│   ├── hummbl-theory/
│   └── krineia/
├── docs/                    # Mintlify docs site
├── sites/                   # GitHub Pages (static)
│   ├── hummbl-dev/
│   ├── hummbl-brand/
│   └── …
├── cli/                     # Scoop / Winget / Homebrew manifests
│   ├── scoop-bucket/
│   ├── winget-manifests/
│   └── homebrew/
├── tools/                   # Shared repo-level tooling
│   ├── scripts/
│   └── templates/
├── .github/
│   └── workflows/
│       ├── ci-python.yml
│       ├── ci-node.yml
│       ├── ci-rust.yml
│       ├── ci-go.yml
│       ├── ci-jvm.yml
│       ├── publish-pypi.yml
│       ├── publish-npm.yml
│       ├── publish-crates.yml
│       ├── publish-go.yml
│       └── publish-jvm.yml
├── README.md
├── LICENSE                  # Apache-2.0
└── docs/
    ├── MONOREPO-DESIGN.md   # this file
    └── PACKAGES.md          # full inventory
```

### Why language-namespaced `packages/<lang>/<name>/`

The current structure is flat: `packages/<name>/`. That works for a
single-language monorepo. For a polyglot monorepo it breaks down:

1. **Build tools conflict.** `pyproject.toml` and `package.json` and
   `Cargo.toml` in the same directory confuse language servers, linters,
   and CI path filters. Namespacing by language keeps each package
   directory homogeneous.

2. **CI path filters are clean.** `packages/python/**` triggers
   `ci-python.yml`, `packages/rust/**` triggers `ci-rust.yml`. No
   per-package glob lists.

3. **Polyglot packages are explicit.** `hummbl-tuples` has 4 language
   implementations. Under the flat scheme they'd collide on directory
   name. Under language namespacing they are siblings:
   `packages/python/hummbl-tuples/`, `packages/rust/hummbl-tuples/`,
   `packages/go/hummbl-tuples/`, `packages/node/hummbl-tuples/`.

4. **Registry mapping is obvious.** The directory name tells you which
   registry the package publishes to. No lookup table needed.

### Migration from current `packages/<name>/`

The current `packages/hummbl-governance/` moves to
`packages/python/hummbl-governance/`. This is a `git mv` — history is
preserved. The `publish-pypi.yml` workflow tag filter and path extraction
are updated in the same PR.

---

## 2. Tag conventions

Every release is a git tag. The tag encodes the language, package name,
and version:

```
<lang>/<package-name>/v<version>
```

Examples:

| Tag | Registry | Package | Version |
|-----|----------|---------|---------|
| `python/hummbl-governance/v1.4.1` | PyPI | hummbl-governance | 1.4.1 |
| `python/hummbl-bus/v0.2.0` | PyPI | hummbl-bus | 0.2.0 |
| `node/hummbl-agent/v0.1.0` | npm | hummbl-agent | 0.1.0 |
| `rust/demosmesh/v0.1.0` | crates.io | demosmesh | 0.1.0 |
| `go/hummbl-tuples/v0.1.0` | Go proxy | hummbl.io/tuples | 0.1.0 |
| `jvm/fabric-adapter/v0.1.0` | Maven Central | fabric-adapter | 0.1.0 |

### Polyglot package releases

A polyglot package like `hummbl-tuples` has independent versions per
language. Each language variant is tagged and released separately:

```
python/hummbl-tuples/v0.2.1    # PyPI
rust/hummbl-tuples/v0.1.0      # crates.io
go/hummbl-tuples/v0.1.0        # Go proxy
node/hummbl-tuples/v0.1.0      # npm
```

Versions MAY align across languages for a coordinated release, but this
is not required. Each language variant has its own changelog under its
package directory.

### Pre-release tags

Use PEP 440 / SemVer suffixes directly in the tag:

```
python/hummbl-governance/v1.5.0a1     # alpha
python/hummbl-governance/v1.5.0b1     # beta
python/hummbl-governance/v1.5.0rc1    # release candidate
node/hummbl-agent/v0.2.0-beta.1       # npm pre-release
rust/demosmesh/v0.1.0-pre.1           # crates pre-release
```

---

## 3. Versioning

**Independent per package.** Each package has its own version number and
its own changelog. There is no monorepo-wide "v1.2.3" release.

Rationale: the packages are independently useful libraries. A governance
fix should not force a version bump on `base120` or `demosmesh`. Users
install one package, not the monorepo.

**Version sources:**

| Language | Version source | Bump command |
|----------|---------------|--------------|
| Python | `pyproject.toml` `[project] version` | manual edit |
| Node | `package.json` `"version"` | `npm version patch` |
| Rust | `Cargo.toml` `[package] version` | `cargo set-version` |
| Go | git tag only (no version file) | tag push |
| JVM | `build.gradle` `version =` | manual edit |

---

## 4. Per-language publishing workflows

### 4.1 Python → PyPI

**Registry:** [pypi.org](https://pypi.org)
**Auth:** Trusted Publishing (OIDC) — no API tokens
**Build tool:** `python -m build` (PEP 517)
**Publish tool:** `twine upload`

**Workflow:** `.github/workflows/publish-pypi.yml`

```yaml
name: Publish to PyPI

"on":
  push:
    tags:
      - "python/*/v*"

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # OIDC trusted publishing
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name from tag
        id: pkg
        run: |
          # tag format: python/<package-name>/v<version>
          name="${GITHUB_REF_NAME#python/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/python/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Build
        working-directory: ${{ steps.pkg.outputs.path }}
        run: |
          pip install build
          python -m build

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        env:
          TWINE_NON_INTERACTIVE: "1"
        run: |
          pip install twine
          twine upload dist/*
```

**Per-package setup (one-time):**
1. On pypi.org → Manage → Publishing → Add trusted publisher
2. Workflow file: `.github/workflows/publish-pypi.yml`
3. Environment: `pypi`
3. Repository: `hummbl-io/oss`
4. Tag pattern: `python/<package-name>/v*`

**To publish:**
```bash
# 1. Bump version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit and tag
git tag python/hummbl-governance/v1.4.1
git push origin python/hummbl-governance/v1.4.1
# 4. CI builds and publishes automatically
```

### 4.2 Node → npm

**Registry:** [npmjs.com](https://npmjs.com)
**Auth:** npm automation token (stored as GitHub secret `NPM_TOKEN`)
**Build tool:** package-specific (tsc, bun, vite, etc.)
**Publish tool:** `npm publish`

**Workflow:** `.github/workflows/publish-npm.yml`

```yaml
name: Publish to npm

"on":
  push:
    tags:
      - "node/*/v*"

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#node/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/node/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          registry-url: "https://registry.npmjs.org"

      - name: Install
        working-directory: ${{ steps.pkg.outputs.path }}
        run: npm ci

      - name: Build
        working-directory: ${{ steps.pkg.outputs.path }}
        run: npm run build --if-present

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npm publish --access public
```

**Per-package setup:**
1. Set `package.json` `"private": false` (remove `"private": true`)
2. Ensure `"name"`, `"version"`, `"license"`, `"repository"` fields are set
3. Add `NPM_TOKEN` to GitHub repo secrets (one token, shared across all npm packages)
4. Tag and push: `git tag node/hummbl-agent/v0.1.0 && git push origin node/hummbl-agent/v0.1.0`

### 4.3 Rust → crates.io

**Registry:** [crates.io](https://crates.io)
**Auth:** crates.io API token (stored as GitHub secret `CARGO_REGISTRY_TOKEN`)
**Build tool:** `cargo build`
**Publish tool:** `cargo publish`

**Workflow:** `.github/workflows/publish-crates.yml`

```yaml
name: Publish to crates.io

"on":
  push:
    tags:
      - "rust/*/v*"

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: crates
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#rust/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/rust/$name" >> "$GITHUB_OUTPUT"

      - uses: dtolnay/rust-toolchain@stable

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        env:
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
        run: cargo publish --token "$CARGO_REGISTRY_TOKEN"
```

**Per-package setup:**
1. Ensure `Cargo.toml` has `[package] name`, `version`, `description`, `license`, `repository`
2. Add `CARGO_REGISTRY_TOKEN` to GitHub repo secrets
3. Tag and push: `git tag rust/demosmesh/v0.1.0 && git push origin rust/demosmesh/v0.1.0`

### 4.4 Go → Go module proxy

**Registry:** [proxy.golang.org](https://proxy.golang.org)
**Auth:** None — Go module proxy fetches from public git tags
**Publish tool:** `git tag` + `git push` (no build step)

Go modules are published by pushing a tag. The Go module proxy
automatically fetches and caches the module. No workflow file is needed
for publishing — the tag push IS the publish.

**Module path convention:**

```go
// go.mod
module github.com/hummbl-io/oss/packages/go/<name>

go 1.22
```

**To publish:**
```bash
git tag go/hummbl-tuples/v0.1.0
git push origin go/hummbl-tuples/v0.1.0
# Go proxy fetches within minutes — no CI needed
```

**CI (optional, for validation only):** `.github/workflows/ci-go.yml`

```yaml
name: CI (Go)

"on":
  push:
    paths:
      - "packages/go/**"
      - ".github/workflows/ci-go.yml"
  pull_request:
    paths:
      - "packages/go/**"

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go-version: ["1.22", "1.23"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - name: Test
        working-directory: packages/go
        run: go test ./...
```

### 4.5 JVM → Maven Central

**Registry:** [Maven Central](https://central.sonatype.com)
**Auth:** Sonatype Central Portal token + GPG signing key
**Build tool:** Gradle
**Publish tool:** `gradle publishAndRelease`

**Workflow:** `.github/workflows/publish-jvm.yml`

```yaml
name: Publish to Maven Central

"on":
  push:
    tags:
      - "jvm/*/v*"

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: maven
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#jvm/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/jvm/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: "temurin"

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v4

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        env:
          ORG_GRADLE_PROJECT_sonatypeUsername: ${{ secrets.SONATYPE_USERNAME }}
          ORG_GRADLE_PROJECT_sonatypePassword: ${{ secrets.SONATYPE_PASSWORD }}
          ORG_GRADLE_PROJECT_signingKeyId: ${{ secrets.GPG_KEY_ID }}
          ORG_GRADLE_PROJECT_signingKey: ${{ secrets.GPG_PRIVATE_KEY }}
          ORG_GRADLE_PROJECT_signingPassword: ${{ secrets.GPG_PASSWORD }}
        run: ./gradlew publishAndRelease
```

**Per-package setup:**
1. Configure `build.gradle` with `maven-publish` plugin and Central Portal credentials
2. Set up GPG signing key (Maven Central requires signed artifacts)
3. Add secrets: `SONATYPE_USERNAME`, `SONATYPE_PASSWORD`, `GPG_KEY_ID`, `GPG_PRIVATE_KEY`, `GPG_PASSWORD`
4. Tag and push: `git tag jvm/fabric-adapter/v0.1.0 && git push origin jvm/fabric-adapter/v0.1.0`

### 4.6 Nix → FlakeHub / nixpkgs

**Registry:** [flakehub.com](https://flakehub.com) (primary), nixpkgs (optional)
**Auth:** FlakeHub API token
**Publish tool:** `fh push`

Nix flakes are referenced directly from git. Publishing to FlakeHub makes
them discoverable and cacheable.

**Workflow:** `.github/workflows/publish-nix.yml`

```yaml
name: Publish Nix flake

"on":
  push:
    tags:
      - "nix/*/v*"

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: nix
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#nix/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/nix/$name" >> "$GITHUB_OUTPUT"

      - uses: DeterminateSystems/nix-installer-action@main

      - uses: DeterminateSystems/flakehub-push@main
        with:
          visibility: public
          name: hummbl-io/${{ steps.pkg.outputs.name }}
          directory: ${{ steps.pkg.outputs.path }}
          tag: ${{ github.ref_name }}
```

### 4.7 TeX → arXiv / Zenodo

**Registry:** [arxiv.org](https://arxiv.org) (preprints), [Zenodo](https://zenodo.org) (DOI deposits)
**Auth:** arXiv API key, Zenodo API token
**Publish tool:** manual submission (arXiv), `zenodo_upload` script (Zenodo)

TeX papers are not "published" in the package sense. The workflow is:

1. Tag: `papers/<name>/v<version>`
2. CI builds PDF from `.tex` sources
3. Upload PDF to arXiv (manual or API)
4. Deposit sources + PDF on Zenodo for a citable DOI
5. Update `CITATION.cff` with the DOI

**Workflow:** `.github/workflows/publish-papers.yml`

```yaml
name: Build and deposit papers

"on":
  push:
    tags:
      - "papers/*/v*"

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract paper name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#papers/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=papers/$name" >> "$GITHUB_OUTPUT"

      - uses: xu-cheng/latex-action@v3
        with:
          working_directory: ${{ steps.pkg.outputs.path }}
          root_file: main.tex

      - uses: actions/upload-artifact@v4
        with:
          name: paper-${{ steps.pkg.outputs.name }}
          path: ${{ steps.pkg.outputs.path }}/main.pdf

      # Zenodo deposit (creates DOI)
      - name: Deposit to Zenodo
        env:
          ZENODO_TOKEN: ${{ secrets.ZENODO_TOKEN }}
        run: |
          python tools/scripts/zenodo_deposit.py \
            --paper "${{ steps.pkg.outputs.path }}" \
            --tag "${{ github.ref_name }}"
```

### 4.8 CLI manifests → Scoop / Winget / Homebrew

CLI manifests are auto-generated when a CLI-bearing package (Python or
Node) is released. The workflow watches for `python/<cli-name>/v*` or
`node/<cli-name>/v*` tags, fetches the released artifact, and generates
manifests into `cli/scoop-bucket/`, `cli/winget-manifests/`, and
`cli/homebrew/`.

**Workflow:** `.github/workflows/publish-cli-manifests.yml`

```yaml
name: Generate CLI manifests

"on":
  push:
    tags:
      - "python/hummbl-cli/v*"
      - "python/hummbl-bus/v*"
      - "python/hummbl-governance/v*"
      - "python/base120/v*"

permissions:
  contents: write

jobs:
  manifests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract package name and version
        id: pkg
        run: |
          name="${GITHUB_REF_NAME%%/v*}"
          name="${name#*/}"
          version="${GITHUB_REF_NAME##*/v}"
          echo "name=$name version=$version" >> "$GITHUB_OUTPUT"

      - name: Generate Scoop manifest
        run: python tools/scripts/gen_scoop_manifest.py --package "${{ steps.pkg.outputs.name }}" --version "${{ steps.pkg.outputs.version }}"

      - name: Generate Winget manifest
        run: python tools/scripts/gen_winget_manifest.py --package "${{ steps.pkg.outputs.name }}" --version "${{ steps.pkg.outputs.version }}"

      - name: Generate Homebrew formula
        run: python tools/scripts/gen_homebrew_formula.py --package "${{ steps.pkg.outputs.name }}" --version "${{ steps.pkg.outputs.version }}"

      - name: Commit manifests
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add cli/
          git commit -m "chore: update CLI manifests for ${{ steps.pkg.outputs.name }} v${{ steps.pkg.outputs.version }}"
          git push
```

---

## 5. CI design

### Per-language CI (validation)

Each language has its own CI workflow triggered by path filters. This
keeps CI fast — a Python change doesn't run Rust tests.

| Workflow | Trigger paths | What it does |
|----------|---------------|--------------|
| `ci-python.yml` | `packages/python/**` | ruff lint, pytest, build smoke |
| `ci-node.yml` | `packages/node/**` | eslint/tsc, test, build smoke |
| `ci-rust.yml` | `packages/rust/**` | cargo fmt --check, clippy, test |
| `ci-go.yml` | `packages/go/**` | go vet, go test |
| `ci-jvm.yml` | `packages/jvm/**` | gradle check, test |

### Publish CI (release)

Each language has its own publish workflow triggered by tags. See
section 4 above.

### Shared checks

A lightweight `ci.yml` workflow runs on every PR for cross-cutting
concerns:

- License header presence
- `CHANGELOG.md` updated for changed packages
- No secrets in diff
- Branch protection: `ci` is the required status check (matches the
  existing hummbl-governance branch protection pattern)

---

## 6. Secrets management

| Secret | Used by | Scope |
|--------|---------|-------|
| `NPM_TOKEN` | publish-npm.yml | npm automation token (shared) |
| `CARGO_REGISTRY_TOKEN` | publish-crates.yml | crates.io API token |
| `SONATYPE_USERNAME` | publish-jvm.yml | Maven Central Portal |
| `SONATYPE_PASSWORD` | publish-jvm.yml | Maven Central Portal |
| `GPG_KEY_ID` | publish-jvm.yml | Artifact signing |
| `GPG_PRIVATE_KEY` | publish-jvm.yml | Artifact signing |
| `GPG_PASSWORD` | publish-jvm.yml | Artifact signing |
| `ZENODO_TOKEN` | publish-papers.yml | Zenodo deposit |
| `FLAKEHUB_TOKEN` | publish-nix.yml | FlakeHub push |

**PyPI uses no secrets** — Trusted Publishing (OIDC) authenticates via
the GitHub Actions identity. This is the preferred model; use it for
any registry that supports it.

Secrets are stored as GitHub repository secrets with environment
gating (`environment: pypi`, `environment: npm`, etc.) so a publish
job can only access the secrets for its registry.

---

## 7. Cross-package dependencies

Some HUMMBL packages depend on other HUMMBL packages. For example,
`hummbl-dashboard` may import `hummbl-governance`.

**During development:** editable installs from the monorepo.

```bash
pip install -e packages/python/hummbl-governance
pip install -e packages/python/hummbl-dashboard
```

**In published metadata:** normal registry dependencies. The
`pyproject.toml` for `hummbl-dashboard` declares
`dependencies = ["hummbl-governance>=1.4.0"]`. When published, pip
resolves it from PyPI.

**Version coordination:** when a dependency releases a breaking change,
dependents should be updated and re-released in the same session. The
monorepo makes this a single PR — change the dependency, update the
dependent's version constraint, tag both.

---

## 8. Migration plan

### Phase 0: Structure (this PR)

- [x] Create `docs/MONOREPO-DESIGN.md` (this file)
- [ ] Create `docs/PACKAGES.md` (full inventory from the survey)
- [ ] Move `packages/hummbl-governance/` → `packages/python/hummbl-governance/`
- [ ] Update `publish-pypi.yml` tag filter to `python/*/v*`
- [ ] Update `publish-pypi.yml` path extraction for `packages/python/` prefix
- [ ] Update README.md package table

### Phase 1: Migrate live PyPI packages (5)

Move source for the 5 live PyPI packages into the monorepo. Each
package is migrated in its own PR to keep diffs reviewable.

- [ ] `hummbl-bus` → `packages/python/hummbl-bus/`
- [ ] `hummbl-cognition` → `packages/python/hummbl-cognition/`
- [ ] `hummbl-tuples` → `packages/python/hummbl-tuples/` (+ `packages/rust/`, `packages/go/`, `packages/node/` for reference impls)
- [ ] `hummbl-bif` → `packages/python/hummbl-bif/`
- [ ] `base120` → `packages/python/base120/`

**For each:** configure trusted publisher on pypi.org, verify dry-run
build, then tag the next release from the monorepo.

### Phase 2: Migrate live npm packages (7)

- [ ] `mcp-server` → `packages/node/mcp-server/`
- [ ] `hermes-agent` → `packages/node/hermes-agent/`
- [ ] `hummbl-bibliography` → `packages/node/hummbl-bibliography/`
- [ ] `arbiter` → `packages/node/arbiter/`
- [ ] `arcana` → `packages/node/arcana/`
- [ ] `crab` → `packages/node/crab/`
- [ ] `randy` → `packages/node/randy/`

**For each:** set `NPM_TOKEN` secret, flip `private: true` → `false`,
verify build, tag release.

### Phase 3: Publish not-yet-live packages (~31 PyPI, ~10 npm)

These are repos with `pyproject.toml` or `package.json` that were never
published. Migration is: move source, add to monorepo, configure
publisher, tag first release.

Prioritize by user value:
1. **Governance ecosystem:** `hummbl-lattice`, `hummbl-eval`,
   `hummbl-clp`, `hummbl-contracts`, `hummbl-validation`
2. **Core libraries:** `hummbl-axis`, `hummbl-crucible`, `hummbl-intel`
3. **Utility:** `hummbl-lint-config`, `hummbl-dashboard`
4. **Domain-specific:** `peptide-check`, `whether-book`, `idp-spec`

### Phase 4: Publish new-language packages

- [ ] `demosmesh` → `packages/rust/demosmesh/` → crates.io
- [ ] `hummbl-tuples` Rust ref impl → `packages/rust/hummbl-tuples/` → crates.io
- [ ] `hummbl-tuples` Go ref impl → `packages/go/hummbl-tuples/` → Go proxy
- [ ] `hummbl-tuples` TS ref impl → `packages/node/hummbl-tuples/` → npm (needs `package.json`)
- [ ] `fabric-adapter` → `packages/jvm/fabric-adapter/` → Maven Central
- [ ] `v3sp3r` → `packages/jvm/v3sp3r/` → Maven Central
- [ ] `hermes-agent` nix flake → `packages/nix/hermes-agent/` → FlakeHub

### Phase 5: Papers, docs, sites, CLI manifests

- [ ] Migrate TeX papers to `papers/`
- [ ] Point Mintlify docs at monorepo
- [ ] Migrate static sites to `sites/`
- [ ] Generate Scoop/Winget/Homebrew manifests for CLI-bearing packages

### Phase 6: Archive legacy repos

After a package is fully migrated and publishing from the monorepo:
1. Update legacy repo README: "Moved to hummbl-io/oss — see
   packages/<lang>/<name>/"
2. Archive the legacy repo on GitHub
3. Do not delete — preserve issues and history

---

## 9. What stays in private repos

The monorepo is for **public-publishable** packages only. The following
stay in `hummbl-io/*` private repos:

- **Internal fleet infrastructure:** `apex-nexus`, `agents`, `fleet-manifests`,
  `fleet-runbooks`, `anvil-bin`, `delta-fleet`
- **Private governance/agent runtime:** `hummbl-production`, `hummbl-iac`,
  `hummbl-gitea-control-plane`, `hummbl-dashboard` (if it contains
  internal fleet URLs — review before publishing)
- **Personal/workflow:** `job-search-2026`, `meeting-archive`,
  `professional-history`, `reubenos`, `lsat-prep`, `jenna-collaboration-routing`
- **Research with sensitive data:** `hd-ai-education-internal`,
  `microsoft-locked-clients-research`
- **Secrets:** `vault`

The rule: if it contains internal hostnames, fleet URLs, personal data,
or secrets, it stays private. If it is a self-contained library that a
user could `pip install` / `npm install` / `cargo add` and use
independently, it goes in the monorepo.

---

## 10. License

All packages in this monorepo are **Apache-2.0**, matching the existing
HUMMBL OSS license. The root `LICENSE` file applies to all packages
unless a package directory contains its own `LICENSE` override (none
currently do).

TeX papers under `papers/` may use **CC BY 4.0** for the document text
while keeping code under Apache-2.0 — this is specified per-paper in
the paper's `LICENSE` file.

---

## 11. Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-21 | Language-namespaced `packages/<lang>/<name>/` | Avoids build-tool conflicts, clean CI path filters, explicit registry mapping |
| 2026-08-21 | Tag format `<lang>/<name>/v<version>` | Encodes language + package + version in one string; unambiguous for CI |
| 2026-08-21 | Independent per-package versioning | Packages are independently useful libraries, not a unified platform |
| 2026-08-21 | PyPI Trusted Publishing (OIDC) | No API tokens to rotate; GitHub-native auth |
| 2026-08-21 | Per-language CI workflows | Fast CI — Python change doesn't run Rust tests |
| 2026-08-21 | Apache-2.0 for all packages | Consistent with existing HUMMBL OSS license |
