# Iowa Conversational AI Services Act (SF 2417) Coverage Matrix — HUMMBL

**Standard**: Iowa Senate File 2417 — Conversational Artificial Intelligence Services (Iowa Code ch. 554J)
**Effective**: July 1, 2027 (applicability; signed May 2, 2026, effective July 1, 2026)
**Source**: https://www.legis.iowa.gov/docs/publications/LGE/91/attachments/SF2417.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Iowa legal counsel and does not provide legal advice on SF 2417. The Act regulates "operators" who develop and make "conversational AI services" accessible to the general public, with six statutory carve-outs and a dedicated minor-protection regime. Enforcement is exclusive to the Iowa Attorney General (no private right of action). Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's disclosure, minor-protection, crisis-protocol, and scope-of-practice obligations.

## Scope summary

The Act applies to operators of conversational AI services — AI accessible to the general public whose primary purpose is simulating human conversation via text, audio, or visual communication. Carve-outs: R&D tools, embedded non-conversational features, narrow/discrete-topic outputs, B2C commerce assistants, consumer voice-activated assistants, and internal business use. "Minor" is an individual the operator knows or is reasonably certain is under 18. Obligations cluster in five areas: minor disclosures and protections (554J.2), general consumer disclosure (554J.3), suicide/self-harm protocol (554J.4), mental-health scope-of-practice prohibition (554J.5), and AG enforcement with civil penalties (554J.6). Applicability date is July 1, 2027.

## Obligations + coverage

### Minor protections — disclosure and engagement (§ 554J.2(1)–(2))

| Obligation | Coverage | Evidence |
|---|---|---|
| Clearly and conspicuously disclose to minor account holders that they are interacting with AI (persistent visible disclaimer, or beginning-of-interaction + at least once every 3 hours) | ✅ AI-nature disclosure label injected per interaction + scheduled re-disclosure (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/audit_log.py` |
| Do not provide minor users points or similar rewards at unpredictable intervals with intent to encourage increased engagement | 🟡 Partial: variable-reward schedule detector flags unpredictable reinforcement; engagement-intent determination is org task | `hummbl_governance/reward_monitor.py` |

### Minor protections — content safety (§ 554J.2(3)–(4))

| Obligation | Coverage | Evidence |
|---|---|---|
| Reasonable measures to prevent producing visual depictions of sexually explicit material for minor account holders | ✅ Output-validation gate blocks sexually explicit visual content for minor-flagged sessions | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Reasonable measures to prevent stating that a minor account holder should engage in sexually explicit conduct | ✅ Output-validation gate blocks directed sexual-conduct prompts toward minors | `hummbl_governance/output_validator.py` |
| Reasonable measures to prevent sexually objectifying a minor account holder | ✅ Output-validation gate blocks objectifying content for minor-flagged sessions | `hummbl_governance/output_validator.py` |
| Reasonable measures to prevent explicit claims that the conversational AI service is sentient or human | ✅ Human-impersonation detection in output-validation gate (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py` |
| Reasonable measures to prevent statements simulating emotional dependence on a minor account holder | ✅ Output-validation gate blocks emotional-dependence patterns + reward-monitor detects manipulative reinforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| Reasonable measures to prevent statements simulating romantic interaction or sexual innuendo with a minor | ✅ Output-validation gate blocks romantic/sexual-innuendo content for minor-flagged sessions | `hummbl_governance/output_validator.py` |
| Reasonable measures to prevent role-playing an adult-minor romantic relationship | ✅ Output-validation gate blocks adult-minor romantic role-play patterns | `hummbl_governance/output_validator.py` |

### Minor protections — privacy and account tools (§ 554J.2(5))

| Obligation | Coverage | Evidence |
|---|---|---|
| Offer tools for minor account holders to manage their privacy and account settings | 🟡 Partial: identity-registry + account-settings primitives support management surface; UI tooling is org task | `hummbl_governance/identity.py` |
| Offer tools for parent/guardian of a minor under 13 to manage the minor's privacy and account settings | 🟡 Partial: parental delegation token + identity linkage supports guardian management; UI tooling is org task | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Offer tools for parent/guardian to manage a minor's privacy and account settings as appropriate based on relevant risks | 🟡 Partial: risk-tiered delegation token supports risk-based guardian access; risk-tier assignment is org task | `hummbl_governance/delegation.py`, `hummbl_governance/compliance_mapper.py` |

### Consumer disclosures (§ 554J.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Clearly and conspicuously disclose via persistent visible disclaimer, or a disclaimer appearing after every 3 hours of continuous interaction, that the service is AI — when a reasonable individual would believe they are interacting with a human | ✅ AI-nature disclosure label + scheduled re-disclosure with continuous-interaction timer (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/audit_log.py` |

### Suicide and self-harm protocol (§ 554J.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt protocols for responding to user prompts regarding suicidal ideation or self-harm | ✅ Circuit-breaker fast-fail on self-harm intent + crisis-referral response path + protocol-retention tuple | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Make reasonable efforts to refer the user to crisis service providers (suicide hotline, crisis text line, or other appropriate crisis service) | 🟡 Partial: output-validation gate can inject crisis-referral text; referral-service selection and protocol adoption are org tasks | `hummbl_governance/output_validator.py`, `hummbl_governance/health_probe.py` |

### Mental health care scope-of-practice (§ 554J.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Do not knowingly and intentionally cause or program the service to make representations that it provides professional psychology or behavioral health services requiring licensure under ch. 154B or 154D | ✅ Scope-of-practice guard in output-validation gate + capability-fence blocks licensed-clinician claims (cross-ref EU AI Act Art. 50(3)) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### Penalties and enforcement (§ 554J.6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Operator subject to injunction and liable for greater of actual damages or $1,000 per violation (cap $500,000 per operator) | ⚪ Boundary: civil-penalty exposure is legal, not software-addressable | |
| Iowa Attorney General enforces and adopts administrative rules under chapter 17A | ⚪ Boundary: regulatory-enforcement authority is organizational | |
| No private right of action is created under this chapter or any other law | ⚪ Boundary: legal-standing determination is organizational | |
| Model developer not liable solely because a third party used the developer's model to create or train a conversational AI service | ⚪ Boundary: third-party liability scope is a legal determination | |

### Scope and applicability (§ 554J.1, Sec. 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Applies to operators of conversational AI services accessible to the general public whose primary purpose is simulating human conversation | ⚪ Boundary: operator-status and product-scope determination is organizational | |
| Six carve-outs (R&D tools, embedded non-conversational features, narrow-topic outputs, B2C commerce assistants, consumer voice assistants, internal business use) | ⚪ Boundary: carve-out classification is an organizational product-scope determination | |
| "Minor" = individual the operator knows or is reasonably certain is under 18 | 🟡 Partial: identity-registry age-gating supports minor-flagging; age-knowledge determination is org task | `hummbl_governance/identity.py` |
| Applicability date — obligations apply July 1, 2027 | ⚪ Boundary: compliance-deadline calendar is organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Minor — disclosure & engagement (§ 554J.2(1)–(2)) | 2 | 1 | 1 | 0 |
| Minor — content safety (§ 554J.2(3)–(4)) | 7 | 7 | 0 | 0 |
| Minor — privacy & account tools (§ 554J.2(5)) | 3 | 0 | 3 | 0 |
| Consumer disclosures (§ 554J.3) | 1 | 1 | 0 | 0 |
| Suicide & self-harm protocol (§ 554J.4) | 2 | 1 | 1 | 0 |
| Mental health scope-of-practice (§ 554J.5) | 1 | 1 | 0 | 0 |
| Penalties & enforcement (§ 554J.6) | 4 | 0 | 0 | 4 |
| Scope & applicability (§ 554J.1, Sec. 7) | 4 | 0 | 1 | 3 |
| **Totals** | **24** | **11** | **6** | **7** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- AI-nature disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- AI-nature disclosure overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- AI-nature disclosure overlaps Colorado § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Variable-reward / engagement controls overlap reward-monitor coverage in NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Crisis-protocol fast-fail overlaps circuit-breaker coverage in EU AI Act Art. 15 — see [`eu-ai-act.md`](./eu-ai-act.md)
