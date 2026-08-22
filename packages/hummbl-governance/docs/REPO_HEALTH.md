# Repository Health Contract

## Identity

- **Repository**: `hummbl-io/hummbl-governance`
- **Canonical URL**: `https://github.com/hummbl-io/hummbl-governance`
- **Package**: `hummbl-governance`
- **Owner**: HUMMBL Team
- **Stewardship scope**: Zero-runtime-dependency governance primitives for AI agent orchestration, including safety, cost, identity, compliance, reasoning, coordination, physical-AI, and audit logging.

## Lifecycle

- **Status**: Active public repository and PyPI package.
- **Default branch**: `main`.
- **Current package version**: `1.4.0`.
- **Release posture**: Runtime primitives, MCP entry points, compliance mappers, and conformance fixtures may continue through reviewed pull requests.
- **Archive trigger**: Archive only if the governance primitive package is superseded by another declared canonical source of truth and PyPI ownership is updated or retired.

## Source Of Truth

- `pyproject.toml` defines package metadata, supported Python versions, runtime dependency policy, test extras, and CLI entry points.
- `hummbl_governance/` contains the importable runtime package and all shipped primitives.
- `tests/` contains the validation suite for primitives, MCP handlers, conformance fixtures, compliance mappings, and failure modes.
- `docs/*-mapping.md` records compliance mapping surfaces for SOC2, GDPR, ISO 27001, NIST CSF, NIST AI RMF, and OWASP.
- `docs/trackers/` records open governance documentation parity, unverified claims, schema freeze, and evidence provenance work.
- `README.md` is the public package overview and should not overclaim test counts, primitive counts, or framework coverage beyond current code and CI evidence.
- `docs/TEST_COUNT_AUTHORITY.md` defines the source-of-truth rules for primitive-count and package test-count claims across README, SECURITY, PyPI, and health surfaces.

## Python Support

- **Supported classifiers** (declared in `pyproject.toml`): Python 3.11, 3.12, 3.13.
- **CI-tested versions**: Python 3.11, 3.12, 3.13 (GitHub Actions matrix). Gitea CI tests Python 3.13.13 only.
- **Python 3.14** is not claimed as supported until the CI matrix includes it.

## Required Local Validation

Before merging non-trivial code or contract changes:

```bash
python -m pip install -e ".[test]"
python -m pytest tests/ -v --cov=hummbl_governance --cov-report=term --cov-fail-under=80
ruff check .
```

Documentation-only changes should at minimum pass:

```bash
git diff --check
```

## CI Expectations

Two separate CI surfaces. Both must be green before release.

### GitHub CI (mirror — public, ubuntu-latest)

- `.github/workflows/ci.yml` runs test suite + coverage threshold 80 on **ubuntu-latest**, Python **3.11, 3.12, 3.13** matrix.
- `.github/workflows/ci.yml` runs install-smoke tests on the same matrix.
- `.github/workflows/ci.yml` verifies zero third-party runtime dependencies.
- `.github/workflows/ci.yml` runs `ruff check .`.

### Gitea CI (canonical — self-hosted Windows, Python 3.13)

- `.gitea/workflows/ci.yml` runs the same 5-job pipeline on a self-hosted Windows runner (`ci-runner`), **Python 3.13.13 only** (toolcache path: `/path/to/runner/toolcache/Python\3.13.13\x64`).
- Uses `& "$env:PYTHON"` explicit invocation. Do NOT use `actions/setup-python@v5` or bare `python` on this runner.
- Includes Arbiter governance score gate (minimum 90.0).
- Aspirational: expand Gitea CI to match GitHub multi-Python matrix in a future pass.

## Branch Protection Expectation

`main` should require pull request review and the hosted CI checks that protect package correctness, installability, linting, zero-runtime-dependency posture, and Arbiter governance score.

Branch protection is tracked centrally in `hummbl-io/hummbl-dev#18`; do not overclaim required checks until that audit is updated.

## Operational Notes

- Core runtime code must remain stdlib-only; third-party packages belong in optional test or tooling extras unless explicitly approved.
- Breaking primitive contracts, CLI entry points, or public package metadata require SemVer review.
- Public compliance and OWASP coverage claims must stay aligned with code, tests, docs, and evidence trackers.
- Conformance fixture changes should preserve deterministic validation and include clear acceptance criteria.

## Fleet Scan Classification

Future fleet scans can classify this repository as:

- **Lifecycle**: active public package
- **Visibility**: public
- **Primary function**: AI governance primitive library
- **Validation entrypoint**: `pytest` with coverage threshold 80
- **Primary metadata owner**: HUMMBL Team
