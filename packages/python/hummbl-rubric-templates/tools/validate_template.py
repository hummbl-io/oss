#!/usr/bin/env python3
"""Backward-compatible CLI wrapper re-exporting hummbl_rubric_templates.validate_template."""
from __future__ import annotations

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from hummbl_rubric_templates.validate_template import (
    load_yaml_file,
    main,
    validate_hard_gates,
    validate_parameters,
    validate_required_outputs,
    validate_template,
    validate_weighted_dimensions,
)

__all__ = [
    "load_yaml_file",
    "main",
    "validate_hard_gates",
    "validate_parameters",
    "validate_required_outputs",
    "validate_template",
    "validate_weighted_dimensions",
]

if __name__ == "__main__":
    main()
