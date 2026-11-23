# Primitive Red-Team Remediation Crosswalk (2026-11-23)

**Issue:** [`hummbl-io/oss#517`](https://github.com/hummbl-io/oss/issues/517) — `[Audit][P1] Close historical primitive red-team findings against current tagged release`  
**Historical source:** [`PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md`](PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md) (assessed `v1.4.1`)  
**Published PyPI release pinned:** `hummbl-governance==1.5.1` (`pyproject.toml`, tag `python/hummbl-governance/v1.5.1`, commit `a8ad4c3150a8357df28f488c51cdda6c5215b8f6`)  
**Current `main` HEAD pinned:** `c92f5db30c333c7fcd1c5000891ee869b0b6ab76`  
**Verification test suite:** [`tests/test_redteam_crosswalk_517.py`](../tests/test_redteam_crosswalk_517.py)

---

## Summary

This document traces all seven high-impact historical findings listed in `#517` from the 2026-08-27 (`v1.4.1`) critical analysis against both the **currently published PyPI release (`v1.5.1`, `a8ad4c3150a8`)** and **current `main` (`HEAD`, `c92f5db30c33`)**.

| Status | Count (v1.5.1) | Count (HEAD) | Findings |
| --- | :---: | :---: | --- |
| `fixed` | 0 | 0 | None of the 7 historical findings are fully closed in code. |
| `partially fixed` | 3 | 3 | F1 (AuthorityEngine), F4 (LawEngine), F7 (EnvelopeCryptosystem) |
| `unfixed` | 4 | 4 | F2 (Uninvoked checks), F3 (EvidenceEngine), F5 (ConvergenceDetector), F6 (Receipt HMAC attribution) |

> **v1.5.1 vs HEAD delta note:** Across the seven target modules, functional behavior is identical between published `v1.5.1` (`a8ad4c3150a8`) and `HEAD` (`c92f5db30c33`) except for:
> 1. **F6 adjacent (`#458`):** At `HEAD`, `_receipt_key.py` replaced hardcoded published HMAC constants in the six GDPR modules (P53–P58); published `v1.5.1` still contains the hardcoded constants. Neither release adds per-agent asymmetric signing to `ReceiptEngine`.
> 2. **F7 rename & disclosure:** `sovereign_cryptosystem.SovereignCryptosystem` (`v1.5.1`) was renamed to `envelope_cryptosystem.EnvelopeCryptosystem` (`HEAD`), and `docs/standards/CRYPTOGRAPHIC_POLICY.md` §7 at `HEAD` now explicitly discloses the OpenSSL `-K` fallback exposure. The underlying fallback code is unchanged.

---

## Master Remediation Crosswalk

| # | Historical Claim (`v1.4.1`) | Impacted Method / Entrypoint | Published `v1.5.1` (`a8ad4c3150a8`) | Current `HEAD` (`c92f5db30c33`) | Test / Runtime Evidence | Remaining Bypass / Gap | Current Public Wording |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **F1** | AuthorityEngine parses markdown tables with `\|` splitting and checks `"cannot ... without ..."` via substring search on `str(context)`; limits without `"cannot"` are ignored. | `kernel/authority_engine.py`: `AuthorityEngine.check()`, `_check_structured()`, `_check_structured_limit()`, `_check_charter()`, `_check_limit()`; `kernel/mutation_gate.py`: `MutationGate._verify_decision_receipt()` | `partially fixed` — Structured JSON policy (`data/authority_policy.json`) added as primary path; legacy charter fallback retained. | `partially fixed` — Same code behavior as `v1.5.1` (copyright header diff only). | `TestFinding1AuthorityEngineBypass` in `tests/test_redteam_crosswalk_517.py` | 1. `_check_structured_limit()` skips any limit not containing `authority_class.lower()` and only parses `"operator decision"` / `"two-person"` truthiness (any non-empty string passes; no receipt verification).<br>2. Legacy `_check_charter()` fallback still passes `"cannot deploy without approval"` when `context={"note": "no approval needed"}`.<br>3. `MutationGate._verify_decision_receipt()` accepts any string with `len >= 8`. | `PRIMITIVES.md` K6: *"Every authority exercise is scoped, limited, and leaves a receipt"* (CRITICAL). Does not state that non-class limits are unparsed or that receipt IDs are presence/length-checked only. |
| **F2** | Zero production call sites for `AuthorityEngine.check()`, `validate_admission()`, and `AdmissionControl`; gates exist only in tests and internal definitions. | `kernel/admission_control.py`: `validate_admission()`, `validate_admission_control()`; `kernel/authority_engine.py`: `AuthorityEngine.check()`; `kernel/mutation_gate.py`: `MutationGate.check()` / `guard()` | `unfixed` — `MutationGate` added inside `kernel/`, but neither `validate_admission` nor `MutationGate`/`AuthorityEngine` is invoked on MCP server, REST API, or deployed mutation paths. | `unfixed` — Same as `v1.5.1`. | `TestFinding2UninvokedAdmissionAndAuthority` in `tests/test_redteam_crosswalk_517.py` + `git grep` across `packages/` non-test `.py` files. | `validate_admission` has zero non-test callers anywhere in `hummbl-io/oss`. `AuthorityEngine` and `MutationGate` are wired inside `Kernel`, but no MCP server (`mcp_*.py`) or `api_server.py` route invokes them before mutations. Overlaps `#345`. | `docs/public-claims.md` states `production_use_established` is `false` and `README.md` marks package Alpha. `PRIMITIVES.md` P25 still presents `kernel/admission_control` as enforcing D5 without stating it is standalone/unwired. |
| **F3** | `EvidenceEngine.grade()` grades credibility by checking `"http"`/`"/"` (`B`) and `"experiment"`/`"trial"` (`A`), hardcodes `recency="C"`, and checks methodology substrings. | `kernel/evidence_engine.py`: `EvidenceEngine.grade()`, `validate_receipt_claims()`, `EvidenceGrade.is_acceptable()` | `unfixed` — Exact string-matching heuristic unchanged from `v1.4.1`. | `unfixed` — Same as `v1.5.1` (copyright header diff only). | `TestFinding3EvidenceEngineHeuristic` in `tests/test_redteam_crosswalk_517.py` | 1. Fabricated URL `https://example.com/experiment-fake` still receives `credibility="A"`.<br>2. `recency` is hardcoded to `"C"`.<br>3. `relevance` defaults to `"B"` (and `"A"` if `len(claim) > 20`), so `is_acceptable()` is **always `True`** — `validate_receipt_claims()` can never reject an all-C claim. | `PRIMITIVES.md` K5: *"Every claim in a receipt is graded or marked speculative"* (HIGH). Module docstring claims *"All-C claims are rejected,"* which is unreachable via `grade()`. |
| **F4** | `LawEngine` degrades silently to zero laws (`/dev/null`) on clean installs without raising `KernelPanic`; mixes optional `yaml` with a manual parser. | `kernel/law_engine.py`: `LawEngine.__init__()`, `_load_atlas()`, `_check_law()`, `evaluate()`; `kernel/kernel.py`: `_boot_sequence()`, `health()`, `store_receipt()` | `partially fixed` — 19 `SL-*.yaml` files are now bundled in `hummbl_governance/data/atlas/` and packaged via `pyproject.toml`; `_parse_yamlish()` fixed to preserve block lists. | `partially fixed` — Same as `v1.5.1` (copyright header diff only). | `TestFinding4LawEngineDegradedMode` in `tests/test_redteam_crosswalk_517.py` | 1. Missing/empty `HUMMBL_KERNEL_ATLAS_DIR` or nonexistent `atlas_dir` still silently loads 0 laws without `KernelPanic`; `Kernel.health()` still reports `healthy=True` / `law_engine=True`.<br>2. `_check_law()` implements checks for only 4 of 19 bundled laws (`SL-07`, `SL-10`, `SL-11`, `SL-15`); `SL-03` is `pass` and 14 laws have no check logic.<br>3. `Kernel.store_receipt()` defaults to `strict_law=False` (advisory warning only). | `PRIMITIVES.md` K2: *"Every receipt is evaluated against at least one scaling law"* (HIGH, KernelPanic). Does not note advisory default (`strict_law=False`), degraded-mode `HEALTHY` status, or 4/19 active rules. |
| **F5** | `ConvergenceDetector.classify()` uses hardcoded substring matching on action names and requires opt-in `record()` calls with no execution-layer wiring. | `convergence_guard.py`: `ConvergenceDetector.classify()`, `record()`, `check()` | `unfixed` — Same 26 hardcoded substrings in `_DEFAULT_RULES`; `metadata` argument in `record()` is unused; opt-in only. | `unfixed` — Same as `v1.5.1` (copyright header diff only). | `TestFinding5ConvergenceDetectorBypass` in `tests/test_redteam_crosswalk_517.py` | 1. Renaming actions (e.g. `"save_state"`, `"read_data"`) returns `None` and never triggers alerts.<br>2. `record(..., metadata=...)` discards `metadata` without storing or inspecting it.<br>3. Benign action names containing a rule substring (e.g. `"request_compute_for_tests"`) trigger false positives.<br>4. Exposed only via opt-in `mcp_agent_monitor.py`; not wired into `Kernel` or `GovernanceLifecycle`. | `README.md` & `PRIMITIVES.md` P16: *"Detect instrumental convergence patterns in agent behavior"* (K13, LOW). Does not note keyword-only matching on caller-supplied action names or opt-in recording. |
| **F6** | `ReceiptEngine` signs receipts with shared symmetric HMAC-SHA256; any key holder can forge receipts for any agent, providing integrity only, not per-agent attribution or non-repudiation. | `kernel/receipt_engine.py`: `ReceiptEngine._resolve_signing_secret()`, `_sign()`, `create()`, `validate()`, `Receipt.verify_signature()`; adjacent `_receipt_key.py` (GDPR P53–P58, `#458`) | `unfixed` — `ReceiptEngine` still uses a single shared HMAC-SHA256 secret. *(Adjacent `#458`: GDPR modules P53–P58 use hardcoded published constant key in `v1.5.1`.)* | `unfixed` for `ReceiptEngine` attribution/non-repudiation. *(Adjacent `#458` closed at HEAD: `_receipt_key.py` removes hardcoded constants in GDPR modules, though still symmetric HMAC.)* | `TestFinding6ReceiptHmacAttribution` in `tests/test_redteam_crosswalk_517.py` | K3 ghost-agent check rejects unregistered `agent_id` in `create()`, but any party possessing the shared `signing_secret` can forge a valid `Receipt` claiming any registered `agent_id` and pass `validate()` / `verify_signature()`. No per-agent asymmetric signing (Ed25519/ECDSA). | `docs/standards/CRYPTOGRAPHIC_POLICY.md` accurately calls HMAC-SHA256 *"receipt integrity"*. `PRIMITIVES.md` K1/P26 says *"signed receipt"* without clarifying symmetric integrity vs non-repudiation. |
| **F7** | `SovereignCryptosystem.encrypt_envelope()` passes the raw 256-bit AES key in OpenSSL CLI arguments (`-K <hex>`), leaking it in process listings. | `v1.5.1`: `sovereign_cryptosystem.SovereignCryptosystem._encrypt_openssl()`, `_decrypt_openssl()`; `HEAD`: `envelope_cryptosystem.EnvelopeCryptosystem._encrypt_openssl()`, `_decrypt_openssl()` | `partially fixed` — Prefers in-process `cryptography` library when optional extra is installed; OpenSSL `-K` CLI fallback remains for default stdlib-only installs. | `partially fixed` — Module renamed to `envelope_cryptosystem.py`; `CRYPTOGRAPHIC_POLICY.md` §7 updated to disclose limitation; OpenSSL `-K` fallback unchanged. | `TestFinding7OpenSSLKeyTransport` in `tests/test_redteam_crosswalk_517.py` | In the default zero-dependency install (`_HAS_CRYPTOGRAPHY == False`), both `_encrypt_openssl()` and `_decrypt_openssl()` still pass `["-K", self.key.hex(), "-iv", iv.hex()]` to `subprocess.Popen`, exposing key material to process-table inspection. | `CRYPTOGRAPHIC_POLICY.md` §7 (at HEAD) accurately discloses the `-K` fallback exposure. `README.md` and `PRIMITIVES.md` P49 still describe `EnvelopeCryptosystem` as *"Hardened cryptographic sync router"* without noting the stdlib fallback limitation. |

---

## Cross-Reference to Existing Issues

Before opening implementation sub-issues, each finding was cross-checked against existing tracked issues in `hummbl-io/oss`:

1. **[`#345`](https://github.com/hummbl-io/oss/issues/345) (Open — Deep review: governance controls not on the deployed path, and public-claim drift):**
   - Directly covers **F2** (governance primitives implemented and unit-tested, but not wired onto deployed MCP/API/mutation paths) and the public-claim alignment dimension of **F1–F7**.
   - **Action:** Do not open a duplicate deployed-path issue for F2; track runtime wiring under `#345`.
2. **[`#458`](https://github.com/hummbl-io/oss/issues/458) (Closed — GDPR modules signed receipts with a hardcoded published constant HMAC key):**
   - Directly adjacent to **F6**. Closed at `HEAD` (`c92f5db30c33`) by adding `hummbl_governance/_receipt_key.py` (operator-supplied env var or owner-restricted key file, fail-closed).
   - **Important release boundary:** Published `v1.5.1` (`a8ad4c3150a8`) predates the `#458` fix and still ships the hardcoded constants in P53–P58; `#458` remediation will only reach PyPI consumers in the next tagged release (e.g. `1.6.0`). Even at `HEAD`, `#458` addresses hardcoded-key forgery, **not** the symmetric-HMAC vs per-agent asymmetric attribution gap in `ReceiptEngine`.

---

## Public Wording Assessment

Per `#517` acceptance criteria (*"Public wording updated only after evidence supports the narrower or stronger statement"*), this crosswalk records the exact gaps without overstating remediation:

- **Accurately scoped today:**
  - `docs/public-claims.md` keeps `production_use_established: false`, preserves the Alpha classification, and scopes CI counts to dated receipts.
  - `docs/standards/CRYPTOGRAPHIC_POLICY.md` §1 and §7 (at `HEAD`) accurately describe `ReceiptEngine` HMAC-SHA256 as *"receipt integrity"* and explicitly disclose the `EnvelopeCryptosystem` OpenSSL `-K` fallback exposure.
- **Public wording that still overstates code-level enforcement (candidates for narrowing in follow-up doc/code PRs):**
  - `PRIMITIVES.md` K2 (`LawEngine`), K5 (`EvidenceEngine`), K6 (`AuthorityEngine`), P16 (`ConvergenceDetector`), P25 (`admission_control`), P26 (`ReceiptEngine`), and P49 (`EnvelopeCryptosystem`).
  - `README.md` P49 (*"Hardened cryptographic sync router"*) and P16 (*"Detect instrumental convergence patterns in agent behavior"*).

---

## Verification Command

```bash
pytest packages/python/hummbl-governance/tests/test_redteam_crosswalk_517.py -v
```
