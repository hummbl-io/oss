"""
Mission Mode Kernel Audit Trail Persistence

Implements file-based persistence for audit trails with HMAC signing for integrity verification.
"""

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditTrailPersistence:
    """
    File-based persistence for audit trails with HMAC signing.

    Audit trails are stored as JSON files with HMAC signatures for integrity verification.
    Files are organized by mission_id in a dedicated audit_trails directory.
    """

    def __init__(self, base_dir: str = "_state/audit_trails", signing_key: Optional[str] = None):
        """
        Initialize audit trail persistence.

        Args:
            base_dir: Base directory for audit trail storage
            signing_key: Optional HMAC signing key (defaults to environment variable)
        """
        self.base_dir = Path(base_dir)
        self.signing_key = signing_key or os.environ.get("MISSION_MODE_SIGNING_KEY")
        if not self.signing_key:
            raise ValueError(
                "AuditTrailPersistence requires a signing key. "
                "Pass signing_key= or set MISSION_MODE_SIGNING_KEY env var. "
                "Do not use a hardcoded default key."
            )

        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Audit trail persistence initialized: {self.base_dir}")

    def _get_audit_trail_path(self, audit_trail_id: str) -> Path:
        """Get file path for an audit trail"""
        return self.base_dir / f"{audit_trail_id}.json"

    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC-SHA256 signature for data"""
        return hmac.new(
            self.signing_key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _sign_audit_trail(self, audit_trail: Dict[str, Any]) -> Dict[str, Any]:
        """Add HMAC signature to audit trail"""
        # Serialize without signature field
        audit_trail_copy = audit_trail.copy()
        if "signature" in audit_trail_copy:
            del audit_trail_copy["signature"]

        audit_trail_json = json.dumps(audit_trail_copy, sort_keys=True)
        signature = self._compute_hmac(audit_trail_json)

        audit_trail["signature"] = signature
        return audit_trail

    def _verify_signature(self, audit_trail: Dict[str, Any]) -> bool:
        """Verify HMAC signature of audit trail"""
        if "signature" not in audit_trail:
            logger.warning("Audit trail missing signature")
            return False

        stored_signature = audit_trail["signature"]
        audit_trail_copy = audit_trail.copy()
        del audit_trail_copy["signature"]

        audit_trail_json = json.dumps(audit_trail_copy, sort_keys=True)
        computed_signature = self._compute_hmac(audit_trail_json)

        is_valid = hmac.compare_digest(stored_signature, computed_signature)
        if not is_valid:
            logger.warning("Audit trail signature verification failed")

        return is_valid

    def save_audit_trail(self, audit_trail: Dict[str, Any]) -> bool:
        """
        Save audit trail to disk with HMAC signature.

        Args:
            audit_trail: Audit trail dictionary

        Returns:
            True if save successful, False otherwise
        """
        try:
            audit_trail_id = audit_trail.get("audit_trail_id")
            if not audit_trail_id:
                logger.error("Audit trail missing audit_trail_id")
                return False

            # Sign the audit trail
            signed_trail = self._sign_audit_trail(audit_trail)

            # Save to file
            file_path = self._get_audit_trail_path(audit_trail_id)
            with open(file_path, "w") as f:
                json.dump(signed_trail, f, indent=2)

            logger.info(f"Saved audit trail: {audit_trail_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save audit trail: {e}")
            return False

    def load_audit_trail(self, audit_trail_id: str) -> Optional[Dict[str, Any]]:
        """
        Load audit trail from disk with signature verification.

        Args:
            audit_trail_id: Audit trail identifier

        Returns:
            Audit trail dictionary if found and valid, None otherwise
        """
        try:
            file_path = self._get_audit_trail_path(audit_trail_id)

            if not file_path.exists():
                logger.warning(f"Audit trail file not found: {audit_trail_id}")
                return None

            with open(file_path, "r") as f:
                audit_trail = json.load(f)

            # Verify signature
            if not self._verify_signature(audit_trail):
                logger.error(f"Invalid signature for audit trail: {audit_trail_id}")
                return None

            logger.info(f"Loaded audit trail: {audit_trail_id}")
            return audit_trail

        except Exception as e:
            logger.error(f"Failed to load audit trail: {e}")
            return None

    def list_audit_trails(self, mission_id: Optional[str] = None) -> List[str]:
        """
        List audit trail IDs, optionally filtered by mission_id.

        Args:
            mission_id: Optional mission ID filter

        Returns:
            List of audit trail IDs
        """
        audit_trail_ids = []

        for file_path in self.base_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    audit_trail = json.load(f)

                # Filter by mission_id if provided
                if mission_id is None or audit_trail.get("mission_id") == mission_id:
                    audit_trail_ids.append(audit_trail.get("audit_trail_id"))

            except Exception as e:
                logger.warning(f"Failed to read audit trail file {file_path}: {e}")

        return audit_trail_ids

    def get_audit_trail_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored audit trails.

        Returns:
            Dictionary with statistics
        """
        total_files = 0
        total_size_bytes = 0
        mission_counts: Dict[str, int] = {}

        for file_path in self.base_dir.glob("*.json"):
            try:
                total_files += 1
                total_size_bytes += file_path.stat().st_size

                with open(file_path, "r") as f:
                    audit_trail = json.load(f)
                    mission_id = audit_trail.get("mission_id", "unknown")
                    mission_counts[mission_id] = mission_counts.get(mission_id, 0) + 1

            except Exception as e:
                logger.warning(f"Failed to read audit trail file {file_path}: {e}")

        return {
            "total_audit_trails": total_files,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "mission_counts": mission_counts,
            "base_dir": str(self.base_dir),
        }


# Singleton instance for use across the application
_persistence_instance: Optional[AuditTrailPersistence] = None


def get_persistence(
    base_dir: str = "_state/audit_trails", signing_key: Optional[str] = None
) -> AuditTrailPersistence:
    """
    Get singleton persistence instance.

    Args:
        base_dir: Base directory for audit trail storage
        signing_key: Optional HMAC signing key

    Returns:
        AuditTrailPersistence instance
    """
    global _persistence_instance

    if _persistence_instance is None:
        _persistence_instance = AuditTrailPersistence(base_dir, signing_key)

    return _persistence_instance
