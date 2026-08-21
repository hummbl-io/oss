# Maine AI Chatbot Disclosure Law Coverage Matrix — HUMMBL

**Standard**: An Act to Ensure Transparency in Consumer Transactions Involving Artificial Intelligence, Public Law 2025, Chapter 294 (10 MRS § 1500-DD)
**Effective**: September 16, 2025 (90 days after adjournment of the First Special Session of the 132nd Legislature; signed June 12, 2025)
**Source**: https://legislature.maine.gov/statutes/10/title10sec1500-DD.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Maine-licensed counsel and does not provide legal advice on PL 2025, c. 294 or the Maine Unfair Trade Practices Act (UTPA, 5 MRS § 205-A et seq.). The law prohibits using an AI chatbot to mislead a reasonable consumer into believing they are engaging with a human unless clear and conspicuous disclosure is provided. Violations are enforced as UTPA violations by the Attorney General. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the law's chatbot-disclosure, consumer-transparency, and enforcement-readiness obligations.

## Scope summary

The law applies to any "person" using an "artificial intelligence chatbot" — defined as a software application, web interface, or computer program that simulates human conversation through textual or aural communications — to engage in "trade and commerce" (as defined in 5 MRS § 206(3)) with a consumer in Maine. The disclosure obligation is triggered when the chatbot interaction could mislead or deceive a reasonable consumer into believing they are engaging with a human being. The law also extends to "any other computer technology" used for the same purpose. Violations are enforced through the Maine UTPA, which authorizes the Attorney General to seek injunctions, civil penalties, restitution, and costs.

## Obligations + coverage

### Definitions and applicability (§ 1500-DD(1))

| Obligation | Coverage | Evidence |
|---|---|---|
| Identify whether system qualifies as "artificial intelligence chatbot" (software simulating human conversation via textual or aural communication) | ✅ System-classification tuple + capability-detection primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Determine whether deployment constitutes "trade and commerce" with a consumer under 5 MRS § 206(3) | 🟡 Partial: deployment-context metadata tuple supports classification; legal-scope determination is org task | `hummbl_governance/compliance_mapper.py` |
| Assess whether "any other computer technology" used for consumer engagement falls within disclosure trigger | 🟡 Partial: capability-detection primitive identifies conversational interfaces; technology-scope determination is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Maintain inventory of chatbot deployments engaging with consumers in trade/commerce | ✅ Audit-log registration tuple + deployment-registry primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |

### Required disclosure obligations (§ 1500-DD(2))

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on using AI chatbot to mislead or deceive a reasonable consumer into believing they are engaging with a human | ✅ Output-validation gate enforces disclosure-before-undisclosed-humanlike-output + reasonableness-check heuristic | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Notify consumer in a clear and conspicuous manner that they are not engaging with a human being | ✅ Disclosure-injection primitive + clear-and-conspicuous format-validation tuple (cross-ref EU AI Act Art. 50, California SB 942 § 22757.3) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Provide disclosure for textual (chat/messaging) AI chatbot communications | ✅ Text-channel disclosure-injection primitive + provenance-labeling tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Provide disclosure for aural (voice/speech) AI chatbot communications | ✅ Voice-channel disclosure-injection primitive + aural-provenance tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure disclosure is presented before or at the outset of consumer engagement | ✅ Lifecycle-disclosure gate enforces disclosure at session-initiation event | `hummbl_governance/lifecycle.py`, `hummbl_governance/output_validator.py` |
| Maintain disclosure persistence throughout the chatbot interaction session | ✅ Session-scoped disclosure-state tracking + periodic re-disclosure checkpoint | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Halt or block chatbot output if disclosure has not been delivered to the consumer | ✅ Circuit-breaker fast-fail on undisclosed-humanlike-output + kill-switch halt mode | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |

### Consumer transparency and data protection (§ 1500-DD(2), UTPA context)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide consumer transparency regarding automated nature of interaction | ✅ Transparency-notification primitive + automated-interaction-labeling tuple (cross-ref Colorado § 6-1-1704, Connecticut SB 2) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Log disclosure delivery events for audit and consumer-complaint response | ✅ Immutable audit-log disclosure-delivery tuple + timestamped receipt | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Protect consumer data collected during chatbot interactions (implied via UTPA unfair-practices framework) | 🟡 Partial: audit-log access controls + identity-based data-handling tuple; full data-protection program is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Implement safeguards for minors interacting with AI chatbots in trade/commerce (implied via UTPA consumer-protection framework) | 🟡 Partial: identity-based audience-classification + capability-fence restriction for minor-flagged sessions; minor-specific policy is org task | `hummbl_governance/identity.py`, `hummbl_governance/capability_fence.py` |
| Enable consumer to request human escalation after AI disclosure | ✅ Human-oversight delegation token + escalation-path primitive (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |

### Enforcement via Maine Unfair Trade Practices Act (§ 1500-DD(3))

| Obligation | Coverage | Evidence |
|---|---|---|
| Violation of disclosure obligation constitutes a UTPA violation enforceable by the Attorney General | ⚪ Boundary: statutory-violation classification is legal determination | |
| Attorney General may seek injunctive relief for chatbot-disclosure violations | ⚪ Boundary: injunctive-relief proceedings are legal | |
| Civil penalties and consumer restitution available under UTPA (5 MRS § 209) | ⚪ Boundary: penalty assessment and restitution are judicial | |
| Produce evidence of disclosure compliance for AG investigation or consumer complaint | 🟡 Partial: audit-log export + compliance-report generator supports investigation response; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Retain disclosure-delivery records for enforcement response and statute-of-limitations window | ✅ Immutable audit-log retention + documentation-retention tuple | `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Definitions and applicability (§ 1500-DD(1)) | 4 | 2 | 2 | 0 |
| Required disclosure (§ 1500-DD(2)) | 7 | 7 | 0 | 0 |
| Consumer transparency and data protection (§ 1500-DD(2), UTPA) | 5 | 3 | 2 | 0 |
| Enforcement via UTPA (§ 1500-DD(3)) | 5 | 1 | 1 | 3 |
| **Totals** | **21** | **13** | **5** | **3** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Chatbot disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Consumer transparency overlaps Colorado AI Act § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Content provenance overlaps California SB 942 — see [`california-sb-942.md`](./california-sb-942.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- UTPA enforcement overlaps Connecticut SB 2 consumer-protection framework — see [`connecticut-sb2-sb5.md`](./connecticut-sb2-sb5.md)
