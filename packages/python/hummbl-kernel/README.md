# hummbl-kernel

HUMMBL orchestration kernel — lightweight workflow execution with security and compliance enforcement.

## Overview

The Mission Mode Kernel is a lightweight orchestration layer that combines Conductor-style deterministic YAML workflow execution with security and compliance enforcement for SOC 2, ISO 27001, and PCI frameworks.

## Design Principles

### 1. Lightweight Architecture
- **Minimal Dependencies**: Stdlib-only Python (no third-party runtime dependencies)
- **Single Responsibility**: Kernel handles orchestration, security, and compliance only
- **No Heavy Runtime**: No built-in LLM inference or complex ML models
- **Fast Startup**: Sub-second initialization time
- **Low Memory Footprint**: < 100MB memory usage at idle

### 2. Security First
- **Capability Admission Policy**: All capabilities must be admitted before execution
- **Risk-Based Enforcement**: High-risk capabilities require explicit approval
- **Least Privilege**: Agents only get capabilities they need for their task
- **Audit Trail**: All security decisions logged to immutable audit trail
- **Secret Protection**: No secrets in logs or audit events

### 3. Compliance Native
- **Framework Mapping**: Native support for SOC 2, ISO 27001, PCI controls
- **Evidence Validation**: Automatic evidence quality and provenance validation
- **Chain of Custody**: Immutable evidence chain with cryptographic signatures
- **Audit Report Generation**: Automated compliance report generation
- **Checkpoint Enforcement**: Mandatory approval points for critical operations

### 4. Fleet Aware
- **Hybrid Deployment**: Seamless coordination between user-supplied compute nodes
- **Health Monitoring**: Continuous fleet health monitoring
- **Automatic Fallback**: Automatic task rerouting on node failure
- **Resource Awareness**: Task routing based on hardware capabilities

## Architecture

### Components

- **Workflow Orchestrator (Conductor)**: YAML workflow parsing and validation, step execution and state management
- **Capability Admission Policy**: Capability registration and validation, risk-based admission decisions
- **Security Enforcement Layer**: Grant generation and validation, capability escalation prevention
- **Compliance Enforcement Layer**: Control mapping and validation, evidence quality checks
- **Audit Trail System**: Immutable event logging, evidence chain of custody
- **Fleet Coordination Layer**: Health monitoring, task routing and fallback
- **Adapter Interface**: Adapter manifest validation, admitted call envelope

## Quick Start

```python
import asyncio
import json
from hummbl_kernel import MissionModeKernel

# Initialize kernel
kernel = MissionModeKernel()

# Define workflow
example_workflow = {
    "name": "example_workflow",
    "intent": "Collect and assess compliance evidence",
    "success_criteria": ["All controls documented"],
    "workflow": [
        {
            "step": "collect_evidence",
            "agent": "evidence_collector",
            "outputs": {"evidence_refs": ["ev_001", "ev_002"]},
        }
    ],
}


# Execute workflow
async def main():
    receipt = await kernel.execute_workflow(
        workflow_yaml=json.dumps(example_workflow),
        inputs={
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
        },
    )
    print(f"Mission completed: {receipt.receipt_id}")
    print(f"Audit trail: {receipt.audit_trail_ref}")


asyncio.run(main())
```

## Documentation

- `hummbl_kernel/audit/audit_trail_system.md` — Audit trail architecture
- `hummbl_kernel/audit/checkpoint_system.md` — Checkpoint enforcement
- `hummbl_kernel/adapters/adapter_interface.md` — Adapter interface specification
- `hummbl_kernel/workflows/schema.md` — Workflow YAML schema
- `hummbl_kernel/security/` — Capability admission policy

## License

Apache-2.0 — see `LICENSE`.
