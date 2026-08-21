# Slack Mobile Command Surface Policy

**Status**: Draft — not canon until namespace review is receipted.
**Issue**: https://github.com/hummbl-io/hummbl-governance/issues/151

## Purpose

Govern Slack-originated mobile commands so Slack can serve as an ingress cockpit for HUMMBL agent/tool execution without becoming an execution surface itself. Slack is ingress and cockpit, not executor or authority.

## Core Invariant

No durable state or tool mutation from Slack without admission, authority, executor, and receipt.

## Risk Classification

Slack-originated commands are classified before routing:

| Risk class | Examples | Default |
|---|---|---|
| `read_only` | status, health, queue, recent receipts | Allow after actor/channel validation |
| `draft_only` | draft issue, draft PR plan, draft message | Allow with receipt, no external write |
| `write_pending_approval` | create issue, send message, modify file, run agent with write permissions | Require explicit approval |
| `destructive` | delete, revoke, deploy rollback, kill process, alter secrets | Require elevated gate / may deny by default |
| `forbidden` | secrets exfiltration, raw shell, credential exposure, private mesh intel disclosure | Deny and receipt |

## Gates

| Gate ID | Description |
|---|---|
| `G-SLACK-NO-SECRETS` | Commands containing secret-like material (API keys, tokens, passwords) are denied or redacted. |
| `G-SLACK-SCOPE-MINIMUM` | Commands must declare minimum scope; broad-scope commands denied by default. |
| `G-SLACK-AUTHORITY-BOUNDARY` | Actor authority is checked against requested action; unauthenticated actors denied. |
| `G-SLACK-DRAFT-FIRST` | Write-class commands must produce a draft before execution; no direct write from Slack. |
| `G-SLACK-APPROVAL-BEFORE-WRITE` | Write-class commands require explicit approval before execution. |
| `G-SLACK-RECEIPT-ROUNDTRIP` | Every command produces a receipt with actor, authority, admission decision, and durable URI. |
| `G-SLACK-THREAD-COMPRESSION` | Long threads are compressed before response; full context linked, not inlined. |
| `G-SLACK-LOST-PHONE-KILL` | Lost-device procedure revokes Slack-originated authority immediately. |

## Receipt Schema

See `docs/ecosystem/schemas/slack_command_receipt.schema.json`.

```yaml
receipt_id: string
surface: slack
workspace_id_hash: string
channel_id_hash: string
thread_ts: string
actor_id_hash: string
received_at: iso8601
command_text_hash: string
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

- Valid read-only status command receipt passes.
- Draft-only issue request passes but marks external write as false.
- Write command without approval fails admission.
- Raw shell command fails admission.
- Secret-looking command/output fails or redacts according to policy.
- Sensitive mesh/local identifiers are not allowed in public receipts.
- Receipt requires actor, authority, executor target or null executor, admission decision, and durable URI.
- Unknown command verbs are denied by default.
- Slack output policy enforces summarization/redaction/link-only modes.

## Fixtures

See `tests/fixtures/slack/` for validated examples:
- `valid_read_only.json` — status command (admitted)
- `valid_draft_only.json` — draft issue request (admitted, no external write)
- `invalid_write_without_approval.json` — write command without approval (denied)
- `invalid_raw_shell.json` — raw shell command (denied)
- `invalid_secret_exposure.json` — secret in command (denied, redacted)
- `invalid_unknown_verb.json` — unknown command verb (denied by default)

## Namespace Audit Status

Unaudited candidates only:

- `SlackCommandReceipt`
- `SlackMobileCommandPolicy`
- `G-SLACK-*` gate names

Do not canonize or package these names until audited and receipted.
