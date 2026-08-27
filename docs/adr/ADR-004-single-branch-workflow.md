# ADR-004 — Single-Branch Workflow for Artifact Stack Buildout

- **Status:** accepted
- **Date:** 2026-06-23
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** none (process ADR)
- **Retrospective:** `docs/artifacts/RETROSPECTIVE_wave_3.md` (F10, P12)

## Context

The artifact stack buildout (waves 1-3, days 1-19) used a two-branch workflow:

1. **Fix branch** (`fix/claude/gitops-cleanup-from-april-audit`) — the working branch where artifacts were drafted, committed, and KRINEIA receipts emitted
2. **Wave branch** (`feat/devin/artifact-stack-wave-1`) — the integration branch where commits were cherry-picked for PR review

The `promote_to_wave_branch.sh` script automated the cherry-pick: stash, checkout wave branch, cherry-pick, push, checkout fix branch, pop stash.

### The problem (F10)

Wave 3 (days 15-19) hit a recurring friction point: **cherry-pick conflicts on `_receipts/krineia/primary.jsonl`**. The receipt file is append-only JSONL. Both branches append different receipts. When cherry-picking a Day N commit from the fix branch to the wave branch, git cannot auto-merge the appended lines — both branches modified the file, and the lines are different.

This required manual conflict resolution (`git checkout --theirs _receipts/krineia/primary.jsonl`) on days 17, 18, and 19. Each resolution added ~5 minutes to the cycle. Wave 3 missed its cycle time target (20-25 min actual vs 15-20 min target) primarily due to F10.

### Root cause

The two-branch workflow was inherited from the april-audit cleanup. The fix branch was created for the april-audit work; the artifact stack buildout was added on top. The two efforts have different goals (audit cleanup vs artifact production) but share the same repository. The cherry-pick workflow was a workaround for committing to two branches simultaneously.

The artifact stack buildout does not need the fix branch. It needs a single branch where artifacts are committed, receipts are emitted, and PRs are opened. The fix branch is for the april-audit cleanup; the artifact stack work is on the wave branch.

### What F10 cost

- 3 of 5 wave 3 days had cherry-pick conflicts (days 17, 18, 19)
- ~5 min per conflict resolution
- Cycle time target missed (20-25 min vs 15-20 min target)
- Manual steps target missed (5-7 vs 4 target)
- Promote script first-try success: 2/5 (target 4/4)

## Decision

**Adopt a single-branch workflow for the artifact stack buildout. Commit directly to the wave branch. Stop using the fix branch for artifact stack work.**

### Scope

This ADR applies to:
- All future artifact stack buildout waves (wave 4+)
- All future artifact drafting, claims addition, receipt emission, and manifest updates
- All future ADRs, playbooks, position papers, and other artifacts

### Out of scope

- The april-audit cleanup continues on the fix branch
- The `promote_to_wave_branch.sh` script is retained for cases where a two-branch workflow is genuinely needed (e.g., backporting a fix to multiple release branches)
- The fix branch's existing commits (days 1-19) are not rebased or moved

### Workflow

The new workflow (wave 4+):

1. **Checkout the wave branch**: `git checkout feat/devin/artifact-stack-wave-1`
2. **Draft the artifact** (using the template and helper scripts)
3. **Add claims**: `python scripts/add_claims.py <claims.json>`
4. **Update the manifest**: `python scripts/update_manifest.py <item> <status> <note>`
5. **Emit the KRINEIA receipt**: `python scripts/emit_receipt.py governance.artifact_promoted <payload.json>`
6. **Commit**: `git add <files> && git commit -F <msg.txt>`
7. **Push**: `git push`

No cherry-pick. No stash. No promote script. No conflict resolution.

### What this eliminates

- F10 (cherry-pick receipt file conflicts) — eliminated entirely
- F11 (stash pop conflicts with untracked files) — eliminated (no stash needed)
- The promote script's stash/checkout/cherry-pick/checkout/pop cycle — eliminated

### What this preserves

- The KRINEIA receipt chain (still append-only, still hash-linked)
- The claims manifest (still validated by P7)
- The artifact manifest (still validated by P11)
- The artifact template and helper scripts (still used)
- The wave retrospective (still produced at the end of each wave)

## Alternatives considered

### Alternative 1: Merge strategy that always takes the longer receipt file

**What:** Configure git to always take the version of `_receipts/krineia/primary.jsonl` with more lines (more receipts = more recent state).

**Why rejected:** This requires a custom merge driver. It's fragile (what if both branches add the same receipt?). It doesn't solve F11 (stash pop conflicts). It adds complexity for a problem that the single-branch workflow eliminates entirely.

### Alternative 2: Move the receipt file to a separate branch

**What:** Keep receipts on a separate `receipts` branch; cherry-pick receipt commits separately.

**Why rejected:** This adds a third branch to the workflow. It complicates the KRINEIA chain verification (which branch is the source of truth?). It doesn't solve the fundamental problem (committing to two branches).

### Alternative 3: Continue the two-branch workflow with manual conflict resolution

**What:** Keep the fix branch + wave branch workflow; accept the ~5 min conflict resolution cost per artifact.

**Why rejected:** The cost compounds. At 5 artifacts per wave, that's 25 min per wave. Over 10 waves, that's 250 min (4+ hours) of wasted conflict resolution. The single-branch workflow eliminates this cost entirely.

## Consequences

### Positive

- F10 eliminated entirely (no cherry-pick, no conflict)
- F11 eliminated entirely (no stash, no pop)
- Cycle time target (15-20 min) achievable
- Manual steps target (4) achievable
- Promote script no longer needed for artifact stack work
- Simpler mental model: one branch, one workflow

### Negative

- The fix branch and wave branch diverge over time (the fix branch has the april-audit work; the wave branch has the artifact stack work). This is acceptable — the two efforts have different goals and will merge to main independently.
- The `promote_to_wave_branch.sh` script's F7 fix (resolve HEAD to concrete SHA before checkout) is no longer exercised by the artifact stack work. The script is retained for other use cases but may regress if not tested.

### Neutral

- The wave branch becomes the single source of truth for the artifact stack. The fix branch is no longer a source of truth for artifacts.
- The KRINEIA receipt chain on the wave branch is the canonical chain. The fix branch's chain is a historical artifact (it has the same receipts up to day 19, but no future receipts).

## Verification

A reader can verify this ADR is in effect by:

1. `git log --oneline feat/devin/artifact-stack-wave-1 | head -5` — wave 4+ commits should be directly on the wave branch (no cherry-pick messages)
2. `git log --oneline fix/claude/gitops-cleanup-from-april-audit | head -5` — the fix branch should not have wave 4+ artifact commits
3. `python scripts/validate_claims.py` — the claims manifest should pass P7 validation
4. `python scripts/validate_manifest.py` — the artifact manifest should pass P11 validation
5. `python3 -c "import json, hashlib; ..."` — the KRINEIA chain should be intact on the wave branch

## References

- Wave 3 retrospective: `docs/artifacts/RETROSPECTIVE_wave_3.md` (F10, P12)
- Wave 2 retrospective: `docs/artifacts/RETROSPECTIVE_wave_2.md` (F7, promote script fix)
- Promote script: `scripts/promote_to_wave_branch.sh`
- Claims validation CI: `.github/workflows/claims-validation.yml` (P7)
- Manifest validation CI: `.github/workflows/manifest-validation.yml` (P11)
- Artifact template: `docs/artifacts/TEMPLATE.md`
- Helper scripts: `scripts/add_claims.py`, `scripts/emit_receipt.py`, `scripts/update_manifest.py`
- ADR-001: `docs/adr/ADR-001-repo-governance-baseline.md` (repo governance baseline)
- ADR-002: `docs/adr/ADR-002-issueops-teaching-surface.md` (IssueOps decision)
- ADR-003: `docs/adr/ADR-003-game-engine-roadmap.md` (game engine decision)

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This ADR was drafted by Devin at the direction of the Principal Agent, based on the wave 3 retrospective (F10, P12) and the cycle time data, and was accepted by Principal Agent decision on 2026-06-23. This ADR is **public** — it documents a process decision that affects how the artifact stack is built, and is published for transparency.
