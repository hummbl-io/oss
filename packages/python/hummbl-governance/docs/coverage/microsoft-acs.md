# Microsoft Agent Control Specification (ACS) Coverage Matrix — HUMMBL

**Standard**: Microsoft Agent Control Specification (ACS) — public preview, spec version **0.3.1-beta**
**Vendor**: Microsoft (vendor specification, **not** IETF / ISO / CEN)
**Part of**: Agent Governance Toolkit (AGT); ACS is vendored under `policy-engine/`
**Sources**:
- https://microsoft.github.io/agent-governance-toolkit/packages/agent-control-specification/
- https://github.com/microsoft/agent-governance-toolkit
- Normative contract: `policy-engine/spec/SPECIFICATION.md` (Draft; describes `0.3.1-beta`)
**Last reviewed**: 2026-08-31
**Reviewer**: documentation pass per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md) and LANDING-013
**HUMMBL version mapped against**: hummbl-governance v1.4.2 (`pyproject.toml` on this tree)

## Boundary disclaimer (vendor spec)

This is a **Microsoft** specification. HUMMBL does **not** claim ACS compatibility, ACS conformance, or AGT interoperability.

ACS is a stateless, deterministic, fail-closed **policy decision** runtime. A host sends a policy manifest plus a complete snapshot at each intervention point; ACS returns a normalized verdict; the **host** enforces it (`SPECIFICATION.md` §1, §17). HUMMBL ships in-process governance primitives. It does not implement the ACS manifest schema, the eight-point host loop, or the five-verdict normalizer.

[`docs/FLEET-GOVERNANCE-MAPPING.md`](../../../../../docs/FLEET-GOVERNANCE-MAPPING.md) (2026-08-21) **open question 4** asks whether HUMMBL's circuit breaker should adopt ACS verdicts (`allow` / `warn` / `deny` / `escalate` / `transform`) for interoperability with ACS-adapter frameworks. **This matrix names that question. It does not decide it.**

**No public “fulfills ACS.”**

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| 🟡 | Partial | HUMMBL primitive provides part; ACS contract / host adapter / customer policy completes it. Both parts named. |
| ⚪ | Boundary | Control is ACS-runtime, host-SDK, or otherwise outside what shipped HUMMBL implements. |
| ⛔ | Out of scope | Control does not apply to the AI governance platform context (retained for completeness). |

## Completeness

Completeness for this first matrix = the **eight intervention points** + the **five verdicts** + the **three normative core properties** in `SPECIFICATION.md` §1.1 (stateless, deterministic, fail-closed). Optional ACS surfaces (Rego/Cedar/custom policy types, IFC lattice, `extends`, annotators) are named in prose only so they are not silently treated as extra controls.

Hypothesis (non-binding, not a claim): `cost_governor` already uses ALLOW / WARN / DENY; ACS adds `escalate` / `transform` and a portable manifest. Circuit breaker uses CLOSED / HALF_OPEN / OPEN, not ACS verdicts.

## Intervention points (`SPECIFICATION.md` §4)

A request that names any other intervention point MUST fail closed (`runtime_error:intervention_point_unknown`). HUMMBL has no ACS intervention-point dispatcher.

| ID | When the host calls ACS | HUMMBL coverage | Evidence |
|---|---|---|---|
| `agent_startup` | Before an agent session starts (agent metadata) | 🟡 Partial: `lifecycle` + `identity` can gate start-of-session authorization. No ACS snapshot/manifest at startup. | `hummbl_governance/lifecycle.py`, `hummbl_governance/identity.py` |
| `input` | After user or system input is assembled | 🟡 Partial: `schema_validator` can reject structurally invalid payloads. No ACS `input` snapshot or policy-target path. | `hummbl_governance/schema_validator.py` |
| `pre_model_call` | Before the model receives a prompt or request | ⚪ Boundary: HUMMBL has no pre-model intervention-point host. Prompt assembly is application-layer. | n/a — boundary |
| `post_model_call` | After the model returns a response | 🟡 Partial: `output_validator` inspects model-adjacent text (PII / injection / blocklists) after generation. Not an ACS post-model snapshot. | `hummbl_governance/output_validator.py` |
| `pre_tool_call` | Before a tool invocation executes | 🟡 Partial: `capability_fence` + `delegation` (`ops_allowed`) can block out-of-scope tool use. No ACS tool catalog / `tool_name_from`. | `hummbl_governance/capability_fence.py`, `hummbl_governance/delegation.py` |
| `post_tool_call` | After a tool result is available | 🟡 Partial: `schema_validator` can check tool-result shape. No ACS post-tool snapshot or transform-on-result. | `hummbl_governance/schema_validator.py` |
| `output` | Before final output is returned or published | 🟡 Partial: `output_validator` is the closest shipped gate. Not a portable ACS `output` binding. | `hummbl_governance/output_validator.py` |
| `agent_shutdown` | Before the agent session is closed | 🟡 Partial: `kill_switch` + `lifecycle` can halt or record end-of-session state. No ACS shutdown snapshot. | `hummbl_governance/kill_switch.py`, `hummbl_governance/lifecycle.py` |

## Verdicts (`SPECIFICATION.md` §13)

Normalized `decision` values: `allow`, `warn`, `deny`, `escalate`, `transform`. HUMMBL does not emit this enum.

| ID | ACS meaning (spec) | HUMMBL coverage | Evidence |
|---|---|---|---|
| `allow` | Host may proceed with the policy target | 🟡 Partial: `cost_governor` decision `ALLOW`; `lifecycle.authorize` returns `allowed=True`. Not an ACS verdict object (no `reason` / `evidence` / identities). | `hummbl_governance/cost_governor.py`, `hummbl_governance/lifecycle.py` |
| `warn` | Host may proceed while recording or surfacing a warning | 🟡 Partial: `cost_governor` decision `WARN` (soft cap). Not ACS `warn` (no manifest reason codes). | `hummbl_governance/cost_governor.py` |
| `deny` | Host must block the action | 🟡 Partial: `cost_governor` decision `DENY` (hard cap); `circuit_breaker` OPEN rejects calls; `kill_switch` engaged modes refuse work. Not ACS `deny` + reserved `runtime_error:*` reasons. | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |
| `escalate` | Host must route to an approval backend or fail closed if none is available | ⚪ Boundary: no ACS `escalate` verdict and no `approval.default_resolver`. Delegation caveats can require human approval; that is not the ACS approval path (`SPECIFICATION.md` §17.1). Named in FLEET open question 4 — **undecided**. | `hummbl_governance/delegation.py` (caveats only; not ACS escalate) |
| `transform` | Host receives a transformed policy target and applies it instead of the original | ⚪ Boundary: no ACS `transform` body (`path` + `value` rooted at `$policy_target`). `output_validator` can block; it does not return a replacement policy target. Named in FLEET open question 4 — **undecided**. | n/a — boundary |

## Core properties (`SPECIFICATION.md` §1.1 — normative MUST)

| ID | Runtime contract | HUMMBL coverage | Evidence |
|---|---|---|---|
| Stateless | Runtime MUST NOT retain mutable state that influences a later verdict; host supplies the complete snapshot every call | ⚪ Boundary: shipped governors are stateful. `cost_governor` persists usage in SQLite; `circuit_breaker` counts failures; `kill_switch` holds mode. That is the opposite of ACS's "complete snapshot, no retained verdict state." | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |
| Deterministic | Same manifest, snapshot, mode, and dispatcher outputs MUST produce the same verdict and transformed policy target | 🟡 Partial: individual primitives are deterministic given their local inputs. HUMMBL has no ACS manifest / snapshot / dispatcher tuple, so the ACS determinism MUST is not implemented. | per-module call contracts (no ACS engine) |
| Fail-closed | Any evaluation error MUST yield `deny` with a reserved `runtime_error:` reason; MUST NOT apply a transform on an error path | 🟡 Partial: `delegation` authentication is fail-closed on anomaly (rejects). Errors do not normalize to ACS `deny` + reserved reasons, and there is no transform path to suppress. | `hummbl_governance/delegation.py` |

## Surfaces named so they are not silent (not extra completeness rows)

- **Portable manifest** (`agent_control_specification_version`, `policies`, `intervention_points`, optional `extends` / `tools` / `annotators` / `approval`): HUMMBL has no ACS manifest. ⚪ Boundary (stated here; not a second counted control family).
- **Policy types** (`rego`, `cedar`, `test`, `custom`): not implemented. ⚪ Boundary.
- **Information-flow control** (stateless label flow; default lattice `public < internal < confidential < secret`): not implemented. ⚪ Boundary.

## Summary

| Section | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---:|---:|---:|---:|---:|
| Intervention points | 8 | 0 | 7 | 1 | 0 |
| Verdicts | 5 | 0 | 3 | 2 | 0 |
| Core properties | 3 | 0 | 2 | 1 | 0 |
| **Totals** | **16** | **0** | **12** | **4** | **0** |

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL is ACS-compatible or AGT-ready. Open question 4 in `FLEET-GOVERNANCE-MAPPING.md` remains open.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Fleet positioning + open question 4: [`docs/FLEET-GOVERNANCE-MAPPING.md`](../../../../../docs/FLEET-GOVERNANCE-MAPPING.md)
- OWASP Agentic overlap (not ACS): [`owasp-agentic.md`](./owasp-agentic.md)
- ACS docs: https://microsoft.github.io/agent-governance-toolkit/packages/agent-control-specification/
- ACS spec: https://github.com/microsoft/agent-governance-toolkit/blob/main/policy-engine/spec/SPECIFICATION.md
