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

import tomllib
from pathlib import Path

import hummbl_governance

def test_init_exports_all_present():
    """Verify all symbols in __all__ are importable and present in the module."""
    for symbol in hummbl_governance.__all__:
        assert hasattr(hummbl_governance, symbol), f"Symbol {symbol} listed in __all__ but missing from module"

def test_version_canonical():
    """Verify version matches current release."""
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    assert hummbl_governance.__version__ == pyproject["project"]["version"]

def test_new_primitives_exported():
    """Verify v0.4.0, v0.5.0, and v0.6.0 primitives are exported."""
    assert "KinematicGovernor" in hummbl_governance.__all__
    assert "pHRISafetyMonitor" in hummbl_governance.__all__
    assert "PhysicalSafetyMode" in hummbl_governance.__all__
    assert "eal_validate" in hummbl_governance.__all__
    assert "LamportTimestamp" in hummbl_governance.__all__


def test_kernel_primitives_exported():
    """Verify Kernel primitives are exported."""
    assert "Kernel" in hummbl_governance.__all__
    assert "KernelInvariant" in hummbl_governance.__all__
    assert "KernelPanic" in hummbl_governance.__all__
    assert "Receipt" in hummbl_governance.__all__
    assert "ReceiptEngine" in hummbl_governance.__all__
    assert "LawEngine" in hummbl_governance.__all__
    assert "IdentityEngine" in hummbl_governance.__all__
    assert "SequenceEngine" in hummbl_governance.__all__
    assert "EvidenceEngine" in hummbl_governance.__all__
    assert "AuthorityEngine" in hummbl_governance.__all__
    assert "ScheduleEngine" in hummbl_governance.__all__
    assert "DoctrineEngine" in hummbl_governance.__all__
    assert "Stage" in hummbl_governance.__all__
