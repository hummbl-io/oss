"""Tests for the Open Brain Consolidator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from hummbl_cognition.ledger_writer import post_entry
from hummbl_cognition.models import LedgerEntry

try:
    from hummbl_governance.kill_switch_core import get_kill_switch_core  # noqa: F401

    _HAS_KILL_SWITCH_CORE = True
except ImportError:
    _HAS_KILL_SWITCH_CORE = False

# This module tests ledger writing directly — allow real writes.
pytestmark = pytest.mark.allow_ledger_writes


def _make_entry(content: str, **kwargs) -> LedgerEntry:
    defaults = dict(
        agent="test-agent",
        vendor="anthropic",
        model="test-model",
        entry_type="lesson",
        scope="project",
    )
    defaults.update(kwargs)
    return LedgerEntry.create(content=content, **defaults)


def _write_ledger(path: Path, entries: list[LedgerEntry]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    for e in entries:
        post_entry(e, ledger_path=path)
    return path


class TestConsolidatorGrouping:
    """Test entry grouping by similarity."""

    def test_groups_similar_entries(self, tmp_path):
        from hummbl_cognition.consolidator import (
            _compute_pairwise_similarity,
            _group_similar,
        )

        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync"),
            _make_entry("Circuit breaker tripped for GitHub adapter"),
            _make_entry("Circuit breaker opened on Linear adapter timeout"),
            _make_entry("Completely unrelated entry about weather forecasting"),
        ]

        similarity = _compute_pairwise_similarity(entries)
        groups = _group_similar(entries, similarity)

        # Should find at least 1 group (the OAuth pair or circuit breaker pair)
        assert len(groups) >= 1
        # Each group should have at least 2 entries
        for group in groups:
            assert len(group) >= 2

    def test_no_groups_for_dissimilar(self, tmp_path):
        from hummbl_cognition.consolidator import (
            _compute_pairwise_similarity,
            _group_similar,
        )

        entries = [
            _make_entry("Alpha beta gamma delta epsilon"),
            _make_entry("Zulu yankee xray whiskey victor"),
            _make_entry("One two three four five six"),
        ]

        similarity = _compute_pairwise_similarity(entries)
        groups = _group_similar(entries, similarity)
        assert len(groups) == 0

    def test_max_group_size_enforced(self):
        from hummbl_cognition.consolidator import (
            MAX_GROUP_SIZE,
            _compute_pairwise_similarity,
            _group_similar,
        )

        # Create many entries with the same content
        entries = [
            _make_entry(f"OAuth token refresh failed attempt {i}") for i in range(20)
        ]

        similarity = _compute_pairwise_similarity(entries)
        groups = _group_similar(entries, similarity)

        for group in groups:
            assert len(group) <= MAX_GROUP_SIZE


class TestConsolidatedIdTracking:
    """Test that already-consolidated entries are tracked."""

    def test_tracks_consolidated_ids(self):
        from hummbl_cognition.consolidator import _get_consolidated_ids

        source_entry = _make_entry("original entry")
        consolidated = _make_entry(
            "consolidated summary",
            tags=["consolidated"],
            links=[source_entry.id],
        )

        consolidated_ids = _get_consolidated_ids([source_entry, consolidated])
        assert source_entry.id in consolidated_ids

    def test_empty_when_no_consolidations(self):
        from hummbl_cognition.consolidator import _get_consolidated_ids

        entries = [_make_entry("entry 1"), _make_entry("entry 2")]
        assert _get_consolidated_ids(entries) == set()


class TestKillSwitchHelper:
    @pytest.mark.skipif(
        not _HAS_KILL_SWITCH_CORE,
        reason="hummbl_governance.kill_switch_core not available",
    )
    def test_runtime_error_fails_closed(self):
        from hummbl_cognition.consolidator import _is_kill_switch_engaged

        with patch(
            "hummbl_governance.kill_switch_core.get_kill_switch_core",
            side_effect=RuntimeError("boom"),
        ):
            assert _is_kill_switch_engaged() is True


class TestRunConsolidation:
    """Test the full consolidation run."""

    def test_dry_run_no_writes(self, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation
        from hummbl_cognition.ledger_writer import read_entries

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
            _make_entry("OAuth token expired causing auth failure"),
        ]
        _write_ledger(ledger, entries)

        result = run_consolidation(ledger_path=ledger, dry_run=True)

        # Should find groups but not write
        assert result["groups_found"] >= 1
        # No new entries written
        final_entries = read_entries(ledger_path=ledger, limit=999)
        assert len(final_entries) == 3

    @patch("hummbl_cognition.consolidator._ollama_generate")
    def test_consolidation_with_mock_ollama(self, mock_ollama, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation
        from hummbl_cognition.ledger_writer import read_entries

        mock_ollama.return_value = (
            "OAuth token refresh is a recurring issue in both morning and evening jobs."
        )

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
            _make_entry("OAuth token expired causing auth failure"),
        ]
        _write_ledger(ledger, entries)

        result = run_consolidation(ledger_path=ledger)

        assert result["consolidated"] >= 1
        assert result["errors"] == []

        # Check a consolidated entry was written
        final_entries = read_entries(ledger_path=ledger, limit=999)
        consolidated = [e for e in final_entries if "consolidated" in e.tags]
        assert len(consolidated) >= 1
        assert consolidated[0].agent == "consolidator"
        assert consolidated[0].links  # Should link to source entries

    @patch("hummbl_cognition.consolidator._ollama_generate")
    def test_fallback_when_ollama_down(self, mock_ollama, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation
        from hummbl_cognition.ledger_writer import read_entries

        mock_ollama.return_value = None  # Ollama unavailable

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
        ]
        _write_ledger(ledger, entries)

        result = run_consolidation(ledger_path=ledger)

        # Should still consolidate with fallback
        assert result["consolidated"] >= 1
        final_entries = read_entries(ledger_path=ledger, limit=999)
        consolidated = [e for e in final_entries if "consolidated" in e.tags]
        assert len(consolidated) >= 1
        assert "Consolidated from related entries" in consolidated[0].content

    def test_skips_already_consolidated(self, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation

        ledger = tmp_path / "ledger.jsonl"
        e1 = _make_entry("OAuth token refresh failed during morning briefing")
        e2 = _make_entry("OAuth token refresh error in evening sync job")
        # Pre-existing consolidation
        e3 = _make_entry(
            "OAuth refresh is a recurring issue",
            tags=["consolidated"],
            links=[e1.id, e2.id],
            agent="consolidator",
        )
        _write_ledger(ledger, [e1, e2, e3])

        result = run_consolidation(ledger_path=ledger, dry_run=True)

        # The two source entries are already consolidated, should find no new groups
        assert result["groups_found"] == 0

    def test_kill_switch_blocks_consolidation(self, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed"),
            _make_entry("OAuth token refresh error"),
        ]
        _write_ledger(ledger, entries)

        with patch(
            "hummbl_cognition.consolidator._is_kill_switch_engaged",
            return_value=True,
        ):
            result = run_consolidation(ledger_path=ledger)

        assert result["consolidated"] == 0
        assert "kill switch engaged" in result["errors"]

    def test_empty_ledger(self, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation

        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text("")

        result = run_consolidation(ledger_path=ledger)
        assert result["groups_found"] == 0
        assert result["consolidated"] == 0


class TestConsolidatorStatus:
    """Test status reporting."""

    def test_status_report(self, tmp_path):
        from hummbl_cognition.consolidator import status

        ledger = tmp_path / "ledger.jsonl"
        e1 = _make_entry("entry one")
        e2 = _make_entry("entry two")
        e3 = _make_entry(
            "consolidated summary",
            tags=["consolidated"],
            links=[e1.id],
        )
        _write_ledger(ledger, [e1, e2, e3])

        s = status(ledger_path=ledger)
        assert s["total_entries"] == 3
        assert s["consolidated_entries"] == 1
        assert s["source_entries_covered"] == 1


class TestConsolidatorCLI:
    """Test CLI entry points."""

    def test_status_command(self, tmp_path):
        from hummbl_cognition.consolidator import main

        ledger = tmp_path / "ledger.jsonl"
        _write_ledger(ledger, [_make_entry("test")])

        rc = main(["status", "--ledger", str(ledger)])
        assert rc == 0

    def test_run_dry_run(self, tmp_path):
        from hummbl_cognition.consolidator import main

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
        ]
        _write_ledger(ledger, entries)

        rc = main(["run", "--dry-run", "--ledger", str(ledger)])
        assert rc == 0

    def test_no_command_shows_help(self, capsys):
        from hummbl_cognition.consolidator import main

        rc = main([])
        assert rc == 2


# ---------------------------------------------------------------------------
# L2: Ollama HTTP integration (real HTTP server mock)
# ---------------------------------------------------------------------------


class TestOllamaHTTPIntegration:
    """Test _ollama_generate with real HTTP server mocks."""

    @pytest.fixture
    def fake_ollama(self):
        import json
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                json.loads(self.rfile.read(length)) if length else {}
                resp = json.dumps({"response": "Synthesized summary."}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)

            def log_message(self, *a):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        yield f"http://127.0.0.1:{port}"
        server.shutdown()

    @pytest.fixture
    def failing_ollama(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error":"fail"}')

            def log_message(self, *a):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        yield f"http://127.0.0.1:{port}"
        server.shutdown()

    def test_ollama_generate_success(self, fake_ollama):
        from hummbl_cognition.consolidator import _ollama_generate

        result = _ollama_generate("test prompt", base_url=fake_ollama)
        assert result == "Synthesized summary."

    def test_ollama_generate_server_error(self, failing_ollama):
        from hummbl_cognition.consolidator import _ollama_generate

        result = _ollama_generate("test prompt", base_url=failing_ollama)
        assert result is None

    def test_ollama_generate_unreachable(self):
        from hummbl_cognition.consolidator import _ollama_generate

        result = _ollama_generate(
            "test prompt",
            base_url="http://127.0.0.1:1",
            timeout_s=1,
        )
        assert result is None

    def test_synthesize_group(self, fake_ollama):
        from hummbl_cognition.consolidator import _synthesize_group

        group = [
            _make_entry("OAuth token refresh failed"),
            _make_entry("OAuth token expired error"),
        ]
        result = _synthesize_group(group, base_url=fake_ollama, model="test")
        assert result == "Synthesized summary."

    def test_full_run_with_http_ollama(self, fake_ollama, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
        ]
        _write_ledger(ledger, entries)

        result = run_consolidation(
            ledger_path=ledger,
            base_url=fake_ollama,
            model="test",
        )
        if result["groups_found"] > 0:
            assert result["consolidated"] > 0
            assert result["errors"] == []

    def test_full_run_fallback_on_http_error(self, failing_ollama, tmp_path):
        from hummbl_cognition.consolidator import run_consolidation
        from hummbl_cognition.ledger_writer import read_entries

        ledger = tmp_path / "ledger.jsonl"
        entries = [
            _make_entry("OAuth token refresh failed during morning briefing"),
            _make_entry("OAuth token refresh error in evening sync job"),
        ]
        _write_ledger(ledger, entries)

        result = run_consolidation(
            ledger_path=ledger,
            base_url=failing_ollama,
            model="test",
        )
        if result["groups_found"] > 0:
            assert result["consolidated"] > 0
            final = read_entries(ledger_path=ledger, limit=999)
            consolidated = [e for e in final if "consolidated" in e.tags]
            assert any(
                "Consolidated from related entries" in c.content for c in consolidated
            )

    def test_kill_switch_mid_run(self, fake_ollama, tmp_path):
        """Kill switch engaged between groups should stop processing."""
        from hummbl_cognition.consolidator import run_consolidation

        ledger = tmp_path / "ledger.jsonl"
        # Create enough similar entries for multiple groups
        entries = [
            _make_entry(f"OAuth token refresh variant {i} failed scheduler")
            for i in range(8)
        ]
        entries += [
            _make_entry(f"Circuit breaker variant {i} tripped adapter")
            for i in range(8)
        ]
        _write_ledger(ledger, entries)

        call_count = [0]

        def _kill_switch_mid():
            call_count[0] += 1
            return call_count[0] > 1  # Allow first check, block on second

        with patch(
            "hummbl_cognition.consolidator._is_kill_switch_engaged",
            side_effect=_kill_switch_mid,
        ):
            result = run_consolidation(
                ledger_path=ledger,
                base_url=fake_ollama,
                model="test",
            )

        if result["groups_found"] > 1:
            assert "kill switch engaged mid-run" in result["errors"]
