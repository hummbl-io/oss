# AGENTS.md — hummbl-intel

## Project

**hummbl-intel** — INT taxonomy framework: intelligence discipline categorization (DoD/ODNI canonical), source reliability grading, collection posture, and all-source fusion for agent systems.

## Scope

- In scope: INT enum (SIGINT, HUMINT, OSINT, GEOINT, MASINT, FININT, TECHINT, IMINT, ALL-SOURCE), source grading (A-F / 1-6), collection posture (GREEN/YELLOW/RED), all-source fusion, INT manager role definitions
- Out of scope: Actual intelligence collection (that's the agents' job), governance enforcement, bus protocol

## Setup

```bash
cd packages/python/hummbl-intel
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Source grading: reliability (A-F) x credibility (1-6), per NATO intelligence doctrine
- MIT OR Apache-2.0 license
