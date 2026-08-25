# Base120 Contract Unit Examples

This directory contains example contract units for testing and demonstration purposes.

## Valid Examples

### `valid-basic-contract.json`

A complete, valid contract unit demonstrating all required fields:
- Proper contract version and service name
- Well-formed artifact schema
- Valid failure graph with termination nodes
- Complete metadata with environment compatibility

**Usage:**
```bash
base120 validate-contract examples/contracts/valid-basic-contract.json
```

## Invalid Examples

These examples demonstrate common validation errors:

### `invalid-termination-edge.json`

**Error**: Termination nodes with outgoing edges

Demonstrates that nodes with `action: "terminate"` cannot have outgoing edges in the failure graph. This violates the semantic rule that termination nodes represent final states.

### `invalid-missing-metadata.json`

**Error**: Missing required field (metadata)

Demonstrates schema validation failure when a required field is missing from the contract unit.

## Testing

These examples are used by the test suite in `tests/test_contract.py` and `tests/test_cli.py`.

## Non-Normative Status

These examples are provided for illustration and testing purposes. They are **non-normative** and do not constitute part of the Base120 specification. Always refer to [spec-v1.0.0.md](../../docs/spec-v1.0.0.md) for authoritative guidance.
