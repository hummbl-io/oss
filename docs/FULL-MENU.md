# The Full Menu

**Origin:** "Full Menu" notates the comprehensive spread — not minimal, not
a la carte, but the complete offering. This document applies that principle
to HUMMBL's open-source publishing: not the minimum viable package, but the
complete spread of everything the world deserves to install.

**Status:** Active
**Date:** 2026-08-22
**Authors:** Operator, HUMMBL fleet

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

Candidates that are not yet both CAN and SHOULD are tracked privately, not
staged into this public document ahead of release. This keeps the public
menu limited to what a consumer can actually act on today.

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

Everything beyond these — packages still pending migration or review — is
tracked in an internal runbook and enters this document only as each is
actually prepared, audited, and tagged for release.

---

## The Full Menu — Other registries

### npm (JavaScript/TypeScript)

All previously-published HUMMBL npm packages were deprecated 2026-08-21.
The `@hummbl` scope is clean. Future npm packages publish fresh under
`@hummbl/*` from this monorepo as each is prepared for release.

### crates.io (Rust), Go module proxy, arXiv / Zenodo (papers)

No packages published yet in these registries. Candidates are tracked
privately and will be added here as each clears the CAN + SHOULD gate and
is actually prepared for release.

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

- [PACKAGES.md](./PACKAGES.md) — published-package detail and registry collision warnings
- [MONOREPO-DESIGN.md](./MONOREPO-DESIGN.md) — the directory structure and migration plan
- [RELEASE.md](../RELEASE.md) — the release discipline (trusted publishing, no manual uploads)
