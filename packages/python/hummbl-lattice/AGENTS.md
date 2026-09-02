# AGENTS.md — hummbl-lattice

## Project

**hummbl-lattice** — Domain-specific reasoning operator lattices: validation, rating, and cohort tooling for the Domain120 framework. Python (stdlib-only), published to PyPI as `hummbl-lattice`.

## Scope

- In scope: Lattice data models (Lattice, LatticeOperator, CompositionMatrix), lattice validator (11 ratification checks), Fleiss' kappa calculator, CLI (`hummbl-lattice validate/kappa/info`), 6-family taxonomy (P/IN/CO/DE/RE/SY)
- Out of scope: Base120 canonical registry (lives in `base120` package), governance primitives (lives in `hummbl-governance`), runtime agent execution

## Setup

```bash
cd packages/python/hummbl-lattice
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Each lattice operator has: code, name, family, definition, base120_ancestor, status
- Canonical serialization: JSON with SHA-256 hash (sort_keys=True, ensure_ascii=False)
- MIT OR Apache-2.0 license
