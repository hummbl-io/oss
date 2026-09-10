import os
import time
import json
import logging
import urllib.request
import urllib.error
from state import GovernanceState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnichannel-d1-sync")

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = "9e594f1cde6d3f71abb954efa5c717b4"
DATABASE_ID = "1b946dd8-a70e-45d6-b699-cbdbf8df2cfb"


def run_d1_query(sql: str, params: list = None):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
    payload = json.dumps({"sql": sql, "params": params or []}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {CLOUDFLARE_API_TOKEN}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not data.get("success"):
                raise RuntimeError(f"D1 query failed: {data.get('errors')}")
            return data["result"][0].get("results", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"D1 API HTTP Error ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"D1 API request failed: {str(e)}")


def sync_drafts(gov_state: GovernanceState):
    logger.info("Fetching new drafts from D1...")
    try:
        # Fetch drafts from D1
        results = run_d1_query("SELECT * FROM drafts WHERE status='draft'")

        if not results:
            logger.debug("No new drafts found.")
            return

        for row in results:
            draft_id = row["id"]
            target = row["target"]
            urgency = row["urgency"]
            content = row["content"]

            logger.info(f"Syncing draft {draft_id} from D1...")

            # Create in local SQLite
            gov_state.create_draft(target=target, urgency=urgency, content=content)

            # Mark as synced in D1 so we don't fetch it again
            run_d1_query("UPDATE drafts SET status='synced' WHERE id = ?", [draft_id])
            logger.info(f"Draft {draft_id} successfully synced and marked in D1.")

    except Exception as e:
        logger.error(f"Error syncing from D1: {e}")


def main():
    if not CLOUDFLARE_API_TOKEN:
        logger.error(
            "CLOUDFLARE_API_TOKEN environment variable is missing. Cannot sync D1."
        )
        return

    gov_state = GovernanceState()
    logger.info(
        f"Starting D1 to SQLite continuous sync loop for account {ACCOUNT_ID}..."
    )

    while True:
        sync_drafts(gov_state)
        time.sleep(10)  # poll every 10 seconds


if __name__ == "__main__":
    main()
