# UNVERIFIED Claims Tracker

Claims in specs, docs, or PRDs that cite no evidence artifact. Each entry must be resolved
(evidence attached or claim downgraded) before the owning document is marked STABLE.

**Format**: `[ ]` = unresolved · `[~]` = in progress · `[x]` = closed

---

## Open

- [ ] **Anthropic ZDR active for HUMMBL**
  - Claim: Anthropic has an active Zero Data Retention agreement covering HUMMBL API usage
  - Source: `hummbl-governance/docs/ecosystem/TECH-SPEC-legal-governance-integration.md`
  - Evidence needed: signed DPA or ZDR confirmation from Anthropic account team
  - Blocker: legal AI section cannot move beyond SYNTHETIC_ONLY without this

- [ ] **Anthropic DPA executed**
  - Claim: A Data Processing Addendum is in place between HUMMBL and Anthropic
  - Source: same as above
  - Evidence needed: countersigned DPA document

- [ ] **Anthropic US-only routing confirmed**
  - Claim: Anthropic routes HUMMBL API calls through US infrastructure only
  - Source: same as above
  - Evidence needed: contractual routing clause or Anthropic confirmation email

- [ ] **Anthropic incident SLA for HUMMBL**
  - Claim: A specific incident response SLA applies to HUMMBL's Anthropic usage
  - Source: same as above
  - Evidence needed: SLA clause in contract or enterprise agreement

- [ ] **OpenRouter "34 free-tier models" count**
  - Claim: OpenRouter has 34 free-tier models available
  - Source: `hummbl-governance/docs/` (PR #625 research brief)
  - Evidence needed: fetch timestamp, source URL, parser command, raw count output
  - Note: unclear whether count includes `:free` suffix variants, `$0/$0` pricing rows,
    or excludes OpenRouter pseudo-models (aggregators)

- [ ] **Linear adapter unconditionally live**
  - Claim: Linear is one of "7 live adapters" without qualification
  - Source: `hummbl-governance/hummbl_governance/docs/SAFETY_STACK.md`,
    `hummbl-governance/hummbl_governance/docs/governance/AI_RISK_ASSESSMENT.md`,
    `hummbl-governance/hummbl_governance/docs/investigation/daily_activity_reconstruction.md`
  - Reality: adapter defaults to mock data when `LINEAR_API_KEY` env var is unset
  - Fix: add "conditionally live (requires LINEAR_API_KEY)" qualifier to all three docs
  - Status: fix in progress (docs/code parity tracker item)

- [ ] **Krineia ADR-001 "FROZEN at v1.0"**
  - Claim: ADR-001 status declared "FROZEN at v1.0 (May 15 LOI gate)"
  - Source: `krineia/docs/adr/ADR-001-receipt-chain-standard.md`
  - Reality: acceptance criteria not yet met (RECEIPT_SCHEMA.md still DRAFT,
    INVARIANTS.md not written, no git tag v1.0.0)
  - Fix: status changed to "ACCEPTED — FREEZE PENDING" (done 2026-05-04)
  - Resolution: close this entry when `git tag v1.0.0` exists on krineia

---

## Closed

_(none yet)_

---

## Resolution protocol

1. Attach evidence artifact (doc path, contract scan, API response with timestamp)
2. Update the owning document to cite the evidence
3. Check the box and record the date closed
