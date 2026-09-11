# Audit: Public Claims Drift on `hummbl-governance` (2026-09-11)

**Status:** Complete, including a second pass (§8.6) after an independent review caught that ground truth moved mid-audit. Current ground truth: **51 implemented primitives, 58 tracked** (not 45 — see §8.6). Safe, verified fixes applied as uncommitted working-tree changes — not committed or pushed. Operator review required before commit.
**Scope:** `hummbl-io/oss`, primarily `packages/python/hummbl-governance/`, triggered by a flagged Show HN submission and a review of the launch surface (X, Substack, Show HN). Expanded mid-audit (§8.6, operator-directed) to also register 6 GDPR primitives that merged into this branch while the audit was in progress.
**Method:** Every number below was computed from a live source in this session (PrimitiveRegistry import, pytest collection, pyproject.toml/wheel inspection, PyPI API/wheel download) — nothing here is copied from a prior doc without independent verification. Sections 1-8.5 below describe the *first* pass (ground truth: 45/52); §8.6 documents why that ground truth changed and reconciles everything to 51/58. Read §8.6 for the current numbers — sections 1-8.5 are retained for their root-cause analysis, which is still valid, not for their now-superseded counts.

---

## 1. Root cause

`hummbl-governance` has used the number **34** as its headline primitive count
across the package README, `docs/public-claims.md`, and every piece of
external launch copy (Show HN, X thread, Substack). That number is real — it
comes from actual code — but it measures the wrong thing, and the codebase has
grown past it regardless.

**Where 34 actually came from:** two independent, coincidentally-equal counts,
neither of which is "how many primitives are implemented":

1. **The v1.4.2-era doc count.** `docs/public-claims.md` (dated 2026-08-31)
   cites `PRIMITIVES.md` "26 existing plus 8 implemented expansion
   primitives" = 34. This was accurate *at the time*, but `PRIMITIVES.md` has
   since been updated (K12-K14 added 2026-09-02, D7 fix 2026-09-02, and 9
   post-v1.2 primitives P44-P52 backfilled into the doc after the fact — the
   doc itself says these "shipped in v1.3-v1.4 but were not tracked in
   PRIMITIVES.md until this update"). The ledger was never refreshed after
   that doc update.
2. **The registry's `governance_primitives()` count.** The actual current
   `PrimitiveRegistry().governance_primitives()` (primitives that enforce at
   least one kernel/doctrine invariant, excluding infrastructure primitives
   like `ComplianceMapper` or `StrideMapper`) computed to 34 *before* the fix
   in §2 below. This is a real, narrower technical subset that happens to
   collide numerically with the older count. The README's own prose lists
   `compliance_mapper` as an example of a "governance primitive," which is
   actually classified as infrastructure (no invariant) — so even this
   reading doesn't match how the term is used in prose.

**Ground truth**, per `PRIMITIVES.md`'s own header ("Total implemented: 45")
and now confirmed by the registry (§2): **45 implemented primitives**, out of
**52 tracked** (45 implemented + 4 proposed/not-started + 3 candidate).

This is not a first occurrence. `docs/artifacts/CASE_STUDY_claims_remediation.md`
already documents an earlier instance of the same bug class: "'25 Modules' —
wrong number. The homepage claimed 25 modules. The actual count was 26
primitives (or 49 modules, depending on how you count)." The fix in §4 targets
the pattern, not just this one instance.

## 2. Code bug found: registry disagreed with its own canonical doc

`hummbl_governance/primitive_registry.py` — which its own docstring calls
"the authoritative runtime source" that "mirrors PRIMITIVES.md" — had **P35
(RegulatorExport)** marked `PrimitiveStatus.NOT_STARTED`, with module path
`kernel.regulator_export`.

`PRIMITIVES.md` (the doc the registry is supposed to mirror) marks P35
"✅ Implemented (7 formats, 8 frameworks, 40 tests)". I verified this against
the filesystem directly:

```
hummbl_governance/regulator_export.py            (exists)
hummbl_governance/data/regulator_export.schema.json  (exists)
tests/test_regulator_export.py                   (exists, real test file)
```

The module also isn't under `kernel/` — it's top-level, matching
`PRIMITIVES.md`'s module column (`regulator_export.py`), not the registry's
`kernel.regulator_export`.

**Fixed** (uncommitted): `primitive_registry.py` now marks P35
`IMPLEMENTED`, module `regulator_export`, and `enforced_invariants=("D5",)`
per `PRIMITIVES.md`'s invariant column. `implemented_primitives()` count moved
44 → 45, now matching `PRIMITIVES.md`'s own header. 19 existing registry tests
still pass (`tests/test_primitive_registry.py`, 19 passed, 0 failed).

## 3. hummbl-bus license: tree and shipped wheel disagree, at the same version

Not part of the primitive-count bug, but found during the review and worth
flagging since the launch copy makes a licensing claim:

- Tree `packages/python/hummbl-bus/pyproject.toml`: `license = {text =
  "Apache-2.0"}`.
- Live PyPI wheel `hummbl_bus-0.2.0-py3-none-any.whl` `METADATA`:
  `License: MIT`, while bundling `License-File: LICENSE`,
  `License-File: LICENSE-APACHE`, **and** `License-File: LICENSE-MIT`.

Both are at version **0.2.0** — this isn't a "tree is ahead of the last
release" situation like `hummbl-governance` (1.5.0 tree / 1.4.2 live). The
same version number carries two different single-license declarations, and
neither is the `MIT OR Apache-2.0` SPDX expression that shipping all three
license files would suggest. **Not fixed here** — this needs an operator
decision (which license is actually intended for `hummbl-bus`?) before either
the tree or a re-release is changed. Flagged as a follow-up in §7.

## 4. Fix: root cause vs. patch

Per the constraint you gave — marketing must conform to implementation and
evidence, not the reverse — the fix has two layers:

1. **Patch the current wrong numbers** (§5) to match verified ground truth.
2. **Make the specific number un-copyable-wrong going forward** for the two
   counts that are purely computable from files already in this repo
   (implemented-primitive count, Python package count). See
   `scripts/check_public_count_claims.py` (new file, §6).

I deliberately did *not* extend `scripts/claim_drift.py`. That script already
exists and does something different by design: it flags risky *wording*
patterns via regex heuristics (superlatives, uncited compliance claims) and
git-diff nudges to "go check this file." It has no notion of ground truth to
compare against — its own pattern list
(`\d{2,7}\s+(?:tests|modules|features|checks|claims|verifications)`) doesn't
even include the word "primitives," so it would never have caught this class
of bug. Bolting exact-match verification onto a fuzzy-heuristic tool would
make both jobs worse. The new script is intentionally separate and small.

## 5. Canonical facts table (2026-09-11, computed live)

| Fact | Value | How it was computed | Do not use |
|---|---|---|---|
| Implemented primitives | **45** | `PrimitiveRegistry().implemented_primitives()` after the P35 fix; matches `PRIMITIVES.md` header. | 34 (see §1), 51 (not sourced from anything found in-repo) |
| Primitives tracked total | **52** | `len(PrimitiveRegistry().all_primitives())` = 45 implemented + 4 proposed/not-started (P32, P33, P39, P40) + 3 candidate (P41-P43) | — |
| Governance (invariant-enforcing) primitives | **35** | `PrimitiveRegistry().governance_primitives()` post-fix (was 34 pre-fix) | Do not call this "total primitives" — it excludes 17 infrastructure primitives (`ComplianceMapper`, `StrideMapper`, `ReasoningEngine`, etc.) that the README's own prose lists as examples of "governance primitives" |
| Runtime dependency status | **Zero third-party runtime deps** | `pyproject.toml`: `dependencies = []`. Verified independently this morning via the published wheel's METADATA too. | — |
| Package version in tree | **1.5.0** | `packages/python/hummbl-governance/pyproject.toml` `version = "1.5.0"` | `PRIMITIVES.md` said "v1.4.1" before this audit — fixed |
| Currently released PyPI version | **1.4.2** | Root `README.md`'s own package table: "Live 1.4.2 — tree 1.5.0 remains unreleased" | Do not state the tree version as "what `pip install` gives you" |
| Supported Python versions | **>=3.11** (classifiers list 3.11, 3.12, 3.13) | `pyproject.toml` | Public CI (see next row) covers less than the classifiers claim |
| Public oss CI coverage | **3.13 only**, no coverage collected (GAP-003, already documented in `docs/public-claims.md`) | `.github/workflows/ci.yml` | Do not claim a public 3.11-3.13 matrix |
| Tests (local collection, 2026-09-11) | **3,392 collected** | `python -m pytest tests/ --collect-only -q`, this session | This is a *collected*, not *passing*, count, and it is a local number — per `docs/public-claims.md`'s own existing policy, local counts must not be promoted as the public test-count claim. The public receipt is the CI run below, which is stale. |
| Public oss CI test result (last known) | **2,463 passed, 3 skipped** | `docs/public-claims.md`, [run 32904924444](https://github.com/hummbl-io/oss/actions/runs/32904924444) | This run predates the P44-P52 / K12-K14 additions (3,392 now collectable vs. 2,463 then). Stale — a fresh CI run is the correct fix, not a hand-edited number. See §7. |
| Python packages in monorepo | **46** | Verified two ways: `find packages/python -maxdepth 1 -type d` minus the untracked `_state/` dir, and counting directories containing a `pyproject.toml` — both give 46 | Accurate as of this audit; already correct in root `README.md` |
| Packages live on PyPI | **9** | Root `README.md`'s own package table, "Live" column: `hummbl-governance`, `base120`, `hummbl-bus`, `hummbl-cognition`, `hummbl-tuples`, `hummbl-bif`, `governed-compression`, `hummbl`, `hummbl-kernel` | Accurate as of this audit; already correct in launch copy |
| License (`hummbl-governance` specifically) | **Apache-2.0** (single, not dual) | `pyproject.toml`, LICENSE file, wheel METADATA all agree | — |
| License (repo root / other packages) | **Dual MIT OR Apache-2.0 at repo level**, but individual packages vary — see §3 for `hummbl-bus`'s unresolved mismatch | Root `README.md`: "Individual packages ship under Apache-2.0 or 'MIT OR Apache-2.0'" | Do not assume every package is dual-licensed; check per-package |
| Security/provenance claims actually enforced | Sigstore signing, GitHub build-provenance attestation, CycloneDX SBOM, hash-locked build env with `pip --require-hashes`, PyPI trusted publishing (OIDC) | Root `README.md` "Verify a release" section, describes a real, checkable workflow (`publish-pypi.yml`) with a documented verification command (`gh attestation verify`) | Did not independently re-run `gh attestation verify` in this session; the workflow's existence and the verification command are documented and match repo conventions, but I have not personally executed a fresh attestation check |

## 6. Drift-prevention mechanism (implemented, low-risk)

New file: `packages/python/hummbl-governance/scripts/check_public_count_claims.py`

- Computes implemented-primitive count from `PrimitiveRegistry` and Python
  package count from the `packages/python/` tree — both purely local,
  deterministic, no network access.
- Scans `README.md`, `PRIMITIVES.md`, and `docs/public-claims.md` (governance
  package) plus the root `README.md` for known phrasings of these counts and
  fails closed (exit 1) on any mismatch, printing expected-vs-found with file
  and line number.
- Does **not** attempt to verify test-pass counts or PyPI-live status — those
  need an external receipt (a CI run, a PyPI API call), and
  `docs/public-claims.md` already has an explicit, correct policy that local
  counts must not stand in for that receipt. Extending this script to those
  would either require network calls in a doc-consistency check (fragile) or
  reimplement what `docs/public-claims.md`'s existing promotion-gate process
  already does by hand. Left as a process, not automated further, on purpose.
- Verified working: ran clean (0 mismatches) after the §5 fixes were applied,
  against the actual current tree.

**Not done:** wiring this into `.github/workflows/ci.yml`. That's a protected,
higher-blast-radius file and I did not want to touch CI workflow definitions
without you looking at it first. Recommended addition (one step, after the
existing test job):

```yaml
- name: Check public count claims
  run: python packages/python/hummbl-governance/scripts/check_public_count_claims.py
```

## 7. Follow-up issues (too large for this pass)

1. **Refresh public oss CI.** The 2,463-passed/3-skipped receipt predates
   P44-P52/K12-K14 (3,392 tests now collectable locally). Trigger a fresh CI
   run, update `docs/public-claims.md`'s receipt (run ID, commit, counts),
   and update the README badge. This is an external-receipt update, not a
   text edit — do not hand-edit the badge number without a real run.
2. **Refresh `landing-claims.json`** (hummbl.io, outside this repo). Still
   says 34; the Metric Scope Table in `docs/public-claims.md` now flags this
   row as stale pending that external update.
3. **Resolve the `hummbl-bus` license mismatch** (§3) — operator decision
   needed on intended license, then either fix the tree pyproject or cut a
   re-release with corrected METADATA.
4. **Decide whether to wire `check_public_count_claims.py` into CI** (§6).
5. **Consider extending the "Expansion & Post-v1.2 Primitives" table pattern**
   used in the governance README fix (§5) to be *generated* from
   `PrimitiveRegistry` rather than hand-maintained markdown, the same way the
   count itself now has a generated check. Not done here — the current fix
   hand-transcribes from `PRIMITIVES.md` (low error risk, since both sources
   were open side-by-side during the edit and the count-check script would
   catch a total-count regression), but a generator would remove the
   hand-transcription step entirely for future primitive additions.

## 8. Impact on already-published launch copy

Checked against the local working copies of the launch materials
(`_internal/public-launch/` on this machine, not this repo):

- **`SHOW_HN.md`** — said "34 primitives total"; superseded (§9 below has
  revised copy; not reposted, per your instruction).
- **`X_THREAD.md`** — tweet 7 said "34 governance primitives:" followed by an
  8-item bullet list (not all 45, understandably — a tweet can't list them
  all). The live-published tweet cannot be silently edited; flagging for your
  awareness, not touching it. If you want a correction, X allows editing a
  posted tweet for a window — that's your call, not something I'll do
  unprompted.
- **`SUBSTACK.md`** — same "34 primitives total" line, already **live and
  published**. Same as above: flagging, not silently editing a published
  post. Substack does support post-publish edits; whether to make one is
  your call.

None of the three already-published posts were modified. Only local
unpublished drafts and repo files were changed.

## 8.5 Self-review addendum (2026-09-11, post-draft)

Before handoff to independent review, I re-ran every check cold (no cached
state, no manual argument overrides) and found three real defects introduced
by this pass itself. All three are fixed as of this addendum:

1. **`check_public_count_claims.py` had an off-by-one path bug.** The default
   `--repo-root` was `Path(__file__).resolve().parents[3]`, which resolves to
   `packages/`, not the oss root — `parents[4]` is correct
   (`scripts→hummbl-governance→python→packages→oss`). Run with no arguments
   (the way anyone, including a future CI step, would actually invoke it),
   this failed with `ModuleNotFoundError: No module named
   'hummbl_governance.primitive_registry'` rather than silently succeeding,
   because the bad path caused Python to fall through to a **different**
   `hummbl_governance` package already on `sys.path`: a globally pip-installed
   `hummbl-governance==1.4.2` at
   `C:\ProgramData\hummbl\python\Lib\site-packages\`. My earlier "verified
   working" claim in §5/§6 was true but incomplete — that test passed an
   explicit `--repo-root` override, which bypassed the buggy default path
   entirely and never exercised the codepath a real invocation would use.
   Fixed (`parents[3]` → `parents[4]`); confirmed the script now imports
   `packages/python/hummbl-governance/hummbl_governance/primitive_registry.py`
   (the tree file, not the installed package) and reports 45/46/clean.
2. **README.md's new P27 row had the wrong invariant.** I wrote `—` for
   P27's Invariant column; both `PRIMITIVES.md` (line 147, "D5") and the
   registry (`enforced_invariants=("D5",)`) say D5. Fixed.
3. **`docs/public-claims.md`'s header and the "Package version" claim row
   still said `pyproject.toml` was `1.4.2`** after I had already updated the
   Metric Scope Table three lines below to correctly show tree=1.5.0 /
   PyPI-live=1.4.2 — an internal inconsistency within the exact file whose
   job is to prevent this class of drift. Reworded both to distinguish
   tree-current (1.5.0, unreleased) from PyPI-live (1.4.2), and separately
   re-verified `dependencies = []` still holds at 1.5.0 (it does) before
   updating that claim row's receipt text too.

All three fixes are included in the diffs already described above (this
addendum documents the finding, not a separate patch). Re-ran after fixing:
`check_public_count_claims.py` → clean; `pytest tests/test_primitive_registry.py -q`
→ 19 passed.

**Not yet independently reviewed as of this addendum**: everything above was
caught by the author (me) re-checking my own work, which is useful but is
explicitly *not* sufficient per this repo's own `claim-honesty-protocol.md`
§8 (anti-self-review — the author of a claim-emitting artifact cannot also be
its sole reviewer, and a same-session sub-agent dispatched by the author does
not count as independent either). Non-author review is the next step.

## 8.6 Second pass: ground truth moved mid-audit (45 → 51)

An independent, non-author subagent review (dispatched after §8.5's self-review) was asked to re-derive every number from scratch rather than trust this document. It found something the self-review couldn't have: **`PRIMITIVES.md` on disk no longer said what this document quoted it as saying.** Its header now read "Total implemented: 51 (...P44-P58)" — not 45 — and it flagged the "45" quote in §5/§8.5 as effectively fabricated.

It wasn't fabricated when written; the ground moved during the review window. Investigation traced the cause:

1. **The working tree's branch changed underneath the audit.** At some point after §1-8.5 were written (against `main`), this local checkout (`C:\Users\Owner\PROJECTS\oss` — a shared machine, not exclusive to this session) ended up on `feat/docker-ci-image`, a branch another agent (Devin, per commit trailers and bus activity) is actively using for unrelated Docker CI work. That branch had been rebased onto a newer `origin/main`.
2. **That newer `origin/main` includes PR #220** (`607ccdc`, merged 2026-09-11, authored by the operator + Devin): *"fix(ci): pypi tracker branch switch + GDPR governance primitives (P53-P58) (#220)."* It added 6 real, tested primitive modules — `human_review_gate.py` (P53), `contestation_handler.py` (P54), `dsar_handler.py` (P55), `redaction_engine.py` (P56), `records_of_processing.py` (P57), `dpia_generator.py` (P58) — implementing GDPR Art. 15/17/21/22/30/35 controls, with 103 passing tests, and updated `PRIMITIVES.md`'s header and category tables to say 51/58.
3. **But PR #220 never added corresponding entries to `primitive_registry.py`** — the same "authoritative runtime source, doc says X, registry says Y" bug class this whole audit exists to catch, this time in an already-merged commit unrelated to anything in §1-8.5. Confirmed: `git log -- primitive_registry.py` showed no commit touching it since `760d304`, well before PR #220; a fresh import of the registry after the branch moved computed 45, not 51, while `PRIMITIVES.md` said 51.
4. **`PRIMITIVES.md` was also internally incomplete**, independent of the registry gap: its per-primitive reference table under "Implemented post-v1.2" still only listed P44-P52 (9 rows) even though the section header above it and the file's summary header both already said "P44-P58" / "51 implemented."

Per operator direction (2026-09-11), scope was expanded to fix this rather than route around it, on the same branch:

- Read all 6 new modules; confirmed via their own docstrings (`human_review_gate.py` line 17 states "Human Review Gate (P53)", etc.) which P-ID maps to which class, and confirmed each has a real test file (`tests/test_*.py`, 103 tests total, all passing: `pytest tests/test_human_review_gate.py tests/test_contestation_handler.py tests/test_dsar_handler.py tests/test_redaction_engine.py tests/test_records_of_processing.py tests/test_dpia_generator.py -q` → 103 passed).
- Added 6 `PrimitiveEntry` objects to `primitive_registry.py` (P53-P58). Family codes derived from the next free slot per family in the existing registry (`_fc("GE", 4)`, `_fc("GE", 5)`, `_fc("AC", 7)`, `_fc("AC", 8)`, `_fc("AC", 9)`, `_fc("RM", 2)`) — cross-checked against `PRIMITIVES.md`'s own category table, which already assigned P53/P54 to Governance Ecology, P55/P56/P57 to Audit & Compliance, and P58 to Risk Management. `records_of_processing.py`'s own docstring claimed "Family: AC-6", which collides with P35's already-assigned AC-6 — that was a docstring error in the merged PR; corrected to AC-9 (the actually-assigned code) as a one-line fix.
- **Invariant assignment (K1) is a judgment call, not a doc-sourced fact** — `PRIMITIVES.md`'s post-v1.2 table has no Invariant column, so unlike the P35 fix there was no existing textual assignment to verify against. K1 (RECEIPT) was assigned to P53-P56 because each produces its own hash/HMAC-signed receipt or record class (`HumanReviewGateReceipt`, `ContestationRecord`, `DSARRecord`, `RedactionReceipt` — confirmed via `hashlib`/`hmac` usage and dedicated receipt classes in each module), matching the same pattern already used for P51 `TransitionReceipt` and P52 `ToolAudit` in this same registry. P57 and P58 were left with no enforced invariant (Infrastructure layer, matching P47 `CorpusAdapter`'s precedent) because both modules explicitly self-describe as stateless assemblers/formatters that query other primitives' evidence rather than producing their own. **This is the one part of this pass that is inference from code pattern, not a verified doc citation — flagged for Devin/operator review, not asserted as settled.**
- Expanded `PRIMITIVES.md`'s post-v1.2 table to include the 6 missing rows; updated its heading (P44-P52 → P44-P58), the "Note" line, and the Organizational Layers table (added P53-P56 to Evidence, P57-P58 to Infrastructure).
- Updated `README.md`, `docs/public-claims.md`, and `SHOW_HN_REVISED.md` throughout: 45 → 51 implemented, 52 → 58 tracked, local test collection 3,392 → 3,495 (recounted live, `pytest --collect-only -q`), "Expansion & Post-v1.2 Primitives (19)" table → (25), added 6 rows.
- Re-ran `scripts/check_public_count_claims.py` (clean: `implemented_primitives: ground truth = 51`) and `pytest tests/test_primitive_registry.py -q` (19 passed) after every change in this section.

**Not done, deliberately out of scope of this audit:**
- No changes to Devin's own Docker CI work on this branch (`Dockerfile`, `.dockerignore`, the `docker-test` CI job) — untouched, unrelated.
- No attempt to determine why PR #220 shipped with this registry gap, or to add process/CI enforcement preventing a repeat (that's exactly what `check_public_count_claims.py` now does going forward for anyone who runs it, but it isn't wired into CI — see §7 follow-up #4, now more urgent given this is the second real instance of the same bug class in one day).
- The K1 invariant assignments for P53-P56 (above) are not independently re-verified beyond the reasoning stated — flagged explicitly for the pending Devin/subagent review rather than presented as fully settled.

**Ground truth as of this section (re-verified live, final check of this pass):**
`implemented_primitives()` = 51, `governance_primitives()` = 39, `all_primitives()` = 58 (51 implemented + 4 proposed + 3 candidate). 46 Python packages (unchanged). `check_public_count_claims.py` clean. `pytest tests/test_primitive_registry.py -q` → 19 passed.

## 9. Receipts

**Commands run this session (all read-only except the four working-tree edits
and one new file, none committed):**

```bash
git -C oss status --short --branch          # clean, up to date with origin/main, before edits
git -C oss remote -v                        # confirmed hummbl-io/oss
python -m pytest tests/ --collect-only -q   # 3,392 tests collected
python -m pytest tests/test_primitive_registry.py -q  # 19 passed, 0 failed (after P35 fix)
python -c "PrimitiveRegistry() ... "        # computed all counts in §5, before and after fix
curl https://pypi.org/pypi/hummbl-bus/json  # license: MIT, version 0.2.0
curl (wheel download) + zipfile inspection  # confirmed METADATA License: MIT, 3 License-File entries
find packages/python -maxdepth 1 -type d    # 47 dirs, 46 excluding untracked _state/
grep -rn "34.*primitiv" **/*.md             # located every stale occurrence before fixing
python packages/python/hummbl-governance/scripts/check_public_count_claims.py  # clean pass after fixes
```

**Files changed (uncommitted, working tree only):**

```
M  packages/python/hummbl-governance/hummbl_governance/primitive_registry.py
M  packages/python/hummbl-governance/hummbl_governance/records_of_processing.py
M  packages/python/hummbl-governance/PRIMITIVES.md
M  packages/python/hummbl-governance/README.md
M  packages/python/hummbl-governance/docs/public-claims.md
A  packages/python/hummbl-governance/scripts/check_public_count_claims.py
A  docs/artifacts/AUDIT_2026-09-11_public_claims_drift.md   (this file)
```

Also modified, outside `hummbl-io/oss`: `C:\Users\Owner\PROJECTS\_internal\public-launch\SHOW_HN_REVISED.md`
(local file, not part of this repo, not published anywhere).

Note: this checkout is currently on `feat/docker-ci-image`, not `main` — see
§8.6. That branch also carries Devin's own commits (Dockerfile/CI work,
unrelated to and untouched by this audit); `git diff` on the files above
shows only the changes described in this document.

**Not touched:** `.github/workflows/ci.yml`, `landing-claims.json` (external),
any already-published social copy, `hummbl-bus`'s license, Devin's Docker CI
commits on this branch, git history, git remote, anything requiring a commit
or push. Per `agent-commit-authority.md`, none of this is committed — you
didn't ask me to commit, so this stays as a
reviewable diff until you say otherwise.

**Unresolved assumptions:**

- I'm treating `PRIMITIVES.md`'s "Total implemented: 45" as the correct
  ground truth (per your instruction to treat the repo as canonical) and
  fixed the registry code to match it, rather than the other direction. If
  P35's actual implementation status is contested for a reason I don't know
  about, that assumption should be checked.
- I have not re-run the full 3,392-test suite (only collected it and ran the
  19 registry-specific tests) — collection succeeding is not the same as the
  suite passing, though the P35 change only touches static metadata (status
  enum, string fields) with no behavioral logic, so the blast radius of that
  specific edit is small.
