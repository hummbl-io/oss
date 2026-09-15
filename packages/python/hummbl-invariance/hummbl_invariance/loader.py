"""Read the packaged JSON: the axis catalog and the run schema."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = ["AXES_PATH", "SCHEMA_PATH", "load_axis_catalog", "load_run_schema"]

AXES_PATH = Path(__file__).parent / "data" / "axes.json"
SCHEMA_PATH = Path(__file__).parent / "schemas" / "battery_run.schema.json"


@lru_cache(maxsize=1)
def load_axis_catalog() -> dict[str, Any]:
    """The seven axes, their expected relations, and the verdict thresholds."""
    with AXES_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    keys = [axis["key"] for axis in catalog["axes"]]
    if len(set(keys)) != len(keys):
        raise ValueError("axes.json contains duplicate axis keys")
    return catalog


@lru_cache(maxsize=1)
def load_run_schema() -> dict[str, Any]:
    """JSON Schema for a battery run record.

    Shipped for callers to validate against with their own validator; this
    package stays stdlib-only and does not bundle one.
    """
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)
