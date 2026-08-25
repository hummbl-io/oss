# California AI Transparency Act (SB 942) Coverage Matrix — HUMMBL

**Standard**: California AI Transparency Act, California Business and Professions Code Chapter 25 (Sections 22757-22757.6)
**Effective**: January 1, 2025 (operative August 2, 2026)
**Source**: https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB942
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not California-licensed counsel and does not provide legal advice on SB 942. The Act is enforced by the Attorney General, city attorneys, and county counsel with civil penalties of $5,000 per violation. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's AI detection tool, manifest/latent disclosure, and provenance requirements.

## Scope summary

SB 942 applies to "covered providers" — persons creating GenAI systems with over 1,000,000 monthly visitors/users publicly accessible in California. It requires AI detection tools, manifest and latent disclosures in AI-generated content, third-party licensee compliance, large online platform provenance display, GenAI hosting platform compliance, and capture device manufacturer latent disclosure options.

## Obligations + coverage

### AI detection tool requirements (§ 22757.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide free AI detection tool to users | 🟡 Partial: output-validation gate detects AI-generated content; public-facing tool deployment is org task | `hummbl_governance/output_validator.py` |
| Detection tool must assess whether image, video, or audio was created/altered by provider's GenAI | ✅ Provenance-verification primitive + content-authenticity tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Detection tool must be publicly accessible with API access | ⚪ Boundary: public-API deployment is infrastructure, not software primitive | |
| Collect and incorporate user feedback on detection tool efficacy | 🟡 Partial: feedback-ingestion tuple type; feedback-loop implementation is org task | `hummbl_governance/audit_log.py` |
| No fee for detection tool use | ⚪ Boundary: pricing policy is organizational | |
| No account creation required for detection tool | ⚪ Boundary: access-policy is organizational | |

### Manifest disclosure requirements (§ 22757.3(a))

| Obligation | Coverage | Evidence |
|---|---|---|
| Offer user option to include manifest disclosure in AI-generated content | ✅ Manifest-disclosure-option tuple + provenance-labeling primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Manifest disclosure identifies content as AI-generated, clear and conspicuous | ✅ Disclosure-format-validation tuple + content-labeling primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Manifest disclosure must be permanent or extraordinarily difficult to remove | 🟡 Partial: provenance-embedding tuple; tamper-resistance implementation is org task | `hummbl_governance/output_validator.py` |

### Latent disclosure requirements (§ 22757.3(b))

| Obligation | Coverage | Evidence |
|---|---|---|
| Include latent disclosure in AI-generated image, video, or audio content | ✅ Latent-disclosure tuple + provenance-embedding primitive (cross-ref C2PA) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Latent disclosure conveys provider name, system name/version, timestamp, unique identifier | ✅ Provenance-metadata tuple with all required fields | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Latent disclosure detectable by provider's detection tool | ✅ Provenance-verification primitive links latent disclosure to detection | `hummbl_governance/output_validator.py` |
| Latent disclosure consistent with widely accepted industry standards | 🟡 Partial: provenance-metadata tuple supports C2PA-compatible fields; standards-conformance is org task | `hummbl_governance/output_validator.py` |
| Latent disclosure permanent or extraordinarily difficult to remove | 🟡 Partial: provenance-embedding tuple; tamper-resistance is org task | `hummbl_governance/output_validator.py` |

### Third-party licensee requirements (§ 22757.3(c))

| Obligation | Coverage | Evidence |
|---|---|---|
| Contractual requirement for licensees to maintain disclosure capability | ⚪ Boundary: contract terms are organizational | |
| License revocation within 96 hours if licensee modifies system to remove disclosure capability | ⚪ Boundary: license-management is organizational | |
| Licensee must cease use after license revocation | ⚪ Boundary: contract enforcement is organizational | |

### Large online platform requirements (§ 22757.3.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Display system provenance data compliant with standards-body specifications | 🟡 Partial: provenance-metadata tuple supports standards-compatible data; UI display is org task | `hummbl_governance/output_validator.py` |
| User interface to disclose provenance data availability | ⚪ Boundary: platform UI is infrastructure, not software primitive | |
| Conspicuous availability information for content authenticity, origin, modification history | 🟡 Partial: provenance-metadata tuple provides data; display is org task | `hummbl_governance/output_validator.py` |

### GenAI hosting platform requirements (§ 22757.3.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on making available non-compliant GenAI systems | 🟡 Partial: compliance-verification primitive can gate uploads; platform enforcement is org task | `hummbl_governance/output_validator.py` |

### Capture device manufacturer requirements (§ 22757.3.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Option for latent disclosure in captured content (devices produced after Jan 1, 2028) | ⚪ Boundary: hardware-manufacturer feature is device-level, not software primitive | |
| Latent disclosure conveys manufacturer name, device name/version, timestamp, unique identifier | ⚪ Boundary: hardware-level provenance is device-level | |

### Enforcement (§ 22757.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Civil penalty of $5,000 per violation (each day = discrete violation) | ⚪ Boundary: civil-penalty exposure is legal | |
| Attorney's fees and costs for prevailing plaintiff | ⚪ Boundary: fee award is judicial | |
| Injunctive relief for third-party licensee violations | ⚪ Boundary: judicial relief is institutional | |

### Exemptions (§ 22757.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Exemption for entertainment content (video games, TV, streaming, movies, interactive) | ⚪ Boundary: exemption applicability is legal determination | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI detection tool (§ 22757.2) | 6 | 1 | 2 | 3 |
| Manifest disclosure (§ 22757.3(a)) | 3 | 2 | 1 | 0 |
| Latent disclosure (§ 22757.3(b)) | 5 | 3 | 2 | 0 |
| Third-party licensee (§ 22757.3(c)) | 3 | 0 | 0 | 3 |
| Large online platform (§ 22757.3.1) | 3 | 0 | 2 | 1 |
| GenAI hosting platform (§ 22757.3.2) | 1 | 0 | 1 | 0 |
| Capture device (§ 22757.3.3) | 2 | 0 | 0 | 2 |
| Enforcement (§ 22757.4) | 3 | 0 | 0 | 3 |
| Exemptions (§ 22757.5) | 1 | 0 | 0 | 1 |
| **Totals** | **27** | **6** | **8** | **13** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Provenance/labeling overlaps EU AI Act Art. 50(2) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Content authenticity overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Output validation overlaps OWASP LLM LLM07:2025 — see [`owasp-llm.md`](./owasp-llm.md)
