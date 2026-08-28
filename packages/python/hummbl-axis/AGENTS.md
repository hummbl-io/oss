# AGENTS.md — hummbl-axis

## Project

**hummbl-axis** — The ladder that selects which Atlas contradiction to act on. Closes the lattice-ladder-loop: Atlas (observe) → Axis (select) → Human (act) → Atlas (re-observe).

## Scope

- In scope: Contradiction extraction from Atlas evidence cuts, claimed-vs-observed count diffing, severity prioritization (P0-P3), cycle state tracking, loop exit conditions, human routing, CLI (`axis scan/report/contradictions`)
- Out of scope: Atlas evidence collection, acting on contradictions, fleet governance primitives

## Setup

```bash
cd packages/python/hummbl-axis
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Contradiction model: scope, claim, observation, severity, confidence, volatility, deterministic id
- Loop exits when stuck (3 unchanged cycles) or healthy (0 new for 3 cycles)
- MIT OR Apache-2.0 license
