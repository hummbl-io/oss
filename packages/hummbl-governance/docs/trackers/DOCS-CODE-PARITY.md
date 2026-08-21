# Docs/Code Parity Tracker

Cases where documentation describes a capability as live, active, required, or complete
but the code disagrees. Each entry: claim, reality, fix needed, status.

---

## Open

### Linear adapter described as unconditionally live
| Field | Detail |
|-------|--------|
| Claim | "7 live adapters" including Linear, stated without qualification |
| Reality | `scheduler_adapters.py`: Linear defaults to mock data when `LINEAR_API_KEY` is unset |
| Docs affected | `hummbl_governance/docs/SAFETY_STACK.md`, `hummbl_governance/docs/governance/AI_RISK_ASSESSMENT.md`, `hummbl_governance/docs/investigation/daily_activity_reconstruction.md` |
| Fix needed | Add qualifier: "conditionally live (requires `LINEAR_API_KEY` env var)" |
| Status | Pending |

### opencode-guardrails.md referenced but absent
| Field | Detail |
|-------|--------|
| Claim | PR #624 review cited `.claude/rules/opencode-guardrails.md` lines 25-32 as specifying "Required" metadata tags |
| Reality | File did not exist in the repository |
| Fix needed | Create `.claude/rules/opencode-guardrails.md` with clear Required vs SHOULD distinction |
| Status | In progress |

---

## Closed

### hummbl-bus file permissions: docstring claims 0o600, code was 0o660
| Field | Detail |
|-------|--------|
| Claim | `bus_writer.py` docstring and PRD F-BUS-010 specify 0o600 (owner-only) |
| Reality | `bus_writer.py:776` was setting `0o660` (owner + group read/write) |
| Fix | Code corrected to 0o600 on 2026-05-04 (commit `b6fae4f`) |
| Status | **CLOSED** — code now matches docs |

### Krineia ADR-001 declared FROZEN before acceptance criteria met
| Field | Detail |
|-------|--------|
| Claim | ADR-001 status: "ACCEPTED — FROZEN at v1.0 (May 15 LOI gate)" |
| Reality | RECEIPT_SCHEMA.md is still DRAFT; INVARIANTS.md not written; no git tag v1.0.0 |
| Fix | Status changed to "ACCEPTED — FREEZE PENDING" on 2026-05-04 |
| Status | **CLOSED** — status now accurately reflects pre-freeze state |

### SchemaValidator examples used constructor-raise pattern
| Field | Detail |
|-------|--------|
| Claim | `TECH-SPEC-legal-governance-integration.md` examples showed `SchemaValidator(schema)` constructor and `pytest.raises(ValueError)` |
| Reality | Actual API: `SchemaValidator.validate(instance, schema) -> list[str]` — no constructor, no raise |
| Fix | 4 locations corrected in legal tech spec on 2026-05-04 (commit `ba06029`) |
| Status | **CLOSED** — examples now match actual API |

---

## Review cadence

Sweep this tracker during every PR review that touches adapters, integrations, or
capability claims in docs. Add new entries immediately when a discrepancy is found.
