# Public Claims

Status: public claim ledger
Last updated: 2026-08-31
Current package metadata: `pyproject.toml` version `1.4.2` (Alpha)

Canonical public promotion source: the [landing claims ledger](https://hummbl.io/manifest/landing-claims.json)
(`as_of` 2026-08-31T21:56:55Z). Honesty over completeness. A number that is not
backed by a public receipt is dropped or scoped, not promoted.

This ledger keeps public claims evidence-backed. A claim should be promoted
only when its status is `verified` or `verified-with-scope`, or when it is
explicitly framed as planned, draft, pending, historical, or source-candidate.

GAP-001 is **closed** on the live landing claims ledger: a scoped public-probe
receipt is linked. `production_use_established` remains false, so a general
production-tested claim is still not allowed. GAP-002 and GAP-003 remain **open**.

## Claim Status Table

| Claim | Status | Receipt | Promotion rule |
| ----- | ------ | ------- | -------------- |
| Package version is `1.4.2` and classified Alpha | verified | `pyproject.toml` declares `version = "1.4.2"` and `Development Status :: 3 - Alpha`. Landing claim LANDING-002. Tag `hummbl-governance/v1.4.2`, commit `b1b0581`. | May be stated as current published package metadata. Alpha is maturity, not production suitability. |
| Runtime Core dependencies are zero | verified-with-scope | `pyproject.toml` has `dependencies = []` at tag `hummbl-governance/v1.4.2`. Landing claim LANDING-005. | May be stated as zero third-party Core runtime dependencies. Optional, test, build, and integration extras are out of scope. |
| Public oss CI reported 2,463 passed and 3 skipped on Python 3.13 | verified-with-scope | GitHub Actions [run 32904924444](https://github.com/hummbl-io/oss/actions/runs/32904924444) at commit `7546c4e` on oss main. Landing claims LANDING-004 and LANDING-006. | May be stated as public oss repository CI on Python 3.13 only. This is not a production-use receipt. |
| Public oss CI tests Python 3.11, 3.12, and 3.13 | not verified (GAP-003) | Public oss `.github/workflows/ci.yml` runs `python-version: "3.13"` only and does not collect coverage. | Do not claim public CI-tested on 3.11–3.13. Declared classifiers in `pyproject.toml` are not a public CI matrix. |
| Public coverage percentage | not verified (GAP-003) | Public oss CI does not collect coverage. | Do not publish a coverage percentage. The earlier 3.11/3.12/3.13 matrix with 84.45% coverage was private-repo only and is not public evidence. |
| Python 3.14 is supported | not verified | Classifiers and public oss CI do not include 3.14. | Do not claim support until public CI includes 3.14 and passes. |
| Local collection of 2314 tests (2026-08-17, commit `bc56261`) | historical / not for public promotion | Former local `pytest --collect-only` receipt. Not the current public CI receipt. | Do not state as the current public test count. Use the public oss CI receipt instead. |
| Local full-suite / coverage-enforced 2027-test passes (2026-07-05) | historical / not for public promotion | Former local working-tree receipts. | Historical only. Do not state as current public suite or coverage status. |
| 34 implemented governance primitives | verified-with-scope | `PRIMITIVES.md` at tag `hummbl-governance/v1.4.2` (26 existing plus 8 implemented expansion primitives). Landing claim LANDING-003. | May be stated as implemented package primitive inventory. Proposed primitives are excluded. |
| 7 MCP server entry points exist | verified | `pyproject.toml` `[project.scripts]` lists 7 `*-mcp` entry points. | May be stated as entry-point inventory. Tool counts require a separate receipt. |
| Scoped public-probe receipt `r-7e400da03299` | verified-with-scope | LANDING-012 (`VERIFIED_WITH_SCOPE`, evidence level `public-surface-production-use`). Published hummbl-governance 1.4.2 `ReceiptEngine` recorded signed receipt `r-7e400da03299` for a live public GET on https://hummbl-receipt-probe.hummbl.workers.dev/ at 2026-08-31T21:56:55Z. Linked receipt: [hummbl-governance-v1.4.2-public-probe-receipt.json](https://hummbl.io/manifest/evidence/hummbl-governance-v1.4.2-public-probe-receipt.json). | May cite this one public-probe GET at that timestamp. Scope is that surface only. |
| General production-tested / runs daily in production | not verified | The linked public-probe receipt sets `production_use_established` to false. LANDING-012 states that the scoped public-surface event does not support a general production-tested claim. The package remains Alpha. | Do not claim general production-tested status for the package, customers, or the private fleet. |
| Cold-visitor comprehension results | not verified (GAP-002) | No public comprehension protocol results are linked. | Do not invent or promote comprehension metrics. |
| Extracted from another repo with 15,600+ tests and 14 CI workflows | not verified | Not in the current landing claims ledger. Depends on another repo. | Do not use for promotion. |
| OWASP Top 10 for Agentic Applications engineering mapping | source-candidate | README has an engineering mapping; no third-party attestation. | Phrase as engineering mapping, not certification or coverage guarantee. |
| SOC2/GDPR/NIST/EU AI Act mappings | source-candidate | Coverage docs exist, but validation state varies. | Phrase as evidence mapping support, not compliance certification. |
| Universal or categorical competitor claims | not verified | No current comparative inventory receipts. | Use bounded package-inventory language; do not claim competitors lack features. |
| `governance.yml` declarative governance metadata in wheel | scoped | HUMMBL packages include `governance.yml`. | May state that HUMMBL packages include governance.yml. Do not claim uniqueness across ecosystems without a dated comparison receipt. |
| Website pricing or homepage aggregate test counts (for example 1,032 or 15,600+) | not verified / not for promotion | Those figures are not in the current landing claims ledger. | Do not promote. Public test counts are the scoped public oss CI receipt above. |

## Closed evidence gaps

| ID | Resolution | Remaining boundary |
| -- | ---------- | ------------------ |
| GAP-001 | Live-closed on the landing claims ledger (`as_of` 2026-08-31T21:56:55Z). A scoped public-probe receipt is linked: `r-7e400da03299` at 2026-08-31T21:56:55Z on https://hummbl-receipt-probe.hummbl.workers.dev/. | `production_use_established` remains false. Do not claim general production-tested status. |

## Open evidence gaps

GAP-002 and GAP-003 stay open.

| ID | Gap | Effect |
| -- | --- | ------ |
| GAP-002 | No cold-visitor comprehension results exist yet. | Do not invent or publish comprehension metrics. |
| GAP-003 | Public oss CI runs Python 3.13 only and does not collect coverage. The earlier 3.11/3.12/3.13 matrix with 84.45% coverage was private-repo only. | Do not claim a public multi-version Python matrix or a public coverage percentage. |

## Required Receipts Before Promotion

- Public oss CI matrix receipt covering every Python version claimed as CI-tested (GAP-003).
- Public coverage receipt if a coverage percentage is claimed (GAP-003). Private-repo coverage is not a substitute.
- A package-level production-use receipt with `production_use_established: true` before any general production-tested claim. The linked public-probe receipt does not satisfy that field.
- Cold-visitor comprehension results if communication effectiveness is claimed (GAP-002).
- Build and wheel install smoke receipt.
- Link check for README and public docs.
- Secret scan with allowlisted fixture/demo patterns.
- PyPI page receipt for current version, project URLs, classifiers, and trusted
  publishing posture.
- Claim inventory receipt for README, package metadata, and release docs.

## Wording Rules

- Use the public oss CI receipt for current test counts: 2,463 passed and 3
  skipped on Python 3.13 ([run 32904924444](https://github.com/hummbl-io/oss/actions/runs/32904924444)).
  Scope the sentence as public oss repository CI, not production use.
- Do not say "CI-tested on Python 3.11 through 3.13" while public oss CI is
  3.13 only. Classifiers may declare 3.11–3.13; that is not a public CI matrix.
- Do not publish 84.45% coverage or any other private-repo coverage figure as
  a public claim.
- Do not reuse historical local counts (2314 collected, 2027 passed) as the
  current public test count.
- Use "engineering mapping" for framework tables unless a third-party
  attestation exists.
- Use "zero third-party Core runtime dependencies" only for package runtime
  deps; test and tooling extras may still use third-party packages.
- The linked public-probe receipt (`r-7e400da03299`) may be cited as one
  scoped public-surface GET. It is not a general production-tested claim.
- Do not use customer, benchmark, extraction, or comprehension claims
  without a current public receipt.
- Do not use universal market claims or categorical competitor comparisons
  without a dated, reproducible comparison receipt.
- Keep the Alpha classification. Do not imply general production readiness.
  `production_use_established` remains false.

## Metric Scope Table

Different surfaces report different metrics. This table clarifies scope so
claims are not mixed across boundaries. Only the public-receipt rows are
eligible for current promotion.

| Surface | Version | Tests | Primitives | Scope |
| ------- | ------- | ----- | ---------- | ----- |
| `pyproject.toml` (source) | 1.4.2 | — | 34 | Package metadata — source of truth for version and Alpha classifier. |
| README.md (repo) | 1.4.2 | 2,463 passed / 3 skipped | 34 | Public docs — aligned to the landing claims ledger and public oss CI. |
| Public oss CI | — | 2,463 passed / 3 skipped | — | [Run 32904924444](https://github.com/hummbl-io/oss/actions/runs/32904924444) at commit `7546c4e` on oss main. Python 3.13 only. No coverage collected. Repository CI evidence, not a production-use receipt. |
| Landing claims ledger | 1.4.2 | 2,463 passed / 3 skipped | 34 | Canonical public promotion source (`as_of` 2026-08-31T21:56:55Z). |
| Historical local collection | — | 2314 collected | — | Former local receipt (2026-08-17). Not current public evidence. |
| Private-repo CI matrix + coverage | — | — | — | 3.11/3.12/3.13 and 84.45% coverage were private-repo only. Not public evidence (GAP-003). |

**Key distinction:** The package has 34 implemented primitives. Public oss CI
currently proves one Python version (3.13) and one job result (2,463 passed,
3 skipped). Declared language classifiers and private-repo history are not
substitutes for a public matrix.
