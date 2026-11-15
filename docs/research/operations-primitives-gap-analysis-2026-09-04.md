# Operations Primitives Gap Analysis

**Research session:** 2026-09-04
**Mode:** RESEARCH (OVERNIGHT tempo)
**Agent:** devin (autonomous research session)
**Status:** PROPOSAL — verify-pass YELLOW (proceed with notes, see Appendix B)
**Verify-pass date:** 2026-09-04
**Verify-pass verdict:** YELLOW — proceed to ADR with 7 conditions (Appendix B)

---

## TL;DR

HUMMBL Governance ships 44 implemented primitives (P1-P52) covering safety,
identity, audit, reasoning, coordination, behavior/health, physical-AI, and
governance Kernel concerns. **Operations primitives** — the SRE/operations
discipline that governs how AI agents run in production — are
**underrepresented**: only 3 of 44 primitives (P2 CircuitBreaker, P18
HealthProbe, P19 Lifecycle) directly address operational concerns, and none
implement SLOs, error budgets, incident management, canary deployment
governance, post-market monitoring, or alerting as first-class governance
primitives.

The fleet has **26+ ops skills** (canary-deploy, slo-define, incident,
postmortem, rollback, deploy-health, alert-rule, runbook-write, etc.) that
operationalize these concerns in practice, but the skills are procedural
shell workflows with no backing governance primitive in the library. This
creates a gap: the fleet's operational discipline is not enforceable,
receipt-backed, or auditable through the governance Kernel.

This analysis proposes **7 new operations primitives** (P53-P59) mapped to
NIST AI RMF MEASURE/MANAGE functions, ISO 42001 Clause 8/9 requirements, EU
AI Act Articles 72-73, and Microsoft's Agent SRE Governance 1.0 spec.

---

## Part I: Current State — What Operations Primitives Exist

### Implemented operations-adjacent primitives (3 of 44)

| ID | Module | Ops concern covered | Gap |
|----|--------|---------------------|-----|
| P2 | `circuit_breaker` | Failure detection + recovery (CLOSED/HALF_OPEN/OPEN) | No SLO linkage, no error budget, no burn-rate alerting |
| P18 | `health_probe` | Composable health checks with latency tracking | No SLO definition, no SLI computation, no error budget accounting |
| P19 | `lifecycle` | NIST AI RMF orchestrator (composes KS+CB+CG+DM+AL+AR+HC) | Orchestration only — no MEASURE/MANAGE primitives to orchestrate |

### Fleet ops skills with NO backing primitive (26+ skills)

| Skill | Ops concern | Closest primitive | Gap |
|-------|-------------|-------------------|-----|
| `slo-define` | SLO/SLI definition, error budgets, burn-rate alerts | None | No SLO primitive in library |
| `canary-deploy` / `deploy-canary` | Progressive delivery governance | None | No canary/deployment-stage primitive |
| `deploy-health` | Post-deploy health verification | P18 HealthProbe (partial) | No deploy-specific verification primitive |
| `deploy-checklist` | Pre-deploy compliance checklist | None | No deployment gate primitive |
| `incident` | Incident triage (health, bus, kill-switch, CI, ports) | None | No incident primitive |
| `incident-response-plan` | AI-specific incident response plan | None | No IRP primitive |
| `incident-timeline-reconstruct` | Timeline reconstruction from logs/bus | None | No timeline reconstruction primitive |
| `postmortem` | Blameless post-incident review | None | No postmortem primitive |
| `rollback` | CD recovery with health verification | P28 Rollback (Kernel-level) | P28 is Kernel reversibility, not CD rollback |
| `alert-rule` | Alert rule definition and dispatch | None | No alerting primitive |
| `alert-digest` / `alert-noise-reduce` | Alert noise reduction | None | No alert management primitive |
| `status-page` | External status communication | None | No status-page primitive |
| `runbook-write` / `runbook-test` | Runbook authoring and testing | None | No runbook primitive |
| `disk-check` | Disk capacity monitoring | P18 HealthProbe (partial) | No capacity-threshold primitive |
| `log-tail` / `log-analyze` | Log analysis | P8 AuditLog (governance logs only) | No operational log analysis primitive |
| `process-check` | Process monitoring | None | No process-health primitive |
| `port-map` | Port exposure auditing | None | No network-surface primitive |
| `uptime-check` | Uptime monitoring | None | No uptime primitive |
| `tailscale-status` / `tunnel-check` / `ssl-check` / `dns-check` | Network health | None | No network-health primitive |
| `circuit-status` | Circuit breaker state inspection | P2 CircuitBreaker (partial) | No fleet-wide circuit status primitive |
| `kill-switch` | Kill switch engagement | P1 KillSwitch (exists) | Skill wraps existing primitive — no gap |
| `docker-manage` | Container management | None | No container governance primitive |
| `launchd` | Service management | None | No service-management primitive |
| `sitrep` | Situation report | None | No SITREP primitive |
| `fleet-status` | Fleet-wide status aggregation | None | No fleet-status primitive |
| `machine-health` | Per-machine health | P18 HealthProbe (partial) | No machine-health primitive |

**Summary:** 26+ ops skills are procedural workflows with zero backing
governance primitives. The fleet operates on discipline and convention, not
enforceable, receipt-backed governance.

---

## Part II: Regulatory and Industry Framework Mapping

### NIST AI RMF (AI 100-1) — MEASURE and MANAGE functions

The MEASURE function (Source: [NIST AI RMF 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf))
requires:

- **MEASURE 2.1**: "Appropriateness of AI metrics and effectiveness of
  existing controls is regularly assessed and updated including reports of
  errors and impacts on affected communities."
- **MEASURE 2.2**: "The functionality and behavior of the AI system and its
  components are monitored when in production."
- **MEASURE 2.5**: "AI system is evaluated regularly for safety risks."
- **MEASURE 2.7**: "Monitoring, and response times for AI system failures."

The MANAGE function requires:

- **MANAGE 2.1**: "Resources required to manage AI risks are identified and
  prioritized."
- **MANAGE 2.3**: "Failure responses are considered and documented."
- **MANAGE 2.4**: "Mechanisms are in place to respond to AI system failures
  and concerns."

**HUMMBL coverage:** MEASURE 2.1 is partially covered by P18 HealthProbe.
MEASURE 2.2, 2.5, 2.7, and MANAGE 2.3, 2.4 have **no backing primitive**.

### ISO/IEC 42001:2023 — Clause 8 (Operation) and Clause 9 (Performance evaluation)

Source: [ISO/IEC 42001:2023](https://www.iso.org/standard/42001)

- **Clause 8.1**: Operational planning and control — "The organization shall
  plan, implement and control the processes needed to meet requirements."
- **Clause 8.3**: AI risk treatment — executing risk treatment plans.
- **Clause 8.4**: AI system impact assessment — performed during operation.
- **Clause 9.1**: Monitoring, measurement, analysis and evaluation — "The
  organization shall determine what needs to be monitored and measured."
- **Clause 9.2**: Internal audit — audit programme for the AIMS.
- **Clause 9.3**: Management review — inputs include "status of actions from
  previous management reviews" and "changes in external and internal issues."
- **Annex A.6**: AI system life cycle — "Lifecycle gates with recorded
  sign-offs from design through verification, deployment, and operation."
- **Annex A.9**: Responsible use of AI systems — "monitoring records that
  show use stays within intended use."

**HUMMBL coverage:** Clause 8.1 is partially covered by P19 Lifecycle.
Clauses 9.1, 9.3, Annex A.6, and Annex A.9 have **no backing primitive**.

### EU AI Act — Articles 72-73 (Post-market monitoring and incident reporting)

Source: [AI Act Article 72](https://overview.legal/laws/ai-act/art-72),
[Article 73](https://overview.legal/laws/ai-act/art-73)

- **Article 72**: Providers of high-risk AI systems shall establish and
  document a post-market monitoring system, proportionate to the nature of
  the AI technologies and the risks. The system must "actively and
  systematically collect, document and analyse relevant data" on
  performance throughout the system's lifetime. Based on a post-market
  monitoring plan (Annex IV point 9).
- **Article 73**: Serious incidents must be reported to market surveillance
  authorities within strict timelines:
  - Death: immediately, not later than **10 days** after awareness.
  - Widespread/critical infrastructure disruption: immediately, not later
    than **2 days**.
  - Other serious incidents: immediately after causal link established, not
    later than **15 days**.
  - Initial report may be incomplete, followed by complete report.

**HUMMBL coverage:** **No backing primitive** for post-market monitoring or
incident reporting timelines. This is a regulatory gap for any HUMMBL
deployment subject to EU AI Act jurisdiction.

### Microsoft Agent SRE Governance 1.0

Source: [AGENT-SRE-GOVERNANCE-1.0.md](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/specs/AGENT-SRE-GOVERNANCE-1.0.md)

Microsoft's Agent SRE spec defines the following operational governance
primitives for AI agents:

1. **SLO Objectives** — composable SLIs and targets
2. **Error Budgets** — SRE-style reliability accounting with burn rate alerts
3. **Circuit Breakers** — automatic agent isolation on sustained failure
4. **Chaos Engineering** — fault injection and adversarial resilience testing
5. **Alerting** — multi-channel alert dispatch with deduplication
6. **Trace Replay** — deterministic capture and replay of agent execution traces
7. **Golden Traces** — regression suites for agent behavior
8. **Artifact Signing** — Ed25519-based signing of agent build artifacts
9. **Incident Detection** — automated incident creation from reliability signals
10. **Incident Response** — severity classification and response actions
11. **OpenTelemetry Integration** — semantic conventions for agent observability

**HUMMBL overlap:** P2 CircuitBreaker covers #3. P44 Attest partially
covers #8 (identity attestation, not artifact signing). P52 ToolAudit
partially covers #6 (tool-call audit, not full trace replay).

**HUMMBL gaps:** #1, #2, #4, #5, #6, #7, #9, #10, #11 have no backing
primitive. That is **9 of 11** Agent SRE capabilities unimplemented.

### Google SRE Workbook — Error budgets and burn-rate alerting

Source: [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/),
[Implementing SLOs](https://sre.google/workbook/implementing-slos/)

Key concepts:

- **SLI**: ratio of good events to total events (0% to 100%).
- **SLO**: target percentage for an SLI (e.g., 99.9% success ratio).
- **Error budget**: 100% minus SLO (e.g., 0.1% allowed errors).
- **Burn rate**: how fast the error budget is being consumed. Burn rate > 1
  means the service will miss its SLO if the current rate continues.
- **Multi-window multi-burn-rate (MWMBR) alerting**: combines a short
  window (e.g., 5 min) and a long window (e.g., 1 hour). Both must exceed
  the threshold simultaneously. This reduces false positives while
  maintaining fast detection.
- **Error budget policy**: when budget is exhausted, halt all changes
  except P01/security fixes until the service is back within SLO.

**HUMMBL coverage:** **No backing primitive** for SLI/SLO/error budget/burn
rate. The fleet has a `slo-define` skill but it is a stub (junction
remediation, no content beyond a description).

---

## Part III: Proposed Operations Primitives (P53-P59)

### Design principles

1. **Receipt-backed** — every operations primitive produces a Kernel receipt
   (K1 RECEIPT invariant).
2. **Composable** — operations primitives compose with existing safety
   primitives (P1 KillSwitch, P2 CircuitBreaker, P18 HealthProbe).
3. **Stdlib-only** — zero third-party runtime dependencies, consistent with
   HUMMBL's architecture constraint.
4. **MCP-exposable** — each primitive should be exposable as a JSON-RPC tool
   via an `mcp_ops` MCP server.
5. **Regulatory-aligned** — each primitive maps to at least one regulatory
   requirement (NIST AI RMF, ISO 42001, EU AI Act).

### P53 — SLOEngine

| Field | Value |
|-------|-------|
| **Family** | OP-1 (Operations) |
| **Layer** | Infrastructure |
| **Invariant** | — (infrastructure) |
| **Module** | `slo_engine.py` |
| **Schema** | `slo.schema.json` |
| **Status** | Proposed |

**Description:** Service Level Objective engine — define SLIs (good/total
event ratio), SLOs (target percentage), and error budgets (100% - SLO).
Supports composable SLI definitions, multiple SLOs per service, and
budget accounting over a compliance window.

**Maps to:** NIST AI RMF MEASURE 2.1, 2.2; ISO 42001 Clause 9.1; Google
SRE Workbook SLI/SLO/ error budget; Microsoft Agent SRE #1, #2.

**Key classes:**
- `SLIDefinition` — name, good-event predicate, total-event predicate
- `SLO` — SLI + target percentage + compliance window
- `ErrorBudget` — SLO + consumed budget + remaining budget + burn rate
- `SLOEngine` — register SLOs, record events, evaluate, produce receipts

**Composes with:** P18 HealthProbe (SLI from health check results), P8
AuditLog (SLO evaluation receipts), P2 CircuitBreaker (budget exhaustion
trips breaker).

### P54 — BurnRateAlerter

| Field | Value |
|-------|-------|
| **Family** | OP-2 (Operations) |
| **Layer** | Infrastructure |
| **Invariant** | — (infrastructure) |
| **Module** | `burn_rate_alerter.py` |
| **Schema** | `burn_rate_alert.schema.json` |
| **Status** | Proposed |

**Description:** Multi-window multi-burn-rate (MWMBR) alerting engine.
Fires alerts when both a short window (e.g., 5 min) and a long window
(e.g., 1 hour) exceed a burn-rate threshold simultaneously. Supports
configurable alert tiers (critical, warning, informational) and
multi-channel dispatch (webhook, Slack, email, bus STATUS).

**Maps to:** NIST AI RMF MEASURE 2.7; Google SRE Workbook MWMBR
alerting; Microsoft Agent SRE #5.

**Key classes:**
- `BurnRateWindow` — window duration + burn rate threshold
- `AlertTier` — severity + short window + long window + threshold
- `AlertChannel` — abstract dispatch (webhook, Slack, email, bus)
- `BurnRateAlerter` — register tiers, evaluate burn rate, dispatch alerts

**Composes with:** P53 SLOEngine (burn rate from error budget), P8
AuditLog (alert receipts), P14 CoordinationBus (bus STATUS dispatch).

### P55 — IncidentManager

| Field | Value |
|-------|-------|
| **Family** | OP-3 (Operations) |
| **Layer** | Infrastructure (corrected from Evidence by verify-pass) |
| **Invariant** | K1 (RECEIPT) |
| **Module** | `incident_manager.py` |
| **Schema** | `incident.schema.json` |
| **Status** | Proposed |

**Description:** AI-specific incident management — detect incidents from
reliability signals (SLO violations, circuit breaker trips, kill switch
engagements), classify severity (P1/P2/P3/P4), track lifecycle (detected →
investigating → mitigated → resolved → postmortem), and enforce reporting
timelines. Includes EU AI Act Article 73 serious-incident reporting
timelines (2 days for critical infrastructure, 10 days for death, 15 days
for other serious incidents).

**Maps to:** NIST AI RMF MANAGE 2.3, 2.4; ISO 42001 Clause 9.1; EU AI Act
Article 73; Microsoft Agent SRE #9, #10.

**Key classes:**
- `Incident` — id, severity, status, signals, timeline, impact
- `IncidentSeverity` — P1 (critical), P2 (high), P3 (medium), P4 (low)
- `IncidentStatus` — DETECTED, INVESTIGATING, MITIGATED, RESOLVED, POSTMORTEM
- `ReportingTimeline` — regulatory deadline tracking (EU AI Act)
- `IncidentManager` — create, update, correlate, enforce timelines, receipt

**Composes with:** P53 SLOEngine (SLO violation as trigger), P2
CircuitBreaker (breaker trip as trigger), P1 KillSwitch (engagement as
trigger), P8 AuditLog (incident receipts), P28 Rollback (rollback as
mitigation).

### P56 — CanaryGovernor

| Field | Value |
|-------|-------|
| **Family** | OP-4 (Operations) |
| **Layer** | Infrastructure (corrected from Containment by verify-pass) |
| **Invariant** | K9 (REVERSIBILITY) |
| **Module** | `canary_governor.py` |
| **Schema** | `canary.schema.json` |
| **Status** | Proposed |

**Description:** Progressive delivery governance — manage canary deployments
with percentage-based traffic splitting, metric comparison against
baseline, automated rollback on regression, and stage promotion gates.
Each stage transition produces a receipt. Rollback threshold is
configurable per deployment.

**Maps to:** NIST AI RMF MANAGE 2.1; ISO 42001 Annex A.6 (lifecycle gates);
Microsoft Agent SRE canary deploy; Google SRE progressive delivery.

**Key classes:**
- `CanaryStage` — percentage, metrics, status (pending, active, promoted, rolled-back)
- `CanaryPolicy` — stages, metric, rollback threshold, promotion gate
- `CanaryGovernor` — start, evaluate, promote, rollback, receipt

**Composes with:** P53 SLOEngine (canary metrics via SLI), P28 Rollback
(rollback path), P18 HealthProbe (health verification at each stage), P8
AuditLog (stage transition receipts).

### P57 — PostMarketMonitor

| Field | Value |
|-------|-------|
| **Family** | OP-5 (Operations) |
| **Layer** | Infrastructure (corrected from Evidence by verify-pass) |
| **Invariant** | K5 (EVIDENCE) |
| **Module** | `post_market_monitor.py` |
| **Schema** | `post_market_monitor.schema.json` |
| **Status** | Proposed |

**Description:** Post-market monitoring system for AI systems in production
— systematically collect, document, and analyze performance data throughout
the system's lifetime. Implements EU AI Act Article 72 requirements:
proportionate monitoring, active and systematic data collection, continuous
compliance evaluation. Produces monitoring receipts and feeds incident
detection.

**Maps to:** EU AI Act Article 72; ISO 42001 Clause 9.1, Annex A.9; NIST
AI RMF MEASURE 2.2, 2.5.

**Key classes:**
- `MonitoringPlan` — scope, data sources, collection frequency, analysis methods
- `MonitoringRecord` — timestamp, data collected, analysis result, compliance status
- `PostMarketMonitor` — register plan, collect, analyze, evaluate compliance, receipt

**Composes with:** P53 SLOEngine (performance data via SLI evaluation), P55
IncidentManager (compliance degradation triggers incident), P8 AuditLog
(monitoring receipts), P9 ComplianceMapper (compliance crosswalk).

### P58 — RunbookRegistry

| Field | Value |
|-------|-------|
| **Family** | OP-6 (Operations) |
| **Layer** | Infrastructure |
| **Invariant** | — (infrastructure) |
| **Module** | `runbook_registry.py` |
| **Schema** | `runbook.schema.json` |
| **Status** | Proposed |

**Description:** Governed registry of operational runbooks — each runbook
has a canonical ID, trigger condition, steps, expected outcome, and
last-tested timestamp. Runbooks are promoted through canon registry stages
(draft → reviewed → validated → adopted → canonical). Stale runbooks
(untested > N days) are flagged for mandatory re-test. This makes
operational knowledge a governed, auditable artifact rather than tribal
knowledge.

**Maps to:** NIST AI RMF MANAGE 2.3; ISO 42001 Clause 8.1 (operational
planning and control); NIST 800-53 IR family (Incident Response).

**Key classes:**
- `Runbook` — id, trigger, steps, expected outcome, last tested, canon status
- `RunbookRegistry` — register, promote, test, flag stale, receipt

**Composes with:** P27 CanonRegistry (runbook promotion through canon
stages), P40 DraftSweeper (stale draft detection — proposed), P8 AuditLog
(runbook receipts).

### P59 — FleetStatusAggregator

| Field | Value |
|-------|-------|
| **Family** | OP-7 (Operations) |
| **Layer** | Infrastructure |
| **Invariant** | — (infrastructure) |
| **Module** | `fleet_status.py` |
| **Schema** | `fleet_status.schema.json` |
| **Status** | Proposed |

**Description:** Fleet-wide status aggregation — collect health, disk,
network, and service status from all fleet nodes, aggregate into a single
fleet status report, and produce a receipt. Supports configurable
aggregation intervals, node discovery, and degraded-node detection. This
is the primitive backing the fleet's `fleet-status` and `machine-health`
skills.

**Maps to:** NIST AI RMF MEASURE 2.2; ISO 42001 Clause 9.1 (monitoring).

**Key classes:**
- `NodeStatus` — node, health, disk, mem, load, uptime, services
- `FleetStatus` — nodes, overall status, degraded nodes, timestamp
- `FleetStatusAggregator` — register nodes, collect, aggregate, receipt

**Composes with:** P18 HealthProbe (per-node health), P8 AuditLog (fleet
status receipts), P14 CoordinationBus (status broadcast).

---

## Part IV: Coverage Matrix — Proposed Primitives vs Frameworks

| Framework requirement | P53 SLO | P54 Burn | P55 Incident | P56 Canary | P57 PostMarket | P58 Runbook | P59 FleetStatus |
|-----------------------|---------|----------|--------------|------------|----------------|-------------|-----------------|
| NIST AI RMF MEASURE 2.1 (metrics) | ✅ | ✅ | — | — | ✅ | — | ✅ |
| NIST AI RMF MEASURE 2.2 (production monitoring) | ✅ | ✅ | — | ✅ | ✅ | — | ✅ |
| NIST AI RMF MEASURE 2.5 (safety evaluation) | — | — | ✅ | ✅ | ✅ | — | — |
| NIST AI RMF MEASURE 2.7 (response times) | — | ✅ | ✅ | — | — | ✅ | — |
| NIST AI RMF MANAGE 2.1 (risk resources) | — | — | — | ✅ | — | — | — |
| NIST AI RMF MANAGE 2.3 (failure responses) | — | — | ✅ | ✅ | — | ✅ | — |
| NIST AI RMF MANAGE 2.4 (response mechanisms) | — | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| ISO 42001 Clause 8.1 (operational control) | — | — | — | ✅ | — | ✅ | — |
| ISO 42001 Clause 9.1 (monitoring) | ✅ | ✅ | ✅ | — | ✅ | — | ✅ |
| ISO 42001 Annex A.6 (lifecycle gates) | — | — | — | ✅ | — | ✅ | — |
| ISO 42001 Annex A.9 (responsible use) | — | — | — | — | ✅ | — | — |
| EU AI Act Art. 72 (post-market monitoring) | — | — | — | — | ✅ | — | — |
| EU AI Act Art. 73 (incident reporting) | — | — | ✅ | — | ✅ | — | — |
| MS Agent SRE #1 (SLO Objectives) | ✅ | — | — | — | — | — | — |
| MS Agent SRE #2 (Error Budgets) | ✅ | ✅ | — | — | — | — | — |
| MS Agent SRE #5 (Alerting) | — | ✅ | — | — | — | — | — |
| MS Agent SRE #9 (Incident Detection) | — | — | ✅ | — | ✅ | — | ✅ |
| MS Agent SRE #10 (Incident Response) | — | — | ✅ | — | — | ✅ | — |
| Google SRE SLI/SLO | ✅ | — | — | — | — | — | — |
| Google SRE Error Budget | ✅ | ✅ | — | — | — | — | — |
| Google SRE MWMBR Alerting | — | ✅ | — | — | — | — | — |
| Google SRE Error Budget Policy | — | ✅ | ✅ | — | — | — | — |

**Coverage:** 7 proposed primitives cover **21 of 22** mapped framework
requirements. The only uncovered requirement is NIST AI RMF MANAGE 2.1
(resource prioritization), which is an organizational/process concern, not
a primitive-level concern.

---

## Part V: MCP Server Proposal — `mcp_ops`

A new MCP server (`mcp_ops.py`) would expose the operations primitives as
JSON-RPC tools, parallel to the existing 7 MCP servers.

| Server | Tools | Primitives exposed |
|--------|-------|--------------------|
| `mcp_ops` | ~15-20 | SLOEngine, BurnRateAlerter, IncidentManager, CanaryGovernor, PostMarketMonitor, RunbookRegistry, FleetStatusAggregator |

This would bring the total MCP server count from 7 to 8 and the total
tool count from 57 to ~72-77.

---

## Part VI: Implementation Priority

| Priority | Primitive | Rationale |
|----------|-----------|-----------|
| P0 (critical) | P55 IncidentManager | Regulatory requirement (EU AI Act Art. 73); fleet already uses `incident` skill with no backing primitive |
| P0 (critical) | P53 SLOEngine | Foundation for P54, P55, P56; fleet already uses `slo-define` skill (stub) |
| P1 (high) | P54 BurnRateAlerter | Depends on P53; completes the SLO→alert pipeline |
| P1 (high) | P57 PostMarketMonitor | Regulatory requirement (EU AI Act Art. 72) |
| P2 (medium) | P56 CanaryGovernor | Fleet already uses `canary-deploy` skill; K9 reversibility |
| P2 (medium) | P59 FleetStatusAggregator | Fleet already uses `fleet-status` skill |
| P3 (lower) | P58 RunbookRegistry | Operational discipline; no regulatory driver |

**Suggested implementation order:** P53 → P55 → P54 → P57 → P56 → P59 → P58

---

## Part VII: Verify-Pass Recommendation

This research recommends **ADOPT** (implement) the proposed primitives. Per
the research mode verify-pass rule, a verify-pass agent should audit the
proposal before an ADR is written. Specifically:

1. **IP/legal audit** — confirm no patent or license conflict with
   Microsoft's Agent SRE spec (MIT licensed) or Google SRE Workbook
   (CC BY 4.0).
2. **Source-read** — read 2-4 files from the existing primitives (P2
   CircuitBreaker, P18 HealthProbe, P19 Lifecycle) to confirm the
   proposed composition patterns are consistent with existing code.
3. **Operational risk audit** — confirm that adding 7 primitives does not
   violate the zero-runtime-dependency constraint or the 80% coverage
   threshold.

**Verdict pending:** GREEN/YELLOW/RED to be determined by verify-pass agent.

---

## Sources

1. NIST AI RMF 1.0 — https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
2. NIST AI RMF Playbook — https://airc.nist.gov/docs/AI_RMF_Playbook.pdf
3. NIST AI RMF Core — https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
4. ISO/IEC 42001:2023 — https://www.iso.org/standard/42001
5. ISO 42001 Requirements Guide — https://www.konfirmity.com/blog/iso-42001-requirements
6. EU AI Act Article 72 — https://overview.legal/laws/ai-act/art-72
7. EU AI Act Article 73 — https://overview.legal/laws/ai-act/art-73
8. EU AI Act Post-Market Monitoring Guide — https://www.legalithm.com/en/blog/ai-act-post-market-monitoring-incident-reporting
9. Microsoft Agent SRE Governance 1.0 — https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/specs/AGENT-SRE-GOVERNANCE-1.0.md
10. Microsoft Agent Governance Toolkit — https://microsoft.github.io/agent-governance-toolkit/
11. Google SRE Workbook — Alerting on SLOs — https://sre.google/workbook/alerting-on-slos/
12. Google SRE Workbook — Implementing SLOs — https://sre.google/workbook/implementing-slos/
13. Google SRE Workbook — Error Budget Policy — https://sre.google/workbook/error-budget-policy/
14. Google Cloud — Alerting on Burn Rate — https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring/alerting-on-budget-burn-rate
15. Multi-Window Multi-Burn-Rate Alerting — https://oneuptime.com/blog/post/2026-02-17-how-to-set-up-multi-window-multi-burn-rate-alerting-for-slos-on-google-cloud/view
16. GenOps Framework — https://github.laiyagushi.com/neerazz/genops-framework
17. HUMMBL Governance PRIMITIVES.md — local file, v1.4.1
18. HUMMBL Governance existing research: `organization-operationalization-of-primitives-invariants-2026-09-02.md`

---

## Appendix A: Existing Primitive Inventory (operations-relevant)

| ID | Module | Ops relevance |
|----|--------|---------------|
| P1 | `kill_switch` | Emergency halt — operational |
| P2 | `circuit_breaker` | Failure detection — operational |
| P5 | `cost_governor` | Budget tracking — operational (cost) |
| P8 | `audit_log` | Audit trail — operational (evidence) |
| P14 | `coordination_bus` | Fleet coordination — operational (comms) |
| P15 | `lamport_clock` | Causal ordering — operational (timing) |
| P17 | `reward_monitor` | Behavioral drift — operational (behavior) |
| P18 | `health_probe` | Health checks — operational (health) |
| P19 | `lifecycle` | NIST RMF orchestrator — operational (lifecycle) |
| P21 | `eal` | Execution assurance — operational (quality) |
| P28 | `rollback` | Reversibility — operational (recovery) |
| P29 | `recovery_verifier` | Recovery gate — operational (recovery) |
| P30 | `receipt_integrity_monitor` | Receipt integrity — operational (integrity) |
| P52 | `tool_audit` | Tool-call audit — operational (audit) |

**14 of 44 primitives** have operations relevance. The proposed P53-P59
would bring this to **21 of 51**.

---

## Appendix B: Verify-Pass Report

**Date:** 2026-09-04
**Auditor:** devin (verify-pass agent, subagent_general, GLM-5.2 High)
**Verdict:** YELLOW (proceed to ADR with conditions)

### IP/Legal: GREEN

- Microsoft Agent SRE spec (MIT): safe to derive architectural concepts;
  preserve copyright notice if code is adapted verbatim.
- Google SRE Workbook (CC BY 4.0): SLI/SLO/error budget/MWMBR are
  methods, not copyrightable expression. Attribution in docstrings
  recommended.
- NIST AI RMF (public domain): no restriction.
- ISO/IEC 42001 (proprietary): clause numbers and paraphrases only, no
  text copied. Safe.
- EU AI Act (EU regulation): legislation is not copyrightable.
- Patent risk: low — SRE patterns are published prior art (2018+).

### Source-Read: YELLOW

- **P2 CircuitBreaker:** Thread-safe via `threading.Lock` (line 104).
  Composition with P53 is plausible but the wiring mechanism (how P53
  trips P2 from external signal) is unspecified. Minor gap.
- **P18 HealthProbe:** Uses `@dataclass(frozen=True, slots=True)` for
  value objects. **NOT thread-safe** (no threading import) — pre-existing
  inconsistency with the "thread-safe throughout" convention. The
  proposal should not claim consistency with a convention that existing
  code violates.
- **P19 Lifecycle:** Orchestrator pattern with DI via constructor, all
  deps optional. This is the exact pattern the proposed primitives
  should follow. Also NOT thread-safe (pre-existing).
- **P28 Rollback:** Function-based validation/declaration API, not an
  execution API. P56's "composes with P28" claim is semantically loose —
  P56 would validate rollback declarations via P28 but execute rollback
  via its own mechanism.

### Operational Risk: YELLOW

- **Layer violations (BLOCKING if uncorrected):** P55, P56, P57 as
  originally assigned (Evidence/Containment) would create 6 layer
  violations by importing from Infrastructure-layer primitives. Fix:
  move all three to Infrastructure layer. **Applied in this revision.**
- **Zero third-party deps:** GREEN. All stdlib-achievable.
- **80% coverage:** GREEN conditional. ~1400 LOC of new code requires
  ~1120 LOC of tests. Tests must ship in the same PR as each primitive.
- **Independent importability:** GREEN conditional. Each module must be
  added to `__init__.py` exports and `MODULE_LAYERS` in
  `scripts/check_layer_dependencies.py`.
- **Thread safety:** YELLOW. New stateful primitives must use
  `threading.Lock` per the `circuit_breaker.py` pattern.

### ADR Conditions

1. **Layer reassignment (BLOCKING):** P55, P56, P57 → Infrastructure.
   Applied in this revision.
2. **Thread-safety commitment:** New stateful primitives must use
   `threading.Lock`. Acknowledge pre-existing thread-safety debt in
   health_probe.py and lifecycle.py.
3. **P28 composition semantics:** Clarify that P56 validates rollback
   declarations via P28 but executes rollback via its own mechanism.
4. **IP attribution:** Include source attributions in module docstrings
   (Google SRE Workbook, Microsoft Agent SRE, NIST AI RMF).
5. **Test coverage mandate:** Each primitive ships with tests in the
   same PR. ~1120 LOC of tests minimum across 7 modules.
6. **`__init__.py` + `MODULE_LAYERS` registration:** Each new module
   exported from `__init__.py` and registered in
   `scripts/check_layer_dependencies.py`.
7. **MCP server scope:** Split `mcp_ops` MCP exposure into a separate
   PR from primitive implementation (fleet PR scope policy: >3 unrelated
   changesets = BLOCKING flag).
