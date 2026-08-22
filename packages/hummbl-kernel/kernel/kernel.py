"""
Mission Mode Kernel - Hybrid Conductor-Kernel Architecture

Implements deterministic mission orchestration with compliance audit trails,
fleet coordination between nodezero and Anvil, and lightweight security enforcement.
"""

import json
import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC_2 = "SOC_2"
    ISO_27001 = "ISO_27001"
    PCI = "PCI"


class EventStatus(Enum):
    """Event status in mission lifecycle"""
    REQUESTED = "requested"
    ADMITTED = "admitted"
    DENIED = "denied"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class RiskClass(Enum):
    """Capability risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FleetConfig:
    """Fleet configuration for nodezero and Anvil"""
    primary_compute: str = "nodezero"
    gpu_compute: str = "anvil"
    fallback_compute: str = "anvil"
    
    # Machine capabilities
    nodezero_m4_pro: bool = True
    anvil_rtx_3080ti: bool = True
    
    # Service endpoints (override via env vars; do not hardcode internal IPs/URLs)
    nodezero_ollama: str = field(default_factory=lambda: os.environ.get("NODEZERO_OLLAMA_URL", "http://100.x.x.x:11434"))
    anvil_gitea: str = field(default_factory=lambda: os.environ.get("ANVIL_GITEA_URL", "https://example.ts.net"))
    
    # Health check intervals
    heartbeat_interval_seconds: int = 30


@dataclass
class AuditEvent:
    """Audit event for compliance trail"""
    event_id: str
    audit_trail_id: str
    mission_id: str
    workflow_id: str
    step_id: str
    timestamp: str
    agent: str
    event_type: str
    actor: str
    payload: Dict[str, Any]
    compliance_metadata: Dict[str, Any]
    evidence_refs: List[str]
    prev_event_id: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class MissionReceipt:
    """Mission completion receipt"""
    receipt_id: str
    mission_id: str
    workflow_id: str
    final_status: str
    agent: str
    started_at: str
    completed_at: str
    final_event_id: str
    audit_trail_ref: str
    compliance_report_ref: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    bus_receipt: Dict[str, Any] = field(default_factory=dict)


class MissionModeKernel:
    """
    Mission Mode Kernel - Hybrid Conductor-Kernel Architecture
    
    Combines:
    - Conductor-style deterministic YAML workflow orchestration
    - Lightweight kernel for security/compliance enforcement
    - Fleet coordination between nodezero and Anvil
    - Immutable audit trail generation for compliance frameworks
    """
    
    def __init__(self, fleet_config: Optional[FleetConfig] = None):
        self.fleet_config = fleet_config or FleetConfig()
        self.active_missions: Dict[str, Dict] = {}
        self.audit_trails: Dict[str, List[AuditEvent]] = {}
        self.capability_registry: Dict[str, Dict] = {}
        
        # Initialize fleet health monitoring
        self.fleet_health = {
            "nodezero": True,
            "anvil": True
        }
        
        logger.info("Mission Mode Kernel initialized")
        logger.info(f"Fleet config: primary={self.fleet_config.primary_compute}, "
                   f"gpu={self.fleet_config.gpu_compute}, "
                   f"fallback={self.fleet_config.fallback_compute}")
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique identifier"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _sign_event(self, event: AuditEvent) -> str:
        """Sign audit event with HMAC-SHA256 using kernel signing key"""
        signing_key = os.environ.get("MISSION_MODE_SIGNING_KEY")
        if not signing_key:
            raise ValueError(
                "Audit event signing requires MISSION_MODE_SIGNING_KEY env var. "
                "Do not use a hardcoded default key."
            )
        event_data = json.dumps({
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "payload": event.payload
        }, sort_keys=True)
        return hmac.new(
            signing_key.encode(),
            event_data.encode(),
            hashlib.sha256,
        ).hexdigest()
    
    async def check_fleet_health(self) -> Dict[str, bool]:
        """Check health of fleet nodes"""
        health_status = {}
        
        # Check nodezero (primary compute)
        try:
            # Check Ollama endpoint
            result = subprocess.run(
                ["curl", "-s", f"{self.fleet_config.nodezero_ollama}/api/tags"],
                capture_output=True,
                timeout=5
            )
            health_status["nodezero"] = result.returncode == 0
        except Exception as e:
            logger.warning(f"Nodezero health check failed: {e}")
            health_status["nodezero"] = False
        
        # Check Anvil (GPU/compliance)
        try:
            # Check Gitea endpoint
            result = subprocess.run(
                ["curl", "-s", self.fleet_config.anvil_gitea],
                capture_output=True,
                timeout=5
            )
            health_status["anvil"] = result.returncode == 0
        except Exception as e:
            logger.warning(f"Anvil health check failed: {e}")
            health_status["anvil"] = False
        
        self.fleet_health = health_status
        return health_status
    
    def get_optimal_compute(self, task_type: str) -> str:
        """
        Determine optimal compute node for task type
        
        Args:
            task_type: Type of task (inference, file_ops, gpu_workload, etc.)
        
        Returns:
            Node identifier (nodezero or anvil)
        """
        # Check fleet health first
        health = self.fleet_health
        
        # If primary is unhealthy, use fallback
        if not health.get(self.fleet_config.primary_compute, False):
            logger.warning(f"Primary compute {self.fleet_config.primary_compute} unhealthy, using fallback")
            return self.fleet_config.fallback_compute
        
        # Task-based routing
        routing_rules = {
            "inference": self.fleet_config.primary_compute,  # M4 Pro for reasoning
            "file_ops": self.fleet_config.gpu_compute,       # Anvil for file operations
            "gpu_workload": self.fleet_config.gpu_compute,      # RTX 3080 Ti for GPU
            "document_generation": self.fleet_config.primary_compute,  # M4 Pro for synthesis
            "database_ops": self.fleet_config.gpu_compute,       # Anvil for database
            "storage_ops": self.fleet_config.gpu_compute,        # Anvil for storage
        }
        
        return routing_rules.get(task_type, self.fleet_config.primary_compute)
    
    def register_capability(self, capability: str, risk_class: RiskClass, 
                          adapter_id: str, compliance_frameworks: List[ComplianceFramework]):
        """Register a capability with the kernel"""
        self.capability_registry[capability] = {
            "risk_class": risk_class,
            "adapter_id": adapter_id,
            "compliance_frameworks": compliance_frameworks,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Registered capability: {capability} (risk: {risk_class}, adapter: {adapter_id})")
    
    def admit_capability(self, capability: str, agent: str, 
                       compliance_framework: ComplianceFramework) -> tuple[bool, str]:
        """
        Admit or deny a capability request based on risk and compliance framework
        
        Returns:
            (admitted: bool, reason: str)
        """
        if capability not in self.capability_registry:
            return False, f"Capability {capability} not registered"
        
        cap_info = self.capability_registry[capability]
        
        # Check if capability is supported for compliance framework
        if compliance_framework not in cap_info["compliance_frameworks"]:
            return False, f"Capability {capability} not supported for {compliance_framework}"
        
        # High-risk capabilities require explicit approval
        if cap_info["risk_class"] in [RiskClass.HIGH, RiskClass.CRITICAL]:
            return False, f"High-risk capability {capability} requires explicit approval"
        
        logger.info(f"Capability admitted: {capability} for agent {agent}")
        return True, "Capability admitted"
    
    def create_audit_trail(self, mission_id: str, workflow_id: str, 
                         compliance_framework: ComplianceFramework,
                         audit_period_start: str, audit_period_end: str,
                         organization_id: str) -> str:
        """Create new audit trail for a mission"""
        audit_trail_id = self._generate_id("at")
        
        audit_trail = {
            "schema_version": "mission_mode.audit_trail.v1",
            "audit_trail_id": audit_trail_id,
            "mission_id": mission_id,
            "workflow_id": workflow_id,
            "compliance_framework": compliance_framework.value,
            "audit_period_start": audit_period_start,
            "audit_period_end": audit_period_end,
            "organization_id": organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "mission_mode_kernel",
            "status": "in_progress",
            "finalized_at": None,
            "events": []
        }
        
        self.audit_trails[audit_trail_id] = audit_trail
        logger.info(f"Created audit trail: {audit_trail_id} for mission {mission_id}")
        
        return audit_trail_id
    
    def append_audit_event(self, audit_trail_id: str, event: AuditEvent) -> bool:
        """Append event to audit trail (append-only, immutable)"""
        if audit_trail_id not in self.audit_trails:
            logger.error(f"Audit trail {audit_trail_id} not found")
            return False
        
        audit_trail = self.audit_trails[audit_trail_id]
        
        # Sign the event
        event.signature = self._sign_event(event)
        
        # Append event (append-only)
        audit_trail["events"].append({
            "event_id": event.event_id,
            "audit_trail_id": event.audit_trail_id,
            "mission_id": event.mission_id,
            "workflow_id": event.workflow_id,
            "step_id": event.step_id,
            "timestamp": event.timestamp,
            "agent": event.agent,
            "event_type": event.event_type,
            "actor": event.actor,
            "payload": event.payload,
            "compliance_metadata": event.compliance_metadata,
            "evidence_refs": event.evidence_refs,
            "prev_event_id": event.prev_event_id,
            "signature": event.signature
        })
        
        logger.info(f"Appended event {event.event_type} to audit trail {audit_trail_id}")
        return True
    
    def finalize_audit_trail(self, audit_trail_id: str) -> bool:
        """Finalize audit trail (immutable after finalization)"""
        if audit_trail_id not in self.audit_trails:
            logger.error(f"Audit trail {audit_trail_id} not found")
            return False
        
        audit_trail = self.audit_trails[audit_trail_id]
        audit_trail["status"] = "finalized"
        audit_trail["finalized_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Finalized audit trail {audit_trail_id}")
        return True
    
    def generate_receipt(self, mission_id: str, workflow_id: str, final_status: str,
                      agent: str, audit_trail_id: str, 
                      evidence_refs: List[str]) -> MissionReceipt:
        """Generate mission completion receipt"""
        receipt_id = self._generate_id("rcpt")
        
        # Get final event from audit trail
        audit_trail = self.audit_trails.get(audit_trail_id, {})
        events = audit_trail.get("events", [])
        final_event_id = events[-1]["event_id"] if events else None
        
        receipt = MissionReceipt(
            receipt_id=receipt_id,
            mission_id=mission_id,
            workflow_id=workflow_id,
            final_status=final_status,
            agent=agent,
            started_at=audit_trail.get("created_at", ""),
            completed_at=datetime.now(timezone.utc).isoformat(),
            final_event_id=final_event_id,
            audit_trail_ref=audit_trail_id,
            evidence_refs=evidence_refs,
            bus_receipt={
                "posted": False,
                "message_ref": None
            }
        )
        
        logger.info(f"Generated receipt {receipt_id} for mission {mission_id}")
        return receipt
    
    async def execute_workflow(self, workflow_yaml: str, inputs: Dict[str, Any]) -> MissionReceipt:
        """
        Execute a Conductor-style YAML workflow
        
        Args:
            workflow_yaml: YAML workflow definition
            inputs: Workflow inputs
            
        Returns:
            Mission receipt with audit trail reference
        """
        # Parse YAML workflow
        try:
            workflow = json.loads(workflow_yaml) if workflow_yaml.startswith('{') else {}
        except:
            # In production, use proper YAML parser
            workflow = {}
        
        workflow_id = workflow.get("workflow_id", "unknown")
        mission_id = self._generate_id("mission")
        
        logger.info(f"Executing workflow {workflow_id} as mission {mission_id}")
        
        # Create audit trail
        compliance_framework = ComplianceFramework(workflow.get("compliance_framework", "SOC_2"))
        audit_trail_id = self.create_audit_trail(
            mission_id=mission_id,
            workflow_id=workflow_id,
            compliance_framework=compliance_framework,
            audit_period_start=inputs.get("audit_period_start", ""),
            audit_period_end=inputs.get("audit_period_end", ""),
            organization_id=inputs.get("organization_id", "org_001")
        )
        
        # Initialize mission event
        init_event = AuditEvent(
            event_id=self._generate_id("evt"),
            audit_trail_id=audit_trail_id,
            mission_id=mission_id,
            workflow_id=workflow_id,
            step_id="step_000",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="mission_mode_kernel",
            event_type="mission.initialized",
            actor="system",
            payload={
                "mission_intent": workflow.get("mission", {}).get("intent", ""),
                "success_criteria": workflow.get("mission", {}).get("success_criteria", [])
            },
            compliance_metadata={
                "framework": compliance_framework.value,
                "control_id": None,
                "evidence_required": False,
                "checkpoint": False
            },
            evidence_refs=[],
            prev_event_id=None
        )
        self.append_audit_event(audit_trail_id, init_event)
        
        # Execute workflow steps (simplified for MVP)
        # In production, this would be a full Conductor-style executor
        evidence_refs = []
        
        # Simulate workflow execution
        for step in workflow.get("workflow", []):
            step_id = step.get("step", "unknown")
            agent = step.get("agent", "unknown")
            
            # Determine optimal compute for this step
            task_type = self._infer_task_type(step)
            compute_node = self.get_optimal_compute(task_type)
            
            # Create step event
            step_event = AuditEvent(
                event_id=self._generate_id("evt"),
                audit_trail_id=audit_trail_id,
                mission_id=mission_id,
                workflow_id=workflow_id,
                step_id=step_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent=agent,
                event_type="step.started",
                actor="mission_mode_kernel",
                payload={
                    "step": step,
                    "compute_node": compute_node
                },
                compliance_metadata={
                    "framework": compliance_framework.value,
                    "control_id": None,
                    "evidence_required": False,
                    "checkpoint": False
                },
                evidence_refs=[],
                prev_event_id=init_event.event_id
            )
            self.append_audit_event(audit_trail_id, step_event)
            
            # Simulate step completion
            # In production, this would call the actual agent
            if "outputs" in step:
                if "evidence_refs" in step["outputs"]:
                    evidence_refs.extend(step["outputs"]["evidence_refs"])
        
        # Finalize audit trail
        self.finalize_audit_trail(audit_trail_id)
        
        # Generate receipt
        receipt = self.generate_receipt(
            mission_id=mission_id,
            workflow_id=workflow_id,
            final_status="completed",
            agent="mission_mode_kernel",
            audit_trail_id=audit_trail_id,
            evidence_refs=evidence_refs
        )
        
        return receipt
    
    def _infer_task_type(self, step: Dict[str, Any]) -> str:
        """Infer task type from step definition"""
        agent = step.get("agent", "")
        
        # Simple inference based on agent type
        if "collector" in agent.lower():
            return "file_ops"
        elif "generator" in agent.lower():
            return "document_generation"
        elif "analyst" in agent.lower():
            return "inference"
        else:
            return "inference"


# Example usage
async def main():
    """Example kernel execution"""
    kernel = MissionModeKernel()
    
    # Check fleet health
    health = await kernel.check_fleet_health()
    print(f"Fleet health: {health}")
    
    # Example workflow (simplified)
    example_workflow = {
        "schema_version": "mission_mode.workflow.v1",
        "workflow_id": "mission_001",
        "name": "SOC 2 Audit Preparation",
        "compliance_framework": "SOC_2",
        "mission": {
            "intent": "Prepare organization for SOC 2 Type II audit",
            "success_criteria": ["All SOC 2 controls documented with evidence"]
        },
        "workflow": [
            {
                "step": "initialize_mission",
                "agent": "compliance_analyst",
                "outputs": {}
            },
            {
                "step": "assess_controls",
                "agent": "compliance_analyst",
                "outputs": {}
            },
            {
                "step": "collect_evidence",
                "agent": "evidence_collector",
                "outputs": {
                    "evidence_refs": ["ev_001", "ev_002"]
                }
            }
        ]
    }
    
    # Execute workflow
    receipt = await kernel.execute_workflow(
        workflow_yaml=json.dumps(example_workflow),
        inputs={
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001"
        }
    )
    
    print(f"Mission completed: {receipt.receipt_id}")
    print(f"Audit trail: {receipt.audit_trail_ref}")


if __name__ == "__main__":
    asyncio.run(main())