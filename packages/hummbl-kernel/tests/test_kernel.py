"""Tests for Mission Mode Kernel."""

import os
import unittest
from datetime import datetime, timezone
from kernel.kernel import (
    MissionModeKernel,
    ComplianceFramework,
    EventStatus,
    RiskClass,
    AuditEvent,
    MissionReceipt,
    FleetConfig,
)

# Set test signing key for audit event signing tests
os.environ["MISSION_MODE_SIGNING_KEY"] = "test-signing-key"


class TestMissionModeKernel(unittest.TestCase):
    def setUp(self):
        self.kernel = MissionModeKernel()

    def test_kernel_initialization(self):
        """Kernel should initialize with default configuration."""
        self.assertIsNotNone(self.kernel)
        self.assertIsNotNone(self.kernel.fleet_config)

    def test_id_generation(self):
        """ID generation should produce identifiers with correct format."""
        id1 = self.kernel._generate_id("test")
        self.assertTrue(id1.startswith("test_"))
        self.assertIn("_", id1)

    def test_hash_computation(self):
        """Hash computation should be deterministic."""
        data = "test data"
        hash1 = self.kernel._compute_hash(data)
        hash2 = self.kernel._compute_hash(data)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex digest

    def test_capability_registration(self):
        """Capabilities should be registered with risk classification."""
        self.kernel.register_capability(
            capability="file.read",
            risk_class=RiskClass.LOW,
            adapter_id="adapter_001",
            compliance_frameworks=[ComplianceFramework.SOC_2]
        )
        self.assertIn("file.read", self.kernel.capability_registry)
        self.assertEqual(
            self.kernel.capability_registry["file.read"]["risk_class"],
            RiskClass.LOW
        )

    def test_capability_admission_low_risk(self):
        """LOW risk capabilities should be auto-admitted."""
        self.kernel.register_capability(
            capability="file.read",
            risk_class=RiskClass.LOW,
            adapter_id="adapter_001",
            compliance_frameworks=[ComplianceFramework.SOC_2]
        )
        admitted, reason = self.kernel.admit_capability(
            capability="file.read",
            agent="test_agent",
            compliance_framework=ComplianceFramework.SOC_2
        )
        self.assertTrue(admitted)
        self.assertEqual(reason, "Capability admitted")

    def test_capability_admission_high_risk(self):
        """HIGH risk capabilities should require approval."""
        self.kernel.register_capability(
            capability="network.external",
            risk_class=RiskClass.HIGH,
            adapter_id="adapter_001",
            compliance_frameworks=[ComplianceFramework.SOC_2]
        )
        admitted, reason = self.kernel.admit_capability(
            capability="network.external",
            agent="test_agent",
            compliance_framework=ComplianceFramework.SOC_2
        )
        self.assertFalse(admitted)
        self.assertIn("requires explicit approval", reason)

    def test_capability_admission_unregistered(self):
        """Unregistered capabilities should be denied."""
        admitted, reason = self.kernel.admit_capability(
            capability="unregistered.cap",
            agent="test_agent",
            compliance_framework=ComplianceFramework.SOC_2
        )
        self.assertFalse(admitted)
        self.assertIn("not registered", reason)

    def test_audit_trail_creation(self):
        """Audit trails should be created for missions."""
        audit_trail_id = self.kernel.create_audit_trail(
            mission_id="test_mission",
            workflow_id="test_workflow",
            compliance_framework=ComplianceFramework.SOC_2,
            audit_period_start="2025-01-01T00:00:00Z",
            audit_period_end="2025-12-31T23:59:59Z",
            organization_id="org_001"
        )
        self.assertIsNotNone(audit_trail_id)
        self.assertTrue(audit_trail_id.startswith("at_"))
        self.assertIn(audit_trail_id, self.kernel.audit_trails)

    def test_audit_event_appending(self):
        """Audit events should be appended to audit trails."""
        audit_trail_id = self.kernel.create_audit_trail(
            mission_id="test_mission",
            workflow_id="test_workflow",
            compliance_framework=ComplianceFramework.SOC_2,
            audit_period_start="2025-01-01T00:00:00Z",
            audit_period_end="2025-12-31T23:59:59Z",
            organization_id="org_001"
        )
        event = AuditEvent(
            event_id=self.kernel._generate_id("evt"),
            audit_trail_id=audit_trail_id,
            mission_id="test_mission",
            workflow_id="test_workflow",
            step_id="step_1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="test_agent",
            event_type="capability_request",
            actor="system",
            payload={},
            compliance_metadata={},
            evidence_refs=[]
        )
        success = self.kernel.append_audit_event(audit_trail_id, event)
        self.assertTrue(success)
        self.assertEqual(len(self.kernel.audit_trails[audit_trail_id]["events"]), 1)

    def test_audit_trail_finalization(self):
        """Audit trails should be finalizable."""
        audit_trail_id = self.kernel.create_audit_trail(
            mission_id="test_mission",
            workflow_id="test_workflow",
            compliance_framework=ComplianceFramework.SOC_2,
            audit_period_start="2025-01-01T00:00:00Z",
            audit_period_end="2025-12-31T23:59:59Z",
            organization_id="org_001"
        )
        success = self.kernel.finalize_audit_trail(audit_trail_id)
        self.assertTrue(success)
        self.assertEqual(self.kernel.audit_trails[audit_trail_id]["status"], "finalized")

    def test_receipt_generation(self):
        """Receipts should be generated for completed missions."""
        audit_trail_id = self.kernel.create_audit_trail(
            mission_id="test_mission",
            workflow_id="test_workflow",
            compliance_framework=ComplianceFramework.SOC_2,
            audit_period_start="2025-01-01T00:00:00Z",
            audit_period_end="2025-12-31T23:59:59Z",
            organization_id="org_001"
        )
        receipt = self.kernel.generate_receipt(
            mission_id="test_mission",
            workflow_id="test_workflow",
            final_status="completed",
            agent="test_agent",
            audit_trail_id=audit_trail_id,
            evidence_refs=["ev_001"]
        )
        self.assertEqual(receipt.mission_id, "test_mission")
        self.assertEqual(receipt.final_status, "completed")
        self.assertEqual(receipt.agent, "test_agent")
        self.assertIsNotNone(receipt.receipt_id)
        self.assertEqual(receipt.audit_trail_ref, audit_trail_id)

    def test_fleet_config_default(self):
        """Fleet config should have generic defaults."""
        self.assertIsNotNone(self.kernel.fleet_config)
        self.assertEqual(self.kernel.fleet_config.primary_compute, "primary")
        self.assertEqual(self.kernel.fleet_config.gpu_compute, "gpu")
        self.assertEqual(self.kernel.fleet_config.fallback_compute, "primary")

    def test_fleet_config_custom(self):
        """Custom fleet config should be respected."""
        custom_config = FleetConfig(
            primary_compute="alpha",
            gpu_compute="beta",
            fallback_compute="gamma"
        )
        kernel_custom = MissionModeKernel(fleet_config=custom_config)
        self.assertEqual(kernel_custom.fleet_config.primary_compute, "alpha")
        self.assertEqual(kernel_custom.fleet_config.gpu_compute, "beta")

    def test_get_optimal_compute(self):
        """Optimal compute should be determined by task type."""
        self.assertEqual(self.kernel.get_optimal_compute("inference"), "primary")
        self.assertEqual(self.kernel.get_optimal_compute("gpu_workload"), "gpu")
        self.assertEqual(self.kernel.get_optimal_compute("file_ops"), "gpu")

    def test_event_signing(self):
        """Audit events should be signed."""
        event = AuditEvent(
            event_id="evt_001",
            audit_trail_id="at_001",
            mission_id="mission_001",
            workflow_id="workflow_001",
            step_id="step_1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="test_agent",
            event_type="test_event",
            actor="system",
            payload={"test": "data"},
            compliance_metadata={},
            evidence_refs=[]
        )
        signature = self.kernel._sign_event(event)
        self.assertIsNotNone(signature)
        self.assertEqual(len(signature), 64)  # SHA-256 hex digest


if __name__ == "__main__":
    unittest.main()
