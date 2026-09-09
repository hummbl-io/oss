# GOVERNANCE.md — hummbl-io/oss monorepo

## Purpose

This document defines the governance model for the `hummbl-io/oss` monorepo.
It establishes per-package ownership, contribution rules, graduated sanctions
for broken or orphaned packages, conflict resolution, and extraction rights.

The model is **nested polycentric governance**: each package retains local
autonomy over its own scope while participating in a shared monorepo commons.

This is a living document. Changes require operator ratification.

## 1. Package Ownership

### 1.1 OWNERS file

Every package under `packages/python/<name>/` MUST have an `OWNERS` file
listing at least one maintainer. Changes to a package require review from
at least one OWNER of that package.

### 1.2 PROVENANCE.md

Every package MUST have a `PROVENANCE.md` documenting:
- Original source repository
- Import date and mechanism (file-copy only — no git history transfer)
- Original maintainer
- Package purpose
- PII/secrets sanitization status

### 1.3 Adding a new package

1. Create `packages/python/<name>/` with `pyproject.toml`, `OWNERS`,
   `PROVENANCE.md`, `README.md`, `LICENSE`, `LICENSE-APACHE`, `LICENSE-MIT`.
2. Add the package to the CI matrix in `.github/workflows/ci.yml`
   (both `test` and `test-preview` jobs).
3. Update the package tables in `AGENTS.md`, `README.md`, `docs/PACKAGES.md`.
4. Run gitleaks full-history scan on the source repository.
5. Verify no internal hostnames, operator names, receipts, or AARs are
   present in the imported content.
6. Open a PR. CI must pass on all declared Python versions.

### 1.4 Removing a package

1. Open a PR proposing removal with a justification.
2. OWNER of the package must ACK or the operator must ratify.
3. Remove from CI matrix and all doc tables.
4. If the package was published to PyPI, note the last published version
   in `docs/PACKAGES.md` under a "Removed" section.

## 2. Contribution Rules

### 2.1 Conventional Commits

All commits MUST follow Conventional Commits format:
`type(scope): description`

### 2.2 No AI attribution

Commit messages MUST NOT include `Co-authored-by`, `Generated-by`, or
equivalent AI attribution trailers.

### 2.3 Branch naming

Feature branches: `type/description` (e.g., `feat/import-mcp-packages`).

### 2.4 CI requirements

- All packages MUST pass CI on their declared Python version matrix.
- `pip-audit` MUST pass for packages with runtime dependencies.
- Workflow validation MUST pass (0 FAIL, 0 WARN).

## 3. Graduated Sanctions

When a package breaks CI or becomes orphaned, the following graduated
sanctions apply:

### Level 1: Warning (CI broken < 7 days)

- The package OWNER is notified via GitHub issue.
- The package remains in the CI matrix.
- Other packages are not affected (fail-fast is disabled).

### Level 2: Quarantine (CI broken 7-30 days)

- The package is moved to a `quarantine` section in the CI matrix
  with `continue-on-error: true`.
- A deprecation notice is added to the package README.
- The OWNER has 30 days to fix or find a new maintainer.

### Level 3: Archive (CI broken > 30 days or OWNER unreachable)

- The package directory is moved to `packages/python/_archived/<name>/`.
- The package is removed from the CI matrix.
- The package is marked as "Archived" in `docs/PACKAGES.md`.
- If published to PyPI, the last version remains available but no new
  releases will be made from this monorepo.
- The original source repo (if still archived on GitHub) remains as the
  canonical historical record.

### Level 4: Removal (archived > 90 days with no restoration)

- The package directory is deleted from the monorepo.
- An entry is added to `docs/PACKAGES.md` under "Removed" with the last
  version and removal date.
- The package can be re-imported later by following section 1.3.

## 4. Conflict Resolution

### 4.1 Technical disputes

1. Open a GitHub issue with the `governance` label.
2. Package OWNER(s) and the operator discuss in the issue.
3. If no resolution within 7 days, the operator decides.

### 4.2 Ownership disputes

1. If an OWNER is unreachable for > 30 days, open a `governance` issue.
2. The operator may reassign ownership.
3. The previous OWNER's `OWNERS` entry is moved to a "Past maintainers"
   comment section.

### 4.3 Cross-package conflicts

1. When two packages have conflicting requirements (e.g., dependency
   version constraints), open a `governance` issue.
2. OWNERS of both packages must participate.
3. The operator arbitrates if no consensus is reached.

## 5. Extraction Rights (Secession)

Any package may be extracted from the monorepo back to a standalone
repository under the following conditions:

1. The package OWNER requests extraction via a `governance` issue.
2. The extraction plan preserves:
   - All package source code and tests
   - `pyproject.toml` (adapted for standalone)
   - `OWNERS` and `PROVENANCE.md`
   - License files
3. The monorepo's `docs/PACKAGES.md` is updated to note the extraction
   and the new standalone repo URL.
4. If the package was published to PyPI from this monorepo, the Trusted
   Publisher configuration on PyPI must be updated to point to the new
   standalone repo before the next release.
5. The operator must ratify the extraction.

Extraction is a right, not a privilege. A package OWNER may leave the
monorepo with their package. The monorepo does not hold packages hostage.

## 6. PyPI Publishing

### 6.1 Trusted Publishers

PyPI publishing uses Trusted Publishers (OIDC) — no API tokens. Each
package must be configured as a trusted publisher on pypi.org pointing
to this repo + `publish-pypi.yml` workflow + `pypi` environment.

### 6.2 Release process

1. Bump version in `pyproject.toml`.
2. Merge the version bump to `main`.
3. Tag the merge commit: `git tag python/<package>/v<version>`.
4. Push the tag: `git push origin python/<package>/v<version>`.
5. The `publish-pypi.yml` workflow builds, tests, publishes, signs
   (Sigstore), generates SBOM, and creates a GitHub Release.

### 6.3 Per-package operator approval

Each package's first PyPI publication requires explicit operator approval.
Subsequent releases of the same package do not require re-approval unless
the package changes ownership or scope.

## 7. Nested Governance

### 7.1 Package-level autonomy

Each package OWNER has authority over:
- Package scope and feature direction
- Dependency choices (subject to stdlib-only default and review)
- Test strategy and coverage requirements
- Release cadence

### 7.2 Monorepo-level coordination

The operator and monorepo maintainers coordinate:
- CI matrix and Python version support
- Shared infrastructure (license files, workflow templates)
- Cross-package dependencies
- Archival and extraction decisions

### 7.3 No monocentric control

No single maintainer controls all packages. Package OWNERS are sovereign
within their package scope. The operator's role is ratification and
arbitration, not day-to-day package management.

## 8. Security

### 8.1 Secret scanning

GitHub Secret Scanning and Push Protection are enabled on this repository.
All source repositories must be scanned with `gitleaks` before import.

### 8.2 PII sanitization

Imported content must not contain:
- Internal hostnames or IP addresses
- Operator names or personal information
- Internal handoffs, session transcripts, AARs, or receipts
- Internal infrastructure details
- Fleet inventory or audit matrices

### 8.3 Incident response

If a secret is discovered post-import:
1. Rotate the secret immediately.
2. Open a `security` issue documenting the exposure.
3. Remove the secret from the monorepo (history rewrite is NOT performed
   — GitHub Push Protection prevents future pushes, and the secret is
   already rotated).
4. Post a bus STATUS documenting the incident and remediation.

## 9. License

All packages in this monorepo are dual-licensed under MIT OR Apache-2.0
unless a package's `pyproject.toml` declares otherwise. License files
(`LICENSE`, `LICENSE-APACHE`, `LICENSE-MIT`) are maintained at the
package level.
