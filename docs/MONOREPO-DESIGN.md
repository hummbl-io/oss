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
│   │   ├── <private-repo>/
│   │   ├── <private-repo>/
│   │   ├── <private-repo>/
│   │   ├── <private-repo>/
│   │   ├── <private-repo>/
│   │   ├── governed-compression/
│   │   └── …
│   ├── node/                # npm
│   │   ├── <private-repo>/
│   │   ├── <private-repo>/
│   │   ├── mcp-server/      # publishes as @hummbl/mcp-server
│   │   ├── <private-repo>/   # TS reference impl
│   │   └── …
│   ├── rust/                # crates.io
│   │   ├── <private-repo>/
│   │   └── <private-repo>/   # Rust reference impl
│   ├── go/                  # Go module proxy
│   │   └── <private-repo>/   # Go reference impl
│   ├── jvm/                 # Maven Central
│   │   ├── fabric-adapter/
│   │   └── v3sp3r/
│   └── nix/                 # Nix flake registry
│       └── hermes-agent/
├── papers/                  # arXiv / Zenodo (TeX)
│   ├── <private-repo>/
│   ├── <private-repo>/
│   └── krineia/
├── site/                    # Mintlify docs site (separate from design docs)
├── sites/                   # GitHub Pages (static)
│   ├── hummbl-io/
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
│       └── publish-jvm.yml
├── README.md
├── LICENSE                  # Apache-2.0
└── docs/                    # design docs (this file + PACKAGES.md)
    ├── MONOREPO-DESIGN.md   # this file
    └── PACKAGES.md          # full inventory
```

Note: Go has no `publish-go.yml` workflow — tag push IS the publish for Go
modules (the Go module proxy fetches from the repo on demand). See section
4.4.

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

3. **Polyglot packages are explicit.** `<private-repo>` has 4 language
   implementations. Under the flat scheme they'd collide on directory
   name. Under language namespacing they are siblings:
   `packages/python/<private-repo>/`, `packages/rust/<private-repo>/`,
   `packages/go/<private-repo>/`, `packages/node/<private-repo>/`.

4. **Registry mapping is obvious.** The directory name tells you which
   registry the package publishes to. No lookup table needed.

### Migration from current `packages/<name>/`

The current `packages/hummbl-governance/` moves to
`packages/python/hummbl-governance/`. The `publish-pypi.yml` workflow tag
filter and path extraction are updated in the same PR.

**Migration method depends on the source repo's visibility:**

- **From a private repo:** use a **clean snapshot (no history)** with a
  PII scan before copy. Private repos may contain hostnames, internal
  paths, credentials, or personal data in their git history that must not
  enter a public monorepo. `hummbl-governance` was migrated this way —
  clean snapshot, PII-scanned, no history carried over.
- **From a public repo:** a `git mv` preserving history is safe, since
  the history is already public.

Never `git mv` from a private repo into this public monorepo without
scanning the full history for PII first.

---

## 2. Tag conventions

Every release is a git tag. The tag encodes the language, package name,
and version:

```
<lang>/<package-name>/v<version>
```

**Exception — Go:** The Go module proxy requires the tag prefix to match
the module path. Go modules at `packages/go/<name>/` with module path
`github.com/hummbl-io/oss/packages/go/<name>` must be tagged
`packages/go/<name>/v<version>` (not `go/<name>/v<version>`). This is the
only language where the tag includes the `packages/` prefix.

Examples:

| Tag | Registry | Package | Version |
|-----|----------|---------|---------|
| `python/hummbl-governance/v1.4.1` | PyPI | hummbl-governance | 1.4.1 |
| `python/<private-repo>/v0.2.0` | PyPI | <private-repo> | 0.2.0 |
| `node/<private-repo>/v0.1.0` | npm | <private-repo> | 0.1.0 |
| `rust/<private-repo>/v0.1.0` | crates.io | <private-repo> | 0.1.0 |
| `packages/go/<private-repo>/v0.1.0` | Go proxy | github.com/hummbl-io/oss/packages/go/<private-repo> | 0.1.0 |
| `jvm/fabric-adapter/v0.1.0` | Maven Central | fabric-adapter | 0.1.0 |

### Polyglot package releases

A polyglot package like `<private-repo>` has independent versions per
language. Each language variant is tagged and released separately:

```
python/<private-repo>/v0.2.1              # PyPI
rust/<private-repo>/v0.1.0                # crates.io
packages/go/<private-repo>/v0.1.0         # Go proxy (tag prefix must match module path)
node/<private-repo>/v0.1.0                # npm
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
node/<private-repo>/v0.2.0-beta.1       # npm pre-release
rust/<private-repo>/v0.1.0-pre.1           # crates pre-release
```

---

## 3. Versioning

**Independent per package.** Each package has its own version number and
its own changelog. There is no monorepo-wide "v1.2.3" release.

Rationale: the packages are independently useful libraries. A governance
fix should not force a version bump on `<private-repo>` or `<private-repo>`. Users
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

### 4.0 Workflow authoring rules (apply to every workflow in this repo)

These rules are mandatory on `hummbl-io/oss`. They were learned from
debugging 4 consecutive `startup_failure` runs during the
`hummbl-governance` 1.4.1 publish. Ignore them and the workflow fails
before any job starts — with no logs.

1. **SHA-pin every action.** The repo has `sha_pinning_required: true`
   (verify: `gh api repos/hummbl-io/oss/actions/permissions`). Tag refs
   (`@v4`, `@v5`, `@stable`, `@main`) cause `startup_failure`. Always
   pin to the full 40-char commit SHA:
   `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`. Resolve
   a tag to its SHA with
   `gh api repos/<owner>/<repo>/commits/<tag> --jq '.sha'`.

2. **ASCII only.** No em-dashes, smart quotes, or non-ASCII characters
   anywhere in `.github/workflows/*.yml` — including comments. Use `--`
   and straight quotes. A single em-dash (`—`, U+2014) in a comment
   caused a `startup_failure` on this repo.

3. **LF line endings.** CRLF causes `startup_failure`. Add a
   `.gitattributes` with `.github/workflows/*.yml text eol=lf` to enforce
   this regardless of contributor OS.

4. **Create environments before referencing them.** GitHub Actions fails
   at startup if a job references an environment that doesn't exist.
   Create each environment first:
   `gh api repos/hummbl-io/oss/environments/<name> -X PUT`. The
   `pypi` environment already exists (created 2026-08-21).

5. **Quote the `on:` key.** YAML 1.1 treats `on` as a boolean. Write
   `"on":` (quoted) to avoid parse ambiguity.

The workflow examples in sections 4.1-4.8 below show SHA-pinned actions
matching these rules. When updating an action, resolve the new tag to its
SHA and replace the pin. These rules are also documented in
[`CONTRIBUTING.md`](../CONTRIBUTING.md) section 1 for contributor visibility.

### 4.1 Python → PyPI

**Registry:** [pypi.org](https://pypi.org)
**Auth:** Trusted Publishing (OIDC) — no API tokens
**Build tool:** `python -m build` (PEP 517)
**Publish tool:** `twine upload`

> **Reusable-workflow constraint:** `pypa/gh-action-pypi-publish` (and the
> `twine upload` + `id-token: write` pattern it wraps) **cannot be used from
> within a reusable workflow** (`on: workflow_call`). The OIDC token's
> `repository_owner`/`repository_name` claims filter to the *calling* repo,
> so the publish step must run in a non-reusable workflow file in
> `hummbl-io/oss`. If a future refactor consolidates publish logic into a
> shared reusable workflow, the PyPI publish step must remain in a wrapper
> job in the calling workflow, not inside the reusable workflow itself.
> (Source: [pypa/gh-action-pypi-publish README](https://github.com/pypa/gh-action-pypi-publish))

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
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract package name from tag
        id: pkg
        run: |
          # tag format: python/<package-name>/v<version>
          name="${GITHUB_REF_NAME#python/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/python/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
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
3. Environment: `pypi` (already created on this repo)
4. Repository: `hummbl-io/oss`
5. Tag pattern: `python/<package-name>/v*`

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
**Auth:** Trusted Publishing (OIDC) — GA July 2025; no `NPM_TOKEN` secret needed
**Build tool:** package-specific (tsc, bun, vite, etc.)
**Publish tool:** `npm publish --provenance`

> **Trusted Publishing (preferred):** npm reached OIDC Trusted Publishing GA
> in July 2025, matching PyPI's model. Requires npm CLI ≥11.5.1 and Node
> ≥22.14.0. The `package.json` `repository` field must match the GitHub
> OIDC claims exactly (Sigstore verifies this); in a monorepo, each
> `package.json` must declare `repository` with the correct `directory`
> subpath or publishing fails with `422 Unprocessable Entity`. The legacy
> `NPM_TOKEN` secret approach below is kept as a fallback for packages not
> yet migrated.

**Workflow (Trusted Publishing):** `.github/workflows/publish-npm.yml`

```yaml
name: Publish to npm

"on":
  push:
    tags:
      - "node/*/v*"

permissions:
  contents: read
  id-token: write  # OIDC trusted publishing

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#node/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/node/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020
        with:
          node-version: "22.14.0"
          registry-url: "https://registry.npmjs.org"

      - name: Install
        working-directory: ${{ steps.pkg.outputs.path }}
        run: npm ci

      - name: Build
        working-directory: ${{ steps.pkg.outputs.path }}
        run: npm run build --if-present

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        run: npm publish --provenance --access public
```

**Per-package setup (Trusted Publishing):**
1. Set `package.json` `"private": false` (remove `"private": true`)
2. Ensure `"name"`, `"version"`, `"license"`, `"repository"` fields are set.
   `repository` must point to `github.com/hummbl-io/oss` with the correct
   `directory` subpath (e.g. `packages/node/<private-repo>`) — Sigstore
   verifies this matches the OIDC claims.
3. On npmjs.com → package settings → Trusted Publishing → add the GitHub
   repo + workflow file + environment
4. Create the `npm` environment: `gh api repos/hummbl-io/oss/environments/npm -X PUT`
5. Tag and push: `git tag node/<private-repo>/v0.1.0 && git push origin node/<private-repo>/v0.1.0`

**Package naming -- DECIDED: scoped `@hummbl/*`**
- **Scoped:** `@hummbl/<name>` (e.g. `@hummbl/governance`). Avoids
  name squatters, is npm best practice for orgs, but diverges from the PyPI
  spelling (`hummbl-governance`).
- ~~Unscoped: `hummbl-<name>` (matches PyPI exactly).~~ Rejected -- exposes
  the package to name collisions on npm.

Operator confirmed scoped `@hummbl/*` on 2026-08-21. This decision is
irreversible after first publish. All npm packages in this monorepo use
the `@hummbl/` scope. The cross-registry spelling divergence (PyPI
`hummbl-governance` vs npm `@hummbl/governance`) is accepted as the cost
of namespace safety on npm.

### 4.3 Rust → crates.io

**Registry:** [crates.io](https://crates.io)
**Auth:** Trusted Publishing (OIDC) — GA July 2025; no `CARGO_REGISTRY_TOKEN` secret needed (after first publish)
**Build tool:** `cargo build`
**Publish tool:** `cargo publish` (via `rust-lang/crates-io-auth-action`)

> **Trusted Publishing (preferred):** crates.io reached OIDC Trusted Publishing
> GA in July 2025 (RFC #3691). Uses `rust-lang/crates-io-auth-action@v1` to
> exchange a GitHub OIDC token for a short-lived API token. **First publish
> of each crate must still be manual** (crates.io requires initial
> owner-confirmed publish); subsequent publishes can use Trusted Publishing.
> The legacy `CARGO_REGISTRY_TOKEN` approach is kept as a fallback for the
> first publish or for packages not yet migrated.

**Workflow (Trusted Publishing):** `.github/workflows/publish-crates.yml`

```yaml
name: Publish to crates.io

"on":
  push:
    tags:
      - "rust/*/v*"

permissions:
  contents: read
  id-token: write  # OIDC trusted publishing

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: crates
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#rust/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/rust/$name" >> "$GITHUB_OUTPUT"

      - uses: dtolnay/rust-toolchain@4360b52568e2003a75bf9bc1d59f33a8e3fc893c

      - uses: rust-lang/crates-io-auth-action@v1
        id: auth

      - name: Publish
        working-directory: ${{ steps.pkg.outputs.path }}
        env:
          CARGO_REGISTRY_TOKEN: ${{ steps.auth.outputs.token }}
        run: cargo publish --token "$CARGO_REGISTRY_TOKEN"
```

**Per-package setup (Trusted Publishing):**
1. Ensure `Cargo.toml` has `[package] name`, `version`, `description`, `license`, `repository`
2. **First publish must be manual** (`cargo login` + `cargo publish` locally)
3. On crates.io → package settings → Trusted Publishing → add the GitHub
   repo + workflow file + environment
4. Create the `crates` environment: `gh api repos/hummbl-io/oss/environments/crates -X PUT`
5. Tag and push: `git tag rust/<private-repo>/v0.1.0 && git push origin rust/<private-repo>/v0.1.0`

> **Workspace ordering:** When publishing multiple crates from a Cargo
> workspace, crates.io requires dependencies to be available before
> dependent crates. Publish in topological order with a `sleep 30-120`
> between publishes to wait for index propagation. There is no
> `cargo publish --workspace` that handles this automatically.

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
git tag packages/go/<private-repo>/v0.1.0
git push origin packages/go/<private-repo>/v0.1.0
# Go proxy fetches within minutes — no CI needed
# Tag prefix MUST match the module path (packages/go/<name>) for the
# Go module proxy to resolve the version. See section 2.
```

> **proxy.golang.org slash-tag bug:** The public Go proxy has a known issue
> (golang/go#73143) where tags containing slashes — which our
> `packages/go/<name>/v*` format requires — can return
> `invalid: disallowed version string` from `proxy.golang.org` even though
> the tag format is spec-correct. If `go get` fails to resolve a HUMMBL
> Go module, set `GONOSUMDB=github.com/hummbl-io/oss` and
> `GONOSUMPROXY=github.com/hummbl-io/oss` in the consuming environment, or
> fetch directly from VCS with `GOFLAGS=-mod=mod GOPROXY=direct`. This is a
> proxy-side bug, not a problem with the tag format. Track golang/go#73143
> for resolution.

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
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
      - uses: actions/setup-go@40f1582b2485089dde7abd97c1529aa768e1baff
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
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#jvm/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/jvm/$name" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3
        with:
          java-version: "21"
          distribution: "temurin"

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@ed408507eac070d1f99cc633dbcf757c94c7933a

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
4. Create the `maven` environment: `gh api repos/hummbl-io/oss/environments/maven -X PUT`
5. Tag and push: `git tag jvm/fabric-adapter/v0.1.0 && git push origin jvm/fabric-adapter/v0.1.0`

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
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract package name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#nix/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=packages/nix/$name" >> "$GITHUB_OUTPUT"

      - uses: DeterminateSystems/nix-installer-action@ef8a148080ab6020fd15196c2084a2eea5ff2d25  # v22

      - uses: DeterminateSystems/flakehub-push@71f57208810a5d299fc6545350981de98fdbc860  # v6
        env:
          FLAKEHUB_TOKEN: ${{ secrets.FLAKEHUB_TOKEN }}
        with:
          visibility: public
          name: hummbl-io/${{ steps.pkg.outputs.name }}
          directory: ${{ steps.pkg.outputs.path }}
          tag: ${{ github.ref_name }}
```

### 4.7 TeX → arXiv / Zenodo

**Registry:** [arxiv.org](https://arxiv.org) (preprints), [Zenodo](https://zenodo.org) (DOI deposits)
**Auth:** Zenodo API token (arXiv has **no submission API** — see note below)
**Publish tool:** `zenodo_deposit.py` (Zenodo, automated); **manual web upload** (arXiv, no API exists)

TeX papers are not "published" in the package sense. The workflow is:

1. Tag: `papers/<name>/v<version>`
2. CI builds PDF from `.tex` sources
3. CI attaches PDF + LaTeX source bundle to the GitHub Release (for the human to download)
4. **Human manually uploads** the PDF to arXiv via the web form (arXiv has no submission API, no OAuth, no webhook — this step cannot be automated)
5. CI deposits sources + PDF on Zenodo for a citable DOI (automated)
6. Human updates `CITATION.cff` with the arXiv ID and Zenodo DOI

> **arXiv automation gap:** arXiv is categorically different from every other registry in this document. There is no end-to-end automated path from git tag to arXiv submission ID, regardless of CI sophistication. The workflow prepares the bundle; a human must complete the submission. Do not attempt to automate this — it will fail.

**Workflow:** `.github/workflows/publish-papers.yml`

```yaml
name: Build and deposit papers

"on":
  push:
    tags:
      - "papers/*/v*"

permissions:
  contents: write  # needed to attach bundle to the GitHub Release

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

      - name: Extract paper name from tag
        id: pkg
        run: |
          name="${GITHUB_REF_NAME#papers/}"
          name="${name%/v*}"
          echo "name=$name" >> "$GITHUB_OUTPUT"
          echo "path=papers/$name" >> "$GITHUB_OUTPUT"

      - uses: xu-cheng/latex-action@e2f99d4b3685b0da93f97e1b86ad8fab81105098
        with:
          working_directory: ${{ steps.pkg.outputs.path }}
          root_file: main.tex

      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: paper-${{ steps.pkg.outputs.name }}
          path: ${{ steps.pkg.outputs.path }}/main.pdf

      # Attach PDF + source bundle to the GitHub Release for manual arXiv upload.
      # arXiv has no submission API — a human must download this bundle and
      # upload it via the arXiv web form.
      - name: Attach bundle to GitHub Release
        uses: softprops/action-gh-release@da05d552573ad5aba9dff4d2c33b7e2a8d9651b8
        with:
          files: |
            ${{ steps.pkg.outputs.path }}/main.pdf
            ${{ steps.pkg.outputs.path }}/*.tex

      # Zenodo deposit (creates DOI) — automated
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
      - "python/<private-repo>/v*"
      - "python/<private-repo>/v*"
      - "python/hummbl-governance/v*"
      - "python/<private-repo>/v*"

permissions:
  contents: write

jobs:
  manifests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262

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
          git checkout -B main
          git add cli/
          git commit -m "chore: update CLI manifests for ${{ steps.pkg.outputs.name }} v${{ steps.pkg.outputs.version }}"
          git push origin main
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

Three registries now support OIDC Trusted Publishing and require **no
long-lived secrets**: PyPI (GA April 2023), npm (GA July 2025), and
crates.io (GA July 2025). The remaining registries (Maven Central, Zenodo,
FlakeHub) each require a registry token or credential set; see the
per-language workflow in section 4 for the specific secret references.

**Registries using Trusted Publishing (no secrets):** PyPI, npm, crates.io.
**Registries requiring secrets:** Maven Central (GPG + Sonatype Portal
token), Zenodo (API token), FlakeHub (JWT). Go module proxy uses no auth
(tag push is the publish).

**Trusted Publishing is the preferred model** — use it for any registry
that supports it. It eliminates long-lived tokens, narrows the credential-
theft attack surface, and (for npm and PyPI) generates provenance
attestations automatically.

Secrets are stored as GitHub repository secrets with environment
gating (`environment: pypi`, `environment: npm`, etc.) so a publish
job can only access the secrets for its registry.

---

## 7. Cross-package dependencies

Some HUMMBL packages depend on other HUMMBL packages. For example,
`<private-repo>` may import `hummbl-governance`.

**During development:** editable installs from the monorepo.

```bash
pip install -e packages/python/hummbl-governance
pip install -e packages/python/<private-repo>
```

**In published metadata:** normal registry dependencies. The
`pyproject.toml` for `<private-repo>` declares
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

### Phase 1: Migrate live PyPI packages (7 remaining)

Move source for the live HUMMBL-owned PyPI packages into the monorepo.
`hummbl-governance` is already migrated (this session, commit 7df31bc).
Each remaining package is migrated in its own PR to keep diffs reviewable.

- [x] `hummbl-governance` → `packages/python/hummbl-governance/` (DONE — 1.4.1 published via trusted publishing)
- [ ] `<private-repo>` → `packages/python/<private-repo>/`
- [ ] `<private-repo>` → `packages/python/<private-repo>/`
- [ ] `<private-repo>` → `packages/python/<private-repo>/` (+ `packages/rust/`, `packages/go/`, `packages/node/` for reference impls)
- [ ] `<private-repo>` → `packages/python/<private-repo>/`
- [ ] `<private-repo>` → `packages/python/<private-repo>/`
- [ ] `governed-compression` → `packages/python/governed-compression/` (ML: governed vector + KV-cache compression; runtime dep on `hummbl-governance>=1.1.0` — cross-package dependency, see section 7)

**Excluded from Phase 1 (not HUMMBL's):** `<private-repo>`, `arcana`, `<private-repo>`, `<private-repo>`, `hermes-agent` are name collisions on PyPI by other authors (see PACKAGES.md). `OBLITERATUS` belongs to Pliny (pliny-lab), not HUMMBL.

**For each:** configure trusted publisher on pypi.org, verify dry-run
build, then tag the next release from the monorepo. Use clean-snapshot
migration (no history) from private repos — see section 1.

### Phase 2: Publish npm packages (clean slate, 0 live)

All previously-published HUMMBL npm packages were deprecated by the
operator on 2026-08-21. The `@hummbl` scope is retained (operator owns
it under the `hummbl-io` npm account). Phase 2 is a clean greenfield:
publish fresh under `@hummbl/*` from this monorepo.

- [ ] `@hummbl/mcp-server` → `packages/node/mcp-server/` (re-publish fresh under scope; old `@hummbl/mcp-server` v1.2.0 is deprecated)
- [ ] `@hummbl/bibliography` → `packages/node/<private-repo>/` (re-publish scoped; old unscoped `<private-repo>` v1.0.0 is deprecated)
- [ ] Other npm candidates from PACKAGES.md "Publishable but not yet on npm" section

**Excluded from Phase 2 (name collisions, never HUMMBL's):** `hermes-agent`, `<private-repo>`, `arcana`, `<private-repo>`, `<private-repo>`, `mcp-server` (unscoped) are unrelated packages by other authors on npm (see PACKAGES.md).

**For each:** configure Trusted Publishing on npmjs.com (or set `NPM_TOKEN` secret as fallback for packages not yet migrated), create `npm` environment, flip `private: true` → `false`, set `"name"` to `@hummbl/<name>`, verify build, tag release.

### Phase 3: Publish not-yet-live packages (~31 PyPI, ~10 npm)

These are repos with `pyproject.toml` or `package.json` that were never
published. Migration is: move source, add to monorepo, configure
publisher, tag first release.

Prioritize by user value:
1. **Governance ecosystem:** `hummbl-lattice`, `hummbl-eval`,
   `<private-repo>`, `<private-repo>`, `hummbl-validation`
2. **Core libraries:** `<private-repo>`, `<private-repo>`, `<private-repo>`
3. **Utility:** `<private-repo>`, `<private-repo>`
4. **Domain-specific:** `peptide-check`, `<private-repo>`, `<private-repo>`

### Phase 4: Publish new-language packages

- [ ] `<private-repo>` → `packages/rust/<private-repo>/` → crates.io
- [ ] `<private-repo>` Rust ref impl → `packages/rust/<private-repo>/` → crates.io
- [ ] `<private-repo>` Go ref impl → `packages/go/<private-repo>/` → Go proxy
- [ ] `<private-repo>` TS ref impl → `packages/node/<private-repo>/` → npm (needs `package.json`)
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

The monorepo is for **public-publishable** packages only. Repos that are
not candidates for public publishing — personal data, internal fleet
infrastructure, secrets, host-specific configs, and private governance/agent
runtimes — stay in `hummbl-io/*` private repos and are tracked in an internal
runbook. They are not enumerated in this public document to avoid publishing
a categorized inventory of non-public infrastructure.

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
| 2026-08-21 | Per-language CI workflows | Fast CI -- Python change doesn't run Rust tests |
| 2026-08-21 | Apache-2.0 for all packages | Consistent with existing HUMMBL OSS license |
| 2026-08-21 | SHA-pin all workflow actions | Repo has `sha_pinning_required: true`; tag refs cause `startup_failure`. Learned from 4 failed runs during 1.4.1 publish |
| 2026-08-21 | ASCII-only + LF for workflow YAML | Em-dash + CRLF caused `startup_failure` on this repo |
| 2026-08-21 | Clean snapshot (no history) for private-repo migrations | Private repo history may contain PII (hostnames, paths, credentials); `git mv` would carry it into the public monorepo |
| 2026-08-21 | Create GitHub environments before workflow reference | Jobs referencing a nonexistent environment fail at startup with no logs |
| 2026-08-21 | npm package naming: scoped `@hummbl/*` (operator-confirmed) | Irreversible after first publish; scoped avoids name squatters. Cross-registry spelling divergence (PyPI `hummbl-governance` vs npm `@hummbl/governance`) accepted as cost of namespace safety |
| 2026-08-21 | Adopt Trusted Publishing for npm + crates.io (GA July 2025) | Eliminates `NPM_TOKEN` and `CARGO_REGISTRY_TOKEN` secrets; matches PyPI model; provenance attestations generated automatically for npm. crates.io first publish still manual. |
| 2026-08-21 | arXiv submission stays manual (no API) | arXiv has no submission API, OAuth, or webhook. CI prepares bundle + attaches to GitHub Release; human uploads via web form. Documented to prevent future automation attempts that will fail. |
| 2026-08-21 | PyPI publish step must NOT live in a reusable workflow | `pypa/gh-action-pypi-publish` + OIDC cannot run inside `on: workflow_call`; the publish step must be in a non-reusable wrapper job in the calling workflow. |
| 2026-08-21 | Document Go proxy slash-tag bug (golang/go#73143) | `proxy.golang.org` may reject spec-correct `packages/go/<name>/v*` tags with `invalid: disallowed version string`. Workaround: `GONOSUMDB`/`GONOSUMPROXY` or `GOPROXY=direct`. Tag format unchanged (spec-correct). |
