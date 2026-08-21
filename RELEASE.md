# Release Discipline

All packages in this monorepo must follow this release process. No exceptions.

## Rules

1. **No manual uploads.** Never use `twine upload` locally. All PyPI publishes go through the GitHub Actions trusted-publishing workflow (`.github/workflows/publish-pypi.yml`) using `pypa/gh-action-pypi-publish` with OIDC. No API tokens.

2. **No releases from unmerged branches.** The source being released must be on `main`. Merge the feature branch to `main` before tagging. This ensures the git tag always points to code that is reachable from `main` and that `git checkout <tag>` reproduces the published artifact.

3. **Tag the merge commit, not the feature branch commit.** After merging, tag the resulting merge commit on `main`:
   ```
   git tag hummbl-governance/v1.4.2
   git push origin hummbl-governance/v1.4.2
   ```
   The tag push triggers the publish workflow.

4. **Version must match.** The version in `pyproject.toml` on the tagged commit must match the version in the tag name. The workflow does not override versions.

5. **One tag per release.** Never reuse a tag. Never move a tag. If a release is bad, yank it on PyPI and cut a new version.

## Why

- **Provenance integrity**: consumers and auditors must be able to trace any PyPI artifact back to an exact git commit via the tag. Manual uploads from feature branches break this traceability (see ADR-2026-08-21-001: hummbl-governance 1.4.0 provenance discrepancy).
- **Trusted publishing**: OIDC-based trusted publishing eliminates API tokens from the supply chain. `twine upload` requires a token, reintroducing a secret that can be leaked or stolen.
- **Reproducibility**: `git checkout <tag>` must produce the same source that was built and published. Tags on unmerged branches violate this.

## Pre-release checklist

1. Version bumped in `pyproject.toml`
2. `CHANGELOG.md` updated
3. Feature branch merged to `main`
4. `main` is green (CI passing)
5. Tag created on the merge commit: `git tag <package>/v<version>`
6. Tag pushed: `git push origin <package>/v<version>`
7. Workflow triggered and completed
8. Verify on PyPI: artifact exists, version matches, "Uploaded using Trusted Publishing? Yes"
