# Source Packet: Strava Global Heatmap Military Exposure

**incident_id:** `wearable-opsec-01`  
**short_name:** `Strava global heatmap military base exposure`  
**status:** pending full source URL verification  
**source_type:** incident report (public reporting + platform response synthesis)

## Reported narrative

Public reports described that location traces visible through public fitness heatmaps can reveal sensitive movement patterns around military or security-sensitive facilities.

## What is in-scope

- Source-level location aggregation behavior.
- Public discoverability of recurring movement routes.
- Operational inference risk from aggregate pattern visibility.

## What is out-of-scope

- Specific attribution of individual victims.
- Any claim that HUMBL infrastructure causes or prevents these events by itself.
- Legal conclusions.

## Suggested inference boundary

- `what_can_be_inferred`: location data design can leak high-value movement context without intent to share precise coordinates.  
- `what_must_not_be_inferred`: no automatic equivalence between this incident and HUMBL design failure without deployment-specific receipt.

## Open follow-up tasks

- Attach archived source links with stable URLs.
- Attach publication dates where available.
- Link public claim-safe language for any future issue briefings.
