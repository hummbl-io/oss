"""SVG renderer for heraldic arms.

Generates SVG shields from AgentArms data. Each shield is rendered with:
- Shield shape outline
- Field tincture fill
- Division (if any)
- Ordinary (if any)
- Charge (simplified geometric representation)
- Cadency mark (if any)
"""

from __future__ import annotations

from typing import Any

from . import AgentArms, Grammar, Tincture


def _tincture_fill(tincture: Tincture) -> str:
    """Get SVG fill for a tincture."""
    if tincture.id == "ermine":
        # Ermine pattern: white background with black spots
        return "url(#ermine_pattern)"
    elif tincture.id == "vair":
        # Vair pattern: blue-white bell pattern
        return "url(#vair_pattern)"
    return tincture.hex


def _shield_path(shape_id: str, cx: float, cy: float, w: float, h: float) -> str:
    """Get SVG path for a shield shape."""
    x0 = cx - w / 2
    y0 = cy - h / 2
    x1 = cx + w / 2
    y1 = cy + h / 2

    if shape_id == "heater":
        # Classic triangular shield
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y0 + h * 0.6} Q {x1},{y1} {cx},{y1} Q {x0},{y1} {x0},{y0 + h * 0.6} Z"
    elif shape_id == "kite":
        # Norman kite — almond shape
        return f"M {x0},{y0} Q {x1},{y0} {x1},{y0 + h * 0.5} Q {cx},{y1} {x0},{y0 + h * 0.5} Q {x0},{y0} {x0},{y0} Z"
    elif shape_id == "swiss":
        # Square-topped with rounded base
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y0 + h * 0.7} Q {x1},{y1} {cx},{y1} Q {x0},{y1} {x0},{y0 + h * 0.7} Z"
    elif shape_id == "french":
        # Taller, pointed base
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y0 + h * 0.7} L {cx},{y1} L {x0},{y0 + h * 0.7} Z"
    elif shape_id == "lozenge":
        # Diamond
        return f"M {cx},{y0} L {x1},{cy} L {cx},{y1} L {x0},{cy} Z"
    elif shape_id == "oval":
        # Oval/ellipse
        rx = w / 2
        ry = h / 2
        return f"M {cx - rx},{cy} A {rx},{ry} 0 1,0 {cx + rx},{cy} A {rx},{ry} 0 1,0 {cx - rx},{cy} Z"
    else:  # square
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y1} L {x0},{y1} Z"


def _division_clip(division_id: str, cx: float, cy: float, w: float, h: float) -> str:
    """Get SVG clip path for field division."""
    x0 = cx - w / 2
    y0 = cy - h / 2
    x1 = cx + w / 2
    y1 = cy + h / 2

    if division_id == "per_pale":
        # Left half
        return f"M {x0},{y0} L {cx},{y0} L {cx},{y1} L {x0},{y1} Z"
    elif division_id == "per_fess":
        # Top half
        return f"M {x0},{y0} L {x1},{y0} L {x1},{cy} L {x0},{cy} Z"
    elif division_id == "per_bend":
        # Top-left triangle
        return f"M {x0},{y0} L {x1},{y0} L {x0},{y1} Z"
    elif division_id == "per_bend_sinister":
        # Top-right triangle
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y1} Z"
    elif division_id == "per_chevron":
        # Top portion (above chevron)
        return f"M {x0},{y0} L {x1},{y0} L {x1},{cy + h * 0.2} L {cx},{y1} L {x0},{cy + h * 0.2} Z"
    elif division_id == "per_saltire":
        # Top quarter
        return f"M {x0},{y0} L {x1},{y0} L {cx},{cy} L {x0},{cy} Z"
    elif division_id == "quarterly":
        # Top-left quarter
        return f"M {x0},{y0} L {cx},{y0} L {cx},{cy} L {x0},{cy} Z"
    elif division_id == "per_pall":
        # Top-left third
        return f"M {x0},{y0} L {cx},{y0} L {cx},{cy} L {x0},{y1} Z"
    elif division_id == "gyronny":
        # Top-left wedge
        return f"M {x0},{y0} L {cx},{y0} L {cx},{cy} L {x0},{cy} Z"
    return ""


def _ordinary_path(ordinary_id: str, cx: float, cy: float, w: float, h: float) -> str:
    """Get SVG path for an ordinary."""
    x0 = cx - w / 2
    y0 = cy - h / 2
    x1 = cx + w / 2
    y1 = cy + h / 2
    bw = w * 0.15  # band width

    if ordinary_id == "pale":
        return f"M {cx - bw/2},{y0} L {cx + bw/2},{y0} L {cx + bw/2},{y1} L {cx - bw/2},{y1} Z"
    elif ordinary_id == "fess":
        return f"M {x0},{cy - bw/2} L {x1},{cy - bw/2} L {x1},{cy + bw/2} L {x0},{cy + bw/2} Z"
    elif ordinary_id == "bend":
        return f"M {x0},{y0} L {x0 + bw},{y0} L {x1},{y1 - bw} L {x1},{y1} Z"
    elif ordinary_id == "chevron":
        return f"M {x0},{y1} L {cx},{cy} L {x1},{y1} L {x1},{y1 - bw} L {cx},{cy - bw} L {x0},{y1 - bw} Z"
    elif ordinary_id == "cross":
        return f"M {cx - bw/2},{y0} L {cx + bw/2},{y0} L {cx + bw/2},{cy - bw/2} L {x1},{cy - bw/2} L {x1},{cy + bw/2} L {cx + bw/2},{cy + bw/2} L {cx + bw/2},{y1} L {cx - bw/2},{y1} L {cx - bw/2},{cy + bw/2} L {x0},{cy + bw/2} L {x0},{cy - bw/2} L {cx - bw/2},{cy - bw/2} Z"
    elif ordinary_id == "saltire":
        # X-shaped cross
        d = bw / 2
        return f"M {x0},{y0} L {x0 + bw},{y0} L {cx},{cy - d} L {x1 - bw},{y0} L {x1},{y0} L {cx + d},{cy} L {x1},{y1} L {x1 - bw},{y1} L {cx},{cy + d} L {x0 + bw},{y1} L {x0},{y1} L {cx - d},{cy} Z"
    elif ordinary_id == "chief":
        return f"M {x0},{y0} L {x1},{y0} L {x1},{y0 + h * 0.25} L {x0},{y0 + h * 0.25} Z"
    return ""


def _charge_svg(charge_id: str, cx: float, cy: float, size: float, fill: str) -> str:
    """Get simplified SVG for a charge."""
    s = size

    if charge_id == "none":
        return ""

    # Geometric simplifications of heraldic charges
    if charge_id in ("mullet", "star"):
        # Five/six-pointed star
        points = []
        n = 5 if charge_id == "mullet" else 6
        for i in range(n * 2):
            angle = (i * 180 / n - 90) * 3.14159 / 180
            r = s if i % 2 == 0 else s * 0.4
            px = cx + r * __import__("math").cos(angle)
            py = cy + r * __import__("math").sin(angle)
            points.append(f"{px:.1f},{py:.1f}")
        return f'<polygon points="{" ".join(points)}" fill="{fill}" />'

    elif charge_id == "crescent":
        # Crescent moon
        return f'<path d="M {cx - s},{cy} A {s},{s} 0 0,0 {cx + s},{cy} A {s * 0.7},{s * 0.7} 0 0,1 {cx - s},{cy} Z" fill="{fill}" />'

    elif charge_id == "annulet":
        # Ring
        return f'<circle cx="{cx}" cy="{cy}" r="{s}" fill="none" stroke="{fill}" stroke-width="{s * 0.3}" />'

    elif charge_id == "cross_moline":
        # Cross with forked ends
        bw = s * 0.3
        return f'<rect x="{cx - bw/2}" y="{cy - s}" width="{bw}" height="{s * 2}" fill="{fill}" /><rect x="{cx - s}" y="{cy - bw/2}" width="{s * 2}" height="{bw}" fill="{fill}" />'

    elif charge_id == "cogwheel" or charge_id == "gear":
        # Cogwheel/gear
        teeth = 8
        path_parts = []
        import math
        for i in range(teeth * 2):
            angle = (i * 360 / (teeth * 2)) * math.pi / 180
            r = s if i % 2 == 0 else s * 0.75
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            path_parts.append(f"{px:.1f},{py:.1f}")
        inner = f'<circle cx="{cx}" cy="{cy}" r="{s * 0.3}" fill="#0F0F12" />'
        return f'<polygon points="{" ".join(path_parts)}" fill="{fill}" />{inner}'

    elif charge_id == "compass":
        # Compass rose (4-pointed star)
        return f'<polygon points="{cx},{cy - s} {cx + s * 0.3},{cy} {cx},{cy + s} {cx - s * 0.3},{cy}" fill="{fill}" /><polygon points="{cx - s},{cy} {cx},{cy + s * 0.3} {cx + s},{cy} {cx},{cy - s * 0.3}" fill="{fill}" opacity="0.7" />'

    elif charge_id == "knot":
        # Heraldic knot — two interlocked circles
        return f'<circle cx="{cx - s * 0.3}" cy="{cy}" r="{s * 0.5}" fill="none" stroke="{fill}" stroke-width="{s * 0.2}" /><circle cx="{cx + s * 0.3}" cy="{cy}" r="{s * 0.5}" fill="none" stroke="{fill}" stroke-width="{s * 0.2}" />'

    elif charge_id == "tower":
        # Castle tower
        return f'<rect x="{cx - s * 0.5}" y="{cy - s * 0.7}" width="{s}" height="{s * 1.4}" fill="{fill}" /><rect x="{cx - s * 0.6}" y="{cy - s * 0.8}" width="{s * 0.2}" height="{s * 0.2}" fill="{fill}" /><rect x="{cx + s * 0.4}" y="{cy - s * 0.8}" width="{s * 0.2}" height="{s * 0.2}" fill="{fill}" />'

    elif charge_id == "sword":
        # Vertical sword
        return f'<rect x="{cx - s * 0.1}" y="{cy - s}" width="{s * 0.2}" height="{s * 1.5}" fill="{fill}" /><rect x="{cx - s * 0.4}" y="{cy - s * 0.4}" width="{s * 0.8}" height="{s * 0.15}" fill="{fill}" /><circle cx="{cx}" cy="{cy + s * 0.6}" r="{s * 0.15}" fill="{fill}" />'

    elif charge_id == "anchor":
        # Anchor
        ring = f'<circle cx="{cx}" cy="{cy - s * 0.7}" r="{s * 0.2}" fill="none" stroke="{fill}" stroke-width="{s * 0.15}" />'
        shank = f'<rect x="{cx - s * 0.08}" y="{cy - s * 0.5}" width="{s * 0.16}" height="{s * 1.2}" fill="{fill}" />'
        arms = f'<path d="M {cx - s * 0.6},{cy + s * 0.5} Q {cx},{cy + s * 0.3} {cx + s * 0.6},{cy + s * 0.5}" fill="none" stroke="{fill}" stroke-width="{s * 0.15}" />'
        return ring + shank + arms

    elif charge_id == "lightning_bolt":
        return f'<polygon points="{cx - s * 0.3},{cy - s} {cx + s * 0.2},{cy - s * 0.2} {cx},{cy - s * 0.1} {cx + s * 0.3},{cy + s} {cx - s * 0.2},{cy + s * 0.2} {cx},{cy + s * 0.1}" fill="{fill}" />'

    elif charge_id == "pall" or charge_id == "pall_reversed":
        # Y-shaped charge
        bw = s * 0.2
        if charge_id == "pall":
            return f'<path d="M {cx},{cy - s} L {cx + bw/2},{cy - s * 0.3} L {cx + s},{cy + s} L {cx + bw/2},{cy + s} L {cx},{cy + s * 0.3} L {cx - bw/2},{cy + s} L {cx - s},{cy + s} L {cx - bw/2},{cy - s * 0.3} Z" fill="{fill}" />'
        else:  # pall_reversed
            return f'<path d="M {cx - s},{cy - s} L {cx - bw/2},{cy - s} L {cx},{cy + s * 0.3} L {cx + bw/2},{cy - s} L {cx + s},{cy - s} L {cx + bw/2},{cy + s * 0.3} L {cx + bw/2},{cy + s} L {cx - bw/2},{cy + s} L {cx - bw/2},{cy + s * 0.3} Z" fill="{fill}" />'

    elif charge_id == "fleur_de_lis":
        # Simplified fleur-de-lis
        return f'<path d="M {cx},{cy - s} Q {cx + s * 0.4},{cy} {cx},{cy + s * 0.3} Q {cx - s * 0.4},{cy} {cx},{cy - s} Z" fill="{fill}" /><rect x="{cx - s * 0.5}" y="{cy + s * 0.2}" width="{s}" height="{s * 0.2}" fill="{fill}" />'

    elif charge_id == "eye":
        # All-seeing eye
        return f'<ellipse cx="{cx}" cy="{cy}" rx="{s}" ry="{s * 0.5}" fill="none" stroke="{fill}" stroke-width="{s * 0.15}" /><circle cx="{cx}" cy="{cy}" r="{s * 0.25}" fill="{fill}" />'

    elif charge_id in ("lion_rampant", "lion_passant", "eagle_displayed", "martlet", "rose", "escallop", "key", "scroll", "lens", "wrench", "caduceus", "divining_rod"):
        # For complex charges, use a simple circle placeholder with the charge name
        return f'<circle cx="{cx}" cy="{cy}" r="{s * 0.6}" fill="{fill}" opacity="0.8" /><text x="{cx}" y="{cy + s * 0.15}" text-anchor="middle" font-size="{s * 0.4}" fill="#0F0F12" font-family="serif">{charge_id[0].upper()}</text>'

    return ""


def _cadency_svg(cadency_id: str, cx: float, cy: float, w: float, h: float, fill: str) -> str:
    """Get SVG for a cadency mark."""
    if cadency_id == "none" or cadency_id is None:
        return ""

    if cadency_id == "label":
        # Label of three points — horizontal bar at top with 3 tabs
        y = cy - h / 2 + h * 0.08
        bw = w * 0.5
        tab_h = h * 0.08
        return f'<rect x="{cx - bw/2}" y="{y}" width="{bw}" height="{tab_h * 0.4}" fill="{fill}" /><rect x="{cx - bw/2}" y="{y + tab_h * 0.4}" width="{bw / 3}" height="{tab_h}" fill="{fill}" /><rect x="{cx - bw/6}" y="{y + tab_h * 0.4}" width="{bw / 3}" height="{tab_h}" fill="{fill}" /><rect x="{cx + bw/6}" y="{y + tab_h * 0.4}" width="{bw / 3}" height="{tab_h}" fill="{fill}" />'

    elif cadency_id == "crescent":
        # Crescent at top
        size = w * 0.08
        y = cy - h / 2 + h * 0.12
        return f'<path d="M {cx - size},{y} A {size},{size} 0 0,0 {cx + size},{y} A {size * 0.7},{size * 0.7} 0 0,1 {cx - size},{y} Z" fill="{fill}" />'

    elif cadency_id == "mullet":
        # Star at top
        size = w * 0.06
        y = cy - h / 2 + h * 0.12
        return _charge_svg("mullet", cx, y, size, fill)

    elif cadency_id == "bordure_compony":
        # Checkered border — represented as a dashed border
        return f'<rect x="{cx - w/2 + 4}" y="{cy - h/2 + 4}" width="{w - 8}" height="{h - 8}" fill="none" stroke="{fill}" stroke-width="6" stroke-dasharray="8,8" />'

    return ""


def render_arms_svg(arms: AgentArms, width: int = 200, height: int = 240) -> str:
    """Render an AgentArms object as an SVG shield.

    Args:
        arms: The agent's heraldic arms
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        SVG string
    """
    cx = width / 2
    cy = height / 2
    sw = width * 0.8  # shield width
    sh = height * 0.85  # shield height

    grammar = Grammar()
    shield_path = _shield_path(arms.shield.id, cx, cy, sw, sh)

    # Build SVG
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Definitions for patterns
    parts.append("<defs>")
    # Ermine pattern
    parts.append(f'<pattern id="ermine_pattern" patternUnits="userSpaceOnUse" width="20" height="20"><rect width="20" height="20" fill="#F3F4F6"/><circle cx="10" cy="10" r="3" fill="#1A1A20"/></pattern>')
    # Vair pattern
    parts.append(f'<pattern id="vair_pattern" patternUnits="userSpaceOnUse" width="20" height="20"><rect width="20" height="20" fill="#93C5FD"/><path d="M 0,0 L 10,10 L 0,20 Z M 10,0 L 20,10 L 10,20 Z" fill="#E5E7EB"/></pattern>')
    parts.append("</defs>")

    # Shield background (field tincture)
    field_fill = _tincture_fill(arms.field_tincture)
    parts.append(f'<path d="{shield_path}" fill="{field_fill}" stroke="#333338" stroke-width="2" />')

    # Division (second tincture on part of field)
    if arms.division.id != "solid" and arms.division_tincture:
        div_clip = _division_clip(arms.division.id, cx, cy, sw, sh)
        if div_clip:
            div_fill = _tincture_fill(arms.division_tincture)
            parts.append(f'<clipPath id="shield_clip_{arms.agent_name}"><path d="{shield_path}" /></clipPath>')
            parts.append(f'<path d="{div_clip}" fill="{div_fill}" clip-path="url(#shield_clip_{arms.agent_name})" />')

    # Ordinary
    if arms.ordinary.id != "none" and arms.ordinary_tincture:
        ord_path = _ordinary_path(arms.ordinary.id, cx, cy, sw, sh)
        if ord_path:
            ord_fill = _tincture_fill(arms.ordinary_tincture)
            parts.append(f'<path d="{ord_path}" fill="{ord_fill}" />')

    # Charge
    if arms.charge.id != "none" and arms.charge_tincture:
        charge_fill = _tincture_fill(arms.charge_tincture)
        charge_svg = _charge_svg(arms.charge.id, cx, cy + sh * 0.05, sh * 0.2, charge_fill)
        if charge_svg:
            parts.append(charge_svg)

    # Cadency mark
    if arms.cadency and arms.cadency.id != "none":
        # Use a contrasting tincture for cadency
        cad_fill = arms.field_tincture.hex if arms.field_tincture.category == "metal" else "#E5E7EB"
        cad_svg = _cadency_svg(arms.cadency.id, cx, cy, sw, sh, cad_fill)
        if cad_svg:
            parts.append(cad_svg)

    # Agent name label
    parts.append(f'<text x="{cx}" y="{height - 5}" text-anchor="middle" font-family="monospace" font-size="12" fill="#E5E7EB">{arms.agent_name}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_fleet_arms_svg(width: int = 200, height: int = 240) -> str:
    """Render the HUMMBL LLC fleet arms.

    Blazon: "Sable, a pall reversed between in chief two mullets Argent
    and in base a cogwheel Or"
    """
    cx = width / 2
    cy = height / 2
    sw = width * 0.8
    sh = height * 0.85

    shield_path = _shield_path("heater", cx, cy, sw, sh)

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Sable field
    parts.append(f'<path d="{shield_path}" fill="#1A1A20" stroke="#333338" stroke-width="2" />')

    # Pall reversed (inverted Y) in Argent
    pall = _charge_svg("pall_reversed", cx, cy, sh * 0.3, "#E5E7EB")
    parts.append(pall)

    # Two mullets in chief (top) in Argent
    star_size = sh * 0.08
    parts.append(_charge_svg("mullet", cx - sw * 0.2, cy - sh * 0.3, star_size, "#E5E7EB"))
    parts.append(_charge_svg("mullet", cx + sw * 0.2, cy - sh * 0.3, star_size, "#E5E7EB"))

    # Cogwheel in base (bottom) in Or
    parts.append(_charge_svg("cogwheel", cx, cy + sh * 0.25, sh * 0.12, "#E6B800"))

    # Label
    parts.append(f'<text x="{cx}" y="{height - 5}" text-anchor="middle" font-family="monospace" font-size="11" fill="#E5E7EB">HUMMBL LLC</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_ics_flag_svg(
    bus_type: str,
    color_scheme: str,
    width: int = 60,
    height: int = 40,
) -> str:
    """Render an ICS-style signal flag for a bus message type.

    Args:
        bus_type: The bus message type (PROPOSAL, ACK, etc.)
        color_scheme: Description of the color scheme
        width: Flag width in pixels
        height: Flag height in pixels

    Returns:
        SVG string
    """
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Parse color scheme and render
    scheme = color_scheme.lower()

    if "swallowtail" in scheme and "red" in scheme:
        # Bravo — red swallowtail
        parts.append(f'<path d="M 0,0 L {width * 0.4},{height/2} L 0,{height} L 0,0 Z" fill="#DC2626" />')
        parts.append(f'<path d="M {width * 0.4},0 L {width},{0} L {width * 0.7},{height/2} L {width},{height} L {width * 0.4},{height} Z" fill="#DC2626" />')
    elif "swallowtail" in scheme and ("white" in scheme or "blue" in scheme):
        # Alfa — white-blue swallowtail
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#E5E7EB" />')
        parts.append(f'<path d="M {width * 0.4},0 L {width},{0} L {width * 0.7},{height/2} L {width},{height} L {width * 0.4},{height} Z" fill="#2563EB" />')
    elif "blue-white-blue" in scheme:
        # Papa — blue-white-blue vertical
        parts.append(f'<rect x="0" y="0" width="{width/3}" height="{height}" fill="#2563EB" />')
        parts.append(f'<rect x="{width/3}" y="0" width="{width/3}" height="{height}" fill="#E5E7EB" />')
        parts.append(f'<rect x="{2*width/3}" y="0" width="{width/3}" height="{height}" fill="#2563EB" />')
    elif "white-blue-white" in scheme:
        # Sierra — white-blue-white with center square
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#E5E7EB" />')
        parts.append(f'<rect x="0" y="{height/3}" width="{width}" height="{height/3}" fill="#2563EB" />')
        parts.append(f'<rect x="{width * 0.35}" y="{height * 0.35}" width="{width * 0.3}" height="{height * 0.3}" fill="#E5E7EB" />')
    elif "red-white-red" in scheme:
        # SITREP custom — red-white-red horizontal
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height/3}" fill="#DC2626" />')
        parts.append(f'<rect x="0" y="{height/3}" width="{width}" height="{height/3}" fill="#E5E7EB" />')
        parts.append(f'<rect x="0" y="{2*height/3}" width="{width}" height="{height/3}" fill="#DC2626" />')
    elif "yellow-blue-yellow" in scheme:
        # Delta — yellow-blue-yellow with center square
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#E6B800" />')
        parts.append(f'<rect x="0" y="{height/3}" width="{width}" height="{height/3}" fill="#2563EB" />')
        parts.append(f'<rect x="{width * 0.35}" y="{height * 0.35}" width="{width * 0.3}" height="{height * 0.3}" fill="#E6B800" />')
    elif scheme.strip() == "yellow":
        # Quebec — solid yellow
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#E6B800" />')
    elif "blue-white" in scheme and "green" not in scheme:
        # Mike — blue-white
        parts.append(f'<rect x="0" y="0" width="{width/2}" height="{height}" fill="#2563EB" />')
        parts.append(f'<rect x="{width/2}" y="0" width="{width/2}" height="{height}" fill="#E5E7EB" />')
    elif "green-white-green" in scheme:
        # SKILL_INVOKE custom — SOPA style
        parts.append(f'<rect x="0" y="0" width="{width/3}" height="{height}" fill="#22C55E" />')
        parts.append(f'<rect x="{width/3}" y="0" width="{width/3}" height="{height}" fill="#E5E7EB" />')
        parts.append(f'<rect x="{2*width/3}" y="0" width="{width/3}" height="{height}" fill="#22C55E" />')
    else:
        # Fallback — gray
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#9CA3AF" />')

    # Border
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="#333338" stroke-width="1" />')

    parts.append("</svg>")
    return "\n".join(parts)
