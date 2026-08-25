"""Integration tests for the Cognitive Ledger Protocol (CLP).

Exercises the full CLP stack: verified_writer -> ledger_writer -> query ->
boot_context -> startup_context, plus state_manager concurrency and
migration roundtrips.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

# This module tests ledger writing directly — allow real writes.
pytestmark = pytest.mark.allow_ledger_writes

from hummbl_cognition.boot_context import build_boot_context
from hummbl_cognition.ledger_writer import (
    post_entry,
    read_entries,
    validate_integrity,
)
from hummbl_cognition.migration import (
    import_from_bus_history,
    import_from_memory_md,
)
from hummbl_cognition.models import (
    LedgerEntry,
    SharedState,
)
from hummbl_cognition.query import (
    active_entries,
    latest_by_scope,
    query_entries,
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(**overrides) -> LedgerEntry:
    """Create a valid LedgerEntry with sensible defaults."""
    defaults = {
        "agent": "test-agent",
        "vendor": "anthropic",
        "model": "claude-opus-4-6",
        "entry_type": "lesson",
        "scope": "project",
        "content": "Integration test lesson",
    }
    defaults.update(overrides)
    return LedgerEntry.create(**defaults)


def _setup_cognition_dir(tmp_path: Path) -> Path:
    """Create a cognition directory structure for testing."""
    cog_dir = tmp_path / "cognition"
    cog_dir.mkdir(parents=True, exist_ok=True)
    return cog_dir


def _write_state_file(cog_dir: Path, state: SharedState) -> None:
    """Write a state.json file into the cognition directory."""
    state_path = cog_dir / "state.json"
    state_path.write_text(state.to_json(), encoding="utf-8")


def _write_intent_file(cog_dir: Path, text: str) -> None:
    """Write an intent.md file into the cognition directory."""
    intent_path = cog_dir / "intent.md"
    intent_path.write_text(text, encoding="utf-8")


def _write_bus_file(tmp_path: Path, rows: list[str]) -> Path:
    """Write a mock bus TSV file."""
    bus_path = tmp_path / "messages.tsv"
    bus_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return bus_path


# ===========================================================================
# 1. Verified Writer -> Ledger -> Query -> Boot Context roundtrip
# ===========================================================================


class TestVerifiedWriterRoundtrip:
    """Write entries via verified_writer, read back via query, render in boot."""

    def test_write_and_read_back(self, tmp_path: Path) -> None:
        """Entries written by post_verified_entry appear in read_entries."""
        ledger = tmp_path / "ledger.jsonl"

        entry = post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="Bus writer requires explicit bus_path kwarg",
            evidence="commit:ac1d525e",
            confidence=0.95,
            tags=["bus", "gotcha"],
            ledger_path=ledger,
        )

        assert entry.id.startswith("clp-")
        assert entry.verify_hash()

        # Read back
        entries = read_entries(ledger_path=ledger)
        assert len(entries) == 1
        assert entries[0].id == entry.id
        assert entries[0].content == "Bus writer requires explicit bus_path kwarg"
        assert "bus" in entries[0].tags

    def test_verified_entry_requires_evidence(self) -> None:
        """Verified writer rejects entries without evidence."""
        with pytest.raises(ValueError, match="evidence"):
            create_verified_entry(
                agent="test",
                vendor="anthropic",
                model="test-model",
                entry_type="lesson",
                scope="project",
                content="Missing evidence",
                evidence="",
                confidence=0.9,
            )

    def test_verified_entry_requires_identity(self) -> None:
        """Verified writer rejects entries without agent/vendor/model."""
        # Clear env vars that might provide identity
        env_overrides = {
            "COGNITION_AGENT": "",
            "HUMMBL_COGNITION_AGENT_ID": "",
            "AGENT_ID": "",
            "COGNITION_VENDOR": "",
            "COGNITION_MODEL": "",
        }
        with pytest.MonkeyPatch.context() as mp:
            for k, v in env_overrides.items():
                mp.delenv(k, raising=False)
            with pytest.raises(ValueError, match="Missing required identity"):
                create_verified_entry(
                    entry_type="lesson",
                    scope="project",
                    content="No identity",
                    evidence="test",
                    confidence=0.9,
                )

    def test_identity_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verified writer resolves identity from environment variables."""
        monkeypatch.setenv("COGNITION_AGENT", "env-agent")
        monkeypatch.setenv("COGNITION_VENDOR", "anthropic")
        monkeypatch.setenv("COGNITION_MODEL", "env-model")

        agent, vendor, model = resolve_entry_identity()
        assert agent == "env-agent"
        assert vendor == "anthropic"
        assert model == "env-model"

    def test_write_read_query_boot_pipeline(self, tmp_path: Path) -> None:
        """Full pipeline: write entries -> query -> boot context includes them."""
        cog_dir = _setup_cognition_dir(tmp_path)
        ledger = cog_dir / "ledger.jsonl"

        # Write multiple entries of different types
        entries_written = []
        for i, (etype, scope) in enumerate([
            ("lesson", "project"),
            ("decision", "module"),
            ("discovery", "file"),
            ("convention", "convention"),
        ]):
            e = post_verified_entry(
                agent=f"agent-{i}",
                vendor="anthropic",
                model="claude-opus-4-6",
                entry_type=etype,
                scope=scope,
                content=f"Entry {i}: {etype} about {scope}",
                evidence=f"test:{i}",
                confidence=0.8 + i * 0.05,
                ledger_path=ledger,
            )
            entries_written.append(e)

        # Query by type
        decisions = query_entries(
            ledger_path=ledger, entry_type="decision"
        )
        assert len(decisions) == 1
        assert decisions[0].type == "decision"

        # Query by agent
        agent_0 = query_entries(ledger_path=ledger, agent="agent-0")
        assert len(agent_0) == 1

        # Active entries (none superseded)
        active = active_entries(ledger_path=ledger)
        assert len(active) == 4

        # Boot context should include learnings
        context = build_boot_context(cognition_dir=cog_dir)
        assert "Cognitive Ledger Boot Context" in context
        assert "Recent Learnings" in context
        # Check at least one entry content shows up
        assert "Entry 0" in context or "Entry 1" in context

    def test_supersedes_chain_filters_old_entries(self, tmp_path: Path) -> None:
        """Active entries exclude superseded entries."""
        ledger = tmp_path / "ledger.jsonl"

        original = post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="Original lesson about bus",
            evidence="test:1",
            confidence=0.8,
            ledger_path=ledger,
        )

        # Correction supersedes original
        correction = post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="correction",
            scope="project",
            content="Corrected lesson about bus",
            evidence="test:2",
            confidence=0.95,
            supersedes=original.id,
            ledger_path=ledger,
        )

        active = active_entries(ledger_path=ledger)
        active_ids = {e.id for e in active}
        assert original.id not in active_ids
        assert correction.id in active_ids

    def test_latest_by_scope(self, tmp_path: Path) -> None:
        """latest_by_scope returns most recent active per scope."""
        ledger = tmp_path / "ledger.jsonl"

        for scope in ["project", "module", "project"]:
            post_verified_entry(
                agent="test",
                vendor="anthropic",
                model="test",
                entry_type="lesson",
                scope=scope,
                content=f"Entry for {scope} at {time.time()}",
                evidence="test",
                confidence=0.9,
                ledger_path=ledger,
            )

        by_scope = latest_by_scope(ledger_path=ledger)
        assert "project" in by_scope
        assert "module" in by_scope
        assert len(by_scope) == 2


# ===========================================================================
# 2. Boot Context with all three layers
# ===========================================================================


class TestBootContextLayers:
    """Integration: boot context assembles intent + state + ledger."""

    def test_all_three_layers(self, tmp_path: Path) -> None:
        """Boot context includes intent, state, and ledger data."""
        cog_dir = _setup_cognition_dir(tmp_path)

        # Layer 3: intent
        _write_intent_file(cog_dir, "Ship the morning briefing v2.")

        # Layer 1: state
        state = SharedState(
            version=5,
            updated_by="claude-code",
            active_agents={
                "claude-code": {"status": "active"},
                "codex": {"status": "idle"},
            },
            sprint={"name": "MARCH-OPS"},
            flags={"idp_enabled": True},
        )
        _write_state_file(cog_dir, state)

        # Layer 2: ledger
        ledger = cog_dir / "ledger.jsonl"
        post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="project",
            content="Kill switch teardown is essential in test cleanup",
            evidence="commit:ac1d525e",
            confidence=0.95,
            ledger_path=ledger,
        )

        context = build_boot_context(cognition_dir=cog_dir)

        assert "Current Intent" in context
        assert "Ship the morning briefing v2." in context
        assert "Shared State" in context
        assert "MARCH-OPS" in context
        assert "claude-code (active)" in context
        assert "idp_enabled=True" in context
        assert "Recent Learnings" in context
        assert "Kill switch teardown" in context

    def test_empty_cognition_dir(self, tmp_path: Path) -> None:
        """Boot context handles empty cognition directory gracefully."""
        cog_dir = _setup_cognition_dir(tmp_path)
        context = build_boot_context(cognition_dir=cog_dir)
        assert "No cognitive data available" in context

    def test_partial_layers(self, tmp_path: Path) -> None:
        """Boot context works with only some layers present."""
        cog_dir = _setup_cognition_dir(tmp_path)
        _write_intent_file(cog_dir, "Just intent, nothing else.")

        context = build_boot_context(cognition_dir=cog_dir)
        assert "Current Intent" in context
        assert "Just intent" in context
        # No state or learnings sections
        assert "Shared State" not in context


# ===========================================================================
# 3. Startup Context integrates boot_context + bus inbox
# ===========================================================================


class TestStartupContextIntegration:
    """Integration: startup context combines boot context with bus inbox."""

    def test_startup_context_with_bus_inbox(self, tmp_path: Path) -> None:
        """Startup context includes both cognition data and bus messages."""
        cog_dir = _setup_cognition_dir(tmp_path)
        _write_intent_file(cog_dir, "Focus on IDP Phase 1.")

        # Create bus with messages targeted at our agent
        bus = _write_bus_file(tmp_path, [
            "2026-03-12T10:00:00Z\tcodex\tclaude-code\tTASK_REQUEST\tPlease review PR #186",
            "2026-03-12T10:05:00Z\tgemini\tall\tSTATUS\tResearch complete",
            "2026-03-12T10:10:00Z\tkimi-1\tkimi-2\tSTATUS\tNot for claude",
        ])

        context = build_startup_context(
            "claude-code",
            cognition_dir=cog_dir,
            bus_path=bus,
        )

        assert "Current Intent" in context
        assert "Focus on IDP Phase 1." in context
        assert "Bus Inbox" in context
        # Should include codex message (targeted at claude-code) and gemini (to all)
        assert "PR #186" in context
        assert "Research complete" in context
        # Should NOT include kimi->kimi message
        assert "Not for claude" not in context

    def test_startup_context_with_aliases(self, tmp_path: Path) -> None:
        """Agent aliases match bus messages."""
        bus = _write_bus_file(tmp_path, [
            "2026-03-12T10:00:00Z\tcodex\topus\tSTATUS\tMessage for opus alias",
        ])
        cog_dir = _setup_cognition_dir(tmp_path)

        context = build_startup_context(
            "claude-code",
            agent_aliases=["opus", "claude"],
            cognition_dir=cog_dir,
            bus_path=bus,
        )
        assert "Message for opus alias" in context

    def test_write_startup_context_to_file(self, tmp_path: Path) -> None:
        """write_startup_context produces a file with correct content."""
        cog_dir = _setup_cognition_dir(tmp_path)
        _write_intent_file(cog_dir, "Test intent for file write.")
        output = tmp_path / "startup" / "agent.md"

        result_path = write_startup_context(
            "test-agent",
            cognition_dir=cog_dir,
            output_path=output,
        )

        assert result_path == output
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Test intent for file write." in content

        # File should have restrictive permissions (on POSIX systems)
        import sys
        if sys.platform != "win32":
            mode = output.stat().st_mode & 0o777
            assert mode == 0o600

    def test_bus_inbox_limit(self, tmp_path: Path) -> None:
        """Bus inbox respects the limit parameter."""
        rows = [
            f"2026-03-12T10:{i:02d}:00Z\tsender\tmy-agent\tSTATUS\tMsg {i}"
            for i in range(20)
        ]
        bus = _write_bus_file(tmp_path, rows)

        messages = read_recent_bus_inbox("my-agent", bus_path=bus, limit=5)
        assert len(messages) == 5
        # Should be the 5 most recent
        assert "Msg 19" in messages[-1]
        assert "Msg 15" in messages[0]


# ===========================================================================
# 4. Migration roundtrip: bus -> ledger -> boot context
# ===========================================================================


class TestMigrationRoundtrip:
    """Import bus history into ledger, then verify boot context sees it."""

    def test_bus_to_ledger_to_boot(self, tmp_path: Path) -> None:
        """Bus DECISION messages imported into ledger appear in boot context."""
        from datetime import datetime, timezone

        cog_dir = _setup_cognition_dir(tmp_path)
        ledger = cog_dir / "ledger.jsonl"

        # Use dynamic timestamps so entries stay within the 14-day boot context window
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        bus = _write_bus_file(tmp_path, [
            f"{today}\tclaude-code\tall\tDECISION\tUse stdlib-only for all runtime code",
            f"{today}\tcodex\tall\tMILESTONE\tAll 5000 tests passing",
            f"{today}\tkimi-1\tall\tSTATUS\tJust a status update",
        ])

        entries = import_from_bus_history(
            bus_path=bus,
            ledger_path=ledger,
        )

        # Should import DECISION and MILESTONE but not STATUS
        assert len(entries) == 2
        types = {e.type for e in entries}
        assert "decision" in types
        assert "discovery" in types  # MILESTONE maps to discovery

        # Verify boot context picks them up
        context = build_boot_context(cognition_dir=cog_dir)
        assert "Recent Learnings" in context
        assert "stdlib-only" in context or "5000 tests" in context

    def test_bus_import_idempotent(self, tmp_path: Path) -> None:
        """Re-importing the same bus data produces no duplicates."""
        cog_dir = _setup_cognition_dir(tmp_path)
        ledger = cog_dir / "ledger.jsonl"

        bus = _write_bus_file(tmp_path, [
            "2026-03-12T09:00:00Z\tclaude-code\tall\tDECISION\tDecision A",
        ])

        first = import_from_bus_history(bus_path=bus, ledger_path=ledger)
        second = import_from_bus_history(bus_path=bus, ledger_path=ledger)

        assert len(first) == 1
        assert len(second) == 0  # No new entries

        all_entries = read_entries(ledger_path=ledger)
        assert len(all_entries) == 1

    def test_memory_md_to_ledger(self, tmp_path: Path) -> None:
        """MEMORY.md import creates ledger entries with correct types."""
        cog_dir = _setup_cognition_dir(tmp_path)
        ledger = cog_dir / "ledger.jsonl"

        memory = tmp_path / "MEMORY.md"
        memory.write_text(
            "# Memory\n\n"
            "## Gotchas\n"
            "- bus_writer requires explicit bus_path kwarg\n"
            "- zombie pytest processes consume CPU\n\n"
            "## Architecture Insights\n"
            "- CostGovernorBridge is ahead of industry\n",
            encoding="utf-8",
        )

        entries = import_from_memory_md(memory, ledger_path=ledger)

        assert len(entries) == 3
        # Gotchas should be lessons
        gotcha_entries = [e for e in entries if "gotcha" in e.tags]
        assert len(gotcha_entries) == 2
        for e in gotcha_entries:
            assert e.type == "lesson"
        # Architecture should be discovery
        arch_entries = [e for e in entries if e.type == "discovery"]
        assert len(arch_entries) == 1


# ===========================================================================
# 5. Concurrent writes (state manager + ledger writer)
# ===========================================================================


class TestConcurrentWrites:
    """Test concurrent access patterns for state and ledger."""

    def test_optimistic_concurrency_on_state(self, tmp_path: Path) -> None:
        """Concurrent state writes with version mismatch raise ConcurrencyError."""
        state_path = tmp_path / "state.json"

        # Write initial state
        initial = SharedState(version=1, updated_by="agent-a")
        write_state(initial, state_path=state_path)

        # Read current state
        current = read_state(state_path=state_path)
        assert current.version == 1

        # Agent A updates state with correct version
        updated_a = SharedState(version=2, updated_by="agent-a")
        write_state(updated_a, state_path=state_path, expected_version=1)

        # Agent B tries to update with stale version
        with pytest.raises(ConcurrencyError, match="Version mismatch"):
            stale_update = SharedState(version=2, updated_by="agent-b")
            write_state(stale_update, state_path=state_path, expected_version=1)

    def test_file_claim_conflict(self, tmp_path: Path) -> None:
        """Two agents cannot claim the same file."""
        state_path = tmp_path / "state.json"

        claim_file(
            "services/scheduler.py",
            "claude-code",
            purpose="refactoring",
            state_path=state_path,
        )

        with pytest.raises(ValueError, match="already claimed"):
            claim_file(
                "services/scheduler.py",
                "codex",
                purpose="also wants it",
                state_path=state_path,
            )

    def test_file_claim_and_release(self, tmp_path: Path) -> None:
        """Claiming then releasing a file allows another agent to claim it."""
        state_path = tmp_path / "state.json"

        claim_file("file.py", "agent-a", state_path=state_path)
        release_file("file.py", "agent-a", state_path=state_path)
        claim_file("file.py", "agent-b", state_path=state_path)

        state = read_state(state_path=state_path)
        assert state.claimed_files["file.py"]["agent"] == "agent-b"

    def test_release_by_wrong_agent_fails(self, tmp_path: Path) -> None:
        """Only the claiming agent can release a file."""
        state_path = tmp_path / "state.json"

        claim_file("file.py", "agent-a", state_path=state_path)

        with pytest.raises(ValueError, match="Cannot release"):
            release_file("file.py", "agent-b", state_path=state_path)

    def test_concurrent_ledger_writes(self, tmp_path: Path) -> None:
        """Multiple threads writing to the ledger produce valid entries."""
        ledger = tmp_path / "ledger.jsonl"
        n_threads = 8
        entries_per_thread = 5
        errors: list[str] = []
        written_ids: list[str] = []
        lock = threading.Lock()

        def writer(thread_id: int) -> None:
            for i in range(entries_per_thread):
                try:
                    entry = _make_entry(
                        agent=f"thread-{thread_id}",
                        content=f"Thread {thread_id} entry {i}",
                    )
                    result = post_entry(entry, ledger_path=ledger)
                    with lock:
                        written_ids.append(result.id)
                except Exception as exc:
                    with lock:
                        errors.append(f"thread-{thread_id}: {exc}")

        threads = [
            threading.Thread(target=writer, args=(t,))
            for t in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"Thread errors: {errors}"
        assert len(written_ids) == n_threads * entries_per_thread

        # Validate integrity of all written entries
        valid_count, integrity_errors = validate_integrity(ledger_path=ledger)
        assert not integrity_errors, f"Integrity errors: {integrity_errors}"
        assert valid_count == n_threads * entries_per_thread

    def test_agent_status_updates(self, tmp_path: Path) -> None:
        """Multiple agents updating status produces consistent state."""
        state_path = tmp_path / "state.json"

        update_agent_status("claude-code", "active", vendor="anthropic",
                            state_path=state_path)
        update_agent_status("codex", "active", vendor="openai",
                            state_path=state_path)
        update_agent_status("claude-code", "idle",
                            state_path=state_path)

        state = read_state(state_path=state_path)
        assert state.active_agents["claude-code"]["status"] == "idle"
        assert state.active_agents["codex"]["status"] == "active"
        assert state.version == 3  # 3 updates


# ===========================================================================
# 6. Read-your-writes: state + ledger + query consistency
# ===========================================================================


class TestReadYourWrites:
    """Verify that writes are immediately visible to reads."""

    def test_ledger_read_after_write(self, tmp_path: Path) -> None:
        """Entry is readable immediately after posting."""
        ledger = tmp_path / "ledger.jsonl"

        for i in range(10):
            post_verified_entry(
                agent="writer",
                vendor="anthropic",
                model="test",
                entry_type="lesson",
                scope="project",
                content=f"Lesson number {i}",
                evidence=f"test:{i}",
                confidence=0.9,
                ledger_path=ledger,
            )

            # Read immediately
            entries = read_entries(ledger_path=ledger)
            assert len(entries) == i + 1
            # Most recent first
            assert entries[0].content == f"Lesson number {i}"

    def test_state_read_after_write(self, tmp_path: Path) -> None:
        """State changes are visible immediately after write."""
        state_path = tmp_path / "state.json"

        for i in range(5):
            state = SharedState(version=i + 1, updated_by=f"agent-{i}")
            write_state(state, state_path=state_path)

            read_back = read_state(state_path=state_path)
            assert read_back.version == i + 1
            assert read_back.updated_by == f"agent-{i}"

    def test_query_filters_after_write(self, tmp_path: Path) -> None:
        """Query filters work correctly on freshly written entries."""
        ledger = tmp_path / "ledger.jsonl"

        post_verified_entry(
            agent="agent-a",
            vendor="anthropic",
            model="m1",
            entry_type="lesson",
            scope="project",
            content="Lesson from agent A",
            evidence="test",
            confidence=0.9,
            tags=["alpha"],
            ledger_path=ledger,
        )
        post_verified_entry(
            agent="agent-b",
            vendor="openai",
            model="m2",
            entry_type="decision",
            scope="module",
            content="Decision from agent B",
            evidence="test",
            confidence=0.85,
            tags=["beta"],
            ledger_path=ledger,
        )

        # Filter by agent
        a_entries = query_entries(ledger_path=ledger, agent="agent-a")
        assert len(a_entries) == 1
        assert a_entries[0].agent == "agent-a"

        # Filter by type
        decisions = query_entries(ledger_path=ledger, entry_type="decision")
        assert len(decisions) == 1
        assert decisions[0].type == "decision"

        # Filter by scope
        modules = query_entries(ledger_path=ledger, scope="module")
        assert len(modules) == 1

        # Filter by tags
        alpha = query_entries(ledger_path=ledger, tags=["alpha"])
        assert len(alpha) == 1
        assert alpha[0].agent == "agent-a"


# ===========================================================================
# 7. Integrity validation end-to-end
# ===========================================================================


class TestIntegrityValidation:
    """Validate ledger integrity across write and read paths."""

    def test_valid_ledger_passes_integrity(self, tmp_path: Path) -> None:
        """A ledger written through post_entry passes validate_integrity."""
        ledger = tmp_path / "ledger.jsonl"

        for i in range(5):
            entry = _make_entry(content=f"Integrity test entry {i}")
            post_entry(entry, ledger_path=ledger)

        valid, errors = validate_integrity(ledger_path=ledger)
        assert valid == 5
        assert errors == []

    def test_tampered_entry_fails_integrity(self, tmp_path: Path) -> None:
        """Modifying content without updating hash fails integrity check."""
        ledger = tmp_path / "ledger.jsonl"

        entry = _make_entry(content="Original content")
        post_entry(entry, ledger_path=ledger)

        # Tamper with the content
        text = ledger.read_text(encoding="utf-8")
        data = json.loads(text.strip())
        data["content"] = "Tampered content"
        ledger.write_text(json.dumps(data, sort_keys=True) + "\n")

        valid, errors = validate_integrity(ledger_path=ledger)
        assert valid == 0
        assert len(errors) == 1
        assert "content_hash mismatch" in errors[0]

    def test_signed_entries_integrity(self, tmp_path: Path) -> None:
        """Signed entries pass integrity validation with correct secret."""
        ledger = tmp_path / "ledger.jsonl"
        secret = b"a" * 32  # 32 bytes minimum

        entry = _make_entry(content="Signed entry content")
        post_entry(entry, ledger_path=ledger, secret=secret)

        valid, errors = validate_integrity(ledger_path=ledger, secret=secret)
        assert valid == 1
        assert errors == []

        # Verify the entry actually has a signature
        entries = read_entries(ledger_path=ledger)
        assert entries[0].signature is not None


# ===========================================================================
# 8. Full stack: verified_writer -> boot_context -> startup_context
# ===========================================================================


class TestFullStackPipeline:
    """End-to-end: write, build boot, build startup with bus."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Complete pipeline from write to startup context artifact."""
        cog_dir = _setup_cognition_dir(tmp_path)
        ledger = cog_dir / "ledger.jsonl"

        # Set up all three layers
        _write_intent_file(cog_dir, "Complete IDP Phase 1 wiring.")
        state = SharedState(
            version=10,
            updated_by="claude-code",
            active_agents={"claude-code": {"status": "active"}},
            sprint={"name": "IDP-PHASE-1"},
        )
        _write_state_file(cog_dir, state)

        # Write verified entries
        post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="decision",
            scope="project",
            content="All IDP tokens use HMAC-SHA256 signing",
            evidence="services/delegation_token.py",
            confidence=0.95,
            tags=["idp", "security"],
            ledger_path=ledger,
        )
        post_verified_entry(
            agent="claude-code",
            vendor="anthropic",
            model="claude-opus-4-6",
            entry_type="lesson",
            scope="module",
            content="Feature flags prevent IDP from affecting non-IDP tests",
            evidence="ENABLE_IDP env var",
            confidence=0.9,
            tags=["idp", "testing"],
            ledger_path=ledger,
        )

        # Create bus with targeted messages
        bus = _write_bus_file(tmp_path, [
            "2026-03-13T08:00:00Z\tcodex\tclaude-code\tTASK_REQUEST\tVerify IDP token expiry",
            "2026-03-13T08:30:00Z\tgemini\tall\tSITREP\tIDP research complete",
        ])

        # Build startup context
        output = tmp_path / "startup_out.md"
        result_path = write_startup_context(
            "claude-code",
            cognition_dir=cog_dir,
            bus_path=bus,
            output_path=output,
        )

        content = result_path.read_text(encoding="utf-8")

        # Verify all layers present
        assert "Current Intent" in content
        assert "IDP Phase 1" in content
        assert "Shared State" in content
        assert "IDP-PHASE-1" in content
        assert "Recent Learnings" in content
        assert "Bus Inbox" in content
        assert "Verify IDP token expiry" in content
        assert "IDP research complete" in content
