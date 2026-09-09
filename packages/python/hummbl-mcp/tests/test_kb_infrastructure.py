#!/usr/bin/env python3
"""Test suite for Knowledge Base infrastructure

Validates memory schemas, storage, queries, and context management.
"""

import json
import os
import tempfile
from pathlib import Path
from hummbl_mcp.kb_tools import MemoryStore, ContextManager


def test_memory_store():
    """Test MemoryStore operations"""
    print("Testing MemoryStore...")

    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore("test-agent", knowledge_dir=tmpdir)

        # Test add
        id1 = store.add(
            content="Test observation",
            type="observation",
            tags=["test", "observation"],
            importance=0.8
        )
        assert id1, "Should return memory ID"

        # Test query by tags
        results = store.query(tags=["test"])
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0]["content"] == "Test observation"

        # Test query by importance
        results = store.query(min_importance=0.7)
        assert len(results) == 1

        results = store.query(min_importance=0.9)
        assert len(results) == 0, "Should not match lower importance"

        # Test get by ID
        entry = store.get(id1)
        assert entry is not None
        assert entry["id"] == id1

        # Test text search
        results = store.query(text_search="observation")
        assert len(results) == 1

        results = store.query(text_search="nonexistent")
        assert len(results) == 0

        # Test GC
        stats = store.gc(dry_run=True)
        assert stats["total"] == 1
        assert stats["expired"] == 0

    print("✅ MemoryStore tests passed")


def test_context_manager():
    """Test ContextManager operations"""
    print("Testing ContextManager...")

    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = ContextManager("test-agent", model="sonnet-4.5", limit=100000, knowledge_dir=tmpdir)

        # Test initial state
        status = ctx.get_status()
        assert status["tokens_used"] == 0
        assert status["tokens_limit"] == 100000
        assert status["utilization"] == 0.0

        # Test track usage
        ctx.track_usage(50000)
        status = ctx.get_status()
        assert status["tokens_used"] == 50000
        assert status["utilization"] == 0.5

        # Test compression check
        assert not ctx.should_compress(threshold=0.8), "Should not need compression at 50%"

        ctx.track_usage(85000)
        assert ctx.should_compress(threshold=0.8), "Should need compression at 85%"

        # Test task management
        ctx.add_task("task-1")
        assert "task-1" in ctx.context["active_tasks"]

        ctx.add_task("task-2")
        assert len(ctx.context["active_tasks"]) == 2

        ctx.remove_task("task-1")
        assert "task-1" not in ctx.context["active_tasks"]
        assert "task-2" in ctx.context["active_tasks"]

        # Test working memory
        ctx.set_working_memory("key1", "value1")
        assert ctx.get_working_memory("key1") == "value1"

        ctx.set_working_memory("key2", "value2")
        assert ctx.get_working_memory("key2") == "value2"

        # Overwrite should work
        ctx.set_working_memory("key1", "new-value")
        assert ctx.get_working_memory("key1") == "new-value"

        # Test compression history
        ctx.record_compression(85000, 50000, 10)
        assert len(ctx.context["compression_history"]) == 1
        assert ctx.context["compression_history"][0]["tokens_before"] == 85000

    print("✅ ContextManager tests passed")


def test_schema_validation():
    """Test that generated entries match schema"""
    print("Testing schema validation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore("test-agent", knowledge_dir=tmpdir)

        # Add entry
        id1 = store.add(
            content="Test",
            type="observation",
            tags=["test"],
            importance=0.5
        )

        # Read it back
        entry = store.get(id1)

        # Check required fields
        assert "id" in entry
        assert "timestamp" in entry
        assert "agent" in entry
        assert "type" in entry
        assert "content" in entry

        # Check types
        assert isinstance(entry["tags"], list)
        assert isinstance(entry["importance"], (int, float))
        assert isinstance(entry["references"], list)
        assert entry["version"] == "v1"

    print("✅ Schema validation tests passed")


def test_memory_expiration():
    """Test memory expiration and GC"""
    print("Testing memory expiration...")

    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore("test-agent", knowledge_dir=tmpdir)

        # Add high importance (should not expire)
        id1 = store.add(content="High importance", importance=0.9)
        e1 = store.get(id1)
        assert e1["expires_at"] is None, "High importance should not expire"

        # Add medium importance (90 days)
        id2 = store.add(content="Medium importance", importance=0.6)
        e2 = store.get(id2)
        assert e2["expires_at"] is not None, "Medium importance should expire"

        # Add low importance (30 days)
        id3 = store.add(content="Low importance", importance=0.3)
        e3 = store.get(id3)
        assert e3["expires_at"] is not None, "Low importance should expire"

        # Custom TTL
        id4 = store.add(content="Custom TTL", ttl_days=7)
        e4 = store.get(id4)
        assert e4["expires_at"] is not None

    print("✅ Memory expiration tests passed")


def test_integration():
    """Test full integration scenario"""
    print("Testing integration scenario...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate agent lifecycle
        store = MemoryStore("integration-test", knowledge_dir=tmpdir)
        ctx = ContextManager("integration-test", knowledge_dir=tmpdir)

        # Agent starts task
        ctx.add_task("task-1")
        store.add(
            type="decision",
            content="Started task-1",
            tags=["task", "start"],
            importance=0.6,
            context={"task_id": "task-1"}
        )

        # Agent makes observations
        for i in range(5):
            store.add(
                type="observation",
                content=f"Observation {i}",
                tags=["observation"],
                importance=0.5 + (i * 0.1)
            )

        # Track context usage
        ctx.track_usage(75000)

        # Query past observations
        observations = store.query(type="observation", min_importance=0.6)
        assert len(observations) >= 2, "Should find high-importance observations"

        # Complete task
        ctx.remove_task("task-1")
        store.add(
            type="success",
            content="Completed task-1",
            tags=["task", "complete"],
            importance=0.7
        )

        # Verify state
        status = ctx.get_status()
        assert status["active_tasks"] == 0
        assert status["tokens_used"] == 75000

    print("✅ Integration tests passed")


if __name__ == "__main__":
    print("Running Knowledge Base infrastructure tests...\n")

    test_memory_store()
    test_context_manager()
    test_schema_validation()
    test_memory_expiration()
    test_integration()

    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED")
    print("=" * 50)
    print("\nKnowledge Base infrastructure is working correctly!")
