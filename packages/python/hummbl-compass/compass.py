"""Backward-compatible root wrapper re-exporting hummbl_compass.compass."""
from __future__ import annotations

import sys
from hummbl_compass.compass import (
    DOMAIN_KEYWORDS,
    LAYER_KEYWORDS,
    Compass,
    Repo,
    RouteResult,
    _fmt_repo,
    _load_topology,
    main,
)

__all__ = [
    "DOMAIN_KEYWORDS",
    "LAYER_KEYWORDS",
    "Compass",
    "Repo",
    "RouteResult",
    "_fmt_repo",
    "_load_topology",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
