"""
Mission Mode Capability Admission Policy

Implements risk-based capability admission for security and compliance enforcement.
Agents must request capabilities before execution; high-risk capabilities require explicit approval.
"""

import json
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskClass(Enum):
    """Capability risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC_2 = "SOC_2"
    ISO_27001 = "ISO_27001"
    PCI = "PCI"


class AdmissionStatus(Enum):
    """Capability admission status"""
    ADMITTED = "admitted"
    DENIED = "denied"
    PENDING_APPROVAL = "pending_approval"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class Capability:
    """Capability definition"""
    capability_id: str
    name: str
    description: str
    risk_class: RiskClass
    actions: List[str]
    adapter_id: str
    compliance_frameworks: List[ComplianceFramework]
    evidence_quality: str  # "artifact", "synthetic", "observation"
    registered_at: str
    registered_by: str
    is_active: bool = True


@dataclass
class Grant:
    """Capability grant for a specific mission"""
    grant_id: str
    mission_id: str
    capability: str
    action: str
    risk_class: RiskClass
    granted_at: str
    granted_by: str
    expires_at: str
    constraints: Dict[str, any] = field(default_factory=dict)
    status: AdmissionStatus = AdmissionStatus.ADMITTED
    revoked_at: Optional[str] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None


@dataclass
class AdmissionRequest:
    """Request for capability admission"""
    request_id: str
    mission_id: str
    agent: str
    capability: str
    action: str
    compliance_framework: ComplianceFramework
    requested_at: str
    justification: str
    target: Optional[str] = None
    arguments: Dict[str, any] = field(default_factory=dict)


@dataclass
class AdmissionDecision:
    """Decision on capability admission request"""
    decision_id: str
    request_id: str
    status: AdmissionStatus
    decision_at: str
    decided_by: str
    reason: str
    grant_id: Optional[str] = None
    expires_at: Optional[str] = None
    constraints: Dict[str, any] = field(default_factory=dict)


class CapabilityAdmissionPolicy:
    """
    Capability Admission Policy for Mission Mode
    
    Implements risk-based capability admission with:
    - Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
    - Framework compatibility checks
    - Grant generation and validation
    - Automatic admission for low-risk capabilities
    - Explicit approval for high-risk capabilities
    """
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.grants: Dict[str, Grant] = {}
        self.admission_requests: Dict[str, AdmissionRequest] = {}
        self.admission_decisions: Dict[str, AdmissionDecision] = {}
        
        # Default grant duration
        self.default_grant_duration_minutes = 60
        
        # Pre-register standard capabilities
        self._register_standard_capabilities()
        
        logger.info("Capability Admission Policy initialized")
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique identifier"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4)
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _register_standard_capabilities(self):
        """Pre-register standard capabilities for common operations"""
        
        # Evidence collection capabilities
        self.register_capability(
            capability_id="evidence.collect",
            name="Evidence Collection",
            description="Collect evidence artifacts for compliance controls",
            risk_class=RiskClass.LOW,
            actions=["read", "validate"],
            adapter_id="evidence-collector",
            compliance_frameworks=[ComplianceFramework.SOC_2, ComplianceFramework.ISO_27001, ComplianceFramework.PCI],
            evidence_quality="artifact",
            registered_by="system"
        )
        
        # Document generation capabilities
        self.register_capability(
            capability_id="document.generate",
            name="Document Generation",
            description="Generate compliance documentation and reports",
            risk_class=RiskClass.MEDIUM,
            actions=["create", "update"],
            adapter_id="document-generator",
            compliance_frameworks=[ComplianceFramework.SOC_2, ComplianceFramework.ISO_27001, ComplianceFramework.PCI],
            evidence_quality="synthetic",
            registered_by="system"
        )
        
        # Control assessment capabilities
        self.register_capability(
            capability_id="control.assess",
            name="Control Assessment",
            description="Assess compliance controls against requirements",
            risk_class=RiskClass.LOW,
            actions=["read", "analyze"],
            adapter_id="control-assessor",
            compliance_frameworks=[ComplianceFramework.SOC_2, ComplianceFramework.ISO_27001, ComplianceFramework.PCI],
            evidence_quality="observation",
            registered_by="system"
        )
        
        # System configuration capabilities (HIGH RISK)
        self.register_capability(
            capability_id="system.configure",
            name="System Configuration",
            description="Modify system configuration for compliance",
            risk_class=RiskClass.HIGH,
            actions=["read", "write", "modify"],
            adapter_id="system-configurator",
            compliance_frameworks=[ComplianceFramework.SOC_2, ComplianceFramework.ISO_27001],
            evidence_quality="artifact",
            registered_by="system"
        )
        
        # Credential access capabilities (CRITICAL RISK)
        self.register_capability(
            capability_id="credential.access",
            name="Credential Access",
            description="Access system credentials and secrets",
            risk_class=RiskClass.CRITICAL,
            actions=["read"],
            adapter_id="credential-manager",
            compliance_frameworks=[ComplianceFramework.SOC_2, ComplianceFramework.ISO_27001, ComplianceFramework.PCI],
            evidence_quality="synthetic",
            registered_by="system"
        )
        
        logger.info(f"Registered {len(self.capabilities)} standard capabilities")
    
    def register_capability(self, capability_id: str, name: str, description: str,
                          risk_class: RiskClass, actions: List[str], adapter_id: str,
                          compliance_frameworks: List[ComplianceFramework],
                          evidence_quality: str, registered_by: str) -> bool:
        """
        Register a new capability
        
        Args:
            capability_id: Unique capability identifier
            name: Human-readable capability name
            description: Capability description
            risk_class: Risk classification
            actions: Supported actions
            adapter_id: Adapter that implements this capability
            compliance_frameworks: Supported compliance frameworks
            evidence_quality: Quality of evidence produced
            registered_by: Entity registering the capability
        
        Returns:
            True if registration successful, False otherwise
        """
        if capability_id in self.capabilities:
            logger.warning(f"Capability {capability_id} already registered")
            return False
        
        capability = Capability(
            capability_id=capability_id,
            name=name,
            description=description,
            risk_class=risk_class,
            actions=actions,
            adapter_id=adapter_id,
            compliance_frameworks=compliance_frameworks,
            evidence_quality=evidence_quality,
            registered_at=datetime.now(timezone.utc).isoformat(),
            registered_by=registered_by,
            is_active=True
        )
        
        self.capabilities[capability_id] = capability
        logger.info(f"Registered capability: {capability_id} (risk: {risk_class.value})")
        return True
    
    def request_admission(self, mission_id: str, agent: str, capability: str,
                       action: str, compliance_framework: ComplianceFramework,
                       justification: str, target: Optional[str] = None,
                       arguments: Optional[Dict[str, any]] = None) -> AdmissionDecision:
        """
        Request admission for a capability
        
        Args:
            mission_id: Mission identifier
            agent: Agent requesting capability
            capability: Capability identifier
            action: Specific action being requested
            compliance_framework: Compliance framework for the mission
            justification: Justification for the request
            target: Optional target of the operation
            arguments: Optional arguments for the operation
        
        Returns:
            Admission decision
        """
        request_id = self._generate_id("req")
        
        # Create admission request
        request = AdmissionRequest(
            request_id=request_id,
            mission_id=mission_id,
            agent=agent,
            capability=capability,
            action=action,
            compliance_framework=compliance_framework,
            requested_at=datetime.now(timezone.utc).isoformat(),
            justification=justification,
            target=target,
            arguments=arguments or {}
        )
        
        self.admission_requests[request_id] = request
        
        # Make admission decision
        decision = self._make_admission_decision(request)
        self.admission_decisions[decision.decision_id] = decision
        
        logger.info(f"Admission decision for {capability}: {decision.status.value} - {decision.reason}")
        return decision
    
    def _make_admission_decision(self, request: AdmissionRequest) -> AdmissionDecision:
        """Make admission decision based on policy"""
        decision_id = self._generate_id("dec")
        
        # Check if capability exists
        if request.capability not in self.capabilities:
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.DENIED,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Capability {request.capability} not registered"
            )
        
        capability = self.capabilities[request.capability]
        
        # Check if capability is active
        if not capability.is_active:
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.DENIED,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Capability {request.capability} is not active"
            )
        
        # Check if action is supported
        if request.action not in capability.actions:
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.DENIED,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Action {request.action} not supported by capability {request.capability}"
            )
        
        # Check framework compatibility
        if request.compliance_framework not in capability.compliance_frameworks:
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.DENIED,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Capability {request.capability} not supported for {request.compliance_framework.value}"
            )
        
        # Risk-based admission
        if capability.risk_class == RiskClass.LOW:
            # Auto-admit low-risk capabilities
            return self._grant_capability(request, capability)
        
        elif capability.risk_class == RiskClass.MEDIUM:
            # Auto-admit medium-risk capabilities if framework-compatible
            return self._grant_capability(request, capability)
        
        elif capability.risk_class == RiskClass.HIGH:
            # High-risk capabilities require explicit approval
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.PENDING_APPROVAL,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"High-risk capability {request.capability} requires explicit approval"
            )
        
        elif capability.risk_class == RiskClass.CRITICAL:
            # Critical capabilities require explicit approval + operator confirmation
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.PENDING_APPROVAL,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Critical-risk capability {request.capability} requires explicit approval + operator confirmation"
            )
        
        else:
            return AdmissionDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                status=AdmissionStatus.DENIED,
                decision_at=datetime.now(timezone.utc).isoformat(),
                decided_by="policy",
                reason=f"Unknown risk class: {capability.risk_class}"
            )
    
    def _grant_capability(self, request: AdmissionRequest, capability: Capability) -> AdmissionDecision:
        """Grant a capability request"""
        grant_id = self._generate_id("grant")
        expires_at = (datetime.now(timezone.utc) + 
                    timedelta(minutes=self.default_grant_duration_minutes)).isoformat()
        
        # Create grant
        grant = Grant(
            grant_id=grant_id,
            mission_id=request.mission_id,
            capability=request.capability,
            action=request.action,
            risk_class=capability.risk_class,
            granted_at=datetime.now(timezone.utc).isoformat(),
            granted_by="policy",
            expires_at=expires_at,
            constraints={
                "max_runtime_seconds": 300,
                "max_output_bytes": 1048576,
                "allowed_targets": self._get_allowed_targets(request, capability)
            },
            status=AdmissionStatus.ADMITTED
        )
        
        self.grants[grant_id] = grant
        
        return AdmissionDecision(
            decision_id=self._generate_id("dec"),
            request_id=request.request_id,
            status=AdmissionStatus.ADMITTED,
            decision_at=datetime.now(timezone.utc).isoformat(),
            decided_by="policy",
            reason=f"Capability {request.capability} admitted",
            grant_id=grant_id,
            expires_at=expires_at,
            constraints=grant.constraints
        )
    
    def _get_allowed_targets(self, request: AdmissionRequest, capability: Capability) -> List[str]:
        """Get allowed targets for a capability grant.

        Fail closed: a request must explicitly specify a target.
        """
        if request.target:
            return [request.target]
        raise ValueError(
            f"Capability {request.capability} requires an explicit target. "
            "Wildcard ('*') grants are not allowed by default."
        )
    
    def approve_request(self, request_id: str, approved_by: str, 
                       expires_in_minutes: Optional[int] = None) -> AdmissionDecision:
        """
        Approve a pending admission request
        
        Args:
            request_id: Request identifier
            approved_by: Entity approving the request
            expires_in_minutes: Optional custom expiration time
        
        Returns:
            Updated admission decision
        """
        if request_id not in self.admission_requests:
            logger.error(f"Request {request_id} not found")
            raise ValueError(f"Request {request_id} not found")
        
        request = self.admission_requests[request_id]
        capability = self.capabilities.get(request.capability)
        
        if not capability:
            logger.error(f"Capability {request.capability} not found")
            raise ValueError(f"Capability {request.capability} not found")
        
        # Grant the capability
        grant_id = self._generate_id("grant")
        expires_at = (datetime.now(timezone.utc) + 
                    timedelta(minutes=expires_in_minutes or self.default_grant_duration_minutes)).isoformat()
        
        grant = Grant(
            grant_id=grant_id,
            mission_id=request.mission_id,
            capability=request.capability,
            action=request.action,
            risk_class=capability.risk_class,
            granted_at=datetime.now(timezone.utc).isoformat(),
            granted_by=approved_by,
            expires_at=expires_at,
            constraints={
                "max_runtime_seconds": 300,
                "max_output_bytes": 1048576,
                "allowed_targets": self._get_allowed_targets(request, capability)
            },
            status=AdmissionStatus.ADMITTED
        )
        
        self.grants[grant_id] = grant
        
        # Update admission decision
        decision_id = self._generate_id("dec")
        decision = AdmissionDecision(
            decision_id=decision_id,
            request_id=request_id,
            status=AdmissionStatus.ADMITTED,
            decision_at=datetime.now(timezone.utc).isoformat(),
            decided_by=approved_by,
            reason=f"Request approved by {approved_by}",
            grant_id=grant_id,
            expires_at=expires_at,
            constraints=grant.constraints
        )
        
        self.admission_decisions[decision_id] = decision
        
        logger.info(f"Request {request_id} approved by {approved_by}")
        return decision
    
    def validate_grant(self, grant_id: str, capability: str, action: str) -> Tuple[bool, str]:
        """
        Validate a grant for capability execution
        
        Args:
            grant_id: Grant identifier
            capability: Capability being executed
            action: Action being executed
        
        Returns:
            (is_valid: bool, reason: str)
        """
        if grant_id not in self.grants:
            return False, f"Grant {grant_id} not found"
        
        grant = self.grants[grant_id]
        
        # Check if grant is active
        if grant.status != AdmissionStatus.ADMITTED:
            return False, f"Grant {grant_id} is not active (status: {grant.status.value})"
        
        # Check if grant is expired
        if datetime.now(timezone.utc) > datetime.fromisoformat(grant.expires_at):
            return False, f"Grant {grant_id} is expired"
        
        # Check if grant matches capability
        if grant.capability != capability:
            return False, f"Grant {grant_id} is for capability {grant.capability}, not {capability}"
        
        # Check if grant matches action
        if grant.action != action:
            return False, f"Grant {grant_id} is for action {grant.action}, not {action}"
        
        return True, "Grant valid"
    
    def revoke_grant(self, grant_id: str, revoked_by: str, reason: str) -> bool:
        """
        Revoke a grant
        
        Args:
            grant_id: Grant identifier
            revoked_by: Entity revoking the grant
            reason: Reason for revocation
        
        Returns:
            True if revocation successful, False otherwise
        """
        if grant_id not in self.grants:
            logger.error(f"Grant {grant_id} not found")
            return False
        
        grant = self.grants[grant_id]
        grant.status = AdmissionStatus.REVOKED
        grant.revoked_at = datetime.now(timezone.utc).isoformat()
        grant.revoked_by = revoked_by
        grant.revocation_reason = reason
        
        logger.info(f"Grant {grant_id} revoked by {revoked_by}: {reason}")
        return True
    
    def get_active_grants(self, mission_id: Optional[str] = None) -> List[Grant]:
        """
        Get active grants, optionally filtered by mission
        
        Args:
            mission_id: Optional mission identifier filter
        
        Returns:
            List of active grants
        """
        active_grants = []
        
        for grant in self.grants.values():
            if grant.status == AdmissionStatus.ADMITTED:
                # Check if expired
                if datetime.now(timezone.utc) <= datetime.fromisoformat(grant.expires_at):
                    # Filter by mission if provided
                    if mission_id is None or grant.mission_id == mission_id:
                        active_grants.append(grant)
        
        return active_grants
    
    def cleanup_expired_grants(self) -> int:
        """Clean up expired grants and return count of cleaned grants"""
        cleaned_count = 0
        now = datetime.now(timezone.utc)
        
        for grant in self.grants.values():
            if grant.status == AdmissionStatus.ADMITTED:
                if now > datetime.fromisoformat(grant.expires_at):
                    grant.status = AdmissionStatus.EXPIRED
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} expired grants")
        return cleaned_count


async def main():
    """Example usage of capability admission policy"""
    policy = CapabilityAdmissionPolicy()
    
    # Request admission for a low-risk capability
    decision = policy.request_admission(
        mission_id="mission_001",
        agent="compliance_analyst",
        capability="evidence.collect",
        action="read",
        compliance_framework=ComplianceFramework.SOC_2,
        justification="Need to collect evidence for control CC1.1",
        target="s3://evidence-bucket/control-cc1.1"
    )
    
    print(f"Decision: {decision.status.value}")
    print(f"Reason: {decision.reason}")
    print(f"Grant ID: {decision.grant_id}")
    
    # Request admission for a high-risk capability
    decision = policy.request_admission(
        mission_id="mission_001",
        agent="system_admin",
        capability="system.configure",
        action="modify",
        compliance_framework=ComplianceFramework.SOC_2,
        justification="Need to configure system for compliance",
        target="/etc/security/limits.conf"
    )
    
    print(f"\nDecision: {decision.status.value}")
    print(f"Reason: {decision.reason}")
    
    # Approve the high-risk request
    if decision.status == AdmissionStatus.PENDING_APPROVAL:
        decision = policy.approve_request(
            request_id=decision.request_id,
            approved_by="operator",
            expires_in_minutes=30
        )
        print(f"\nApproved: {decision.status.value}")
        print(f"Grant ID: {decision.grant_id}")
        
        # Validate the grant
        is_valid, reason = policy.validate_grant(
            grant_id=decision.grant_id,
            capability="system.configure",
            action="modify"
        )
        print(f"Grant valid: {is_valid} - {reason}")
    
    # Get active grants
    active_grants = policy.get_active_grants(mission_id="mission_001")
    print(f"\nActive grants for mission_001: {len(active_grants)}")
    
    # Cleanup expired grants
    cleaned = policy.cleanup_expired_grants()
    print(f"Cleaned {cleaned} expired grants")


if __name__ == "__main__":
    asyncio.run(main())