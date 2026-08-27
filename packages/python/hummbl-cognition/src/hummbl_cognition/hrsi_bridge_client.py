#!/usr/bin/env python3
"""HRSI Bridge Client — Post HRSI check-ins to a remote bridge server.

Mirrors bridge_client.py for the bus. Used by hrsi_checkin.py when
HRSI_CANONICAL_BRIDGE_URL is set, and by the mobile-hrsi skill.

Usage:
    python -m hummbl_cognition.hrsi_bridge_client <host> \\
        --cogstate AVAILABLE --safety 4 --mattering 3 --connection 4 \\
        --hule "Noticed pattern between X and Y"
    python -m hummbl_cognition.hrsi_bridge_client --health <host>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_PORT = 18791
DEFAULT_TOKEN_FILE = Path.home() / ".config" / "hummbl" / "hrsi_bridge_token"


def _load_bridge_token() -> str | None:
    """Load the HRSI bridge token from env or a mode-600 token file."""
    env_token = os.environ.get("HRSI_BRIDGE_TOKEN", "").strip()
    if env_token:
        return env_token

    token_file = os.environ.get("HRSI_BRIDGE_TOKEN_FILE", "").strip()
    candidate = Path(token_file).expanduser() if token_file else DEFAULT_TOKEN_FILE

    try:
        if candidate.exists():
            token = candidate.read_text(encoding="utf-8").strip()
            if token:
                return token
    except OSError:
        return None

    return None


def post_hrsi_to_bridge_url_result(
    base_url: str,
    *,
    cogstate: str,
    safety: int,
    mattering: int,
    connection: int,
    hule: str,
    lens: str | None = None,
    delta: str | None = None,
    energy: int | None = None,
    sleep_hours: float | None = None,
    relational_note: str | None = None,
    origin_machine: str | None = None,
    force: bool = False,
) -> dict:
    """Post an HRSI check-in to a remote bridge and return a structured result."""
    url = f"{base_url.rstrip('/')}/hrsi"

    body: dict = {
        "cogstate": cogstate,
        "safety": safety,
        "mattering": mattering,
        "connection": connection,
        "hule": hule,
    }
    if lens:
        body["lens"] = lens
    if delta:
        body["delta"] = delta
    if energy is not None:
        body["energy"] = energy
    if sleep_hours is not None:
        body["sleep_hours"] = sleep_hours
    if relational_note:
        body["relational_note"] = relational_note
    if origin_machine:
        body["origin_machine"] = origin_machine
    if force:
        body["force"] = True

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    token = _load_bridge_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = response.read().decode("utf-8")
            decoded = json.loads(payload) if payload else {}
            return {
                "ok": response.status == 200,
                "status_code": response.status,
                "body": decoded,
                "permanent_error": False,
            }
    except urllib.error.HTTPError as e:
        resp_body = {}
        try:
            payload = e.read().decode()
            resp_body = json.loads(payload) if payload else {}
        except Exception:
            resp_body = {}
        return {
            "ok": False,
            "status_code": e.code,
            "body": resp_body,
            "permanent_error": e.code in {400, 401, 403},
            "error": e.reason,
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "status_code": None,
            "body": {},
            "permanent_error": False,
            "error": str(e.reason),
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "body": {},
            "permanent_error": False,
            "error": str(e),
        }


def post_hrsi_to_bridge(
    host: str,
    *,
    cogstate: str,
    safety: int,
    mattering: int,
    connection: int,
    hule: str,
    port: int = DEFAULT_PORT,
    **kwargs,
) -> bool:
    """Post an HRSI check-in to a remote bridge. Returns True on success."""
    base_url = f"http://{host}:{port}"
    result = post_hrsi_to_bridge_url_result(
        base_url,
        cogstate=cogstate,
        safety=safety,
        mattering=mattering,
        connection=connection,
        hule=hule,
        **kwargs,
    )
    if not result["ok"]:
        status_code = result.get("status_code")
        if status_code is not None:
            print(f"HTTP Error {status_code}: {result.get('error')}", file=sys.stderr)
            if result.get("body"):
                print(f"Response: {json.dumps(result['body'])}", file=sys.stderr)
        else:
            print(f"Connection error: {result.get('error')}", file=sys.stderr)
    return bool(result["ok"])


def health_check(host: str, port: int = DEFAULT_PORT) -> bool:
    """Check if remote HRSI bridge is healthy."""
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post HRSI check-in to remote bridge",
    )
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT)
    parser.add_argument("--health", "-c", action="store_true")
    parser.add_argument("host", nargs="?")
    parser.add_argument("--cogstate", required=False)
    parser.add_argument("--safety", type=int, required=False)
    parser.add_argument("--mattering", type=int, required=False)
    parser.add_argument("--connection", type=int, required=False)
    parser.add_argument("--hule", required=False)
    parser.add_argument("--lens", required=False)
    parser.add_argument("--delta", required=False)
    parser.add_argument("--energy", type=int, required=False)
    parser.add_argument("--sleep", type=float, required=False)
    parser.add_argument("--relational-note", required=False)
    parser.add_argument("--origin-machine", required=False)

    args = parser.parse_args()

    if args.health:
        if not args.host:
            print("Usage: --health requires <host>", file=sys.stderr)
            sys.exit(1)
        ok = health_check(args.host, args.port)
        print(f"Health check for {args.host}:{args.port}: {'OK' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)

    if not args.host:
        parser.print_help()
        sys.exit(1)

    missing = []
    for f in ("cogstate", "safety", "mattering", "connection", "hule"):
        if getattr(args, f) is None:
            missing.append(f"--{f}")
    if missing:
        print(f"ERROR: requires {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    success = post_hrsi_to_bridge(
        args.host,
        cogstate=args.cogstate,
        safety=args.safety,
        mattering=args.mattering,
        connection=args.connection,
        hule=args.hule,
        port=args.port,
        lens=args.lens,
        delta=args.delta,
        energy=args.energy,
        sleep_hours=args.sleep,
        relational_note=args.relational_note,
        origin_machine=args.origin_machine,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
