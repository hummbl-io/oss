import sqlite3
import uuid
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class UniversalMessage:
    id: str
    target: str  # e.g., "human_operator", "public_feed", "+1234567890"
    urgency: str  # "low", "normal", "high", "critical"
    content: str
    status: str  # "draft", "approved", "rejected", "dispatched", "failed"
    created_at: str
    updated_at: str
    platform: Optional[str] = None  # Populated when dispatched
    error_msg: Optional[str] = None


class GovernanceState:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to a local sqlite file in the config dir
            config_dir = os.environ.get(
                "HUMMBL_CONFIG_DIR", os.path.expanduser("~/.gemini/config")
            )
            os.makedirs(config_dir, exist_ok=True)
            db_path = os.path.join(config_dir, "omnichannel_governance.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    platform TEXT,
                    error_msg TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def create_draft(self, target: str, urgency: str, content: str) -> UniversalMessage:
        now = datetime.utcnow().isoformat() + "Z"
        msg = UniversalMessage(
            id=str(uuid.uuid4()),
            target=target,
            urgency=urgency,
            content=content,
            status="draft",
            created_at=now,
            updated_at=now,
        )

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO messages (id, target, urgency, content, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    msg.id,
                    msg.target,
                    msg.urgency,
                    msg.content,
                    msg.status,
                    msg.created_at,
                    msg.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return msg

    def get_message(self, msg_id: str) -> Optional[UniversalMessage]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM messages WHERE id = ?", (msg_id,)
            ).fetchone()
            if not row:
                return None
            return UniversalMessage(**dict(row))
        finally:
            conn.close()

    def update_status(
        self, msg_id: str, new_status: str, platform: str = None, error_msg: str = None
    ) -> bool:
        now = datetime.utcnow().isoformat() + "Z"
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "UPDATE messages SET status = ?, updated_at = ?, platform = COALESCE(?, platform), error_msg = COALESCE(?, error_msg) WHERE id = ?",
                (new_status, now, platform, error_msg, msg_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_pending_drafts(self) -> List[UniversalMessage]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE status = 'draft' ORDER BY created_at ASC"
            ).fetchall()
            return [UniversalMessage(**dict(row)) for row in rows]
        finally:
            conn.close()
