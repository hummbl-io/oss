"""Cognitive Ledger Protocol (CLP) -- vendor-agnostic shared memory for multi-agent AI.

Three layers:
  1. Shared State  (state.json)  -- mutable snapshot of who's doing what
  2. Shared Memory (ledger.jsonl) -- append-only learning log
  3. Shared Intent (intent.md)    -- human-authored goals and priorities

Usage:
    from hummbl_cognition import LedgerEntry, post_entry, read_entries

CLI:
    python -m hummbl_cognition post --agent claude-code ...
    python -m hummbl_cognition query --type lesson --limit 5
"""

from __future__ import annotations

from hummbl_cognition.boot_context import build_boot_context
from hummbl_cognition.indexer import BM25Index
from hummbl_cognition.ledger_writer import (
    post_entry,
    read_entries,
    validate_integrity,
)
from hummbl_cognition.migration import (
    import_from_bus_history,
    import_from_git_log,
    import_from_memory_md,
)
from hummbl_cognition.models import (
    LedgerEntry,
    LedgerEntryType,
    LedgerScope,
    SharedState,
)
from hummbl_cognition.retriever import OpenBrainRetriever
from hummbl_cognition.schema_validator import (
    ValidationError,
    validate,
    validate_entry_dict,
    validate_file,
    validate_state_dict,
)
from hummbl_cognition.startup_context import (
    build_startup_context,
    read_recent_bus_inbox,
    write_startup_context,
)
from hummbl_cognition.state_manager import (
    ConcurrencyError,
    claim_file,
    read_state,
    release_file,
    update_agent_status,
    write_state,
)
from hummbl_cognition.verified_writer import (
    create_verified_entry,
    post_verified_entry,
    resolve_entry_identity,
)

__all__ = [
    "LedgerEntry",
    "LedgerEntryType",
    "LedgerScope",
    "SharedState",
    "ConcurrencyError",
    "ValidationError",
    "post_entry",
    "read_entries",
    "validate_integrity",
    "read_state",
    "write_state",
    "claim_file",
    "release_file",
    "update_agent_status",
    "build_boot_context",
    "build_startup_context",
    "read_recent_bus_inbox",
    "write_startup_context",
    "resolve_entry_identity",
    "create_verified_entry",
    "post_verified_entry",
    "import_from_memory_md",
    "import_from_bus_history",
    "import_from_git_log",
    "validate",
    "validate_entry_dict",
    "validate_state_dict",
    "validate_file",
    "BM25Index",
    "OpenBrainRetriever",
]
