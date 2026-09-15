from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_bus.seed_import import import_bus_history, seed_request_id


def test_seed_request_id_is_deterministic() -> None:
    line = "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello\n"
    rid1 = seed_request_id(line)
    rid2 = seed_request_id(line)
    assert rid1 == rid2
    assert rid1.startswith("seed-")


def test_seed_request_id_differs_for_different_lines() -> None:
    line1 = "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello\n"
    line2 = "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\tworld\n"
    assert seed_request_id(line1) != seed_request_id(line2)


def _write_source_tsv(path: Path, rows: list[str], header: str | None = None) -> None:
    lines = []
    if header:
        lines.append(header)
    lines.extend(rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_import_bus_history_imports_rows(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        [
            "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello",
            "2026-01-01T00:01:00Z\tcodex\tall\tSTATUS\tworld",
        ],
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"

    summary = import_bus_history(
        source_path=source,
        dest_bus_path=dest,
        ledger_path=ledger,
    )

    assert summary["rows_seen"] == 2
    assert summary["rows_imported"] == 2
    assert summary["rows_duplicate"] == 0
    assert summary["rows_quarantined"] == 0
    assert dest.exists()
    lines = dest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    # ledger has 2 entries
    ledger_lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(ledger_lines) == 2


def test_import_bus_history_dry_run_does_not_write(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        ["2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello"],
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"

    summary = import_bus_history(
        source_path=source,
        dest_bus_path=dest,
        ledger_path=ledger,
        dry_run=True,
    )

    assert summary["rows_seen"] == 1
    assert summary["rows_imported"] == 1
    assert not dest.exists()
    assert not ledger.exists()


def test_import_bus_history_quarantines_privileged_rows(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        [
            "2026-01-01T00:00:00Z\treuben\tall\tDECISION\tapprove plan",
            "2026-01-01T00:01:00Z\tcodex\tall\tSTATUS\thello",
        ],
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"
    quarantine = tmp_path / "quarantine.jsonl"

    summary = import_bus_history(
        source_path=source,
        dest_bus_path=dest,
        ledger_path=ledger,
        quarantine_path=quarantine,
    )

    assert summary["rows_seen"] == 2
    assert summary["rows_quarantined"] == 1
    assert summary["rows_imported"] == 1
    assert quarantine.exists()
    q_lines = quarantine.read_text(encoding="utf-8").splitlines()
    assert len(q_lines) == 1
    entry = json.loads(q_lines[0])
    assert entry["schema"] == "hummbl_bus.import_quarantine.v1"
    assert entry["type"] == "DECISION"
    assert (
        entry["reason"]
        == "historical privileged row lacks authenticated principal proof"
    )
    # privileged row not in dest
    dest_lines = dest.read_text(encoding="utf-8").splitlines()
    assert len(dest_lines) == 1
    assert "STATUS" in dest_lines[0]


def test_import_bus_history_is_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        ["2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello"],
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"

    import_bus_history(source_path=source, dest_bus_path=dest, ledger_path=ledger)
    summary2 = import_bus_history(
        source_path=source, dest_bus_path=dest, ledger_path=ledger
    )

    assert summary2["rows_seen"] == 1
    assert summary2["rows_duplicate"] == 1
    assert summary2["rows_imported"] == 0
    # dest still has only 1 line
    lines = dest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_import_bus_history_skips_header(tmp_path: Path) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        ["2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello"],
        header="timestamp_utc\tfrom\tto\ttype\tmessage",
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"

    summary = import_bus_history(
        source_path=source,
        dest_bus_path=dest,
        ledger_path=ledger,
    )

    assert summary["rows_seen"] == 1
    assert summary["rows_imported"] == 1
    lines = dest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "header" not in lines[0].lower() or "timestamp" not in lines[0]


def test_import_bus_history_raises_on_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_bus_history(
            source_path=tmp_path / "nonexistent.tsv",
            dest_bus_path=tmp_path / "dest.tsv",
            ledger_path=tmp_path / "ledger.jsonl",
        )


def test_import_bus_history_skips_malformed_rows(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source.tsv"
    _write_source_tsv(
        source,
        [
            "2026-01-01T00:00:00Z\tcodex\tall\tSTATUS\thello",
            "only\tthree\tfields",
            "2026-01-01T00:01:00Z\tcodex\tall\tSTATUS\tworld",
        ],
    )
    dest = tmp_path / "dest.tsv"
    ledger = tmp_path / "ledger.jsonl"

    summary = import_bus_history(
        source_path=source,
        dest_bus_path=dest,
        ledger_path=ledger,
    )

    assert summary["rows_seen"] == 2
    assert summary["rows_imported"] == 2
