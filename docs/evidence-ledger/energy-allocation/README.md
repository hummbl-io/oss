# Energy-Allocation Evidence Ledger Extension

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #564
- **Operator approval:** Approved by Operator on 2026-06-28
- **Source seed:** YouTube video `uT3PwI_pX5E` (Martin Picard, Energy Constraints and Tradeoffs)
- **Source status:** `video_verified_metadata_only`
- **Transcript status:** `pending`
- **Namespace status:** external vocabulary only (MDEE, metaboception, mitoception, GMR); no new HUMMBL term canonized

## Purpose

Extend evidence-ledger support for energy-allocation, stress, sleep, recovery, and executive-health claims so future artifact-compiler packets can distinguish source authority and claim maturity.

## Schema

`schemas/evidence-ledger/energy_claim.schema.json` — Draft 2020-12 JSON Schema with:

- 13 required fields
- source_type enum (8 values): peer_reviewed_article, review_article, study_registration_or_recruitment_page, institutional_public_material, public_video_metadata, public_video_transcript, secondary_report, product_or_wearable_claim
- claim_class enum (7 values): ux_metaphor, coaching_heuristic, physiological_hypothesis, biomarker_supported, wearable_supported, peer_reviewed_human_evidence, clinical_claim
- human_subject_status enum (5 values)
- transcript_status enum (4 values)
- approval_status enum (5 values): proposed, operator_approved_for_investigation, evidence_bounded, rejected, canonized
- risk_boundaries with 4 boolean flags
- do_not_infer array for explicit boundary documentation

## Fixture

`fixtures/evidence-ledger/picard_energy_constraints.json` — Picard / Energy Constraints / MDEE fixture with:
- source_type: public_video_metadata (video metadata only, not transcript)
- claim_class: physiological_hypothesis
- transcript_status: pending
- approval_status: operator_approved_for_investigation
- namespace_audit_required: true (external terms need audit)
- 5 do_not_infer boundaries documented

## Do Not Infer

- Do not treat video metadata as a transcript
- Do not promote secondary symposium reporting to final primary evidence
- Do not convert energy-allocation models into personalized medical advice
- Do not infer that mitochondrial function claims are clinically validated without peer-reviewed evidence
- External terms (MDEE, metaboception, mitoception, GMR) are external vocabulary only; no new HUMMBL term canonized

## Acceptance Criteria

- [x] Implement ledger extension for energy-allocation / recovery claims
- [x] Support mixed authority sources (8 source types)
- [x] Require transcript status for video-derived claims
- [x] Require claim class before artifact-compiler promotion
- [x] Require population scope and do_not_infer boundaries
- [x] Require namespace-audit flag for any new HUMMBL candidate term
- [x] Add fixture for Picard / Energy Constraints / MDEE with video metadata-only status
