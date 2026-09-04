"""HUMMBL Design Token System — single source of truth for fleet visual identity.

Loads tokens from YAML, converts colors between OKLCH/hex/HSL/256-index,
and generates output formats for every rendering surface.
"""

from hummbl_design_tokens.color import (
    hex_to_oklch,
    hex_to_hsl,
    hex_to_256,
    oklch_to_hex,
    hsl_to_hex,
    golden_ratio_color,
    delta_e2000,
    luminance,
    contrast_ratio,
    closest_256,
)
from hummbl_design_tokens.loader import TokenSystem, load_tokens

__all__ = [
    "hex_to_oklch",
    "hex_to_hsl",
    "hex_to_256",
    "oklch_to_hex",
    "hsl_to_hex",
    "golden_ratio_color",
    "delta_e2000",
    "luminance",
    "contrast_ratio",
    "closest_256",
    "TokenSystem",
    "load_tokens",
]
__version__ = "0.1.0"
