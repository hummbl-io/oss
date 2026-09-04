# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""SOUL Injector — Load SOUL.md, resolve composition, generate system-prompt blocks.

Given a SOUL.md file path, this module:
1. Parses the YAML frontmatter
2. Resolves composition (extends + mixins) with deep merge
3. Generates the Regulatory Awareness Block from the regulatory_profile
4. Generates the Persona Block from the prose body
5. Returns a complete system-prompt injection string

Usage:
    from hummbl_governance.soul_injector import SoulInjector

    injector = SoulInjector()
    prompt = injector.inject("/path/to/SOUL.md")

Stdlib-only. Zero third-party dependencies.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from hummbl_governance.regulatory_context import RegulatoryContext


class SoulInjector:
    """Load SOUL.md files and generate system-prompt injection blocks."""

    def __init__(self) -> None:
        self._regulatory_ctx = RegulatoryContext()

    def inject(self, soul_path: str | Path) -> str:
        """Generate the full system-prompt injection for a SOUL.md file."""
        path = Path(soul_path)
        frontmatter, prose_body = self._parse_soul(path)
        resolved = self._resolve(path, frontmatter)

        gov = resolved.get("governance", {})
        if not isinstance(gov, dict):
            gov = {}
        profile = gov.get("regulatory_profile", "minimal-risk")
        agent_name = resolved.get("name", "unknown")

        blocks: list[str] = []

        if prose_body.strip():
            blocks.append(prose_body.strip())

        reg_block = self._regulatory_ctx.awareness_block(profile, agent_name=agent_name)
        blocks.append(reg_block)

        identity_lines = self._generate_identity_summary(resolved)
        if identity_lines:
            blocks.append(identity_lines)

        return "\n\n".join(blocks)

    def inject_persona_only(self, soul_path: str | Path) -> str:
        """Generate only the persona block (prose body)."""
        path = Path(soul_path)
        _, prose_body = self._parse_soul(path)
        return prose_body.strip()

    def inject_regulatory_only(self, soul_path: str | Path) -> str:
        """Generate only the Regulatory Awareness Block."""
        path = Path(soul_path)
        frontmatter, _ = self._parse_soul(path)
        resolved = self._resolve(path, frontmatter)
        gov = resolved.get("governance", {})
        if not isinstance(gov, dict):
            gov = {}
        profile = gov.get("regulatory_profile", "minimal-risk")
        agent_name = resolved.get("name", "unknown")
        return self._regulatory_ctx.awareness_block(profile, agent_name=agent_name)

    def get_resolved(self, soul_path: str | Path) -> dict[str, Any]:
        """Get the resolved frontmatter (with composition merged)."""
        path = Path(soul_path)
        frontmatter, _ = self._parse_soul(path)
        return self._resolve(path, frontmatter)

    def _generate_identity_summary(self, resolved: dict[str, Any]) -> str:
        """Generate a concise identity summary from resolved frontmatter."""
        gov = resolved.get("governance", {})
        if not isinstance(gov, dict):
            gov = {}
        lines = ["## Agent Identity", ""]
        name = resolved.get("name", "unknown")
        lines.append(f"**Name**: {name}")
        if gov.get("trust_tier"):
            lines.append(f"**Trust tier**: {gov['trust_tier']}")
        if gov.get("authority_scope"):
            lines.append(f"**Authority scope**: {gov['authority_scope']}")
        if gov.get("doctrine_stage"):
            lines.append(f"**Doctrine stage**: {gov['doctrine_stage']}")
        if gov.get("regulatory_profile"):
            lines.append(f"**Regulatory profile**: {gov['regulatory_profile']}")
        if gov.get("delegation_required"):
            lines.append("**Delegation required**: yes — must hold DCT for consequential actions")
        allowed = gov.get("allowed_tools", [])
        if isinstance(allowed, list) and allowed:
            lines.append(f"**Allowed tools**: {', '.join(allowed)}")
        prohibited = gov.get("prohibited_actions", [])
        if isinstance(prohibited, list) and prohibited:
            lines.append(f"**Prohibited actions**: {', '.join(prohibited)}")
        lines.append("")
        return "\n".join(lines)

    def _parse_soul(self, path: Path) -> tuple[dict[str, Any], str]:
        """Parse a SOUL.md file into (frontmatter, prose_body)."""
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        fm = self._parse_yaml(parts[1].strip("\n"))
        return fm, parts[2].strip("\n")

    def _resolve(self, path: Path, frontmatter: dict[str, Any]) -> dict[str, Any]:
        """Resolve composition (extends + mixins) with deep merge."""
        comp = frontmatter.get("composition", {})
        if not isinstance(comp, dict) or not comp:
            return frontmatter
        base_dir = path.parent.parent / "_base" if path.parent.name != "_base" else path.parent
        merged: dict[str, Any] = {}
        extends = comp.get("extends", "")
        if extends:
            for ext in [base_dir / f"{extends}.soul.md", base_dir / f"{extends}.md"]:
                if ext.exists():
                    parent_fm, _ = self._parse_soul(ext)
                    merged = self._deep_merge(merged, self._resolve(ext, parent_fm))
                    break
        for mixin in comp.get("mixins", []):
            for ext in [base_dir / f"{mixin}.soul.md", base_dir / f"{mixin}.md"]:
                if ext.exists():
                    mixin_fm, _ = self._parse_soul(ext)
                    merged = self._deep_merge(merged, self._resolve(ext, mixin_fm))
                    break
        return self._deep_merge(merged, frontmatter)

    def _deep_merge(self, base: dict, overlay: dict) -> dict:
        """Deep merge: overlay overrides base. Governance block is replaced entirely."""
        result = dict(base)
        for key, val in overlay.items():
            if key == "governance":
                result[key] = val
            elif key in result:
                if isinstance(result[key], dict) and isinstance(val, dict):
                    result[key] = self._deep_merge(result[key], val)
                elif isinstance(result[key], list) and isinstance(val, list):
                    seen = set()
                    merged = []
                    for item in result[key] + val:
                        if isinstance(item, str):
                            if item not in seen:
                                seen.add(item)
                                merged.append(item)
                        else:
                            merged.append(item)
                    result[key] = merged
                else:
                    result[key] = val
            else:
                result[key] = val
        return result

    def _parse_yaml(self, text: str) -> dict[str, Any]:
        """Parse restricted YAML subset (same as soul_md_parser.py)."""
        lines: list[tuple[int, str, str]] = []
        for raw in text.split("\n"):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip())
            if stripped.startswith("- "):
                lines.append((indent, "LIST_ITEM", stripped[2:].strip()))
            elif ":" in stripped:
                lines.append((indent, "KEY_VAL", stripped))
            else:
                lines.append((indent, "BARE", stripped))

        def _build(start: int, parent_indent: int) -> tuple[Any, int]:
            if start >= len(lines):
                return {}, start
            first_indent = lines[start][0]
            if first_indent <= parent_indent:
                return {}, start
            is_list = lines[start][1] == "LIST_ITEM"
            result_list: list[Any] = []
            result_dict: dict[str, Any] = {}
            i = start
            while i < len(lines):
                indent, kind, content = lines[i]
                if indent <= parent_indent:
                    break
                if indent != first_indent:
                    i += 1
                    continue
                if kind == "LIST_ITEM":
                    if i + 1 < len(lines) and lines[i + 1][0] > indent:
                        nested, i = _build(i + 1, indent)
                        if is_list:
                            result_list.append(nested)
                    else:
                        val = self._parse_val(content)
                        if ":" in content and not content.startswith('"'):
                            parts = content.split(":", 1)
                            k = parts[0].strip().strip('"').strip("'")
                            v_str = parts[1].strip()
                            if v_str:
                                if is_list:
                                    result_list.append({k: self._parse_val(v_str)})
                            else:
                                nested, i = _build(i + 1, indent)
                                if is_list:
                                    result_list.append({k: nested})
                        else:
                            if is_list:
                                result_list.append(val)
                        i += 1
                elif kind == "KEY_VAL":
                    parts = content.split(":", 1)
                    key = parts[0].strip().strip('"').strip("'")
                    value_str = parts[1].strip()
                    if not value_str:
                        if i + 1 < len(lines) and lines[i + 1][0] > indent:
                            nested, i = _build(i + 1, indent)
                            if not is_list:
                                result_dict[key] = nested
                        else:
                            if not is_list:
                                result_dict[key] = {}
                            i += 1
                    else:
                        if not is_list:
                            result_dict[key] = self._parse_val(value_str)
                        i += 1
                else:
                    i += 1
            return (result_list if is_list else result_dict, i)

        built, _ = _build(0, -1)
        return built if isinstance(built, dict) else {}

    @staticmethod
    def _parse_val(value: str) -> Any:
        value = value.strip()
        if not value:
            return ""
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [SoulInjector._parse_val(v.strip()) for v in inner.split(",")]
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() in ("null", "~"):
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value
