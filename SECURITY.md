# Security Policy

## Supported Versions

This is a monorepo. Each package has its own support lifecycle.

| Package | Version | Supported          |
|---------|---------|--------------------|
| hummbl-governance | 1.4.x | Yes (current)      |
| hummbl-governance | 1.0.x | Yes (security fixes only) |
| hummbl-kernel | 0.1.x | Yes (current, pre-release) |
| hummbl | 0.1.x | Yes (current, pre-release) |
| < 1.0 (any package) | — | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in any HUMMBL OSS package, please report it responsibly:

1. **Email:** security@hummbl.io
2. **Do NOT** open a public GitHub issue for security vulnerabilities
3. Include: package name, description of the vulnerability, steps to reproduce, and potential impact
4. You can expect an initial response within 48 hours

## Scope

This policy covers all Python packages published from this monorepo to PyPI
under the `hummbl-*` namespace. Each package's security surface is documented
in its respective package README and `SECURITY.md` (where present).

Key security-relevant packages:
- **hummbl-governance** — governance primitives (kill switch, circuit breaker, audit log, identity registry, capability fence, output validator)
- **hummbl-kernel** — orchestration kernel with capability admission policy and audit trail

## Disclosure Policy

- Vulnerabilities are disclosed after a fix is released and a minimum 90-day
  window has passed, or sooner if the reporter agrees.
- Credit is given to reporters unless they prefer to remain anonymous.
