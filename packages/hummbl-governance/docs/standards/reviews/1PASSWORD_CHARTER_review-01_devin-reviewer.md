# Peer Review 01 — 1Password Operations Charter

**Reviewer profile**: `devin-reviewer` (subagent, read-only tools)
**Reviewer model**: glm-5-2 (free tier)
**Reviewed commits**: `6f1a049` (agy first pass) → `058b426` (Devin revision)
**Review date**: 2026-08-19
**Verdict**: needs changes (not blocked, not merge-ready)

## Tool-surface limitation

The reviewer's provisioned tools were `read`, `grep`, and `find_file_by_name` only — no `exec`/shell. All "verify by running" items are reported as unverified by the reviewer and flagged as requiring the launcher's deterministic git/op evidence or operator-supplied receipts. Findings are from static analysis of the charter text against the repo's governing documents.

## Invalidations (claims demonstrably false from the text itself)

### INV-1 — Tier 1 "Agents may list any vault" contradicts the HUMMBL/Private no-access rule

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:64-65` vs `:167-168`, `:175-176`, `:77-79`
- **Evidence**: Tier 1 stated: *"Agents may list any vault to find the correct item title before retrieving a credential."* The `HUMMBL` and `Private` entries both said *"Agents should not list or read this vault during normal operations."* The audit exception said *"Normal agent operations must not list or read these vaults."*
- **Impact**: An agent reading Tier 1 in isolation is told it may list any vault for discovery — the exact behavior the no-access rule forbids for `HUMMBL`/`Private`. Direct permission conflict.
- **Status**: **FIXED in `f935350`** — Tier 1 now says "agent-accessible vault" and explicitly excludes HUMMBL/Private/empty.

### INV-2 — "There is no pop-up safety net" (headline) vs the biometric caveat (body)

- **Path/line**: `:12` (headline) vs `:18-19` (caveat)
- **Evidence**: Headline: *"There is no pop-up safety net."* Body: *"Biometric approval is required only for initial app unlock and for certain high-sensitivity operations configured in the app's settings."*
- **Impact**: The caveat concedes pop-ups can appear for operator-flagged high-sensitivity items. The absolute headline was false for those items.
- **Status**: **FIXED in `f935350`** — Headline now qualified with "In the common operating state" and adds guidance for when a prompt does appear.

## Inaccuracies

### INA-1 — Vault item counts and contents: unverified

- Counts (api-keys=58, bots=19, infrastructure=16, etc.) asserted, not verified by reviewer (no exec).
- **Status**: Counts were verified by the launcher (Devin) during the original revision via live `op item list` runs. Counts are marked "as of 2026-08-19" snapshots.

### INA-2 — Security-model empirical claim: unverified by reviewer

- The no-pop-up claim is consistent with known 1Password behavior and the prior Devin review's live test, but the reviewer could not independently reproduce it.
- **Status**: Verified by launcher during original revision.

### INA-3 — "Safe: pipe to a file" was not clearly safe, and wrong platform

- The `/tmp/.secret` + `chmod 600` pattern had a TOCTOU/symlink race window and used Unix semantics on a Windows host.
- **Status**: **FIXED in `f935350`** — Removed the temp-file pattern entirely. Added PowerShell equivalents. Added platform note (bash = WSL/Git Bash, PowerShell = native Windows).

### INA-4 — All bash examples assumed Unix; the only provisioned host is Windows

- **Status**: **FIXED in `f935350`** — Added PowerShell equivalents for capture-in-variable and unsafe patterns.

## Gaps

| # | Gap | Status |
|---|---|---|
| GAP-1 | No cross-vault disambiguation guidance | **FIXED** — Directive 4 now includes prefer-by-purpose rule |
| GAP-2 | "Warn operator" had no mechanism | **FIXED** — Directive 3 specifies chat-channel warning with pause |
| GAP-3 | Bus STATUS had no recipient/channel | **FIXED** — Directive 5 specifies `fleet` recipient and full `post` command |
| GAP-4 | No guidance for multiple-match titles | **FIXED** — New "Multiple matches" usage pattern with notes-field disambiguation |
| GAP-5 | No guidance on non-credential fields | **FIXED** — Tier 2 now explicitly covers username/totp/password |
| GAP-6 | Incident response lacks rotation-confirmation closure | **FIXED** — Step 7 added |
| GAP-7 | Empty vaults listed without purpose | **FIXED** — Vault 9 now has per-vault purposes |

## Internal-contradiction check

| Apparent conflict | Reconciles? |
|---|---|
| "None" access for HUMMBL/Private vs audit exception | Yes — audit exception explicitly carves out operator-supervised listing |
| Tier 1 "list any vault" vs HUMMBL/Private no-list | **Was No — fixed in f935350** |
| "no pop-up safety net" vs biometric caveat | **Was No — fixed in f935350** |
| Session Mgmt vs Cross-Machine wording | Mostly yes — minor wording tension |
| `fleet-autonomous-read-prod` "Scoped" tier | **Was undefined — fixed in f935350** (mapped to Low/Restricted) |

## Usage-example safety audit

| Example | Label | Actual safety |
|---|---|---|
| `op run --env-file` | Safe | Safe — best pattern |
| `export VAR=$(op item get ...)` | Safe | Safe — command substitution captures |
| `op item get ... > /tmp/.secret; chmod 600` | Was "Safe" | **Was not safe — removed in f935350** |
| `op item get ... --fields credential` (no pipe) | Unsafe | Correctly unsafe |
| `op item list --vault ... --format json` | Safe (discovery) | Safe — titles only |

## Placement & naming

- The file is the only "Charter" in `docs/standards/` — every other file is a Standard, Audit, Register, Inventory, Doctrine, or Tracking doc.
- `HUMMBL_REPO_STANDARD.md` does not define a "charter" artifact class.
- **Recommendation**: Either rename to `1PASSWORD_OPERATIONS_STANDARD.md`, or create `docs/operations/` or `docs/charters/` + ADR.
- **Status**: Not yet addressed — deferred to operator decision on directory structure convention.

## Commit / provenance / attribution (verified by launcher)

- Commits `6f1a049` and `058b426` exist on `feat/gemini/1password-charter`. **Verified.**
- Diff stat (289 ins / 45 del) matches commit message. **Verified.**
- No AI/vendor attribution in commit messages. **Verified** — `git log` checked for `Co-authored`, `Generated with`, `Generated-by`, `Authored-with`, `Devin`, `devin-ai` — all empty.
- No `[skip ci]` in commit messages. **Verified.**

## Strengths

1. Honest security model — replaced false "every call requires approval" with candid "agent is the last line of defense"
2. Tier 1 / Tier 2 distinction cleanly separates listing from reading
3. Audit exception is explicitly scoped to operator-supervised charter maintenance
4. Incident response is concrete and conservative
5. Circular-dependency callout for 1Password Service Account token
6. SSH-key-in-bots and DCT_SECRET-in-infrastructure notes show real audit care
7. Charter Maintenance section defines re-verification triggers
8. `op run --env-file` as preferred pattern is the safest default

## Recommended changes (prioritized)

| # | Priority | Item | Status |
|---|---|---|---|
| 1 | Block | Fix INV-1: Tier 1 scope | **DONE** |
| 2 | Block | Fix INA-3/INA-4: remove unsafe example, add PowerShell | **DONE** |
| 3 | High | Fix INV-2: soften headline | **DONE** |
| 4 | High | Attach evidence for vault counts | **DONE** (launcher verified) |
| 5 | High | Map "Scoped" to defined tier | **DONE** |
| 6 | Medium | Cross-vault disambiguation | **DONE** |
| 7 | Medium | Specify warn-operator mechanism + bus recipient | **DONE** |
| 8 | Medium | Multiple-match + non-credential fields | **DONE** |
| 9 | Low | Placement/naming | Deferred to operator |
| 10 | Low | Rotation closure + empty vault purposes | **DONE** |
| 11 | Gate | Git attribution/provenance receipts | **DONE** (launcher verified) |

## Gate summary

```
HEADLESS_REVIEW_RESULT
VERDICT: REQUEST_CHANGES (all blocks resolved in f935350)
CODE_GATE: PASS (after f935350)
TEST_GATE: PASS (doc-only)
PROVENANCE_GATE: PASS (launcher-verified)
SIGNATURE_GATE: PASS (launcher-verified)
ATTRIBUTION_GATE: PASS (launcher-verified)
REF_DRIFT_GATE: PASS
END_HEADLESS_REVIEW_RESULT
```
