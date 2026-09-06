# AAR: Base120 MCP Product Canary | PUBLIC | 20260905-2357Z | codex

═══════════════════════════════════════════════════════════════════

## 1. Mission & Intent (P6: Point-of-View Anchoring)

- **Objective**: Build one sanitized, consumable Base120 MCP canary in
  `hummbl-io/oss` without exposing fleet internals or prematurely publishing a
  product.
- **Success criteria**: Four bounded read-only tools; deterministic catalog
  generation and provenance; no network egress, telemetry, mutation, or durable
  writes; passing tests and public-boundary checks; a signed PR with explicit
  admission gates.
- **Constraints**: Work in an isolated branch/worktree, preserve dirty shared
  checkouts, avoid the active `hummbl-production` lane, add no external runtime
  dependency, and do not publish, deploy, merge, or contact customers.
- **Intent receipt**: Canonical bus `WIP_START`,
  `2026-09-05T23:23:32Z`, lane
  `feat/codex/base120-product-canary-20260905`.

## 2. Chronology (RE17: Versioning & Diff)

| Time/Commit | Action | Result / receipt |
|-------------|--------|------------------|
| `2026-09-05T23:23:32Z` | Claimed the canary lane and bounded external actions. | Canonical bus `WIP_START`; scope named `oss`, with publish, deploy, and customer contact prohibited. |
| Session test cycle | Wrote tests before the catalog/server implementation and exercised red-to-green behavior. | Session command receipts: first `npm test` failed because the server exports did not yet exist; final `npm test` passed 21 tests. |
| Session specification check | Compared the implementation with the current MCP protocol and expanded it to dual-era behavior. | [`src/server.mjs`](../../packages/node/mcp-base120/src/server.mjs) supports `2026-07-28`, `2025-11-25`, and `2025-06-18`; official [MCP versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) defines the modern/legacy split. |
| `fc5cb14` | Committed the technical canary, product boundary, generated data, tests, and CI changes. | Signed commit `fc5cb14b67a19b59a34c50758f92ff35809d0568`; `git diff --stat origin/main..HEAD` reported 24 files, 2,144 insertions, and 17 deletions. |
| `2026-09-05T23:53:32Z`–`23:54:53Z` | Ran public exact-head workflows on PR #138. | GitHub runs `33999853958`, `33999854183`, and `33999853960` completed successfully at head `fc5cb14`; `ci-ok` succeeded. |
| `2026-09-05T23:55:26Z` | Posted the implementation SITREP. | Canonical bus request `5b66f2964f3c4f71a586ba94e6d81047`; recorded 21 passing tests, 95.79% line coverage, 83.16% branch coverage, zero npm vulnerabilities, and admission `HOLD`. |
| `2026-09-05T23:55:28Z` | Closed the implementation lane. | Canonical bus request `155eb0677fb540c288257a5e25d12f34`; PR #138 recorded as mergeable and ready for Reuben's merge decision. |

## 3. Outcome vs Plan (IN17: Counterfactual Negation)

- **Planned**: Produce one sanitized Base120 canary that demonstrates how an
  internal capability can become a bounded consumable, while preventing public
  release until product-admission gates are satisfied. Receipt: bus
  `WIP_START` at `2026-09-05T23:23:32Z`.
- **Actual**: PR [#138](https://github.com/hummbl-io/oss/pull/138) contains a
  private, zero-dependency `@hummbl/mcp-base120` package with four tools,
  catalog/provenance verification, sanitization, tests, Node CI, and a product
  manifest. Receipt: signed commit `fc5cb14`; [`product.json`](../../packages/node/mcp-base120/product.json).
- **Actual validation**: Exact-head CI completed with 37 successful checks,
  one neutral check, one skipped preview, and zero failures. Local coverage was
  95.79% lines and 83.16% branches. Receipts: `gh pr view 138`; Tests run
  `33999853958`; bus SITREP at `2026-09-05T23:55:26Z`.
- **Delta**: The repository canary is public source but remains a private,
  non-publishable package. Corpus licensing, public-release provenance, hosted
  contract parity, and privacy review remain open. Receipt:
  [`product.json`](../../packages/node/mcp-base120/product.json).
- **Delta**: No `hummbl-production` integration, npm publication, hosted
  deployment, merge, or customer action occurred. Receipts: bus `WIP_START` and
  `WIP_END`; [`SECURITY.md`](../../packages/node/mcp-base120/SECURITY.md).

## 4. Root Causes (DE1: Root Cause Analysis)

### Deviation: source is reviewable, but the package is not launchable

- **Why 1**: The product manifest sets `admission.decision` to `hold` and
  `public_launch` to `false`.
- **Why 2**: Four gates lack completed receipts: corpus license, public-release
  provenance, hosted contract parity, and privacy review.
- **Root cause**: The canonical Base120 notice distinguishes its Apache-2.0
  software license from commercial use of the structured corpus. Receipt:
  `packages/python/base120/NOTICE:52-60`. Release rights therefore require an
  explicit decision before npm redistribution.

### Deviation: production integration was deferred

- **Why 1**: The canary implements local stdio only; authentication, HTTP,
  multi-tenancy, billing, and hosted telemetry are outside its boundary.
- **Why 2**: The operation explicitly excluded the active
  `hummbl-production` lane and prohibited deployment until gates passed.
- **Root cause**: This operation was scoped as a technical proof of the
  sanitization/product boundary, not a hosted-product launch. Receipts:
  canonical bus `WIP_START`; package [`SECURITY.md`](../../packages/node/mcp-base120/SECURITY.md).

### Deviation: automated AAR finalization was unavailable

- **Why 1**: `Get-Command aar-finalize` returned command-not-found on Anvil.
- **Why 2**: No `aar-finalize` script was found in the configured fleet skill
  roots or host utility directory.
- **Root cause**: The AAR skill documents a finalize shortcut that is not
  installed or discoverable on this Windows host. Receipt: AAR evidence-gathering
  command output from `2026-09-05T23:56Z`.

## 5. Sustains (RE16: Retrospective -> Prospective Loop)

- Isolated-worktree execution preserved dirty shared checkouts and prevented
  cross-lane edits — evidence: worktree
  `oss-base120-product-canary-20260905`; bus `WIP_START`.
- Test-first development exposed missing behavior before implementation and
  ended with 21 passing tests — evidence: session `npm test` red/green receipts
  and Tests run `33999853958`.
- The current-protocol check prevented shipping a legacy-only MCP surface —
  evidence: [`src/server.mjs`](../../packages/node/mcp-base120/src/server.mjs)
  and the official MCP `2026-07-28` versioning specification.
- The package boundary is executable rather than descriptive: generated-data
  drift, packed files, prohibited text, secrets, and CI are checked — evidence:
  [`check-package-boundary.mjs`](../../packages/node/mcp-base120/scripts/check-package-boundary.mjs),
  Boundary run `33999854183`, and Tests run `33999853958`.
- Product ambition and release authority stayed separate — evidence:
  [`product.json`](../../packages/node/mcp-base120/product.json) retains explicit
  blockers while PR #138 remains open and mergeable.

## 6. Improves (IN20: Antigoals & Anti-Patterns Catalog)

- Protocol freshness was checked after the first implementation cycle rather
  than before test design — evidence: session command order showed initial
  `2025-06-18` expectations before the official `2026-07-28` check.
- The tests exercise the wire contract directly but do not yet include an
  interoperability smoke test with a Tier 1 official MCP SDK — evidence:
  [`package.json`](../../packages/node/mcp-base120/package.json) has zero
  dependencies and the test tree uses the local handler/CLI.
- `product.json` is machine-readable but its `hummbl.product.v1` shape is not
  backed by a committed JSON Schema or reusable repository validator — evidence:
  [`product.json`](../../packages/node/mcp-base120/product.json) and
  [`cli-and-product.test.mjs`](../../packages/node/mcp-base120/test/cli-and-product.test.mjs).
- The nominal `Devin Review` status cannot be counted as substantive independent
  review because the check description reported that full review was skipped —
  evidence: session `gh pr checks 138` receipt. Treat it as neutral operational
  metadata, not a review gate.
- The AAR skill's documented finalize command is unavailable on Anvil, forcing
  manual section validation and bus posting — evidence: `Get-Command
  aar-finalize` command-not-found receipt.

## 7. Recommendations (DE7: Pareto Decomposition)

1. **[HIGH] Resolve and record the Base120 corpus distribution/license decision**
   before changing `private` or `public_launch` — addresses the primary product
   admission blocker.
2. **[HIGH] Promote the canary manifest into a versioned product-admission JSON
   Schema and repository validator** — turns this one canary into a repeatable
   factory gate for MCP servers, APIs, SDKs, ADKs, and agent toolkits.
3. **[MED] Add an isolated official-SDK interoperability smoke test** for both
   modern discovery and one legacy initialization path, without adding a runtime
   dependency — addresses protocol conformance confidence.
4. **[MED] Restore a cross-platform `aar-finalize` command or update the AAR
   skill with an explicit Windows fallback** — removes manual finalization and
   receipt drift.
5. **[LOW] Design hosted parity, privacy, authentication, and rate-limit gates
   only after the license decision** — preserves the local canary's boundary
   while sequencing investment behind the controlling constraint.

---
Base120 Applied: P6, RE17, IN17, DE1, RE16, IN20, DE7
Evidence: `fc5cb14`; PR #138; GitHub runs `33999853958`, `33999854183`, `33999853960`; canonical bus requests `5b66f2964f3c4f71a586ba94e6d81047`, `155eb0677fb540c288257a5e25d12f34`, `c70a0ae70941415e9f7c9be617771ef9`
Bus: Y (AAR SITREP accepted `2026-09-06T00:01:07Z`; request `c70a0ae70941415e9f7c9be617771ef9`; manual fallback because `aar-finalize` is unavailable on Anvil)
