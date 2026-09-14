# PSI Ship → arcana topic-spec Mapping

Status: **draft** — contract proposal for the cross-repo pipeline join
(Option D from `psi-crucible-integration-options.md`). Defines how a PSI
Ship-gated innovation becomes an arcana topic-spec input. No code yet; this
is the contract before the join.

## Context

PSI refines **noisy intent → fleet-ready signal** (`PSI/docs/signal-pipeline.md`).
arcana refines **topic → article family → scored → released**. The join: when
PSI Ship-gates an innovation, that ship-packet becomes an arcana topic-spec
input, so fleet-ready signal gets multi-lens analysis + adversarial debate.

```
PSI:  playground → sandbox → innovations ─[Ship gate]→ fleet
                                              ↓
                                         ship-packet
                                              ↓ (this mapping)
                                         topic-spec-seed
                                              ↓ (arcana grows)
                                         full topic-spec
                                              ↓
                                    arcana debate + paideia + release
```

## The two shapes (grounded)

### PSI ship-packet (`PSI/docs/templates/ship-packet-template.md`)

Header: Innovation title, Date, Source proposal, Owner, Target fleet
destination, Gate (`Ship`), Gate status (`candidate`/`approved`/`rejected`).

Body fields:
- **Fleet Ask** — what should the fleet do?
- **Evidence** — what makes this worth fleet resources?
- **Artifact Target** — ADR / Spec / PRD / Issue / PR / Bus proposal / Product lane
- **Review Required** — who must review before adoption
- **Rollback / Rejection Path** — how to stop or reverse
- **Residual Risk** — what remains uncertain
- **Operator Gate** — Ship criterion ("This is worth fleet resources.") + Approval reference

### arcana topic-spec (`scripts/topics/arcana-metaethics-good-evil-001.json`)

Required keys (`debate_protocol.SPEC_REQUIRED_KEYS`): `topic_id`, `topic`,
`resolution`, `definitions_required`, `constructive_mandate`,
`adversarial_mandate`, `applied_cases`.

Full field list: `topic_id`, `topic`, `resolution`, `domains`,
`definitions_required`, `constructive_mandate`, `adversarial_mandate`,
`arbiter_verdicts`, `applied_cases`, `claim_types`,
`prohibited_reasoning_failures`, `interpretations_to_evaluate`,
`semantic_framings_to_test`, `initial_hypothesis`.

## Field mapping

### Direct (ship-packet → topic-spec)

| Ship-packet field | topic-spec field | Quality |
|---|---|---|
| Innovation title | `topic` | direct |
| Fleet Ask | `resolution` | **shaped** — fleet ask is a directive ("the fleet should do X"); resolution is a proposition ("X should be treated as Y"). The mapping reframes the ask as the proposition under debate. |
| Evidence | `initial_hypothesis` | **lossy** — evidence is a list of justifications; initial_hypothesis is a single statement. Compress evidence into the hypothesis it supports. |
| Target fleet destination | `domains` | **lossy** — fleet destination is a product lane; domains are intellectual disciplines. Map product lane → likely intellectual domains (manual or LLM-assisted). |

### Provenance (ship-packet → new `provenance` block)

The topic-spec has no provenance field today. This contract proposes adding
a `provenance` block to the topic-spec schema:

```json
"provenance": {
  "source": "PSI",
  "ship_packet_path": "PSI/innovations/<slug>/ship-packet.md",
  "ship_packet_hash": "<sha256>",
  "gate_status": "approved",
  "approval_reference": "<operator approval ref>",
  "imported_at": "<UTC ISO>"
}
```

This records where the topic came from, which ship-packet seeded it, and the
operator approval that authorized the Ship gate. Without this, arcana cannot
trace a topic-spec back to its PSI origin.

### Must be authored on the arcana side (ship-packet provides no seed)

These fields are what arcana needs to run a debate + paideia review; the
ship-packet does not provide them, so arcana must grow them (LLM-assisted or
human-authored) from the seed:

| topic-spec field | How arcana grows it |
|---|---|
| `topic_id` | Assigned by arcana: `ARCANA-<DOMAIN>-<SLUG>-<NNN>` |
| `definitions_required` | Derived from the resolution — what terms must be defined before substantive debate? |
| `constructive_mandate` | Authored — how to defend the resolution in its strongest form |
| `adversarial_mandate` | Authored — how to attack the resolution in its strongest form |
| `applied_cases` | Authored — test cases that stress the resolution (2-7 cases) |
| `arbiter_verdicts` | Fixed vocabulary from `debate_protocol.VERDICT_STATUSES` |
| `claim_types` | Derived from `domains` |
| `prohibited_reasoning_failures` | Authored — domain-specific reasoning errors to forbid |
| `interpretations_to_evaluate` | Authored — if the topic has competing interpretations |
| `semantic_framings_to_test` | Authored — if the topic has use/mention or casing distinctions |

### Not mapped (ship-packet fields with no topic-spec target)

| Ship-packet field | Disposition |
|---|---|
| Owner | Recorded in `provenance` (not a topic-spec field) |
| Source proposal | Recorded in `provenance` |
| Date | Recorded in `provenance.imported_at` (the import date; the ship-packet date stays in provenance) |
| Review Required | Not mapped — arcana's review is the debate arbiter, not a human review list |
| Rollback / Rejection Path | Not mapped — arcana is read-only analysis; it does not enact or roll back fleet work |
| Residual Risk | Not mapped to `prohibited_reasoning_failures` (those are reasoning errors, not risks). Could inform `applied_cases` (a risk becomes a test case). Manual. |
| Artifact Target (ADR/Spec/PRD/Issue/PR) | Not mapped — these are fleet artifacts, not analysis inputs. Recorded in `provenance` as reference links if useful. |

## Direction: push (PSI → arcana), not pull

Two options for the import path:

- **Push**: PSI Ship-gate approval writes a `topic-spec-seed.json` into
  `arcana/scripts/topics/` with the direct-mapped fields + `provenance`.
  arcana then grows the missing fields via a `grow_topic_spec` step.
- **Pull**: arcana reads `PSI/innovations/<approved>/` and constructs the
  topic-spec at run time.

**This contract proposes push.** Reasons:
- Decoupled — PSI does not need to know arcana's full topic-spec schema, only
  the seed shape (4 direct-mapped fields + provenance).
- arcana does not need to parse PSI's directory structure or gate state.
- The seed is a stable artifact arcana can version and review.
- Pull couples arcana to PSI's filesystem layout; push couples only via the
  seed schema.

## The seed schema (the shared contract)

```json
{
  "topic": "<Innovation title>",
  "resolution": "<Fleet Ask, reframed as a proposition>",
  "initial_hypothesis": "<Evidence, compressed>",
  "domains": ["<intellectual domain>", "..."],
  "provenance": {
    "source": "PSI",
    "ship_packet_path": "<path>",
    "ship_packet_hash": "<sha256>",
    "gate_status": "approved",
    "approval_reference": "<ref>",
    "imported_at": "<UTC ISO>"
  }
}
```

This is the minimal payload PSI pushes. arcana's `grow_topic_spec` step
fills `topic_id`, `definitions_required`, `constructive_mandate`,
`adversarial_mandate`, `applied_cases`, `arbiter_verdicts`, `claim_types`,
`prohibited_reasoning_failures`, `interpretations_to_evaluate`,
`semantic_framings_to_test`.

## Open questions this contract does NOT decide

- **Who authors the grown fields?** LLM-assisted draft + operator review, or
  human-authored? This is an arcana workflow decision, not a mapping decision.
- **Does the seed require operator approval on the arcana side too?** PSI's
  Ship gate is operator-approved; does arcana auto-accept the seed or run it
  through its own gate? Proposed: auto-accept the seed (it is already
  operator-approved on the PSI side), but the grown topic-spec is reviewed
  before the debate runs.
- **What if the Fleet Ask does not reframed cleanly as a proposition?** Some
  fleet asks are directives ("ship X") not propositions ("X is Y"). The
  mapping may need an intermediate reframing step. Flag for the first live
  import.
- **Versioning**: if a ship-packet is revised after import, does arcana
  re-import? The `provenance.ship_packet_hash` lets arcana detect drift;
  re-import is a manual decision.

## What this contract does NOT decide

- The `grow_topic_spec` implementation (LLM-assisted or human-authored).
- Whether PSI writes the seed automatically on Ship-gate approval or an
  operator triggers the push manually.
- Whether arcana's debate/paideia results flow back to PSI (a reverse join).
  That is a separate contract.
