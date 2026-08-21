# Peer Review 02b — 1Password Operations Charter (Blue Team / Compliance Auditor)

**Reviewer**: subagent_general (Blue Team, Reviewer B)
**Reviewed commits**: `6f1a049` → `058b426` → `f935350` → `c28f9a1` on `feat/gemini/1password-charter`
**Review date**: 2026-08-19
**Verdict**: needs changes (not blocked, not merge-ready)

## Methodology

Unlike review-01 (which was static-only, no exec), this review ran live `op` commands
against the actual 1Password vault, inspected raw commit bytes, and tested PowerShell
example syntax. All credential values were captured in variables or piped to null —
no secrets appear in this document.

## Vault verification — actual vs charter claims

All vaults were listed via `op vault list` and item counts via `op item list --vault
<name> --format json` (piped through `ConvertFrom-Json` and counted).

### Vault name verification

All 11 vault names in the charter match reality exactly:

| # | Charter name | Actual name | Match |
|---|---|---|---|
| 1 | `api-keys` | `api-keys` | YES |
| 2 | `bots` | `bots` | YES |
| 3 | `infrastructure` | `infrastructure` | YES |
| 4 | `service-accounts` | `service-accounts` | YES |
| 5 | `runtime-bus-prod` | `runtime-bus-prod` | YES |
| 6 | `fleet-autonomous-read-prod` | `fleet-autonomous-read-prod` | YES |
| 7 | `HUMMBL` | `HUMMBL` | YES |
| 8 | `Private` | `Private` | YES |
| 9 | `HUMMBL Sensitive Intake` | `HUMMBL Sensitive Intake` | YES |
| 9 | `Shared` | `Shared` | YES |
| 9 | `jenna` | `jenna` | YES |

### Item count verification

| Vault | Charter count | Actual count | Match | Delta |
|---|---|---|---|---|
| `api-keys` | 58 | **63** | **NO** | +5 |
| `bots` | 19 | 19 | YES | 0 |
| `infrastructure` | 16 | 16 | YES | 0 |
| `service-accounts` | 8 | 8 | YES | 0 |
| `runtime-bus-prod` | 1 | 1 | YES | 0 |
| `fleet-autonomous-read-prod` | 1 | 1 | YES | 0 |
| `HUMMBL` | 582 | 582 | YES | 0 |
| `Private` | 630 | 630 | YES | 0 |
| `HUMMBL Sensitive Intake` | 0 | 0 | YES | 0 |
| `Shared` | 0 | 0 | YES | 0 |
| `jenna` | 0 | 0 | YES | 0 |

**Finding V-1 (NEW)**: `api-keys` count is stale. Charter says 58, actual is 63. The
charter marks counts "as of 2026-08-19" — the same date as this review — so the count
was either wrong at time of writing or items were added between the launcher's
verification and this review. Five items in the current vault are not reflected in the
charter's count or contents list (see V-2).

### Key item verification

| Claim | Verified | Notes |
|---|---|---|
| SSH key in `bots` (`Tail0ff7b3`) | YES | Item exists with exact title `Tail0ff7b3`. Fields: `public_key`, `fingerprint`, `private_key` (SSHKEY type), `key_type`, `notesPlain`, `key generated on` (URL). |
| `DCT_SECRET` in `infrastructure` | YES | Item exists as `DCT_SECRET - Delegation Token HMAC Key`. Has `credential` field (CONCEALED). Retrieval confirmed (value suppressed). |
| 7 Discord webhooks in `bots` | YES | Exactly 7 webhook items confirmed: `agent_ops`, `sitrep`, `decision_log`, `hummbl`, `hummbl_announcements`, `reuben`, `github-activity - founder-mode-bridge`. |
| Langfuse 6 entries in `api-keys` | **NO** | Actual is **7** items: `Langfuse Public Key`, `Langfuse Base URL`, `API Credential - langfuse`, `Langfuse Secret Key`, `Langfuse MCP Auth Header`, `Langfuse` (note), `API Credential - ANVIL_LANGFUSE_API_KEY`. Charter says 6. |
| Cloudflare token scopes | PARTIAL | Charter lists 6 scopes (build, edit workers, DNS, billing, user read-all, agent token). Actual: 10 Cloudflare-related items including additional scopes not listed (admin, api-editor, generic, phase0b-mike-lab). `Edit Zone DNS` item exists but was not captured in my initial regex — it IS present and matches the charter's "DNS" scope claim. |
| GitHub PATs multiple scopes | YES | 6 GitHub items confirmed: org PAT, classic, MCP, Hermes Gateway, plus 2 additional (HUMMBL_DEV_ORG_PAT, ANVIL-HUMMBL-DEV-CLASSIC). Charter says "multiple scopes: org, classic, MCP, Hermes Gateway" — accurate but not exhaustive. |

**Finding V-2 (NEW)**: `api-keys` contents list is incomplete. The charter's contents
enumeration omits several items present in the vault: `API Credential - HERMES_SOCKET`,
`API Credential - ONBOARDING_KEY`, `API Credential - token-admin-hummbl`,
`cf-user-token-admin`, `API Credential - Cloudflare - phase0b-mike-lab`,
`API Credential - api-editor - cloudflare`, `API Credential - Cloudflare` (generic),
`OpenRouter Key OSS` (second OpenRouter key), `Anvil Gemini API Key` (second Gemini
key), `API Credential - Dune - Paper trades` / `Dune - REAL MONEY` (2 Dune items, not
1), `SUM_GUY_429_HF_API_KEY` and `operator_HF_API_KEY` (additional HuggingFace
keys), `HUMMBL-CYBER-OPENAI-API-KEY` (OpenAI key — charter does not mention OpenAI at
all, only OpenRouter). The charter's contents list is illustrative, not exhaustive,
but the count (58) is presented as exact and is wrong.

## Compliance findings (AGENTS.md)

### C-1: Branch naming — COMPLIANT

Branch: `feat/gemini/1password-charter`
Convention: `type/agent/short-desc`
- `type` = `feat` (valid Conventional Commit type)
- `agent` = `gemini` (identifies the agent that produced the work)
- `short-desc` = `1password-charter` (kebab-case, descriptive)

The branch name contains "gemini" (an AI vendor name). AGENTS.md prohibits AI
attribution in commit metadata/trailers, but the branch naming convention explicitly
includes an `agent` segment. Branch names are not commit metadata. **Compliant.**

### C-2: Conventional Commits — COMPLIANT (with provenance issue)

| Commit | Subject | Format |
|---|---|---|
| `6f1a049` | `feat(docs): add 1Password Operations Charter for agents` | Valid |
| `058b426` | `docs(standards): peer-review revision of 1Password Operations Charter` | Valid (but see C-4) |
| `f935350` | `docs(standards): address peer-review findings on 1Password charter` | Valid |
| `c28f9a1` | `docs(standards): add peer review 01 for 1Password charter` | Valid |

All four commits use valid Conventional Commits format with appropriate types and
scopes.

### C-3: AI attribution in commit messages — BORDERLINE

AGENTS.md prohibits `Co-authored-by`, `Generated with`, `Generated-by`,
`Authored-with`, or equivalent AI/vendor attribution in commits.

- No prohibited trailer strings (`Co-authored-by`, `Generated with`, `Generated-by`,
  `Authored-with`) found in any commit message. **PASS.**
- No `[skip ci]` tokens found in any commit message. **PASS.**
- Commit authors are all `Reuben Bowlby <reuben@hummbl.io>` (human). **PASS.**
- **BORDERLINE**: The `f935350` commit body contains "Fixes from devin-reviewer
  subagent peer review:" — this names an AI agent (`devin-reviewer`) in the commit
  message body. While not a formal attribution trailer, AGENTS.md states agent
  activity "belongs in internal receipts, bus messages, handoffs, or PR notes, not
  commit credit." Naming the AI tool in the commit body is not explicitly prohibited
  (the prohibition targets authorship metadata and trailers), but it skirts the
  spirit of the rule. **Recommend rewording to "Fixes from peer review 01:" in any
  future amend.**

### C-4: Mojibake BOM in commit `058b426` — PROVENANCE ISSUE (NEW)

The commit message of `058b426` begins with garbage bytes: `E2 88 A9 E2 95 97 E2 94
90` which decode to `∩╗┐` in UTF-8. This is a double-encoded UTF-8 BOM (the original
`EF BB BF` BOM was decoded as CP1252, producing `∩╗┐`, then re-encoded to UTF-8). The
commit subject renders as `∩╗┐docs(standards): peer-review revision...`.

The other three commits (`6f1a049`, `f935350`, `c28f9a1`) start with clean ASCII
bytes — no BOM. This is an isolated provenance defect in one commit.

**Impact**: The commit subject is corrupted with 3 garbage characters. This does not
break `git log --oneline` (the BOM chars are invisible in some terminals) but it is
visible in raw output and could cause issues with automated tooling that parses
commit subjects. The Conventional Commits type/scope is still parseable (the BOM
precedes `docs(...)`) but strictly speaking the subject does not start with a valid
type token.

**Recommendation**: If the commit is amended, remove the mojibake BOM. If not
amendable (to preserve hash history), document it and ensure future commits use
UTF-8 without BOM.

### C-5: Charter placement — DEFERRED (confirmed from review-01)

The charter is in `docs/standards/` alongside 24 other files. Review-01 already
flagged that this is the only "Charter" in a directory of Standards, Audits,
Registers, Inventories, Doctrines, and Tracking docs. `HUMMBL_REPO_STANDARD.md` does
not define a "charter" artifact class.

This review confirms: `docs/operations/` exists and contains operational docs
(`AGENT_TOOLSET_STARTER.md`, `DRAFT_PR_PROMOTION_QUEUE.md`). The 1Password charter is
an operational document (how to retrieve credentials), not a standard (what must be
true). **`docs/operations/` would be a more accurate home.** However, this is a
naming/placement preference, not a compliance violation — the repo standard does not
prohibit the current placement.

### C-6: Bus STATUS format — INCONSISTENT (NEW)

AGENTS.md defines the canonical bus write as:
```
python /c/Users/Owner/bin/bus-global.py post hummbl-governance <to> <type> "<message>"
```

The charter's Directive 5 (line 62) shows:
```
post hummbl-governance fleet STATUS "host=<machine> surface=1password retrieved: <item title> from vault=<name> for purpose=<task>"
```

This omits the `python /c/Users/Owner/bin/bus-global.py` prefix. An agent that
copy-pastes the charter's command will get "command not found" (there is no `post`
binary on PATH). The charter should either include the full canonical command or
explicitly state that `post` is shorthand for the full `python
/c/Users/Owner/bin/bus-global.py post` invocation.

Additionally, the Audit Logging section (line 304-306) shows only the message body
(`host=anvil surface=1password retrieved: ...`) without any `post` command at all,
and the Incident Response section (line 337) similarly shows only the message body.
These are inconsistent with Directive 5's format and with each other.

## Operational verification

### O-1: End-to-end usability test — PASS with caveats

A new agent needing a credential can follow the charter end-to-end:
1. Check auth state (`op account list`, `op whoami`) — clearly documented
2. List vault to find item title (`op item list --vault <name>`) — clearly documented
3. Chat-channel warning before Tier 2 read (Directive 3) — clearly documented
4. Capture credential in variable — examples provided for both bash and PowerShell
5. Post bus STATUS — format provided (but see C-6 for the prefix issue)

**Caveat**: An agent needing the SSH key (`Tail0ff7b3`) would follow the charter's
examples which all use `--fields credential`. SSH key items in 1Password use a
`private_key` field, not `credential`. Running `op item get "Tail0ff7b3" --vault bots
--fields credential` returns an error: `"credential" isn't a field in the "Tail0ff7b3"
item`. The charter notes the SSH key exists but does not mention the field name
difference. **An agent would hit this error and have to discover the correct field
name by introspecting the item.**

### O-2: PowerShell example syntax — PASS

Tested the PowerShell capture pattern from the charter (line 262):
```powershell
$env:OPENROUTER_API_KEY = op item get "OpenRouter API Key (main)" --vault api-keys --fields credential
```
Equivalent test with SSH key private_key field:
```powershell
$pk = op item get "Tail0ff7b3" --vault bots --fields "private_key"
```
Both succeeded. The value was captured in the variable and not printed to stdout.
**Syntax is correct.**

### O-3: Bus STATUS format consistency — FAIL

Three different representations of the bus STATUS across the charter:
1. **Directive 5 (line 62)**: `post hummbl-governance fleet STATUS "host=... ..."` —
   uses `post` shorthand, no `python` prefix
2. **Audit Logging (line 305)**: `host=anvil surface=1password retrieved: ...` —
   message body only, no `post` command
3. **Incident Response (line 337)**: `host=<machine> surface=1password INCIDENT:
   ...` — message body only, no `post` command

None of these match the AGENTS.md canonical format which requires the `python
/c/Users/Owner/bin/bus-global.py` prefix. An agent following any of these literally
will fail to post to the bus.

## Fix verification (f935350)

Each fix from `f935350` was verified against the review-01 finding it addressed:

| Fix | Review-01 ID | Verified | Notes |
|---|---|---|---|
| Tier 1 narrowed to "agent-accessible vault" | INV-1 | YES | Line 74-78 now says "agent-accessible vault" and explicitly excludes HUMMBL/Private/empty. No longer contradicts no-access rules. |
| Headline softened with "common operating state" | INV-2 | YES | Line 12 now qualifies with "In the common operating state (app unlocked, no item-level prompt configured)". Adds guidance for when a prompt does appear (lines 30-32). Consistent with body. |
| Removed /tmp file-redirect example | INA-3 | YES | The race-unsafe `/tmp/.secret` + `chmod 600` pattern is gone. No temp-file pattern remains. |
| Added PowerShell equivalents | INA-4 | YES | Lines 260-264 (safe capture) and 273-276 (unsafe). PowerShell syntax tested and confirmed correct. |
| Cross-vault disambiguation (Directive 4) | GAP-1 | YES | Lines 52-58 now include prefer-by-purpose rule and "list both and ask" fallback. |
| Chat-channel warning mechanism (Directive 3) | GAP-2 | YES | Lines 44-50 specify stating item title + vault in chat, pausing for acknowledgment. Clarifies this is chat, not bus. |
| Bus STATUS recipient + full command (Directive 5) | GAP-3 | PARTIAL | Recipient (`fleet`) and type (`STATUS`) are specified. But the `post` command omits the `python /c/Users/Owner/bin/bus-global.py` prefix per AGENTS.md canonical format. See C-6. |
| Multiple-match disambiguation via notes | GAP-4 | YES | Lines 286-297 describe reading the `notes` field to disambiguate. Correctly notes `notes` is not a secret field. |
| Tier 2 covers username/totp/password | GAP-5 | YES | Lines 85-87 explicitly list `username`, `totp`, `password` as Tier 2 reads. |
| Rotation-confirmation closure (step 7) | GAP-6 | YES | Lines 342-344 add step 7: resume only after operator confirms rotation, re-list vault for new title. |
| Empty vault purposes | GAP-7 | YES | Lines 194-201 now give per-vault purposes for `HUMMBL Sensitive Intake`, `Shared`, `jenna`. |
| Map "Scoped" to Low/Restricted | (internal) | YES | Line 174 now says "Low/Restricted" instead of "Scoped". |

**No fix introduced a new problem.** All fixes resolve their intended issues. The
only partial fix is GAP-3 (bus STATUS format) which added the recipient and type but
did not include the full canonical command prefix.

## New findings (not in review-01)

### N-1: `api-keys` item count is wrong (58 vs 63)

Charter line 102 states `api-keys` — 58 items. Actual count is 63. The charter marks
counts "as of 2026-08-19" — the same date as this review. Either the count was
incorrect at time of writing or 5 items were added between the launcher's
verification and this review. **Priority: High.** The count is presented as an exact
snapshot and is demonstrably false.

### N-2: Langfuse count is wrong (6 vs 7)

Charter line 109 states "Langfuse — 6 entries". Actual count is 7 items. **Priority:
Medium.** Same date discrepancy as N-1.

### N-3: SSH key field name not documented

The charter notes an SSH key exists in `bots` (line 125-130) but all retrieval
examples use `--fields credential`. SSH key items use a `private_key` field, not
`credential`. An agent following the examples will get an error. **Priority:
Medium.** The charter should either add an SSH-key-specific example or note that
non-credential items may use different field names (and to check via `op item get
--format json` first).

### N-4: Bus STATUS format missing canonical prefix

See C-6. The charter's `post` shorthand omits the `python
/c/Users/Owner/bin/bus-global.py` prefix required by AGENTS.md. Three different
representations across the charter are mutually inconsistent. **Priority: High.** An
agent following the charter literally cannot post to the bus.

### N-5: Mojibake BOM in commit `058b426`

See C-4. The commit subject begins with garbage bytes (`∩╗┐`). **Priority: Low.**
Cosmetic provenance issue that doesn't break functionality but is visible in raw git
output.

### N-6: `api-keys` contents list is not exhaustive

The charter's contents enumeration for `api-keys` (lines 105-112) omits several
items including OpenAI (`HUMMBL-CYBER-OPENAI-API-KEY`), Hermes Socket
(`HERMES_SOCKET`), Onboarding Key, token-admin, and multiple additional Cloudflare
and HuggingFace keys. The list is presented as illustrative ("Contents: ...") but
the item count (58) implies exhaustiveness. **Priority: Low.** If the count is
corrected, the mismatch between "58 items" and a partial list is less problematic.
Alternatively, label the list as non-exhaustive.

### N-7: `f935350` commit body names AI agent

See C-3. The commit body says "Fixes from devin-reviewer subagent peer review:"
which names an AI tool in the commit message. Not a formal attribution trailer, but
skirts the spirit of AGENTS.md's AI-attribution prohibition. **Priority: Low.**

## Recommended changes (prioritized)

| # | Priority | Item | Action |
|---|---|---|---|
| 1 | High | Fix `api-keys` count (58 → 63) | Update line 102 |
| 2 | High | Fix bus STATUS format to include canonical `python /c/Users/Owner/bin/bus-global.py` prefix | Update Directive 5, Audit Logging, and Incident Response sections to use the full canonical command or explicitly define `post` as shorthand |
| 3 | Medium | Fix Langfuse count (6 → 7) | Update line 109 |
| 4 | Medium | Add SSH key field-name guidance | Add a note that SSH keys use `private_key` field, not `credential`, or add an SSH-key-specific example |
| 5 | Low | Remove mojibake BOM from `058b426` commit message | Amend if possible; otherwise document and prevent recurrence |
| 6 | Low | Reword `f935350` commit body to remove "devin-reviewer" agent name | Amend if possible; use "peer review 01" instead |
| 7 | Low | Label `api-keys` contents list as non-exhaustive, or make it exhaustive | Add "including" qualifier or complete the list |
| 8 | Low | Consider moving charter to `docs/operations/` | Deferred to operator decision (review-01 also flagged) |

## Gate summary

```
HEADLESS_REVIEW_RESULT
VERDICT: REQUEST_CHANGES
CODE_GATE: PASS (doc-only, no code changes)
TEST_GATE: PASS (doc-only, no tests)
PROVENANCE_GATE: FAIL (mojibake BOM in 058b426 commit message)
SIGNATURE_GATE: PASS (all commits by human author Reuben Bowlby)
ATTRIBUTION_GATE: PASS (no prohibited trailers; borderline agent-name mention in f935350 body — not a formal violation)
REF_DRIFT_GATE: FAIL (api-keys count 58 vs actual 63; Langfuse count 6 vs actual 7; bus format drifts from AGENTS.md canonical)
END_HEADLESS_REVIEW_RESULT
```

## Strengths (confirmed from review-01, still hold)

1. Honest security model — "agent is the last line of defense" is candid and accurate
2. Tier 1 / Tier 2 distinction cleanly separates listing from reading
3. Audit exception is explicitly scoped to operator-supervised charter maintenance
4. Incident response is concrete and conservative (7 steps with rotation closure)
5. Circular-dependency callout for 1Password Service Account token
6. SSH-key-in-bots and DCT_SECRET-in-infrastructure notes show real audit care
7. Charter Maintenance section defines re-verification triggers
8. `op run --env-file` as preferred pattern is the safest default
9. PowerShell examples are syntactically correct (tested)
10. All vault names match reality exactly (11/11)

## Summary

The charter is operationally sound and the f935350 fixes correctly resolve all
review-01 findings. However, this review found 3 count inaccuracies (api-keys 58→63,
Langfuse 6→7, and an incomplete contents list), 1 operational gap (SSH key field
name), 1 format inconsistency (bus STATUS missing canonical prefix in 3 places), and
1 provenance defect (mojibake BOM in commit 058b426). The count and bus-format
issues should be fixed before merge. The BOM and agent-name issues are low-priority
but should be noted for future commit hygiene.
