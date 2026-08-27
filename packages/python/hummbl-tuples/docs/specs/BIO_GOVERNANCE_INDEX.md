# Bio-Governance Index

Date: 2026-03-27
Status: draft

## Purpose

Provide a single entry point for the emerging bio-cognitive, bio-operational, and bio-governance lane in `hummbl-tuples`.

## Core Frame

This lane is organized around three layers:

- `bio-cognitive`
  - sensing and modeling human state
- `bio-operational`
  - adapting tasks, interfaces, and training in response
- `bio-governance`
  - constraining, supervising, and auditing those adaptations

## Key Specs

- [BIO_COGNITIVE_TERMINOLOGY.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/specs/BIO_COGNITIVE_TERMINOLOGY.md)
- [BIO_GOVERNANCE_TUPLE_TAXONOMY.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/specs/BIO_GOVERNANCE_TUPLE_TAXONOMY.md)

## Key Research Notes

- [BIO_COGNITIVE_STANDARDS_MEMO.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_COGNITIVE_STANDARDS_MEMO.md)
- [BIO_COGNITIVE_EXPERIMENT_BRIEF.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_COGNITIVE_EXPERIMENT_BRIEF.md)
- [BIO_COGNITIVE_HUMMBL_BRIDGE.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/docs/research/BIO_COGNITIVE_HUMMBL_BRIDGE.md)

## Schemas

### Signal And State

- [bio_signal_captured.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_signal_captured.schema.json)
- [readiness_inferred.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/readiness_inferred.schema.json)
- [workload_inferred.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/workload_inferred.schema.json)
- [strain_flagged.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/strain_flagged.schema.json)

### Adaptation And Authority

- [bio_adaptation_proposed.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_adaptation_proposed.schema.json)
- [bio_action_authorized.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_action_authorized.schema.json)
- [bio_action_blocked.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_action_blocked.schema.json)
- [bio_override.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_override.schema.json)
- [bio_adaptation_executed.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_adaptation_executed.schema.json)

### Outcomes And Harms

- [bio_outcome_observed.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_outcome_observed.schema.json)
- [bio_harm_signal.schema.json](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/schemas/bio_harm_signal.schema.json)

## Examples

- [examples/bio/README.md](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-tuples/examples/bio/README.md)

The current example set covers:

- low-stakes session fatigue
- HOTL supervision
- blocked actions
- overrides
- observed harms

## Working Rule

This lane should stay:

- non-clinical by default
- operator-centered
- standards-aware
- and explicit about the difference between signal, inference, recommendation, authorization, and outcome

## Next Moves

- add machine-readable activity classification tuples tied to Compendium-style activity codes
- add a dedicated experiment matrix across control regimes
- connect the lane directly to readiness and BKI in the Unified Tier Framework
