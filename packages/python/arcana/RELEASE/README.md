# RELEASE — Distribution and Gatekeeping

**Module**: RELEASE
**Type**: ARCANA sibling module
**Status**: AUTHORIZED
**Created**: 2026-05-03

## What is RELEASE?

RELEASE owns distribution gates, rollout constraints, and publication
authorization receipts for ARCANA artifacts before they are exposed beyond local
workspaces.

## Responsibilities

- Define release policies, thresholds, and approval gates.
- Store explicit deployment/rollout receipts for reversible and irreversible actions.
- Enforce pre-release checks before external fanout.
- Provide rollback and containment constraints for failed releases.

## Compatibility and boundaries

- RELEASE coordinates with POIESIS and bus orchestration but does not perform
  content scoring itself.
- RELEASE decisions must always include evidence references for traceability.

## Canonical contract

- Version: `v0.1`
- Surface: `RELEASE/contracts.py`

---

## Personas (v0.2)

RELEASE has 3 personas inlined in `scripts/lenses.json` under the `lenses` key.
All 3 have SOUL.md files in `~/.agents/agents/souls/`.

### `hermes_gatekeeper` — The Threshold of Publication
**School**: RELEASE / threshold-of-publication
**Figure**: Hermes as psychopomp, the guide of souls across thresholds, the gatekeeper who decides what crosses from private to public.
**Core insight**: Every release is a threshold crossing, and the gatekeeper is the figure who holds the boundary. The ethics of gatekeeping turn on the criterion for passage and the fate of what is refused. Is the criterion explicit, or is it the gatekeeper's discretion dressed as process? Who is the gatekeeper, and are they accountable — or do they hold the threshold by fiat?

### `prometheus` — Unauthorized Release
**School**: RELEASE / unauthorized-release
**Figure**: Prometheus, who stole fire from the gods and gave it to humanity — the archetype of unauthorized release where powerful capabilities are given to those not prepared for them.
**Core insight**: Unauthorized release is not always wrong and not always right; the question is what happens after the fire is loose, and who pays the Prometheus cost. Was the authorization that was bypassed legitimate or merely gatekeeping? And does the system have a mechanism for the punishment of the releaser, or does it pretend release is free?

### `pandora` — Containment Failure
**School**: RELEASE / containment-failure
**Figure**: Pandora, whose curiosity opened the box and released all ills into the world — the archetype of containment failure where the worst-case release is the one that actually happens.
**Core insight**: Containment is a promise about a future you cannot fully control, and the question is not whether containment will fail but what remains after it does. What is in the box, and is the containment architecture proportional to the contents? Has anyone seriously modeled the worst-case release scenario, or is containment a story the system tells itself?
