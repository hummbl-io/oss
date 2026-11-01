# hummbl-mcp-governance

MCP servers exposing HUMMBL governance primitives — 7 servers, 32+ JSON-RPC tools.

## Servers (7)

| Server | Entry point | Tools | Wraps |
|--------|-------------|-------|-------|
| **Governance** | `hummbl-governance-mcp` | 9 | KillSwitch, CircuitBreaker, CostGovernor, AuditLog, ComplianceMapper, HealthProbe |
| **Compliance** | `hummbl-compliance-mcp` | 5 | NIST AI RMF, SOC2, ISO crosswalk, STRIDE, evidence export |
| **Sandbox** | `hummbl-sandbox-mcp` | 5 | CapabilityFence, OutputValidator sandbox |
| **Identity** | `hummbl-identity-mcp` | 10 | AgentRegistry, DelegationTokenManager, LamportClock |
| **Agent Monitor** | `hummbl-agent-monitor-mcp` | 12 | BehaviorMonitor, ConvergenceDetector, GovernanceLifecycle, EvolutionLineage |

Unknown agents are denied by `lifecycle_authorize` (`agent:unknown`). Register
them with `lifecycle_register_agent`, or preload a JSON roster via
`MONITOR_REGISTRY`. `allow_unregistered_agents` is not enabled on this path.
| **Reasoning** | `hummbl-reasoning-mcp` | — | ReasoningEngine, SchemaValidator, ContractNetManager |
| **Physical AI** | `hummbl-physical-mcp` | 6 | KinematicGovernor, pHRISafetyMonitor |

## Install from source

From the root of a checkout of
[hummbl-io/oss](https://github.com/hummbl-io/oss):

```bash
python -m pip install ./packages/python/hummbl-mcp-governance
```

## Run

```bash
# Any of the 7 entry points
hummbl-governance-mcp
hummbl-compliance-mcp
hummbl-sandbox-mcp
hummbl-identity-mcp
hummbl-agent-monitor-mcp
hummbl-reasoning-mcp
hummbl-physical-mcp
```

## Dependencies

- `hummbl-governance>=1.1.0` (from PyPI)

## License

Apache-2.0

Kill-switch release is not an MCP tool. Former direct calls are rejected, and
engagement cannot weaken an existing halt. Use the separately protected
[governance operator release path](../hummbl-governance/docs/OPERATOR_RELEASE.md).
Engagement also fails closed when an installed governance core lacks operator
release authorization support. Adopt the fixed core and wrapper together.
