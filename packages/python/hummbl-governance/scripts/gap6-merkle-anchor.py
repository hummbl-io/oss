#!/usr/bin/env python3
"""Gap-6: Activate Merkle anchoring on the coordination bus.

Hashes bus entries, generates Signed Tree Heads (STHs), and publishes
them to GitHub gists for external tamper-evidence.

Operator decision (2026-08-27): GitHub gist per-machine.

Three modes:
    anchor   - Hash bus entries, generate STH, publish to gist
    verify   - Verify local bus against published STH
    history  - Show STH history from gist

Usage:
    python scripts/gap6-merkle-anchor.py anchor [--bus-path PATH] [--machine NAME]
    python scripts/gap6-merkle-anchor.py verify [--bus-path PATH] [--machine NAME]
    python scripts/gap6-merkle-anchor.py history [--machine NAME]

NIST 800-53 SC-8 (Transmission Integrity), SC-16 (Transmission of
Security Attributes).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add the package to path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

from hummbl_governance.primitives.merkle_anchor import (
    MerkleTree,
    SignedTreeHead,
    anchor_tuple_log,
)


def find_bus_file() -> Path:
    """Find the coordination bus file.

    Uses BUS_PATH env var. No hardcoded local paths — this is a public repo.
    """
    bus_env = os.environ.get("BUS_PATH", "")
    if bus_env:
        return Path(bus_env)
    raise FileNotFoundError(
        "BUS_PATH env var not set. Set it to your coordination bus TSV path."
    )


def hash_bus_entries(bus_path: Path) -> list[str]:
    """Hash each line of the bus TSV file.

    Returns a list of SHA-256 hashes, one per non-empty line.
    """
    if not bus_path.exists():
        print(f"ERROR: Bus file not found: {bus_path}", file=sys.stderr)
        return []

    hashes = []
    with open(bus_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if line:
                hashes.append(hashlib.sha256(line.encode("utf-8")).hexdigest())
    return hashes


def generate_sth(hashes: list[str], machine: str) -> dict:
    """Generate a Signed Tree Head from bus entry hashes.

    Returns a dict with the STH data (JSON-serializable).
    """
    if not hashes:
        return {
            "machine": machine,
            "tree_size": 0,
            "root_hash": "",
            "timestamp": int(time.time()),
            "entry_count": 0,
        }

    tree = MerkleTree()
    for h in hashes:
        tree.append(h)

    root = tree.root_hash()
    timestamp = int(time.time())

    return {
        "machine": machine,
        "tree_size": tree.size(),
        "root_hash": root,
        "timestamp": timestamp,
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp)),
        "entry_count": len(hashes),
        "first_entry_hash": hashes[0],
        "last_entry_hash": hashes[-1],
    }


def publish_to_gist(sth: dict, machine: str, dry_run: bool = False) -> str:
    """Publish STH to a GitHub gist.

    Returns the gist URL or empty string on failure.
    """
    gist_content = json.dumps(sth, indent=2)
    gist_filename = f"bus-sth-{machine}.json"

    if dry_run:
        print(f"[DRY RUN] Would publish STH to gist: {gist_filename}")
        print(f"[DRY RUN] Content:\n{gist_content}")
        return f"dry-run://gist/{gist_filename}"

    # Use gh CLI to create/update a gist
    try:
        # Check if gist already exists (by filename)
        result = subprocess.run(
            ["gh", "gist", "list"],
            capture_output=True, text=True, timeout=10
        )
        existing_gist_id = None
        for line in result.stdout.split("\n"):
            if gist_filename in line:
                parts = line.split()
                if parts:
                    existing_gist_id = parts[0]
                    break

        if existing_gist_id:
            # Update existing gist
            result = subprocess.run(
                ["gh", "gist", "edit", existing_gist_id, "--filename", gist_filename],
                input=gist_content, capture_output=True, text=True, timeout=10
            )
        else:
            # Create new gist
            result = subprocess.run(
                ["gh", "gist", "create", "--public", "--filename", gist_filename,
                 "--desc", f"HUMMBL bus STH for {machine}"],
                input=gist_content, capture_output=True, text=True, timeout=10
            )

        if result.returncode == 0:
            gist_url = result.stdout.strip()
            return gist_url
        else:
            print(f"ERROR: gh gist command failed: {result.stderr}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"ERROR: Failed to publish gist: {e}", file=sys.stderr)
        return ""


def anchor(bus_path: Path, machine: str, dry_run: bool = False) -> int:
    """Hash bus entries, generate STH, publish to gist."""
    print(f"Hashing bus entries from: {bus_path}", file=sys.stderr)
    hashes = hash_bus_entries(bus_path)

    if not hashes:
        print("No bus entries to anchor.", file=sys.stderr)
        return 1

    print(f"Found {len(hashes)} bus entries.", file=sys.stderr)

    sth = generate_sth(hashes, machine)
    print(f"STH: tree_size={sth['tree_size']}, root={sth['root_hash'][:16]}...", file=sys.stderr)

    gist_url = publish_to_gist(sth, machine, dry_run)
    if gist_url:
        print(f"Published STH to: {gist_url}", file=sys.stderr)
        # Output STH as JSON to stdout
        sth["gist_url"] = gist_url
        print(json.dumps(sth, indent=2))
        return 0
    else:
        print("Failed to publish STH.", file=sys.stderr)
        return 1


def verify(bus_path: Path, machine: str) -> int:
    """Verify local bus against published STH."""
    print(f"Verifying bus integrity for machine: {machine}", file=sys.stderr)

    # Get published STH from gist
    gist_filename = f"bus-sth-{machine}.json"
    try:
        result = subprocess.run(
            ["gh", "gist", "list"],
            capture_output=True, text=True, timeout=10
        )
        gist_id = None
        for line in result.stdout.split("\n"):
            if gist_filename in line:
                parts = line.split()
                if parts:
                    gist_id = parts[0]
                    break

        if not gist_id:
            print(f"ERROR: No published STH found for {machine}", file=sys.stderr)
            return 1

        result = subprocess.run(
            ["gh", "gist", "view", gist_id, "--raw"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"ERROR: Failed to fetch STH: {result.stderr}", file=sys.stderr)
            return 1

        published_sth = json.loads(result.stdout)
    except Exception as e:
        print(f"ERROR: Failed to get published STH: {e}", file=sys.stderr)
        return 1

    # Hash current bus entries
    hashes = hash_bus_entries(bus_path)
    if not hashes:
        print("ERROR: No bus entries to verify.", file=sys.stderr)
        return 1

    # Generate current STH
    current_sth = generate_sth(hashes, machine)

    # Compare
    pub_size = published_sth.get("tree_size", 0)
    pub_root = published_sth.get("root_hash", "")
    cur_size = current_sth["tree_size"]
    cur_root = current_sth["root_hash"]

    print(f"Published STH: tree_size={pub_size}, root={pub_root[:16]}...", file=sys.stderr)
    print(f"Current STH:   tree_size={cur_size}, root={cur_root[:16]}...", file=sys.stderr)

    if cur_size < pub_size:
        print(f"ALERT: Bus has FEWER entries than published STH ({cur_size} < {pub_size})!", file=sys.stderr)
        print("Bus entries may have been deleted (tampering).", file=sys.stderr)
        return 1

    if cur_size == pub_size:
        if cur_root == pub_root:
            print("VERIFIED: Bus matches published STH.", file=sys.stderr)
            return 0
        else:
            print("ALERT: Root hash mismatch! Bus entries may have been modified.", file=sys.stderr)
            return 1

    # cur_size > pub_size — new entries since last anchor (expected)
    # Verify the prefix matches
    tree = MerkleTree()
    for h in hashes[:pub_size]:
        tree.append(h)
    prefix_root = tree.root_hash()

    if prefix_root == pub_root:
        print(f"VERIFIED: First {pub_size} entries match published STH.", file=sys.stderr)
        print(f"  {cur_size - pub_size} new entries since last anchor.", file=sys.stderr)
        return 0
    else:
        print(f"ALERT: First {pub_size} entries do NOT match published STH!", file=sys.stderr)
        print("Bus history may have been tampered with.", file=sys.stderr)
        return 1


def history(machine: str) -> int:
    """Show STH history from gist."""
    gist_filename = f"bus-sth-{machine}.json"
    try:
        result = subprocess.run(
            ["gh", "gist", "list"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if gist_filename in line:
                print(line)
                return 0
        print(f"No STH found for machine: {machine}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Gap-6: Merkle anchoring for bus integrity")
    parser.add_argument("mode", choices=["anchor", "verify", "history"],
                        help="anchor: generate+publish STH, verify: check bus, history: show STH")
    parser.add_argument("--bus-path", default="", help="Path to bus TSV file")
    parser.add_argument("--machine", default=os.environ.get("MACHINE_NAME", "unknown"),
                        help="Machine name (default: unknown or MACHINE_NAME env)")
    parser.add_argument("--dry-run", action="store_true", help="Don't publish, just print")
    args = parser.parse_args()

    bus_path = Path(args.bus_path) if args.bus_path else find_bus_file()

    if args.mode == "anchor":
        return anchor(bus_path, args.machine, args.dry_run)
    elif args.mode == "verify":
        return verify(bus_path, args.machine)
    elif args.mode == "history":
        return history(args.machine)

    return 0


if __name__ == "__main__":
    sys.exit(main())
