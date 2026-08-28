# hummbl-axis

**Axis** — the ladder that selects which Atlas contradiction to act on. Closes the lattice-ladder-loop.

```
Atlas (lattice: observe) → Axis (ladder: select) → Human (act) → Atlas (loop: re-observe)
```

## What it does

Axis is not a platform. It is a script that:

1. Reads Atlas evidence cuts (markdown ledger + JSON inventory)
2. Diffs claimed state against observed state
3. Emits prioritized contradiction rows (P0-P3, by severity then confidence)
4. Routes to human (bus post or stdout)
5. Runs on cadence
6. Exits when stuck (3 unchanged cycles) or healthy (0 new for 3 cycles)

## Install

```bash
pip install hummbl-axis
```

## Usage

```bash
# One-shot: list contradictions from Atlas markdown
axis contradictions --atlas-dir ~/docs

# Full cycle: read Atlas, diff inventory, track state, report
axis scan --atlas-dir ~/docs \
  --inventory path/to/atlas-inventory.json \
  --observed-counts path/to/observed.json

# View cycle history
axis report
```

## Architecture

```
src/hummbl_axis/
  __init__.py        — package metadata
  contradiction.py   — Contradiction dataclass + CycleState (loop tracking)
  atlas_reader.py    — Markdown ledger parser + JSON inventory loader + count differ
  cli.py             — CLI entry point (scan, report, contradictions commands)
```

### Contradiction model

A Contradiction is the atomic unit Axis produces:
- `scope`: what surface the claim is about (e.g. "count:skills")
- `claim`: what the system says is true (e.g. "declared: 360")
- `observation`: what Atlas actually found (e.g. "observed: 547")
- `severity`: P0 (safety) → P3 (minor)
- `confidence`: 0.0-1.0 (from Atlas evidence grade)
- `volatility`: low/medium/high (how fast this changes)
- `id`: deterministic hash of scope+claim+observation (for cycle tracking)

### Cycle state and exit conditions

The loop exits when:
- **Stuck**: same contradiction persists 3 cycles unchanged → escalate to human, stop looping
- **Healthy**: 0 new contradictions for 3 consecutive cycles → reduce cadence

### Ladder rungs

Before Axis selects a contradiction to act on, it checks:
0. Already solved by a running loop? → use that loop
1. Does this need to exist at all? → skip (YAGNI)
2. Already in this codebase? → reuse
3. Stdlib does it? → use stdlib
4. Native platform feature? → use it
5. Already-installed dependency? → use it
6. Can it be one line? → one line
7. Minimum code that works → write it

## Testing

```bash
python -m pytest tests/ -v --cov=hummbl_axis
```

## License

Apache 2.0 — Copyright 2026 HUMMBL, LLC
