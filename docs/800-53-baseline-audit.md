Subagent ac59765a completed successfully:

# NIST SP 800-53 Rev 5 — Security Control Family Mapping for `hummbl-io/oss`

**Audit type:** Read-only static code / documentation review  
**Scope:** `packages/python/*` (14 packages) and `.github/workflows` in `hummbl-io/oss`  
**Framework:** NIST SP 800-53 Rev 5 control families  
**Date:** Current as of repository state under `C:\Users\Owner\AppData\Local\Temp\anvil-audit\oss`

---

## 1. Executive Summary

| Family | Status | Top Evidence | Top Gap |
|---|---|---|---|
| **AC** Access Control | **PARTIAL** | `hummbl_kernel/security/capability_admission_policy.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` | No human RBAC/MFA, no centralized PDP/PEP, no network ACLs |
| **AU** Audit & Accountability | **PARTIAL** | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_bus/bus_auditor.py`, `hummbl_bus/bus_verifier.py`, `hummbl_kernel/audit/file_persistence.py` | `AuditLog.append()` does **not** cryptographically verify signatures; not full NIST SP 800-92 |
| **CM** Configuration Mgmt | **PARTIAL** | `base120` drift detection, schema registry in `hummbl-tuples`, `pyproject.toml` per package, `hummbl_governance/schema_validator.py` | No centralized configuration baseline, no formal change control board, no lock/requirements files |
| **CP** Contingency Planning | **GAP** | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/recovery_verifier.py` (runtime recovery only) | No backups, disaster recovery, failover, or business continuity plan |
| **IA** Identification & Authentication | **PARTIAL** | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_bus/authority.py`, `hummbl_bus/bus_ed25519_verifier.py`, `hummbl_kernel/security/capability_admission_policy.py` | No MFA, no human-user authentication, no credential lifecycle/rotation, secrets from env vars |
| **IR** Incident Response | **PARTIAL** | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/approval.py`, `hummbl_governance/physical_governor.py`, 48 h response in `SECURITY.md` | No formal IR plan, incident declaration/escalation playbooks, or communication plan |
| **MA** Maintenance | **PARTIAL** | `pip-audit`, `CodeQL`, `dependency-review`, `ruff`, `mypy` | `pip-audit` has `|| true` and only covers packages with runtime deps; no automated patch/change window process |
| **PE** Physical & Environmental | **GAP** | `hummbl_governance/physical_governor.py` (robot/pHRI safety only) | No facility access, environmental, or fire/HVAC controls |
| **PL** Planning | **PARTIAL** | `SECURITY.md` policies, `hummbl_governance/compliance_mapper.py` (NIST 800-53 overlay), `hummbl_governance/docs/coverage/nist-csf.md` | No System Security Plan (SSP), rules of behavior, or privacy plan |
| **RA** Risk Assessment | **PARTIAL** | `hummbl_governance/stride_mapper.py`, `hummbl-rubric-templates/templates/nist-ai-rmf-compliance.yaml`, `hummbl-governance/tools/vendor_ip_risk_lint.py`, `hummbl_kernel/security/capability_admission_policy.py` | No formal risk register, CVSS scoring, or recurring assessment cadence |
| **SA** System & Services Acquisition | **PARTIAL** | Stdlib-first design, `pip-audit`, `dependency-review`, `vendor_ip_risk_lint.py` | No formal acquisition/contractor controls; `governed-compression` `numpy` exception |
| **SC** System & Communications Protection | **PARTIAL** | HMAC/Ed25519 signing, `hummbl_governance/sovereign_cryptosystem.py` (AES-256-GCM), `hummbl-bus` security policy, `hummbl_governance/capability_fence.py` | No encryption at rest by default (bus TSV plaintext), no transport encryption by default (HTTP over Tailscale), no network segmentation |
| **SI** System & Information Integrity | **PARTIAL** | `hummbl_governance/output_validator.py`, `hummbl_cognition/ledger_writer.py` (PII/credential scrubbing), `hummbl_bus/replay_ledger.py`, replay-attack / duplicate-nonce checks, `hummbl_governance/schema_validator.py`, `CodeQL` | No FIPS-validated crypto, no automated flaw-remediation/patch workflow, no antivirus |
| **SR** Supply Chain Risk Mgmt | **PARTIAL** | `publish-pypi.yml` SBOM (`cyclonedx-py`), Sigstore signing, build-provenance attestation, SHA-pinned workflows, checksums on release | SBOM is environment-based not artifact-based; no lock file; no SLSA level; no reproducible build verification |

---

## 2. Scope & Methodology

- **Packages reviewed:** all 14 directories in `packages/python/` as enumerated in `.github/workflows/ci.yml` (`base120`, `governed-compression`, `hummbl`, `hummbl-bif`, `hummbl-bus`, `hummbl-cognition`, `hummbl-compass`, `hummbl-free-models`, `hummbl-governance`, `hummbl-kernel`, `hummbl-rubric-templates`, `hummbl-taxonomy`, `hummbl-tuples`, `hummbl-validation`), plus the shared `.github/workflows` CI/CD and `tools/scripts` hardening.
- **Evidence types:** source code, docstrings, `pyproject.toml` files, `SECURITY.md` files, `docs/coverage/*` matrices, GitHub Actions workflow definitions, pre-commit / helper scripts, and package READMEs/ADRs.
- **Limitations:** This is a static, read-only mapping. It does not verify runtime behavior, test pass rates, or effectiveness of controls. Gaps are based on absence of implementation evidence in the audited tree.

---

## 3. Family-by-Family Mapping

### 3.1 Access Control (AC) — PARTIAL

**Implemented**

- **Capability admission with risk classes**  
  `hummbl_kernel/security/capability_admission_policy.py` defines `RiskClass` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and `AdmissionStatus` (`ADMITTED`, `DENIED`, `PENDING_APPROVAL`, `EXPIRED`, `REVOKED`). Grants expire, can be revoked, and high-risk capabilities require explicit approval (l. 1, 45, 61, 79). This maps to **AC-2 / AC-3** (account/role management and access enforcement).
- **Capability fence / allow-deny lists**  
  `hummbl_governance/capability_fence.py` implements a “soft sandbox” enforcing per-agent capability boundaries and audit logs the decision. Supports **AC-3**.
- **Delegation Capability Tokens (DCT)**  
  `hummbl_governance/delegation.py` supports scoped, caveated, expiring tokens with resource selectors and revocation. This supports **AC-2, AC-3, AC-16**.
- **Agent identity and trust tiers**  
  `hummbl_governance/identity.py` provides `AgentRegistry` with canonical names, aliases, and `TrustTier` (`OWNER > SYSTEM > HIGH > MEDIUM > LOW`) (l. 45–56). This supports **AC-2 / AC-16**.
- **PII/credential scrubbing before logging**  
  `hummbl_cognition/ledger_writer.py` hashes PII and blocks credential patterns before append-only storage, preventing over-exposure (l. 47–149).
- **`hummbl_governance/approval.py`** human-in-the-loop gating for high-risk operations, enforcing separation of privilege (**AC-5** concept).

**Gaps**

- No human user authentication, role-based access control, or multi-factor authentication (**IA-2 / AC-2**).
- No centralized policy decision/enforcement point across packages; each package independently enforces capabilities.
- No network access control lists, firewall rules, or network segmentation code.
- Capability tokens rely on shared secrets rather than robust credential lifecycle/rotation.

---

### 3.2 Audit and Accountability (AU) — PARTIAL

**Implemented**

- **Append-only signed audit log**  
  `hummbl_governance/audit_log.py` writes JSONL audit records with daily rotation, configurable retention, and an HMAC-SHA256 `signature` field (l. 1, docstring; `__init__.py` l. 10).
- **Receipt engine with HMAC-SHA256**  
  `hummbl_governance/kernel/receipt_engine.py` creates and verifies `Receipt` objects using `hmac.new(..., hashlib.sha256, ...)`; stores receipts in an append-only JSONL file with `0o600` secret file permissions (l. 1, 112–119).
- **Receipt integrity monitor**  
  `hummbl_governance/kernel/receipt_integrity_monitor.py` checks sequences for gaps, hash-chain integrity, and timestamp anomalies; critical integrity failures raise `KernelPanic` (l. 1, summary).
- **Bus auditor and verifier**  
  - `hummbl_bus/bus_auditor.py` audits the coordination bus for format drift, stale WIPs, unreviewed decisions, and message-type drift.  
  - `hummbl_bus/bus_verifier.py` counts signed vs unsigned messages, verifies HMAC signatures, detects duplicate nonces, unknown senders, and timestamp anomalies.
- **Replay ledger**  
  `hummbl_bus/replay_ledger.py` records accepted remote bus writes in an append-only JSONL file with cross-process locking.
- **Kernel file persistence with verification on load**  
  `hummbl_kernel/audit/file_persistence.py` signs audit records on write and verifies on read with HMAC.
- **Compliance mapping**  
  `hummbl_governance/compliance_mapper.py` explicitly references 800-53 `AU-2`, `AU-6`, and `AU-12` in the COSAiS overlay (l. 1030+).

**Gaps**

- **Critical:** `hummbl-governance/SECURITY.md` (l. 32–41) states that `AuditLog.append()` only *presence-checks* the `signature` field; it does **not** verify the HMAC against the entry body. Tamper detection is “the responsibility of an external verifier.” This is a **significant 800-92 / AU-6 gap**.
- No centralized log collection/SIEM; no log forwarding; no file-integrity monitoring of audit files.
- Timestamps rely on local system clock; no trusted time source.
- Log access control and separation of duties for log administrators are not implemented.
- No formal log review schedule or alerting on audit events.

---

### 3.3 Configuration Management (CM) — PARTIAL

**Implemented**

- **Per-package `pyproject.toml`** specifying versions, Python compatibility, and dependency ranges (`packages/python/*/pyproject.toml`). This supports **CM-2 / CM-4**.
- **Schema registry and validation**  
  `hummbl_governance/schema_validator.py` provides a stdlib-only JSON Schema validator with `$ref` resolution and cycle detection. `hummbl-tuples` defines machine-readable tuple schemas (`schemas/*.json`), giving a structured data baseline.
- **Base120 drift detection**  
  `base120/docs/drift-detection.md` describes versioned golden-corpus snapshots, `base120/drift/capture_baseline.py`, `base120/drift/compare.py`, and a CI workflow to catch semantic drift before merge.
- **GitHub boundary check**  
  `.github/workflows/boundary-check.yml` + `tools/scripts/check_boundary_patterns.py` enforce the public/private artifact boundary, preventing accidental config leakage.
- **AGENTS.md** documents the monorepo structure, versioning, and pre-PR checklist (rebase, tests, no internal docs).

**Gaps**

- No centralized configuration management database (CMDB) or configuration baseline for all packages.
- No formal change-control board or mandatory change approval workflow for configuration changes.
- No lock files, hashes, or reproducible environment manifests; `pyproject.toml` version ranges are loose.
- No documented rollback procedure for configuration changes beyond base120 rollback mention.

---

### 3.4 Contingency Planning (CP) — GAP

**Implemented**

- Runtime resiliency primitives: `hummbl_governance/circuit_breaker.py` (`CLOSED`/`OPEN`/`HALF_OPEN`), `hummbl_governance/recovery_verifier.py`, `hummbl_governance/__init__.py` exports these, and `hummbl_governance/physical_governor.py` has safety modes.
- Kill switch / emergency halt in `hummbl_governance/kill_switch.py` provides operational stops but is not a backup/DR plan.

**Gaps**

- No backup, restore, replication, failover, or disaster-recovery procedures. No evidence of off-site media, backup testing, or RTO/RPO definitions.
- No contingency plan documentation, alternate processing site, or recovery playbook.
- Business continuity / data redundancy controls are absent.

---

### 3.5 Identification and Authentication (IA) — PARTIAL

**Implemented**

- **Agent identity registry**  
  `hummbl_governance/identity.py` maps canonical IDs, aliases, and trust tiers.
- **DCT with issuer/subject/caveats**  
  `hummbl_governance/delegation.py` binds tokens to an issuer and subject, with scope, expiry, and revocation.
- **Ed25519 principal authentication**  
  `hummbl_bus/authority.py` defines `PRIVILEGED_TYPES` and `HUMAN_PRINCIPALS`, verifies authenticated principal proofs with Ed25519, and consumes nonces for replay protection (l. 90–234).
- **Bus Ed25519 verifier**  
  `hummbl_bus/bus_ed25519_verifier.py` verifies Ed25519 signatures on privileged bus event types.
- **Capability admission policy**  
  `hummbl_kernel/security/capability_admission_policy.py` requires agents to request capabilities and approve high-risk ones.
- **Signing secret resolution from env**  
  `hummbl_bus/bus_writer.py`, `hummbl_cognition/ledger_writer.py`, `hummbl_governance/kernel/receipt_engine.py`, and `hummbl-kernel/hummbl_kernel/audit/file_persistence.py` resolve HMAC secrets from environment variables; bus file permissions are hardened to `0o600`.

**Gaps**

- **No MFA / 2FA** for any human or administrative principals.
- No human user authentication system, session management, or password policy.
- No credential lifecycle management, key rotation, or account revocation for operators.
- Shared fallback `HUMMBL_SIGNING_SECRET` and `BUS_SIGNING_SECRET` mean secrets are not isolated per package/function.
- Secrets are read from environment variables (visible in process table to same-UID processes) and not from a secret manager/HSM.
- No evidence of cryptographic authenticator binding to a hardware-backed identity.

---

### 3.6 Incident Response (IR) — PARTIAL

**Implemented**

- **Kill switch** with graduated modes (`DISENGAGED`, `HALT_NONCRITICAL`, `HALT_ALL`, `EMERGENCY`) in `hummbl_governance/kill_switch.py` (l. 1, summary; emergency halt).
- **Circuit breaker** automatic failure detection/recovery in `hummbl_governance/circuit_breaker.py`.
- **Human-in-the-loop approval** with expiry and audit integration in `hummbl_governance/approval.py`.
- **Physical governor** for pHRI/collision safety in `hummbl_governance/physical_governor.py`.
- **SECURITY.md** files across packages commit to 48-hour acknowledgment and 7-day initial assessment.

**Gaps**

- No formal incident response plan, roles (CISO/IO/communicator), or playbooks.
- No incident declaration, categorization, reporting, or escalation workflow beyond kill switch/circuit breaker.
- No post-incident review / AAR process stored in the public repo (intentionally excluded).
- IR relies on human operators; no automated containment playbooks beyond hard stops.

---

### 3.7 Maintenance (MA) — PARTIAL

**Implemented**

- **CI testing on Python 3.11/3.12/3.13** per `AGENTS.md` and `.github/workflows/ci.yml` matrix.
- **`pip-audit`** job in `ci.yml` audits packages with runtime dependencies.
- **`CodeQL`** static analysis runs on PRs and weekly (`.github/workflows/codeql.yml`).
- **`dependency-review`** blocks moderate+ severity vulnerable dependencies on PRs changing `pyproject.toml` (`.github/workflows/dependency-review.yml`).
- **`ruff`**, `mypy`, pre-commit secret detection (`detect-secrets`), and custom key checks in `hummbl-cognition/.pre-commit-config.yaml`.
- **`nosec_audit.py`** justifies `# nosec` suppressions.

**Gaps**

- `pip-audit` runs with `|| true` (non-blocking) and only on `governed-compression`, `hummbl-rubric-templates`, and `hummbl-free-models`. Stdlib-only packages are not audited for interpreter/runtime CVEs.
- No documented maintenance windows, patch management SOP, or automated patch/upgrade workflow.
- No separate maintenance test environment or change rollback validation.
- `bandit`/`semgrep` are mentioned in `hummbl-governance/docs/coverage/*` but no CI workflow actually runs them (only `nosec_audit.py`).

---

### 3.8 Physical and Environmental Protection (PE) — GAP

**Implemented**

- `hummbl_governance/physical_governor.py` and `hummbl_governance/docs/standards/...` define robot/pHRI kinematic and safety constraints (`PhysicalSafetyMode`, `KinematicGovernor`, `pHRISafetyMonitor`).

**Gaps**

- No facility/site physical access controls, guard/protection, or visitor management.
- No environmental controls (HVAC, fire suppression, temperature/humidity monitoring).
- No media storage or disposal controls.
- The package-level “physical governor” does **not** satisfy NIST PE-2, PE-3, PE-6, etc.

---

### 3.9 Planning (PL) — PARTIAL

**Implemented**

- `SECURITY.md` files define vulnerability reporting, supported versions, response timelines, and scope.
- `hummbl_governance/compliance_mapper.py` builds an 800-53 / COSAiS overlay and maps primitives to controls (l. 1030+).
- `hummbl_governance/docs/coverage/nist-csf.md` maps primitives to CSF 2.0, including governance/risk/planning categories.
- `hummbl_kernel/security/capability_admission_policy.py` and `hummbl_governance/stride_mapper.py` embed risk-based planning into runtime.

**Gaps**

- No System Security Plan (SSP), privacy impact assessment, or rules of behavior.
- No system of record for security planning decisions, milestones, or review cadence.
- Planning is mostly encoded in code/docs but not as a formal organizational plan.

---

### 3.10 Risk Assessment (RA) — PARTIAL

**Implemented**

- **STRIDE mapping**  
  `hummbl_governance/stride_mapper.py` maps agent interactions to Spoofing, Tampering, Repudiation, Information Disclosure, DoS, and Elevation of Privilege, then suggests mitigation modules.
- **NIST AI RMF / compliance control specs**  
  `hummbl_governance/compliance_frameworks.py` includes `ControlSpec` for `MAP-2.2` and `RA-AI`. `hummbl-rubric-templates/templates/nist-ai-rmf-compliance.yaml` contains risk assessment criteria.
- **Risk-based capability admission**  
  `hummbl_kernel/security/capability_admission_policy.py` classifies capabilities by risk and requires approval for high/critical.
- **Vendor IP risk register lint**  
  `hummbl-governance/tools/vendor_ip_risk_lint.py` validates an AI vendor IP risk register against RED/YELLOW/GREEN levels and allowed tiers.
- **Mandate integrity docs**  
  `hummbl-governance/docs/standards/mandate-integrity/...` require profiles to declare a threat model.

**Gaps**

- No formal, versioned risk register with risk owners, likelihood, impact, and treatment plans.
- No CVSS or equivalent scoring methodology visible in code.
- No recurring vulnerability scanning beyond `pip-audit`, `CodeQL`, and `dependency-review`.
- Risk assessment is ad-hoc / embedded rather than a documented organizational process.

---

### 3.11 System and Services Acquisition (SA) — PARTIAL

**Implemented**

- **Stdlib-first dependency posture** — `AGENTS.md` and multiple `pyproject.toml` files declare zero third-party runtime dependencies, reducing supply-chain exposure.
- **`pip-audit` / `dependency-review` / `CodeQL`** in CI.
- **`vendor_ip_risk_lint.py`** for evaluating vendor IP risk.
- **SBOM + provenance** in `publish-pypi.yml` (detailed under Supply Chain, below).

**Gaps**

- No formal acquisition process, security requirements for contractors, or acceptance testing for COTS/GOTS.
- No SOW/security control flow-downs for third-party components.
- `governed-compression` has an intentional `numpy>=1.26` exception; additional third-party admission controls would strengthen **SA-9 / SA-12**.

---

### 3.12 System and Communications Protection (SC) — PARTIAL

**Implemented**

- **Message signing / verification**  
  `hummbl_bus/bus_writer.py`, `hummbl_bus/message_signing.py`, and `hummbl_governance/primitives/basen_tuple.py` use HMAC-SHA256 and Ed25519.
- **Authenticated envelope encryption**  
  `hummbl_governance/sovereign_cryptosystem.py` provides AES-256-GCM with HMAC-SHA256 (l. 1, summary).
- **Bus security policy**  
  `hummbl_bus/bus_policy.py` enforces `PERMISSIVE`/`WARN`/`STRICT` signing levels.
- **Secure TSV**  
  `hummbl_bus/secure_tsv.py` base64-encodes message payloads to prevent tab/newline injection.
- **Capability fence / sandbox**  
  `hummbl_governance/capability_fence.py` enforces allow/deny lists.
- **TLS in transit (optional)**  
  `hummbl_cognition/agenthub_bridge.py` uses `urllib.request` with an `ssl._create_default_https_context` for HTTPS.
- **Public/private boundary enforcement**  
  `.github/workflows/boundary-check.yml` and `tools/scripts/check_boundary_patterns.py`.

**Gaps**

- **No encryption at rest by default** — `hummbl-bus` docs (`packages/python/hummbl-bus/docs/security/index.md`, l. 354) explicitly state the bus file is “plaintext TSV” and “No transport encryption … the bridge uses plain HTTP. Tailscale provides WireGuard encryption.”
- **Default permissive signing** — `bus_policy.py` allows `PERMISSIVE` mode, which accepts unsigned messages and only logs warnings.
- No network segmentation, firewall, VPN, or TLS-by-default for internal bus bridge.
- No secure enclave / TEE usage, no certificate pinning, no DNS security.
- AES-256-GCM in `sovereign_cryptosystem.py` exists but is not the default for all persisted data.

---

### 3.13 System and Information Integrity (SI) — PARTIAL

**Implemented**

- **Output/content validation**  
  `hummbl_governance/output_validator.py` detects PII leakage, prompt injection, blocked terms, jailbreak patterns, steganography, and encoding bypasses (`PIIDetector`, `InjectionDetector`, `JailbreakPatternDetector`, etc.).
- **Cognition ledger scrubbing**  
  `hummbl_cognition/ledger_writer.py` scans for PII, credentials (OpenAI/Anthropic keys), and injection patterns; hashes PII and redacts credentials before storage.
- **Schema validation**  
  `hummbl_governance/schema_validator.py` and `hummbl-tuples` schemas enforce structured data integrity.
- **Bus integrity**  
  `hummbl_bus/replay_ledger.py`, `bus_verifier.py` duplicate-nonce detection, and `secure_tsv.py` protect against replay and injection.
- **Receipt integrity monitor**  
  `hummbl_governance/kernel/receipt_integrity_monitor.py` detects sequence gaps, hash-chain breaks, and retroactive insertion.
- **Secret / boundary leak prevention**  
  `.github/workflows/boundary-check.yml` runs `gitleaks` and a custom pattern denylist; `hummbl-governance/scripts/scan-sensitive-pre-commit.py` blocks internal hostnames, IPs, and token patterns.
- **SAST / SCA**  
  `CodeQL`, `dependency-review`, `ruff`, `mypy`.

**Gaps**

- No automated flaw remediation / patch management workflow.
- No file-integrity monitoring (FIM) for binaries, configuration, or log files.
- No FIPS-validated crypto modules.
- `pip-audit` is non-blocking and limited in scope.
- No malware/anti-virus scanning.

---

### 3.14 Supply Chain Risk Management (SR) — PARTIAL

**Implemented**

- **`publish-pypi.yml`** (l. 111–177):
  - Generates an SBOM with `cyclonedx-py environment --output-reproducible` → `sbom.json`.
  - Signs release artifacts (`*.whl`, `*.tar.gz`) with Sigstore.
  - Generates GitHub build-provenance attestation via `actions/attest-build-provenance`.
  - Publishes SHA-256 checksums on the release.
- **SHA-pinned workflows** enforced by `.github/workflows/validate-workflows.yml`.
- **`pip-audit`** and **`dependency-review`** in CI.
- **Vendor IP risk register lint** `hummbl-governance/tools/vendor_ip_risk_lint.py`.

**Gaps**

- **SBOM is environment-based** (`cyclonedx-py environment`), generated after installing the package + test extras, so it may include test/dev dependencies and does not strictly represent the published wheel artifact. No SBOM for the built wheel itself.
- No `requirements.txt` or lock file (`uv.lock`, `poetry.lock`) for any package; reproducible builds are not verified.
- No declared SLSA level; provenance attestation gives build provenance but not full SLSA L2/L3 (no build service isolation or hermeticity evidence).
- `governed-compression` requires `numpy>=1.26`; this exception is documented but no deeper SCA/SBOM attestation is generated for it beyond `pip-audit`.
- No checksum verification at package install time; no artifact cosign/Sigstore verification instructions.

---

## 4. Special Assessments

### 4.1 Cryptographic Posture

**Strengths**

- Modern, conservative algorithm choices: **SHA-256**, **HMAC-SHA256**, **AES-256-GCM**, **Ed25519**.
- No use of broken/deprecated algorithms (MD5, SHA-1, RSA < 2048, DES/3DES).
- `secrets` module used for CSPRNG where needed.
- Optional `cryptography>=42.0` provides Ed25519 and AES-GCM implementations; stdlib `hashlib`/`hmac` used by default to minimize dependencies.
- `sovereign_cryptosystem.py` provides authenticated encryption with associated data (AEAD).

**Weaknesses / Gaps**

- **No FIPS 140-2/140-3 mode.** Python `hashlib`/`hmac` rely on the underlying OpenSSL build; no explicit FIPS provider or module validation is enforced.
- **No FIPS self-test or algorithm allowlist.** There is no configuration to reject non-FIPS algorithms.
- **Key derivation is weak/informal.** `sovereign_cryptosystem.py` derives a key by SHA-256 of concatenated strings (not PBKDF2, scrypt, or HKDF).
- **No certificate pinning, TLS 1.3 enforcement, or cert validation beyond Python defaults.** The bus bridge uses plain HTTP unless the operator adds a reverse proxy.
- **No post-quantum or crypto-agility roadmap.**
- **`nosec` comments exist** and are audited by `nosec_audit.py`, but no `bandit` CI job actually enforces them.

**Recommendation**  
Add a documented crypto policy, evaluate `cryptography` FIPS provider usage, replace ad-hoc key derivation with HKDF/PBKDF2, and enforce TLS for production bus bridges.

---

### 4.2 Key Management

**Strengths**

- Multiple components resolve signing secrets from well-known environment variables (`BUS_SIGNING_SECRET`, `MISSION_MODE_SIGNING_KEY`, `RECEIPTENGINE_HMAC_KEY`, `HUMMBL_SIGNING_SECRET`).
- Ed25519 public keys can be loaded from a configurable file (`BUS_PRINCIPAL_PUBLIC_KEY_FILE`) with a default `key_id`.
- Receipt signing key storage file permissions are set to `0o600`.
- Nonce consumption in `hummbl_bus/authority.py` provides replay protection for Ed25519 proofs.
- DCTs support expiry and revocation, limiting key/secret lifetime.

**Weaknesses / Gaps**

- **Secrets are environment-variable based**, making them visible in `/proc/<pid>/environ` to same-UID processes and potentially logged by CI.
- **Shared master fallback** (`HUMMBL_SIGNING_SECRET`) is used across `kill_switch.py`, `receipt_engine.py`, and other modules. A single compromise affects multiple primitives.
- **No key generation ceremony, key rotation, key escrow, or key compromise procedure.**
- **No HSM, KMS, or hardware-backed key storage.**
- **No per-package or per-function key isolation** (many modules read `BUS_SIGNING_SECRET`).
- **No key derivation** from a master key; keys are used directly as raw strings.

**Recommendation**  
Introduce a small key-hierarchy (master key → per-package derived keys via HKDF), integrate with a secret manager (e.g., AWS KMS, HashiCorp Vault, or at least `keyring`), and establish a key rotation and compromise-response procedure.

---

### 4.3 Audit Log Integrity / NIST SP 800-92

**Strengths**

- Multiple append-only logs (`hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_bus/replay_ledger.py`, `hummbl_cognition/ledger_writer.py`).
- HMAC-SHA256 signatures are generated and stored.
- Hash chaining, sequence-gap detection, and retroactive-insertion detection in `hummbl-tuples` and `hummbl_governance/kernel/receipt_integrity_monitor.py`.
- `hummbl_kernel/audit/file_persistence.py` verifies signatures when reading audit files.
- File permissions hardened to `0o600`; daily rotation and retention in `hummbl_governance/audit_log.py`.

**Weaknesses / Gaps**

- **`hummbl_governance/audit_log.py` does NOT verify the HMAC on append** (confirmed by `hummbl-governance/SECURITY.md` l. 32–41). The signature field is presence-checked, not cryptographically validated at the point of collection.
- No file-integrity monitoring (FIM) for log files.
- No centralized log aggregation or SIEM; no secure log forwarding.
- Timestamps depend on local system clock; no NTP hardening or trusted timestamp authority.
- No write-once media or remote, append-only log storage for long-term integrity.
- The repository is public; internal audit matrices and AARs are intentionally excluded, which is good for boundary control but limits visibility into operational log-review processes.

**Recommendation**  
Add HMAC verification at `AuditLog.append()`, deploy FIM, forward logs to a tamper-evident store, and implement trusted timestamping. This is the highest-priority finding for AU-6 / 800-92 alignment.

---

### 4.4 Supply Chain / SBOM / SLSA

**Strengths**

- Release pipeline (`publish-pypi.yml`) generates an SBOM, signs artifacts with Sigstore, creates GitHub build-provenance attestations, and publishes SHA-256 checksums.
- Trusted publishing to PyPI via OIDC (no long-lived API tokens in CI).
- SHA-pinned workflow actions enforced by `validate-workflows.yml`.
- `dependency-review` and `pip-audit` for dependency risk.
- Stdlib-first design reduces third-party dependency surface.

**Weaknesses / Gaps**

- **SBOM generation is `cyclonedx-py environment`**, not per-artifact. It reflects the CI environment (including test extras) rather than the minimal runtime dependency graph of the shipped wheel.
- **No lock file / reproducible manifest** for any package. Installers resolve floating version ranges at install time.
- **No documented SLSA level.** Build provenance attestation is present but the build is not demonstrably hermetic or isolated.
- **No artifact verification instructions** for consumers (how to verify Sigstore signatures or checksums).
- **`pip-audit` is non-blocking** (`|| true`) and only covers packages with declared runtime dependencies; it does not block the build.
- **One documented exception to the “stdlib-only” rule** (`governed-compression` → `numpy`), but no formal admission/allowlisting process for additional exceptions.

**Recommendation**  
Generate per-artifact SBOMs from the built wheel, add lock files, document SLSA level and consumer verification steps, make `pip-audit` blocking, and expand it to include the Python interpreter/stdlib CVE surface or run it on all packages.

---

## 5. Cross-Cutting Observations & Next Steps

1. **Highest-priority control gap:** `hummbl_governance/audit_log.py` does not verify signatures at append time. Fixing this is the fastest path to material improvement in the **AU** family and NIST SP 800-92 alignment.
2. **Cryptographic hardening:** Establish a formal crypto and key-management policy. Move from raw environment secrets to a derived key hierarchy and secret-manager integration. Add FIPS mode analysis, even if FIPS validation is not pursued.
3. **Bus encryption:** The `hummbl-bus` documentation explicitly notes plaintext-at-rest and plain-HTTP transport. For any production deployment, add filesystem-level encryption and a TLS-terminating reverse proxy as a minimum.
4. **Supply chain completeness:** Make `pip-audit` blocking, generate wheel-level SBOMs, and add lock files to enable reproducible builds and full SLSA traceability.
5. **Formal documentation vs. code:** Many controls are well represented in code but not in a formal System Security Plan, incident response plan, or contingency plan. For a full 800-53 assessment, those organizational artifacts will be required regardless of code maturity.

This report is based on a read-only review and is intended as a baseline gap map. A full 800-53 assessment would additionally require interviews, runtime testing, and review of the private `hummbl-io/hummbl-governance` repository and operational procedures.