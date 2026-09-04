# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""CLI entry point for SOUL.md injection.

Usage:
    hummbl-soul inject <path>       # Full system-prompt injection
    hummbl-soul persona <path>      # Persona block only
    hummbl-soul regulatory <path>   # Regulatory awareness block only
    hummbl-soul resolve <path>      # Resolved frontmatter (JSON)
    hummbl-soul validate <path>     # Validate SOUL.md schema
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from hummbl_governance.soul_injector import SoulInjector


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    cmd = sys.argv[1]
    path = Path(sys.argv[2])
    injector = SoulInjector()

    if cmd == "inject":
        print(injector.inject(path))
        return 0
    elif cmd == "persona":
        print(injector.inject_persona_only(path))
        return 0
    elif cmd == "regulatory":
        print(injector.inject_regulatory_only(path))
        return 0
    elif cmd == "resolve":
        resolved = injector.get_resolved(path)
        print(json.dumps(resolved, indent=2, default=str))
        return 0
    elif cmd == "validate":
        resolved = injector.get_resolved(path)
        gov = resolved.get("governance", {})
        if not isinstance(gov, dict):
            gov = {}
        name = resolved.get("name", "unknown")
        profile = gov.get("regulatory_profile", "none")
        required = ["name", "version", "description", "personality"]
        missing = [f for f in required if f not in resolved]
        if missing:
            print(f"INVALID: missing required fields: {missing}")
            return 1
        print(f"VALID: {name} (profile={profile})")
        return 0
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
