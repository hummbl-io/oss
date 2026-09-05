# Artifact Manifest

**Standard:** HUMMBL Repo Standard v0.1
**Last reviewed:** 2026-06-23
**Steward:** HUMMBL, LLC
**Cadence:** weekly review, quarterly archival sweep

This manifest lists the artifacts retained in this public tree. Private artifacts are omitted; gaps in item numbers preserve historical identifiers and do not imply missing public files. Historical review entries describe earlier states and are not fresh verification of claims or publication readiness.

## Status legend

- `draft` — being written
- `live` — published and current
- `stale` — past last review date, needs review or archival
- `archived` — no longer active, kept in git history with receipt

## Wave 1 — Foundation (days 1-30)

| #   | Artifact                                                       | Path                                                    | Status         | Reader                                      | Decision                               | Last reviewed | Trigger fired?                         |
| --- | -------------------------------------------------------------- | ------------------------------------------------------- | -------------- | ------------------------------------------- | -------------------------------------- | ------------- | -------------------------------------- |
| 1   | White paper: Why Governance Infrastructure for AI-Native Teams | docs/artifacts/WHITE_PAPER_governance_infrastructure.md | live           | enterprise buyer, analyst                   | take HUMMBL seriously                  | 2026-06-23    | yes                                    |
| 4   | Competitive analysis: AI governance vendors                    | docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md    | live           | enterprise buyer, analyst                   | shortlist HUMMBL                       | 2026-06-23    | yes                                    |
| 7   | Case study: Claims remediation 2026-06-23                      | docs/artifacts/CASE_STUDY_claims_remediation.md         | live           | enterprise buyer                            | proof we do what we say                | 2026-06-23    | yes                                    |
| 9   | Position paper: EU AI Act readiness                            | docs/artifacts/POSITION_PAPER_eu_ai_act.md              | live           | compliance buyer                            | engage HUMMBL for EU readiness         | 2026-06-23    | yes                                    |
| 10  | Position paper: NIST AI RMF alignment                          | docs/artifacts/POSITION_PAPER_nist_ai_rmf.md            | live           | compliance buyer                            | engage HUMMBL for NIST alignment       | 2026-06-23    | yes                                    |
| 11  | Doctrine: AI governance principles                             | docs/artifacts/DOCTRINE_ai_governance.md                | live           | team, agents                                | decision consistency                   | —             | yes                                    |
| 12  | Charter: HUMMBL, LLC                             | docs/artifacts/CHARTER_hri.md                           | live           | steward, operators                          | what HRI may decide                    | —             | yes                                    |
| 13  | Evidence pack: fleet governance rollout                        | docs/artifacts/EVIDENCE_PACK_fleet_rollout.md           | live           | enterprise buyer, analyst                   | credibility                            | —             | yes                                    |
| 14  | Playbook: claims change protocol                               | docs/artifacts/PLAYBOOK_claims_change.md                | live           | agents, operators                           | consistent claim changes               | —             | yes                                    |
| 15  | Playbook: fleet rollout protocol                               | docs/artifacts/PLAYBOOK_fleet_rollout.md                | live           | agents, operators                           | consistent rollouts                    | —             | yes                                    |
| 16  | ADR-002: IssueOps teaching surface decision                    | docs/adr/ADR-002-issueops-teaching-surface.md           | live           | team                                        | build / don't build                    | —             | yes                                    |
| 17  | ADR-003: Game engine roadmap decision                          | docs/adr/ADR-003-game-engine-roadmap.md                 | live           | team                                        | pursue / don't pursue                  | —             | yes                                    |
| 20  | Artifact manifest (this file)                                  | docs/artifacts/ARTIFACT_MANIFEST.md                     | live           | Operator + agents                             | what to create next                    | 2026-06-23    | yes                                    |
| 21  | ADR-001: hummbl-production repo governance baseline            | docs/adr/ADR-001-repo-governance-baseline.md            | live           | team                                        | repo governance baseline               | 2026-06-23    | yes (added Day 21 — predated manifest) |
| 22  | ADR-004: Single-branch workflow decision                       | docs/adr/ADR-004-single-branch-workflow.md              | live           | team                                        | single-branch vs two-branch workflow   | 2026-06-23    | yes                                    |
| 23  | Playbook: agent onboarding                                     | docs/artifacts/PLAYBOOK_agent_onboarding.md             | live           | agents, operators                           | consistent agent activation            | 2026-06-23    | yes                                    |
| 24  | Position paper: SOC 2 Type II readiness                        | docs/artifacts/POSITION_PAPER_soc2_type_ii_readiness.md | live           | enterprise buyer, compliance buyer, auditor | engage HUMMBL for SOC 2                | 2026-06-23    | yes                                    |
| 25  | ADR-005: KRINEIA chain verification CI                         | docs/adr/ADR-005-krineia-chain-ci.md                    | live           | team                                        | automated chain verification           | 2026-06-23    | yes                                    |
| 26  | ADR-006: Rate limiting strategy                                | docs/adr/ADR-006-rate-limiting-strategy.md              | live           | team                                        | API abuse protection architecture      | 2026-06-25    | yes                                    |
| 27  | ADR-007: API key tier system                                   | docs/adr/ADR-007-api-key-tier-system.md                 | live           | team                                        | API tier and key model                 | 2026-06-25    | yes                                    |
| 28  | ADR-008: Open Brain fallback mode                              | docs/adr/ADR-008-open-brain-fallback.md                 | live           | team                                        | Open Brain dependency failure behavior | 2026-06-25    | yes                                    |
| 29 | Evidence packet: IL4/IL5 air-gap claim | docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md | draft | operator, legal, security | claim boundary | 2026-07-03 | yes |
| 30 | Model Router v2: co-design scoring | docs/artifacts/MODEL_ROUTER_V2_CODESIGN_SCORING.md | draft | engineering, agents | router design | 2026-07-03 | yes |
| 31 | Model Router v2: grindability gate | docs/artifacts/MODEL_ROUTER_V2_GRINDABILITY_GATE.md | draft | engineering, agents | router design | 2026-07-03 | yes |
| 32 | Privacy policy surface plan | docs/artifacts/PRIVACY_POLICY_SURFACE_PLAN.md | draft | operator, legal | policy review | 2026-07-03 | yes |
| 33 | Public surface claim sync receipt | docs/artifacts/PUBLIC_SURFACE_CLAIM_SYNC_RECEIPT.md | draft | agents, reviewers | claim review | 2026-07-03 | yes |
| 34 | Ownward reflective friction gates | docs/artifacts/OWNWARD_REFLECTIVE_FRICTION_GATES.md | draft | product, governance | product behavior | 2026-07-03 | yes |
| 35 | Ownward language law draft | docs/artifacts/OWNWARD_LANGUAGE_LAW.md | draft | product, legal, governance | copy and law boundary | 2026-07-03 | yes |
| 36 | Open-weight model-router candidates | docs/artifacts/OPEN_WEIGHT_MODEL_ROUTER_CANDIDATES.md | draft | engineering, model-router | routing set definition | 2026-07-03 | yes |
| 37 | Wearable OPSEC incident-ledger schema | docs/security/wearable-opsec/incident-ledger.schema.v0.1.json | draft | security, Ownward | source and inference boundaries | 2026-07-03 | yes |
| 38 | Wearable OPSEC incident ledger | docs/security/wearable-opsec/incident-ledger.v0.1.md | draft | security, Ownward, consulting | ledger coverage | 2026-07-03 | yes |

## Wave 2 — Persuasion & positioning (days 31-60)

Pending Wave 1 completion. Artifacts added as triggers fire.

## Wave 3 — Operations & resilience (days 61-90)

Pending Wave 2 completion. Artifacts added as triggers fire.

## Wave 4 — As triggered (day 90+)

Artifacts created only when their trigger fires.

## Archived

| Artifact     | Archived date | Reason |
| ------------ | ------------- | ------ |
| _(none yet)_ |               |        |

## Review log

| Date       | Reviewer        | Action                                                                                                                                                                                                                                                                                                                 |
| ---------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-06-23 | devin           | Manifest created with Wave 1 list (20 artifacts)                                                                                                                                                                                                                                                                       |
| 2026-06-23 | devin           | Day 2: strategic plan drafted (item 2 → draft)                                                                                                                                                                                                                                                                         |
| 2026-06-23 | devin           | Day 3: risk register drafted (item 3 → draft)                                                                                                                                                                                                                                                                          |
| 2026-06-23 | devin           | Day 4: competitive analysis drafted (item 4 → draft)                                                                                                                                                                                                                                                                   |
| 2026-06-23 | devin           | Day 5: IssueOps business case drafted (item 5 → draft)                                                                                                                                                                                                                                                                 |
| 2026-06-23 | board           | Triggered Board meeting (5 Directors) — UNANIMOUS_ACCEPT with 3 conditions (bus REVIEW 2026-06-23)                                                                                                                                                                                                                     |
| 2026-06-23 | devin           | Promotion packet drafted per Board conditions — Day 6+ paused pending PA decision                                                                                                                                                                                                                                      |
| 2026-06-23 | principal-agent | PA approved promotion packet as written — items 1-5 promoted to live (1, 4 public; 2, 3, 5 private); Phase 1 funding approved; Day 6+ resumed per re-sequenced plan (case study first)                                                                                                                                 |
| 2026-06-23 | devin           | Day 6: case study (claims remediation 2026-06-23) drafted + promoted to live (public); 16 case study claims added to manifest (CS-001..CS-016); total claims now 117, validated 89                                                                                                                                     |
| 2026-06-23 | devin           | Day 7: EU AI Act position paper drafted + promoted to live (public); 14 EU claims added (EU-001..EU-014); total claims now 131, validated 103; existing claims sanitized to utf-8                                                                                                                                      |
| 2026-06-23 | devin           | Day 8: NIST AI RMF position paper drafted + promoted to live (public); 14 NIST claims added (NR-001..NR-014); total claims now 145, validated 117; crosswalk to EU AI Act noted (same primitives, different mapper)                                                                                                    |
| 2026-06-23 | devin           | Day 11: doctrine (AI governance principles) drafted + promoted to live (public); 14 doctrine claims added (DO-001..DO-014); total claims now 185, validated 153; 10 principles as decision-consistency baseline; principles 1/6/7 are constitutional invariants                                                        |
| 2026-06-23 | devin           | Day 12: charter (HUMMBL, LLC) drafted + promoted to live (public); 12 charter claims added (CH-001..CH-012); total claims now 197, validated 165; HRI is functional role not legal entity; Director is PA; Board is advisory                                                                             |
| 2026-06-23 | devin           | Day 13: evidence pack (fleet governance rollout) drafted + promoted to live (public); 14 evidence claims added (EP-001..EP-014); total claims now 211, validated 178, unproven 5; credibility pack for enterprise buyer/analyst; 10 evidence items with runnable verification commands                                 |
| 2026-06-23 | devin           | Day 14: playbook (claims change protocol) drafted + promoted to live (public); 12 playbook claims added (PB-001..PB-012); total claims now 223, validated 190, unproven 5; 5 change types (add/update/validate/retract/remove); 4 roles; 6 common mistakes documented; WAVE 2 COMPLETE                                 |
| 2026-06-23 | devin           | Day 15: playbook (fleet rollout protocol) drafted + promoted to live (public); 12 fleet claims added (FR-001..FR-012); total claims now 235, validated 202; 4 rollout scenarios; 5 roles; 6 verification commands; rollback procedure; wave 3 first artifact                                                           |
| 2026-06-23 | devin           | Day 16: ADR-002 (IssueOps teaching surface decision #410) drafted + promoted to live (public); 12 ADR claims added (AD2-001..AD2-012); total claims now 247, validated 214; decision: build Phase 1 at hummbl.io/issueops.html; /usr/bin/bash capital, ~40 hours, 3-week implementation                                |
| 2026-06-23 | devin           | Day 17: ADR-003 (game engine roadmap decision #408) drafted + promoted to live (public); 12 ADR claims added (AD3-001..AD3-012); total claims now 259, validated 226; decision: fund Stage 0 (doctrine + schema + simulation affordance for 8 primitives); $15-25K, 4-6 weeks; playable governance category            |
| 2026-06-23 | devin           | Day 22: ADR-004 (single-branch workflow) drafted + promoted to live (public); 12 ADR-004 claims added (AD4-001..AD4-012); total claims now 295, validated 261; codifies P12 from wave 3 retrospective; eliminates F10 + F11                                                                                            |
| 2026-06-23 | devin           | Day 23: playbook (agent onboarding) drafted + promoted to live (public); 12 onboarding claims added (AO-001..AO-012); total claims now 307, validated 273; 6-step protocol, 5 roles, 6 common mistakes, 6-step retirement checklist                                                                                    |
| 2026-06-23 | devin           | Day 24: position paper (SOC 2 Type II readiness) drafted + promoted to live (public); 12 SOC 2 claims added (SO2-001..SO2-012); total claims now 319, validated 284; maps HUMMBL to 4 of 5 SOC 2 TSC; 6 operational gaps; 4-phase readiness plan; WAVE 4 COMPLETE                                                      |
| 2026-06-23 | devin           | Day 25: ADR-005 (KRINEIA chain verification CI) drafted + promoted to live (public); P16 manifest insertion helper added; P17 validator + 14 tests + CI workflow; 12 ADR-005 claims added (AD5-001..AD5-012); total claims now 331, validated 296; chain has 18 receipts, all verified                                 |
| 2026-06-25 | codex           | Registered orphan ADR-006, ADR-007, and ADR-008 in manifest; clears validate_manifest.py orphan warnings.                                                                                                                                                                                                              |
