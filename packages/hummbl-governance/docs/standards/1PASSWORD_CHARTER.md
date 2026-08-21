# 1Password Operations Charter

## Purpose

This charter defines the rules, structure, and operational boundaries for agent
interactions with 1Password across the HUMMBL ecosystem. It ensures that agents
safely retrieve credentials without leaking sensitive information to logs, chat
outputs, transcripts, or the coordination bus.

## Security Model

**In the common operating state (app unlocked, no item-level prompt configured),
the agent is the last line of defense. There is no pop-up safety net.**

1Password CLI (`op`) calls succeed **without per-call biometric or manual
approval** when the desktop app is unlocked. `op vault list`, `op item list`,
and `op item get` all execute silently in this state — the operator is not
prompted between the command and the output. Biometric approval is required
only for initial app unlock and for certain high-sensitivity operations
configured in the app's settings.

This means:

- An agent that runs `op item get ... --fields credential` without piping will
  **print the secret directly to the transcript with no pop-up to stop it**.
- The "user authorization" safety net is illusory in the common operating state
  (app unlocked). Rule 1 (never print) is the only real-time control.
- Agents must treat every `op` call as if its output could appear in a public
  log — because it can and will appear in the session transcript.
- If a prompt **does** appear, treat it as a signal that the item is
  operator-flagged high-sensitivity. Pause and confirm with the operator before
  proceeding — do not assume the prompt is an error or a failure.

## Core Directives for Agents

1. **Never Print Credentials**: Under no circumstances should an agent output a
   credential, token, or password to the chat interface, log files, transcript,
   or the bus. This is the primary safety control — not biometric approval.

2. **In-Memory & Environment Only**: When a credential is required for a script
   or command, retrieve it securely via the `op` CLI and pass it directly into
   the process environment or memory. Never let credential output touch stdout.

3. **No Per-Call Approval Assumption**: Do not assume the operator will be
   prompted before an `op` call executes. Before running any Tier 2 read (a
   command that retrieves a credential value, not just lists titles), state the
   item title and vault in your next chat message and pause for operator
   acknowledgment. This is a chat-channel warning, not a bus post — the bus
   STATUS (Directive 5) is posted after the read, not before. Do not rely on a
   pop-up to catch mistakes — it will not appear in the common operating state.

4. **Use Exact Vault Names**: Always scope your search to the specific vault
   using `--vault "<Vault Name>"` to prevent cross-vault confusion and
   unauthorized access attempts. When a service appears in multiple vaults
   (e.g., Cloudflare tokens in both `api-keys` and `infrastructure`), prefer the
   vault whose purpose matches the use case: integration config → `api-keys`,
   deployment/infra → `infrastructure`. When unclear, list both and ask the
   operator.

5. **Log Secret Access on the Bus**: Post a bus `STATUS` to `fleet` when you
   retrieve a credential value (not when you list titles). Canonical command
   (per AGENTS.md):
   `python /c/Users/Owner/bin/bus-global.py post hummbl-governance fleet STATUS "host=<machine> surface=1password retrieved: <item title> from vault=<name> for purpose=<task>"`.
   This makes secret access visible to the fleet without exposing the secret.

## Access Tiers

Agent access to 1Password operates on two distinct tiers. The distinction
matters because listing and reading have different risk profiles:

### Tier 1: Listing (titles and metadata only)

`op vault list` and `op item list --vault <name>` return item titles, categories,
and metadata — **not credential values**. Listing is safe for discovery and
audit purposes. Agents may list any **agent-accessible** vault (see Vault
Taxonomy for access levels) to find the correct item title before retrieving a
credential. `HUMMBL`, `Private`, and the empty vaults are out of bounds for
normal listing — they appear in the taxonomy only because of the
operator-supervised audit exception below.

### Tier 2: Reading (credential values)

`op item get ... --fields <field>` returns the actual secret. This is the
operation that must be piped, injected, or captured — never printed. Tier 2
access is governed by the vault access levels defined below. The same
never-print rule applies to all sensitive fields, not just `credential`:
`username`, `totp`, `password`, and any field containing a secret value are
all Tier 2 reads.

### Audit exception for "No Access" vaults

The vault taxonomy below was established by an operator-supervised audit that
listed all vaults including `HUMMBL` and `Private`. This listing was necessary
to write the taxonomy. Normal agent operations must not list or read these
vaults. The audit exception is: operator-supervised listing for the purpose of
maintaining this charter, with the operator present and aware.

## Vault Taxonomy

The ecosystem's 1Password vaults are segmented by purpose and sensitivity.
Item counts are as of 2026-08-19.

### 1. `api-keys` — 63 items

- **Purpose**: Programmatic API keys for external services.
- **Contents** (illustrative, not exhaustive): LLM provider tokens (OpenRouter,
  Gemini, Claude, DeepSeek, Mistral, Moonshot, xAI, Groq, NVIDIA, HuggingFace,
  OpenAI), GitHub PATs (multiple scopes: org, classic, MCP, Hermes Gateway,
  dev-org), Cloudflare tokens (multiple scopes: build, edit workers, DNS,
  billing, user read-all, agent token, admin, api-editor), telemetry keys
  (Langfuse — 7 entries: public key, secret key, base URL, MCP auth header,
  Anvil key, note, langfuse credential), PyPI and npm publish tokens, UpCloud,
  Tailscale, Resend, Tavily, Context7, ElevenLabs, Tripo, Zenodo, Dune (paper
  trades + real money), Supadata, OpenCode, HuggingFace Router, MXRoute, Gitea,
  Hermes Socket, Onboarding Key, Anvil ZAI API key.
- **Agent Access**: High. This is the primary vault agents read from when
  standing up integrations or configuring environment variables.
- **Naming patterns**: `API Credential - <SERVICE>`, `API Credential - <ENV_VAR_NAME>`,
  `<Service> API Key`, `OpenRouter API Key (main)`, `HUMMBL-<SERVICE>-API-KEY`.

### 2. `bots` — 19 items

- **Purpose**: ChatOps and notification integrations.
- **Contents**: Discord bot tokens (founder-mode-bridge, main), 7 Discord
  webhooks (agent_ops, sitrep, decision_log, hummbl, hummbl_announcements,
  reuben, github-activity), Discord Application IDs and Public Key, Discord
  Application Setup Notes, Slack Bot Token and Slack App Token (HUMMBL Hermes),
  Telegram API credential, MXRoute Discord Bots note, and one SSH key
  (`Tail0ff7b3`).
- **Agent Access**: Medium. Accessed when configuring notification services or
  deploying new ChatOps handlers.
- **Note**: The SSH key in this vault is not a bot token. Agents looking for SSH
  keys should check `bots` in addition to `infrastructure`. SSH key items use a
  `private_key` field, not `credential` — retrieve with
  `op item get "Tail0ff7b3" --vault bots --fields private_key`. When retrieving
  an unfamiliar item type, check its field names first with
  `op item get "<title>" --vault <name> --format json` (Tier 1 metadata only).

### 3. `infrastructure` — 16 items

- **Purpose**: Core platform deployment and ecosystem infrastructure secrets.
- **Contents**: Stripe (2 webhook signing secrets, API credential, sandbox
  note), Hetzner (Cloud API, runner spawner), Cloudflare (R2 S3 credential,
  Access Service Token for uptime-monitor, access-policy-edit-hummbl credential),
  Bus Signing Secret, DCT_SECRET (Delegation Token HMAC Key — governance
  primitive), Hermes Gateway Token, MXRoute (API credential + mailbox
  hermes@hummbl.io), B2 backup credential, Context Registry Backup (Anvil).
- **Agent Access**: Medium. Accessed primarily during deployment, CI/CD, or
  infrastructure-as-code runs.
- **Note**: The DCT_SECRET (Delegation Token HMAC Key) is a governance control
  surface. Agents working on hummbl-governance delegation tokens will find the
  HMAC key here, not in a governance-specific vault.

### 4. `service-accounts` — 8 items

- **Purpose**: Authentication tokens for programmatic platforms and
  system-to-system auth.
- **Contents**: hummbl-dev Access Token, 1Password Service Account token
  (Anvil Engineering Cloudflare read, 2026-08-12), Service Account Auth Tokens
  (Staging, Production, GitHub Actions, Maintenance), GitLab PAT, hummbl-dev
  Credentials File (document).
- **Agent Access**: Low/Restricted. Usually accessed only by CI/CD runners or
  core bootstrapping scripts, not typical agent operations.
- **Bootstrap note**: The 1Password Service Account token stored here is itself
  used to access 1Password programmatically via `OP_SERVICE_ACCOUNT_TOKEN`. This
  is a circular dependency — the token must be provisioned by the operator
  outside of `op` before it can be used. The service account grants scoped
  access (Anvil Cloudflare read-only), not full vault access.

### 5. `runtime-bus-prod` — 1 item

- **Purpose**: BusBridge operational secrets.
- **Contents**: BusBridge Runtime Token (single item).
- **Agent Access**: Low/Restricted. Used by the coordination bus infrastructure.

### 6. `fleet-autonomous-read-prod` — 1 item

- **Purpose**: Scoped read-only access for the autonomous agent fleet.
- **Contents**: Cloudflare - Anvil Engineering Account Read (single scoped
  credential, created 2026-08-12).
- **Agent Access**: Low/Restricted. This is a single credential for
  non-destructive reconnaissance on Anvil's Cloudflare account, not a general
  category. Agents should not expect multiple items here.

### 7. `HUMMBL` — 582 items

- **Purpose**: General business operations, web logins, and financial accounts.
- **Contents**: Shared company logins (Amazon, Zoom, social media, bank
  accounts, and other interactive web logins credentials).
- **Agent Access**: None. Agents should not list or read this vault during
  normal operations. See the audit exception above for charter maintenance.

### 8. `Private` — 630 items

- **Purpose**: The operator's personal vault.
- **Contents**: Personal web accounts, private API keys, local service logins,
  and secure notes.
- **Agent Access**: None. This vault is out of bounds for ecosystem agent
  operations. See the audit exception above for charter maintenance.

### 9. `HUMMBL Sensitive Intake`, `Shared`, `jenna` — 0 items each

- **Purpose**: Reserved vaults — `HUMMBL Sensitive Intake` for future
  high-sensitivity business intake, `Shared` for future cross-team sharing,
  `jenna` for a named individual's vault. All three are currently empty.
- **Agent Access**: None. These vaults are empty as of 2026-08-19. If an agent
  encounters these names elsewhere, treat them as out-of-bounds reserved
  vaults, not as populated resources.

## Item Naming Conventions

1Password items do not follow a single naming convention. Agents should not
guess item titles. Instead, use `op item list --vault <name> --format json` to
discover the exact title before retrieving a credential.

Common patterns observed in the vaults:

- `API Credential - <SERVICE>` — most common pattern
- `API Credential - <ENV_VAR_NAME>` — matches the environment variable name
- `<Service> API Key` — plain English variant
- `Discord Webhook <channel>` — ChatOps webhooks are named by channel
- `Service Account Auth Token: <ENV>` — service account tokens by environment
- `<Service> - <scope> - <date>` — scoped credentials with creation date
- `HUMMBL-<SERVICE>-API-KEY` — uppercase env-var-style names

When retrieving a credential, always `op item list` first to confirm the exact
title. Guessing will produce "item not found" errors or, worse, retrieve the
wrong credential if a partial match succeeds.

## Session Management

- **Check auth state in this order** (avoids unnecessary prompts):
  1. Run `op vault list` first — if it succeeds, the session is active and you
     can proceed with listing and reading. **Do not run `op whoami` if
     `op vault list` already works** — `op whoami` often returns "not signed in"
     even when `op vault list` succeeds, and running `op signin` in response
     will trigger an unnecessary desktop prompt.
  2. If `op vault list` fails, run `op account list` to check if an account is
     configured (note: this prints the operator's email — PII, treat
     accordingly).
  3. If no account is configured, ask the operator to provision `op`.
  4. If an account is configured but `op vault list` fails, run `op signin` to
     re-authenticate. This will prompt the operator for approval.
- **Service account token**: For headless/CI operations, set
  `OP_SERVICE_ACCOUNT_TOKEN` in the environment. This bypasses the desktop app
  entirely but grants only the scope configured for that service account (not
  full vault access). The token must be provisioned by the operator out-of-band
  (not retrieved via `op`, which would be circular — the token is what enables
  headless `op` access). See `service-accounts` vault for the available tokens.
- **App unlock state**: `op vault list` succeeding does not mean `op whoami`
  will report "signed in". The two checks test different states. If
  `op vault list` works, you can proceed with listing and reading.

## Usage Patterns

The examples below show both bash (WSL/Git Bash) and PowerShell forms. `op` is
configured on anvil (Windows), so PowerShell is the native shell. Bash examples
apply when running via WSL or Git Bash on anvil, or on Unix fleet machines.

### Safe: inject directly into process environment (preferred)

```bash
# op run reads .env.template, resolves op:// references, and runs the command
# with secrets injected into the process environment — never to stdout
op run --env-file=.env.template -- python script.py
```

### Safe: capture in variable, never to stdout

```bash
# Credential is captured in the variable; nothing is printed.
# 2>/dev/null suppresses stderr (op may write diagnostics containing item
# titles or vault names to stderr, which would appear in the transcript)
export OPENROUTER_API_KEY=$(op item get "OpenRouter API Key (main)" --vault api-keys --fields credential 2>/dev/null)
python script.py
```

```powershell
# PowerShell equivalent — credential captured in env var, never to stdout.
# 2>$null suppresses stderr for the same reason
$env:OPENROUTER_API_KEY = op item get "OpenRouter API Key (main)" --vault api-keys --fields credential 2>$null
python script.py
```

### Unsafe — never do this

```bash
# This prints the credential to stdout, which appears in the transcript
op item get "OpenRouter API Key (main)" --vault api-keys --fields credential
```

```powershell
# Same hazard in PowerShell — prints to stdout, appears in transcript
op item get "OpenRouter API Key (main)" --vault api-keys --fields credential
```

### Discovery — safe (titles only, no secrets)

```bash
# List all items in a vault — returns titles and categories, not credentials
op item list --vault api-keys --format json
```

### Multiple matches — disambiguate before reading

When `op item list` returns multiple items for the same service (e.g., multiple
GitHub PATs with different scopes), do not guess by picking the first. The
`notesPlain` field may contain disambiguating context (scope, environment,
purpose), but **treat `notesPlain` as Tier 2** — users can paste secrets into
notes, so always pipe it, never print it directly:

```bash
# notesPlain is the correct field id (not "notes"). Pipe it — notes can contain
# pasted secrets even though the field type is STRING, not CONCEALED.
NOTES=$(op item get "GitHub Personal Access Token" --vault api-keys --fields notesPlain 2>/dev/null)
echo "$NOTES" | head -c 200   # preview first 200 chars only; full value stays in variable
```

```powershell
# PowerShell equivalent — capture in variable, preview truncated
$notes = op item get "GitHub Personal Access Token" --vault api-keys --fields notesPlain 2>$null
$notes.Substring(0, [Math]::Min(200, $notes.Length))
```

If the notes field does not clarify the scope, ask the operator which item to
use rather than guessing. Do not read the credential value until the operator
confirms the correct item.

## Audit Logging

Post a bus `STATUS` when you retrieve a credential value (Tier 2 access). This
makes secret access visible to the fleet without exposing the secret.

```
python /c/Users/Owner/bin/bus-global.py post hummbl-governance fleet STATUS "host=anvil surface=1password retrieved: OpenRouter API Key (main) from vault=api-keys for purpose=openrouter-integration-test"
```

Do not post the credential value, the field name beyond `credential`, or any
partial output. The STATUS is an access log, not a content log.

Listing operations (Tier 1) do not require a bus post — they reveal no secrets.

## Cross-Machine Availability

`op` CLI is configured on **anvil** (Windows, desktop app integration). Agents
on other machines (delta, huxley, slate, nodezero) should not assume `op` is
installed or authenticated. Before relying on `op` on a non-anvil machine:

1. Check `op --version` — confirms the CLI is installed
2. Check `op account list` — confirms an account is configured
3. Check `op vault list` — confirms the session is active

If any check fails, either SSH to anvil to run `op` there, or ask the operator
to provision `op` on the target machine. Do not attempt to install or configure
`op` without operator approval.

For headless operations on any machine, use `OP_SERVICE_ACCOUNT_TOKEN` from the
`service-accounts` vault (Anvil-scoped Cloudflare read only, as of 2026-08-19).

## Incident Response

If a credential is leaked to a transcript, log, or bus post:

1. **Stop immediately** — do not attempt to redact the transcript in-place
2. **Notify the operator** — surface the leak in the next message, not deferred
3. **Identify the leaked credential** — item title and vault (not the value)
4. **Post a bus `STATUS`** —
   `python /c/Users/Owner/bin/bus-global.py post hummbl-governance fleet STATUS "host=<machine> surface=1password INCIDENT: <item title> from vault=<name> leaked to <surface>. Operator notified. Rotation required."`
5. **Do not rotate the credential yourself** — rotation is operator-only. The
   operator will rotate in the 1Password app and update any dependent services.
   If the leaked credential is `OP_SERVICE_ACCOUNT_TOKEN` (service-accounts
   vault), the operator must **revoke** the token in the 1Password app to
   immediately cut access, not just rotate it — the compromised token may still
   grant live scoped read access until revoked.
6. **Do not delete the transcript** — it may be needed for forensic analysis.
   The operator will decide whether to redact or purge the affected transcript.
7. **Resume only after operator confirms rotation** — the operator will provide
   the new item title (it may change after rotation). Do not resume using the
   old item title; re-list the vault to confirm the new title before reading.
   If the leaked credential was `OP_SERVICE_ACCOUNT_TOKEN`, the operator must
   provision a replacement out-of-band (not via `op`, which depends on it).

## Charter Maintenance

This charter should be re-verified against the actual 1Password state when:
- A new vault is created or an existing vault is renamed
- Item counts change significantly (new category of credentials added)
- A new machine is provisioned with `op` access
- The `op` CLI version changes in a way that affects the security model

Re-verification requires an operator-supervised audit (see the audit exception
in Access Tiers). The operator must be present and aware that vault listing is
occurring, including for `HUMMBL` and `Private`.
