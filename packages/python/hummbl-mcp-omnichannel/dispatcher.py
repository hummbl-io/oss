import json
import time
import subprocess
import os
from state import GovernanceState


def dispatch_to_signal(target: str, content: str) -> bool:
    # Delegate to the standalone S2 hummbl-mcp-signal server via stdio
    cmd = [
        "uv",
        "run",
        "--directory",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "signal"),
        "hummbl-mcp-signal",
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # We need to wrap the call in JSON-RPC
        req_id = "1"
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {
                "name": "signal_send_message",
                "arguments": {"target": target, "content": content},
            },
        }

        stdout_data, stderr_data = proc.communicate(
            input=json.dumps(payload) + "\n", timeout=30
        )

        if proc.returncode != 0:
            print(f"[Dispatcher] Signal MCP server crashed: {stderr_data}")
            return False

        for line in stdout_data.strip().split("\n"):
            try:
                response = json.loads(line)
                if response.get("id") == req_id:
                    if "error" in response:
                        print(
                            f"[Dispatcher] Signal dispatch failed: {response['error']}"
                        )
                        return False
                    return True
            except json.JSONDecodeError:
                continue

        return False
    except Exception as e:
        print(f"[Dispatcher] Signal MCP dispatch failed: {e}")
        return False


def run_dispatch_loop():
    gov = GovernanceState()
    print("Omnichannel Governance Dispatcher started.")
    print("Watching for 'approved' drafts...")

    while True:
        try:
            # Note: We'd normally have a method list_approved_drafts, but since this is an MVP
            # we can query directly or add the method. Let's add it to state.py in a real pass.
            import sqlite3

            with sqlite3.connect(gov.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM messages WHERE status = 'approved' AND platform IS NULL"
                ).fetchall()

                for row in rows:
                    msg_id = row["id"]
                    target = row["target"]
                    urgency = row["urgency"]
                    content = row["content"]

                    print(
                        f"Dispatching approved message {msg_id} (Urgency: {urgency}) to {target}"
                    )

                    # Routing Logic
                    if urgency in ["high", "critical"]:
                        # High urgency routes to Signal for secure/direct delivery
                        success = dispatch_to_signal(target, content)
                        if success:
                            gov.update_status(msg_id, "dispatched", platform="signal")
                        else:
                            gov.update_status(
                                msg_id,
                                "failed",
                                error_msg="Signal CLI execution failed",
                            )
                    else:
                        # Normal/Low routes to Discord or Email (mocked for now)
                        print(f"Mock dispatching to Discord: {target}")
                        gov.update_status(msg_id, "dispatched", platform="discord")

        except Exception as e:
            print(f"Dispatcher error: {e}")

        time.sleep(5)


if __name__ == "__main__":
    run_dispatch_loop()
