# Public Claims

Status: public claim ledger
Last updated: 2026-08-23
Current package metadata: `pyproject.toml` version `1.4.1`

This ledger keeps public claims evidence-backed. A claim should be promoted
only when its status is `verified` or when it is explicitly framed as planned,
draft, pending, or source-candidate.

## Claim Status Table

| Claim                                                                   | Status           | Receipt                                                                                                                                                                                            | Promotion rule                                                                  |
| ----------------------------------------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Package version is `1.4.1`                                              | verified         | `pyproject.toml` declares `version = "1.4.1"`                                                                                                                                                      | May be stated as package metadata.                                              |
| Runtime dependencies are zero                                           | verified         | `pyproject.toml` has `dependencies = []`                                                                                                                                                           | May be stated as zero third-party runtime dependencies.                         |
| CI tests Python 3.11, 3.12, and 3.13                                    | verified         | `.github/workflows/ci.yml` matrix includes 3.11, 3.12, 3.13                                                                                                                                        | May be stated as CI-tested on 3.11-3.13.                                        |
| Python 3.14 is supported                                                | not verified     | CI matrix and `pyproject.toml` classifiers do not include 3.14 at this audit                                                                                                                       | Do not claim support until CI includes 3.14 and passes.                         |
| Current local test inventory is 2314 collected tests                    | verified-locally | `python -m pytest --collect-only -q tests` on 2026-08-17 collected 2314 tests from the tree based on commit `bc56261`                                                                                                          | May be stated as local collection evidence.                                     |
| Last full local functional suite passed 2027 tests                      | verified-locally | `python -m pytest tests/ -q --no-cov` on 2026-07-05 passed 2027 tests on the local working tree at `ae0ef412eb9dd79fdd809841f03ec5866b85046a`                                                      | Historical receipt only; rerun before claiming current full-suite status.       |
| Last coverage-enforced command passed 2027 tests                        | verified-locally | `python -m pytest tests/ -q --cov=hummbl_governance --cov-report=term --cov-fail-under=80` on 2026-07-05 passed 2027 tests on the local working tree at `ae0ef412eb9dd79fdd809841f03ec5866b85046a` | Historical receipt only; rerun before claiming current coverage status.         |
| 34 implemented governance primitives exist                              | verified         | `PRIMITIVES.md` lists 26 existing primitives and 8 implemented expansion primitives                                                                                                                | May be stated as implemented package primitive inventory.                       |
| 7 MCP server entry points exist                                         | verified         | `pyproject.toml` `[project.scripts]` lists 7 `*-mcp` entry points                                                                                                                                  | May be stated as entry-point inventory. Tool counts require a separate receipt. |
| Production-tested / runs daily in production                            | needs receipt    | No production operations receipt captured in this pass                                                                                                                                             | Do not use for promotion until receipt exists.                                  |
| Extracted from hummbl-governance with 15,600+ tests and 14 CI workflows      | needs receipt    | Depends on another repo and current live state                                                                                                                                                     | Do not use for promotion until independently verified.                          |
| OWASP Top 10 for Agentic Applications engineering mapping               | source-candidate | README has an engineering mapping; no third-party attestation                                                                                                                                      | Phrase as engineering mapping, not certification or coverage guarantee.         |
| SOC2/GDPR/NIST/EU AI Act mappings                                       | source-candidate | Coverage docs exist, but validation state varies                                                                                                                                                   | Phrase as evidence mapping support, not compliance certification.               |
| Universal or categorical competitor claims                              | not verified     | No current comparative inventory receipts the former "Every team," "nothing to govern," or "No other library" wording                                                                          | Use bounded package-inventory language; do not claim competitors lack features. |
| `governance.yml` declarative governance metadata in wheel              | scoped           | README line 159 reworded (2026-08-07): universal-negative "No other Python ecosystem ships..." replaced with capability-specific "giving consumers a machine- and human-readable statement..."  | May state that HUMMBL packages include governance.yml. Do not claim uniqueness across ecosystems without a dated comparison receipt. |
| `hummbl.io/pricing` reports 1,032 tests                                  | stale/blocking   | Current package collection is 2314; a paired static-site draft corrects the pricing page                                                                                                            | Merge and verify the website correction before sponsorship launch.              |

## Required Receipts Before Promotion

- Full coverage-enforced test pass receipt for the target commit.
- Build and wheel install smoke receipt.
- Link check for README and public docs.
- Secret scan with allowlisted fixture/demo patterns.
- GitHub settings receipt for description, topics, homepage, Issues,
  Discussions, Pages, Wiki, branch protection, and security features.
- PyPI page receipt for current version, project URLs, classifiers, and trusted
  publishing posture.
- Claim inventory receipt for README, package metadata, and release docs.

## Wording Rules

- Use "CI-tested on Python 3.11 through 3.13" only while the CI matrix excludes
  Python 3.14. Do not include a Python 3.14 classifier until CI covers it.
- Use "engineering mapping" for framework tables unless a third-party
  attestation exists.
- Use "zero third-party runtime dependencies" only for package runtime deps;
  test and tooling extras may still use third-party packages.
- Do not use production, customer, benchmark, or extraction claims without a
  current receipt.
- Do not use universal market claims or categorical competitor comparisons
  without a dated, reproducible comparison receipt.

## Metric Scope Table

Different surfaces report different metrics. This table clarifies scope so
claims are not mixed across boundaries.

| Surface                   | Version | Tests                | Primitives | Scope                                                                         |
| ------------------------- | ------- | -------------------- | ---------- | ----------------------------------------------------------------------------- |
| `pyproject.toml` (source) | 1.3.0   | —                    | 34         | Package metadata — source of truth for version                                |
| README.md (repo)          | 1.3.0   | 2314 collected       | 34         | Repo docs — current local collection at base `bc56261`                        |
| ROADMAP.md (repo)         | 1.3.0   | 2027 collected       | 34         | Release-history statement, not current working-tree inventory                 |
| GitHub repo description   | 1.3.x   | 2,027                | 34         | Stale repo metadata; launch blocker pending a separately authorized update     |
| PyPI long description     | 1.3.0   | 2027 collected (verified) | 34         | Published on PyPI for `hummbl-governance 1.3.0`                            |
| hummbl.io homepage        | —       | 15,600+ aggregate    | 7 marketed | Website — ecosystem aggregate tests; 7 is the marketed subset on /primitives/ |
| hummbl.io pricing         | —       | 1,032                | —          | Stale live metric; paired static-site draft updates it to 2314                 |

**Key distinction:** The package has 34 implemented primitives. The hummbl.io
website markets 7 of those as user-facing primitives on its /primitives/ index.
Both numbers are correct in their respective scopes.
