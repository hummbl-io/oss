# Signal CLI Communication Lane Policy

**Status**: Draft — not canon until namespace review is receipted.
**Issue**: https://github.com/hummbl-io/hummbl-governance/issues/152
**Related**:
- Mobile ops ADR addendum: https://github.com/hummbl-io/hummbl-governance/issues/1149
- Signal adapter: https://github.com/hummbl-dev/hummbl-agent/issues/218
- Bus Signal lane: https://github.com/hummbl-dev/hummbl-bus/issues/2

## Purpose

Govern Signal CLI communications so Signal can be used by agents and the HUMMBL coordination bus without becoming ambient messaging authority. Signal is a notification and coordination surface, not an execution surface.

## Core Invariant

No durable state mutation, tool execution, or external write from Signal without admission, authority, executor, and receipt.

## Risk Classification

Signal-originated and Signal-bound messages are classified before routing:

| Risk class | Examples | Default |
|---|---|---|
| `notify_read_only` | digest, health summary, run blocked | Allow after recipient and event-class validation |
| `ack_only` | received, acknowledged, seen | Allow with receipt |
| `candidate_command` | inbound instruction from allowlisted person/group | Parse into candidate bus event; no direct mutation |
| `write_pending_approval` | message that triggers external action | Require approval/admission |
| `forbidden` | secrets, broad broadcast, unregistered recipient, raw shell, sensitive operational disclosure | Deny and receipt |

## Gates

| Gate ID | Description |
|---|---|
| `G-SIGNAL-RECIPIENT-ALLOWLIST` | Outbound messages only to allowlisted recipients. Unknown recipient → deny. |
| `G-SIGNAL-NO-SECOND-BUS` | Signal is not a second coordination bus. Bus events originate on the canonical bus, not Signal. |
| `G-SIGNAL-DRY-RUN-FIRST` | First outbound to a new recipient or lane must be dry-run. |
| `G-SIGNAL-RECEIPT-ROUNDTRIP` | Every sent message produces a receipt; every inbound message produces a candidate-event receipt. |
| `G-SIGNAL-NO-SECRETS` | Messages containing secret-like material (API keys, tokens, passwords) are denied or redacted before sending. |
| `G-SIGNAL-NO-SENSITIVE-OPS-DETAILS` | Operational details (hostnames, IPs, paths, account names) are redacted before sending. |
| `G-SIGNAL-RATE-LIMIT` | Rate-limit policy enforced per recipient and per lane. |
| `G-SIGNAL-INBOUND-ADMISSION` | Inbound Signal messages are never direct execution. They become candidate bus events requiring admission. |
| `G-SIGNAL-AGENT-TO-AGENT-SCOPE` | Agent-to-agent Signal messages fail unless lane scope is explicitly declared. |

## Receipt Schema

See `docs/ecosystem/schemas/signal_receipt.schema.json`.

```yaml
receipt_id: string
surface: signal
lane: notify | ack | candidate_command | agent_coordination
actor_or_agent: string
recipient_alias: string
group_alias: string | null
event_class: string
risk_class: notify_read_only | ack_only | candidate_command | write_pending_approval | forbidden
message_hash: string
message_summary: string
admission_decision: admitted | denied | pending_approval | dry_run
executor: signal-cli | null
transport_mode: json_rpc | cli | daemon | dry_run
sent_timestamp: string | null
received_timestamp: string | null
durable_uri: string
redactions_applied: array
```

## Validators / Tests

- Outbound notify message to allowlisted alias passes in dry-run mode.
- Outbound notify message to unknown recipient fails.
- Inbound Signal message is never direct execution; it becomes a candidate command/event.
- Broad broadcast without explicit lane policy fails.
- Agent-to-agent Signal message fails unless lane scope is declared.
- Message containing secret-like material fails or redacts before sending.
- Receipt requires lane, event class, risk class, admission decision, and durable URI.
- Rate-limit policy is enforced.

## Fixtures

See `tests/fixtures/signal/` for validated examples:
- `notify_allowlisted.json` — outbound notify to allowlisted recipient (admitted)
- `notify_unknown_recipient.json` — outbound notify to unknown recipient (denied)
- `inbound_candidate_command.json` — inbound message parsed as candidate event
- `broad_broadcast_denied.json` — broadcast without lane policy (denied)
- `agent_to_agent_no_scope.json` — agent-to-agent without declared scope (denied)
- `secret_redaction.json` — message with secret-like material (redacted)

## Namespace Audit Status

Unaudited candidates only:

- `SignalCommunicationPolicy`
- `SignalCommandReceipt`
- `G-SIGNAL-*` gate names

Do not canonize or package until namespace review is receipted.
