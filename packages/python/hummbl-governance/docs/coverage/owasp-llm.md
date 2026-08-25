# OWASP LLM Top 10 (2025) Coverage Matrix — HUMMBL

**Standard**: OWASP Top 10 for Large Language Model Applications — 2025 edition
**Source**: https://genai.owasp.org/
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

OWASP LLM Top 10 is a **risk catalog**, not a regulation. No certification. Coverage means HUMMBL provides primitives that detect, prevent, or mitigate the risk at the platform layer; application-layer prompt engineering and product-level safety controls remain customer responsibilities.

## Summary

10 risk categories. **8 ✅ Fulfilled at platform layer · 2 🟡 Partial (require app-layer completion).**

| ID | Category | Coverage | Evidence |
|---|---|---|---|
| LLM01:2025 | Prompt Injection | 🟡 Partial | |
| LLM02:2025 | Sensitive Information Disclosure | ✅ Fulfilled | `hummbl_governance/schema_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| LLM03:2025 | Supply Chain | ✅ Fulfilled | `hummbl_governance/schema_validator.py`, `.github/workflows/ci.yml` |
| LLM04:2025 | Data and Model Poisoning | 🟡 Partial | |
| LLM05:2025 | Improper Output Handling | ✅ Fulfilled | `hummbl_governance/schema_validator.py`, `.github/workflows/ci.yml` |
| LLM06:2025 | Excessive Agency | ✅ Fulfilled | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |
| LLM07:2025 | System Prompt Leakage | ✅ Fulfilled | `.github/workflows/ci.yml`, `hummbl_governance/schema_validator.py` |
| LLM08:2025 | Vector and Embedding Weaknesses | ✅ Fulfilled | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| LLM09:2025 | Misinformation | ✅ Fulfilled | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| LLM10:2025 | Unbounded Consumption | ✅ Fulfilled | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, `hummbl_governance/kill_switch.py` |

---

## Per-category coverage

### LLM01:2025 — Prompt Injection 🟡

**Risk**: Adversarial inputs that manipulate LLM to behave against intent — direct injection, indirect injection (via retrieved content), multi-modal injection.

**HUMMBL coverage**:
- ✅ INTENT-tuple constraint: every agent action carries declared objective; prompt-injection-induced behavior deviates from INTENT and triggers governance bus anomaly detection
- ✅ DCT scope binding: even if LLM is manipulated into executing an op, the op must match the delegation token's `ops_allowed` — out-of-scope ops blocked at primitive layer
- ✅ kill_switch_core: 4-mode halt available for runaway agent behavior
- 🟡 Application-layer: prompt template hardening, content-filtering, jailbreak-detection — product/app responsibility

**Evidence**: `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py`, INTENT-deviation detection tuples

### LLM02:2025 — Sensitive Information Disclosure ✅

**Risk**: LLM exposing sensitive data — PII, financial, confidential business info — via training-data leakage or context leakage.

**HUMMBL coverage**:
- ✅ Classification-tag enforcement at tuple ingress (cross-ref GDPR Art. 5, ISO 27001 A.5.12-A.5.13)
- ✅ Pseudonymisation tuple type + masking transforms (cross-ref GDPR Art. 32)
- ✅ Resource-selectors in DCT prevent LLM access to out-of-scope sensitive surfaces
- ✅ Append-only governance bus = forensic disclosure-event tracking

**Evidence**: classification enforcement, masking primitives, DCT scope

### LLM03:2025 — Supply Chain ✅

**Risk**: Vulnerable third-party components — model providers, training data sources, embeddings, pre-trained models.

**HUMMBL coverage**:
- ✅ SBOM generation per release (cross-ref ISO 27001 A.5.21, NIST CSF GV.SC-04)
- ✅ `pip-audit` blocking in CI = dependency-CVE gate
- ✅ Supplier-DCT tuples track model providers + data sources
- ✅ Stdlib-only in services/integrations (Tier-2 admission ADR for exceptions)

**Evidence**: `pip-audit` workflow, SBOM artifacts, Tier-2 admission table in `pyproject.toml`

### LLM04:2025 — Data and Model Poisoning 🟡

**Risk**: Pre-training, fine-tuning, or embedding data manipulated to compromise security/effectiveness.

**HUMMBL coverage**:
- ✅ Dataset provenance chain via DATASET tuples (cross-ref ISO 42001 A.7.5)
- ✅ Integrity-check tuples at training-pipeline boundary
- 🟡 Model-evaluation pipelines for poisoning detection — application/research responsibility
- ✅ Supplier-DCT for pre-trained model providers

**Evidence**: DATASET tuple provenance, integrity-check primitives

### LLM05:2025 — Improper Output Handling ✅

**Risk**: LLM outputs not validated/sanitized before downstream use — XSS, SQLi, code injection via LLM-generated code.

**HUMMBL coverage**:
- ✅ Output-validation tuples at LLM→downstream boundary
- ✅ Schema enforcement: outputs must match declared output-schema or trip validation tuple
- ✅ Bandit (Python SAST) + Semgrep blocking on LLM-generated code that lands in repo
- ✅ Output-handling DCT separates LLM-output processing from downstream effect surfaces

**Evidence**: output-validation primitives, Bandit/Semgrep CI gates

### LLM06:2025 — Excessive Agency ✅

**Risk**: LLM granted too much autonomy — excessive permissions, excessive functionality, excessive autonomy.

**HUMMBL coverage**:
- ✅ Least-privilege via DCT `ops_allowed` — agent only does what its delegation token permits
- ✅ Delegation-depth limit prevents indefinite chain
- ✅ Human-in-the-loop required for INTENT classes outside delegation scope
- ✅ kill_switch_core 4-mode halt for runaway agency

**Evidence**: `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py`, depth-limit constants

### LLM07:2025 — System Prompt Leakage ✅

**Risk**: System prompts containing sensitive info (credentials, internal architecture) exposed.

**HUMMBL coverage**:
- ✅ No secrets in code/config (env vars + Keychain only) — system prompts cannot contain secrets by policy
- ✅ Secret-scan in lint-and-schema workflow (PR diff scan)
- ✅ Prompt-template tuples separated from secret-material storage

**Evidence**: secret-scan CI workflow, env-var policy, prompt-template schema

### LLM08:2025 — Vector and Embedding Weaknesses ✅

**Risk**: Vulnerabilities in retrieval-augmented generation (RAG) — poisoned vectors, embedding extraction, untrusted retrieval sources.

**HUMMBL coverage**:
- ✅ Retrieval-source DCT binding: every embedding/vector retrieval traceable to authorized source
- ✅ Provenance chain for embeddings (cross-ref ISO 42001 A.7.5)
- ✅ Integrity-checks on embedding artifacts (signed)
- ✅ Access-control on vector stores via DCT

**Evidence**: retrieval-DCT scope, embedding provenance chain

### LLM09:2025 — Misinformation ✅

**Risk**: LLM producing false/misleading information presented as authoritative.

**HUMMBL coverage**:
- ✅ Output-confidence tuple + hallucination-detection primitives
- ✅ Source-citation enforcement: outputs with claims must cite governance-bus-traceable sources
- ✅ Boundary disclaimers (this very matrix uses them) signal when output is bounded
- ✅ Transparency tuples disclose AI authorship per EU AI Act Art. 50

**Evidence**: confidence tuples, citation-enforcement primitives, transparency tuples

### LLM10:2025 — Unbounded Consumption ✅

**Risk**: Uncontrolled resource consumption — DoS via expensive queries, runaway token use, inference loops.

**HUMMBL coverage**:
- ✅ Circuit-breaker primitives (CLOSED/HALF_OPEN/OPEN) per integration
- ✅ Rate-limit + token-budget primitives per DCT
- ✅ Cost-governor integration (cross-ref `hummbl_governance/cost_governor.py`)
- ✅ kill_switch_core HALT_NONCRITICAL mode for cost runaway

**Evidence**: `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, kill-switch modes

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Existing OWASP doc: `docs/OWASP_MAPPING.md` (covers LLM Top 10 with hummbl-governance v1.2.2 — 2027 collected tests)
- Supply-chain overlap with ISO 27001 A.5.21, NIST CSF GV.SC — see [`iso-27001.md`](./iso-27001.md), [`nist-csf.md`](./nist-csf.md)
- Privacy overlap with GDPR Art. 5/32 — see [`gdpr.md`](./gdpr.md)
