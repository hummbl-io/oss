# hummbl-heraldry

HUMMBL Procedural Heraldic Identity System — SHA-256 agent arms generator.

## Overview

Generates deterministic heraldic arms from agent names using SHA-256. Implements
the 7-layer identity system from the heraldry research synthesis:

| Layer | Content | Mutability |
|-------|---------|------------|
| 0 | Fleet/host heraldry (manually designed) | Fixed |
| 1 | Base arms (SHA-256(agent_name) → shield, tincture, division, ordinary, charge) | Immutable |
| 2 | Trust tier cadency mark | Changes with tier |
| 3 | Role badge (gear, scroll, lens, compass, wrench, star) | Changes with role |
| 4 | Host patch (Delta, Anvil, VPS, etc.) | Changes with deployment |
| 5 | Skill tabs (earned competencies) | Append-only |
| 6 | Runtime status (ephemeral: healthy/degraded/critical) | Real-time |

## Grammar

- 7 shield shapes (heater, kite, swiss, french, lozenge, oval, square)
- 9 tinctures (or, argent, gules, azure, sable, vert, purpure, ermine, vair)
- 10 divisions (solid, per pale, per fess, per bend, per chevron, per saltire, quarterly, per pall, gyronny)
- 8 ordinaries (none, pale, fess, bend, chevron, cross, saltire, chief)
- 30 charges (lion, eagle, mullet, crescent, fleur-de-lis, cogwheel, compass, etc.)
- 5 cadency marks (label, crescent, mullet, bordure compony, none)
- 6 role badges (star, gear, scroll, lens, compass, wrench)
- 5 host patches (delta, anvil, hummbl-vps, beachhead, slate)
- 9 ICS signal flags for bus message types

**Combination space:** 7 × 9 × 10 × 8 × 30 = 15,120 base combinations (without
tincture variations). With tincture assignments and contextual layers: 21,600+.

## Rule of Tincture

The generator enforces the heraldic rule of tincture: metal on color, color on
metal. Furs (ermine, vair) are exempt and can go on either. This guarantees
visual contrast at any scale.

## Usage

```bash
# Generate arms for a single agent
hummbl-heraldry generate devin --trust MEDIUM-HIGH --role coordinator --host delta

# Generate arms for all 11 fleet agents with SVGs
hummbl-heraldry generate-all --outdir /tmp/heraldry

# Show fleet arms
hummbl-heraldry fleet-arms --outdir /tmp/heraldry

# Generate ICS signal flags for bus message types
hummbl-heraldry ics-flags --outdir /tmp/heraldry/ics

# Print blazon for an agent
hummbl-heraldry blazon devin

# Show grammar statistics
hummbl-heraldry info
```

## Python API

```python
from hummbl_heraldry import ArmsGenerator

gen = ArmsGenerator()
arms = gen.generate("devin", trust_tier="MEDIUM-HIGH", role="coordinator", host="delta")
print(arms.blazon)

from hummbl_heraldry.svg import render_arms_svg
svg = render_arms_svg(arms)
```

## Fleet Arms

**HUMMBL LLC blazon:** *Sable, a pall reversed between in chief two mullets
Argent and in base a cogwheel Or*

- Sable (black) field — the void
- Pall reversed (inverted Y) — fleet structure: agents, hosts, bus
- Two mullets (stars) in chief — guidance
- Cogwheel in base — engineering

## License

MIT OR Apache-2.0
