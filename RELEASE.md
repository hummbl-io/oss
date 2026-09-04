# Release Discipline

All packages in this monorepo must follow this release process. No exceptions.

## Tag contract (one string)

Canonical tag shape, parsed by `.github/workflows/publish-pypi.yml`:

```
python/<package>/v<version>
```

Example:

```
git tag python/hummbl-governance/v1.4.2
git push origin python/hummbl-governance/v1.4.2
```

The workflow extracts `package` and `version` by stripping the `python/`
prefix and splitting on `/v`. A tag that does not match
`python/<package>/v*` **will not start the workflow**.

### Legacy tags (do not reuse this shape)

These existing tags are **not** in the workflow filter:

- `hummbl-governance/v1.4.2`
- `hummbl/v0.1.0`
- `hummbl-kernel/v0.1.0`

They remain as historical refs. New publishes use `python/<package>/v*`
only.

`hummbl-bus==0.2.0` is on PyPI (2026-08-27) without a matching
`python/hummbl-bus/v0.2.0` tag in this repo. Do not publish another bus
version until that provenance gap is documented in the package changelog
or backfilled from the matching commit.

## Rules

1. **No manual uploads.** Never use `twine upload` locally. All PyPI publishes go through the GitHub Actions trusted-publishing workflow (`.github/workflows/publish-pypi.yml`) using `pypa/gh-action-pypi-publish` with OIDC. No API tokens. The workflow is split into a `build` job (no `id-token`) and a `publish` job (`id-token: write`, `environment: pypi`) so build-time code never has access to the OIDC token.

2. **No releases from unmerged branches.** The source being released must be on `main`. The workflow enforces this with a `git merge-base --is-ancestor` check — a tag not on main will fail the build. Merge the feature branch to `main` before tagging.

3. **Tag the merge commit, not the feature branch commit.** After merging, tag the resulting merge commit on `main` with the canonical shape above.

4. **Version must match.** The version in `pyproject.toml` on the tagged commit must match the version in the tag name. The workflow enforces this with a comparison step — a mismatch will fail the build. Keep `pyproject.toml` and any `__init__.py` / `governance.yml` versions in sync.

5. **One tag per release.** Never reuse a tag. Never move a tag. If a release is bad, yank it on PyPI and cut a new version. The workflow does NOT use `skip-existing` — a duplicate upload will fail loudly, signaling a possible tag reuse or manual upload that needs investigation.

## Why

- **Provenance integrity**: consumers and auditors must be able to trace any PyPI artifact back to an exact git commit via the tag. Manual uploads from feature branches break this traceability (see the 2026-08-21 provenance discrepancy where PyPI 1.4.0 was built from an unmerged branch commit, not the v1.4.0 tag).
- **Trusted publishing**: OIDC-based trusted publishing eliminates API tokens from the supply chain. `twine upload` requires a token, reintroducing a secret that can be leaked or stolen.
- **Build/publish separation**: the PyPA-recommended two-job pattern ensures build-time dependencies (e.g., a compromised `setuptools` or `build` package) cannot access the OIDC token. Only the publish job has `id-token: write`.
- **Reproducibility**: `git checkout <tag>` must produce the same source that was built and published. Tags on unmerged branches violate this.

## Pre-release checklist

1. Version bumped in `pyproject.toml` (and `__init__.py`, `governance.yml` if applicable)
2. `CHANGELOG.md` updated with a `## [<version>]` section
3. Feature branch merged to `main`
4. `main` is green (CI passing)
5. Tag created on the merge commit: `git tag python/<package>/v<version>`
6. Tag pushed: `git push origin python/<package>/v<version>`
7. Workflow triggered and completed — both `build` and `publish` jobs pass
8. Verify on PyPI: artifact exists, version matches, "Uploaded using Trusted Publishing? Yes"

## Workflow-enforced gates

The publish workflow (`publish-pypi.yml`) enforces these checks automatically:

| Gate | How | Fails if |
|------|-----|----------|
| Tag on main | `git merge-base --is-ancestor $GITHUB_SHA origin/main` | Tag is not an ancestor of main |
| Version match | Compare `pyproject.toml` version to tag version | Versions differ |
| Build/publish separation | Two jobs; only publish has `id-token: write` | Build-time code cannot access OIDC token |
| No silent skips | `skip-existing` is not set (defaults to false) | Duplicate upload fails loudly |
| OIDC only | `pypa/gh-action-pypi-publish` with no `password` input | No API token in workflow |

The workflow also runs package tests, builds an SBOM, signs artifacts
with Sigstore, attests provenance, and opens a GitHub Release for the
tag. Those steps exist in YAML; they only run when the tag matches the
filter.

## Repository configuration requirements

These must be configured outside the workflow file:

- **PyPI trusted publisher**: for each package, configure on pypi.org with owner `hummbl-io`, repo `oss`, workflow `publish-pypi.yml`, environment `pypi`
- **GitHub `pypi` environment**: configure required reviewers and/or wait timer for production safety
- **Branch protection on `main`**: require PR reviews + CI before merge
- **Tag protection**: prevent force-pushing or deleting tags
- **No PyPI API tokens**: remove any legacy API tokens from PyPI account settings; trusted publishing replaces them

## Yank and rollback

If a release is bad:
1. **Yank on PyPI**: `pip download hummbl-governance==<version>` will still work but `pip install` won't pick it up by default
2. **Do NOT move the tag** — leave it pointing to the bad commit for audit trail
3. **Cut a new version**: bump version, merge to main, tag, push
4. **Document** the yank in `CHANGELOG.md` under the new version

## Pre-releases (alpha/beta/rc)

Pre-release tags follow the same contract:
`python/hummbl-governance/v1.5.0a1`,
`python/hummbl-governance/v1.5.0b1`,
`python/hummbl-governance/v1.5.0rc1`.
Use PyPI's pre-release handling — consumers must opt in with `--pre`.

## Adding a new package

1. Create `packages/python/<name>/` with source and `pyproject.toml`
2. Add the tag pattern `python/<name>/v*` to `.github/workflows/publish-pypi.yml`
3. Add `<name>` to the CI package matrix in `.github/workflows/ci.yml`
4. Add a row to README, `AGENTS.md`, and `docs/PACKAGES.md`
5. Configure the trusted publisher on pypi.org (owner `hummbl-io`, repo `oss`, workflow `publish-pypi.yml`, environment `pypi`)
6. Document the package in `packages/python/<name>/README.md`
