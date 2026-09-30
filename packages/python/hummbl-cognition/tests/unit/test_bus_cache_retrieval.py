"""Local-cache retrieval regressions; all filesystem fixtures are temporary."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hummbl_cognition import retriever as mod
from hummbl_cognition.retriever import MemoryResult, OpenBrainRetriever


def row(message="needle", timestamp="2026-09-30T12:00:00Z"):
    return f"{timestamp}\tagent\tall\tSTATUS\t{message}\n".encode("utf-8")


def write_cache(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@pytest.fixture(autouse=True)
def isolated_sources(monkeypatch, tmp_path):
    monkeypatch.delenv("HUMMBL_BUS_CACHE_PATH", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))
    monkeypatch.setattr(mod, "_resolve_state_dirs", lambda override: [tmp_path / "state"])
    monkeypatch.setattr(mod, "_resolve_bibliography_path", lambda override: None)


def retriever(path=None):
    return OpenBrainRetriever(index=MagicMock(), bus_cache_path=path)


def search(r, query="needle", **kwargs):
    return r.search(query, sources=["bus"], **kwargs)


@pytest.mark.parametrize("selection", ["argument", "environment", "default"])
def test_cache_precedence_and_provenance(tmp_path, monkeypatch, selection):
    paths = {
        "argument": tmp_path / "explicit.tsv",
        "environment": tmp_path / "env.tsv",
        "default": Path.home() / ".cache/bus/messages.tsv",
    }
    for name, path in paths.items():
        write_cache(path, row(f"needle {name}"))
    if selection != "default":
        monkeypatch.setenv("HUMMBL_BUS_CACHE_PATH", str(paths["environment"]))
    r = retriever(paths["argument"] if selection == "argument" else None)

    results = search(r)

    assert len(results) == 1
    assert selection in results[0].content
    metadata = results[0].metadata
    assert metadata["path"] == str(paths[selection])
    assert metadata["source_selection"] == selection
    assert metadata["source_kind"] == "local_bus_cache"
    assert metadata["live_verified"] is False
    assert metadata["freshness"] == "cache_only_unverified"
    assert metadata["coverage"] == "complete_cache"
    assert metadata["latest_valid_timestamp_scope"] == "scanned_rows"
    assert metadata["latest_valid_timestamp"] == "2026-09-30T12:00:00+00:00"
    observed = datetime.fromisoformat(metadata["observed_at"])
    latest = datetime.fromisoformat(metadata["latest_valid_timestamp"])
    assert metadata["latest_message_age_seconds"] == pytest.approx(
        (observed - latest).total_seconds(), abs=0.001
    )
    assert metadata["cache_mtime_age_seconds"] == pytest.approx(
        observed.timestamp() - paths[selection].stat().st_mtime, abs=0.001
    )
    json.dumps(results[0].to_dict())


def test_no_automatic_mirror_fallback_but_explicit_override_allowed(tmp_path):
    mirror = write_cache(tmp_path / "state/coordination/messages.tsv", row())
    r = retriever()
    with patch.object(r, "_search_text_pool", side_effect=AssertionError("mirror scan")):
        assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "missing"
    assert search(retriever(mirror))


@pytest.mark.parametrize("value", [
    "", "relative.tsv", "https://example.invalid/cache.tsv", "//server/cache.tsv",
    "\\\\server\\cache.tsv", "\\/server/cache.tsv", "\\\\.\\device",
])
def test_invalid_override_does_not_fall_back(tmp_path, monkeypatch, value):
    write_cache(Path.home() / ".cache/bus/messages.tsv", row())
    monkeypatch.setenv("HUMMBL_BUS_CACHE_PATH", value)
    r = retriever()
    assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "invalid_cache_path"
    assert r.source_diagnostics["bus"]["source_selection"] == "environment"


def test_nul_in_explicit_path_is_rejected_without_fallback(tmp_path, monkeypatch):
    fallback = write_cache(tmp_path / "fallback.tsv", row())
    monkeypatch.setenv("HUMMBL_BUS_CACHE_PATH", str(fallback))
    r = retriever("C:/bad\x00.tsv")
    assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "invalid_cache_path"
    assert r.source_diagnostics["bus"]["source_selection"] == "argument"


def test_explicit_missing_cache_does_not_use_environment(tmp_path, monkeypatch):
    fallback = write_cache(tmp_path / "fallback.tsv", row())
    monkeypatch.setenv("HUMMBL_BUS_CACHE_PATH", str(fallback))
    r = retriever(tmp_path / "missing.tsv")
    assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "missing"
    assert r.source_diagnostics["bus"]["source_selection"] == "argument"


def test_nonregular_cache_is_diagnosed(tmp_path):
    r = retriever(tmp_path)
    assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "not_regular_file"


def test_unreadable_cache_is_diagnosed(tmp_path):
    path = write_cache(tmp_path / "cache.tsv", row())
    r = retriever(path)
    with patch.object(Path, "open", side_effect=PermissionError("inert fixture")):
        assert search(r) == []
    assert r.source_diagnostics["bus"]["status"] == "unreadable"
    assert r.source_diagnostics["bus"]["error_type"] == "PermissionError"


@pytest.mark.parametrize("since", [
    "2026-09-30", "20260930", "2026-09-30T00:00:00", "20260930T000000Z",
    "2026-09-30T02:00:00+02:00",
])
def test_since_is_inclusive_and_normalizes_iso_forms(tmp_path, since):
    path = write_cache(tmp_path / "cache.tsv", b"".join([
        row("needle oldmarker", "20260929T235959Z"),
        row("needle compactequal", "20260930T000000Z"),
        row("needle offsetequal", "2026-09-30T02:00:00+02:00"),
        row("needle latermarker", "2026-09-30T00:00:01Z"),
    ]))
    r = retriever(path)
    results = search(r, since=since)
    assert len(results) == 1
    assert "oldmarker" not in results[0].content_window
    for marker in ("compactequal", "offsetequal", "latermarker"):
        assert marker in results[0].content_window
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["since_utc"] == "2026-09-30T00:00:00+00:00"
    assert diagnostic["rows_after_since"] == 3
    assert diagnostic["latest_valid_timestamp"] == "2026-09-30T00:00:01+00:00"


@pytest.mark.parametrize("since", ["", "invalid", 123, {}, "9999-12-31T23:59:59-23:59"])
def test_invalid_since_fails_before_open(tmp_path, since):
    path = write_cache(tmp_path / "cache.tsv", row())
    r = retriever(path)
    with patch.object(Path, "open", side_effect=AssertionError("unexpected read")):
        assert search(r, since=since) == []
    assert r.source_diagnostics["bus"]["status"] == "invalid_since"


def test_malformed_rows_and_utf8_are_excluded_without_replacement(tmp_path):
    invalid = [b"not\ta\trow\n", row("bad", "not-a-time"),
               row("naive", "2026-09-30T12:00:00"),
               row().replace(b"needle", b"needle\xff")]
    path = write_cache(tmp_path / "cache.tsv", b"".join(invalid) + row("needle\textra payload"))
    r = retriever(path)
    results = search(r)
    assert len(results) == 1
    assert "extra payload" in results[0].content
    assert "\ufffd" not in results[0].content
    assert r.source_diagnostics["bus"]["malformed_rows"] == 4
    assert r.source_diagnostics["bus"]["valid_rows"] == 1


@pytest.mark.parametrize("data,query,since,status", [
    (b"", "needle", None, "empty"),
    (b"malformed\n", "needle", None, "no_valid_rows"),
    (row(), "needle", "2026-10-01", "no_rows_after_since"),
    (row("different"), "needle", None, "no_match"),
    (row(), "the a an", None, "no_match"),
])
def test_no_hit_diagnostics(tmp_path, data, query, since, status):
    path = write_cache(tmp_path / "cache.tsv", data)
    r = retriever(path)
    assert search(r, query, since=since) == []
    assert r.source_diagnostics["bus"]["status"] == status
    assert r.source_diagnostics["bus"]["path"] == str(path)
    json.dumps(r.source_diagnostics)


def test_diagnostics_reset_for_each_search(tmp_path):
    r = retriever(tmp_path / "missing.tsv")
    assert search(r) == []
    assert "bus" in r.source_diagnostics
    with patch.object(r, "_search_text_pool", return_value=[]):
        assert r.search("needle", sources=["briefings"]) == []
    assert r.source_diagnostics == {}


@pytest.mark.parametrize("row_count", [200, 201])
def test_row_bound_and_latest_timestamp_cover_only_scanned_rows(tmp_path, row_count):
    # A future timestamp in the first row must not describe an excluded row.
    data = row("excludedneedle", "2099-01-01T00:00:00Z")
    data += row("ordinary") * (row_count - 1)
    r = retriever(write_cache(tmp_path / "cache.tsv", data))
    results = search(r, "excludedneedle")
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["rows_scanned"] == 200
    assert diagnostic["row_tail_truncated"] is (row_count == 201)
    assert bool(results) is (row_count == 200)
    expected = "2099-01-01T00:00:00+00:00" if row_count == 200 else "2026-09-30T12:00:00+00:00"
    assert diagnostic["latest_valid_timestamp"] == expected
    assert diagnostic["coverage"] == ("complete_cache" if row_count == 200 else "partial_cache")


class RecordingCache:
    def __init__(self, file, reads, before_read=None):
        self.file = file
        self.reads = reads
        self.before_read = before_read

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.file.close()

    def fileno(self):
        return self.file.fileno()

    def seek(self, *args):
        return self.file.seek(*args)

    def read(self, size=-1):
        assert size >= 0, "An unbounded read was attempted"
        if self.before_read:
            callback, self.before_read = self.before_read, None
            callback()
        offset = self.file.tell()
        data = self.file.read(size)
        self.reads.append((offset, size, len(data)))
        return data


def record_cache_reads(monkeypatch, path, reads, callback=None):
    real_open = Path.open

    def open_path(self, *args, **kwargs):
        file = real_open(self, *args, **kwargs)
        if self == path and args == ("rb",):
            return RecordingCache(file, reads, callback)
        return file

    monkeypatch.setattr(Path, "open", open_path)
    return real_open


@pytest.mark.parametrize("extra_prefix", [False, True])
def test_actual_one_mib_bound_and_leading_boundary_byte(tmp_path, monkeypatch, extra_prefix):
    size = mod._BUS_CACHE_MAX_BYTES
    final = row("needle")
    first = row("padding")
    body = first[:-1] + b"x" * (size - len(first) - len(final)) + b"\n" + final
    data = (row("outside") if extra_prefix else b"") + body
    path = write_cache(tmp_path / "cache.tsv", data)
    reads = []
    record_cache_reads(monkeypatch, path, reads)
    r = retriever(path)

    result = search(r)[0]
    assert "needle" in result.content
    assert "needle" in result.content_window

    assert sum(actual for _, _, actual in reads) == size + int(extra_prefix)
    assert all(offset + requested <= len(data) for offset, requested, _ in reads)
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["bytes_read"] == size + int(extra_prefix)
    assert diagnostic["byte_tail_truncated"] is extra_prefix
    assert diagnostic["partial_first_row_discarded"] is False
    assert diagnostic["valid_rows"] == 2


def test_utf8_cut_in_first_partial_row_does_not_poison_complete_rows(tmp_path, monkeypatch):
    final = row("needle complete")
    data = row("é" * 30) + final
    # Start at the second byte of the final é in the preceding row.
    monkeypatch.setattr(mod, "_BUS_CACHE_MAX_BYTES", len(final) + 2)
    path = write_cache(tmp_path / "cache.tsv", data)
    r = retriever(path)
    assert search(r)
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["partial_first_row_discarded"] is True
    assert diagnostic["malformed_rows"] == 0
    assert diagnostic["valid_rows"] == 1
    assert diagnostic["bytes_read"] == len(final) + 3


def test_entire_tail_inside_one_unterminated_row(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_BUS_CACHE_MAX_BYTES", 64)
    path = write_cache(tmp_path / "cache.tsv", row("needle " + "x" * 200).rstrip(b"\n"))
    r = retriever(path)
    assert search(r) == []
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["partial_first_row_discarded"] is True
    assert diagnostic["partial_last_row_discarded"] is True
    assert diagnostic["rows_scanned"] == 0
    assert diagnostic["bytes_read"] == 65
    assert diagnostic["coverage"] == "partial_cache"


def test_unterminated_last_row_is_intentionally_discarded(tmp_path):
    data = row("old", "2026-09-29T12:00:00Z") + row("needle").rstrip(b"\n")
    r = retriever(write_cache(tmp_path / "cache.tsv", data))
    assert search(r, since="2026-09-30") == []
    diagnostic = r.source_diagnostics["bus"]
    assert diagnostic["partial_last_row_discarded"] is True
    assert diagnostic["coverage"] == "partial_cache"
    assert diagnostic["status"] == "no_rows_after_since"
    assert diagnostic["rows_scanned"] == 1


@pytest.mark.parametrize("initially_complete", [False, True])
def test_concurrent_append_does_not_read_beyond_captured_eof(tmp_path, monkeypatch, initially_complete):
    initial = row("needle original")
    if not initially_complete:
        initial = initial.rstrip(b"\n")
    path = write_cache(tmp_path / "cache.tsv", initial)
    reads = []
    real_open = Path.open

    def append_after_fstat():
        with real_open(path, "ab") as writer:
            writer.write((b"" if initially_complete else b"\n") + row("needle appended"))

    record_cache_reads(monkeypatch, path, reads, append_after_fstat)
    r = retriever(path)
    results = search(r)
    assert bool(results) is initially_complete
    assert all(offset + requested <= len(initial) for offset, requested, _ in reads)
    assert r.source_diagnostics["bus"]["file_bytes"] == len(initial)
    assert r.source_diagnostics["bus"]["changed_during_read"] is True
    assert r.source_diagnostics["bus"]["coverage"] == "partial_cache"
    assert r.source_diagnostics["bus"]["partial_last_row_discarded"] is (not initially_complete)
    if results:
        assert "appended" not in results[0].content_window


def test_filtered_context_is_not_reloaded_from_source(tmp_path):
    data = row("needle excluded", "2026-09-29T12:00:00Z") + row("needle retained")
    path = write_cache(tmp_path / "cache.tsv", data)
    r = retriever(path)
    with patch.object(Path, "read_text", side_effect=AssertionError("unbounded reload")):
        result = search(r, since="2026-09-30")[0]
    assert "retained" in result.content_window
    assert "excluded" not in result.content_window


def test_physical_read_does_not_prefetch_past_captured_eof(tmp_path, monkeypatch):
    initial = row("needle original")
    path = write_cache(tmp_path / "cache.tsv", initial)
    real_open = Path.open

    def append_after_fstat():
        with real_open(path, "ab") as writer:
            writer.write(row("later " + "x" * 1000))

    class CheckedCache(RecordingCache):
        def read(self, size=-1):
            data = super().read(size)
            raw = getattr(self.file, "raw", self.file)
            assert raw.tell() <= len(initial), "Buffered I/O read beyond captured EOF"
            return data

    def open_path(self, *args, **kwargs):
        file = real_open(self, *args, **kwargs)
        if self == path and args == ("rb",):
            return CheckedCache(file, [], append_after_fstat)
        return file

    monkeypatch.setattr(Path, "open", open_path)
    assert search(retriever(path))


def test_all_bus_producers_skip_context_path_rereads(tmp_path):
    result = MemoryResult(source="bus", entry_id="bus:legacy", score=1,
                          content="needle", metadata={"path": str(tmp_path / "cache.tsv")})
    with patch.object(Path, "read_text", side_effect=AssertionError("unbounded reload")):
        retriever()._expand_windows([result])
    assert result.content_window == "needle"


def test_non_bus_context_expansion_is_preserved(tmp_path):
    path = tmp_path / "briefing.md"
    path.write_text("before needle after", encoding="utf-8")
    result = MemoryResult(source="briefings", entry_id="briefing", score=1,
                          content="needle", metadata={"path": str(path)})
    retriever()._expand_windows([result])
    assert result.content_window == "before needle after"


@pytest.mark.parametrize("has_cache", [False, True])
def test_mcp_exposes_serializable_source_diagnostics_without_live_ledger(tmp_path, monkeypatch, has_cache):
    from hummbl_cognition import mcp_server

    if has_cache:
        write_cache(Path.home() / ".cache/bus/messages.tsv", row())
    monkeypatch.setattr(mcp_server, "get_indexer", lambda: MagicMock())
    monkeypatch.setattr(mcp_server, "LEDGER_DIR", tmp_path / "state/cognition")
    response = mcp_server.handle_tool("memory_search", {"query": "needle", "sources": ["bus"]})
    assert response["count"] == int(has_cache)
    assert response["source_diagnostics"]["bus"]["status"] == ("available" if has_cache else "missing")
    assert response["source_diagnostics"]["bus"]["live_verified"] is False
    json.dumps(response)
