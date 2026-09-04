"""Color space conversions for HUMMBL design tokens.

All conversions use stdlib only (math). No third-party dependencies.

Supported conversions:
  hex <-> HSL <-> OKLCH
  hex -> 256-color index
  hex -> ANSI 16-color index

Validation:
  delta_e2000 (CIEDE2000 color difference)
  luminance (relative)
  contrast_ratio (WCAG)
  golden_ratio_color (agent identity color generation)
"""

from __future__ import annotations

import math
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class HSL(NamedTuple):
    h: float  # 0-360
    s: float  # 0-100
    l: float  # 0-100


class OKLCH(NamedTuple):
    l: float  # 0-100 (lightness)
    c: float  # 0-~150 (chroma)
    h: float  # 0-360 (hue)


class RGB(NamedTuple):
    r: float  # 0-1
    g: float  # 0-1
    b: float  # 0-1


# ---------------------------------------------------------------------------
# hex <-> RGB
# ---------------------------------------------------------------------------


def hex_to_rgb(hex_str: str) -> RGB:
    """Convert #RRGGBB to linear RGB (0-1 floats)."""
    h = hex_str.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Expected 6-digit hex, got {hex_str!r}")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return RGB(r, g, b)


def rgb_to_hex(rgb: RGB) -> str:
    """Convert RGB (0-1 floats) to #RRGGBB."""
    r = max(0, min(255, round(rgb.r * 255)))
    g = max(0, min(255, round(rgb.g * 255)))
    b = max(0, min(255, round(rgb.b * 255)))
    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# sRGB <-> linear RGB (for OKLCH)
# ---------------------------------------------------------------------------


def _srgb_to_linear(c: float) -> float:
    """Inverse sRGB gamma encoding."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    """Forward sRGB gamma encoding."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1 / 2.4)) - 0.055


# ---------------------------------------------------------------------------
# linear RGB <-> LMS (for OKLab/OKLCH)
# ---------------------------------------------------------------------------

# OKLab matrices from Björn Ottosson's paper (2020)
_M_LMS_FROM_RGB = [
    [0.4122214708, 0.5363325363, 0.0514459929],
    [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005],
]

_M_RGB_FROM_LMS = [
    [4.0767416621, -3.3077115913, 0.2309699292],
    [-1.2684380, 2.6097574, -0.3413194],
    [-0.00419609, -0.70341861, 1.7076147],
]

_M_OKLAB_FROM_LMS = [
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
]

_M_LMS_FROM_OKLAB = [
    [1.0, 0.3963377774, 0.2158037573],
    [1.0, -0.1055613458, -0.0638541728],
    [1.0, -0.0894841775, -1.2914855480],
]


def _matmul3(m: list[list[float]], v: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


# ---------------------------------------------------------------------------
# hex <-> HSL
# ---------------------------------------------------------------------------


def hex_to_hsl(hex_str: str) -> HSL:
    """Convert #RRGGBB to HSL (0-360, 0-100, 0-100)."""
    r, g, b = hex_to_rgb(hex_str)
    mx = max(r, g, b)
    mn = min(r, g, b)
    delta = mx - mn
    l = (mx + mn) / 2.0 * 100.0
    if delta == 0:
        return HSL(0.0, 0.0, l)
    s = delta / (1 - abs(2 * l / 100.0 - 1)) * 100.0
    if mx == r:
        h = 60.0 * (((g - b) / delta) % 6)
    elif mx == g:
        h = 60.0 * ((b - r) / delta + 2)
    else:
        h = 60.0 * ((r - g) / delta + 4)
    return HSL(h, s, l)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (0-360, 0-100, 0-100) to #RRGGBB."""
    s = s / 100.0
    l = l / 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r1, g1, b1 = c, x, 0
    elif h < 120:
        r1, g1, b1 = x, c, 0
    elif h < 180:
        r1, g1, b1 = 0, c, x
    elif h < 240:
        r1, g1, b1 = 0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    r = round((r1 + m) * 255)
    g = round((g1 + m) * 255)
    b = round((b1 + m) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# hex <-> OKLCH
# ---------------------------------------------------------------------------


def hex_to_oklch(hex_str: str) -> OKLCH:
    """Convert #RRGGBB to OKLCH (L: 0-100, C: 0-~150, H: 0-360)."""
    r, g, b = hex_to_rgb(hex_str)
    # sRGB -> linear
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)
    # linear RGB -> LMS
    l, m, s = _matmul3(_M_LMS_FROM_RGB, (rl, gl, bl))
    # non-linear cube root
    l_ = math.copysign(abs(l) ** (1 / 3), l) if l != 0 else 0.0
    m_ = math.copysign(abs(m) ** (1 / 3), m) if m != 0 else 0.0
    s_ = math.copysign(abs(s) ** (1 / 3), s) if s != 0 else 0.0
    # LMS -> OKLab
    lab_l, lab_a, lab_b = _matmul3(_M_OKLAB_FROM_LMS, (l_, m_, s_))
    # OKLab -> OKLCH
    L = lab_l * 100.0
    C = math.sqrt(lab_a ** 2 + lab_b ** 2) * 100.0
    H = math.degrees(math.atan2(lab_b, lab_a)) % 360.0
    return OKLCH(L, C, H)


def oklch_to_hex(L: float, C: float, H: float) -> str:
    """Convert OKLCH (L: 0-100, C: 0-~150, H: 0-360) to #RRGGBB."""
    lab_l = L / 100.0
    h_rad = math.radians(H)
    lab_a = (C / 100.0) * math.cos(h_rad)
    lab_b = (C / 100.0) * math.sin(h_rad)
    # OKLab -> LMS
    l_, m_, s_ = _matmul3(_M_LMS_FROM_OKLAB, (lab_l, lab_a, lab_b))
    # cube
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3
    # LMS -> linear RGB
    rl, gl, bl = _matmul3(_M_RGB_FROM_LMS, (l, m, s))
    # linear -> sRGB
    r = _linear_to_srgb(max(0.0, min(1.0, rl)))
    g = _linear_to_srgb(max(0.0, min(1.0, gl)))
    b = _linear_to_srgb(max(0.0, min(1.0, bl)))
    return rgb_to_hex(RGB(r, g, b))


# ---------------------------------------------------------------------------
# 256-color and ANSI 16-color
# ---------------------------------------------------------------------------


def hex_to_256(hex_str: str) -> int:
    """Convert hex to nearest xterm 256-color index (16-255)."""
    r, g, b = hex_to_rgb(hex_str)
    # 6x6x6 color cube starting at index 16
    # levels: 0, 95, 135, 175, 215, 255
    levels = [0, 95, 135, 175, 215, 255]
    ri = min(range(6), key=lambda i: abs(levels[i] - r * 255))
    gi = min(range(6), key=lambda i: abs(levels[i] - g * 255))
    bi = min(range(6), key=lambda i: abs(levels[i] - b * 255))
    return 16 + 36 * ri + 6 * gi + bi


def closest_256(hex_str: str) -> int:
    """Alias for hex_to_256."""
    return hex_to_256(hex_str)


_ANSI_16_MAP = {
    "black": 0, "red": 1, "green": 2, "yellow": 3,
    "blue": 4, "magenta": 5, "cyan": 6, "white": 7,
    "bright_black": 8, "bright_red": 9, "bright_green": 10,
    "bright_yellow": 11, "bright_blue": 12, "bright_magenta": 13,
    "bright_cyan": 14, "bright_white": 15,
}

_ANSI_16_HEX = {
    0: "#000000", 1: "#800000", 2: "#008000", 3: "#808000",
    4: "#000080", 5: "#800080", 6: "#008080", 7: "#C0C0C0",
    8: "#808080", 9: "#FF0000", 10: "#00FF00", 11: "#FFFF00",
    12: "#0000FF", 13: "#FF00FF", 14: "#00FFFF", 15: "#FFFFFF",
}


def hex_to_ansi16(hex_str: str) -> int:
    """Convert hex to nearest ANSI 16-color index (0-15)."""
    target = hex_to_rgb(hex_str)
    best = 0
    best_dist = float("inf")
    for idx, ref_hex in _ANSI_16_HEX.items():
        ref = hex_to_rgb(ref_hex)
        dist = sum((a - b) ** 2 for a, b in zip(target, ref))
        if dist < best_dist:
            best_dist = dist
            best = idx
    return best


# ---------------------------------------------------------------------------
# Validation: WCAG contrast, luminance, CIEDE2000
# ---------------------------------------------------------------------------


def luminance(hex_str: str) -> float:
    """Relative luminance per WCAG 2.x (0-1)."""
    r, g, b = hex_to_rgb(hex_str)
    def chan(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG contrast ratio between two hex colors (1-21)."""
    l1 = luminance(hex1)
    l2 = luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def delta_e2000(hex1: str, hex2: str) -> float:
    """CIEDE2000 color difference between two hex colors.

    Uses CIE Lab internally. Lower = more similar. <1 = imperceptible, >5 = clearly noticeable.
    """
    # Convert hex -> sRGB -> linear RGB -> XYZ -> Lab
    lab1 = _hex_to_lab(hex1)
    lab2 = _hex_to_lab(hex2)
    return _ciede2000_lab(lab1, lab2)


def _hex_to_lab(hex_str: str) -> tuple[float, float, float]:
    """hex -> CIE Lab (D65 illuminant)."""
    r, g, b = hex_to_rgb(hex_str)
    # sRGB -> linear
    rl = _srgb_to_linear(r)
    gl = _srgb_to_linear(g)
    bl = _srgb_to_linear(b)
    # linear RGB -> XYZ (D65, sRGB matrix)
    x = 0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl
    y = 0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl
    z = 0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl
    # Normalize by D65 white point
    xn, yn, zn = 0.95047, 1.0, 1.08883
    fx = _lab_f(x / xn)
    fy = _lab_f(y / yn)
    fz = _lab_f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return (L, a, b)


def _lab_f(t: float) -> float:
    delta = 6 / 29
    if t > delta ** 3:
        return t ** (1 / 3)
    return t / (3 * delta ** 2) + 4 / 29


def _ciede2000_lab(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
    """CIEDE2000 implementation on Lab values."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Step 1: Lab -> L'C'h'
    C1 = math.sqrt(a1 ** 2 + b1 ** 2)
    C2 = math.sqrt(a2 ** 2 + b2 ** 2)
    C_bar = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(C_bar ** 7 / (C_bar ** 7 + 25 ** 7)))
    a1p = (1 + G) * a1
    a2p = (1 + G) * a2
    C1p = math.sqrt(a1p ** 2 + b1 ** 2)
    C2p = math.sqrt(a2p ** 2 + b2 ** 2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360

    # Step 2: deltas
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        diff = h2p - h1p
        if abs(diff) <= 180:
            dhp = diff
        elif diff > 180:
            dhp = diff - 360
        else:
            dhp = diff + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))

    # Step 3: weighting
    L_bar_p = (L1 + L2) / 2
    C_bar_p = (C1p + C2p) / 2
    if C1p * C2p == 0:
        h_bar_p = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        h_bar_p = (h1p + h2p) / 2
    elif (h1p + h2p) < 360:
        h_bar_p = (h1p + h2p + 360) / 2
    else:
        h_bar_p = (h1p + h2p - 360) / 2

    T = (1 - 0.17 * math.cos(math.radians(h_bar_p - 30))
         + 0.24 * math.cos(math.radians(2 * h_bar_p))
         + 0.32 * math.cos(math.radians(3 * h_bar_p + 6))
         - 0.20 * math.cos(math.radians(4 * h_bar_p - 63)))

    d_theta = 30 * math.exp(-((h_bar_p - 275) / 25) ** 2)
    R_C = 2 * math.sqrt(C_bar_p ** 7 / (C_bar_p ** 7 + 25 ** 7))
    S_L = 1 + (0.015 * (L_bar_p - 50) ** 2) / math.sqrt(20 + (L_bar_p - 50) ** 2)
    S_C = 1 + 0.045 * C_bar_p
    S_H = 1 + 0.015 * C_bar_p * T
    R_T = -math.sin(math.radians(2 * d_theta)) * R_C

    kL = kC = kH = 1.0
    dE = math.sqrt(
        (dLp / (kL * S_L)) ** 2
        + (dCp / (kC * S_C)) ** 2
        + (dHp / (kH * S_H)) ** 2
        + R_T * (dCp / (kC * S_C)) * (dHp / (kH * S_H))
    )
    return dE


# ---------------------------------------------------------------------------
# Agent identity color generation
# ---------------------------------------------------------------------------

_GOLDEN_RATIO = (1 + math.sqrt(5)) / 2 - 1  # 0.618...


def golden_ratio_color(index: int, saturation: float = 85.0, lightness: float = 65.0) -> str:
    """Generate a golden-ratio-spaced HSL color for agent identity.

    Args:
        index: Agent index (0-based). Hue = (index * 360 * golden_ratio) % 360.
        saturation: HSL saturation (0-100). Default 85%.
        lightness: HSL lightness (0-100). Default 65%.

    Returns:
        Hex color string (#RRGGBB).
    """
    hue = (index * 360.0 * _GOLDEN_RATIO) % 360.0
    return hsl_to_hex(hue, saturation, lightness)


def golden_ratio_color_for_name(name: str, saturation: float = 85.0, lightness: float = 65.0) -> str:
    """Generate a golden-ratio color from an agent name.

    Uses a simple hash to determine the index, then applies golden ratio spacing.
    """
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return golden_ratio_color(h % 360, saturation, lightness)
