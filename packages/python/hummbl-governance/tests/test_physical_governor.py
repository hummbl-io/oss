# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from hummbl_governance.physical_governor import (
    KinematicGovernor,
    PhysicalSafetyMode,
    pHRISafetyMonitor,
)


def test_kinematic_governor_enforces_velocity():
    gov = KinematicGovernor(max_velocity=1.0)
    # Within limit
    assert gov.check_motion(velocity=0.5)["allowed"] is True
    # Exceeds limit
    result = gov.check_motion(velocity=1.5)
    assert result["allowed"] is False
    assert "Velocity 1.5 exceeds limit 1.0" in result["reason"]

def test_kinematic_governor_enforces_force():
    gov = KinematicGovernor(max_force=50.0)
    assert gov.check_motion(force=30.0)["allowed"] is True
    result = gov.check_motion(force=60.0)
    assert result["allowed"] is False
    assert "Force 60.0 exceeds limit 50.0" in result["reason"]

def test_phri_monitor_detects_human_proximity():
    monitor = pHRISafetyMonitor(min_distance=0.5)
    # Safe distance
    assert monitor.check_safety(distance=1.0)["mode"] == PhysicalSafetyMode.NORMAL
    # Close proximity -> Caution
    assert monitor.check_safety(distance=0.4)["mode"] == PhysicalSafetyMode.CAUTION
    # Critical proximity -> Emergency
    assert monitor.check_safety(distance=0.1)["mode"] == PhysicalSafetyMode.EMERGENCY

def test_phri_monitor_collision_detection():
    monitor = pHRISafetyMonitor()
    result = monitor.check_safety(collision=True)
    assert result["mode"] == PhysicalSafetyMode.EMERGENCY
    assert "Collision detected" in result["reason"]

def test_kinematic_governor_dynamic_scaling():
    gov = KinematicGovernor(max_velocity=1.0)
    assert gov.get_scaled_velocity(PhysicalSafetyMode.NORMAL) == 1.0
    assert gov.get_scaled_velocity(PhysicalSafetyMode.CAUTION) == 0.25
    assert gov.get_scaled_velocity(PhysicalSafetyMode.EMERGENCY) == 0.0
