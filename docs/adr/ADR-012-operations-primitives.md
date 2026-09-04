# ADR-012 — Operations Primitives (P53-P59)

- **Status:** proposed — operator acceptance required before implementation begins
- **Date:** 2026-09-04
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Verify-pass:** YELLOW (2026-09-04, conditions in Appendix B of research artifact)

## Context

HUMMBL Governance ships 44 implemented primitives (P1-P52) covering safety,
identity, audit, reasoning, coordination, behavior/health, physical-AI, and
governance Kernel concerns. **Operations primitives** — the SRE/operations
discipline that governs how AI agents run in production — are
underrepresented: only 3 of 44 primitives (P2 CircuitBreaker, P18
HealthProbe, P19 Lifecycle) directly address operational concerns, and none
implement SLOs, error budgets, incident management, canary deployment
governance, post-market monitoring, or alerting as first-class governance
primitives.

The fleet has 26+ ops skills (canary-deploy, slo-define, incident,
postmortem, rollback, deploy-health, alert-rule, runbook-write, etc.) that
operationalize these concerns in practice, but the skills are procedural
shell workflows with no backing governance primitive in the library. This
creates a gap: the fleet's operational discipline is not enforceable,
receipt-backed, or auditable through the governance Kernel.

The full gap analysis is in
`docs/research/operations-primitives-gap-analysis-2026-09-04.md`.

## Decision

Implement 7 new operations primitives (P53-P59), all assigned to the
**Infrastructure layer** per verify-pass correction:

| ID | Name | Module | Priority | Regulatory driver |
|----|------|--------|----------|-------------------|
| P53 | SLOEngine | `slo_engine.py` | P0 | NIST AI RMF MEASURE 2.1/2.2 |
| P54 | BurnRateAlerter | `burn_rate_alerter.py` | P1 | NIST AI RMF MEASURE 2.7 |
| P55 | IncidentManager | `incident_manager.py` | P0 | EU AI Act Art. 73, NIST MANAGE 2.3/2.4 |
| P56 | CanaryGovernor | `canary_governor.py` | P2 | ISO 42001 Annex A.6 |
| P57 | PostMarketMonitor | `post_market_monitor.py` | P1 | EU AI Act Art. 72 |
| P58 | RunbookRegistry | `runbook_registry.py` | P3 | ISO 42001 Clause 8.1 |
| P59 | FleetStatusAggregator | `fleet_status.py` | P2 | NIST AI RMF MEASURE 2.2 |

Implementation order: P53 → P55 → P54 → P57 → P56 → P59 → P58

## Conditions (from verify-pass)

1. **Layer assignment:** All 7 primitives assigned to Infrastructure
   layer. P55, P56, P57 were originally proposed as Evidence/Containment
   but corrected to Infrastructure to avoid 6 layer dependency violations.
2. **Thread safety:** New stateful primitives (P53, P54, P55, P56) must
   use `threading.Lock` following the `circuit_breaker.py` pattern.
   Pre-existing thread-safety debt in `health_probe.py` and
   `lifecycle.py` is acknowledged but out of scope for this ADR.
3. **P28 composition semantics:** P56 CanaryGovernor validates rollback
   declarations via P28 Rollback but executes rollback via its own
   mechanism. P28 is a validation/declaration API, not an execution API.
4. **IP attribution:** Module docstrings must include source attributions:
   - Google SRE Workbook (CC BY 4.0) — for SLI/SLO/error budget/MWMBR
   - Microsoft Agent SRE Governance 1.0 (MIT) — for incident detection/response
   - NIST AI RMF (public domain) — for MEASURE/MANAGE function mapping
5. **Test coverage:** Each primitive ships with tests in the same PR.
   ~1120 LOC of tests minimum across 7 modules (80% coverage threshold).
6. **Registration:** Each new module exported from
   `hummbl_governance/__init__.py` and registered in `MODULE_LAYERS` in
   `scripts/check_layer_dependencies.py`.
7. **MCP server scope:** The proposed `mcp_ops` MCP server (Part V of
   research artifact) is deferred to a separate PR from primitive
   implementation, per fleet PR scope policy (>3 unrelated changesets =
   BLOCKING flag).

## Consequences

- **Positive:** Closes the operations primitives gap; makes fleet ops
  discipline enforceable and receipt-backed; provides EU AI Act Art.
  72-73 compliance primitives; aligns with Microsoft Agent SRE spec.
- **Negative:** 7 new modules increase the primitive count from 44 to 51
  and require ~1400 LOC of implementation + ~1120 LOC of tests. The
  80% coverage threshold must be maintained across all new modules.
- **Neutral:** The `mcp_ops` MCP server is deferred but will add ~15-20
  tools when implemented, bringing total tool count from 57 to ~72-77.

## References

- Research artifact: `docs/research/operations-primitives-gap-analysis-2026-09-04.md`
- NIST AI RMF 1.0: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- EU AI Act Art. 72: https://overview.legal/laws/ai-act/art-72
- EU AI Act Art. 73: https://overview.legal/laws/ai-act/art-73
- Microsoft Agent SRE Governance 1.0: https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/specs/AGENT-SRE-GOVERNANCE-1.0.md
- Google SRE Workbook — Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
- Google SRE Workbook — Implementing SLOs: https://sre.google/workbook/implementing-slos/
- Ledger entries: clp-939a3dfa7a2e, clp-531e423c23fc, clp-07465cf94f8b, clp-2043ea9281f2
