import os
import tempfile
import uuid
from state import GovernanceState


def test_governance_state_lifecycle():
    """Test draft create -> list -> approve -> verify lifecycle."""
    db_path = os.path.join(tempfile.gettempdir(), f"test_gov_{uuid.uuid4().hex}.db")
    try:
        gov = GovernanceState(db_path)

        # 1. Create a draft
        msg = gov.create_draft("human_operator", "high", "System is down!")
        assert msg.id is not None
        assert msg.status == "draft"

        # 2. List pending drafts
        drafts = gov.list_pending_drafts()
        assert len(drafts) == 1
        assert drafts[0].id == msg.id

        # 3. Approve it
        success = gov.update_status(msg.id, "approved")
        assert success

        # 4. Check status
        updated = gov.get_message(msg.id)
        assert updated.status == "approved"

        # 5. Check pending again
        drafts = gov.list_pending_drafts()
        assert len(drafts) == 0
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except PermissionError:
                pass  # Windows may still hold a brief lock
