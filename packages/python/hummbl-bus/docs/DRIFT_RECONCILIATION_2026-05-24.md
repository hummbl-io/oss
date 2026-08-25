# Bus Drift Reconciliation - 2026-05-24

## Verdict

`hummbl-bus` is not v1-ready as the canonical bus package yet.

The standalone package is healthy as an extraction candidate: local tests pass,
the package is stdlib-only at runtime, and the README correctly says extraction
is still in progress. The release blocker is drift from the live
`hummbl-governance/hummbl_governance/bus/` surface.

## Validation Run

Executed from `~/projects\PROJECTS\hummbl-bus`:

```bash
python -m pytest -q
```

Observed result:

```text
20 passed
```

## Live Module Comparison

Compared:

- Source: `~/projects\PROJECTS\hummbl-governance\hummbl_governance\bus`
- Target: `~/projects\PROJECTS\hummbl-bus\src\hummbl_bus`

| Module | Status | Founder lines | Standalone lines | Same SHA |
| --- | --- | ---: | ---: | --- |
| `__init__.py` | common | 62 | 64 | no |
| `bridge_client.py` | common | 240 | 108 | no |
| `bridge_server.py` | common | 542 | 218 | no |
| `bridge_tcp_client.py` | common | 62 | 62 | no |
| `bus_integration.py` | common | 638 | 393 | no |
| `bus_manager.py` | common | 500 | 476 | no |
| `bus_policy.py` | common | 158 | 158 | yes |
| `bus_security.py` | common | 475 | 475 | yes |
| `bus_utils.py` | founder-only | 38 | - | - |
| `bus_verifier.py` | common | 340 | 339 | no |
| `bus_writer.py` | common/absorbed split-outs | 132 | 1287 | no |
| `bus_writer_cli.py` | founder-only/absorbed | 181 | - | - |
| `bus_writer_core.py` | founder-only/absorbed | 1843 | - | - |
| `bus_writer_signing.py` | founder-only/absorbed | 265 | - | - |
| `mcp_server.py` | common | 310 | 307 | no |
| `message_signing.py` | common | 266 | 265 | no |
| `replay_ledger.py` | founder-only | 113 | - | - |
| `replay_worker.py` | founder-only | 78 | - | - |
| `secure_tsv.py` | common | 404 | 403 | no |
| `seed_import.py` | founder-only | 137 | - | - |
| `spool.py` | founder-only | 167 | - | - |

## Release Gates Before Canonical Promotion

1. Classify each founder-only module as `promote`, `absorbed`, `defer`, or
   `hummbl-governance-only`.
2. Diff the common modules semantically, not only by SHA. Most common files
   have drift, and several differ substantially in line count.
3. Add process-level concurrency tests for `bus_writer.py`, not just unit-level
   write coverage.
4. Decide whether replay and spool are part of the portable bus contract.
5. Only after the above, update README from "Extraction status: IN PROGRESS" to
   a canonical release posture.

## Current Recommendation

Keep `hummbl-bus` at `0.1.0` extraction status. Do not publish it as the
canonical v1 bus package until the hummbl-governance drift is classified and the
common modules have semantic parity tests.
