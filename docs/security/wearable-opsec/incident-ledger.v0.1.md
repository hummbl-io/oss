# Wearable OPSEC Incident Ledger v0.1

**Status:** candidate evidence ledger for issue `#569`  
**Scope:** wearable and fitness-device OPSEC incidents relevant to protected-person contexts  
**Purpose:** maintainable incident catalog for source-backed design and consulting use  
**Last reviewed:** 2026-07-03

## Problem

Ownward and HUMBL-facing consulting materials need a bounded source ledger before turning
wearable/location incidents into design or product prescriptions.

This ledger keeps incidents explicit about what is factual, what is reported, what is
response-level action, and what HUMBL/Ownward may or may not infer.

## Ledger schema

The ledger follows `incident-ledger.schema.v0.1.json` and includes:

- `incident_id`
- `short_name`
- `date_event_or_reported`
- `source_url`
- `source_type`
- `source_reliability_notes`
- `actors_or_population`
- `device_or_platform`
- `exposed_data_types`
- `protective_intelligence_surface`
- `reported_impact`
- `official_response`
- `product_implication`
- `consulting_implication`
- `federal_defense_relevance`
- `what_can_be_inferred`
- `what_must_not_be_inferred`
- `public_claim_safe`
- `source_packet_path`
- `receipt_hash_optional`

## Incident catalog (seed set)

| Incident | Short name | Population | Source status | Claim-safe reading |
|---|---|---|---|---|
| `wearable-opsec-01` | Strava global heatmap military base exposure | military personnel and public users near operational areas | report summary packet exists | Location traces can persist in aggregate visualizations longer than expected; does not imply universal victimization |
| `wearable-opsec-02` | DoD geolocation policy for fitness platforms in operational contexts | U.S. service-connected personnel and protected persons | policy packet exists | Policy language distinguishes data class, mission profile, and platform controls; not a product safety verdict |
| `wearable-opsec-03` | Polar Flow military/diplomatic-adjacent investigation | diplomats, military attachés, intelligence personnel | investigative packet exists | Exposure reports require separate confirmation before operational inference |
| `wearable-opsec-04` | Biden / connected-fitness security concerns | high-profile protectees and households with connected devices | report packet exists | Security concerns are often about operational discipline plus public-facing platform behavior, not platform architecture claims |
| `wearable-opsec-05` | Bodyguard-social fitness exposure | protectees, bodyguards, private security teams | reporting packet exists | Presence on activity platforms can create triangulation risk where physical context is predictable |
| `wearable-opsec-06` | Secret Service bodyguard platform exposure reporting | protectees, federal protection teams | reporting packet exists | Similar pattern as other incidents; inference requires mission-specific corroboration |
| `wearable-opsec-07` | Swedish PM / royal-family Strava exposure and Säpo response | dignitaries and associated household/ security teams | reporting packet exists | Official response evidence should be attached before using as prescriptive claim |

## Packet index

- `source-packets/wearable-opsec-01-strava-global-heatmap.md`
- `source-packets/wearable-opsec-02-dod-fitness-geolocation-policy.md`
- `source-packets/wearable-opsec-03-polar-flow-investigation.md`
- `source-packets/wearable-opsec-04-biden-connected-fitness-security.md`
- `source-packets/wearable-opsec-05-bodyguard-social-fitness-reporting.md`
- `source-packets/wearable-opsec-06-secret-service-bodyguard-exposure.md`
- `source-packets/wearable-opsec-07-royal-family-strava-sapo-response.md`

## Use constraints

Use this ledger as a bounded source layer only:

- Do not infer HUMBL-level security guarantees from incident recurrence.
- Do not infer public policy outcomes.
- Do not use incident-level reporting as a substitute for direct deployment evidence.
- Require explicit product-owner review before public claims reference any incident.

## Open questions

1. Which protectee categories (government, defense, executive, humanitarian) should share one
   inference boundary.
2. What retention controls are needed before any incident facts enter internal training or
   eval fixtures.
3. How to represent uncertainty and redaction level without overclaiming.
4. Which incidents should be excluded from external consulting one-pagers because they add
   no durable design signal.

## Do not infer

- This ledger does not certify or invalidate HUMBL for protectee safety by itself.
- This ledger does not establish a direct technical remediation sequence without separate engineering fixtures.
- This ledger does not authorize claims about legal, medical, or criminal outcomes.
