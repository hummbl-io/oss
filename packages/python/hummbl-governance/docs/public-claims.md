# Public Claims

Status: public claim ledger
Last updated: 2026-09-11
Current package metadata: `pyproject.toml` version `1.5.0` (tree, Alpha) — latest published release is `1.4.2` on PyPI; see `RELEASE.md`

Canonical public promotion source: the [landing claims ledger](https://hummbl.io/manifest/landing-claims.json)
(`as_of` 2026-08-31T21:56:55Z). Honesty over completeness. A number that is not
backed by a public receipt is dropped or scoped, not promoted.

This ledger keeps public claims evidence-backed. A claim should be promoted
only when its status is `verified` or `verified-with-scope`, or when it is
explicitly framed as planned, draft, pending, historical, or source-candidate.

GAP-001 is **closed** on the live landing claims ledger: a scoped public-probe
receipt is linked. `production_use_established` remains false, so a general
production-tested claim is still not allowed. GAP-003 is **closed** as of
2026-09-11 (public oss CI already runs the full 3.11-3.14 matrix with
coverage collection; this file previously said otherwise and was itself
stale — see the Closed evidence gaps table). GAP-002 remains **open**.

## Claim Status Table

| Claim | Status | Receipt | Promotion rule |
| ----- | ------ | ------- | -------------- |
| Published package version is `1.4.2` and classified Alpha | verified-with-scope | PyPI-live `pyproject.toml` at tag `hummbl-governance/v1.4.2`, commit `b1b0581`, declares `version = "1.4.2"` and `Development Status :: 3 - Alpha`. Landing claim LANDING-002. The current tree has since moved to `1.5.0` (also Alpha, also verified in-tree 2026-09-11) but has not been released; see `RELEASE.md`. | May be stated as the current published package metadata. State tree work as unreleased when describing `1.5.0`-tree features. Alpha is maturity, not production suitability. |
| Runtime Core dependencies are zero | verified-with-scope | `pyproject.toml` has `dependencies = []` at tag `hummbl-governance/v1.4.2` (PyPI-live) and confirmed still `dependencies = []` in the current `1.5.0` tree as of 2026-09-11. Landing claim LANDING-005. | May be stated as zero third-party Core runtime dependencies. Optional, test, build, and integration extras are out of scope. |
| Public oss CI reported 3,479 passed and 16 skipped on Python 3.13 | verified-with-scope | GitHub Actions [run 34610754121](https://github.com/hummbl-io/oss/actions/runs/34610754121) at commit `77854dd` on oss main (the PR #222 merge commit). Supersedes the prior 2,463/3 receipt (run 32904924444, commit `7546c4e`), which predated P44-P58/K12-K14. | May be stated as public oss repository CI on Python 3.13. This is not a production-use receipt. |
| Public oss CI tests Python 3.11, 3.12, 3.13, and 3.14 | verified (GAP-003 closed 2026-09-11) | Same run 34610754121: `test (hummbl-governance, 3.11)`, `3.12`, `3.13`, `3.14` all `success`. `.github/workflows/ci.yml` matrix is `["3.11","3.12","3.13","3.14"]`, not 3.13-only — this row and GAP-003 were themselves stale; corrected 2026-09-11. | May be stated as public CI-tested on 3.11 through 3.14. |
| Public oss CI collects coverage for hummbl-governance | verified (GAP-003 closed 2026-09-11) | `ci.yml` runs `pytest tests/ -q --cov=hummbl_governance --cov-report=term` for this package specifically; confirmed in run 34610754121's logs. | May state that public CI collects coverage for this package. Do not publish a specific coverage percentage (not extracted/verified here) — that remains a separate, unverified claim. |
| Python 3.14 is supported | verified | Public oss CI (run 34610754121) includes and passes `test (hummbl-governance, 3.14)`. | May be stated as CI-tested on 3.14. |
| Local collection of 2314 tests (2026-08-17, commit `bc56261`) | historical / not for public promotion | Former local `pytest --collect-only` receipt. Not the current public CI receipt. | Do not state as the current public test count. Use the public oss CI receipt instead. |
| Local full-suite / coverage-enforced 2027-test passes (2026-07-05) | historical / not for public promotion | Former local working-tree receipts. | Historical only. Do not state as current public suite or coverage status. |
| 51 implemented governance primitives | verified | `PRIMITIVES.md` header ("Total implemented: 51") and `hummbl_governance.primitive_registry.PrimitiveRegistry().implemented_primitives()` agree as of 2026-09-11 (58 tracked total: 51 implemented, 4 proposed/not-started, 3 candidate). Supersedes the prior "34" figure (v1.4.2-era: 26 existing + 8 implemented expansion; missed P35, P37, and the 9 post-v1.2 primitives P44-P52) and the intermediate "45" figure recorded earlier the same day. Two registry gaps were fixed 2026-09-11: (1) P35 RegulatorExport was marked `not_started` despite the module, schema, and 40 tests existing and PRIMITIVES.md marking it implemented; (2) PR #220 (merged 2026-09-11, same day) added 6 real, tested GDPR primitives (P53 HumanReviewGate, P54 ContestationHandler, P55 DSARHandler, P56 RedactionEngine, P57 RecordsOfProcessing, P58 DPIAGenerator — 103 passing tests) and updated `PRIMITIVES.md`'s header/counts, but never added corresponding `PrimitiveRegistry` entries, so the registry still computed 45 immediately after that merge. Both gaps are now fixed; registry and `PRIMITIVES.md` agree at 51. | May be stated as implemented package primitive inventory. Proposed (4) and candidate (3) primitives are excluded. Regenerate this count from `PrimitiveRegistry` rather than hand-counting before any future promotion. |
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
| GAP-003 | Closed 2026-09-11. This file previously said public oss CI ran Python 3.13 only with no coverage collection; that was itself stale. Verified via run [34610754121](https://github.com/hummbl-io/oss/actions/runs/34610754121): the matrix covers 3.11/3.12/3.13/3.14 and `hummbl-governance` runs with `--cov`. | A coverage *percentage* is still not extracted or published — do not state one. The private-repo 84.45% figure remains private-repo-only evidence. |

## Open evidence gaps

GAP-002 stays open.

| ID | Gap | Effect |
| -- | --- | ------ |
| GAP-002 | No cold-visitor comprehension results exist yet. | Do not invent or publish comprehension metrics. |

## Required Receipts Before Promotion

- Public coverage *percentage* receipt if a specific number is ever claimed (coverage collection itself is now verified, but no percentage has been extracted from public CI). Private-repo coverage is not a substitute.
- A package-level production-use receipt with `production_use_established: true` before any general production-tested claim. The linked public-probe receipt does not satisfy that field.
- Cold-visitor comprehension results if communication effectiveness is claimed (GAP-002).
- Build and wheel install smoke receipt.
- Link check for README and public docs.
- Secret scan with allowlisted fixture/demo patterns.
- PyPI page receipt for current version, project URLs, classifiers, and trusted
  publishing posture.
- Claim inventory receipt for README, package metadata, and release docs.

## Wording Rules

- Use the public oss CI receipt for current test counts: 3,479 passed and 16
  skipped on Python 3.13 ([run 34610754121](https://github.com/hummbl-io/oss/actions/runs/34610754121)).
  Scope the sentence as public oss repository CI, not production use.
- "CI-tested on Python 3.11 through 3.14" is now accurate (GAP-003 closed
  2026-09-11) — public oss CI runs the full matrix, not 3.13 only.
- Coverage is collected in public CI for this package, but do not publish a
  specific coverage *percentage* — none has been extracted from a public
  receipt. Do not publish 84.45% coverage or any other private-repo coverage
  figure as a public claim.
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
| `pyproject.toml` / tree (source) | 1.5.0 (tree); 1.4.2 (PyPI live) | 3,495 collected locally (2026-09-11, not a public CI receipt) | 51 | Package metadata and `PrimitiveRegistry` — source of truth for primitive count. Tree version has moved past the last PyPI release; see `RELEASE.md`. |
| README.md (repo) | 1.4.2 | 3,479 passed / 16 skipped (current — matches run 34610754121) | 51 | Public docs — primitive count and test-count badge both corrected 2026-09-11. |
| Public oss CI | — | 3,479 passed / 16 skipped | — | [Run 34610754121](https://github.com/hummbl-io/oss/actions/runs/34610754121) at commit `77854dd` (the PR #222 merge) on oss main. Full 3.11-3.14 matrix, coverage collected (no percentage published). Repository CI evidence, not a production-use receipt. |
| Landing claims ledger | 1.4.2 | 2,463 passed / 3 skipped | 34 (stale) | Canonical public promotion source (`as_of` 2026-08-31T21:56:55Z) — has not yet been refreshed to 51 or to the fresh test-count receipt; landing-claims.json update is a follow-up outside this repo (needs a real hummbl-governance PyPI release + a new landing-release-receipt, not a hand-edit — see `scripts/emit_landing_release_receipt.py` in hummbl-production). |
| Historical local collection | — | 2314 collected | — | Former local receipt (2026-08-17). Not current public evidence. |
| Private-repo CI matrix + coverage | — | — | — | The 84.45% coverage *percentage* remains private-repo-only evidence (public CI now collects coverage but doesn't publish a percentage). |

**Key distinction:** The package has 51 implemented primitives (58 tracked:
51 implemented, 4 proposed, 3 candidate), regenerable from `PrimitiveRegistry`.
Public oss CI now proves the full 3.11-3.14 matrix with coverage collection
(run 34610754121, 2026-09-11) — GAP-003 is closed. Only a specific coverage
*percentage* remains unpublished. The `hummbl.io` landing claims ledger is a
separate, out-of-repo surface still showing the stale figures; fixing it
needs a real PyPI release and receipt regeneration, not a text edit here.
