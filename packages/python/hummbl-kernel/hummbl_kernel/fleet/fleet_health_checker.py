"""
Mission Mode Fleet Health Checker

Monitors health of a user-supplied fleet, provides task routing recommendations,
and implements fallback strategy for hybrid fleet deployment.

No internal fleet names, IPs, URLs, or ports are hardcoded."""

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FleetMode(Enum):
    """Fleet deployment modes"""

    LOCAL = "local"
    HYBRID = "hybrid"
    SINGLE_MACHINE = "single_machine"


class MachineStatus(Enum):
    """Machine health status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MachineHealth:
    """Health status of a fleet machine"""

    name: str
    status: MachineStatus
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)
    services: Dict[str, bool] = field(default_factory=dict)


@dataclass
class FleetHealth:
    """Overall fleet health status"""

    timestamp: str
    mode: FleetMode
    machines: Dict[str, MachineHealth] = field(default_factory=dict)
    overall_status: MachineStatus = MachineStatus.UNKNOWN
    routing_recommendations: Dict[str, str] = field(default_factory=dict)


class FleetHealthChecker:
    """
    Fleet health checker for Mission Mode hybrid deployment

    Monitors a user-supplied fleet, provides task routing recommendations,
    and implements fallback strategy.
    """

    def __init__(
        self,
        mode: FleetMode = FleetMode.HYBRID,
        fleet_config: Optional[Dict] = None,
        task_routing: Optional[Dict] = None,
    ):
        self.mode = mode
        if not fleet_config:
            raise ValueError(
                "FleetHealthChecker requires an explicit fleet_config. "
                "Do not use internal network defaults."
            )
        self.fleet_config = fleet_config

        if not task_routing:
            raise ValueError(
                "FleetHealthChecker requires an explicit task_routing map. "
                "Values must be keys present in fleet_config."
            )
        self.task_routing = task_routing

        # Validate that task_routing values point to known machines.
        for task, machine in task_routing.items():
            if machine not in fleet_config:
                raise ValueError(
                    f"task_routing['{task}'] = '{machine}' is not a key in fleet_config. "
                    "All task routing targets must be defined in fleet_config."
                )

        logger.info(f"Fleet health checker initialized in {mode.value} mode")

    def _check_http_endpoint(self, url: str, timeout: int = 5) -> Tuple[bool, str]:
        """Check if HTTP endpoint is reachable"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                capture_output=True,
                timeout=timeout,
            )
            http_code = result.stdout.decode().strip()
            is_healthy = http_code.startswith("2") or http_code.startswith("3")
            return is_healthy, f"HTTP {http_code}"
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            return False, str(e)

    def _check_ssh_connectivity(self, ssh_alias: str, timeout: int = 5) -> Tuple[bool, str]:
        """Check if SSH connectivity works"""
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", ssh_alias, "echo", "connected"],
                capture_output=True,
                timeout=timeout,
            )
            is_healthy = result.returncode == 0 and b"connected" in result.stdout
            return is_healthy, "connected" if is_healthy else str(result.stderr.decode())
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            return False, str(e)

    def _check_machine(self, machine_name: str) -> MachineHealth:
        """Check health of a specific machine"""
        config = self.fleet_config.get(machine_name)
        if not config:
            return MachineHealth(
                name=machine_name,
                status=MachineStatus.UNKNOWN,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"error": "Machine not in fleet config"},
            )

        services_status = {}
        details = {}

        # Check each service
        for service_name, service_url in config["services"].items():
            is_healthy, status_msg = self._check_http_endpoint(service_url)
            services_status[service_name] = is_healthy
            details[service_name] = status_msg

        # Check SSH connectivity
        ssh_healthy, ssh_msg = self._check_ssh_connectivity(config["ssh_alias"])
        services_status["ssh"] = ssh_healthy
        details["ssh"] = ssh_msg

        # Determine overall status
        # Machine is healthy if SSH and at least one service is healthy
        is_healthy = ssh_healthy and any(services_status.values())
        status = MachineStatus.HEALTHY if is_healthy else MachineStatus.UNHEALTHY

        return MachineHealth(
            name=machine_name,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details,
            services=services_status,
        )

    def check_fleet_health(self) -> FleetHealth:
        """Check health of entire fleet"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check each machine
        machines = {}
        for machine_name in self.fleet_config.keys():
            machines[machine_name] = self._check_machine(machine_name)

        # Determine overall status
        all_healthy = all(m.status == MachineStatus.HEALTHY for m in machines.values())
        any_healthy = any(m.status == MachineStatus.HEALTHY for m in machines.values())

        if all_healthy:
            overall_status = MachineStatus.HEALTHY
        elif any_healthy:
            overall_status = MachineStatus.UNHEALTHY
        else:
            overall_status = MachineStatus.UNHEALTHY

        # Generate routing recommendations based on mode and health
        routing_recommendations = self._generate_routing_recommendations(machines)

        return FleetHealth(
            timestamp=timestamp,
            mode=self.mode,
            machines=machines,
            overall_status=overall_status,
            routing_recommendations=routing_recommendations,
        )

    def _generate_routing_recommendations(
        self, machines: Dict[str, MachineHealth]
    ) -> Dict[str, str]:
        """Generate task routing recommendations based on fleet health.

        Routes each task to its default machine. If that machine is unhealthy,
        falls back to any other healthy machine. All machine names come from the
        user-supplied fleet_config and task_routing maps.
        """
        healthy_machines = [
            name for name, health in machines.items() if health.status == MachineStatus.HEALTHY
        ]
        recommendations = {}

        for task, default_machine in self.task_routing.items():
            if default_machine in healthy_machines:
                recommendations[task] = default_machine
            elif healthy_machines:
                # Fall back to the first healthy machine.
                recommendations[task] = healthy_machines[0]
            else:
                # No healthy machines; keep the default as best-effort.
                recommendations[task] = default_machine

        return recommendations

    def get_optimal_compute(
        self, task_type: str, fleet_health: Optional[FleetHealth] = None
    ) -> str:
        """
        Get optimal compute node for a task type.

        Args:
            task_type: Type of task (inference, file_ops, gpu_workload, etc.)
            fleet_health: Optional fleet health status (will check if not provided)

        Returns:
            Machine identifier from fleet_config.
        """
        if fleet_health is None:
            fleet_health = self.check_fleet_health()

        if task_type in fleet_health.routing_recommendations:
            return fleet_health.routing_recommendations[task_type]

        first_machine = next(iter(self.fleet_config), None)
        if first_machine is None:
            raise ValueError("fleet_config contains no machines")
        return first_machine

    async def monitor_fleet_health(self, interval_seconds: int = 30):
        """Continuously monitor fleet health at specified interval"""
        logger.info(f"Starting fleet health monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                fleet_health = self.check_fleet_health()

                # Log health status
                logger.info(f"Fleet health at {fleet_health.timestamp}:")
                logger.info(f"  Overall: {fleet_health.overall_status.value}")
                logger.info(f"  Mode: {fleet_health.mode.value}")

                for machine_name, machine_health in fleet_health.machines.items():
                    logger.info(f"  {machine_name}: {machine_health.status.value}")
                    for service, status in machine_health.services.items():
                        logger.info(f"    {service}: {status}")

                # Log routing recommendations
                logger.info("  Routing recommendations:")
                for task, machine in fleet_health.routing_recommendations.items():
                    logger.info(f"    {task}: {machine}")

                # Alert if any machine is unhealthy
                for machine_name, machine_health in fleet_health.machines.items():
                    if machine_health.status == MachineStatus.UNHEALTHY:
                        logger.warning(f"ALERT: {machine_name} is unhealthy!")

            except Exception as e:
                logger.error(f"Error checking fleet health: {e}")

            # Wait for next interval
            await asyncio.sleep(interval_seconds)

    def print_health_report(self, fleet_health: FleetHealth):
        """Print a formatted health report"""
        print(f"\n{'=' * 60}")
        print("Fleet Health Report")
        print(f"{'=' * 60}")
        print(f"Timestamp: {fleet_health.timestamp}")
        print(f"Mode: {fleet_health.mode.value}")
        print(f"Overall Status: {fleet_health.overall_status.value}")
        print("\nMachine Status:")

        for machine_name, machine_health in fleet_health.machines.items():
            print(f"  {machine_name}: {machine_health.status.value}")
            for service, status in machine_health.services.items():
                print(f"    {service}: {status}")

        print("\nRouting Recommendations:")
        for task, machine in fleet_health.routing_recommendations.items():
            print(f"  {task}: {machine}")

        print(f"{'=' * 60}\n")


async def main():
    """Example usage of fleet health checker"""
    checker = FleetHealthChecker(mode=FleetMode.HYBRID)

    # Check fleet health once
    fleet_health = checker.check_fleet_health()
    checker.print_health_report(fleet_health)

    # Get optimal compute for a task
    task_type = "inference"
    optimal_compute = checker.get_optimal_compute(task_type, fleet_health)
    print(f"Optimal compute for {task_type}: {optimal_compute}")

    # Optionally start continuous monitoring
    # await checker.monitor_fleet_health(interval_seconds=30)


if __name__ == "__main__":
    asyncio.run(main())
