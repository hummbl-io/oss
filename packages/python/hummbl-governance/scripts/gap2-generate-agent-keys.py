#!/usr/bin/env python3
"""Gap-2: Generate GPG keys for 5 fleet agents.

Generates EdDSA/ed25519 keys with no protection (automated signing),
2y expiry, @hummbl.io email. Operator-authorized (gap-2 remediation).

Usage:
    python scripts/gap2-generate-agent-keys.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

AGENTS = ["devin", "codex", "claude-code", "opencode", "gemini"]

KEY_PARAMS_TEMPLATE = """%no-protection
Key-Type: EdDSA
Key-Curve: ed25519
Subkey-Type: EdDSA
Subkey-Curve: ed25519
Name-Real: {agent}
Name-Email: {agent}@hummbl.io
Expire-Date: 2y
%commit
"""


def generate_key(agent: str) -> dict:
    """Generate a GPG key for an agent. Returns result dict."""
    params = KEY_PARAMS_TEMPLATE.format(agent=agent)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpg-batch", delete=False) as f:
        f.write(params)
        params_path = f.name
    try:
        r = subprocess.run(
            ["gpg", "--batch", "--generate-key", params_path],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return {"agent": agent, "result": "error", "error": r.stderr[:200]}
        return {"agent": agent, "result": "generated"}
    except Exception as e:
        return {"agent": agent, "result": "error", "error": str(e)[:200]}
    finally:
        Path(params_path).unlink(missing_ok=True)


def get_fingerprint(agent: str) -> str:
    """Get the fingerprint for an agent's key."""
    r = subprocess.run(
        ["gpg", "--list-secret-keys", "--keyid-format=long",
         "--with-colons", f"{agent}@hummbl.io"],
        capture_output=True, text=True, timeout=10
    )
    # Parse colon format: fpr:::FINGERPRINT:
    for line in r.stdout.split("\n"):
        if line.startswith("fpr:") and ":::" in line:
            parts = line.split(":")
            if len(parts) >= 10:
                return parts[9]
    return ""


def main():
    import json
    results = []
    fingerprints = {}
    for agent in AGENTS:
        print(f"Generating key for {agent}...", file=sys.stderr)
        res = generate_key(agent)
        results.append(res)
        if res["result"] == "generated":
            fp = get_fingerprint(agent)
            fingerprints[agent] = fp
            print(f"  {agent}: {fp}", file=sys.stderr)
        else:
            print(f"  {agent}: FAILED - {res.get('error','')}", file=sys.stderr)
    output = {
        "agent_fingerprints": fingerprints,
        "results": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
