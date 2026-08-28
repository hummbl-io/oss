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

"""hummbl-lattice — domain-specific reasoning operator lattices.

Tools for building, validating, and rating Domain120 lattices:
domain-specific reasoning operator sets that generalize TRIZ's
40-principle structure across arbitrary domains of practice.

Quick start::

    from hummbl_lattice import Lattice, LatticeValidator, KappaCalculator

    # Validate a lattice
    validator = LatticeValidator()
    report = validator.validate("my_lattice.json")

    # Compute inter-rater reliability
    kappa = KappaCalculator()
    result = kappa.compute("ratings.csv")

    # Build a lattice programmatically
    lattice = Lattice(domain="Structural Engineering")
    lattice.add_operator(
        code="IN01",
        name="Seismic Load Path Inversion",
        family="IN",
        definition="Instead of designing for expected loads, trace the failure path backward.",
        base120_ancestor="IN3",
    )

Apache 2.0. Copyright 2026 HUMMBL, LLC.
"""

from __future__ import annotations

from hummbl_lattice.models import Lattice, LatticeOperator, CompositionMatrix
from hummbl_lattice.validator import LatticeValidator, ValidationReport
from hummbl_lattice.kappa import KappaCalculator, KappaResult

__version__ = "0.1.0"

__all__ = [
    "Lattice",
    "LatticeOperator",
    "CompositionMatrix",
    "LatticeValidator",
    "ValidationReport",
    "KappaCalculator",
    "KappaResult",
    "__version__",
]
