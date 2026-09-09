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

"""Shared helpers for kernel tests.

K3 fail-closed enforcement requires an IdentityEngine before receipts
can be created. These helpers wire one up automatically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hummbl_governance.kernel import IdentityEngine, ReceiptEngine


def make_receipt_engine(
    state_dir: Path,
    agent_ids: tuple[str, ...] = ("test-agent",),
    **kwargs: Any,
) -> ReceiptEngine:
    """Create a ReceiptEngine with an IdentityEngine wired in.

    Registers each agent_id in the IdentityEngine, then returns a
    ReceiptEngine with the identity_engine wired. Forward any
    ReceiptEngine kwargs (e.g. signing_secret) via **kwargs.
    """
    identity = IdentityEngine(state_dir)
    for aid in agent_ids:
        if identity.resolve(aid) is None:
            identity.register(agent_id=aid)
    return ReceiptEngine(state_dir, identity_engine=identity, **kwargs)
