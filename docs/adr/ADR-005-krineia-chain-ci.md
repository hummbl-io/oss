# ADR-005 — KRINEIA Chain Verification CI Check

- **Status:** accepted
- **Date:** 2026-06-23
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** none (process ADR)
- **Retrospective:** `docs/artifacts/RETROSPECTIVE_wave_4.md` (P17)

## Context

The KRINEIA receipt chain (`_receipts/krineia/primary.jsonl`) is HUMMBL's audit trail. Every governance event (artifact promotion, manifest adoption, claims change) emits a receipt with:

- A unique `id` (UUID)
- A `prev_hash` linking to the prior receipt
- A `hash` (SHA-256 of the canonical JSON, excluding the hash field)
- A `state` (event name + payload)
- A `time` (ISO 8601 timestamp)

The chain is append-only and hash-chained: tampering with any receipt breaks the chain because the next receipt's `prev_hash` won't match, and the tampered receipt's `hash` won't match the recomputed hash.

### The problem

The chain was previously verified manually:
- `python3 -c "import json, hashlib; ..."` (ad hoc, error-prone)
- Visual inspection of the JSONL file (does not catch hash mismatches)

There was no automated check that:
1. Every receipt's `prev_hash` matches the prior receipt's `hash`
2. Every receipt's `hash` is correctly computed (no tampering)
3. The genesis receipt's `prev_hash` is all zeros
4. There are no duplicate receipt IDs
5. Every receipt has the required fields

A tampered receipt (e.g., a backdated timestamp, a modified payload, a forged hash) would not be caught until an auditor inspected the chain. By then, the tampering would be undetectable (the chain is append-only; you can't fix a broken link without rewriting all subsequent receipts).

### What P17 does

P17 (KRINEIA chain verification CI check) runs `scripts/validate_krineia_chain.py` on every push/PR that touches the chain or the validator. The validator:

- Parses every line as JSON (catches corruption)
- Checks every receipt has the 5 required fields (`id`, `prev_hash`, `hash`, `state`, `time`)
- Verifies the hash chain: each receipt's `prev_hash` matches the prior receipt's `hash`
- Recomputes each receipt's `hash` and verifies it matches (catches tampering)
- Checks the genesis receipt's `prev_hash` is all zeros
- Checks for duplicate receipt IDs
- Checks timestamps are present

The validator has 14 tests, all passing, covering: valid chain, missing file, empty file, invalid JSON, missing fields, broken prev_hash link, tampered hash, genesis with wrong prev_hash, duplicate IDs, unexpected fields, hash determinism, hash excludes hash field, hash key-order independence, and the real chain.

## Decision

**Adopt P17: run `scripts/validate_krineia_chain.py` as a CI check on every push/PR that touches the KRINEIA chain or the validator.**

### Scope

This ADR applies to:
- The primary KRINEIA chain at `_receipts/krineia/primary.jsonl`
- Any future KRINEIA chains (e.g., per-repo chains, per-agent chains)
- The validator script `scripts/validate_krineia_chain.py`
- The CI workflow `.github/workflows/krineia-validation.yml`

### Out of scope

- Receipt emission (handled by `scripts/emit_receipt.py`)
- Receipt content validation (the validator checks structure, not whether the payload is correct)
- Cross-repo chain verification (each repo has its own chain)

### What this enables

- **Tamper detection:** Any modification to a receipt (backdated timestamp, modified payload, forged hash) is caught at push time, before merge.
- **Chain integrity:** A broken `prev_hash` link (e.g., from a bad merge or a manual edit) is caught at push time.
- **Audit readiness:** An auditor can run the same validator and get the same result. The chain is self-verifying.
- **Defense in depth:** The chain is already hash-chained (structural integrity). P17 adds automated verification (operational integrity). Together, they provide defense in depth.

## Alternatives considered

### Alternative 1: Manual verification on demand

**What:** Run the validator manually when needed (e.g., before an audit).

**Why rejected:** Manual verification is easy to forget. A tampered receipt could sit in the chain for months before anyone notices. CI verification catches tampering at push time, before it merges.

### Alternative 2: GPG-sign each receipt

**What:** Sign each receipt with the operator's GPG key ([REDACTED-GPG-KEY]) and verify signatures in CI.

**Why rejected:** GPG signing requires the operator's passphrase for every receipt emission. This blocks automated receipt emission (the emit_receipt.py script runs without prompts). The hash chain already provides tamper detection (a tampered receipt breaks the chain). GPG signing adds non-repudiation (the operator can't deny emitting the receipt), but that is a higher bar than HUMMBL currently needs. P17 can be extended to GPG verification in a future ADR if needed.

### Alternative 3: Use a blockchain / distributed ledger

**What:** Store the KRINEIA chain on a blockchain (Ethereum, Hyperledger, etc.) for decentralized tamper resistance.

**Why rejected:** HUMMBL's chain is internal. A blockchain adds cost, complexity, and external dependencies for no benefit. The hash chain + CI verification provides sufficient tamper detection for an internal audit trail. A blockchain is appropriate for multi-party audit trails where no single party is trusted; HUMMBL's chain is single-party (the operator emits all receipts).

## Consequences

### Positive

- Tamper detection at push time (before merge)
- Chain integrity verification (broken links caught)
- Audit readiness (auditor can run the same validator)
- Defense in depth (structural + operational integrity)
- 14 tests covering edge cases (all passing)

### Negative

- CI adds ~10 seconds per run (Python startup + chain parse + hash computation)
- The validator does not check payload correctness (e.g., that a `governance.artifact_promoted` receipt has the right payload fields). This is a future extension (P19 candidate).

### Neutral

- The validator is the canonical chain verification tool. Any other tool that verifies the chain must produce the same result.
- The chain remains append-only. The validator does not modify the chain.

## Verification

A reader can verify this ADR is in effect by:

1. **The validator exists:** `ls scripts/validate_krineia_chain.py`
2. **The CI workflow exists:** `ls .github/workflows/krineia-validation.yml`
3. **The tests pass:** `python -m pytest scripts/test_validate_krineia_chain.py -v`
4. **The real chain passes:** `python scripts/validate_krineia_chain.py`
5. **The CI workflow runs on push:** Check GitHub Actions tab for "KRINEIA Chain Validation (P17)"

## References

- Wave 4 retrospective: `docs/artifacts/RETROSPECTIVE_wave_4.md` (P17)
- KRINEIA chain: `_receipts/krineia/primary.jsonl`
- Receipt emission script: `scripts/emit_receipt.py`
- Validator: `scripts/validate_krineia_chain.py`
- Tests: `scripts/test_validate_krineia_chain.py`
- CI workflow: `.github/workflows/krineia-validation.yml`
- ADR-001: `docs/adr/ADR-001-repo-governance-baseline.md` (item 21)
- ADR-004: `docs/adr/ADR-004-single-branch-workflow.md` (item 22)
- P7 (claims CI): `.github/workflows/claims-validation.yml`
- P11 (manifest CI): `.github/workflows/manifest-validation.yml`

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL. **Devin** (and other software agents) are delegated drafting, research, and execution systems. This ADR was drafted by Devin at the direction of the Principal Agent, based on the wave 4 retrospective (P17) and the KRINEIA chain's role as HUMMBL's audit trail, and was accepted by Principal Agent decision on 2026-06-23. This ADR is **public** — it documents a CI check that affects how the KRINEIA chain is verified, and is published for transparency.
