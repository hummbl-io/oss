#!/usr/bin/env python3
"""Release-Registry Freshness Check.

Verifies version parity across the three release-authority surfaces:
1. pyproject.toml (source of truth for the package version)
2. PyPI (external registry — the published version)
3. hummbl-production manifest (delegated public-release-state surface)

Implements the freshness-check requirement from issue #251.

Usage:
    python scripts/release_registry_freshness.py
    python scripts/release_registry_freshness.py --json
    python scripts/release_registry_freshness.py --manifest-url <url>

Exit codes:
    0 = all surfaces in parity
    1 = version drift detected (surfaces disagree)
    2 = operational error (network failure, parse error)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/hummbl-io/hummbl-production/main/"
    "web/manifest/public-release-state.json"
)
PYPI_JSON_URL = "https://pypi.org/pypi/hummbl-governance/json"
PYPROJECT_PATH = "pyproject.toml"


def read_pyproject_version(repo_root: Path) -> str:
    """Extract the version from pyproject.toml."""
    content = (repo_root / PYPROJECT_PATH).read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version in {PYPROJECT_PATH}")
    return match.group(1)


def fetch_pypi_version() -> str:
    """Fetch the latest version from PyPI."""
    req = urllib.request.Request(PYPI_JSON_URL, headers={"User-Agent": "release-freshness-check/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["info"]["version"]


def fetch_manifest_version(manifest_url: str) -> dict:
    """Fetch the hummbl-production manifest and extract version fields.

    Tries the raw URL first, falls back to `gh api` for private repos.
    """
    data: dict
    try:
        req = urllib.request.Request(
            manifest_url, headers={"User-Agent": "release-freshness-check/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Private repo — fall back to gh api
            import subprocess
            result = subprocess.run(
                [
                    "gh", "api",
                    "repos/hummbl-io/hummbl-production/contents/"
                    "web/manifest/public-release-state.json",
                    "--jq", ".content",
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"gh api failed: {result.stderr.strip()}")
            import base64
            content = base64.b64decode(result.stdout.strip()).decode("utf-8")
            data = json.loads(content)
        else:
            raise

    latest = data.get("latest_version")
    source_state = data.get("source_state_version")
    generated_at = data.get("generated_at", "unknown")

    # If latest_version is empty/None, try to extract from verification_sources
    if not latest:
        sources = data.get("verification_sources", {})
        for key, val in sources.items():
            if "pypi" in key and "hummbl_governance" in key:
                match = re.search(r"/(\d+\.\d+\.\d+)/?", val)
                if match:
                    latest = match.group(1)
                    break

    return {
        "latest_version": latest or "NOT_FOUND",
        "source_state_version": source_state or "NOT_FOUND",
        "generated_at": generated_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Release-Registry Freshness Check")
    parser.add_argument("--repo", default=".", help="Path to hummbl-governance repo root")
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL, help="Manifest JSON URL")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()

    try:
        pyproject_version = read_pyproject_version(repo)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        pypi_version = fetch_pypi_version()
    except urllib.error.URLError as e:
        print(f"ERROR: PyPI fetch failed: {e}", file=sys.stderr)
        return 2

    try:
        manifest = fetch_manifest_version(args.manifest_url)
    except urllib.error.URLError as e:
        print(f"ERROR: Manifest fetch failed: {e}", file=sys.stderr)
        return 2

    surfaces = {
        "pyproject.toml": pyproject_version,
        "pypi": pypi_version,
        "hummbl-production manifest": manifest["latest_version"],
    }

    versions = set(surfaces.values())
    in_parity = len(versions) == 1
    manifest_stale = manifest["latest_version"] != pypi_version

    result = {
        "check": "release-registry-freshness",
        "timestamp": None,
        "surfaces": surfaces,
        "manifest_generated_at": manifest["generated_at"],
        "manifest_source_state_version": manifest["source_state_version"],
        "in_parity": in_parity,
        "manifest_stale": manifest_stale,
        "drift_detail": (
            None if in_parity
            else f"pyproject={pyproject_version}, pypi={pypi_version}, manifest={manifest['latest_version']}"
        ),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Release-Registry Freshness Check")
        print(f"  pyproject.toml:              {pyproject_version}")
        print(f"  PyPI latest:                 {pypi_version}")
        print(f"  manifest latest_version:     {manifest['latest_version']}")
        print(f"  manifest generated_at:       {manifest['generated_at']}")
        print(f"  manifest source_state:       {manifest['source_state_version']}")
        print(f"  In parity:                   {'YES' if in_parity else 'NO'}")
        if not in_parity:
            print(f"  Drift:                       {result['drift_detail']}")
            if manifest_stale:
                print(f"  Manifest is STALE — needs regeneration to match PyPI v{pypi_version}")

    return 0 if in_parity else 1


if __name__ == "__main__":
    sys.exit(main())
