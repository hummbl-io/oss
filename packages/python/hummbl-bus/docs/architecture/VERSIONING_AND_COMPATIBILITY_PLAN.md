# Versioning and Compatibility Plan

Status: PROPOSED

One number cannot safely describe package code, stored data, HTTP behavior,
deployment state, and configuration. HUMMBL Bus therefore needs parallel,
explicitly related version axes.

## Version axes

| Axis | Identifier | Governs | Current observed state |
|---|---|---|---|
| Package/API | `package_version` | Python imports, callable signatures, CLI | `0.1.0` |
| Wire | `wire_version` | five-column TSV and message-column representation | implicit legacy v1 |
| Structured event | `event_schema` | JSON structured-event discriminator and fields | two incompatible v1 names |
| Signed envelope | `envelope_version` | `{c,n,s}` meaning and HMAC canonicalization | implicit v1 |
| Bridge HTTP | `bridge_api_version` | endpoints, request/response/error contract | deployed health says `1.3`; package contract not frozen |
| Replay ledger | `replay_schema` | request identity, outcome, retention, recovery | founder-only implementation |
| Spool/dead letter | `delivery_schema` | offline record and disposition semantics | founder-only plus separate legacy queue |
| Configuration | `config_schema` | environment variables, paths, enforcement defaults | divergent founder/package names |
| Deployment | `deployment_revision` | exact package/config/service/task hashes per host | unversioned |

Every release manifest must declare all axes. Package SemVer must not silently
stand in for a wire or deployment version.

The machine-readable Phase 0 baseline is
[`version-manifest.phase0.json`](version-manifest.phase0.json).

## Compatibility classes

- `EXACT`: byte and behavior equivalent.
- `BACKWARD_READ`: new reader accepts old artifact without rewriting it.
- `BACKWARD_WRITE`: new writer emits an artifact accepted by the old reader.
- `ADAPTER`: compatibility requires a named, versioned adapter.
- `MIGRATION`: explicit offline or shadow migration required.
- `INCOMPATIBLE`: must fail closed with an actionable error.
- `UNKNOWN`: blocked; never inferred compatible from ordinal version numbers.

Compatibility is directional. A dual reader may accept both schema names while
an old reader rejects the neutral successor schema. The matrix must state both
directions and must not assume higher versions include lower-version behavior.

## Release train

### `0.1.x` — evidence baseline

Documentation, golden-corpus fixtures, inventories, and corrections only. No
claim of canonical status. Tags begin only after the repository state and
release procedure are reconciled.

### `0.2.0` — compatibility core

- Preserve the existing 15-name facade and three CLI entry points.
- Preserve byte-compatible five-column TSV and `{c,n,s}` HMAC envelope.
- Dual-read `hummbl_governance.bus.event.v1` and `hummbl_bus.event.v1`.
- Split the monolithic writer internally while retaining direct-import adapters.
- Add golden tests for Unicode, escaping, timestamps, signed/unsigned legacy
  rows, malformed input, and historical corpus reads.
- No production cutover.

### `0.3.0` — reliable delivery candidate

- Add authenticated and authorized reads.
- Add principal-to-sender binding, freshness enforcement, persistent atomic
  request idempotency, replay ledger, spool, replay worker, seed import, bounds,
  error taxonomy, path/SSRF controls, and real fsync durability.
- Validate Windows and POSIX thread/process concurrency.
- Run a single-writer, dual-reader canary behind a feature flag.

### `0.4.0` — optional governance adapters

- Add configurable privileged-type policy, capability/principal proof adapter,
  auditor integration, and optional asymmetric signing dependencies.
- Keep founder identity constants and orchestration policy outside the core.
- Work-queue/lane/tier behavior remains an optional extension, not core.

### `1.0.0` — canonical stable contract

- Adopt a neutral structured-event schema only after the announced dual-read
  window and fleet evidence show old readers are retired or adapted.
- Freeze public API, wire compatibility, bridge error semantics, and version
  negotiation rules.
- hummbl-governance retains only a compatibility shim; no canonical implementation
  remains inside hummbl-governance.
- Publish signed artifacts, provenance, SBOM, compatibility manifest, and restore
  evidence. Production promotion remains separately authorized.

## Branch and worktree topology

Planning uses `docs/codex/phase-minus1-1-cutover-plan`. Later implementation
must use independent, non-overlapping branches:

1. `feat/codex/v020-contract-fixtures`
2. `refactor/codex/v020-writer-compat`
3. `feat/codex/v030-bridge-security`
4. `feat/codex/v030-replay-delivery`
5. `test/codex/cross-runtime-conformance`
6. `ops/codex/shadow-deployment-manifest`

Each branch receives the exact contract fixture commit rather than merging
partially completed feature branches into each other. Integration occurs through
reviewed PRs into `main`, followed by immutable release-candidate tags. Only one
deployment canary runs at a time to prevent signal contamination.

## Tagging and manifests

- Package tags: `v0.2.0`, `v0.3.0`, and so on.
- Release candidates: `v0.3.0-rc.1` following SemVer.
- Deployment revisions: signed manifest IDs such as
  `bus-deploy-20260808.1`; these are not package versions.
- Wire/schema identifiers live in artifacts and HTTP capability responses.
- A release manifest binds Git SHA, artifact hashes, all version axes, supported
  compatibility edges, tests, signer, and rollback predecessor.

## Version negotiation

Clients send their chosen bridge API version and supported compatible versions.
The server returns its chosen version and supported set. Compatibility must be
explicitly declared and tested; unknown pairs abort. Negotiation must be bound
to the authenticated exchange to prevent downgrade manipulation. A health
endpoint may reveal service/version capability but no bus content.

## Deprecation

Deprecation requires announcement, telemetry proving remaining consumers,
adapter availability, a minimum supported window, and a tested rollback.
Historical TSV is never rewritten solely to remove a schema name. Readers retire
old schema support only after all retained archives remain independently readable.
