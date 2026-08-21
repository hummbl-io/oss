# ADR Backlog

Decisions that have been made in PRDs, code, or docs but lack a formal ADR. Each entry
should become an ADR before the owning repo is considered execution-ready.

**Priority**: P0 = blocking execution · P1 = should precede implementation · P2 = write before next review

---

## Open

### hummbl-bus: bus file permissions standard (P0)
- **Decision made**: 0o600 (owner-only) per PRD F-BUS-010; code bug fixed 2026-05-04
- **ADR location**: `hummbl-bus/docs/adr/ADR-002-bus-file-permissions.md` (not yet written)
- **Why ADR needed**: The 0o660 → 0o600 correction was a bug fix, but the permission policy
  is a security decision that should be recorded with rationale (why not 0o660, why not 0o644,
  Windows handling, group-write risks in multi-user environments)
- **Blocking**: PyPI readiness claim for hummbl-bus

### hummbl-compliance: crosswalk data model (P0)
- **Decision needed**: How are controls mapped to framework requirements?
  - Option A: flat JSONL (one row per control-framework pair)
  - Option B: nested JSON (framework → domain → control)
  - Option C: SQLite (queryable, supports multiple frameworks)
- **ADR location**: `hummbl-compliance/docs/adr/ADR-001-crosswalk-data-model.md` (not yet written)
- **Blocking**: Any implementation of `hummbl-compliance`

### krineia: schema field name resolution (P0 — resolved, ADR update needed)
- **Decision made**: `state.event` (dotted lowercase) is canonical for v1.0;
  `state.type` (uppercase) from PRD draft is superseded
- **ADR location**: `krineia/docs/adr/ADR-001-receipt-chain-standard.md` (exists; needs note)
- **Status**: Context note added to ADR-001 2026-05-04; no separate ADR needed

### hummbl-contracts: schema versioning and breaking-change policy (P1)
- **Decision needed**: What constitutes a breaking change? What is the promotion path
  from DRAFT → STABLE? Who must sign off?
- **ADR location**: `hummbl-contracts/docs/adr/ADR-001-schema-versioning-policy.md`
- **Blocking**: Contracts repo execution-readiness

### hummbl-governance: opencode metadata policy (P1)
- **Decision needed**: Are opencode pilot metadata tags Required or SHOULD? What is the
  enforcement mechanism?
- **ADR location**: `hummbl-governance/.claude/rules/opencode-guardrails.md` (being created)
  plus a formal ADR if the policy is complex enough to need rationale
- **Notes**: `opencode-guardrails.md` is referenced in PR #624 review but file did not exist

### hummbl-governance: SchemaValidator ownership — governance vs cognition (P2)
- **Decision needed**: `SchemaValidator` currently lives in `hummbl_governance/cognition/`. As it
  is extracted to `hummbl-governance`, which version is canonical? What is the migration path?
- **ADR location**: `hummbl-governance/docs/adr/ADR-XXX-schema-validator-ownership.md`

### research evidence provenance standard (P2)
- **Decision needed**: What provenance metadata is required for volatile research artifacts
  (model catalogs, benchmark results, free-tier counts)?
- **ADR location**: `hummbl-governance/docs/adr/ADR-XXX-research-evidence-standard.md`
  or a policy doc
- **Notes**: OpenRouter catalog in PR #625 has no fetch timestamp, source URL, or parser command

---

## Closed

_(none yet)_
