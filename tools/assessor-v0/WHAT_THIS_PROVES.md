# What Assessor Pack v0 Proves (and Does Not)

**Alpha-honest boundary.** This document is the claim envelope for
`tools/assessor-v0/`. Anything not listed under **Proves** is out of
scope.

## Proves

Given a JSONL file of public tuple records:

1. **Shape:** Each line is JSON with `tuple_type` in
   `{CONTRACT, DCT, EVIDENCE}` and the required envelope fields used by
   `hummbl-tuples` public schemas (`id`, `time`, `intent_id`, `task_id`,
   `tuple_data`, `state`, `drift`, `tier`, `agent`, `tool`).
2. **Type payloads:** Minimal required keys inside `tuple_data` for each
   type (CONTRACT: objective / allowed_tools / outputs / risk_tier;
   DCT: issuer / subject / ops_allowed; EVIDENCE: event).
3. **Local chain discipline:** When `previous_hash` is present, it is
   either `null` (genesis) or a 64-char lowercase hex SHA-256 string, and
   consecutive non-null links match the assessor's recomputed prior-line
   digest (assessor-local hashing, not a fleet ReceiptEngine signature).
4. **Cross-type intent binding:** All records that share an `intent_id`
   also share the same `task_id` within the file.

## Does not prove

- Production readiness, production use, or daily fleet operation
- Compliance certification (SOC2, GDPR, NIST AI RMF, EU AI Act, etc.)
- Cryptographic authenticity of live HMAC/Ed25519 DCT signatures
- ReceiptEngine K1 integrity against a deployed signing secret
- That a third party ran the same commands in the same environment
- Competitor absence of features, uniqueness, or categorical superiority
- Anything about Atlas Constitution (public **C** = **CONTRACT**)

## Citation

- Governance Tuple Protocol: `docs/research/2026-08-23_governance-tuple-protocol-spec.md`
- Zenodo Tuple v2.1: DOI [10.5281/zenodo.21957831](https://doi.org/10.5281/zenodo.21957831)
- Claim ledger spirit: `packages/python/hummbl-governance/docs/public-claims.md`
  (`production_use_established` remains false for general claims)

If you need a stronger claim, publish a dated public receipt and update
the landing claims ledger first. Do not stretch Assessor v0 output.
