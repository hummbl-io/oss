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

"""hummbl-lattice CLI.

Usage::

    hummbl-lattice validate <lattice.json>
    hummbl-lattice kappa <ratings.csv>
    hummbl-lattice info <lattice.json>
"""

from __future__ import annotations

import sys

from hummbl_lattice.kappa import KappaCalculator
from hummbl_lattice.models import Lattice
from hummbl_lattice.validator import LatticeValidator


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 0

    command = args[0]

    if command == "validate":
        if len(args) < 2:
            print("Usage: hummbl-lattice validate <lattice.json>")
            return 1
        validator = LatticeValidator()
        report = validator.validate(args[1])
        print(report.to_text())
        return 0 if report.ratification_ready else 1

    elif command == "kappa":
        if len(args) < 2:
            print("Usage: hummbl-lattice kappa <ratings.csv>")
            return 1
        calc = KappaCalculator()
        result = calc.compute(args[1])
        print(result.to_text())
        return 0 if result.threshold_passed else 1

    elif command == "info":
        if len(args) < 2:
            print("Usage: hummbl-lattice info <lattice.json>")
            return 1
        lattice = Lattice.from_json(args[1])
        print(f"Domain:              {lattice.domain}")
        print(f"Version:             {lattice.version}")
        print(f"Author:              {lattice.author or '(none)'}")
        print(f"Language:            {lattice.language}")
        print(f"Operators:           {lattice.operator_count}")
        print(f"Family counts:       {lattice.family_counts}")
        print(f"Missing families:    {lattice.missing_families or 'none'}")
        print(f"Admissible pairs:    {lattice.composition_matrix.admissible_count}")
        print(f"Cross-maps:          {len(lattice.cross_maps)}")
        print(f"SHA-256:             {lattice.lattice_hash}")
        return 0

    else:
        print(f"Unknown command: {command}")
        print("Commands: validate, kappa, info")
        return 1


if __name__ == "__main__":
    sys.exit(main())
