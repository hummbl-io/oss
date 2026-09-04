# The Full Menu

**Origin:** "Full Menu" notates the comprehensive spread — not minimal, not
a la carte, but the complete offering. This document is the *gate*, not the
inventory.

**Status:** Active as a release-discipline note.
**As of:** 2026-09-02.
**Canonical inventory:** [`PACKAGES.md`](./PACKAGES.md) and the root
[`README.md`](../README.md). Do not keep a second live-package table here.

---

## Public sentence

Same sentence as [hummbl.io](https://hummbl.io) and the root README:

> HUMMBL is open-source governance infrastructure for agentic AI: scoped
> delegation, kill switches, circuit breakers, and verifiable receipts that
> run inside your Python environment.

The Full Menu is how those packages reach a registry. It is not a second
definition of the product.

---

## What is the Full Menu?

The Full Menu is the public publishing gate for `hummbl-io/oss`.
A package appears as installable to the world only when it is **both CAN
and SHOULD** and has a trusted-publishing tag under `RELEASE.md`.

There is no `packages/node/`, `packages/rust/`, or `packages/go/` tree in
this repository. Do not tell readers they can `npm install`, `cargo add`,
or `go get` HUMMBL packages from this monorepo today.

| Section | Meaning | Decision gate |
|---------|---------|---------------|
| **CAN** | Technically publishable — has a manifest, tests, no blocking technical issues | Mechanical: does it build, test, and install? |
| **SHOULD** | Strategically aligned — stable enough, public-facing, adds value to the ecosystem, not private/internal | Judgment: does the world benefit from this being public? |
| **SHOULD NOT (yet)** | Not ready for public release — private data, internal infrastructure, needs review, or not stable enough | Temporary: can graduate to SHOULD when the blocker is resolved |

CAN is about capability. SHOULD is about judgment. A package can be CAN
without being SHOULD (technically publishable but strategically premature),
and SHOULD without being CAN (strategically ready but technically blocked).

What is actually Live vs in-tree is listed in `PACKAGES.md`. Candidates that
are not yet both CAN and SHOULD stay private and are not staged into this
public document ahead of release.

Canonical landing-page install names:

```text
pip install base120
pip install hummbl-governance
```

Do not document `pip install arbiter`, `agent-governance`, or `base120-mcp`.

---

## Other registries

### npm (JavaScript/TypeScript)

All previously-published HUMMBL npm packages were deprecated 2026-08-21.
The `@hummbl` scope exists. Future npm packages publish under `@hummbl/*`
from this monorepo **after** a `packages/node/` tree exists.

### crates.io, Go module proxy, arXiv / Zenodo

No packages published from this monorepo in those registries. Candidates
stay private until they clear CAN + SHOULD and have a tree here.

---

## Release readiness criteria

Every package must pass this checklist before its first trusted-publishing
tag from this repo:

- [ ] `pyproject.toml` with: name, version, description, authors, license, keywords, classifiers, project.urls
- [ ] `LICENSE` file matching the package SPDX in `pyproject.toml`
- [ ] `README.md` with install instructions (`pip install <name>` only if the name is HUMMBL-owned)
- [ ] `CHANGELOG.md` with at least one released version section
- [ ] Tests pass (`pytest -q`)
- [ ] No secrets, internal fleet URLs, or personal data in the source
- [ ] Source under `packages/python/<name>/`
- [ ] Trusted publisher configured on pypi.org (owner: hummbl-io, repo: oss, workflow: publish-pypi.yml, environment: pypi)
- [ ] Tag pattern `python/<package>/v*` in `.github/workflows/publish-pypi.yml`
- [ ] Root README, `AGENTS.md`, and `docs/PACKAGES.md` updated in the same PR

---

## See also

- [PACKAGES.md](./PACKAGES.md) — live vs in-tree inventory and registry collisions
- [MONOREPO-DESIGN.md](./MONOREPO-DESIGN.md) — directory structure and migration plan
- [RELEASE.md](../RELEASE.md) — trusted publishing, tag contract, no manual uploads
- Issue `#79` — remaining identity work outside this repo (PyPI org blurb, `arbiter-dev`)
