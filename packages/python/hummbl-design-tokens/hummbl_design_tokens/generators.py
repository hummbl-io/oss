"""Output generators for HUMMBL design tokens.

Each function takes a TokenSystem and produces an output format string.
"""

from __future__ import annotations

from typing import Any

from hummbl_design_tokens.color import hex_to_256, hex_to_hsl, hex_to_oklch, contrast_ratio
from hummbl_design_tokens.loader import TokenSystem


def generate_base24(ts: TokenSystem) -> str:
    """Generate a Base24 terminal theme YAML."""
    lines = [
        "scheme: HUMMBL Fleet",
        "author: HUMMBL Open Source",
        "description: HUMMBL design token system — Base24 terminal theme",
        f"variant: {'dark' if ts.meta.get('dark_mode', 'primary') == 'primary' else 'light'}",
        "",
    ]
    # Base24 has 24 slots: 00-07 (normal), 08-0F (bright), 10-17 (extended)
    # Map surfaces and semantic colors
    color_map = {
        "base00": ts.surfaces["base"],
        "base01": ts.surfaces["elevated"],
        "base02": ts.surfaces["raised"],
        "base03": ts.surfaces["text_muted"],
        "base04": ts.surfaces["border"],
        "base05": ts.surfaces["text_body"],
        "base06": "#F3F4F6",  # bright text
        "base07": "#FFFFFF",  # brightest text
        "base08": ts.status["CRITICAL"]["hex"],  # red — errors
        "base09": ts.bus_types["MILESTONE"]["hex"],  # amber — warnings
        "base0A": ts.bus_types["QUESTION"]["hex"],  # yellow — attention
        "base0B": ts.status["HEALTHY"]["hex"],  # green — success
        "base0C": ts.bus_types["SKILL_INVOKE"]["hex"],  # cyan — info
        "base0D": ts.bus_types["STATUS"]["hex"],  # blue — keywords
        "base0E": ts.bus_types["DECISION"]["hex"],  # purple — special
        "base0F": ts.bus_types["PROPOSAL"]["hex"],  # magenta — deprecated/standout
        # Extended slots for fleet semantics
        "base10": ts.trust_tiers["OWNER"]["hex"],
        "base11": ts.trust_tiers["TRUSTED"]["hex"],
        "base12": ts.trust_tiers["MEDIUM-HIGH"]["hex"],
        "base13": ts.trust_tiers["MEDIUM"]["hex"],
        "base14": ts.trust_tiers["PROBATIONARY"]["hex"],
        "base15": ts.bus_types["BLOCKED"]["hex"],
        "base16": ts.bus_types["SITREP"]["hex"],
        "base17": ts.bus_types["ACK"]["hex"],
    }
    for slot, hex_val in color_map.items():
        lines.append(f"{slot}: \"{hex_val}\"")
    return "\n".join(lines) + "\n"


def generate_css(ts: TokenSystem) -> str:
    """Generate CSS custom properties from tokens."""
    lines = [
        "/* HUMMBL Design Tokens — Auto-generated. Do not edit directly. */",
        f"/* Version: {ts.version} | Authored: {ts.meta.get('authored', 'unknown')} */",
        "",
        ":root {",
        "  /* Surfaces */",
        f"  --surface-base: {ts.surfaces['base']};",
        f"  --surface-elevated: {ts.surfaces['elevated']};",
        f"  --surface-raised: {ts.surfaces['raised']};",
        f"  --text-body: {ts.surfaces['text_body']};",
        f"  --text-muted: {ts.surfaces['text_muted']};",
        f"  --border: {ts.surfaces['border']};",
        f"  --border-focus: {ts.surfaces['border_focus']};",
        "",
        "  /* Agent identity colors (dark mode) */",
    ]
    for name in sorted(ts.agents.keys()):
        agent = ts.agents[name]
        lines.append(f"  --agent-{name.replace('-', '_')}: {agent['hex_dark']};")
    lines.append("")
    lines.append("  /* Trust tier colors */")
    for tier_name in ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY"]:
        tier = ts.trust_tiers[tier_name]
        tier_key = tier_name.lower().replace("-", "_")
        lines.append(f"  --trust-{tier_key}: {tier['hex']};")
    lines.append("")
    lines.append("  /* Bus message type colors */")
    for btype in ["PROPOSAL", "ACK", "STATUS", "SITREP", "BLOCKED", "DECISION", "QUESTION", "MILESTONE", "SKILL_INVOKE"]:
        bt = ts.bus_types[btype]
        bkey = btype.lower().replace("_", "-")
        lines.append(f"  --bus-{bkey}: {bt['hex']};")
    lines.append("")
    lines.append("  /* Status colors */")
    for sname in ["HEALTHY", "DEGRADED", "CRITICAL"]:
        st = ts.status[sname]
        skey = sname.lower()
        lines.append(f"  --status-{skey}: {st['hex']};")
    lines.append("")
    lines.append("  /* Typography */")
    tp = ts.typography
    lines.append(f"  --font-ui: \"{tp['primary_ui_sans']['family']}\", {', '.join(tp['primary_ui_sans']['fallback'])};")
    lines.append(f"  --font-mono: \"{tp['primary_mono']['family']}\", {', '.join(tp['primary_mono']['fallback'])};")
    lines.append(f"  --font-icons: \"{tp['tui_icons']['family']}\";")
    lines.append(f"  --font-agent: \"{tp['agent_identity']['family']}\";")
    lines.append(f"  --type-scale-ratio: {tp['type_scale']['ratio']};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def generate_python_module(ts: TokenSystem) -> str:
    """Generate a Python color module from tokens."""
    lines = [
        '"""HUMMBL design tokens — auto-generated. Do not edit directly.',
        f'Version: {ts.version}',
        '"""',
        "",
        "# Surfaces",
        f"BASE = \"{ts.surfaces['base']}\"",
        f"ELEVATED = \"{ts.surfaces['elevated']}\"",
        f"RAISED = \"{ts.surfaces['raised']}\"",
        f"TEXT_BODY = \"{ts.surfaces['text_body']}\"",
        f"TEXT_MUTED = \"{ts.surfaces['text_muted']}\"",
        f"BORDER = \"{ts.surfaces['border']}\"",
        "",
        "# Agent identity colors (dark mode)",
        "AGENTS = {",
    ]
    for name in sorted(ts.agents.keys()):
        agent = ts.agents[name]
        lines.append(f"    \"{name}\": \"{agent['hex_dark']}\",")
    lines.append("}")
    lines.append("")
    lines.append("# Trust tier colors")
    lines.append("TRUST_TIERS = {")
    for tier_name in ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY"]:
        tier = ts.trust_tiers[tier_name]
        lines.append(f"    \"{tier_name}\": \"{tier['hex']}\",")
    lines.append("}")
    lines.append("")
    lines.append("# Bus message type colors")
    lines.append("BUS_TYPES = {")
    for btype in ["PROPOSAL", "ACK", "STATUS", "SITREP", "BLOCKED", "DECISION", "QUESTION", "MILESTONE", "SKILL_INVOKE"]:
        bt = ts.bus_types[btype]
        lines.append(f"    \"{btype}\": \"{bt['hex']}\",")
    lines.append("}")
    lines.append("")
    lines.append("# Status colors")
    lines.append("STATUS = {")
    for sname in ["HEALTHY", "DEGRADED", "CRITICAL"]:
        st = ts.status[sname]
        lines.append(f"    \"{sname}\": \"{st['hex']}\",")
    lines.append("}")
    return "\n".join(lines) + "\n"


def generate_typescript_module(ts: TokenSystem) -> str:
    """Generate a TypeScript color module from tokens."""
    lines = [
        "/** HUMMBL design tokens — auto-generated. Do not edit directly. */",
        f"// Version: {ts.version}",
        "",
        "export const SURFACES = {",
        f"  base: \"{ts.surfaces['base']}\",",
        f"  elevated: \"{ts.surfaces['elevated']}\",",
        f"  raised: \"{ts.surfaces['raised']}\",",
        f"  textBody: \"{ts.surfaces['text_body']}\",",
        f"  textMuted: \"{ts.surfaces['text_muted']}\",",
        f"  border: \"{ts.surfaces['border']}\",",
        "} as const;",
        "",
        "export const AGENTS = {",
    ]
    for name in sorted(ts.agents.keys()):
        agent = ts.agents[name]
        key = name.replace("-", "_")
        lines.append(f"  {key}: \"{agent['hex_dark']}\",")
    lines.append("} as const;")
    lines.append("")
    lines.append("export const TRUST_TIERS = {")
    for tier_name in ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY"]:
        tier = ts.trust_tiers[tier_name]
        key = tier_name.replace("-", "_")
        lines.append(f"  {key}: \"{tier['hex']}\",")
    lines.append("} as const;")
    lines.append("")
    lines.append("export const BUS_TYPES = {")
    for btype in ["PROPOSAL", "ACK", "STATUS", "SITREP", "BLOCKED", "DECISION", "QUESTION", "MILESTONE", "SKILL_INVOKE"]:
        bt = ts.bus_types[btype]
        key = btype.replace("-", "_")
        lines.append(f"  {key}: \"{bt['hex']}\",")
    lines.append("} as const;")
    lines.append("")
    lines.append("export const STATUS = {")
    for sname in ["HEALTHY", "DEGRADED", "CRITICAL"]:
        st = ts.status[sname]
        skey = sname.lower()
        lines.append(f"  {skey}: \"{st['hex']}\",")
    lines.append("} as const;")
    return "\n".join(lines) + "\n"


def generate_livery(ts: TokenSystem, agent_name: str) -> str:
    """Generate a livery JSON for a specific agent."""
    import json as _json
    livery = ts.agent_livery(agent_name)
    return _json.dumps(livery, indent=2, ensure_ascii=False) + "\n"


def generate_swatches_html(ts: TokenSystem) -> str:
    """Generate an HTML documentation page with color swatches."""
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>HUMMBL Design Token Swatches</title>",
        "<style>",
        "body { background: #0F0F12; color: #E5E7EB; font-family: 'JetBrains Mono', monospace; margin: 2rem; }",
        "h1 { font-size: 1.5rem; } h2 { font-size: 1.2rem; margin-top: 2rem; color: #9CA3AF; }",
        ".grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem; }",
        ".swatch { padding: 0.75rem; border-radius: 4px; border: 1px solid #333338; }",
        ".swatch .color { width: 100%; height: 40px; border-radius: 2px; margin-bottom: 0.5rem; }",
        ".swatch .label { font-size: 0.8rem; color: #E5E7EB; }",
        ".swatch .hex { font-size: 0.7rem; color: #9CA3AF; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>HUMMBL Design Token Swatches — v{ts.version}</h1>",
        "",
        "<h2>Agent Identity Colors (Dark Mode)</h2>",
        "<div class='grid'>",
    ]
    for name in sorted(ts.agents.keys()):
        agent = ts.agents[name]
        hex_val = agent["hex_dark"]
        lines.append(f"  <div class='swatch'><div class='color' style='background:{hex_val}'></div>"
                     f"<div class='label'>{name}</div><div class='hex'>{hex_val}</div></div>")
    lines.append("</div>")
    lines.append("")
    lines.append("<h2>Trust Tier Colors</h2>")
    lines.append("<div class='grid'>")
    for tier_name in ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY"]:
        tier = ts.trust_tiers[tier_name]
        hex_val = tier["hex"]
        lines.append(f"  <div class='swatch'><div class='color' style='background:{hex_val}'></div>"
                     f"<div class='label'>{tier_name}</div><div class='hex'>{hex_val}</div></div>")
    lines.append("</div>")
    lines.append("")
    lines.append("<h2>Bus Message Type Colors</h2>")
    lines.append("<div class='grid'>")
    for btype in ["PROPOSAL", "ACK", "STATUS", "SITREP", "BLOCKED", "DECISION", "QUESTION", "MILESTONE", "SKILL_INVOKE"]:
        bt = ts.bus_types[btype]
        hex_val = bt["hex"]
        icon = bt.get("icon", "")
        lines.append(f"  <div class='swatch'><div class='color' style='background:{hex_val}'></div>"
                     f"<div class='label'>{icon} {btype}</div><div class='hex'>{hex_val}</div></div>")
    lines.append("</div>")
    lines.append("")
    lines.append("<h2>Status Colors</h2>")
    lines.append("<div class='grid'>")
    for sname in ["HEALTHY", "DEGRADED", "CRITICAL"]:
        st = ts.status[sname]
        hex_val = st["hex"]
        icon = st.get("icon", "")
        lines.append(f"  <div class='swatch'><div class='color' style='background:{hex_val}'></div>"
                     f"<div class='label'>{icon} {sname}</div><div class='hex'>{hex_val}</div></div>")
    lines.append("</div>")
    lines.append("")
    # Contrast verification
    lines.append("<h2>Contrast Verification (against base surface)</h2>")
    lines.append("<table style='border-collapse:collapse;font-size:0.8rem'>")
    lines.append("<tr><th style='text-align:left;padding:0.5rem;border:1px solid #333'>Color</th>"
                 "<th style='padding:0.5rem;border:1px solid #333'>Hex</th>"
                 "<th style='padding:0.5rem;border:1px solid #333'>Contrast vs base</th>"
                 "<th style='padding:0.5rem;border:1px solid #333'>AA (4.5:1)</th>"
                 "<th style='padding:0.5rem;border:1px solid #333'>AAA (7:1)</th></tr>")
    base = ts.surfaces["base"]
    all_colors = {}
    for name in sorted(ts.agents.keys()):
        all_colors[f"agent:{name}"] = ts.agents[name]["hex_dark"]
    for tier_name in ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY"]:
        all_colors[f"trust:{tier_name}"] = ts.trust_tiers[tier_name]["hex"]
    for btype in ["PROPOSAL", "ACK", "STATUS", "SITREP", "BLOCKED", "DECISION", "QUESTION", "MILESTONE", "SKILL_INVOKE"]:
        all_colors[f"bus:{btype}"] = ts.bus_types[btype]["hex"]
    for sname in ["HEALTHY", "DEGRADED", "CRITICAL"]:
        all_colors[f"status:{sname}"] = ts.status[sname]["hex"]
    for label, hex_val in sorted(all_colors.items()):
        cr = contrast_ratio(hex_val, base)
        aa = "✓" if cr >= 4.5 else "✗"
        aaa = "✓" if cr >= 7.0 else "✗"
        lines.append(f"<tr><td style='padding:0.5rem;border:1px solid #333'>{label}</td>"
                     f"<td style='padding:0.5rem;border:1px solid #333;text-align:center'>{hex_val}</td>"
                     f"<td style='padding:0.5rem;border:1px solid #333;text-align:center'>{cr:.2f}:1</td>"
                     f"<td style='padding:0.5rem;border:1px solid #333;text-align:center'>{aa}</td>"
                     f"<td style='padding:0.5rem;border:1px solid #333;text-align:center'>{aaa}</td></tr>")
    lines.append("</table>")
    lines.append("</body></html>")
    return "\n".join(lines) + "\n"
