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

"""Physical Governor — safety and kinematic constraints for physical AI.

Provides monitoring for biomechanical physical-AI alignment (pHRI), 
enforcing limits on velocity, force, and proximity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class PhysicalSafetyMode(Enum):
    """Graduated safety modes for physical interaction."""
    NORMAL = "normal"      # Full performance within limits
    CAUTION = "caution"    # Performance restricted (e.g. human nearby)
    EMERGENCY = "emergency" # Immediate halt (e.g. collision or critical proximity)


@dataclass(frozen=True)
class KinematicGovernor:
    """Enforces physical motion constraints."""
    max_velocity: float = 1.0  # m/s
    max_force: float = 50.0    # Newtons
    max_jerk: float = 5.0      # m/s^3
    
    # Scaling factors for different safety modes
    caution_scale: float = 0.25
    
    def check_motion(self, 
                     velocity: Optional[float] = None, 
                     force: Optional[float] = None, 
                     jerk: Optional[float] = None) -> Dict[str, Any]:
        """Check if proposed motion parameters are within limits."""
        if velocity is not None and velocity > self.max_velocity:
            return {"allowed": False, "reason": f"Velocity {velocity} exceeds limit {self.max_velocity}"}
            
        if force is not None and force > self.max_force:
            return {"allowed": False, "reason": f"Force {force} exceeds limit {self.max_force}"}
            
        if jerk is not None and jerk > self.max_jerk:
            return {"allowed": False, "reason": f"Jerk {jerk} exceeds limit {self.max_jerk}"}
            
        return {"allowed": True, "reason": "Within kinematic limits"}

    def get_scaled_velocity(self, mode: PhysicalSafetyMode) -> float:
        """Get the effective velocity limit for a given safety mode."""
        if mode == PhysicalSafetyMode.EMERGENCY:
            return 0.0
        if mode == PhysicalSafetyMode.CAUTION:
            return self.max_velocity * self.caution_scale
        return self.max_velocity


@dataclass
class pHRISafetyMonitor:
    """Monitors biomechanical physical-AI human-robot interaction (pHRI)."""
    min_distance: float = 0.5  # meters
    critical_distance: float = 0.1 # meters
    
    def check_safety(self, 
                     distance: Optional[float] = None, 
                     collision: bool = False) -> Dict[str, Any]:
        """Evaluate current safety mode based on sensor data."""
        if collision:
            return {"mode": PhysicalSafetyMode.EMERGENCY, "reason": "Collision detected"}
            
        if distance is not None:
            if distance <= self.critical_distance:
                return {"mode": PhysicalSafetyMode.EMERGENCY, "reason": f"Critical proximity breach: {distance}m"}
            if distance <= self.min_distance:
                return {"mode": PhysicalSafetyMode.CAUTION, "reason": f"Human proximity detected: {distance}m"}
                
        return {"mode": PhysicalSafetyMode.NORMAL, "reason": "No safety violations"}
