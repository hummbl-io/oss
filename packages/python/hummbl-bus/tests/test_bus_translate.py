from __future__ import annotations

from hummbl_bus.bus_translate import compress_message, format_entry, main, read_tail


def test_compress_drops_articles_filler_hedging() -> None:
    out = compress_message("The agent is just going to basically confirm that it is ready")
    assert "The" not in out
    assert "just" not in out
    assert "basically" not in out
    assert "going to" not in out
    assert "ready" in out


def test_compress_keeps_technical_identifiers() -> None:
    msg = "ACK devin directive. correlation_id=zai-content-engines-2026-08-09 host=anvil machine=delta"
    out = compress_message(msg)
    assert "correlation_id=zai-content-engines-2026-08-09" in out
    assert "host=anvil" in out
    assert "machine=delta" in out


def test_compress_keeps_paths_and_brackets() -> None:
    msg = "Updated [skill=start-session] [mode=side_effecting] at C:/Users/reuben/bin/bus-global.py"
    out = compress_message(msg)
    assert "[skill=start-session]" in out
    assert "[mode=side_effecting]" in out
    assert "C:/Users/reuben/bin/bus-global.py" in out


def test_compress_keeps_citations_and_refs() -> None:
    msg = "Citing BIS 90 FR 4617 (see §14) and PR #1752 for the Entity-List finding"
    out = compress_message(msg)
    assert "§14" in out
    assert "PR #1752" in out


def test_compress_empty_returns_empty() -> None:
    assert compress_message("") == ""
    assert compress_message("   ") == ""


def test_compress_expands_contractions() -> None:
    out = compress_message("I don't think it's ready yet")
    assert "do not" in out
    assert "it is" in out


def test_compress_keeps_message_types_and_agent_names() -> None:
    msg = "devin posted STATUS to all agents"
    out = compress_message(msg)
    assert "devin" in out
    assert "STATUS" in out


def test_read_tail_returns_entries(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\tHello world\n"
        "2026-08-09T15:01:00Z\tcodex\tall\tACK\tAcknowledged\n",
        encoding="utf-8",
    )
    entries = read_tail(bus, 10)
    assert len(entries) == 2
    assert entries[0]["from"] == "devin"
    assert entries[1]["type"] == "ACK"


def test_read_tail_respects_n(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    lines = [f"2026-08-09T15:0{i}:00Z\tdevin\tall\tSTATUS\tmsg{i}\n" for i in range(10)]
    bus.write_text("".join(lines), encoding="utf-8")
    entries = read_tail(bus, 3)
    assert len(entries) == 3
    assert entries[-1]["message"] == "msg9"


def test_read_tail_missing_file_returns_empty(tmp_path) -> None:
    assert read_tail(tmp_path / "nope.tsv", 5) == []


def test_read_tail_skips_malformed_lines(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thello\n"
        "broken\tline\n"
        "2026-08-09T15:01:00Z\tcodex\tall\tACK\tworld\n",
        encoding="utf-8",
    )
    entries = read_tail(bus, 10)
    assert len(entries) == 2


def test_format_entry_compressed_by_default() -> None:
    entry = {
        "timestamp": "2026-08-09T15:00:00Z",
        "from": "devin",
        "to": "all",
        "type": "STATUS",
        "message": "The agent is just basically ready",
    }
    out = format_entry(entry)
    assert "The" not in out
    assert "just" not in out
    assert "devin" in out


def test_format_entry_raw_skips_compression() -> None:
    entry = {
        "timestamp": "2026-08-09T15:00:00Z",
        "from": "devin",
        "to": "all",
        "type": "STATUS",
        "message": "The agent is just basically ready",
    }
    out = format_entry(entry, compressed=False)
    assert "The agent is just basically ready" in out


def test_main_prints_compressed_tail(tmp_path, capsys) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\tThe agent is just ready\n",
        encoding="utf-8",
    )
    rc = main(["--bus", str(bus), "1"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "devin" in captured.out
    assert "ready" in captured.out
    assert " just " not in captured.out


def test_main_raw_flag_prints_verbatim(tmp_path, capsys) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\tThe agent is just ready\n",
        encoding="utf-8",
    )
    rc = main(["--bus", str(bus), "1", "--raw"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "The agent is just ready" in captured.out


def test_main_missing_file_returns_1(tmp_path, capsys) -> None:
    rc = main(["--bus", str(tmp_path / "nope.tsv"), "5"])
    assert rc == 1


def test_main_bad_n_returns_2(tmp_path, capsys) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n", encoding="utf-8")
    rc = main(["--bus", str(bus), "abc"])
    assert rc == 2


# --- Reviewer-identified gap tests ---


def test_compress_keeps_backtick_code_spans() -> None:
    msg = 'The function `run_task("foo")` is just basically ready'
    out = compress_message(msg)
    assert '`run_task("foo")`' in out
    assert "just" not in out


def test_compress_keeps_double_quoted_strings() -> None:
    msg = 'Error: "file not found" is just a basic issue'
    out = compress_message(msg)
    assert '"file not found"' in out
    assert "just" not in out


def test_compress_keeps_issue_number_refs() -> None:
    msg = "Fixed issue #1535 and PR #1752 for the bug"
    out = compress_message(msg)
    assert "issue #1535" in out
    assert "PR #1752" in out


def test_compress_only_drop_words_returns_empty() -> None:
    assert compress_message("The just basically really perhaps maybe") == ""


def test_compress_null_bytes_preserved() -> None:
    msg = "The agent\x00binary is just ready"
    out = compress_message(msg)
    assert "\x00" in out
    assert "just" not in out
    assert "ready" in out


def test_compress_mixed_protected_content() -> None:
    msg = 'The [skill=bus] at C:/path/to/file.py said "hello" correlation_id=foo §14 PR #1'
    out = compress_message(msg)
    assert "[skill=bus]" in out
    assert "C:/path/to/file.py" in out
    assert '"hello"' in out
    assert "correlation_id=foo" in out
    assert "§14" in out
    assert "PR #1" in out


def test_compress_strips_leading_punctuation_after_drops() -> None:
    out = compress_message("The just basically, ready")
    assert not out.startswith(",")
    assert "ready" in out


def test_compress_case_insensitive_drop() -> None:
    out = compress_message("THE agent is JUST basically REALLY ready")
    assert "THE" not in out
    assert "JUST" not in out
    assert "ready" in out


def test_read_tail_n_zero_returns_empty(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n", encoding="utf-8")
    assert read_tail(bus, 0) == []


def test_read_tail_negative_n_returns_empty(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n", encoding="utf-8")
    assert read_tail(bus, -5) == []


def test_read_tail_n_larger_than_file(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n"
        "2026-08-09T15:01:00Z\tcodex\tall\tACK\tbye\n",
        encoding="utf-8",
    )
    entries = read_tail(bus, 100)
    assert len(entries) == 2


def test_read_tail_empty_file(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("", encoding="utf-8")
    assert read_tail(bus, 5) == []


def test_read_tail_all_malformed_returns_empty(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("broken\tline\nanother\tbad\n", encoding="utf-8")
    assert read_tail(bus, 5) == []


def test_read_tail_skips_empty_lines(tmp_path) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text(
        "\n"
        "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n"
        "\n"
        "2026-08-09T15:01:00Z\tcodex\tall\tACK\tbye\n"
        "\n",
        encoding="utf-8",
    )
    entries = read_tail(bus, 10)
    assert len(entries) == 2


def test_format_entry_sanitizes_tabs_in_message() -> None:
    entry = {
        "timestamp": "2026-08-09T15:00:00Z",
        "from": "devin",
        "to": "all",
        "type": "STATUS",
        "message": "hello\tworld",
    }
    out = format_entry(entry, compressed=False)
    # Output should have exactly 5 tab-separated columns, no extra tabs.
    assert out.count("\t") == 4
    assert "hello world" in out


def test_format_entry_sanitizes_newlines_in_message() -> None:
    entry = {
        "timestamp": "2026-08-09T15:00:00Z",
        "from": "devin",
        "to": "all",
        "type": "STATUS",
        "message": "hello\nworld",
    }
    out = format_entry(entry, compressed=False)
    assert "\n" not in out
    assert "hello world" in out


def test_main_help_returns_0(capsys) -> None:
    rc = main(["--help"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Usage" in captured.err


def test_main_unknown_arg_returns_2(tmp_path, capsys) -> None:
    bus = tmp_path / "messages.tsv"
    bus.write_text("2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\thi\n", encoding="utf-8")
    rc = main(["--bus", str(bus), "--bogus"])
    assert rc == 2


def test_main_bus_without_arg_returns_2(capsys) -> None:
    rc = main(["--bus"])
    assert rc == 2


def test_init_lazy_exports_compress_message() -> None:
    from hummbl_bus import compress_message as cm

    assert cm is compress_message


def test_init_lazy_exports_read_tail() -> None:
    from hummbl_bus import read_tail as rt

    assert rt is read_tail


def test_init_lazy_exports_format_entry() -> None:
    from hummbl_bus import format_entry as fe

    assert fe is format_entry


if __name__ == "__main__":
    # ponytail: runnable smoke check — run with `python test_bus_translate.py`
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        bus = pathlib.Path(td) / "messages.tsv"
        bus.write_text(
            "2026-08-09T15:00:00Z\tdevin\tall\tSTATUS\tThe agent is just basically ready correlation_id=foo\n",
            encoding="utf-8",
        )
        rc = main(["--bus", str(bus), "1"])
        print(f"\n[smoke] exit={rc}")
        assert rc == 0
    print("[smoke] OK")
