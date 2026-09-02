# AGENTS.md — hummbl-contracts

## Project

**hummbl-contracts** — Versioned contract schemas for HUMMBBL agent systems. 13 JSON schemas across 8 domains plus a stdlib-only JSON Schema validator (Draft 2020-12 subset).

## Scope

- In scope: Contract schemas (cognition, governance, foundry, idp, knowledge, lexicon, registry, eal), schema loader, schema validator, CLI (`hummbl-contracts list/validate/validate-inline`)
- Out of scope: Agent runtime, contract enforcement (that's `hummbl-governance`), contract negotiation protocols

## Setup

```bash
cd packages/python/hummbl-contracts
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Schemas are frozen at baseline tags; breaking changes require SemVer major bumps
- MIT OR Apache-2.0 license
