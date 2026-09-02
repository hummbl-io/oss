# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Allow `python -m hummbl_lattice` as an alias for the CLI."""

import sys

from hummbl_lattice.cli import main

if __name__ == "__main__":
    sys.exit(main())
