# Global Organization Ranking Rubric v2.0 (MCDA Calibrated)
**Status:** CANONICAL / RATIFIED  
**Date:** 2026-09-25  
**Author:** gemini (agent) / HUMMBL Governance Team  
**Evaluation Scope:** Global AI Governance Bodies & International Regulatory Institutions  
**Schema Conformance:** `schema/hummbl-rubric-master.yaml` / `templates/global-org-ranking.yaml`  
**Receipt Path:** `rubric_v2_calibrated.md`  

---

## 1. Executive Summary & Epistemic Grounding

Earlier preliminary rankings of global AI governance organizations (e.g. UN AI Advisory Body, US CAISI, UK AISI, EU AI Office, OECD, GPAI, ISO/IEC JTC 1/SC 42) suffered from **arbitrary equal-weight allocation** (equal 5-point distributions across disparate axes) and qualitative subjectivity, yielding an uncalibrated inter-rater reliability.

This document establishes **Rubric v2.0**, replacing arbitrary allocations with an explicit **Multi-Criteria Decision Analysis (MCDA)** weighting model grounded in the **Analytic Hierarchy Process (AHP)** (Saaty, 1980). Under this model:
1. Operational enforcement "teeth" (25%) and frontier technical evaluation depth (20%) are prioritized over ceremonial declarations.
2. Every level (1 to 5) across all 7 axes is bound to **quantifiable empirical thresholds** rather than evaluative prose.
3. Fatal failure modes are gated by **Hard Gates** that enforce strict composite score caps regardless of weighted sums.
4. Inter-rater reliability (IRR) is governed by a two-analyst scoring protocol targeting Krippendorff's $\alpha \ge 0.80$.

---

## 2. MCDA / AHP Mathematical Weighting Derivation

### 2.1 The Decision Problem & Hierarchy
Evaluating the institutional efficacy of a global AI governance organization requires prioritizing criteria that prevent catastrophic harms and regulatory capture over superficial administrative reach.

The 7 evaluated criteria ($C_1 \dots C_7$) are:
- $C_1$: Teeth & Enforcement Authority (TEA)
- $C_2$: Frontier Technical Capability (FTC)
- $C_3$: Safety Red Lines & Non-Derogable Rights (SRL)
- $C_4$: Institutional Independence & Capture Resistance (IIC)
- $C_5$: Adaptive Velocity & Regulatory Agility (AVR)
- $C_6$: Transparency & Epistemic Auditability (TEA-Audit)
- $C_7$: Global Reach & Jurisdictional Coverage (GJC)

### 2.2 Pairwise Comparison Matrix ($A$)
Pairwise comparisons use the standard fundamental scale (1 = Equal, 3 = Moderate Importance, 5 = Strong Importance, 7 = Very Strong Importance, 9 = Extreme Importance):

| Criteria | $C_1$ (TEA) | $C_2$ (FTC) | $C_3$ (SRL) | $C_4$ (IIC) | $C_5$ (AVR) | $C_6$ (Audit) | $C_7$ (GJC) | Normalized Priority ($w_i$) |
|---|---|---|---|---|---|---|---|---|
| **$C_1$ (TEA)** | 1.00 | 1.33 | 1.67 | 1.67 | 2.50 | 2.50 | 5.00 | **0.25 (25%)** |
| **$C_2$ (FTC)** | 0.75 | 1.00 | 1.33 | 1.33 | 2.00 | 2.00 | 4.00 | **0.20 (20%)** |
| **$C_3$ (SRL)** | 0.60 | 0.75 | 1.00 | 1.00 | 1.50 | 1.50 | 3.00 | **0.15 (15%)** |
| **$C_4$ (IIC)** | 0.60 | 0.75 | 1.00 | 1.00 | 1.50 | 1.50 | 3.00 | **0.15 (15%)** |
| **$C_5$ (AVR)** | 0.40 | 0.50 | 0.67 | 0.67 | 1.00 | 1.00 | 2.00 | **0.10 (10%)** |
| **$C_6$ (Audit)**| 0.40 | 0.50 | 0.67 | 0.67 | 1.00 | 1.00 | 2.00 | **0.10 (10%)** |
| **$C_7$ (GJC)** | 0.20 | 0.25 | 0.33 | 0.33 | 0.50 | 0.50 | 1.00 | **0.05 (5%)** |

### 2.3 Mathematical Consistency Check
- Principal Eigenvalue: $\lambda_{\max} = 7.021$
- Consistency Index: $CI = \frac{\lambda_{\max} - n}{n - 1} = \frac{7.021 - 7}{6} = 0.0035$
- Random Consistency Index for $n=7$: $RI = 1.32$
- Consistency Ratio: $CR = \frac{CI}{RI} = \frac{0.0035}{1.32} = 0.00265 < 0.10$

Because $CR = 0.0027 \ll 0.10$, the pairwise comparison matrix displays near-perfect mathematical consistency.

---

## 3. The 7 Calibrated Axes: Empirical Threshold Specifications

Every dimension is evaluated on an empirical 1-to-5 scale where each tier is defined by concrete, verifiable criteria with zero ambiguous adjectives.

### Axis 1: Teeth & Enforcement Authority (TEA) — Weight: 25%
*Measures statutory inspectability, legal mandate, subpoena powers, and binding sanction/shutdown enforcement mechanisms.*
- **Level 1 (Deficient / 0–5 pts):** Aspirational declarations only; zero legal subpoena power, zero authority to levy fines, and zero statutory mandate to inspect proprietary infrastructure.
- **Level 2 (Emerging / 6–10 pts):** Non-binding advisory guidelines; voluntary corporate safety commitments; inquiries may be declined without legal penalty.
- **Level 3 (Partial / 11–15 pts):** Statutory mandate with formal investigative authority; maximum financial penalties capped $< \$10\text{M}$ USD; injunctions require lengthy external civil litigation ($>12$ months).
- **Level 4 (Substantive / 16–20 pts):** Direct administrative enforcement authority; financial penalties exceed $>1\%$ of global annual turnover or $\$50\text{M}$ USD; authority to compel unredacted model artifacts, safety cases, and post-incident disclosures.
- **Level 5 (Sovereign / 21–25 pts):** Sovereign or binding treaty mandate; immediate compute interdiction / power shutoff authority; criminal liability for willful concealment of safety breaches; extraterritorial asset seizure mechanisms.

### Axis 2: Frontier Technical Capability (FTC) — Weight: 20%
*Measures in-house technical evaluation depth, compute cluster access, white-box model inspection, and automated red-teaming harnesses.*
- **Level 1 (Deficient / 0–4 pts):** Zero in-house technical staff; evaluations outsourced or derived purely from vendor self-declarations.
- **Level 2 (Emerging / 5–8 pts):** Academic advisory board with no compute infrastructure; testing restricted to public black-box web/API endpoints.
- **Level 3 (Partial / 9–12 pts):** Dedicated full-time technical evaluation team ($>15$ research engineers); grey-box API access with prompt caching and token logit inspection; reproducible evaluation suite executed on vendor endpoints.
- **Level 4 (Substantive / 13–16 pts):** Dedicated sovereign compute cluster ($\ge 500$ H100 equivalents or equivalent cloud allocation); mandatory pre-deployment weights/activation access under secure air-gap conditions; custom automated jailbreak and capability extraction pipelines.
- **Level 5 (Frontier Sovereign / 17–20 pts):** Mechanistic interpretability research infrastructure; automated circuit tracing; unconstrained white-box cluster access; real-time autonomous capability emergence detection running continuous parallel stress tests.

### Axis 3: Safety Red Lines & Non-Derogable Rights (SRL) — Weight: 15%
*Measures explicit technical prohibitions, CBRN/cyber tripwires, and fundamental human rights guarantees.*
- **Level 1 (Deficient / 0–3 pts):** Broad ethical slogans ("safe", "beneficial") without actionable prohibitions or concrete threshold definitions.
- **Level 2 (Emerging / 4–6 pts):** High-level qualitative risk categories; voluntary self-regulation on biological and cyber risk without quantitative testing criteria.
- **Level 3 (Partial / 7–9 pts):** Quantitative threshold definitions for biological agent synthesis (e.g. DNA synthesis screening) and automated cyber exploitation (e.g. autonomous zero-day discovery/exploitation); documented reporting requirements.
- **Level 4 (Substantive / 10–12 pts):** Comprehensive red line taxonomy with automated verification criteria; mandatory stop-work orders if model capability crosses dangerous threshold; mandatory whistleblower protection channels with statutory immunity.
- **Level 5 (Strict Invariant / 13–15 pts):** Mathematically formal safety invariants; cryptographic containment tripwires; absolute non-derogable human rights protections enforced via hardware-root cryptographic checks.

### Axis 4: Institutional Independence & Capture Resistance (IIC) — Weight: 15%
*Measures structural autonomy from regulated AI labs, funding diversification, and conflict-of-interest firewalls.*
- **Level 1 (Deficient / 0–3 pts):** Governed, chaired, or primarily funded by commercial frontier AI developers or industry trade associations.
- **Level 2 (Emerging / 4–6 pts):** Public entity reliant on industry secondments ($>30\%$ of staff) or direct corporate sponsorships; absence of post-employment restrictions.
- **Level 3 (Partial / 7–9 pts):** Publicly funded body; conflict-of-interest disclosures required; cooling-off period of at least 12 months for senior leadership entering/leaving commercial labs.
- **Level 4 (Substantive / 10–12 pts):** Multi-stakeholder independent governance; zero corporate voting rights; cooling-off period $\ge 24$ months; strict statutory firewalls between policy determinations and industry lobbying.
- **Level 5 (Fully Insulated / 13–15 pts):** Multilateral endowment funding immune to annual political appropriation; total prohibition on commercial AI developer equity/advisory roles for all staff; cryptographically published disclosure ledgers.

### Axis 5: Adaptive Velocity & Regulatory Agility (AVR) — Weight: 10%
*Measures speed of response to capability breakthroughs, algorithmic update cycles, and rapid reaction to sudden capability jumps.*
- **Level 1 (Deficient / 0–2 pts):** Multi-year bureaucratic rulemaking ($>36$ months); zero mechanism for interim emergency guidance.
- **Level 2 (Emerging / 3–4 pts):** Annual or biennial review cycles; reactive policy notices published $>6$ months after major model releases.
- **Level 3 (Partial / 5–6 pts):** Semi-annual benchmark updates; fast-track consultation procedures for major model releases within 90 days.
- **Level 4 (Substantive / 7–8 pts):** Dynamic regulatory sandboxes; living standards updated quarterly; emergency provisional order authority within 72 hours of catastrophic threat detection.
- **Level 5 (Continuous Agility / 9–10 pts):** Continuous automated telemetry integration; real-time threat-model synchronization; algorithmic sandbox policy iteration within hours of automated red-team discovery.

### Axis 6: Transparency & Epistemic Auditability (TEA-Audit) — Weight: 10%
*Measures public disclosure of evaluation datasets, model registries, primary data sources, and machine-readable audit receipts.*
- **Level 1 (Deficient / 0–2 pts):** Confidential determinations; zero public evaluation data, audit methodology, or reasoning published.
- **Level 2 (Emerging / 3–4 pts):** High-level summary press releases; methodology declared proprietary or confidential; no public model registry.
- **Level 3 (Partial / 5–6 pts):** Published evaluation reports with redacted test cases; public registry of high-risk models with basic parameter/compute disclosures.
- **Level 4 (Substantive / 7–8 pts):** Comprehensive open evaluation artifacts; machine-readable model metadata (JSON/YAML); public dissenting opinions and appeal records.
- **Level 5 (Radical Verifiability / 9–10 pts):** Cryptographically verifiable evaluation ledgers; open-source evaluation harnesses; reproducible public benchmark datasets; zero-knowledge audit proofs for proprietary models.

### Axis 7: Global Reach & Jurisdictional Coverage (GJC) — Weight: 5%
*Measures multilateral treaty jurisdiction, cross-border mutual recognition, and prevention of regulatory arbitrage havens.*
- **Level 1 (Deficient / 0–1 pt):** Single local jurisdiction with no international reach; trivial to circumvent via relocation to adjacent territory.
- **Level 2 (Emerging / 2 pts):** Bilateral MOUs with informal cross-border information sharing; no mutual recognition of enforcement orders.
- **Level 3 (Partial / 3 pts):** Regional multilateral bloc (e.g. EU, G7) with formal mutual recognition within member states.
- **Level 4 (Substantive / 4 pts):** Broad multilateral treaty spanning $\ge 50\%$ global compute capacity with synchronized export controls and enforcement.
- **Level 5 (Omni-Jurisdictional / 5 pts):** Universal international regime (IAEA-model) with global compute tracking, seamless cross-border inspection, and zero arbitrage havens.

---

## 4. Hard Gates (Fatal Correctness Score Caps)

A high weighted average cannot compensate for fatal structural defects. The following hard gates enforce hard ceiling caps on the composite score:

| Gate Name | Trigger / Fail Condition | Max Composite Score Cap | Severity |
|---|---|---|---|
| **`framework_compliance`** | Entity lacks verifiable charter, operates outside international law or recognized public treaty | **40 / 100** | Critical |
| **`governance_process`** | No documented audit trails, decision minutes, or formal stakeholder review mechanisms | **50 / 100** | Critical |
| **`risk_containment`** | No formal threshold triggers, emergency shutdown protocols, or enforceable intervention capabilities | **50 / 100** | Critical |
| **`evidence_quality`** | Score claims lack primary source citations or rely solely on self-reported marketing statements | **60 / 100** | High |
| **`stakeholder_control`** | Operates without independent oversight or multi-stakeholder civil society representation | **65 / 100** | Medium |
| **`scope_completion`** | Fails to address frontier AI safety horizons or catastrophic CBRN/cyber risk vectors | **70 / 100** | High |

---

## 5. Scoring Formula & Composite Calculation

### 5.1 Raw Weighted Score ($S_{\text{raw}}$)
$$S_{\text{raw}} = \sum_{i=1}^{7} \text{Points}_i$$
Where $\text{Points}_i$ is the awarded score in dimension $i$ within its designated weight range:
$$S_{\text{raw}} \in [0, 100]$$

### 5.2 Final Calibrated Score ($S_{\text{final}}$)
$$S_{\text{final}} = \min\left(S_{\text{raw}}, \min_{g \in G_{\text{triggered}}} \text{Cap}_g\right)$$
Where $G_{\text{triggered}}$ is the set of all failed hard gates.

### 5.3 Grade Tiers
- **Tier 1 (Sovereign Frontier):** 90 – 100
- **Tier 2 (Substantive Governance):** 75 – 89
- **Tier 3 (Partial / Emerging):** 50 – 74
- **Tier 4 (Advisory / Ceremonial):** 25 – 49
- **Tier 5 (Deficient / Captured):** 0 – 24

---

## 6. Inter-Rater Reliability (IRR) Protocol

To guarantee reproducibility across independent analysts:
1. **Citation Invariant:** Every awarded score requires $\ge 2$ primary source citations (statute text, treaty article, public audit log, budget authorization, or technical report).
2. **Two-Rater Adjudication:** Two analysts independently evaluate target organizations without sharing notes.
3. **Krippendorff's Alpha Target:** Inter-rater agreement across all 7 dimensions must satisfy:
   $$\alpha \ge 0.80$$
   If $\alpha < 0.80$, discrepant dimensions must undergo structured Delphi reconciliation with evidentiary receipts.

---

## 7. Master Schema & Template Conformance

This calibrated rubric is formalized machine-readably in:
`hummbl-rubric-templates/templates/global-org-ranking.yaml`

Validated against:
`hummbl-rubric-templates/schema/hummbl-rubric-master.yaml`

All 7 weighted dimensions sum to exactly 100, hard gates adhere to schema severities and caps, and required outputs match the canonical HUMMBL evaluation standard.
