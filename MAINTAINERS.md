# Maintainers

## Current maintainers

| Name | GitHub | PyPI role | Scope |
|------|--------|-----------|-------|
| Reuben Bowlby | @reuben | Owner (all `hummbl-*` + `base120` + `governed-compression` projects) | All packages, release authority, security response |

## Bus factor

This monorepo currently has a single maintainer. That is a known risk for
a public supply chain: if the sole maintainer becomes unavailable, every
published package becomes orphaned. Per the deprecation policy in
[`CONTRIBUTING.md`](./CONTRIBUTING.md) section 5, published package names
are never deleted (Revival Hijack defense), so an orphaned package
becomes **permanently unmaintained attack surface** rather than a
recoverable vacancy.

## Succession policy

To reduce this risk, the following are required or planned:

1. **Required — second trusted publisher.** At least one additional
   maintainer must be configured as a trusted publisher on PyPI for every
   package published from this repo, so releases are not blocked by a
   single person's availability. Configure on pypi.org under each project:
   owner `hummbl-io`, repo `oss`, workflow `publish-pypi.yml`, environment
   `pypi`.
2. **Required — second owner on the `hummbl-io` GitHub organization.** At
   least one other admin must hold the organization so repository and
   ruleset administration is not single-person.
3. **Planned — `MAINTAINERS.md` expansion.** When a second maintainer is
   onboarded, add them to the table above with their package scope.
4. **Planned — transfer policy.** If the sole maintainer is permanently
   unavailable, packages transfer to the `hummbl-io` organization's
   surviving admin rather than being abandoned. This must be documented in
   the org-level governance, not only here.

## Release authority

Only maintainers listed in the table above may merge to `main` and push
release tags. The publish workflow uses OIDC trusted publishing bound to
the `hummbl-io/oss` repository and `pypi` environment — no individual API
tokens are involved, so release authority is governed by GitHub branch
protection and the `pypi` environment's required reviewers, not by
whoever holds a PyPI token. See [`RELEASE.md`](./RELEASE.md).

## Security response

The security contact is `security@hummbl.io` (see
[`SECURITY.md`](./SECURITY.md)). A second security contact should be
configured so vulnerability reports are not single-point-of-failure.
