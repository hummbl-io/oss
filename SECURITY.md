# Security Policy

## Supported Versions

This is a monorepo. Each package has its own support lifecycle.
"Supported" here means security reports against that version line will be
accepted. It is not a production-use or certification claim.

Published packages (wheel on PyPI + matching tree version):

| Package | Version line | Supported |
|---------|--------------|-----------|
| hummbl-governance | 1.4.x | Yes (current) |
| hummbl-governance | 1.0.x | Security fixes only |
| base120 | 3.0.x | Yes (current) |
| hummbl-bif | 1.0.x | Yes (current) |
| hummbl-bus | 0.2.x | Yes (current, pre-1.0) |
| hummbl-tuples | 0.2.x | Yes (current, pre-1.0) |
| hummbl-cognition | 0.1.x | Yes (current, pre-1.0) |
| governed-compression | 0.1.x | Yes (current, pre-1.0) |
| hummbl | 0.1.x | Yes (current, pre-1.0) |
| hummbl-kernel | 0.1.x | Yes (current, pre-1.0) |
| any other line of a published package | older than current | No |

In-tree packages that are **not** on PyPI are accepted as source-level
reports against `main` only. They have no supported release line until
the first trusted-publishing tag (`python/<package>/v*`).

Pre-1.0 does **not** mean unsupported. It means no long-term support
window: only the current `0.x` line listed above.

## Reporting a Vulnerability

If you discover a security vulnerability in any HUMMBL OSS package, please report it responsibly:

1. **Email:** security@hummbl.io
2. **Do NOT** open a public GitHub issue for security vulnerabilities
3. Include: package name, description of the vulnerability, steps to reproduce, and potential impact
4. You can expect an initial response within 48 hours

## Scope

This policy covers:

- Every Python package under `packages/python/` in this monorepo
- PyPI projects published from this repo (`hummbl-*`, `base120`,
  `governed-compression`, `idp-spec`)

Each package's security surface is documented in its package README
and `SECURITY.md` where present.

Key security-relevant packages:

- **hummbl-governance** — kill switch, circuit breaker, audit log, identity registry, capability fence, output validator, delegation
- **hummbl-kernel** — orchestration kernel with capability admission and audit trail
- **hummbl-bus** — append-only coordination bus, principal proof on privileged writes
- **idp-spec** — HMAC delegation profile (in-tree)

## Disclosure Policy

- Vulnerabilities are disclosed after a fix is released and a minimum 90-day
  window has passed, or sooner if the reporter agrees.
- Credit is given to reporters unless they prefer to remain anonymous.
