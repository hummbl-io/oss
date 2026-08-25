# Signal Lane Policy

`hummbl-bus` remains the source of truth. Signal is a **transport-only** lane for selected coordination alerts.

## Positioning

- Do not mirror the full bus into Signal.
- Do not use Signal messages as a source-of-truth state.
- Do not trigger bus mutations from inbound Signal replies without admission.

## Allowed Event Classes

The following message classes are allowed for Signal transport:

- `agent_blocked`
- `approval_needed`
- `circuit_breaker_triggered`
- `gateway_health_degraded`
- `receipt_digest`
- `human_ping`
- `agent_ack`

## Message Shape

Each Signal message SHOULD include:

- `priority` (low / medium / high)
- short summary
- `receipt_id` (where available)
- `action_needed`
- `durable_uri`

Keep payloads concise for manual review.

## Operational Policy

- Default mode: `dry_run` until the bus policy owner publishes approvals.
- Dry-run behavior:
  - validate destination and class mapping
  - emit a receipt for every candidate
  - do not deliver messages until explicit enablement changes
- Rate limit: 6 messages/hour max
- Max message length: 900 chars
- Require `receipt_id` when available
- Dry-run and production channels must emit receipts

## Security Boundaries

- Never include phone numbers, identities, group IDs, raw file paths, keys, tokens, or secrets.
- Signal messages must include `receipt_id` or `receipt_uri` links to avoid private content being embedded in clear text.
- Transport failures, drops, and retries are logged as receipts.

## Inbound Acknowledgements

Signal replies are **candidate events only**. They must be:

1. parsed as untrusted text
2. normalized against explicit command patterns
3. admitted through normal bus workflows before any state changes

Inbound replies without a matching receipt reference are routed to a manual review bucket.

## Non-Goals

- No claim of operational or emergency service guarantees.
- No commitment on transport delivery SLAs.
- No architectural commitment to one Signal deployment pattern.
