# hummbl-garage

HUMMBL Garage — Agent Performance Index, livery presets, watch faces, and failure aesthetics.

## Overview

Implements the automotive + horology + kintsugi metaphors from the design synthesis:

- **Agent Performance Index (API):** 100-999 composite score with 6 sub-ratings
- **Livery presets:** Martini, Gulf, John Player Special, Rothmans, Marlboro, Castrol
- **Watch face status:** 4-layer display (analog hands, complications, dial finish, cockpit)
- **Failure states:** degraded (wabi-sabi), broken (kintsugi), dead (death screen)
- **Ruin gallery:** Append-only failure archive

## Agent Performance Index

```
Class D (100-299)  → Entry level
Class C (300-499)  → Standard
Class B (500-699)  → Competent
Class A (700-799)  → Advanced
Class S1 (800-899) → Superior
Class S2 (900-949) → Exceptional
Class R (950-999)  → Racing (theoretical max)
```

6 sub-ratings (0-10 each), weighted:
- Reasoning speed (20%)
- Tool-use accuracy (25%)
- Context efficiency (15%)
- Latency (10%)
- Safety/braking (20%)
- Composite (10%)

## Watch Face (4 layers)

| Layer | Content | Source |
|-------|---------|--------|
| 1 | Analog hand (color + position by state) | Runtime state |
| 2 | Complications (token budget, trust, task, errors) | Runtime + roster |
| 3 | Dial finish (flat/sunburst/guilloche/enamel/skeleton) | Trust tier |
| 4 | Fleet cockpit (PFD six-pack) | Fleet-wide |

Hand colors: blue=working, amber=waiting, red=blocked, green=completed, gray=idle

Dial finishes: flat (PROBATIONARY), sunburst (MEDIUM), guilloche (MEDIUM-HIGH), enamel (TRUSTED), skeleton (OWNER)

## Failure States

| State | Visual | Meaning |
|-------|--------|---------|
| Degraded | Wabi-sabi + glitch, amber | Partial loss, agent continues |
| Broken | Kintsugi gold seam | Halted, repair underway |
| Dead | Death screen "AGENT LOST" | Terminated, successor spawned |

## Usage

```bash
# Show garage stats
hummbl-garage info

# List livery presets
hummbl-garage liveries

# Render livery swatches as SVG
hummbl-garage liveries --outdir /tmp/garage

# Render a watch face
hummbl-garage watch working --trust TRUSTED --task "building" --tokens 75 --errors 0 --svg watch.svg

# Show failure state
hummbl-garage failure broken --svg broken.svg

# Classify an API score
hummbl-garage api 750

# Calculate API from sub-ratings
hummbl-garage api-score 8.5 9.0 7.5 8.0 9.5 8.0
```

## Python API

```python
from hummbl_garage import Garage, AgentPerformanceIndex, WatchFace, RuinGallery

g = Garage()

# Get livery preset
livery = g.find_livery("gulf")
print(livery.primary, livery.secondary)

# Calculate API
api = AgentPerformanceIndex(reasoning_speed=8.5, tool_accuracy=9.0, ...)
print(api.api_score, api.api_class)  # e.g. 842, "S1"

# Watch face
face = WatchFace(state="working", trust_tier="TRUSTED", token_budget_pct=72.5)
print(face.hand_color, face.dial_finish)

# Ruin gallery
gallery = RuinGallery()
gallery.record("gemini", "broken", "2026-09-02T12:00:00Z", "Context overflow")
```

## License

MIT OR Apache-2.0
