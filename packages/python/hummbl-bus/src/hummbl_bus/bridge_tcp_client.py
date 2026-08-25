#!/usr/bin/env python3
"""
TCP Bridge Client - Posts to raw TCP socket bridges (like MacBook Pro's netcat bridge).

Usage:
    python -m hummbl_bus.bridge_tcp_client <host> <port> <from> <to> <type> <message>
"""

import argparse
import socket
import sys
from datetime import UTC, datetime


def post_to_tcp_bridge(
    host: str, port: int, from_agent: str, to_agent: str, msg_type: str, message: str
) -> bool:
    """Post a TSV message to a raw TCP bridge."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Escape tabs/newlines in message for TSV safety
    safe_message = message.replace("\t", " ").replace("\n", "\\n").replace("\r", "")

    # Build TSV line: timestamp\tfrom\tto\ttype\tmessage
    tsv_line = f"{timestamp}\t{from_agent}\t{to_agent}\t{msg_type}\t{safe_message}\n"

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        sock.sendall(tsv_line.encode("utf-8"))
        sock.close()
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Post to raw TCP bridge")
    parser.add_argument("host", help="Remote host IP")
    parser.add_argument("port", type=int, help="Remote port")
    parser.add_argument("from_agent", help="From agent ID")
    parser.add_argument("to_agent", help="To agent ID")
    parser.add_argument("msg_type", help="Message type")
    parser.add_argument("message", nargs="+", help="Message content")

    args = parser.parse_args()

    success = post_to_tcp_bridge(
        args.host,
        args.port,
        args.from_agent,
        args.to_agent,
        args.msg_type,
        " ".join(args.message),
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
