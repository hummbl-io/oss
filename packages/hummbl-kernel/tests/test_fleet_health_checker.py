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
        self.primary_name = "primary"
        self.gpu_name = "gpu"
        self.test_config = {
            self.primary_name: {
                "tailscale_ip": "100.x.x.x",
                "hostname": "primary",
                "ssh_alias": "primary",
                "services": {
                    "ollama": "http://100.x.x.x:11434/api/tags",
                    "bus": "http://100.x.x.x:18790/health"
                }
            },
            self.gpu_name: {
                "tailscale_ip": "100.x.x.x",
                "hostname": "gpu",
                "ssh_alias": "gpu",
                "services": {
                    "gitea": "https://example.com",
                    "ollama": "http://localhost:11434/api/tags"
                }
            }
        }
        self.test_routing = {
            "inference": self.primary_name,
            "file_ops": self.gpu_name,
            "gpu_workload": self.gpu_name,
            "document_generation": self.primary_name,
            "database_ops": self.gpu_name,
            "storage_ops": self.gpu_name,
            "compliance_validation": self.primary_name,
            "evidence_collection": self.gpu_name,
            "report_generation": self.primary_name,
            "audit_trail_storage": self.gpu_name
        }
        self.checker = FleetHealthChecker(
            mode=FleetMode.HYBRID,
            fleet_config=self.test_config,
            task_routing=self.test_routing,
        )

    def test_checker_initialization(self):
        """Health checker should initialize with correct mode."""
        self.assertEqual(self.checker.mode, FleetMode.HYBRID)
        self.assertIsNotNone(self.checker.fleet_config)
        self.assertIn(self.primary_name, self.checker.fleet_config)
        self.assertIn(self.gpu_name, self.checker.fleet_config)

    def test_requires_explicit_config(self):
        """Health checker should require explicit fleet_config and task_routing."""
        with self.assertRaises(ValueError):
            FleetHealthChecker()
        with self.assertRaises(ValueError):
            FleetHealthChecker(fleet_config=self.test_config)

    def test_primary_config(self):
        """Primary machine should be configured with correct services."""
        primary_config = self.checker.fleet_config[self.primary_name]
        self.assertEqual(primary_config["hostname"], self.primary_name)
        self.assertEqual(primary_config["ssh_alias"], self.primary_name)
        self.assertIn("ollama", primary_config["services"])
        self.assertIn("bus", primary_config["services"])

    def test_gpu_config(self):
        """GPU machine should be configured with correct services."""
        gpu_config = self.checker.fleet_config[self.gpu_name]
        self.assertEqual(gpu_config["hostname"], self.gpu_name)
        self.assertEqual(gpu_config["ssh_alias"], self.gpu_name)
        self.assertIn("gitea", gpu_config["services"])
        self.assertIn("ollama", gpu_config["services"])

    def test_task_routing_config(self):
        """Task routing should be configured."""
        self.assertIn("inference", self.checker.task_routing)
        self.assertIn("gpu_workload", self.checker.task_routing)
        self.assertIn("file_ops", self.checker.task_routing)
        self.assertEqual(self.checker.task_routing["inference"], self.primary_name)
        self.assertEqual(self.checker.task_routing["gpu_workload"], self.gpu_name)

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
            is_healthy, msg = self.checker._check_ssh_connectivity(self.primary_name)
            self.assertTrue(is_healthy)
            self.assertEqual(msg, "connected")

    def test_check_ssh_connectivity_failure(self):
        """SSH connectivity check should fail."""
        with patch.object(self.checker, '_check_ssh_connectivity', return_value=(False, "Connection refused")):
            is_healthy, msg = self.checker._check_ssh_connectivity(self.primary_name)
            self.assertFalse(is_healthy)
            self.assertEqual(msg, "Connection refused")

    def test_check_machine_healthy(self):
        """Machine check should return healthy status when all checks pass."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(True, "HTTP 200")):
            with patch.object(self.checker, '_check_ssh_connectivity', return_value=(True, "connected")):
                health = self.checker._check_machine(self.primary_name)
                self.assertEqual(health.status, MachineStatus.HEALTHY)
                self.assertEqual(health.name, self.primary_name)
                self.assertIsNotNone(health.timestamp)

    def test_check_machine_unhealthy(self):
        """Machine check should return unhealthy status when checks fail."""
        with patch.object(self.checker, '_check_http_endpoint', return_value=(False, "HTTP 404")):
            with patch.object(self.checker, '_check_ssh_connectivity', return_value=(False, "Connection refused")):
                health = self.checker._check_machine(self.primary_name)
                self.assertEqual(health.status, MachineStatus.UNHEALTHY)
                self.assertEqual(health.name, self.primary_name)

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
            def mock(name):
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            mock_check.side_effect = mock

            fleet_health = self.checker.check_fleet_health()
            self.assertEqual(fleet_health.overall_status, MachineStatus.HEALTHY)
            self.assertEqual(fleet_health.mode, FleetMode.HYBRID)
            self.assertEqual(len(fleet_health.machines), 2)

    def test_fleet_health_degraded(self):
        """Fleet health should be degraded when one machine is unhealthy."""
        def mock_check_machine(name):
            if name == self.primary_name:
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
            def mock(name):
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            mock_check.side_effect = mock

            fleet_health = self.checker.check_fleet_health()
            self.assertIn("inference", fleet_health.routing_recommendations)
            self.assertIn("gpu_workload", fleet_health.routing_recommendations)

    def test_routing_recommendations_fallback(self):
        """Routing should fallback when primary node is unhealthy."""
        def mock_check_machine(name):
            if name == self.primary_name:
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
            # Inference should fallback to gpu when primary is unhealthy
            self.assertEqual(fleet_health.routing_recommendations["inference"], self.gpu_name)

    def test_get_optimal_compute(self):
        """Optimal compute should return recommended node."""
        with patch.object(self.checker, 'check_fleet_health') as mock_health:
            mock_health.return_value = MagicMock(
                routing_recommendations={"inference": self.primary_name}
            )
            optimal = self.checker.get_optimal_compute("inference")
            self.assertEqual(optimal, self.primary_name)

    def test_get_optimal_compute_with_health_param(self):
        """Optimal compute should use provided health status."""
        fleet_health = MagicMock(
            routing_recommendations={"gpu_workload": self.gpu_name}
        )
        optimal = self.checker.get_optimal_compute("gpu_workload", fleet_health)
        self.assertEqual(optimal, self.gpu_name)

    def test_local_mode_routing(self):
        """Local mode should route all tasks to the configured single machine."""
        local_routing = {task: self.gpu_name for task in self.test_routing}
        local_checker = FleetHealthChecker(
            mode=FleetMode.LOCAL,
            fleet_config=self.test_config,
            task_routing=local_routing,
        )
        with patch.object(local_checker, '_check_machine') as mock_check:
            def mock(name):
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            mock_check.side_effect = mock

            fleet_health = local_checker.check_fleet_health()
            for task, machine in fleet_health.routing_recommendations.items():
                self.assertEqual(machine, self.gpu_name)

    def test_single_machine_mode_routing(self):
        """Single-machine mode should route all tasks to the designated machine."""
        single_routing = {task: self.primary_name for task in self.test_routing}
        single_checker = FleetHealthChecker(
            mode=FleetMode.SINGLE_MACHINE,
            fleet_config=self.test_config,
            task_routing=single_routing,
        )
        with patch.object(single_checker, '_check_machine') as mock_check:
            def mock(name):
                return MachineHealth(
                    name=name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            mock_check.side_effect = mock

            fleet_health = single_checker.check_fleet_health()
            for task, machine in fleet_health.routing_recommendations.items():
                self.assertEqual(machine, self.primary_name)

    def test_print_health_report(self):
        """Health report should print without errors."""
        fleet_health = FleetHealth(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=FleetMode.HYBRID,
            machines={
                self.primary_name: MachineHealth(
                    name=self.primary_name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ),
                self.gpu_name: MachineHealth(
                    name=self.gpu_name,
                    status=MachineStatus.HEALTHY,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            },
            overall_status=MachineStatus.HEALTHY,
            routing_recommendations={"inference": self.primary_name}
        )
        # Should not raise exception
        self.checker.print_health_report(fleet_health)


if __name__ == "__main__":
    unittest.main()
