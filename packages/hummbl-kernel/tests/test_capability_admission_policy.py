"""Tests for Capability Admission Policy."""

import unittest
from datetime import datetime, timezone, timedelta
from hummbl_kernel.security.capability_admission_policy import (
    CapabilityAdmissionPolicy,
    RiskClass,
    ComplianceFramework,
    AdmissionStatus,
    AdmissionDecision,
)


class TestCapabilityAdmissionPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = CapabilityAdmissionPolicy()

    def test_initialization(self):
        """Policy should initialize with standard capabilities."""
        self.assertIsNotNone(self.policy)
        self.assertGreater(len(self.policy.capabilities), 0)
        self.assertEqual(len(self.policy.capabilities), 5)  # 5 standard capabilities

    def test_pre_registered_capabilities(self):
        """Standard capabilities should be pre-registered."""
        self.assertIn("evidence.collect", self.policy.capabilities)
        self.assertIn("document.generate", self.policy.capabilities)
        self.assertIn("control.assess", self.policy.capabilities)
        self.assertIn("system.configure", self.policy.capabilities)
        self.assertIn("credential.access", self.policy.capabilities)

    def test_low_risk_auto_admit(self):
        """LOW risk capabilities should be auto-admitted."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Collect evidence for audit",
            target="/tmp/evidence.txt",
        )
        self.assertEqual(decision.status, AdmissionStatus.ADMITTED)
        self.assertIsNotNone(decision.grant_id)
        self.assertIn("admitted", decision.reason.lower())

    def test_medium_risk_auto_admit(self):
        """MEDIUM risk capabilities should be auto-admitted."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="document.generate",
            action="create",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Generate compliance report",
            target="report.pdf",
        )
        self.assertEqual(decision.status, AdmissionStatus.ADMITTED)
        self.assertIsNotNone(decision.grant_id)

    def test_high_risk_requires_approval(self):
        """HIGH risk capabilities should require approval."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="system.configure",
            action="modify",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Modify system configuration",
            target="/etc/config",
        )
        self.assertEqual(decision.status, AdmissionStatus.PENDING_APPROVAL)
        self.assertIsNone(decision.grant_id)
        self.assertIn("requires explicit approval", decision.reason.lower())

    def test_critical_risk_requires_approval(self):
        """CRITICAL risk capabilities should require approval."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="credential.access",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Access credentials",
            target="/etc/credentials",
        )
        self.assertEqual(decision.status, AdmissionStatus.PENDING_APPROVAL)
        self.assertIsNone(decision.grant_id)
        self.assertIn("requires explicit approval", decision.reason.lower())

    def test_framework_compatibility_soc2(self):
        """SOC 2 framework should be compatible with standard capabilities."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Collect evidence",
            target="/tmp/evidence.txt",
        )
        self.assertEqual(decision.status, AdmissionStatus.ADMITTED)

    def test_framework_compatibility_pci(self):
        """PCI framework should be compatible with security capabilities."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="credential.access",
            action="read",
            compliance_framework=ComplianceFramework.PCI,
            justification="Access credentials",
            target="/etc/credentials",
        )
        # Credential access is CRITICAL risk, so it requires approval
        self.assertEqual(decision.status, AdmissionStatus.PENDING_APPROVAL)

    def test_framework_incompatibility(self):
        """Incompatible frameworks should be denied."""
        # Register a capability that only supports SOC_2
        self.policy.register_capability(
            capability_id="soc2_only",
            name="SOC 2 Only Capability",
            description="Only for SOC 2",
            risk_class=RiskClass.LOW,
            actions=["read"],
            adapter_id="test_adapter",
            compliance_frameworks=[ComplianceFramework.SOC_2],
            evidence_quality="artifact",
            registered_by="test"
        )
        
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="soc2_only",
            action="read",
            compliance_framework=ComplianceFramework.PCI,  # Incompatible
            justification="Test",
            target="/tmp/test",
        )
        self.assertEqual(decision.status, AdmissionStatus.DENIED)
        self.assertIn("not supported for", decision.reason.lower())

    def test_unregistered_capability_denied(self):
        """Unregistered capabilities should be denied."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="unregistered.cap",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Test",
            target="/tmp/test",
        )
        self.assertEqual(decision.status, AdmissionStatus.DENIED)
        self.assertIn("not registered", decision.reason.lower())

    def test_unsupported_action_denied(self):
        """Unsupported actions should be denied."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="delete",  # Not supported
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Test",
            target="/tmp/test",
        )
        self.assertEqual(decision.status, AdmissionStatus.DENIED)
        self.assertIn("not supported", decision.reason.lower())

    def test_grant_validation_valid(self):
        """Valid grants should pass validation."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Read local file",
            target="/tmp/file.txt",
        )
        
        is_valid, reason = self.policy.validate_grant(
            grant_id=decision.grant_id,
            capability="evidence.collect",
            action="read",
        )
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Grant valid")

    def test_grant_validation_capability_mismatch(self):
        """Grants should fail validation for different capabilities."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Read local file",
            target="/tmp/file.txt",
        )
        
        is_valid, reason = self.policy.validate_grant(
            grant_id=decision.grant_id,
            capability="document.generate",  # Different capability
            action="read",
        )
        self.assertFalse(is_valid)
        self.assertIn("not", reason.lower())

    def test_grant_validation_action_mismatch(self):
        """Grants should fail validation for different actions."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Read local file",
            target="/tmp/file.txt",
        )
        
        is_valid, reason = self.policy.validate_grant(
            grant_id=decision.grant_id,
            capability="evidence.collect",
            action="write",  # Different action
        )
        self.assertFalse(is_valid)
        self.assertIn("not", reason.lower())

    def test_grant_validation_invalid_grant_id(self):
        """Invalid grant IDs should fail validation."""
        is_valid, reason = self.policy.validate_grant(
            grant_id="invalid_grant_id",
            capability="evidence.collect",
            action="read",
        )
        self.assertFalse(is_valid)
        self.assertIn("not found", reason.lower())

    def test_grant_constraints(self):
        """Grants should include constraints."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Read local file",
            target="/tmp/file.txt",
        )
        
        self.assertIsNotNone(decision.constraints)
        self.assertIn("max_runtime_seconds", decision.constraints)
        self.assertIn("max_output_bytes", decision.constraints)
        self.assertIn("allowed_targets", decision.constraints)

    def test_grant_expiration(self):
        """Grants should expire after default duration."""
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="evidence.collect",
            action="read",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Read local file",
            target="/tmp/file.txt",
        )
        
        self.assertIsNotNone(decision.expires_at)
        expires_at = datetime.fromisoformat(decision.expires_at)
        granted_at = datetime.fromisoformat(decision.decision_at)
        
        # Check that expiration is approximately 60 minutes in the future
        duration = (expires_at - granted_at).total_seconds()
        self.assertAlmostEqual(duration, 60 * 60, delta=5)  # 60 minutes ± 5 seconds

    def test_custom_capability_registration(self):
        """Custom capabilities should be registrable."""
        success = self.policy.register_capability(
            capability_id="custom.cap",
            name="Custom Capability",
            description="A custom capability",
            risk_class=RiskClass.MEDIUM,
            actions=["read", "write"],
            adapter_id="custom_adapter",
            compliance_frameworks=[ComplianceFramework.SOC_2],
            evidence_quality="synthetic",
            registered_by="test"
        )
        self.assertTrue(success)
        self.assertIn("custom.cap", self.policy.capabilities)

    def test_duplicate_capability_registration(self):
        """Duplicate capability registration should fail."""
        success = self.policy.register_capability(
            capability_id="evidence.collect",  # Already exists
            name="Duplicate",
            description="Duplicate capability",
            risk_class=RiskClass.LOW,
            actions=["read"],
            adapter_id="test",
            compliance_frameworks=[ComplianceFramework.SOC_2],
            evidence_quality="artifact",
            registered_by="test"
        )
        self.assertFalse(success)

    def test_request_approval(self):
        """Pending requests should be approvable."""
        # First, create a pending request
        decision = self.policy.request_admission(
            mission_id="test_mission",
            agent="test_agent",
            capability="system.configure",
            action="modify",
            compliance_framework=ComplianceFramework.SOC_2,
            justification="Modify system configuration",
            target="/etc/config",
        )
        
        self.assertEqual(decision.status, AdmissionStatus.PENDING_APPROVAL)
        
        # Approve the request
        approved_decision = self.policy.approve_request(
            request_id=decision.request_id,
            approved_by="operator",
            expires_in_minutes=120
        )
        
        self.assertEqual(approved_decision.status, AdmissionStatus.ADMITTED)
        self.assertIsNotNone(approved_decision.grant_id)
        self.assertIn("approved by operator", approved_decision.reason.lower())

    def test_approve_nonexistent_request(self):
        """Approving non-existent request should raise error."""
        with self.assertRaises(ValueError):
            self.policy.approve_request(
                request_id="nonexistent_request",
                approved_by="operator"
            )


if __name__ == "__main__":
    unittest.main()
