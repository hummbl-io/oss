# hummbl-contracts

Versioned contract schemas for HUMMBL agent systems. The canonical source of truth for data shapes across the ecosystem.

[![Runtime Deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen)]()

**Tier:** 0 — Absolute Stdlib Only. Zero third-party runtime dependencies. The JSON Schema validator is implemented with Python stdlib only.

## What This Is

JSON schemas that define the data contracts between agents, services, and governance systems. Contracts are frozen at baseline tags and breaking changes require SemVer major bumps.

## Contract Domains

- **CLP (Cognitive Ledger Protocol)**: ledger_entry, shared_state schemas
- **Governance**: delegation_token, governance_event, audit_log schemas
- **Foundry**: action_envelope, state_snapshot, telemetry_event schemas
- **IDP**: intent-driven project contract schema
- **Knowledge**: memory, context schemas
- **Lexicon**: acronym schema
- **Registry**: agent registry schema
- **EAL**: validation report schema

## Frozen Baselines

| Tag | Date | Scope |
|-----|------|-------|
| `fm-contracts-v0.1` | 2026-02 | Initial baseline |

Breaking changes require:
1. SemVer major bump
2. New baseline tag (`fm-contracts-vX.Y`)
3. Migration path documented

## Structure

```
schemas/
  cognition/           # Cognitive Ledger Protocol schemas
  governance/          # Governance schemas
  foundry/             # Foundry action/state/telemetry schemas
  idp/                 # Intent-driven project contract schema
  knowledge/           # Memory/context schemas
  lexicon/             # Lexicon schemas
  registry/            # Agent registry schemas
  eal/                 # EAL validation report schema
```

## Installation

```bash
pip install hummbl-contracts
```

## Usage

```python
from hummbl_contracts import validate, validate_entry_dict, load_schema, list_schemas

# List all available schemas
print(list_schemas())

# Load a schema
schema = load_schema("cognition/clp.ledger_entry")

# Validate a dict against a schema
errors = validate(my_data, schema)
if errors:
    print(f"Validation failed: {errors}")

# Validate a ledger entry (uses default CLP schema)
is_valid, errors = validate_entry_dict(my_entry)
```

## CLI

```bash
# List all available schemas
python -m hummbl_contracts list

# Validate a data file against a named schema
python -m hummbl_contracts validate cognition/clp.ledger_entry entry.json

# Validate inline JSON against a named schema
python -m hummbl_contracts validate-inline governance/governor_decision_record '{"...": "..."}'
```

## License

Apache 2.0
