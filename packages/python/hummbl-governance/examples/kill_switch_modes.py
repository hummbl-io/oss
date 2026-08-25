#!/usr/bin/env python3
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

"""Kill Switch: Demonstrate graduated emergency halt modes.

Four modes from least to most restrictive:
- DISENGAGED: Normal operation
- HALT_NONCRITICAL: Non-critical tasks queued, critical continue
- HALT_ALL: Stop new work, complete in-flight
- EMERGENCY: Immediate halt, preserve state
"""

from hummbl_governance import KillSwitch, KillSwitchMode

ks = KillSwitch()
print(f"Mode: {ks.mode.name} (engaged={ks.engaged})")

# Engage HALT_NONCRITICAL -- safety monitoring continues, non-critical halts
ks.engage(
    mode=KillSwitchMode.HALT_NONCRITICAL,
    reason="Cost budget 90% consumed",
    triggered_by="cost-governor",
    affected_tasks=12,
)
print(f"\nMode: {ks.mode.name}")

# Critical tasks still allowed
allowed = ks.check_task_allowed("safety_monitoring")
print(f"  safety_monitoring allowed: {allowed}")

# Non-critical tasks blocked
allowed = ks.check_task_allowed("data_enrichment")
print(f"  data_enrichment allowed:   {allowed}")

# Escalate to EMERGENCY
ks.engage(
    mode=KillSwitchMode.EMERGENCY,
    reason="Anomalous token burn detected",
    triggered_by="anomaly-detector",
    affected_tasks=50,
)
print(f"\nMode: {ks.mode.name}")

# Even critical tasks blocked in EMERGENCY (except kill_switch_itself)
allowed = ks.check_task_allowed("safety_monitoring")
print(f"  safety_monitoring allowed: {allowed}")
allowed = ks.check_task_allowed("kill_switch_itself")
print(f"  kill_switch_itself allowed: {allowed}")

# Disengage
ks.disengage(reason="Budget replenished", triggered_by="operator")
print(f"\nMode: {ks.mode.name} (engaged={ks.engaged})")

# Show history
print(f"\nEvent history ({len(ks.get_history())} events):")
for event in ks.get_history():
    print(f"  {event.mode.name}: {event.reason}")
