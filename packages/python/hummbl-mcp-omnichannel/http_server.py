"""Omnichannel ingress HTTP server -- stdlib only.

Replaces the original FastAPI/uvicorn implementation with
http.server.BaseHTTPRequestHandler + ThreadingHTTPServer.

Endpoints:
    POST /api/v1/webhooks/vapi/escalation  -- Vapi escalation webhook
    GET  /health                            -- health check
"""

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from state import GovernanceState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnichannel-ingress")

gov_state = GovernanceState()

_DEFAULT_PORT = 18795


class _Handler(BaseHTTPRequestHandler):
    """Request handler for omnichannel ingress."""

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "healthy", "service": "omnichannel-ingress"})
        else:
            self._send_json(404, {"detail": "Not Found"})

    def do_POST(self) -> None:
        if self.path != "/api/v1/webhooks/vapi/escalation":
            self._send_json(404, {"detail": "Not Found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            payload = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"detail": "Invalid JSON payload"})
            return

        logger.info("Received Vapi escalation webhook")
        logger.debug(f"Payload: {json.dumps(payload)}")

        # Vapi wraps tool calls in a specific structure.
        # We gracefully attempt to parse the arguments out.
        args: dict = {}

        # 1. Check if it's a raw test payload (just the args)
        if "issue_summary" in payload or "transcript_excerpt" in payload:
            args = payload

        # 2. Check if it's a Vapi Server Message wrapper
        elif "message" in payload and payload["message"].get("type") == "tool-calls":
            tool_list = payload["message"].get("toolWithToolCallList", [])
            for item in tool_list:
                tool_call = item.get("toolCall", {}).get("function", {})
                if tool_call.get("name") == "escalate_to_governance_gate":
                    args = tool_call.get("arguments", {})
                    break

        if not args:
            # If we can't parse it nicely, stringify the whole payload as the context
            logger.warning(
                "Could not extract expected tool arguments from payload. "
                "Falling back to raw stringification."
            )
            args = {
                "issue_summary": "Unknown External Escalation",
                "urgency": "high",
                "caller_context": "Vapi Raw Payload",
                "transcript_excerpt": json.dumps(payload),
            }

        # Format into a clean draft
        urgency = args.get("urgency", "high").lower()
        if urgency not in ["low", "normal", "high", "critical"]:
            urgency = "high"

        content = (
            f"**Voice Escalation Request**\n"
            f"**Summary**: {args.get('issue_summary', 'N/A')}\n"
            f"**Specialist Area**: {args.get('specialist_area', 'General')}\n"
            f"**Caller Context**: {args.get('caller_context', 'N/A')}\n"
            f"**Troubleshooting Attempted**: {args.get('troubleshooting_attempted', 'N/A')}\n\n"
            f"**Transcript Excerpt**:\n{args.get('transcript_excerpt', 'N/A')}"
        )

        try:
            # We assign it to the 'triage_queue' target for the swarm to review
            draft = gov_state.create_draft(
                target="triage_queue", urgency=urgency, content=content
            )
            logger.info(f"Created draft {draft.id} successfully.")
        except Exception as e:
            logger.error(f"Failed to create draft: {e}")
            self._send_json(500, {"detail": "Database write failed"})
            return

        # Vapi expects a standard response for custom tools so the agent can acknowledge the user
        tool_call_id = (
            payload.get("message", {})
            .get("toolWithToolCallList", [{}])[0]
            .get("toolCall", {})
            .get("id", "unknown")
        )
        self._send_json(200, {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": "Ticket escalated successfully. A specialist from the governance team will review it asynchronously.",
                }
            ]
        })

    def log_message(self, fmt: str, *args) -> None:
        # Route through logging instead of stderr
        logger.info(fmt % args)


def main() -> None:
    """Run the omnichannel ingress HTTP server."""
    server = ThreadingHTTPServer(("0.0.0.0", _DEFAULT_PORT), _Handler)
    logger.info(f"Omnichannel ingress listening on 0.0.0.0:{_DEFAULT_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
