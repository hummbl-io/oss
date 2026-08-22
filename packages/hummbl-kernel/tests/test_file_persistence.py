"""Tests for audit trail file persistence."""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from kernel.audit.file_persistence import AuditTrailPersistence, get_persistence


class TestAuditTrailPersistence(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.persistence = AuditTrailPersistence(base_dir=self.temp_dir, signing_key="test-key")
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Persistence should initialize with base directory."""
        self.assertEqual(self.persistence.base_dir, Path(self.temp_dir))
        self.assertTrue(self.persistence.base_dir.exists())
    
    def test_save_audit_trail(self):
        """Audit trail should be saved to disk."""
        audit_trail = {
            "audit_trail_id": "at_001",
            "mission_id": "mission_001",
            "workflow_id": "workflow_001",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": []
        }
        
        success = self.persistence.save_audit_trail(audit_trail)
        self.assertTrue(success)
        
        # Check file exists
        file_path = self.persistence._get_audit_trail_path("at_001")
        self.assertTrue(file_path.exists())
    
    def test_save_audit_trail_with_signature(self):
        """Saved audit trail should include HMAC signature."""
        audit_trail = {
            "audit_trail_id": "at_002",
            "mission_id": "mission_002",
            "workflow_id": "workflow_002",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": []
        }
        
        self.persistence.save_audit_trail(audit_trail)
        
        # Load and check signature
        loaded = self.persistence.load_audit_trail("at_002")
        self.assertIsNotNone(loaded)
        self.assertIn("signature", loaded)
        self.assertEqual(len(loaded["signature"]), 64)  # SHA-256 hex digest
    
    def test_load_audit_trail(self):
        """Audit trail should be loaded from disk."""
        audit_trail = {
            "audit_trail_id": "at_003",
            "mission_id": "mission_003",
            "workflow_id": "workflow_003",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": []
        }
        
        self.persistence.save_audit_trail(audit_trail)
        
        loaded = self.persistence.load_audit_trail("at_003")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["audit_trail_id"], "at_003")
        self.assertEqual(loaded["mission_id"], "mission_003")
    
    def test_load_audit_trail_not_found(self):
        """Loading non-existent audit trail should return None."""
        loaded = self.persistence.load_audit_trail("nonexistent")
        self.assertIsNone(loaded)
    
    def test_load_audit_trail_invalid_signature(self):
        """Audit trail with invalid signature should fail verification."""
        # Create audit trail with invalid signature
        audit_trail = {
            "audit_trail_id": "at_004",
            "mission_id": "mission_004",
            "workflow_id": "workflow_004",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": [],
            "signature": "invalid_signature"
        }
        
        # Manually write file with invalid signature
        file_path = self.persistence._get_audit_trail_path("at_004")
        with open(file_path, 'w') as f:
            json.dump(audit_trail, f)
        
        # Load should return None due to invalid signature
        loaded = self.persistence.load_audit_trail("at_004")
        self.assertIsNone(loaded)
    
    def test_list_audit_trails(self):
        """List should return all audit trail IDs."""
        # Create multiple audit trails
        for i in range(3):
            audit_trail = {
                "audit_trail_id": f"at_00{i}",
                "mission_id": "mission_001",
                "workflow_id": "workflow_001",
                "compliance_framework": "SOC_2",
                "audit_period_start": "2025-01-01T00:00:00Z",
                "audit_period_end": "2025-12-31T23:59:59Z",
                "organization_id": "org_001",
                "created_at": "2025-01-01T00:00:00Z",
                "created_by": "test",
                "status": "in_progress",
                "events": []
            }
            self.persistence.save_audit_trail(audit_trail)
        
        audit_trail_ids = self.persistence.list_audit_trails()
        self.assertEqual(len(audit_trail_ids), 3)
        self.assertIn("at_000", audit_trail_ids)
        self.assertIn("at_001", audit_trail_ids)
        self.assertIn("at_002", audit_trail_ids)
    
    def test_list_audit_trails_filtered_by_mission(self):
        """List should filter audit trails by mission_id."""
        # Create audit trails for different missions
        for i in range(2):
            audit_trail = {
                "audit_trail_id": f"at_00{i}",
                "mission_id": "mission_001",
                "workflow_id": "workflow_001",
                "compliance_framework": "SOC_2",
                "audit_period_start": "2025-01-01T00:00:00Z",
                "audit_period_end": "2025-12-31T23:59:59Z",
                "organization_id": "org_001",
                "created_at": "2025-01-01T00:00:00Z",
                "created_by": "test",
                "status": "in_progress",
                "events": []
            }
            self.persistence.save_audit_trail(audit_trail)
        
        audit_trail = {
            "audit_trail_id": "at_002",
            "mission_id": "mission_002",
            "workflow_id": "workflow_002",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": []
        }
        self.persistence.save_audit_trail(audit_trail)
        
        # Filter by mission_001
        filtered = self.persistence.list_audit_trails(mission_id="mission_001")
        self.assertEqual(len(filtered), 2)
        self.assertIn("at_000", filtered)
        self.assertIn("at_001", filtered)
        self.assertNotIn("at_002", filtered)
    
    def test_get_audit_trail_stats(self):
        """Stats should return correct counts."""
        # Create audit trails
        for i in range(3):
            audit_trail = {
                "audit_trail_id": f"at_00{i}",
                "mission_id": f"mission_00{i % 2}",  # Alternate between 2 missions
                "workflow_id": "workflow_001",
                "compliance_counts": "SOC_2",
                "audit_period_start": "2025-01-01T00:00:00Z",
                "audit_period_end": "2025-12-31T23:59:59Z",
                "organization_id": "org_001",
                "created_at": "2025-01-01T00:00:00Z",
                "created_by": "test",
                "status": "in_progress",
                "events": []
            }
            self.persistence.save_audit_trail(audit_trail)
        
        stats = self.persistence.get_audit_trail_stats()
        self.assertEqual(stats["total_audit_trails"], 3)
        self.assertGreater(stats["total_size_bytes"], 0)
        self.assertIn("mission_000", stats["mission_counts"])
        self.assertIn("mission_001", stats["mission_counts"])
    
    def test_singleton_get_persistence(self):
        """get_persistence should return singleton instance."""
        # Reset singleton for testing
        import kernel.audit.file_persistence as persistence_module
        persistence_module._persistence_instance = None
        
        # First call creates instance
        instance1 = get_persistence(base_dir=self.temp_dir)
        self.assertIsNotNone(instance1)
        
        # Second call returns same instance
        instance2 = get_persistence(base_dir=self.temp_dir)
        self.assertIs(instance1, instance2)
    
    def test_custom_signing_key(self):
        """Custom signing key should be used for HMAC."""
        custom_key = "custom-test-key"
        custom_persistence = AuditTrailPersistence(
            base_dir=self.temp_dir,
            signing_key=custom_key
        )
        
        audit_trail = {
            "audit_trail_id": "at_006",
            "mission_id": "mission_006",
            "workflow_id": "workflow_006",
            "compliance_framework": "SOC_2",
            "audit_period_start": "2025-01-01T00:00:00Z",
            "audit_period_end": "2025-12-31T23:59:59Z",
            "organization_id": "org_001",
            "created_at": "2025-01-01T00:00:00Z",
            "created_by": "test",
            "status": "in_progress",
            "events": []
        }
        
        custom_persistence.save_audit_trail(audit_trail)
        
        # Load with same key should succeed
        loaded = custom_persistence.load_audit_trail("at_006")
        self.assertIsNotNone(loaded)
        
        # Load with different key should fail
        different_persistence = AuditTrailPersistence(
            base_dir=self.temp_dir,
            signing_key="different-key"
        )
        loaded = different_persistence.load_audit_trail("at_006")
        self.assertIsNone(loaded)


if __name__ == "__main__":
    unittest.main()
