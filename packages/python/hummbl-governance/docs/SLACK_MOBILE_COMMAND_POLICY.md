# Slack Mobile Command Surface Policy

**Status**: Draft — not canon until namespace review is receipted.
**Related**:
- Signal CLI admission policy: `docs/SIGNAL_CLI_ADMISSION_POLICY.md`
- Receipt schema: `docs/ecosystem/schemas/slack_command_receipt.schema.json`

## Purpose

Govern Slack-originated mobile commands so Slack can be used by agents
and operators as a read-only, draft, and approval-gated command surface
without becoming an ambient execution authority. Slack is a notification
and coordination surface, not an execution surface.

## Core Invariant

No durable state mutation, tool execution, or external write from Slack
without admission, authority, executor, and receipt.

## Risk Classification

Slack-originated commands are classified before routing:

| Risk class | Examples | Default |
|---|---|---|
| `read_only` | status check, list PRs, show CI | Allow after workspace and channel validation |
| `draft_only` | draft issue, draft PR description, draft reply | Allow with receipt; no publish |
| `write_pending_approval` | merge PR, close issue, push commit | Require approval/admission |
| `destructive` | force-push, delete branch, drop table | Deny from Slack; require operator console |
| `forbidden` | secrets, raw shell, unregistered workspace, unknown verb | Deny and receipt |

## Gates

| Gate ID | Description |
|---|---|
| `G-SLACK-WORKSPACE-ALLOWLIST` | Commands only from allowlisted workspaces. Unknown workspace → deny. |
| `G-SLACK-NO-SECOND-BUS` | Slack is not a second coordination bus. Bus events originate on the canonical bus, not Slack. |
| `G-SLACK-DRY-RUN-FIRST` | First command from a new channel or actor must be dry-run. |
| `G-SLACK-RECEIPT-ROUNDTRIP` | Every command produces a receipt; every response produces a receipt. |
| `G-SLACK-NO-SECRETS` | Commands containing secret-like material (API keys, tokens, passwords) are denied. |
| `G-SLACK-NO-RAW-SHELL` | Raw shell commands are forbidden from Slack. |
| `G-SLACK-RATE-LIMIT` | Rate-limit policy enforced per actor and per channel. |
| `G-SLACK-OUTPUT-POLICY` | Response output is summarized, redacted, or link-only — never full command output. |
| `G-SLACK-HASHED-IDENTIFIERS` | Receipts store SHA-256 hashes of workspace ID, channel ID, actor ID, and command text — never raw values. |

## Receipt Schema

See `docs/ecosystem/schemas/slack_command_receipt.schema.json`.

```yaml
receipt_id: string
surface: slack
workspace_id_hash: string (sha256)
channel_id_hash: string (sha256)
thread_ts: string | null
actor_id_hash: string (sha256)
received_at: string (iso8601)
command_text_hash: string (sha256)
parsed_intent: string
risk_class: read_only | draft_only | write_pending_approval | destructive | forbidden
requested_repo: string | null
requested_tool: string | null
authority: string
executor: string | null
admission_decision: admitted | denied | pending_approval
approval_ref: string | null
output_policy: summarized | redacted | link_only
slack_response_ts: string | null
durable_receipt_uri: string
redactions_applied: array
```

## Validators / Tests

- Read-only command from allowlisted workspace passes.
- Draft-only command produces a receipt but does not publish.
- Write-pending-approval command requires approval before execution.
- Destructive command is denied from Slack.
- Raw shell command is denied.
- Secret in command text is denied and redacted in receipt.
- Unknown command verb is denied by default.
- All 6 required fixtures must exist.
- Schema file must exist at expected path.
- Policy document must exist at expected path.

## Fixtures

See `tests/fixtures/slack/` for validated examples:
- `valid_read_only.json` — read-only status check (admitted)
- `valid_draft_only.json` — draft command (admitted, no publish)
- `invalid_write_without_approval.json` — write without approval (denied)
- `invalid_raw_shell.json` — raw shell command (denied, forbidden)
- `invalid_secret_exposure.json` — command with secret (denied, redacted)
- `invalid_unknown_verb.json` — unknown verb (denied)

## Namespace Audit Status

Unaudited candidates only:

- `SlackMobileCommandPolicy`
- `SlackCommandReceipt`
- `G-SLACK-*` gate names

Do not canonize or package until namespace review is receipted.
