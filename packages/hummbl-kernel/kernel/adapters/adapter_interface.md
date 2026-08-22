# Mission Mode Kernel Adapter Interface

## Adapter Manifest Schema

```json
{
  "schema_version": "mission_mode.adapter_manifest.v1",
  "adapter_id": "compliance-evidence-collector",
  "name": "Compliance Evidence Collector Adapter",
  "version": "1.0.0",
  "isolation_mode": "process",
  "persistence_mode": "kernel-audit",
  "supported_capabilities": [
    {
      "capability": "evidence.collect",
      "actions": ["read", "validate"],
      "risk_class": "low",
      "evidence_quality": "artifact",
      "compliance_frameworks": ["SOC_2", "ISO_27001", "PCI"]
    },
    {
      "capability": "document.generate",
      "actions": ["create", "update"],
      "risk_class": "medium",
      "evidence_quality": "synthetic",
      "compliance_frameworks": ["SOC_2", "ISO_27001", "PCI"]
    }
  ],
  "fleet_placement": {
    "preferred": "anvil",
    "fallback": "nodezero",
    "gpu_required": false
  },
  "trace_support": {
    "otel": true,
    "external_trace_refs": true
  },
  "limits": {
    "max_runtime_seconds": 300,
    "max_output_bytes": 1048576,
    "max_evidence_size_mb": 100
  }
}
```

## Admitted Call Envelope

```json
{
  "schema_version": "mission_mode.admitted_call.v1",
  "mission_id": "mission_001",
  "workflow_id": "mission_001",
  "step_id": "step_003",
  "grant_id": "grant_001",
  "adapter_id": "compliance-evidence-collector",
  "capability": "evidence.collect",
  "action": "read",
  "target": "s3://evidence-bucket/control-cc1.1",
  "arguments": {
    "control_id": "CC1.1",
    "evidence_types": ["policy", "procedure", "artifact"],
    "validation_required": true
  },
  "idempotency_key": "idem_001",
  "timeout_seconds": 300,
  "evidence_requirements": ["observation.summary", "artifact.ref", "validation.hash"],
  "compliance_context": {
    "framework": "SOC_2",
    "control_id": "CC1.1",
    "audit_period_start": "2025-01-01",
    "audit_period_end": "2025-12-31"
  }
}
```

## Observation Envelope

```json
{
  "schema_version": "mission_mode.observation.v1",
  "observation_id": "obs_001",
  "mission_id": "mission_001",
  "workflow_id": "mission_001",
  "step_id": "step_003",
  "grant_id": "grant_001",
  "adapter_id": "compliance-evidence-collector",
  "status": "completed",
  "summary": "Collected 3 evidence artifacts for control CC1.1: access policy (2024-03-15), procedure document (2024-06-20), and system configuration export (2024-12-01)",
  "outputs": {
    "evidence_count": 3,
    "validation_status": "passed",
    "evidence_types": ["policy", "procedure", "artifact"],
    "control_coverage": "complete"
  },
  "evidence_refs": [
    {
      "ref_id": "ev_001",
      "type": "policy",
      "location": "s3://evidence-bucket/control-cc1.1/access-policy.pdf",
      "hash": "sha256:abc123...",
      "collected_at": "2026-05-28T10:00:00Z"
    },
    {
      "ref_id": "ev_002",
      "type": "procedure",
      "location": "s3://evidence-bucket/control-cc1.1/procedure.docx",
      "hash": "sha256:def456...",
      "collected_at": "2026-05-28T10:05:00Z"
    },
    {
      "ref_id": "ev_003",
      "type": "artifact",
      "location": "s3://evidence-bucket/control-cc1.1/config-export.json",
      "hash": "sha256:ghi789...",
      "collected_at": "2026-05-28T10:10:00Z"
    }
  ],
  "trace_refs": [],
  "redaction": {
    "contains_secret": false,
    "redacted_fields": []
  },
  "compliance_metadata": {
    "framework": "SOC_2",
    "control_id": "CC1.1",
    "evidence_quality": "high",
    "audit_ready": true
  }
}
```

## Failure Envelope

```json
{
  "schema_version": "mission_mode.adapter_failure.v1",
  "mission_id": "mission_001",
  "workflow_id": "mission_001",
  "step_id": "step_003",
  "grant_id": "grant_001",
  "adapter_id": "compliance-evidence-collector",
  "error_class": "evidence.validation_failed",
  "message": "Evidence artifact failed validation: hash mismatch for policy document",
  "retryable": true,
  "safe_to_replay": true,
  "evidence_refs": [],
  "compliance_metadata": {
    "framework": "SOC_2",
    "control_id": "CC1.1",
    "validation_failure_reason": "hash_mismatch"
  }
}
```

## Adapter Rules

1. **Grant Validation**: Adapter must reject calls without valid grant_id
2. **Adapter Matching**: Adapter must reject calls where adapter_id does not match manifest
3. **No Capability Escalation**: Adapter must not request additional capabilities by itself
4. **Single Output**: Adapter must return one observation or one failure for each admitted call
5. **Idempotency Preservation**: Adapter must preserve idempotency_key in all output
6. **Secret Protection**: Adapter must not include secrets in observation summary or evidence refs
7. **Compliance Context**: Adapter must preserve compliance_context in all output
8. **Evidence Quality**: Adapter must validate evidence quality against compliance requirements
9. **Audit Trail**: Adapter must log all operations to audit trail
10. **Fleet Awareness**: Adapter must respect fleet placement rules (preferred/fallback compute)

## First Adapter: noop-local

Following founder-mode agent-kernel-v0 spec, the first adapter should be `noop-local`:

**Purpose**:
- Validate schemas
- Validate state transitions
- Validate replay and idempotency
- Validate fleet coordination
- Avoid approving any external runtime dependency before kernel contract is stable

**Manifest**:
```json
{
  "schema_version": "mission_mode.adapter_manifest.v1",
  "adapter_id": "noop-local",
  "name": "No-op Local Adapter",
  "version": "0.1.0",
  "isolation_mode": "none",
  "persistence_mode": "kernel-only",
  "supported_capabilities": [
    {
      "capability": "noop.echo",
      "actions": ["read"],
      "risk_class": "low",
      "evidence_quality": "synthetic",
      "compliance_frameworks": []
    }
  ],
  "fleet_placement": {
    "preferred": "local",
    "fallback": "local",
    "gpu_required": false
  },
  "trace_support": {
    "otel": false,
    "external_trace_refs": false
  },
  "limits": {
    "max_runtime_seconds": 30,
    "max_output_bytes": 65536,
    "max_evidence_size_mb": 0
  }
}
```

## Real Adapter Readiness Checklist

Before implementing a real adapter:

1. **License reviewed** - Commercial use allowed?
2. **Install path reviewed** - Safe installation location?
3. **Top-level architecture** - Entry point understood?
4. **Secret handling** - How are credentials managed?
5. **Sandbox/isolation** - What isolation mode is required?
6. **Test mode** - Can it run without external side effects?
7. **Compliance framework support** - Does it support SOC 2/ISO 27001/PCI evidence requirements?
8. **Fleet compatibility** - Can it run on both nodezero and Anvil?
9. **Audit trail integration** - Can it log to Mission Mode audit trail?
10. **Evidence validation** - Can it validate evidence quality and provenance?