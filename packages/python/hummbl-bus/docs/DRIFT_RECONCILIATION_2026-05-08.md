# Bus Drift Reconciliation — 2026-05-08

## Comparison

Source repo compared:

- `hummbl-governance/bus/` in `hummbl-io/hummbl-governance`

Target repo:

- `hummbl-bus`

This repo now contains the portable coordination-bus surface with a conventional
`src/hummbl_bus/` package layout and core test coverage.

## Promoted Modules

These hummbl-governance bus modules are represented here in the standalone package:

- `bus_writer.py`
- `bus_verifier.py`
- `bus_policy.py`
- `bus_security.py`
- `message_signing.py`
- `secure_tsv.py`
- `bridge_client.py`
- `bridge_server.py`
- `bridge_tcp_client.py`
- `bus_integration.py`
- `mcp_server.py`

## Absorbed Helpers

These hummbl-governance split-outs no longer need separate top-level modules in the
standalone repo because their responsibilities are absorbed into the main
package:

- `bus_writer_cli.py` -> `bus_writer.main`
- `bus_writer_core.py` -> `bus_writer.py`
- `bus_writer_signing.py` -> `message_signing.py` and the signing paths in
  `bus_writer.py`

## Still hummbl-governance Adjacent

These items are present in hummbl-governance but are not yet promoted here:

- `spool.py`
- `replay_worker.py`
- `replay_ledger.py`
- `seed_import.py`
- `bus_utils.py`
- `BRIDGE_SETUP.md`

## Classification

- `promote` means the module is part of the portable bus repo.
- `absorbed` means the split-out helper is already represented in the portable
  package and does not need a separate file.
- `defer` means the capability is useful but not yet justified as a portable
  standalone surface.
- `hummbl-governance-only` means keep the capability in hummbl-governance until a real
  consumer for the standalone repo appears.

## Current Recommendation

Keep `hummbl-bus` narrow for now. The missing modules mostly look like
orchestration or replay machinery, not the core transport and verification
surface that the standalone repo is supposed to own.
