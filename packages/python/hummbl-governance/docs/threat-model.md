# Threat Model — hummbl-governance

**Scope**: `hummbl_governance` package — governance kernel (admission
control, mutation gate, receipt engine, kill switch, circuit breaker,
recovery verifier), delegation tokens, contract enforcement, HTTP API
server, MCP stdio servers.
**Assessed**: 2026-09-22, git SHA `86d70b3dfe409d95750981f94f2754dc7f6b0b55`
(`oss/packages/python/hummbl-governance`)
**Status**: draft — requires second-party review (GAP-6 acceptance criterion)

## Assets

- **Policy integrity** — admission control, authority policy, and
  invariants decide what agents may do; bypass = ungoverned execution.
- **Receipt/audit integrity** — `kernel/receipt_engine.py`,
  `transition_receipt.py`, and the append-only evidence chain.
- **Delegation token authority** — `delegation.py` issues HMAC-SHA256 or
  Ed25519-signed capability tokens; forgery = privilege escalation.
- **API surface secrets** — `GOVERNANCE_API_TOKEN` /
  `GOVERNANCE_API_TOKEN_FILE`.
- **Kill-switch effectiveness** — the guarantee that graduated halt
  actually halts.
- **Human-review independence** — `human_review_gate.py` enforces
  non-author approval; subverting it removes the accountability link.

## Adversaries

- Malicious or prompt-injected agent seeking to exceed granted authority.
- External attacker reaching the HTTP API server.
- Local attacker modifying policy files, receipts, or the audit chain.
- Supply-chain adversary (runtime deps minimal; dev toolchain broader).
- Insider collusion: author self-approving via review-gate bypass.

## Attack surfaces

- `api_server.py` — `http.server.HTTPServer` with Bearer-token auth;
  fail-closed when `GOVERNANCE_API_TOKEN` configured-required
  (`_require_api_auth`, `api_server.py:79-183`).
- MCP stdio servers (`mcp_server.py` + `mcp_*.py`) — JSON-RPC tool
  surface; input crosses into kernel operations.
- Kernel mutation path — `kernel/mutation_gate.py` mediates state
  changes; bypass writes governed state unchecked.
- Policy/schema inputs — `data/*.schema.json` validated artifacts;
  malformed or hostile inputs reach validators.
- Delegation-token verification — signature and claims checking.
- Recovery/rollback path — `kernel/recovery_verifier.py`,
  `data/rollback.schema.json`.

## Trust boundaries

1. **HTTP request → API handler**: bearer auth is the boundary;
   unauthenticated reachability must fail closed.
2. **MCP stdio → kernel**: tool arguments cross from the MCP host into
   admission/mutation paths.
3. **Agent action → admission_control**: every governed action crosses
   the policy gate; the gate is the boundary between declared and
   effective authority.
4. **Policy files ↔ engine**: policy-as-data is untrusted input until
   schema-validated.
5. **Token issuance → token presentation**: delegation tokens cross
   time/process boundaries; verification must be replay- and
   forgery-resistant.

## Threat scenarios

| # | Scenario | Vector | Current control |
|---|----------|--------|-----------------|
| T1 | Ungoverned action via gate bypass | caller skips admission_control | kernel wiring tests (`test_k9_k11_kernel_wiring.py`) pin the gate in the path; **caller discipline still required** |
| T2 | Delegation-token forgery | crafted/unsigned token | HMAC-SHA256 or Ed25519 signature verification; claim checks |
| T3 | Token replay | captured token reused | token claims (expiry/scope) — **verify expiry enforcement is on the verifier path** |
| T4 | API auth bypass | no token configured → open endpoint | `_require_api_auth` fail-closed mode when auth is mandatory |
| T5 | Receipt tampering | modify ledger post-write | receipt schemas + `receipt_integrity_monitor.py`; HMAC/hashing of content (see hummbl-bus model for transport) |
| T6 | Policy injection | hostile policy data | JSON-schema validation on admission; malformed policies rejected |
| T7 | Kill-switch circumvention | agent ignores halt signal | kill switch is kernel-mediated (enforced at gate, not advisory) |
| T8 | Self-approval | author acts as own reviewer | `human_review_gate.py` enforces non-author review; evidence_readiness review receipts |
| T9 | Recovery-path abuse | rollback to known-vulnerable state | `recovery_verifier.py` verifies recovery targets; rollback schema constrains targets |
| T10 | DoS via admission spam | flood policy gate | **gap: no rate limiting in-module** — deployment-level concern |
| T11 | Schema-validation oracle | malformed input probes validator | schemas reject by default; error paths reviewed for info leakage (none observed beyond type messages) |
| T12 | Supply-chain (build deps) | trojanized build backend | stdlib-only runtime; reproducible-wheel procedure in BUILD.md (oss PR #267) pins backend + expected hash |

## Mitigations (current controls)

- Fail-closed API auth (401 when token required but unconfigured)
- Kernel-mediated admission/mutation — gates are structural, not advisory
- Cryptographic delegation tokens (HMAC-SHA256 / Ed25519)
- Schema-validated policy and receipt artifacts (`data/*.schema.json`)
- Append-only receipt stream with integrity monitoring
- Non-author review enforcement at the merge boundary
- Kill switch + circuit breaker as kernel-level halt/isolation
- 3496-test suite green under process-level egress isolation
  (hummbl-compliance PR #14); runtime is offline-capable

## Residual risk

- **Physical/host compromise**: kernel guarantees assume the host Python
  process is not itself subverted — in-process agents with arbitrary
  code exec can in principle bypass gates. The model governs
  *cooperating* agents; fully adversarial in-process code is out of
  scope and requires sandboxing (see `sandbox_contracts.py`).
- **HTTP API transport**: module does not terminate TLS; deployments
  must front it or bind loopback.
- **Token lifecycle**: rotation/revocation lists are deployment-owned.
- **Build artifacts**: release-artifact builds require network
  (pip build isolation) — see air-gap receipt; offline builds need
  `--no-build-isolation` (BUILD.md, oss PR #267).
- **FIPS gap**: no CMVP-validated crypto module (see hummbl-compliance
  PR #15 — applies transitively to delegation-token signing).

## Second-party review

[PENDING — required by GAP-6 acceptance criteria. Reviewer should
challenge T1 (in-process bypass scope), T3 (replay window), and the
residual-risk boundary statements.]
