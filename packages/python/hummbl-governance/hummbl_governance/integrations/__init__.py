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

"""HUMMBL Governance integrations package.

Currently provides:
    - google_calendar_adapter: stub Google Calendar adapter.
"""

from __future__ import annotations

from hummbl_governance.integrations.google_calendar_adapter import (
    CalendarEntry,
    GoogleCalendarAdapter,
)

__all__ = ["CalendarEntry", "GoogleCalendarAdapter"]
