#!/usr/bin/env python3
"""
Bus Bridge Client - Post messages to remote machine's coordination bus.

Usage:
    python -m hummbl_bus.bridge_client <host> <from> <to> <type> <message>
    python -m hummbl_bus.bridge_client 100.120.13.37 kimi-mini kimi-mbp STATUS "Hello from Mac Mini"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from pathlib import Path

DEFAULT_PORT = 18790
DEFAULT_TOKEN_FILE = Path.home() / ".config" / "hummbl-bus" / "bus_bridge_token"


def _load_bridge_token(explicit_token: str | None = None) -> str:
    """Load bridge token from explicit argument, env var, or config file."""
    if explicit_token is not None:
        return explicit_token.strip()
    env_token = os.environ.get("BUS_BRIDGE_TOKEN", "").strip().lstrip("\ufeff")
    if env_token:
        return env_token
    token_file_env = os.environ.get("BUS_BRIDGE_TOKEN_PATH")
    token_path = Path(token_file_env) if token_file_env else DEFAULT_TOKEN_FILE
    if token_path.exists():
        try:
            return token_path.read_text(encoding="utf-8-sig").strip().lstrip("\ufeff")
        except OSError:
            return ""
    return ""


def _request_headers(
    *,
    bearer_token: str | None = None,
    client_id: str | None = None,
) -> dict[str, str]:
    """Build bridge headers without logging or serializing credentials."""
    token = _load_bridge_token(bearer_token)
    effective_client_id = (
        client_id
        if client_id is not None
        else os.environ.get("BUS_BRIDGE_CLIENT_ID", "")
    ).strip()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if effective_client_id:
        headers["X-Bridge-Client-ID"] = effective_client_id
    return headers


def post_to_remote_bus(
    host: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    port: int = DEFAULT_PORT,
    *,
    bearer_token: str | None = None,
    client_id: str | None = None,
) -> bool:
    """Post a message to a remote machine's bus via HTTP."""
    url = f"http://{host}:{port}/bus"

    data = json.dumps(
        {"from": from_agent, "to": to_agent, "type": msg_type, "message": message}
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers=_request_headers(
            bearer_token=bearer_token,
            client_id=client_id,
        ),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        try:
            body = e.read().decode()
            print(f"Response: {body}", file=sys.stderr)
        except Exception:
            pass  # Best-effort error body read
        return False
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def post_to_remote_bus_result(
    host: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    *,
    timestamp: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
    principal_proof: str | None = None,
    bearer_token: str | None = None,
    client_id: str | None = None,
    port: int = DEFAULT_PORT,
) -> dict[str, object]:
    """Post a message to a remote machine's bus and return a structured result dict.

    Adapter wrapping the bool-returning ``post_to_remote_bus`` into the result
    shape that ``replay_worker`` expects: ``{"ok": bool, "duplicate": bool,
    "permanent_error": bool, "status_code": int|None, "error": str}``.

    Optional request metadata and principal proof are forwarded to the bridge.
    A genuine idempotent replay is a successful HTTP 200 response with
    ``duplicate=true``. HTTP 409 instead means that the idempotency key is
    already bound to a different request and is therefore a permanent error.
    """
    url = f"http://{host}:{port}/bus"
    payload: dict[str, object] = {
        "from": from_agent,
        "to": to_agent,
        "type": msg_type,
        "message": message,
    }
    if timestamp is not None:
        payload["timestamp"] = timestamp
    if request_id is not None:
        payload["request_id"] = request_id
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    if origin_machine is not None:
        payload["origin_machine"] = origin_machine
    if principal_proof is not None:
        payload["principal_proof"] = principal_proof
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers=_request_headers(
            bearer_token=bearer_token,
            client_id=client_id,
        ),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            try:
                response_data = json.loads(response_body) if response_body else {}
            except json.JSONDecodeError:
                response_data = {}
            duplicate = bool(
                isinstance(response_data, dict)
                and response_data.get("duplicate") is True
            )
            return {
                "ok": response.status == 200,
                "duplicate": duplicate,
                "permanent_error": False,
                "status_code": response.status,
                "error": "",
            }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        # Successful idempotent replays return HTTP 200 with duplicate=true.
        # HTTP 409 means the key is bound to a different request, so retrying
        # the same queued record cannot succeed.
        permanent = e.code in (400, 401, 403, 409, 413, 422)
        return {
            "ok": False,
            "duplicate": False,
            "permanent_error": permanent,
            "status_code": e.code,
            "error": body or str(e.reason),
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "duplicate": False,
            "permanent_error": False,
            "status_code": None,
            "error": str(e.reason),
        }
    except Exception as e:
        return {
            "ok": False,
            "duplicate": False,
            "permanent_error": False,
            "status_code": None,
            "error": str(e),
        }


def health_check(host: str, port: int = DEFAULT_PORT) -> bool:
    """Check if remote bridge is healthy."""
    url = f"http://{host}:{port}/health"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Post messages to remote coordination bus",
        usage="%(prog)s [-p PORT] <host> <from> <to> <type> <message>",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help="Remote port (default: 18790)",
    )
    parser.add_argument("--health", "-c", action="store_true", help="Health check only")
    parser.add_argument(
        "host", nargs="?", help="Remote host (Tailscale IP or hostname)"
    )
    parser.add_argument("from_agent", nargs="?", help="From agent ID")
    parser.add_argument("to_agent", nargs="?", help="To agent ID")
    parser.add_argument("msg_type", nargs="?", help="Message type")
    parser.add_argument("message", nargs="?", help="Message content")

    args = parser.parse_args()

    if args.health:
        if not args.host:
            print("Usage: --health requires <host>", file=sys.stderr)
            sys.exit(1)
        ok = health_check(args.host, args.port)
        print(f"Health check for {args.host}:{args.port}: {'OK' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)

    if not all(
        [args.host, args.from_agent, args.to_agent, args.msg_type, args.message]
    ):
        parser.print_help()
        sys.exit(1)

    success = post_to_remote_bus(
        args.host,
        args.from_agent,
        args.to_agent,
        args.msg_type,
        args.message,
        args.port,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
