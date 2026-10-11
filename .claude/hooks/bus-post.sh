#!/usr/bin/env bash
# Post one message to the HUMMBL coordination bus from a Claude Code session.
#
# Usage: .claude/hooks/bus-post.sh <to> <type> <message...>
#   e.g. .claude/hooks/bus-post.sh "*" STATUS "oss#292 CI green on c902d04"
#
# Routing, first match wins:
#   BUS_CANONICAL_BRIDGE_URL (+ BUS_BRIDGE_TOKEN or BUS_BRIDGE_TOKEN_PATH)
#       -> POST <url>/bus on the remote bridge (hummbl_bus.bridge_server)
#   COORDINATION_BUS
#       -> append to that local TSV via hummbl_bus.bus_writer_cli
#   neither
#       -> print and exit 0 (bus not configured in this environment)
#
# Sender is BUS_SENDER_ID (default: claude-code). A bridge that binds tokens
# to senders (BUS_SENDER_TOKENS_FILE) overrides this with the token's identity.
# Never fails the caller unless BUS_POST_STRICT=1.
set -uo pipefail

to="${1:?usage: bus-post.sh <to> <type> <message...>}"
msg_type="${2:?usage: bus-post.sh <to> <type> <message...>}"
shift 2
message="$*"

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
from_id="${BUS_SENDER_ID:-claude-code}"

# Agent-originated posts must carry a canonical host= tag (bus-protocol.md,
# Machine tagging). Cloud containers are not fleet machines, so the default is
# host=unknown; set BUS_ORIGIN_MACHINE to a canonical name to override.
case " $message" in
  *" host="*) ;;
  *) message="host=${BUS_ORIGIN_MACHINE:-unknown} surface=${BUS_ORIGIN_SURFACE:-claude-code-web} $message" ;;
esac

if [ -n "${BUS_CANONICAL_BRIDGE_URL:-}" ]; then
  "$PY" - "$BUS_CANONICAL_BRIDGE_URL" "$from_id" "$to" "$msg_type" "$message" <<'PYEOF'
import json
import sys
import urllib.error
import urllib.request

from hummbl_bus.bridge_client import _request_headers

url, from_id, to, msg_type, message = sys.argv[1:6]
payload = json.dumps(
    {"from": from_id, "to": to, "type": msg_type, "message": message}
).encode("utf-8")
req = urllib.request.Request(
    url.rstrip("/") + "/bus", data=payload, headers=_request_headers(), method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"bus: {from_id} -> {to} [{msg_type}] -> {url} ({resp.status})")
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")[:200]
    print(f"bus: bridge rejected ({exc.code}): {body}", file=sys.stderr)
    sys.exit(1)
except Exception as exc:  # network errors must never break the caller
    print(f"bus: bridge unreachable: {exc}", file=sys.stderr)
    sys.exit(1)
PYEOF
  rc=$?
elif [ -n "${COORDINATION_BUS:-}" ]; then
  "$PY" -c "import sys; from hummbl_bus.bus_writer_cli import main; sys.exit(main(sys.argv[1:]))" \
    "$from_id" "$to" "$msg_type" "$message"
  rc=$?
else
  echo "bus: not configured (set BUS_CANONICAL_BRIDGE_URL or COORDINATION_BUS); skipped [$msg_type] $message"
  rc=0
fi

if [ "${BUS_POST_STRICT:-0}" = "1" ]; then
  exit "$rc"
fi
exit 0
