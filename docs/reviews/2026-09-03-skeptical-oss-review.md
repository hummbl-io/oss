# Skeptical OSS Review — hummbl-io/oss

| Field | Value |
| --- | --- |
| Status | local working-tree artifact (untracked at write time; not committed; not pushed) |
| Date (UTC) | 2026-09-03 |
| Reviewer identity | grok-build (advisory; non-principal) |
| Host | delta |
| Target | https://github.com/hummbl-io/oss |
| Checkout | `/work/active/oss` ≡ `~/PROJECTS/oss` |
| HEAD | `3fa541198845f1379b5386628364b9644d34c4c1` (`3fa5411`) |
| Branch | `main` tracking `origin/main` |
| Lens | External OSS reviewer: would a stranger star, depend on, or contribute to this repo? |
| Related open audits | GitHub issues #80 (Audit-0), #84 (Audit-1) — unlabeled; this review does not assume they were actioned |
| Companion rubric | `docs/reviews/public-trust-surface-audit.md` |

This document records the 2026-09-03 skeptical review. It is evidence, not a merge, publish, or label action.

**Write envelope for this file:** operator instruction “save all findings to a doc.” Path allowlist is this file only. Pre-existing dirty paths were not modified. No commit, push, PR, or GitHub mutation.

---

## 1. Method

### 1.1 What was inspected

- Local git tree at HEAD `3fa5411` (README, LICENSE*, SECURITY.md, CONTRIBUTING.md, AGENTS.md, `.github/`, `packages/python/`, `docs/artifacts/`, `tools/scripts/check_boundary_patterns.py`).
- GitHub repo metadata, issues, PRs, releases, Actions runs, branch protection (`gh` on 2026-09-03).
- PyPI JSON for 25 package names (`https://pypi.org/pypi/<name>/json`).
- Contributor and tag telemetry from `git log` / `git tag` (no `git fetch` on the write pass).

### 1.2 What was not inspected (do not infer)

- Local install or `pytest` of the 25-package CI matrix.
- Byte-for-byte diff of `hummbl-io/hummbl-governance` vs `packages/python/hummbl-governance` (open issue #48).
- OSV/NVD advisory sweep of published wheels.
- Fresh `git fetch` against `origin` on the write pass.
- Legal/trademark/privacy judgment.
- Whether `docs/artifacts/` was copied from a private proving-ground on purpose.

### 1.3 Claim rules used

Load-bearing statements in this review use a 4-field provenance row: **claim**, **source**, **source_quote**, **verified_date**. Rows missing a field are marked Tier C and must not be reused as public copy.

Severity:

- **high** — leak, false public claim, or a control that fails closed for a stranger
- **medium** — docs-vs-reality, publish-path drift, or maintenance risk
- **low** — missing community files or local hygiene

Health score is a reviewer rubric, not a certification.

---

## 2. Verdict

**Health score: 41 / 100.**

Nine live PyPI wheels and a working Actions surface keep this from being a ghost repo. An external OSS reviewer still should not treat `hummbl-io/oss` as a healthy open-source project. It reads as a public dump of a one-maintainer company plus some real libraries: bus factor 1, zero adopters, GitHub cannot parse the license, private strategy docs sit on the default branch, Tests are not a required check, and 16 of 25 named packages are unpublished.

Scoring (reviewer rubric, not a standard):

| Axis | Score | Cap | Basis |
| --- | ---: | ---: | --- |
| Activity | 12 | 15 | 103 commits in ~90 days; HEAD 2026-09-03 |
| License clarity | 5 | 15 | Dual MIT OR Apache-2.0 in-tree; GitHub `Other`/`NOASSERTION`; PyPI license fields disagree |
| Community | 2 | 15 | 0 stars, 0 forks, 0 watchers, 0 subscribers |
| Bus factor / maintainers | 4 | 15 | 88/103 commit authors are Reuben Bowlby; CODEOWNERS is `@hummbl-dev` only |
| Security / merge gates | 8 | 15 | gitleaks + CodeQL + SECURITY.md exist; Tests not required; reviews null |
| Docs honesty / boundary | 6 | 15 | README inventory is mostly accurate; CONTRIBUTING and artifacts are not |
| **Total** | **37** | **90** | scaled to **41/100** |

---

## 3. Findings

### F1 — high — Private board/strategy corpus is tracked on the public default branch

`docs/artifacts/` is git-tracked (36 files, 638,633 bytes). Multiple files declare `Status: live v1.0 (private)` and still ship in this public repository. `BRIEFING_BOOK_board_q3_2026.md` is a Q3 2026 board briefing (funding, priorities, exit gates). `SWOT_hummbl_current_state.md` is marked private and discusses pre-revenue / single-founder status.

This is an org-boundary failure, not “docs.” GitHub issue #45 already names the class; the files remain.

**Evidence**

- `git ls-files docs/artifacts` → 36 paths (list in §5.4).
- `git ls-files -z docs/artifacts \| xargs -0 wc -c` → `638633 total`.
- `docs/artifacts/BRIEFING_BOOK_board_q3_2026.md` lines 1–11.
- `docs/artifacts/SWOT_hummbl_current_state.md` lines 1–11.

### F2 — high — Public/private boundary CI cannot see F1

`tools/scripts/check_boundary_patterns.py` denies filenames (`HANDOFF-*`, `AAR-*`, `RECEIPT-*`, …) and Tailscale CGNAT IPs. It does not deny `docs/artifacts/`, the word `private`, board briefings, or SOC 2 papers. Latest **Boundary check** on `main` concluded `success` (created 2026-09-03T15:57:54Z). Control passed; the leak remained.

**Evidence**

- `tools/scripts/check_boundary_patterns.py` docstring: “file-name-based detection”; `DENYFILE_PATTERNS` / `DENYDIR_NAMES` do not include `artifacts`.
- GitHub Actions run list: Boundary check `conclusion=success` on `headBranch=main` at 2026-09-03T15:57:54Z.

### F3 — high — `Tests` is not a required status check

Branch protection on `main` requires only `gitleaks` and `pattern-denylist`. `required_pull_request_reviews` is null. `enforce_admins` is true. `.github/workflows/ci.yml` defines a `ci-ok` aggregator so Tests can be required (comment cites #91). It is not in the protection snapshot. A write-access push can land with a red test matrix.

**Evidence**

- `gh api repos/hummbl-io/oss/branches/main/protection` → `contexts=["gitleaks","pattern-denylist"]`, `reviews=null`, `enforce_admins=true`, `strict=true`.
- `.github/workflows/ci.yml` job `ci-ok` (lines 103–118) and comment “Single required-check context for branch protection.”

### F4 — high — License files exist; GitHub and PyPI do not agree

Root `LICENSE` is a pointer (“dual-licensed … SPDX … MIT OR Apache-2.0”). GitHub license API reports `key=other`, `spdx=NOASSERTION`. PyPI: `hummbl-bus` and `hummbl-cognition` license `MIT`; `hummbl-bif` `Apache-2.0`; several wheels have empty license metadata. A stranger cannot answer “what am I allowed to do?” from the GitHub license badge.

**Evidence**

- `LICENSE` (full file, 7 lines).
- `gh api repos/hummbl-io/oss/license` → `spdx=NOASSERTION`, `name=Other`.
- PyPI JSON `info.license` sampled 2026-09-03 (§5.6).

### F5 — high — Public SOC 2 copy overclaims readiness

`docs/artifacts/POSITION_PAPER_soc2_type_ii_readiness.md` is marked `Status: live v1.0 (public)` and states HUMMBL is “structurally ready for SOC 2 Type II.” Readiness ≠ attestation. This is public copy on an OSS default branch.

**Evidence**

- File header lines 1–10 (quoted in C12).

### F6 — medium — CONTRIBUTING.md describes registries that are not in this tree

CONTRIBUTING claims the monorepo publishes to PyPI, npm, crates.io, Go proxy, Maven Central, Nix, arXiv/Zenodo. README: “There is no `packages/node/` or `packages/rust/` tree in this repository yet.” Inventory fiction.

**Evidence**

- `CONTRIBUTING.md` lines 3–4.
- `README.md` lines 18–20.

### F7 — medium — `governed-compression` is live on PyPI as a “Private research surface”

PyPI summary (2026-09-03 GET): `Private research surface for governed compression experiments`. `docs/PACKAGES.md` already flags the leftover. The public registry still says private.

**Evidence**

- `https://pypi.org/pypi/governed-compression/json` → `info.summary` as above.
- `docs/PACKAGES.md` line 55.

### F8 — medium — SECURITY.md lists `idp-spec` among published PyPI projects; PyPI 404s it

SECURITY.md scope bullet includes `idp-spec` in the published-from-this-repo set. Later in the same file, `idp-spec` is correctly called in-tree. PyPI GET for `idp-spec` returned HTTP 404.

**Evidence**

- `SECURITY.md` lines 45–47 vs 56–57.
- PyPI GET 404, 2026-09-03.

### F9 — medium — Bus factor 1; zero public adopters

`git log --format='%an'` unique counts: Reuben Bowlby 88, dependabot[bot] 11, cursor[bot] 2, hummbl-agent 1, github-actions[bot] 1. `.github/CODEOWNERS` is `@hummbl-dev` on `*`. GitHub: `stargazerCount=0`, `forkCount=0`, watchers 0, subscribers 0.

**Evidence**

- Author histogram §5.3.
- `.github/CODEOWNERS` (entire file).
- `gh repo view` / `gh api repos/hummbl-io/oss` §5.1.

### F10 — medium — Most of the monorepo is not a shipped product

README table: 25 Python packages. PyPI GET 2026-09-03: **9 LIVE**, **16 MISS (404)**. Live versions matched the README “Live” column. 14 in-tree packages have a single `tests/test_*.py` (count of files matching `test_*.py` / `*_test.py`). CI still spends a matrix job on each.

**Evidence**

- README package table (lines 32–58).
- PyPI results §5.6.
- Test file counts §5.5.
- `.github/workflows/ci.yml` matrix `package:` list (25 names).

### F11 — medium — Publish-path drift vs documented tag contract

`README.md` / `RELEASE.md`: publish tags must be `python/<package>/v<version>`. Existing tags: `hummbl/v0.1.0`, `hummbl-kernel/v0.1.0`, `hummbl-governance/v1.4.2`. `docs/PACKAGES.md` records `hummbl-bus` 0.2.0 uploaded 2026-08-27 with **no** `python/hummbl-bus/v0.2.0` tag.

**Evidence**

- `git tag --list` → three tags, none with `python/` prefix.
- `docs/PACKAGES.md` line 52.
- GitHub Releases: those three tag names, dated 2026-08-26.

### F12 — medium — Adoption tracker advertised in README is failing

README § Adoption tracking presents a daily PyPI download workflow as live. Actions: last three PyPI Download Tracker runs = failure, success, failure.

**Evidence**

- `README.md` lines 95–103.
- `gh run list --workflow 'PyPI Download Tracker' --limit 3` §5.7.

### F13 — low — No Code of Conduct

`CODE_OF_CONDUCT.md` absent at repo root and `.github/` (`test -f` exit 1 both paths). Fine for a tiny library; not fine next to “enterprise” / SOC 2 papers in the same tree.

### F14 — low — Root `AGENTS.md` is agent-runtime instruction, not contributor docs

Present and tracked. Unusual on a public package monorepo; not a secret, but it is not a CONTRIBUTING substitute.

### F15 — low — Local `_state/` exists (gitignored)

`.gitignore:17:_state/` ignores `_state/coordination/messages.tsv`. Local directories `_state/` and `packages/python/_state` exist on this checkout. Not a GitHub leak. Operator hygiene.

### F16 — low — Prior audits unlabeled and open

- #80 Audit-0 (2026-08-30), updated 2026-08-31, labels `[]`, OPEN.
- #84 Audit-1 (2026-08-31), updated 2026-08-31, labels `[]`, OPEN.

This review does not close or duplicate them; it records that they were not labeled.

---

## 4. Claims ledger (4-field provenance)

`verified_date` is the UTC calendar date of this review unless noted. Quotes are truncated with `…` only after a complete clause.

| ID | claim | source | source_quote | verified_date | finding |
| --- | --- | --- | --- | --- | --- |
| C1 | The GitHub repository `hummbl-io/oss` is public, has 0 stars and 0 forks, default branch `main`, created 2026-08-21. | `gh repo view hummbl-io/oss --json isPrivate,stargazerCount,forkCount,createdAt,defaultBranchRef` | `"isPrivate":false,"stargazerCount":0,"forkCount":0,"createdAt":"2026-08-21T05:03:34Z"`; defaultBranchRef.name `main` | 2026-09-03 | F9 |
| C2 | GitHub license detection is `Other` / SPDX `NOASSERTION`. | `gh api repos/hummbl-io/oss/license` | `"spdx":"NOASSERTION"`, `"name":"Other"`, `"key":"other"` | 2026-09-03 | F4 |
| C3 | In-tree license is dual MIT OR Apache-2.0. | `LICENSE` | `The SPDX expression for this dual-license is "MIT OR Apache-2.0".` | 2026-09-03 | F4 |
| C4 | Required status checks on `main` are only `gitleaks` and `pattern-denylist`; PR reviews are not required. | `gh api repos/hummbl-io/oss/branches/main/protection` | `contexts: ["gitleaks","pattern-denylist"]`, `reviews: null`, `enforce_admins: true` | 2026-09-03 | F3 |
| C5 | Latest Tests and Boundary check on `main` succeeded at 2026-09-03T15:57:54Z. | `gh run list --repo hummbl-io/oss --limit 8 --json name,conclusion,headBranch,createdAt` | Tests `conclusion=success` `headBranch=main` `createdAt=2026-09-03T15:57:54Z`; Boundary check same | 2026-09-03 | F2, F3 |
| C6 | Nine README “Live” packages exist on PyPI at the listed versions; sixteen in-tree names 404. | HTTP GET `https://pypi.org/pypi/<name>/json` for 25 names | See §5.6; e.g. `hummbl-governance` `info.version=1.4.2`; `idp-spec` `HTTP Error 404` | 2026-09-03 | F10, F8 |
| C7 | `governed-compression` PyPI summary calls it a private research surface. | `https://pypi.org/pypi/governed-compression/json` `info.summary` | `Private research surface for governed compression experiments` | 2026-09-03 | F7 |
| C8 | `docs/artifacts/` is tracked: 36 files, 638,633 bytes. | `git ls-files docs/artifacts`; `git ls-files -z docs/artifacts \| xargs -0 wc -c` | 36 paths listed; `638633 total` | 2026-09-03 | F1 |
| C9 | The Q3 board briefing is marked private and is in the public tree. | `docs/artifacts/BRIEFING_BOOK_board_q3_2026.md` L1–L7 | `# Briefing Book: Board Q3 2026` / `**Status:** live v1.0 (private)` / `**Reader:** Board members …` | 2026-09-03 | F1 |
| C10 | The SWOT is marked private and is in the public tree. | `docs/artifacts/SWOT_hummbl_current_state.md` L1–L8 | `**Status:** live v1.0 (private)` / `**Reader:** Operator, Board, agents` | 2026-09-03 | F1 |
| C11 | Boundary checker is filename/IP based and skips `packages/` for filename denies. | `tools/scripts/check_boundary_patterns.py` L8–L13, L67–L83 | `Approach: file-name-based detection is false-positive safe.` / `Skips packages/ directory` | 2026-09-03 | F2 |
| C12 | A public SOC 2 position paper claims structural Type II readiness. | `docs/artifacts/POSITION_PAPER_soc2_type_ii_readiness.md` L1–L10 | `**Status:** live v1.0 (public)` / `**Position:** HUMMBL is structurally ready for SOC 2 Type II; the gap is operational (no external audit yet conducted)` | 2026-09-03 | F5 |
| C13 | CONTRIBUTING claims polyglot publishing; README says no node/rust trees. | `CONTRIBUTING.md` L3–4; `README.md` L18–20 | CONTRIBUTING: `publishes HUMMBL packages to public registries (PyPI, npm, crates.io, Go proxy, Maven Central, Nix, arXiv/Zenodo).` README: `There is no \`packages/node/\` or \`packages/rust/\` tree in this repository yet.` | 2026-09-03 | F6 |
| C14 | SECURITY.md includes `idp-spec` in the published-PyPI set. | `SECURITY.md` L45–47 | `PyPI projects published from this repo (\`hummbl-*\`, \`base120\`, \`governed-compression\`, \`idp-spec\`)` | 2026-09-03 | F8 |
| C15 | Existing git tags are not `python/<package>/v<version>`. | `git tag --list` | `hummbl/v0.1.0` / `hummbl-kernel/v0.1.0` / `hummbl-governance/v1.4.2` | 2026-09-03 | F11 |
| C16 | README documents the `python/<package>/v<version>` tag contract. | `README.md` L91–93 | `Publish tags must be \`python/<package>/v<version>\` (see \`RELEASE.md\`).` | 2026-09-03 | F11 |
| C17 | `hummbl-bus` 0.2.0 was uploaded without the documented tag. | `docs/PACKAGES.md` L52 | `0.2.0 was uploaded 2026-08-27 with **no** \`python/hummbl-bus/v0.2.0\` tag in this repo.` | 2026-09-03 | F11 |
| C18 | Commit-author concentration is one human. | `git log --format='%an' \| sort \| uniq -c` | `88 Reuben Bowlby` of 103 author records (plus 15 bot/agent) | 2026-09-03 | F9 |
| C19 | CODEOWNERS is a single identity. | `.github/CODEOWNERS` | `* @hummbl-dev` | 2026-09-03 | F9 |
| C20 | PyPI Download Tracker is not reliably green. | `gh run list --workflow 'PyPI Download Tracker' --limit 3` | conclusions `failure`, `success`, `failure` | 2026-09-03 | F12 |
| C21 | README presents the download tracker as a live daily loop. | `README.md` L95–103 | `Daily PyPI download stats are collected by … A GitHub Actions workflow runs daily at 12:00 UTC` | 2026-09-03 | F12 |
| C22 | Checkout HEAD is `3fa541198845f1379b5386628364b9644d34c4c1`. | `git rev-parse HEAD` | `3fa541198845f1379b5386628364b9644d34c4c1` | 2026-09-03 | method |
| C23 | Last commit message on HEAD is the GAP-004 docs commit. | `git log -1 --format='%s'` | `docs: add competitive landscape matrix and close GAP-004` | 2026-09-03 | activity |
| C24 | Canonical public sentence is locked in README. | `README.md` L3–12 | `**Structured thinking at fleet scale. One operator, governed agents, any domain.**` / `That sentence is the public definition. It is the same sentence as [hummbl.io](https://hummbl.io).` | 2026-09-03 | positioning (not scored as false) |
| C25 | `pip install base120` and `pip install hummbl-governance` are the two names README recommends. | `README.md` L63–68 | those two lines in a fenced `text` block | 2026-09-03 | F10 |
| C26 | No `CODE_OF_CONDUCT.md` at root or `.github/`. | `test -f CODE_OF_CONDUCT.md`; `test -f .github/CODE_OF_CONDUCT.md` | both exit 1 | 2026-09-03 | F13 |
| C27 | Watchers/subscribers are 0; open_issues 15. | `gh api repos/hummbl-io/oss --jq '{subscribers,watchers,open_issues}'` | `subscribers:0, watchers:0, open_issues:15` | 2026-09-03 | F9 |
| C28 | `_state/` is gitignored; the coordination TSV is not tracked. | `.gitignore` L17; `git check-ignore -v _state/coordination/messages.tsv` | `.gitignore:17:_state/` | 2026-09-03 | F15 |

Tier notes:

- C1–C28 are Tier A for this internal review (primary source resolved in-session).
- Do not promote C12’s *subject-matter* sentence (“structurally ready for SOC 2 Type II”) as HUMMBL public copy. The ledger cites it as a **defect in the tree**, not as a HUMMBL claim to repeat.
- Health score 41/100 is **reviewer-constructed** (Tier C as a public metric; do not publish as a certified score).

---

## 5. Telemetry

All timestamps UTC unless a git `%ci` offset is shown. Commands were run on host `delta` from `/home/reuben/PROJECTS/oss` unless noted.

### 5.1 Repository identity (GitHub)

Command: `gh repo view hummbl-io/oss --json name,isPrivate,description,url,defaultBranchRef,pushedAt,createdAt,stargazerCount,forkCount,licenseInfo,hasIssuesEnabled,visibility,diskUsage,repositoryTopics`

Recorded 2026-09-03 (session open of this review):

| Field | Value |
| --- | --- |
| name | oss |
| visibility / isPrivate | PUBLIC / false |
| url | https://github.com/hummbl-io/oss |
| createdAt | 2026-08-21T05:03:34Z |
| pushedAt | 2026-09-03T15:57:52Z |
| defaultBranchRef | main |
| stargazerCount | 0 |
| forkCount | 0 |
| diskUsage (KB) | 6029 |
| licenseInfo.key / name | other / Other |
| topics | active-ci, hummbl, python |
| hasIssuesEnabled | true |

Command: `gh api repos/hummbl-io/oss --jq '{has_issues,has_discussions:.hasDiscussionsEnabled,subscribers:.subscribers_count,watchers:.watchers_count,open_issues:.open_issues_count}'`

| Field | Value |
| --- | --- |
| subscribers | 0 |
| watchers | 0 |
| open_issues | 15 |
| has_discussions | null |

### 5.2 Local git snapshot

Write-pass snapshot `2026-09-03T22:47:11Z`:

| Field | Value |
| --- | --- |
| branch | main |
| HEAD | 3fa541198845f1379b5386628364b9644d34c4c1 |
| HEAD author-date | 2026-09-03 12:52:50 -0400 |
| HEAD author | Reuben Bowlby \<reuben@hummbl.io\> |
| HEAD subject | docs: add competitive landscape matrix and close GAP-004 |
| upstream | origin/main |
| `rev-list --left-right --count origin/main...HEAD` | `0 1` (0 on origin not in HEAD, 1 on HEAD not in origin) **without git fetch on this write pass** |
| stash | 0 |
| porcelain | 6 |
| samefile PROJECTS/oss vs /work/active/oss | true |

Porcelain at write time (untouched by this review):

```text
 M packages/python/hummbl-design-tokens/hummbl_design_tokens/__init__.py
?? .pyspector_cache/
?? docs/research/2026-09-02-ternary-models-registry-gap-analysis.md
?? packages/python/hummbl-design-tokens/hummbl_design_tokens/ansi.py
?? packages/python/hummbl-garage/hummbl_garage/text.py
?? packages/python/hummbl-heraldry/hummbl_heraldry/text.py
```

This file is an additional untracked path after write: `docs/reviews/2026-09-03-skeptical-oss-review.md`.

### 5.3 Contributors

Command: `git log --format='%an' | sort | uniq -c | sort -rn`

| Count | Author |
| ---: | --- |
| 88 | Reuben Bowlby |
| 11 | dependabot[bot] |
| 2 | cursor[bot] |
| 1 | hummbl-agent |
| 1 | github-actions[bot] |
| **103** | **total author records** |

`git rev-list --count --since='90 days ago' HEAD` → **103** (repo is younger than 90 days; this is essentially full history).

`git shortlog -sn --all` (includes all refs): Reuben Bowlby 109, devin 13, dependabot[bot] 11, Cursor Agent 5, cursor[bot] 2, github-actions[bot] 2, hummbl-agent 1. Shortlog and `git log` histograms are not the same population (all-refs vs current HEAD first-parent author field). Both show one human owner.

### 5.4 Tracked `docs/artifacts/` (F1)

Command: `git ls-files docs/artifacts`

36 paths (byte total 638,633):

```text
docs/artifacts/ARTIFACT_MANIFEST.md
docs/artifacts/ARTIFACT_STACK_PROMOTION_PACKET.md
docs/artifacts/BRIEFING_BOOK_board_q3_2026.md
docs/artifacts/BUSINESS_CASE_game_engine.md
docs/artifacts/BUSINESS_CASE_issueops.md
docs/artifacts/CASE_STUDY_claims_remediation.md
docs/artifacts/CHARTER_hri.md
docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md
docs/artifacts/DOCTRINE_ai_governance.md
docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md
docs/artifacts/EVIDENCE_PACK_fleet_rollout.md
docs/artifacts/MARKET_ANALYSIS_ai_governance.md
docs/artifacts/MODEL_ROUTER_V2_CODESIGN_SCORING.md
docs/artifacts/MODEL_ROUTER_V2_GRINDABILITY_GATE.md
docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md
docs/artifacts/OWNWARD_LANGUAGE_LAW.md
docs/artifacts/OWNWARD_REFLECTIVE_FRICTION_GATES.md
docs/artifacts/PLAYBOOK_agent_onboarding.md
docs/artifacts/PLAYBOOK_claims_change.md
docs/artifacts/PLAYBOOK_fleet_rollout.md
docs/artifacts/POSITION_PAPER_eu_ai_act.md
docs/artifacts/POSITION_PAPER_nist_ai_rmf.md
docs/artifacts/POSITION_PAPER_soc2_type_ii_readiness.md
docs/artifacts/PRIVACY_POLICY_SURFACE_PLAN.md
docs/artifacts/PUBLIC_SURFACE_CLAIM_SYNC_RECEIPT.md
docs/artifacts/RETROSPECTIVE_wave_1.md
docs/artifacts/RETROSPECTIVE_wave_2.md
docs/artifacts/RETROSPECTIVE_wave_3.md
docs/artifacts/RETROSPECTIVE_wave_4.md
docs/artifacts/RISK_REGISTER.md
docs/artifacts/STRATEGIC_PLAN_12mo.md
docs/artifacts/STRESS_TEST_uc7_uc1_uc2.md
docs/artifacts/SWOT_hummbl_current_state.md
docs/artifacts/TEMPLATE.md
docs/artifacts/USE_CASE_CATALOG_hummbl_governance.md
docs/artifacts/WHITE_PAPER_governance_infrastructure.md
```

Header quotes (leak class only; this review does not repeat board funding tables):

```text
# Briefing Book: Board Q3 2026
**Status:** live v1.0 (private)
```

```text
# SWOT: HUMMBL Current State (2026-06-23)
**Status:** live v1.0 (private)
```

```text
# Position Paper: SOC 2 Type II Readiness
**Status:** live v1.0 (public)
**Position:** HUMMBL is structurally ready for SOC 2 Type II; the gap is operational (no external audit yet conducted)
```

### 5.5 Test file counts

Command: count unique `tests/test_*.py` and `tests/*_test.py` under each `packages/python/<pkg>/` (2026-09-03T22:47:35Z). `packages/python/_state` exists on disk and is not a package; ignored here.

| test_*.py files | package |
| ---: | --- |
| 106 | hummbl-governance |
| 54 | hummbl-cognition |
| 22 | hummbl-bus |
| 17 | hummbl-tuples |
| 8 | base120 |
| 8 | hummbl-bif |
| 5 | hummbl-axis |
| 4 | hummbl |
| 4 | hummbl-kernel |
| 4 | hummbl-lattice |
| 4 | idp-spec |
| 2 | hummbl-design-tokens |
| 1 | governed-compression, hummbl-compass, hummbl-contracts, hummbl-free-models, hummbl-garage, hummbl-heraldry, hummbl-identity, hummbl-intel, hummbl-lint-config, hummbl-rubric-templates, hummbl-taxonomy, hummbl-validation, hummbl-validation-framework |

This is **file count**, not assertion count or coverage. Tests were not executed in this review.

### 5.6 PyPI registry GET (2026-09-03)

Command: HTTP GET `https://pypi.org/pypi/<name>/json` for each README table name.

| Package | README status | PyPI | pypi version | pypi license field |
| --- | --- | --- | --- | --- |
| hummbl-governance | Live 1.4.2 | LIVE | 1.4.2 | empty |
| base120 | Live 3.0.0 | LIVE | 3.0.0 | empty |
| hummbl-bus | Live 0.2.0 | LIVE | 0.2.0 | MIT |
| hummbl-cognition | Live 0.1.0 | LIVE | 0.1.0 | MIT |
| hummbl-tuples | Live 0.2.0 | LIVE | 0.2.0 | empty |
| hummbl-bif | Live 1.0.1 | LIVE | 1.0.1 | Apache-2.0 |
| governed-compression | Live 0.1.0 | LIVE | 0.1.0 | empty; summary = “Private research surface…” |
| hummbl | On PyPI 0.1.0 | LIVE | 0.1.0 | empty |
| hummbl-kernel | On PyPI 0.1.0 | LIVE | 0.1.0 | empty |
| hummbl-lattice | In-tree | MISS 404 | — | — |
| hummbl-contracts | In-tree | MISS 404 | — | — |
| hummbl-axis | In-tree | MISS 404 | — | — |
| hummbl-intel | In-tree | MISS 404 | — | — |
| hummbl-lint-config | In-tree | MISS 404 | — | — |
| idp-spec | In-tree | MISS 404 | — | — |
| hummbl-compass | In-tree | MISS 404 | — | — |
| hummbl-free-models | In-tree | MISS 404 | — | — |
| hummbl-rubric-templates | In-tree | MISS 404 | — | — |
| hummbl-taxonomy | In-tree | MISS 404 | — | — |
| hummbl-validation | In-tree | MISS 404 | — | — |
| hummbl-design-tokens | In-tree | MISS 404 | — | — |
| hummbl-heraldry | In-tree | MISS 404 | — | — |
| hummbl-garage | In-tree | MISS 404 | — | — |
| hummbl-identity | In-tree | MISS 404 | — | — |
| hummbl-validation-framework | In-tree | MISS 404 | — | — |

**9 LIVE / 16 MISS.** Live versions matched the README tree/PyPI column for those nine names.

### 5.7 GitHub Actions (sampled 2026-09-03)

`gh run list --repo hummbl-io/oss --limit 8`:

| createdAt | name | headBranch | conclusion |
| --- | --- | --- | --- |
| 2026-09-03T15:57:54Z | Tests | main | success |
| 2026-09-03T15:57:54Z | Boundary check | main | success |
| 2026-09-03T15:57:54Z | CodeQL | main | success |
| 2026-09-03T15:56:10Z | Tests | docs/positioning-update | success |
| 2026-09-03T15:56:10Z | Boundary check | docs/positioning-update | success |
| 2026-09-03T15:56:10Z | CodeQL | docs/positioning-update | success |
| 2026-09-03T15:29:08Z | PyPI Download Tracker | main | **failure** |
| 2026-09-03T10:25:11Z | CodeQL | feat/belief-audit-bus-type | success |

`gh run list --workflow 'PyPI Download Tracker' --limit 3`: failure, success, failure.

### 5.8 Branch protection

Command: `gh api repos/hummbl-io/oss/branches/main/protection`

| Field | Value |
| --- | --- |
| required_status_checks.contexts | gitleaks, pattern-denylist |
| required_status_checks.strict | true |
| required_pull_request_reviews | null |
| enforce_admins.enabled | true |
| restrictions | null |

`Tests` / `ci-ok` are **not** in the required contexts.

### 5.9 Releases and tags

`git tag --list`:

```text
hummbl/v0.1.0
hummbl-kernel/v0.1.0
hummbl-governance/v1.4.2
```

`gh release list --repo hummbl-io/oss --limit 10`: those three, all dated 2026-08-26T22:39:10Z–13Z. Latest = `hummbl/v0.1.0`.

### 5.10 Issues / PRs (sampled)

Open issues (first page of `gh issue list --state open`): #84, #80, #51, #50, #49, #48, #47, #46, #45, #44, #39 (titles include P0 org-boundary, personal-data, standalone vs oss divergence).

`gh issue view 80` / `84`: both OPEN, labels `[]`.

Open PRs at review time: #112, #111, #110, #108.

### 5.11 Workflows on disk

```text
.github/workflows/boundary-check.yml
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/dependency-review.yml
.github/workflows/publish-pypi.yml
.github/workflows/pypi-download-tracker.yml
.github/workflows/validate-workflows.yml
```

### 5.12 Boundary-check control (excerpt)

`tools/scripts/check_boundary_patterns.py` denies file names matching `HANDOFF-`, `AAR-`, `RECEIPT-`, `SESSION-TRANSCRIPT`, `FLEET-INVENTORY`, `AUDIT-<digit>`, `BACKCHANNEL`, `RETIRED-`, `INTERNAL-`, plus directory names `{handoffs, receipts, backchannel, session-transcripts, fleet-inventory, audit-matrices, internal-infra}`, plus CGNAT IPs `100.64.0.0/10` except `100.64.0.1`. Filename checks skip `packages/`. **`docs/artifacts` is not denied.**

---

## 6. Residual risk

- Private material in `docs/artifacts/` is already public git history even if deleted later; deletion is not erasure.
- Tests-not-required means a green “latest Tests run” is not a merge invariant.
- `hummbl-io/hummbl-governance` vs oss package divergence (#48) is unmeasured here.
- Health score 41/100 is a reviewer construct.
- This file, if committed to `main`, becomes another public artifact. It should stay an audit record, not a marketing page. Do not copy C12’s SOC 2 sentence outward.

---

## 7. Recommended next actions (not executed)

1. Remove or rewrite `docs/artifacts/` files that still say `private`; treat remaining public-claim papers under claim-honesty before they stay on `main`.
2. Put SPDX in a GitHub-detectable license file so the badge is not `Other`.
3. Add `ci-ok` (or `Tests`) to required checks; decide whether reviews stay null.
4. Yank or retitle `governed-compression` on PyPI.
5. Strike npm/crates/Maven/Zenodo from CONTRIBUTING until those trees exist.
6. Align SECURITY.md published-package list with PyPI (drop `idp-spec` from the published set).
7. Label or close #80 / #84.

None of the above was done in this session.

---

## 8. Reviewer closeout

| Item | State |
| --- | --- |
| Findings recorded | F1–F16 |
| Claims with 4-field provenance | C1–C28 |
| Telemetry captured | §5 |
| GitHub labels applied | no |
| Commit / push / PR | no |
| Bus post | no (`grok-build` bus inactive) |
| Pre-existing dirty tree | preserved |
| Next owner | operator |
