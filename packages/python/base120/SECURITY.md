#  Supported Versions

## Supported Versions

The Base120 project currently supports the following versions with security updates:

| Version | Supported |
| --- | --- |
| v1.0.0 | Yes |

All prior or future experimental branches are unsupported unless explicitly stated.

## Reporting a Vulnerability

If you discover a security vulnerability in Base120, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, use one of the following channels:

- Email: hummbl@proton.me
- GitHub Security Advisories: https://github.com/hummbl-io/oss/security/advisories

Include, at minimum:

- A clear description of the vulnerability
- Steps to reproduce (proof-of-concept if possible)
- Affected versions / commits
- Potential impact assessment

## Disclosure Process

1. You submit a private report.
2. The maintainers acknowledge receipt within 72 hours.
3. The issue is triaged and assigned a severity.
4. A fix is developed and validated against the canonical corpus.
5. A coordinated disclosure is performed, including:
   - Patch release
   - Advisory publication
   - Credit to the reporter (if desired)

## Scope

Security considerations apply to:

- Validator logic
- Registry integrity (ERR / FM / mappings)
- Schema enforcement
- CI/CD workflows
- Release artifacts and tags

Out of scope unless explicitly stated:

- Third-party mirrors or forks
- Downstream consumer implementations
- Non-authoritative language ports

## Security Guarantees

Base120 v1.0.0 guarantees:

- Deterministic validation outputs
- Corpus-backed semantic enforcement
- Explicit failure-mode escalation rules
- No network access or dynamic code execution in core logic

Any violation of these guarantees is considered a security issue.

## Key Management

- Git tags are the source of truth for released versions.
- No cryptographic signing is currently enforced for artifacts.
- Governance for signed releases is proposed in v1.1.0.

## Acknowledgements

We appreciate responsible disclosure and contributions that improve the safety and reliability of the Base120 ecosystem.
