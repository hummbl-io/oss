"""SVG renderers for watch faces, livery swatches, and failure state visuals."""

from __future__ import annotations

import math
from typing import Any

from . import Garage, WatchFace, FailureState, LiveryPreset


def render_watch_face_svg(face: WatchFace, size: int = 200) -> str:
    """Render a 4-layer watch face as SVG.

    Layer 1: Analog hand (colored, positioned by state)
    Layer 2: Complication slots (4 small sub-dials)
    Layer 3: Dial finish (texture pattern by trust tier)
    Layer 4: Fleet cockpit (PFD six-pack — simplified)
    """
    cx = size / 2
    cy = size / 2
    r = size * 0.45

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">')

    # Layer 3: Dial finish (background pattern)
    dial = face.dial_finish
    if dial == "flat":
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1A1A20" stroke="#333338" stroke-width="2" />')
    elif dial == "sunburst":
        # Sunburst radial lines
        parts.append(f'<defs><radialGradient id="sunburst"><stop offset="0%" stop-color="#2A2A30"/><stop offset="100%" stop-color="#1A1A20"/></radialGradient></defs>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sunburst)" stroke="#333338" stroke-width="2" />')
        for i in range(60):
            angle = i * 6 * math.pi / 180
            x1 = cx + r * 0.3 * math.cos(angle)
            y1 = cy + r * 0.3 * math.sin(angle)
            x2 = cx + r * math.cos(angle)
            y2 = cy + r * math.sin(angle)
            parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#333338" stroke-width="0.3" opacity="0.5" />')
    elif dial == "guilloche":
        # Guilloché concentric circles
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1A1A20" stroke="#333338" stroke-width="2" />')
        for i in range(1, 8):
            sr = r * i / 8
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{sr:.1f}" fill="none" stroke="#333338" stroke-width="0.5" opacity="0.4" />')
    elif dial == "enamel":
        # Enamel — smooth gradient
        parts.append(f'<defs><radialGradient id="enamel"><stop offset="0%" stop-color="#2C2C34"/><stop offset="80%" stop-color="#1A1A20"/><stop offset="100%" stop-color="#0F0F12"/></radialGradient></defs>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#enamel)" stroke="#D4AF37" stroke-width="1" />')
    else:  # skelton
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#333338" stroke-width="2" />')

    # Hour markers
    for i in range(12):
        angle = i * 30 * math.pi / 180 - math.pi / 2
        x1 = cx + r * 0.88 * math.cos(angle)
        y1 = cy + r * 0.88 * math.sin(angle)
        x2 = cx + r * 0.95 * math.cos(angle)
        y2 = cy + r * 0.95 * math.sin(angle)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#9CA3AF" stroke-width="1" />')

    # Layer 1: Analog hand
    hand_angle = face.hand_angle * math.pi / 180 - math.pi / 2
    hx = cx + r * 0.6 * math.cos(hand_angle)
    hy = cy + r * 0.6 * math.sin(hand_angle)
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="{face.hand_color}" stroke-width="3" stroke-linecap="round" />')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{face.hand_color}" />')

    # Layer 2: Complication slots (4 small sub-dials)
    comp_r = r * 0.18
    comp_positions = [
        (cx - r * 0.45, cy - r * 0.3),  # top-left: token budget
        (cx + r * 0.45, cy - r * 0.3),  # top-right: trust tier
        (cx - r * 0.45, cy + r * 0.3),  # bottom-left: current task
        (cx + r * 0.45, cy + r * 0.3),  # bottom-right: error count
    ]
    comp_labels = ["TKN", "TRT", "TSK", "ERR"]
    comp_values = [
        f"{face.token_budget_pct:.0f}%",
        face.trust_tier[:3],
        face.current_task[:4] if face.current_task != "idle" else "—",
        str(face.error_count),
    ]

    for i, (px, py) in enumerate(comp_positions):
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{comp_r:.1f}" fill="#0F0F12" stroke="#333338" stroke-width="0.5" />')
        parts.append(f'<text x="{px:.1f}" y="{py - comp_r * 0.3:.1f}" text-anchor="middle" font-size="6" fill="#6B7280" font-family="monospace">{comp_labels[i]}</text>')
        parts.append(f'<text x="{px:.1f}" y="{py + comp_r * 0.4:.1f}" text-anchor="middle" font-size="8" fill="#E5E7EB" font-family="monospace" font-weight="bold">{comp_values[i]}</text>')

    # State label at bottom
    parts.append(f'<text x="{cx}" y="{size - 8}" text-anchor="middle" font-size="10" fill="{face.hand_color}" font-family="monospace" font-weight="bold">{face.state.upper()}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_livery_swatch_svg(preset: LiveryPreset, width: int = 240, height: int = 120) -> str:
    """Render a livery preset as an SVG swatch card."""
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Background
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0F0F12" />')

    # Color stripes
    stripe_w = width / len(preset.paint_codes)
    for i, color in enumerate(preset.paint_codes):
        x = i * stripe_w
        parts.append(f'<rect x="{x:.0f}" y="0" width="{stripe_w:.0f}" height="{height * 0.6:.0f}" fill="{color}" />')

    # Name and description
    parts.append(f'<text x="10" y="{height * 0.75:.0f}" font-size="14" fill="#E5E7EB" font-family="sans-serif" font-weight="bold">{preset.name}</text>')
    parts.append(f'<text x="10" y="{height * 0.88:.0f}" font-size="10" fill="#9CA3AF" font-family="sans-serif">{preset.description}</text>')
    parts.append(f'<text x="10" y="{height * 0.96:.0f}" font-size="8" fill="#6B7280" font-family="monospace">{preset.era} — {preset.origin}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_failure_state_svg(state: FailureState, width: int = 200, height: int = 120) -> str:
    """Render a failure state visual as SVG."""
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    if state.id == "degraded":
        # Wabi-sabi: cracked but functional, amber tint
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#1A1A20" />')
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{state.color}" opacity="0.15" />')
        # Glitch lines
        for i in range(5):
            y = 20 + i * 20
            offset = (i * 7) % 15
            parts.append(f'<line x1="{offset}" y1="{y}" x2="{width}" y2="{y}" stroke="{state.color}" stroke-width="1" opacity="0.3" />')
        parts.append(f'<text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="24" fill="{state.color}" font-family="monospace">{state.icon}</text>')
        parts.append(f'<text x="{width/2}" y="{height - 15}" text-anchor="middle" font-size="12" fill="{state.color}" font-family="monospace" font-weight="bold">{state.name.upper()}</text>')

    elif state.id == "broken":
        # Kintsugi: gold seams on dark
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0F0F12" />')
        # Gold crack seams
        parts.append(f'<path d="M {width * 0.3},0 L {width * 0.4},{height * 0.3} L {width * 0.35},{height * 0.5} L {width * 0.5},{height * 0.7} L {width * 0.45},{height}" stroke="{state.color}" stroke-width="2" fill="none" />')
        parts.append(f'<path d="M {width * 0.7},0 L {width * 0.6},{height * 0.25} L {width * 0.65},{height * 0.45} L {width * 0.55},{height * 0.65} L {width * 0.6},{height}" stroke="{state.color}" stroke-width="1.5" fill="none" />')
        parts.append(f'<text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="24" fill="{state.color}" font-family="monospace">{state.icon}</text>')
        parts.append(f'<text x="{width/2}" y="{height - 15}" text-anchor="middle" font-size="12" fill="{state.color}" font-family="monospace" font-weight="bold">{state.name.upper()}</text>')

    elif state.id == "dead":
        # Death screen: red on black, terminal style
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0A0A0A" />')
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{state.color}" opacity="0.08" />')
        parts.append(f'<rect x="2" y="2" width="{width - 4}" height="{height - 4}" fill="none" stroke="{state.color}" stroke-width="1" />')
        parts.append(f'<text x="{width/2}" y="{height * 0.35}" text-anchor="middle" font-size="16" fill="{state.color}" font-family="monospace" font-weight="bold">AGENT LOST</text>')
        parts.append(f'<text x="{width/2}" y="{height * 0.55}" text-anchor="middle" font-size="24" fill="{state.color}" font-family="monospace">{state.icon}</text>')
        parts.append(f'<text x="{width/2}" y="{height - 15}" text-anchor="middle" font-size="10" fill="{state.color}" font-family="monospace">SUCCESSOR SPAWNED</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_api_gauge_svg(api_score: int, api_class: str, width: int = 200, height: int = 100) -> str:
    """Render an Agent Performance Index gauge as SVG."""
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Background
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0F0F12" stroke="#333338" stroke-width="1" />')

    # Gauge arc (semicircle)
    cx = width / 2
    cy = height * 0.7
    r = width * 0.35

    # Arc background
    parts.append(f'<path d="M {cx - r},{cy} A {r},{r} 0 0,1 {cx + r},{cy}" fill="none" stroke="#333338" stroke-width="8" />')

    # Arc fill (proportional to score)
    pct = (api_score - 100) / 899  # 100-999 → 0-1
    pct = max(0, min(1, pct))
    end_angle = math.pi * (1 - pct)
    ex = cx + r * math.cos(end_angle)
    ey = cy - r * math.sin(end_angle)

    # Color by class
    class_colors = {
        "D": "#6B7280", "C": "#9CA3AF", "B": "#22C55E",
        "A": "#2563EB", "S1": "#7C3AED", "S2": "#A21CAF", "R": "#D4AF37",
    }
    arc_color = class_colors.get(api_class, "#2563EB")

    if pct > 0:
        parts.append(f'<path d="M {cx - r},{cy} A {r},{r} 0 0,1 {ex:.1f},{ey:.1f}" fill="none" stroke="{arc_color}" stroke-width="8" stroke-linecap="round" />')

    # Score text
    parts.append(f'<text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="28" fill="{arc_color}" font-family="monospace" font-weight="bold" font-variant-numeric="tabular-nums">{api_score}</text>')
    parts.append(f'<text x="{cx}" y="{height - 10}" text-anchor="middle" font-size="14" fill="{arc_color}" font-family="monospace" font-weight="bold">CLASS {api_class}</text>')

    parts.append("</svg>")
    return "\n".join(parts)
