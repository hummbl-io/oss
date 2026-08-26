# Security Policy

## Supported Versions

This is a monorepo. Each package has its own support lifecycle. The table
below covers all packages currently published from this repo.

| Package | Version | Supported |
|---------|---------|-----------|
| hummbl-governance | 1.4.x | Yes (current) |
| hummbl-governance | 1.0.x – 1.3.x | Yes (security fixes only) |
| base120 | 3.0.x | Yes (current) |
| hummbl-bif | 1.0.x | Yes (current; package is archived, security fixes only) |
| hummbl-tuples | 0.2.x | Yes (current, pre-1.0) |
| hummbl-bus | 0.1.x | Yes (current, pre-1.0) |
| hummbl-cognition | 0.1.x | Yes (current, pre-1.0) |
| governed-compression | 0.1.x | Yes (current, pre-1.0) |
| hummbl | 0.1.x | Yes (current, pre-1.0) |
| hummbl-kernel | 0.1.x | Yes (current, pre-1.0) |

Pre-1.0 packages receive security fixes but have no API stability guarantee.
Fixes are released as patch bumps within the 0.x line.

## Reporting a Vulnerability

If you discover a security vulnerability in any HUMMBL OSS package, please
report it responsibly. **Do NOT open a public GitHub issue.**

Preferred reporting channels, in order of preference:

1. **GitHub Private Security Advisory** (preferred):
   https://github.com/hummbl-io/oss/security/advisories/new
   This enables coordinated disclosure, CVE assignment, and a one-click
   patch-Publish flow directly from the advisory.
2. **Email:** security@hummbl.io

For sensitive reports sent by email, PGP-encrypted reports are accepted.
Contact security@hummbl.io first to request the current public key
fingerprint (the key is published on request rather than committed to the
repo to avoid key-rotation drift in source control).

Please include:
- Package name and affected version(s)
- Description of the vulnerability
- Steps to reproduce (proof of concept if possible)
- Potential impact and affected primitives/surfaces

You can expect an initial response within **48 hours**. We will work with
you on a fix and coordinated disclosure timeline.

## Scope

This policy covers all packages published from this monorepo. The primary
registry today is **PyPI** (Python). When packages are published to
additional registries (npm, crates.io, Go proxy, Maven Central), this
policy extends to those artifacts as well.

Key security-relevant packages:
- **hummbl-governance** — governance primitives (kill switch, circuit
  breaker, audit log, identity registry, capability fence, output
  validator, delegation tokens)
- **hummbl-bus** — append-only coordination bus with optional HMAC message
  signing
- **hummbl-kernel** — orchestration kernel with capability admission policy
  and audit trail
- **hummbl-cognition** — Cognitive Ledger Protocol and server

For each package's specific security surface and threat model, see the
package's own README and any `docs/security-model.md` it ships.

## Disclosure Policy

- Vulnerabilities are disclosed after a fix is released and a minimum
  90-day window has passed, or sooner if the reporter agrees.
- Credit is given to reporters unless they prefer to remain anonymous.
- Fixed vulnerabilities are recorded in the affected package's
  `CHANGELOG.md` with a reference to the advisory or CVE once published.

## Supply Chain

This monorepo uses the following supply-chain controls:

- **Trusted publishing (OIDC)** to PyPI — no long-lived API tokens. See
  [`RELEASE.md`](./RELEASE.md).
- **SHA-pinned GitHub Actions** — enforced by
  `.github/workflows/validate-workflows.yml`; tag refs (`@v4`, `@main`)
  cause `startup_failure`.
- **Build/publish separation** — the build job has no `id-token` access;
  only the publish job has `id-token: write`.

Known supply-chain gaps currently being addressed (tracked separately):
- No secret-scanning / gitleaks CI gate on PR diffs (public/private
  boundary relies on human review per [`CONTRIBUTING.md`](./CONTRIBUTING.md)
  section 3).
- No SBOM, SLSA provenance, or Sigstore artifact attestation on releases.
- CI runs on a single Python version (3.13); declared 3.11/3.12 support is
  not yet matrix-tested.
