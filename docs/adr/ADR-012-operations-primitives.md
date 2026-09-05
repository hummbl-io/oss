# ADR-012 — Operations Primitives (P53-P59)

- **Status:** revised — ARCANA review findings addressed (issue #128)
- **Date:** 2026-09-04
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Verify-pass:** YELLOW (2026-09-04, conditions in Appendix B of research artifact)
- **ARCANA review:** NEEDS-REVISION → revised (5-lens, 24 findings, issue #128)

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
operationalize these concerns in practice. These skills constitute a
functioning spontaneous order — they work today. The 7 new primitives are
positioned as a **complement** to this evolved order, not a replacement: they
add enforceability, receipt-backing, and auditability to operational
discipline while the skills continue to handle procedural execution and
tacit operational knowledge that the primitives do not capture.

The full gap analysis is in
`docs/research/operations-primitives-gap-analysis-2026-09-04.md`.

## Decision

Implement 7 new operations primitives (P53-P59), all assigned to the
**Infrastructure layer** per verify-pass correction:

| ID | Name | Module | Priority | Regulatory driver | Maturity |
|----|------|--------|----------|-------------------|----------|
| P53 | SLOEngine | `slo_engine.py` | P0 | NIST AI RMF MEASURE 2.1/2.2 | declared |
| P54 | BurnRateAlerter | `burn_rate_alerter.py` | P1 | NIST AI RMF MEASURE 2.7 | declared |
| P55 | IncidentManager | `incident_manager.py` | P0 | EU AI Act Art. 73, NIST MANAGE 2.3/2.4 | declared |
| P56 | CanaryGovernor | `canary_governor.py` | P2 | ISO 42001 Annex A.6 | declared |
| P57 | PostMarketMonitor | `post_market_monitor.py` | P1 | EU AI Act Art. 72 | declared |
| P58 | RunbookRegistry | `runbook_registry.py` | P3 | ISO 42001 Clause 8.1 | declared |
| P59 | FleetStatusAggregator | `fleet_status.py` | P2 | NIST AI RMF MEASURE 2.2 | declared |

**Maturity field**: `declared` → `implemented` → `accepted` → `verified`.
Compliance claims are prohibited below `verified`. The regulatory driver
column indicates alignment intent, not achieved compliance.

Implementation order: P53 → P54 → P55 → P57 → P56 → P59 → P58

(P54 BurnRateAlerter moved ahead of P55 IncidentManager so the automated
trigger source ships before the incident detection primitive that depends
on it. P55 can accept manual incident creation in the interim if P54 is
delayed.)

## Conditions (from verify-pass + ARCANA review)

1. **Layer assignment:** All 7 primitives assigned to Infrastructure
   layer. P55, P56, P57 were originally proposed as Evidence/Containment
   but corrected to Infrastructure to avoid 6 layer dependency violations.
   **Institutional fit note (ARCANA P2-8):** P55 (fleet-scale), P56
   (service-scale), and P57 (regulatory-scale) operate at different
   governance scales but share the Infrastructure layer for technical
   dependency reasons. If scale-specific behavior is needed, it will be
   handled via configuration within each primitive, not via layer
   reassignment.

2. **Thread safety (ARCANA P1-1):** New stateful primitives (P53, P54,
   P55, P56) must use `threading.Lock` following the `circuit_breaker.py`
   pattern. **Pre-existing thread-safety debt in `health_probe.py` and
   `lifecycle.py` must be remediated in the same PR** as the first new
   primitive that shares an operational path with them (P53 SLOEngine).
   A two-tier safety regime in safety-critical infrastructure is
   unacceptable — the weakest link determines system safety.

3. **P56 rollback execution (ARCANA P1-2):** P56 CanaryGovernor must
   route rollback **execution** through P28 Rollback or a P28-validated
   execution channel. The declaration-execution split is eliminated: P28
   validates and P56 executes via a P28-validated entry point. A
   tamper-evident audit record links the governance declaration to the
   executed action. No ungoverned action channel may exist in a canary
   rollback primitive.

4. **Enforcement model (ARCANA P1-3):** The enforcement actor is the
   **Kernel** (acting on operator-configured rules). The enforcement
   target is the **AI agent or service** being governed. The graduated
   sanctions ladder:
   - **Level 0 (warning):** SLO approaching breach — log + notify
   - **Level 1 (throttle):** Error budget exhausted — reduce request rate
   - **Level 2 (suspend):** Repeated violations — halt new deployments
   - **Level 3 (revoke):** Safety violation — kill switch activation
   Due-process path: governed agents may contest enforcement actions via
   the contestability primitive (D6). Contested actions are logged with
   full receipt chain for operator review.

5. **Compliance claims (ARCANA P1-4):** The Consequences section below
   uses the maturity field. No compliance value is asserted for
   primitives below `verified` maturity. Regulatory drivers in the
   decision table indicate alignment intent only.

6. **IP attribution:** Module docstrings must include source attributions:
   - Google SRE Workbook (CC BY 4.0) — for SLI/SLO/error budget/MWMBR
   - Microsoft Agent SRE Governance 1.0 (MIT) — for incident detection/response
   - NIST AI RMF (public domain) — for MEASURE/MANAGE function mapping

7. **Test coverage (ARCANA P2-1):** Each primitive ships with tests in
   the same PR. Minimum 80% line coverage across all modules, plus:
   - **≥95% branch coverage** on safety-critical paths (rollback
     execution, incident escalation, alert firing logic, kill switch
     triggers)
   - **At least one misuse/abuse test case per primitive** (invalid
     inputs, partial failures, concurrent state mutation, attempted
     audit record tampering)
   - The uncovered 20% must be identified and justified as non-critical

8. **Registration:** Each new module exported from
   `hummbl_governance/__init__.py` and registered in `MODULE_LAYERS` in
   `scripts/check_layer_dependencies.py`.

9. **MCP server scope (ARCANA P2-2):** The proposed `mcp_ops` MCP server
   is deferred to a separate PR per fleet PR scope policy. **Interim
   risk acknowledged:** during the gap between primitive implementation
   and MCP tool exposure, the primitives are library-only and not
   fleet-invokable. The existing 26+ ops skills continue to handle
   fleet-invokable operational workflows. A minimal read-only MCP
   surface (SLO status, incident state, fleet status queries) may be
   bundled with the primitive PR if scope allows.

10. **Operator acceptance criteria (ARCANA P2-3):** Operator acceptance
    requires:
    - (a) All P1 ARCANA findings resolved or explicitly risk-accepted
    - (b) Test suite passing with the risk-weighted coverage model
    - (c) Thread-safety remediation in `health_probe.py` and
      `lifecycle.py` verified
    - (d) P56 rollback execution through P28 validated by integration test
    - (e) Enforcement sanctions ladder documented and tested
    Acceptance is not a binary gate — operators may request
    modifications before final acceptance.

11. **Tacit-knowledge preservation (ARCANA P2-11):** For each primitive,
    document which existing ops skills' behavior it encodes and what
    tacit operational knowledge those skills contain that the primitive
    does not capture. The 26+ ops skills are not deprecated by these
    primitives — they continue to handle procedural execution.

12. **Post-deployment feedback (ARCANA P2-14):** Each primitive must emit
    usage telemetry (invocation count, enforcement actions taken,
    operator overrides). A periodic review (quarterly) evaluates
    primitive utility. Low-utility primitives are candidates for
    revision or retirement.

## Consequences

- **Positive:** Closes the operations primitives gap; makes fleet ops
  discipline enforceable and receipt-backed via a defined sanctions
  ladder; provides primitives that **enable** EU AI Act Art. 72-73 and
  NIST AI RMF alignment once implemented and verified; aligns with
  Microsoft Agent SRE spec; complements the existing 26+ ops skills
  rather than replacing them.
- **Negative:** 7 new modules increase the primitive count from 44 to 51
  and require ~1400 LOC of implementation + ~1120 LOC of tests, plus
  thread-safety remediation in 2 existing modules. The risk-weighted
  coverage model requires targeted ≥95% coverage on safety-critical
  paths. Thread-safety remediation in `health_probe.py` and
  `lifecycle.py` is now in-scope and adds to the implementation burden.
- **Neutral:** The `mcp_ops` MCP server is deferred but will add ~15-20
  tools when implemented, bringing total tool count from 57 to ~72-77.
  During the interim, primitives are library-only.

## References

- Research artifact: `docs/research/operations-primitives-gap-analysis-2026-09-04.md`
- ARCANA review: issue #128 (5-lens, 24 findings, NEEDS-REVISION → revised)
- NIST AI RMF 1.0: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- EU AI Act Art. 72: https://overview.legal/laws/ai-act/art-72
- EU AI Act Art. 73: https://overview.legal/laws/ai-act/art-73
- Microsoft Agent SRE Governance 1.0: https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/specs/AGENT-SRE-GOVERNANCE-1.0.md
- Google SRE Workbook — Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
- Google SRE Workbook — Implementing SLOs: https://sre.google/workbook/implementing-slos/
- Ledger entries: clp-939a3dfa7a2e, clp-531e423c23fc, clp-07465cf94f8b, clp-2043ea9281f2
