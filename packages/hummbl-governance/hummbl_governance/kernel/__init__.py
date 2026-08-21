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

"""HUMMBL Governance Kernel — Minimal substrate for AI fleet governance.

The Kernel is not a role. It is the operating system of the fleet — the shared
substrate that guarantees every agent action is observable, every observation is
checkable, and every check is against empirical law.

Eleven invariants (K1-K11) and their engines provide the foundation for AI officer
roles, compliance enforcement, and scaling-law governance. K1-K8 are enforced on
every receipt path; K9-K11 are enum-defined, schema-backed, and exposed through
Kernel validation methods (mandatory at call sites that invoke them).

All engines are stdlib-only. No vendor-specific APIs, models, or runtimes.

Usage:
    from hummbl_governance.kernel import Kernel
    kernel = Kernel.boot()
    receipt = kernel.receipt.create(agent_id="devin", ...)
    violations = kernel.law.evaluate(receipt)

__dissect__
-----------
- surface: kernel (governance operating system)
- dependencies: bus_writer_core (for receipt storage), schema_validator (for validation)
- receipts: KERNEL_BOOT, KERNEL_HEALTH, KERNEL_PANIC
- telemetry: engine health, invariant checks, role status
- imports-stdlib: json, hashlib, hmac, os, pathlib, re, datetime, typing
- imports-internal: bus_writer_core (receipt storage), cognition/schema_validator
- imports-third-party: none
- mutable-state: identity registry, role registry, sequence counters
- feature-flags: KERNEL_BOOT_ON_IMPORT (default: False)
- side-effects: writes to _state/kernel/ (receipts, registry, health)
- thread-safe: TBD — engines use file locking via bus_writer patterns
- async: no
"""

from __future__ import annotations

__version__ = "1.2.2"
__spec_version__ = "1.2.2"

from .kernel import Kernel
from .invariants import KernelInvariant, KernelPanic
from .receipt_engine import Receipt, ReceiptEngine
from .law_engine import LawEngine
from .identity_engine import IdentityEngine
from .sequence_engine import SequenceEngine
from .evidence_engine import EvidenceEngine
from .authority_engine import AuthorityEngine
from .schedule_engine import ScheduleEngine
from .doctrine_engine import DoctrineEngine, Stage

__all__ = [
    "Kernel",
    "KernelInvariant",
    "KernelPanic",
    "Receipt",
    "ReceiptEngine",
    "LawEngine",
    "IdentityEngine",
    "SequenceEngine",
    "EvidenceEngine",
    "AuthorityEngine",
    "ScheduleEngine",
    "DoctrineEngine",
    "Stage",
]
