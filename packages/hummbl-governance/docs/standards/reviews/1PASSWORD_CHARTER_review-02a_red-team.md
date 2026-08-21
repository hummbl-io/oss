# Peer Review 02a (Red Team) — 1Password Operations Charter

**Reviewer**: subagent_general (Red Team, Reviewer A)
**Reviewer model**: inherited from parent
**Reviewed commits**: `6f1a049` → `058b426` → `f935350` → `c28f9a1` on `feat/gemini/1password-charter`
**Review date**: 2026-08-19
**Verdict**: **needs changes** — 3 invalidations, 10 new findings, 5 adversarial scenarios

## Methodology

Unlike review-01 (which had read-only tools only), this review ran live `op` commands
against the actual 1Password state, verified git history, and checked commit attribution.
All credential values were captured in variables or piped to files — no secret was printed
to the transcript. The temp file used for item-count verification was deleted after use.

## Verification evidence

### op vault list (security model claim)

```
op vault list → succeeded with NO pop-up, NO biometric prompt, NO operator interaction
```

**Result**: The security model claim is **CONFIRMED**. `op vault list` executes silently
when the desktop app is unlocked. 11 vaults returned: api-keys, bots,
fleet-autonomous-read-prod, HUMMBL, HUMMBL Sensitive Intake, infrastructure, jenna,
Private, runtime-bus-prod, service-accounts, Shared.

### op whoami vs op vault list (session state discrepancy)

```
op whoami → [ERROR] account is not signed in
op vault list → succeeds (11 vaults)
op account list → succeeds, prints operator email (reuben@hummbl.io)
```

**Result**: The charter's claim that "`op vault list` succeeding does not mean `op whoami`
will report 'signed in'" is **CONFIRMED**. However, this creates an operational issue
(see NF-2).

### op CLI version

```
op --version → 2.38.1
```

### Vault item counts (live verification)

| Vault | Charter claim | Actual (live) | Match? |
|---|---|---|---|
| api-keys | 58 | **63** | **NO — off by 5** |
| bots | 19 | 19 | yes |
| infrastructure | 16 | 16 | yes |
| service-accounts | 8 | 8 | yes |
| runtime-bus-prod | 1 | 1 | yes |
| fleet-autonomous-read-prod | 1 | 1 | yes |
| HUMMBL Sensitive Intake | 0 | 0 | yes |
| Shared | 0 | 0 | yes |
| jenna | 0 | 0 | yes |

### Git history

```
git log --oneline 6f1a049..c28f9a1:
c28f9a1 docs(standards): add peer review 01 for 1Password charter
f935350 docs(standards): address peer-review findings on 1Password charter
058b426 docs(standards): peer-review revision of 1Password Operations Charter

git diff 6f1a049..c28f9a1 --stat:
 docs/standards/1PASSWORD_CHARTER.md                | 377 ++++++++++++++++++---
 .../1PASSWORD_CHARTER_review-01_devin-reviewer.md  | 135 ++++++++
 2 files changed, 467 insertions(+), 45 deletions(-)
```

3 commits, 2 files, 467 ins / 45 del. **Matches** the charter history described in the task.

### AI attribution check

```
git log 6f1a049..c28f9a1 --format="%B" | grep -i "Co-authored|Generated with|Generated-by|Authored-with|devin-ai"
→ (no matches for prohibited trailer formats)
```

**However**: the `f935350` commit body contains: *"Fixes from devin-reviewer subagent
peer review:"* — this credits an AI subagent by name in the commit message body. See
ATTRIBUTION_GATE below.

---

## Invalidations (claims demonstrably false, with evidence)

### INV-3 — api-keys item count is 63, not 58

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:102` — `### 1. api-keys — 58 items`
- **Evidence**: `op item list --vault api-keys --format json` returns 63 items (verified
  by piping to file, parsing JSON, counting `.Count`). All other vault counts match.
- **Impact**: The charter understates the primary vault by 5 items (8.6% drift). The
  content list is also incomplete — at least 5 items represent services not mentioned in
  the charter's contents: `HERMES_SOCKET`, `ONBOARDING_KEY`, `ANVIL_ZAI_API_KEY`,
  `cf-user-token-admin`, `HUMMBL-CYBER-OPENAI-API-KEY` (OpenAI is absent from the LLM
  provider list). The charter's own maintenance section says to re-verify when "Item
  counts change significantly" — 5 items in one vault is significant.
- **Severity**: Medium. The count is marked "as of 2026-08-19" so this may be staleness
  rather than an original error, but the current claim is false regardless.

### INV-4 — The "Multiple matches" example command is broken (wrong field name)

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:293` —
  `op item get "GitHub Personal Access Token" --vault api-keys --fields notes`
- **Evidence**: The 1Password CLI field id is `notesPlain`, not `notes`. Live test:
  ```
  op item get "API Credential - Cloudflare" --vault api-keys --fields notes
  → [ERROR] "notes" isn't a field in the "API Credential - Cloudflare" item

  op item get "API Credential - Cloudflare" --vault api-keys --fields notesPlain
  → succeeds (exit 0)
  ```
  The item's field structure (from `--format json`): `id=notesPlain label=notesPlain
  type=STRING`. There is no field called `notes`.
- **Impact**: An agent following the charter's disambiguation guidance will get an error
  on every `--fields notes` call. The agent must either guess the correct field name
  (`notesPlain`) or abandon the disambiguation step entirely. This defeats the purpose
  of the "Multiple matches" section.
- **Severity**: High. This is the charter's only disambiguation mechanism for
  same-title items, and it doesn't work as written.

### INV-5 — "notes is not a secret field" is a false categorical claim

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:292` —
  `# notes is not a secret field — safe to print for disambiguation`
- **Evidence**: The `notesPlain` field is type `STRING` (not `CONCEALED`), which means
  1Password does not treat it as a secret in its data model. However, the field is
  free-text — users can paste ANY content into it, including passwords, API keys,
  private keys, connection strings, or tokens. The field being `STRING` type makes it
  EASIER to leak, not safer, because `op` will return it without concealment. The
  categorical claim "not a secret field" is false: the field TYPE is non-secret, but
  the field CONTENT can be anything.
- **Impact**: An agent that discovers the correct field name (`notesPlain`) and reads it
  for disambiguation could print a secret that a user pasted into the notes field. The
  charter explicitly says this is "safe to print" — it is not.
- **Severity**: Critical. This is a credential-leak vector embedded in the charter's
  own guidance.

---

## New findings (issues NOT already covered in review-01)

### NF-1 — `op account list` leaks the operator's email

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:225` —
  "Run `op account list` to see if an account is configured."
- **Evidence**: `op account list` prints a table including the operator's email
  (`reuben@hummbl.io`) and user ID to stdout. The charter recommends this command
  without warning that it outputs PII.
- **Impact**: An agent running this command in a transcript-visible context leaks the
  operator's email address. The charter's own Directive 1 says "never output a
  credential, token, or password" — email isn't a credential, but it is PII that
  probably shouldn't be in transcripts.
- **Severity**: Low-Medium.

### NF-2 — Session Management check order causes unnecessary prompts

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:225-229` —
  "Run `op account list`... Run `op whoami` to check if the session is active...
  If a command returns 'account is not signed in', run `op signin`"
- **Evidence**: Live test shows `op whoami` returns "account is not signed in" while
  `op vault list` succeeds. An agent following the charter's recommended check order
  would: (1) run `op whoami`, (2) see "not signed in", (3) run `op signin`, (4) trigger
  a desktop prompt — even though `op vault list` already works and no sign-in is needed.
  The charter explains the discrepancy later (line 234-236) but the check order is
  misleading.
- **Impact**: Unnecessary `op signin` prompts, contradicting the security model's "no
  pop-up in the common operating state" claim. The agent causes the exact pop-up the
  charter says won't happen.
- **Severity**: Medium.

### NF-3 — Circular dependency not addressed in Session Management or Cross-Machine

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:230-233` (Session Management) and
  `:327-328` (Cross-Machine Availability)
- **Evidence**: Both sections tell agents to "set `OP_SERVICE_ACCOUNT_TOKEN` in the
  environment" and refer to the `service-accounts` vault for available tokens. But to
  read from the `service-accounts` vault, the agent needs `op` access — which is what
  the service account token provides. The circular dependency is acknowledged in the
  vault taxonomy (line 157-161) but NOT in the two sections that tell agents to retrieve
  the token.
- **Impact**: An agent on a headless machine without `op` configured follows Cross-Machine
  Availability, tries to retrieve `OP_SERVICE_ACCOUNT_TOKEN` from the `service-accounts`
  vault, and fails — because `op` isn't configured on that machine. The agent is stuck
  with no resolution path. The charter should state that the service account token must
  be provisioned by the operator out-of-band, not retrieved via `op`.
- **Severity**: Medium.

### NF-4 — Incident response doesn't handle leaked OP_SERVICE_ACCOUNT_TOKEN

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:330-344` (Incident Response)
- **Evidence**: The incident response section is generic — it says "stop, notify, post
  STATUS, don't rotate, don't delete transcript, resume after operator confirms." But
  if the leaked credential is `OP_SERVICE_ACCOUNT_TOKEN` itself:
  - The compromised token may still be active, granting scoped read access to Cloudflare
  - The agent's headless access is compromised
  - The agent cannot re-read the token from 1Password (it's compromised)
  - The incident response doesn't mention revoking the service account token in the
    1Password app (only generic "rotation is operator-only")
  - The circular dependency means the agent can't bootstrap a replacement
- **Impact**: A leaked service account token has different blast radius and recovery
  path than a leaked API key. The charter treats all leaks identically.
- **Severity**: Medium.

### NF-5 — Directive 3 chat-channel warning has no timeout or fallback

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:44-50` (Directive 3)
- **Evidence**: Directive 3 says "state the item title and vault in your next chat
  message and pause for operator acknowledgment." There is no timeout, no escalation
  path, no default behavior if the operator doesn't respond. An agent could hang
  indefinitely waiting for acknowledgment.
- **Impact**: Operational deadlock. The agent is told to pause but never told when to
  unpause if no response comes.
- **Severity**: Medium.

### NF-6 — Item titles can reveal sensitive strategic metadata

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:47` (Directive 3) and `:62`
  (Directive 5 bus STATUS format)
- **Evidence**: Directive 3 requires stating the item title in chat before reading.
  Directive 5 requires posting the item title in a bus STATUS. Some actual titles
  reveal strategic information: `API Credential - Dune - REAL MONEY` (reveals real-money
  trading), `HUMMBL-CYBER-OPENAI-API-KEY` (reveals a "cyber" OpenAI key exists),
  `API Credential - ONBOARDING_KEY` (reveals an onboarding key exists). The charter
  treats all titles as non-sensitive metadata.
- **Impact**: Following the charter perfectly leaks strategic metadata to the chat
  transcript and the bus. The charter's own Directive 1 says "never output a credential"
  — titles aren't credentials, but they are intelligence.
- **Severity**: Low-Medium.

### NF-7 — Safe examples don't address stderr leakage

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:254-258` (bash) and `:261-264`
  (PowerShell)
- **Evidence**: The "safe" capture-in-variable examples capture stdout but don't redirect
  stderr. In both bash (`export VAR=$(op item get ...)`) and PowerShell
  (`$env:VAR = op item get ...`), stderr output goes to the terminal/transcript. If `op`
  writes diagnostic output containing item titles, vault names, or error context to
  stderr, it appears in the transcript even in the "safe" pattern.
- **Impact**: The "safe" examples are not fully safe. They should include `2>/dev/null`
  (bash) or `2>$null` (PowerShell) to suppress stderr.
- **Severity**: Low.

### NF-8 — api-keys content list missing at least 5 unnamed services

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:105-112` (api-keys contents)
- **Evidence**: Live item list (63 items) includes services not mentioned in the
  charter's content list: `HERMES_SOCKET`, `ONBOARDING_KEY`, `ANVIL_ZAI_API_KEY`,
  `cf-user-token-admin`, `HUMMBL-CYBER-OPENAI-API-KEY` (OpenAI is absent from the LLM
  provider list at line 105). Also: `OpenRouter Key OSS` (second OpenRouter key),
  `operator_HF_API_KEY` and `SUM_GUY_429_HF_API_KEY` (personal HF keys),
  `Cloudflare - phase0b-mike-lab`, `HUMMBL_ALL_PYPI_PROJECTS_API_KEY` (second PyPI token).
- **Impact**: The content list is presented as comprehensive but is incomplete. An agent
  searching for an OpenAI key would not find it mentioned in the charter and might
  conclude it doesn't exist.
- **Severity**: Medium.

### NF-9 — Cross-vault disambiguation only covers 2-vault case

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:52-58` (Directive 4)
- **Evidence**: Directive 4 gives one example: Cloudflare tokens in `api-keys` vs
  `infrastructure`. But Cloudflare credentials actually appear in at least 3 vaults:
  `api-keys` (multiple Cloudflare tokens), `infrastructure` (R2, Access Service Token,
  access-policy-edit), and `fleet-autonomous-read-prod` (Anvil Cloudflare read). The
  rule says "When unclear, list both and ask the operator" — but "both" doesn't cover
  three or more vaults.
- **Impact**: An agent facing a 3+ vault disambiguation has no guidance. The rule says
  "list both" but there may be three or more to list.
- **Severity**: Low-Medium.

### NF-10 — `op item list --format json` returns `last_edited_by` metadata

- **Path/line**: `docs/standards/1PASSWORD_CHARTER.md:70-74` (Tier 1 listing)
- **Evidence**: The Tier 1 JSON output includes fields: `id, title, tags, version, vault,
  category, last_edited_by, created_at, updated_at`. The `last_edited_by` field is an
  array that could contain user identifiers. The charter says Tier 1 returns "titles,
  categories, and metadata — not credential values" and is "safe for discovery." While
  no credential values are exposed, the metadata is richer than "titles and categories"
  implies. (Live check: `last_edited_by` for the sampled item was an empty array, so no
  email was leaked in this case — but the field exists and could contain identifiers.)
- **Impact**: Minor — the charter undersells how much metadata Tier 1 returns, but no
  credential values are exposed.
- **Severity**: Low.

---

## Confirmed fixes (what f935350 correctly resolved)

| Review-01 finding | Status | Verification |
|---|---|---|
| INV-1: Tier 1 "list any vault" vs HUMMBL/Private | **FIXED** | Line 74 now says "agent-accessible vault"; lines 76-78 explicitly exclude HUMMBL/Private/empty |
| INV-2: "no pop-up safety net" headline vs caveat | **FIXED** | Line 12 now qualified with "In the common operating state"; lines 30-32 add guidance for when a prompt does appear |
| INA-3: Unsafe temp-file example | **FIXED** | Removed entirely; no `/tmp/.secret` pattern remains |
| INA-4: All bash, no PowerShell | **FIXED** | PowerShell equivalents added at lines 260-264 and 273-276 |
| GAP-1: No cross-vault disambiguation | **FIXED** | Directive 4 (lines 52-58) added prefer-by-purpose rule |
| GAP-2: No warn mechanism | **FIXED** | Directive 3 (lines 44-50) specifies chat-channel warning with pause |
| GAP-3: No bus recipient | **FIXED** | Directive 5 (lines 60-63) specifies `fleet` recipient and full `post` command |
| GAP-4: No multiple-match guidance | **PARTIALLY FIXED** | Section added (lines 286-297) but the example command is broken (INV-4) and the safety claim is false (INV-5) |
| GAP-5: No non-credential field guidance | **FIXED** | Tier 2 (lines 85-87) now covers username/totp/password |
| GAP-6: No rotation closure | **FIXED** | Step 7 added (lines 342-344) |
| GAP-7: Empty vaults without purpose | **FIXED** | Vault 9 (lines 194-201) now has per-vault purposes |

---

## Adversarial scenarios (concrete charter-failure cases)

### Scenario 1: The notes-field leak (CRITICAL)

An agent needs a GitHub PAT. `op item list --vault api-keys` returns two matches:
"GitHub Personal Access Token" and "GitHub Personal Access Token - HUMMBL_DEV_ORG_PAT".
The agent follows the "Multiple matches" section and runs:

```bash
op item get "GitHub Personal Access Token" --vault api-keys --fields notes
```

**Outcome A**: The command fails — `"notes" isn't a field`. The agent is stuck and
cannot disambiguate. It must either guess (which the charter forbids) or ask the
operator (which Directive 3 already requires for Tier 2 reads, making this section
redundant).

**Outcome B**: The agent discovers `notesPlain` on its own, runs the command without
piping (as the charter's example shows), and the notes field contains a pasted API
key or token that a user stored for reference. The secret prints to the transcript.
**The agent followed the charter's guidance and leaked a credential.**

### Scenario 2: The headless bootstrapping deadlock

An agent on `delta` (non-anvil machine) needs to run a headless operation. It follows
Cross-Machine Availability (line 327): "use `OP_SERVICE_ACCOUNT_TOKEN` from the
`service-accounts` vault." The agent SSHes to anvil, runs `op item get` to retrieve
the token, and... the token is in the `service-accounts` vault which has
"Low/Restricted" access. Even if the agent can read it, it must now transport the
token to `delta` — by printing it to the SSH session (leak) or writing it to a file
(the unsafe pattern the charter removed). The charter provides no safe mechanism for
cross-machine token transport.

### Scenario 3: The unnecessary sign-in prompt

An agent starts a session. Following Session Management (line 225-229), it runs
`op whoami` → "account is not signed in." The agent runs `op signin` as instructed.
This triggers a desktop biometric prompt — the exact pop-up the Security Model section
says "will not appear in the common operating state." The operator is confused: the
charter said no pop-ups, but the agent caused one by following the recommended check
order. If the operator is AFK, the agent is now blocked.

### Scenario 4: The strategic metadata leak via bus STATUS

An agent retrieves the "API Credential - Dune - REAL MONEY" credential. Following
Directive 5, it posts:

```
post hummbl-governance fleet STATUS "host=anvil surface=1password retrieved: API Credential - Dune - REAL MONEY from vault=api-keys for purpose=dune-trading-bot"
```

This bus post is visible to the entire fleet. It reveals: (1) a real-money trading
credential exists, (2) it's in the api-keys vault, (3) the agent is building a Dune
trading bot. The charter says "Do not post the credential value" but the item title
itself is strategic intelligence. **The agent followed the charter perfectly and leaked
strategic information to the fleet.**

### Scenario 5: The compromised service account token

The `OP_SERVICE_ACCOUNT_TOKEN` is leaked to a transcript. The agent follows Incident
Response: stops, notifies operator, posts bus STATUS, waits. But the compromised token
is still active — it grants scoped read access to the Anvil Cloudflare account. The
incident response says "rotation is operator-only" and "resume only after operator
confirms rotation" but doesn't mention that the token should be REVOKED (not just
rotated) in the 1Password app to immediately cut access. The agent waits while the
attacker has live access.

---

## Recommended changes (prioritized)

| # | Priority | Item | Addresses |
|---|---|---|---|
| 1 | **Block** | Fix INV-5: Remove the claim "notes is not a secret field — safe to print." Replace with: "The notes field (`notesPlain`) is free-text and MAY contain secrets. Never print notes to stdout. If disambiguation is needed, use `op item list` titles and tags, or ask the operator." | INV-5, Scenario 1 |
| 2 | **Block** | Fix INV-4: Change `--fields notes` to `--fields notesPlain` in the example, OR remove the notes-field approach entirely and replace with "ask the operator" (given INV-5, this is safer) | INV-4, Scenario 1 |
| 3 | **Block** | Fix INV-3: Update api-keys count from 58 to 63 and add missing items to the content list (HERMES_SOCKET, ONBOARDING_KEY, ANVIL_ZAI_API_KEY, cf-user-token-admin, HUMMBL-CYBER-OPENAI-API-KEY, etc.) | INV-3, NF-8 |
| 4 | High | Fix NF-2: Reorder Session Management — list `op vault list` as the primary check, not `op whoami`. Add: "If `op vault list` succeeds, proceed. Do not run `op signin` unless `op vault list` fails." | NF-2, Scenario 3 |
| 5 | High | Fix NF-3: In Session Management and Cross-Machine Availability, add: "The service account token must be provisioned by the operator out-of-band. Agents cannot retrieve it via `op` on a machine where `op` is not yet configured." | NF-3, Scenario 2 |
| 6 | High | Fix NF-5: Add timeout/escalation to Directive 3: "If the operator does not acknowledge within a reasonable timeframe, do not proceed. Abort the task and report the stall." | NF-5 |
| 7 | Medium | Fix NF-4: Add a sub-section to Incident Response for leaked service account tokens: "If the leaked credential is `OP_SERVICE_ACCOUNT_TOKEN`, the operator must REVOKE (not just rotate) the token in the 1Password app to immediately cut access. The agent cannot bootstrap a replacement — the operator must provision a new token out-of-band." | NF-4, Scenario 5 |
| 8 | Medium | Fix NF-7: Add `2>/dev/null` to bash safe examples and `2>$null` to PowerShell safe examples | NF-7 |
| 9 | Medium | Fix NF-1: Add warning to Session Management: "`op account list` prints the operator's email to stdout. Pipe or capture if transcript visibility is a concern." | NF-1 |
| 10 | Low | Fix NF-9: Extend Directive 4 to cover 3+ vault cases: "When a service appears in three or more vaults, list all candidate vaults and ask the operator." | NF-9 |
| 11 | Low | Fix NF-6: Add a note to Directives 3 and 5: "Some item titles reveal strategic metadata. If the title itself is sensitive, refer to the item by vault and partial identifier rather than full title." | NF-6, Scenario 4 |
| 12 | Low | Fix NF-10: Update Tier 1 description to accurately list the metadata fields returned by `op item list --format json` | NF-10 |
| 13 | Gate | Review commit message attribution (see ATTRIBUTION_GATE below) | Attribution |

---

## Gate summary

```
HEADLESS_REVIEW_RESULT
VERDICT: NEEDS_CHANGES
CODE_GATE: PASS (doc-only, no code changes)
TEST_GATE: PASS (doc-only)
PROVENANCE_GATE: PASS (3 commits verified, diff stat matches: 467 ins / 45 del, 2 files)
SIGNATURE_GATE: PASS (live op commands verified security model, vault counts, field names)
ATTRIBUTION_GATE: BORDERLINE FAIL — no prohibited trailers (Co-authored-by, Generated-by,
  Authored-with) found, but f935350 commit body credits "devin-reviewer subagent peer
  review" which is AI agent attribution in commit credit. AGENTS.md says "Agent activity
  belongs in internal receipts, bus messages, handoffs, or PR notes, not commit credit."
  The letter of the rule (trailers/metadata) is satisfied; the spirit is not.
REF_DRIFT_GATE: FAIL — api-keys count is 63, not 58 (5-item / 8.6% drift). Content list
  missing at least 5 services. Other vault counts match.
END_HEADLESS_REVIEW_RESULT
```

---

## Comparison to review-01

Review-01 found 2 invalidations, 4 inaccuracies, and 7 gaps — all of which were addressed
in f935350. This review (Red Team) found 3 NEW invalidations, 10 new findings, and 5
adversarial scenarios that review-01 missed. The difference is attributable to:

1. **Live `op` execution** — review-01 had read-only tools only and could not verify
   counts, field names, or command behavior. This review ran `op vault list`, `op item
   list`, `op item get`, `op whoami`, and `op account list` against the live state.
2. **Adversarial framing** — review-01 checked for contradictions and gaps. This review
   actively tried to break the charter by constructing failure scenarios and testing
   them against live state.
3. **Notes-field investigation** — review-01 accepted the "Multiple matches" fix at face
   value. This review tested the actual command and discovered the field name is wrong
   and the safety claim is false.

The most critical finding (INV-5: "notes is not a secret field") is a credential-leak
vector that was INTRODUCED by the f935350 fix for GAP-4. The fix for the gap created a
new, more dangerous problem.
