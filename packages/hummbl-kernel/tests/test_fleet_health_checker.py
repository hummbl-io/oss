"""Tests for fleet health checker."""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from kernel.fleet.fleet_health_checker import (
    FleetHealthChecker,
    FleetMode,
    MachineStatus,
    MachineHealth,
    FleetHealth,
)


class TestFleetHealthChecker(unittest.TestCase):
    def setUp(self):
        self.checker = FleetHealthChecker(mode=FleetMode.HYBRID)

    def test_checker_initialization(self):
        """Health checker should initialize with correct mode."""
        self.assertEqual(self.checker.mode, FleetMode.HYBRID)
        self.assertIsNotNone(self.checker.fleet_config)
        self.assertIn("nodezero", self.checker.fleet_config)
        self.assertIn("anvil", self.checker.fleet_config)

    def test_nodezero_config(self):
        """Nodezero should be configured with correct services."""
        nodezero_config = self.checker.fleet_config["nodezero"]
        self.assertEqual(nodezero_config["hostname"], "nodezero")
        self.assertEqual(nodezero_config["ssh_alias"], "nodezero")
        self.assertIn("ollama", nodezero_config["services"])
        self.assertIn("bus", nodezero_config["services"])

    def test_anvil_config(self):
        """Anvil should be configured with correct services."""
        anvil_config = self.checker.fleet_config["anvil"]
        self.assertEqual(anvil_config["hostname"], "anvil")
        self.assertEqual(anvil_config["ssh_alias"], "anvil")
        self.assertIn("gitea", anvil_config["services"])
        self.assertIn("ollama", anvil_config["services"])

    def test_task_routing_config(self):
        """Task routing should be configured."""
        self.assertIn("inference", self.checker.task_routing)
        self.assertIn("gpu_workload", self.checker.task_routing)
        self.assertIn("file_ops", self.checker.task_routing)
        self.assertEqual(self.checker.task_routing["inference"], "nodezero")
        self.assertEqual(self.checker.task_routing["gpu_workload"], "anvil")

    def test_check_http_endpoint_success(self):
        """HTTP endpoint check should succeed for 2xx/3xx codes."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(True, "HTTP 200")):
            is_healthy, msg = self.checker._check_http_endpoint("http://example.com")
            self.assertTrue(is_healthy)
            self.assertEqual(msg, "HTTP 200")

    def test_check_http_endpoint_failure(self):
        """HTTP endpoint check should fail for 4xx/5xx codes."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(False, "HTTP 404")):
            is_healthy, msg = self.checker._check_http_endpoint("http://example.com")
            self.assertFalse(is_healthy)
            self.assertEqual(msg, "HTTP 404")

    def test_check_http_endpoint_timeout(self):
        """HTTP endpoint check should handle timeout."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(False, "timeout")):
            is_healthy, msg = self.checker._check_http_endpoint("http://example.com")
            self.assertFalse(is_healthy)
            self.assertEqual(msg, "timeout")

    def test_check_ssh_connectivity_success(self):
        """SSH connectivity check should succeed."""
        with patch.object(self.checker, '_check_ssh_connectivity', return_value=(True, "connected")):
            is_healthy, msg = self.checker._check_ssh_connectivity("nodezero")
            self.assertTrue(is_healthy)
            self.assertEqual(msg, "connected")

    def test_check_ssh_connectivity_failure(self):
        """SSH connectivity check should fail."""
        with patch.object(self.checker, '_check_ssh_connectivity', return_value=(False, "Connection refused")):
            is_healthy, msg = self.checker._check_ssh_connectivity("nodezero")
            self.assertFalse(is_healthy)
            self.assertEqual(msg, "Connection refused")

    def test_check_machine_healthy(self):
        """Machine check should return healthy status when all checks pass."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(True, "HTTP 200")):
            with patch.object(self.checker, '_check_ssh_connectivity', return_value=(True, "connected")):
                health = self.checker._check_machine("nodezero")
                self.assertEqual(health.status, MachineStatus.HEALTHY)
                self.assertEqual(health.name, "nodezero")
                self.assertIsNotNone(health.timestamp)

    def test_check_machine_unhealthy(self):
        """Machine check should return unhealthy status when checks fail."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(False, "HTTP 404")):
            with patch.object(self.checker, '_check_ssh_connectivity', return_value=(False, "Connection refused")):
                health = self.checker._check_machine("nodezero")
                self.assertEqual(health.status, MachineStatus.UNHEALTHY)
                self.assertEqual(health.name, "nodezero")

    def test_check_machine_unknown(self):
        """Machine check should return unknown status for unconfigured machines."""
        health = self.checker._check_machine("unknown_machine")
        self.assertEqual(health.status, MachineStatus.UNKNOWN)
        self.assertEqual(health.name, "unknown_machine")
        self.assertIn("error", health.details)

    def test_check_fleet_health(self):
        """Fleet health check should return status for all machines."""
        with patch.object(self.checker, '_check_machine') as mock_check:
            # Mock both machines as healthy
            mock_check.return_value = MachineHealth(
                name="test",
                status=MachineStatus.HEALTHY,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            fleet_health = self.checker.check_fleet_health()
            self.assertEqual(fleet_health.overall_status, MachineStatus.HEALTHY)
            self.assertEqual(fleet_health.mode, FleetMode.HYBRID)
            self.assertEqual(len(fleet_health.machines), 2)

    def test_fleet_health_degraded(self):
        """Fleet health should be degraded when one machine is unhealthy."""
        def mock_check_machine(name):
            if name == "nodezero":
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                return MachineHealth(
                    name=name,
                    status=MachineStatus.UNHEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        with patch.object(self.checker, '_check_machine', side_effect=mock_check_machine):
            fleet_health = self.checker.check_fleet_health()
            self.assertEqual(fleet_health.overall_status, MachineStatus.UNHEALTHY)

    def test_routing_recommendations_hybrid(self):
        """Hybrid mode should generate routing recommendations."""
        with patch.object(self.checker, '_check_machine') as mock_check:
            mock_check.return_value = MachineHealth(
                name="test",
                status=MachineStatus.HEALTHY,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            fleet_health = self.checker.check_fleet_health()
            self.assertIn("inference", fleet_health.routing_recommendations)
            self.assertIn("gpu_workload", fleet_health.routing_recommendations)

    def test_routing_recommendations_fallback(self):
        """Routing should fallback when primary node is unhealthy."""
        def mock_check_machine(name):
            if name == "nodezero":
                return MachineHealth(
                    name=name,
                    status=MachineStatus.UNHEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        
        with patch.object(self.checker, '_check_machine', side_effect=mock_check_machine):
            fleet_health = self.checker.check_fleet_health()
            # Inference should fallback to anvil when nodezero is unhealthy
            self.assertEqual(fleet_health.routing_recommendations["inference"], "anvil")

    def test_get_optimal_compute(self):
        """Optimal compute should return recommended node."""
        with patch.object(self.checker, 'check_fleet_health') as mock_health:
            mock_health.return_value = MagicMock(
                routing_recommendations={"inference": "nodezero"}
            )
            optimal = self.checker.get_optimal_compute("inference")
            self.assertEqual(optimal, "nodezero")

    def test_get_optimal_compute_with_health_param(self):
        """Optimal compute should use provided health status."""
        fleet_health = MagicMock(
            routing_recommendations={"gpu_workload": "anvil"}
        )
        optimal = self.checker.get_optimal_compute("gpu_workload", fleet_health)
        self.assertEqual(optimal, "anvil")

    def test_local_mode_routing(self):
        """Local mode should route all tasks to anvil."""
        local_checker = FleetHealthChecker(mode=FleetMode.LOCAL)
        with patch.object(local_checker, '_check_machine') as mock_check:
            mock_check.return_value = MachineHealth(
                name="test",
                status=MachineStatus.HEALTHY,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            fleet_health = local_checker.check_fleet_health()
            for task, machine in fleet_health.routing_recommendations.items():
                self.assertEqual(machine, "anvil")

    def test_nodezero_only_mode_routing(self):
        """Nodezero-only mode should route all tasks to nodezero."""
        nodezero_checker = FleetHealthChecker(mode=FleetMode.NODEZERO_ONLY)
        with patch.object(nodezero_checker, '_check_machine') as mock_check:
            mock_check.return_value = MachineHealth(
                name="test",
                status=MachineStatus.HEALTHY,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            fleet_health = nodezero_checker.check_fleet_health()
            for task, machine in fleet_health.routing_recommendations.items():
                self.assertEqual(machine, "nodezero")

    def test_print_health_report(self):
        """Health report should print without errors."""
        fleet_health = FleetHealth(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=FleetMode.HYBRID,
            machines={
                "nodezero": MachineHealth(
                    name="nodezero",
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                "anvil": MachineHealth(
                    name="anvil",
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            },
            overall_status=MachineStatus.HEALTHY,
            routing_recommendations={"inference": "nodezero"}
        )
        # Should not raise exception
        self.checker.print_health_report(fleet_health)


if __name__ == "__main__":
    unittest.main()
