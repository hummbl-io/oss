# Mission Mode Kernel Schema

## Conductor-Based Workflow Schema

Mission Mode uses Conductor-style YAML workflows for deterministic mission orchestration with compliance audit trails.

## Workflow Schema

```yaml
schema_version: "mission_mode.workflow.v1"
workflow_id: "mission_001"
name: "SOC 2 Audit Preparation Mission"
description: "Structured mission for SOC 2 audit readiness with audit trail generation"
version: "1.0.0"
compliance_framework: "SOC_2"
created_at: "2026-05-28T00:00:00Z"
created_by: "reubenbowlby"

# Mission definition
mission:
  intent: "Prepare organization for SOC 2 Type II audit"
  success_criteria:
    - "All SOC 2 controls documented with evidence"
    - "Audit trail generated for review period"
    - "Gap analysis completed"
  constraints:
    max_duration_hours: 40
    required_approvals: ["compliance_lead", "cto"]
    evidence_requirements: ["observation.summary", "artifact.ref"]

# Agents involved
agents:
  - id: "compliance_analyst"
    name: "Compliance Analyst Agent"
    model: "claude-sonnet-4.5"
    provider: "anthropic"
    role: "Analyzes controls and identifies gaps"
    
  - id: "evidence_collector"
    name: "Evidence Collector Agent"
    model: "claude-haiku-4.5"
    provider: "anthropic"
    role: "Gathers and validates evidence artifacts"
    
  - id: "audit_generator"
    name: "Audit Report Generator"
    model: "claude-sonnet-4.5"
    provider: "anthropic"
    role: "Generates final audit trail documentation"

# Workflow topology (deterministic routing)
workflow:
  # Step 1: Mission initialization
  - step: "initialize_mission"
    agent: "compliance_analyst"
    inputs:
      mission_context: "${mission}"
      organization_profile: "${inputs.organization_profile}"
    outputs:
      mission_plan: "mission_plan"
      control_inventory: "control_inventory"
    next: "assess_controls"
    
  # Step 2: Control assessment (parallel)
  - step: "assess_controls"
    agent: "compliance_analyst"
    inputs:
      control_inventory: "${initialize_mission.control_inventory}"
      soc2_framework: "${inputs.soc2_framework}"
    outputs:
      control_assessment: "control_assessment"
      gap_analysis: "gap_analysis"
    next: "collect_evidence"
    
  # Step 3: Evidence collection (parallel with control assessment)
  - step: "collect_evidence"
    agent: "evidence_collector"
    inputs:
      gap_analysis: "${assess_controls.gap_analysis}"
      evidence_sources: "${inputs.evidence_sources}"
    outputs:
      evidence_artifacts: "evidence_artifacts"
      validation_results: "validation_results"
    next: "generate_audit_trail"
    
  # Step 4: Audit trail generation
  - step: "generate_audit_trail"
    agent: "audit_generator"
    inputs:
      mission_plan: "${initialize_mission.mission_plan}"
      control_assessment: "${assess_controls.control_assessment}"
      evidence_artifacts: "${collect_evidence.evidence_artifacts}"
      validation_results: "${collect_evidence.validation_results}"
    outputs:
      audit_trail: "audit_trail"
      compliance_report: "compliance_report"
    next: "complete_mission"
    
  # Step 5: Mission completion
  - step: "complete_mission"
    agent: "system"
    inputs:
      audit_trail: "${generate_audit_trail.audit_trail}"
      compliance_report: "${generate_audit_trail.compliance_report}"
    outputs:
      mission_receipt: "mission_receipt"
      audit_receipt: "audit_receipt"
    next: null

# Fleet deployment configuration
fleet:
  primary_compute: "primary"  # Apple Silicon for inference
  gpu_compute: "gpu"        # NVIDIA GPU for GPU workloads
  fallback_compute: "gpu"    # Fallback if primary unavailable
  
  # Agent placement rules
  agent_placement:
    compliance_analyst: "primary"  # Heavy reasoning
    evidence_collector: "gpu"     # File operations
    audit_generator: "primary"    # Document generation

# Audit trail configuration
audit_trail:
  format: "jsonl"
  retention_days: 2555  # 7 years for SOC 2
  encryption: true
  immutability: true  # Append-only
  signature_required: true
  
  # Required audit events
  required_events:
    - "mission.initialized"
    - "control.assessed"
    - "evidence.collected"
    - "evidence.validated"
    - "gap.identified"
    - "audit.trail.generated"
    - "mission.completed"
    
  # Evidence quality standards
  evidence_quality:
    min_confidence: 0.8
    required_sources: ["observation", "artifact", "document"]
    validation_required: true

# Security constraints
security:
  capability_admission:
    enabled: true
    policy: "compliance_first"
    high_risk_capabilities:
      - "network.egress"
      - "system.write"
      - "credential.access"
      
  checkpoint_enforcement:
    enabled: true
    checkpoints:
      - "pre_evidence_collection"
      -pre_audit_generation"
      -pre_mission_completion"
      
  redaction:
    enabled: true
    secret_patterns:
      - "api_key"
      - "credential"
      - "token"
      - "password"
```

## Mission Execution Lifecycle

```
requested → admitted → planned → running → completed
                    ↓
                  denied
                    ↓
                  blocked
```

## Event Schema

```json
{
  "schema_version": "mission_mode.event.v1",
  "event_id": "evt_...",
  "workflow_id": "mission_001",
  "mission_id": "mission_001",
  "step_id": "step_001",
  "timestamp": "2026-05-28T00:00:00Z",
  "agent": "compliance_analyst",
  "event_type": "mission.initialized",
  "payload": {},
  "prev_event_id": null,
  "audit_metadata": {
    "compliance_framework": "SOC_2",
    "control_id": "CC1.1",
    "evidence_required": true
  }
}
```

## Receipt Schema

```json
{
  "schema_version": "mission_mode.receipt.v1",
  "receipt_id": "rcpt_...",
  "mission_id": "mission_001",
  "workflow_id": "mission_001",
  "final_status": "completed",
  "agent": "compliance_analyst",
  "started_at": "2026-05-28T00:00:00Z",
  "completed_at": "2026-05-28T10:00:00Z",
  "final_event_id": "evt_...",
  "audit_trail_ref": "audit_trail_001.jsonl",
  "compliance_report_ref": "compliance_report_001.pdf",
  "evidence_refs": ["ev_001", "ev_002"],
  "bus_receipt": {
    "posted": true,
    "message_ref": "bus_001"
  }
}
```

## Fleet Coordination

### primary (Primary Compute)
- **Role**: Primary inference engine for agent reasoning
- **Hardware**: Apple Silicon (12 cores, 48GB unified memory)
- **Models**: qwen3.5:9b, qwen3.5:4b for agent workloads
- **Services**: Ollama, OpenClaw gateways
- **Responsibility**: Heavy reasoning tasks, document generation

### gpu (GPU/Compliance)
- **Role**: GPU workloads and compliance operations
- **Hardware**: NVIDIA GPU (12GB VRAM, 270W cap)
- **Services**: Gitea, file operations, GPU inference
- **Responsibility**: File operations, evidence collection, GPU-intensive tasks

### Coordination Protocol
1. **Agent placement rules** defined in workflow YAML
2. **Fallback mechanism**: If primary unavailable, route to gpu
3. **Load balancing**: Distribute parallel steps across available compute
4. **Heartbeat monitoring**: Fleet health checks every 30 seconds
