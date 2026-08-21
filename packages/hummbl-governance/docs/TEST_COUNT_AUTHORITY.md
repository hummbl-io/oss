# Package Test-Count Authority Model

Status: draft authority model for issue #166.
Last verified: 2026-08-16.

## Purpose

`hummbl-governance` has several public and internal surfaces that mention
primitive counts, package-level test counts, and wider HUMMBL platform test
totals. Those numbers must not be reused across scopes without a named
authority source.

This document defines which source controls each metric and how README, PyPI,
site, security, and health surfaces should describe the values.

## Metric Authorities

| Metric | Canonical authority | Verification command or source | Current observed value |
|---|---|---|---|
| Package version | `pyproject.toml` `[project].version` | inspect `pyproject.toml` | `1.3.0` |
| Implemented package primitives | `PRIMITIVES.md` implemented inventory | count "Existing primitives" plus "Implemented expansion primitives"; exclude proposed/candidate primitives | `34` implemented primitives |
| Core historical primitives | `PRIMITIVES.md` "Existing primitives (P1-P26)" | use only when explicitly describing core or historical scope | `26` existing primitives |
| Package-level dedicated test collection | `pytest` collection on the release candidate working tree | `python -m pytest --collect-only -q tests` | `2314 tests collected` on 2026-08-17 from the tree based on commit `bc56261` |
| Built package long description | built wheel/sdist metadata | build the release artifact and inspect `dist/*` metadata before publish | release-gated, not editable after upload |
| Published PyPI rendered description | PyPI project/version page | public PyPI JSON/page for the uploaded artifact | `1.2.2` renders `34` implementation primitives and `2027` collected tests |
| Wider HUMMBL or hummbl-governance platform tests | owning platform repository and release-state manifest | verify in that repository, not this package | do not reuse as package count |

## Scope Rules

1. Public current-package claims must say "implemented package primitives" when
   using the 34-primitives number.
2. The 26-primitives number is valid only for "core primitives", older release
   artifacts, or an explicitly historical PyPI-rendered description.
3. Package test-count claims must come from pytest collection on the commit
   being described. Do not preserve a hard-coded count after test files change.
4. Aggregate platform totals, hummbl-governance totals, and internal validation
   totals must not be described as package-level dedicated tests.
5. PyPI text for an already uploaded version is evidence of what users see, not
   a mutable repo surface. Correcting stale PyPI text requires a new approved
   release path if the uploaded artifact contains stale metadata.

## Surface Mapping

| Surface | Allowed metric scope | Required wording posture |
|---|---|---|
| `README.md` | current package version, implemented package primitives, package-level pytest collection | Use current package wording and include the verification command when practical. |
| PyPI long description | built artifact metadata for the uploaded version | Must match the built README/long description at publish time; stale published text is fixed by release, not in-place edit. |
| `SECURITY.md` | supported versions and security scope | If it uses `26`, label that as core primitives. If it describes current package scope, use implemented primitive authority. |
| `docs/REPO_HEALTH.md` | repo lifecycle, current package version, validation entrypoint | Version must follow `pyproject.toml`; validation claims should point to commands, not stale counts. |
| Public site/readiness pages | public release-state manifest plus linked package evidence | Separate PyPI-rendered release metrics from source-README metrics. |
| Issue and PR comments | evidence for a point in time | Include date, command/source, commit or URL, and residual risk. |

## Wording Templates

### README

```markdown
`hummbl-governance` provides 34 implemented governance primitives in the
current package inventory. Test claims are package-level pytest collection
claims from the release candidate commit; verify with:

`python -m pytest --collect-only -q tests`
```

### PyPI / Built Long Description

```markdown
This release description was generated from the release-candidate README and
verified against the built wheel/sdist before upload. Primitive and test counts
are package-level claims, not wider HUMMBL platform totals.
```

### Cross-Site Reference

```markdown
Package metrics and platform metrics are separate. `hummbl-governance` package
metrics are governed by the package repository and release artifact; wider
platform validation totals are governed by their owning repository or public
release-state manifest.
```

## Minimal Drift-Prevention Check

Add a release-time check, not a broad runtime dependency:

1. Run `python -m pytest --collect-only -q tests` and capture the collected test
   count for the release candidate.
2. Build wheel and sdist.
3. Inspect the built long description and `hummbl_governance/governance.yml`.
4. Fail the release gate if README, built metadata, `SECURITY.md`,
   `docs/REPO_HEALTH.md`, or the package governance metadata use conflicting
   current-package counts without a scope label.

This check belongs in the release gate for issue #155 after this authority
model is reviewed.

## Verification Receipt

Commands and sources used for this draft:

```text
git rev-parse HEAD
# d320a56

git status --short --branch
# main

python -m pytest --collect-only -q tests
# 2314 tests collected in 0.68s

PyPI JSON for hummbl-governance 1.3.0
# description contains 34 governance primitives and 2314 tests

PRIMITIVES.md
# 26 existing primitives plus 8 implemented expansion primitives
```
