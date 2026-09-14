#!/usr/bin/env python3
"""Knowledge Base Tools - Memory query and management utilities

Provides standardized tools for querying, adding, and managing agent memories
across the shared knowledge base.

Usage:
    from kb_tools import MemoryStore, ContextManager

    # Query memories
    store = MemoryStore("agent-name")
    results = store.query(tags=["cost"], min_importance=0.7)

    # Add new memory
    store.add(type="observation", content="...", tags=["tag"], importance=0.8)

    # Manage context
    ctx = ContextManager("agent-name", model="sonnet-4.5", limit=200000)
    ctx.track_usage(tokens_used=45000)
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


class MemoryStore:
    """Manages memory storage and retrieval for an agent"""

    def __init__(self, agent_name: str, knowledge_dir: str = "~/.knowledge"):
        self.agent_name = agent_name
        self.knowledge_dir = Path(knowledge_dir).expanduser()
        self.agent_dir = self.knowledge_dir / "agents" / agent_name
        self.memory_file = self.agent_dir / "memory.jsonl"

        # Ensure directories exist
        self.agent_dir.mkdir(parents=True, exist_ok=True)

    def add(
        self,
        content: str,
        type: str = "observation",
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        references: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        ttl_days: Optional[int] = None,
        verified: bool = False,
    ) -> str:
        """Add a new memory entry

        Args:
            content: Memory content
            type: Type of memory (observation, decision, fact, pattern, etc.)
            tags: List of tags for categorization
            importance: Importance score 0.0-1.0
            references: IDs of related memories
            context: Additional context metadata
            ttl_days: Time-to-live in days (None = use default based on importance)
            verified: Whether this memory is verified

        Returns:
            UUID of the created memory
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Calculate expiration based on importance
        if ttl_days is None:
            if importance >= 0.8:
                expires_at = None  # Keep indefinitely
            elif importance >= 0.5:
                expires_at = (now + timedelta(days=90)).isoformat() + "Z"
            else:
                expires_at = (now + timedelta(days=30)).isoformat() + "Z"
        else:
            expires_at = (now + timedelta(days=ttl_days)).isoformat() + "Z"

        entry = {
            "id": memory_id,
            "timestamp": now.isoformat() + "Z",
            "agent": self.agent_name,
            "type": type,
            "content": content,
            "tags": tags or [],
            "importance": importance,
            "references": references or [],
            "context": context or {},
            "expires_at": expires_at,
            "verified": verified,
            "version": "v1",
        }

        # Append to JSONL file
        with open(self.memory_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return memory_id

    def query(
        self,
        tags: Optional[List[str]] = None,
        type: Optional[str] = None,
        min_importance: Optional[float] = None,
        text_search: Optional[str] = None,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """Query memories with filters

        Args:
            tags: Filter by tags (any match)
            type: Filter by memory type
            min_importance: Minimum importance score
            text_search: Search in content (case-insensitive substring)
            limit: Maximum results to return
            include_expired: Whether to include expired memories

        Returns:
            List of matching memory entries
        """
        if not self.memory_file.exists():
            return []

        results = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        with open(self.memory_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)

                # Filter by expiration
                if not include_expired and entry.get("expires_at"):
                    expires = datetime.fromisoformat(entry["expires_at"].rstrip("Z"))
                    if expires < now:
                        continue

                # Filter by type
                if type and entry.get("type") != type:
                    continue

                # Filter by tags
                if tags and not any(t in entry.get("tags", []) for t in tags):
                    continue

                # Filter by importance
                if min_importance and entry.get("importance", 0) < min_importance:
                    continue

                # Filter by text search
                if text_search and text_search.lower() not in entry.get("content", "").lower():
                    continue

                results.append(entry)

                if len(results) >= limit:
                    break

        # Sort by importance (descending) and timestamp (descending)
        results.sort(key=lambda x: (-x.get("importance", 0), x.get("timestamp", "")), reverse=True)

        return results[:limit]

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID"""
        if not self.memory_file.exists():
            return None

        with open(self.memory_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("id") == memory_id:
                    return entry

        return None

    def gc(self, dry_run: bool = False) -> Dict[str, int]:
        """Garbage collect expired memories

        Args:
            dry_run: If True, just count expired entries without removing

        Returns:
            Stats dict with counts
        """
        if not self.memory_file.exists():
            return {"total": 0, "expired": 0, "kept": 0}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        kept = []
        expired_count = 0
        total_count = 0

        with open(self.memory_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                total_count += 1
                entry = json.loads(line)

                # Check expiration
                if entry.get("expires_at"):
                    expires = datetime.fromisoformat(entry["expires_at"].rstrip("Z"))
                    if expires < now:
                        expired_count += 1
                        continue

                kept.append(entry)

        # Rewrite file without expired entries
        if not dry_run and expired_count > 0:
            with open(self.memory_file, "w") as f:
                for entry in kept:
                    f.write(json.dumps(entry) + "\n")

        return {
            "total": total_count,
            "expired": expired_count,
            "kept": len(kept),
        }


class ContextManager:
    """Manages agent context window and token budget"""

    def __init__(
        self,
        agent_name: str,
        model: str = "sonnet-4.5",
        limit: int = 200000,
        knowledge_dir: str = "~/.knowledge",
    ):
        self.agent_name = agent_name
        self.model = model
        self.limit = limit

        self.knowledge_dir = Path(knowledge_dir).expanduser()
        self.agent_dir = self.knowledge_dir / "agents" / agent_name
        self.context_file = self.agent_dir / "context.json"

        # Ensure directories exist
        self.agent_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize context
        self.context = self._load_context()

    def _load_context(self) -> Dict[str, Any]:
        """Load context from disk or create new"""
        if self.context_file.exists():
            with open(self.context_file, "r") as f:
                return json.load(f)

        return {
            "agent": self.agent_name,
            "session_id": None,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            "tokens": {
                "used": 0,
                "limit": self.limit,
                "model": self.model,
                "utilization": 0.0,
            },
            "memory_summary": {
                "count": 0,
                "oldest": None,
                "newest": None,
                "compressed": False,
            },
            "active_tasks": [],
            "working_memory": [],
            "compression_history": [],
            "version": "v1",
        }

    def track_usage(self, tokens_used: int, session_id: Optional[str] = None) -> None:
        """Update token usage tracking"""
        self.context["tokens"]["used"] = tokens_used
        self.context["tokens"]["utilization"] = tokens_used / self.limit
        self.context["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"

        if session_id:
            self.context["session_id"] = session_id

        self._save_context()

    def add_task(self, task_id: str) -> None:
        """Add active task to context"""
        if task_id not in self.context["active_tasks"]:
            self.context["active_tasks"].append(task_id)
            self._save_context()

    def remove_task(self, task_id: str) -> None:
        """Remove completed task from context"""
        if task_id in self.context["active_tasks"]:
            self.context["active_tasks"].remove(task_id)
            self._save_context()

    def set_working_memory(self, key: str, value: str) -> None:
        """Set ephemeral working memory value"""
        # Remove existing entry with same key
        self.context["working_memory"] = [
            m for m in self.context["working_memory"] if m["key"] != key
        ]

        # Add new entry
        self.context["working_memory"].append({
            "key": key,
            "value": value,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        })

        # Limit to 20 entries
        self.context["working_memory"] = self.context["working_memory"][-20:]

        self._save_context()

    def get_working_memory(self, key: str) -> Optional[str]:
        """Get ephemeral working memory value"""
        for entry in self.context["working_memory"]:
            if entry["key"] == key:
                return entry["value"]
        return None

    def should_compress(self, threshold: float = 0.8) -> bool:
        """Check if context should be compressed"""
        return self.context["tokens"]["utilization"] >= threshold

    def record_compression(self, tokens_before: int, tokens_after: int, memories_compressed: int) -> None:
        """Record a compression event"""
        event = {
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "memories_compressed": memories_compressed,
        }

        self.context["compression_history"].append(event)
        self.context["compression_history"] = self.context["compression_history"][-10:]
        self.context["memory_summary"]["compressed"] = True

        self._save_context()

    def _save_context(self) -> None:
        """Save context to disk"""
        with open(self.context_file, "w") as f:
            json.dump(self.context, f, indent=2)

    def get_status(self) -> Dict[str, Any]:
        """Get current context status"""
        return {
            "agent": self.agent_name,
            "tokens_used": self.context["tokens"]["used"],
            "tokens_limit": self.limit,
            "utilization": self.context["tokens"]["utilization"],
            "active_tasks": len(self.context["active_tasks"]),
            "working_memory_size": len(self.context["working_memory"]),
            "last_updated": self.context["updated_at"],
        }


# CLI Interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: kb_tools.py <command> [args...]")
        print("\nCommands:")
        print("  query <agent> [--tags tag1,tag2] [--type TYPE] [--min-importance 0.7]")
        print("  add <agent> <content> [--type TYPE] [--tags tag1,tag2] [--importance 0.8]")
        print("  gc <agent> [--dry-run]")
        print("  status <agent>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "query" and len(sys.argv) >= 3:
        agent = sys.argv[2]
        store = MemoryStore(agent)

        # Parse optional args
        tags = None
        type_ = None
        min_importance = None

        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1].split(",")
            elif arg == "--type" and i + 1 < len(sys.argv):
                type_ = sys.argv[i + 1]
            elif arg == "--min-importance" and i + 1 < len(sys.argv):
                min_importance = float(sys.argv[i + 1])

        results = store.query(tags=tags, type=type_, min_importance=min_importance)
        print(json.dumps(results, indent=2))

    elif command == "add" and len(sys.argv) >= 4:
        agent = sys.argv[2]
        content = sys.argv[3]
        store = MemoryStore(agent)

        # Parse optional args
        type_ = "observation"
        tags = []
        importance = 0.5

        for i, arg in enumerate(sys.argv[4:], 4):
            if arg == "--type" and i + 1 < len(sys.argv):
                type_ = sys.argv[i + 1]
            elif arg == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1].split(",")
            elif arg == "--importance" and i + 1 < len(sys.argv):
                importance = float(sys.argv[i + 1])

        memory_id = store.add(content=content, type=type_, tags=tags, importance=importance)
        print(f"Created memory: {memory_id}")

    elif command == "gc" and len(sys.argv) >= 3:
        agent = sys.argv[2]
        dry_run = "--dry-run" in sys.argv
        store = MemoryStore(agent)
        stats = store.gc(dry_run=dry_run)
        print(json.dumps(stats, indent=2))

    elif command == "status" and len(sys.argv) >= 3:
        agent = sys.argv[2]
        ctx = ContextManager(agent)
        status = ctx.get_status()
        print(json.dumps(status, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
