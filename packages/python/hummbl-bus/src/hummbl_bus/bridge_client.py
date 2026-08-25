#!/usr/bin/env python3
"""
Bus Bridge Client - Post messages to remote machine's coordination bus.

Usage:
    python -m hummbl_bus.bridge_client <host> <from> <to> <type> <message>
    python -m hummbl_bus.bridge_client 100.120.13.37 kimi-mini kimi-mbp STATUS "Hello from Mac Mini"
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_PORT = 18790


def post_to_remote_bus(
    host: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    port: int = DEFAULT_PORT,
) -> bool:
    """Post a message to a remote machine's bus via HTTP."""
    url = f"http://{host}:{port}/bus"

    data = json.dumps(
        {"from": from_agent, "to": to_agent, "type": msg_type, "message": message}
    ).encode("utf-8")

    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
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
    port: int = DEFAULT_PORT,
) -> dict[str, object]:
    """Post a message to a remote machine's bus and return a structured result dict.

    Adapter wrapping the bool-returning ``post_to_remote_bus`` into the result
    shape that ``replay_worker`` expects: ``{"ok": bool, "duplicate": bool,
    "permanent_error": bool, "status_code": int|None, "error": str}``.

    Note: the underlying ``post_to_remote_bus`` does not currently forward
    request_id/correlation_id/origin_machine/principal_proof. Those fields are
    accepted for API compatibility with hummbl-governance's richer client but are
    not yet sent over the wire. Promote the full HTTP result machinery when
    the bridge server supports them.
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
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return {
                "ok": response.status == 200,
                "duplicate": False,
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
        # 409 Conflict is the conventional duplicate-rejection status
        duplicate = e.code == 409
        permanent = e.code in (400, 401, 403, 413, 422)
        return {
            "ok": False,
            "duplicate": duplicate,
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
