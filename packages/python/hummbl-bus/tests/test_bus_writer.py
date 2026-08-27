from __future__ import annotations

import json
import os
import stat
from concurrent.futures import ProcessPoolExecutor, as_completed

import pytest
from hummbl_bus.bus_writer import (
    _cross_process_lock,
    _validate_kimi_constraints,
    is_signed_message,
    post_message,
    read_verified_messages,
    validate_tsv_integrity,
    verify_bus_message,
    write_dead_letter,
)

SECRET = b"0123456789abcdef0123456789abcdef"


def _concurrent_writer(args: tuple[str, str, str, str, str]) -> None:
    bus_path_str, sender, recipient, msg_type, message = args
    post_message(
        bus_path_str,
        sender,
        recipient,
        msg_type,
        message,
        validate=False,
    )


def _concurrent_dead_letter_writer(args: tuple[str, int]) -> None:
    dead_letter_path_str, i = args
    write_dead_letter(
        dead_letter_path=dead_letter_path_str,
        source="concurrency-test",
        reason=f"reason-{i}",
        payload={"i": i},
    )


def test_post_message_writes_signed_and_unsigned_rows(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "hello",
        secret=SECRET,
        validate=False,
    )
    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "world",
        validate=False,
    )

    lines = bus_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    signed_parts = lines[0].split("\t")
    unsigned_parts = lines[1].split("\t")

    assert is_signed_message(signed_parts[4])
    assert not is_signed_message(unsigned_parts[4])

    verified, content = verify_bus_message(*signed_parts[:4], signed_parts[4], SECRET)
    assert verified
    assert content == "hello"

    verified, content = verify_bus_message(
        *unsigned_parts[:4],
        unsigned_parts[4],
        SECRET,
    )
    assert not verified
    assert content == "world"


def test_validate_tsv_integrity_reports_bad_rows(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "hello",
        validate=False,
    )

    with bus_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("broken\tline\twith\textra\tcolumns\ttoo\tmany\n")

    valid_count, errors = validate_tsv_integrity(bus_path)

    assert valid_count == 1
    assert len(errors) == 1
    assert "Expected 5 columns" in errors[0]


def test_read_verified_messages_returns_only_signed_messages(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "hello",
        secret=SECRET,
        validate=False,
    )
    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "world",
        validate=False,
    )

    messages = read_verified_messages(
        bus_path,
        secret=SECRET,
        require_signature=True,
        since_minutes=999999,
    )

    assert len(messages) == 1
    assert messages[0]["sender"] == "codex"
    assert messages[0]["message"] == "hello"


def test_write_dead_letter_serializes_jsonl(tmp_path) -> None:
    dead_letters = tmp_path / "dead_letters.jsonl"

    write_dead_letter(
        dead_letter_path=dead_letters,
        source="unit-test",
        reason="boom",
        payload={"x": 1},
        metadata={"y": 2},
        timestamp="2026-05-08T23:40:00Z",
    )

    record = json.loads(dead_letters.read_text(encoding="utf-8").strip())
    assert record == {
        "metadata": {"y": 2},
        "payload": {"x": 1},
        "reason": "boom",
        "source": "unit-test",
        "timestamp": "2026-05-08T23:40:00Z",
    }


def test_concurrent_writes_lose_no_messages(tmp_path) -> None:
    """Process-level concurrency: N processes writing simultaneously must not
    lose messages. This is the failure mode hummbl-governance #1915 fixed -- without
    a cross-process lock, two processes can read the same content, both append,
    and the second os.replace silently overwrites the first.
    """
    bus_path = tmp_path / "messages.tsv"
    n = 20

    args = [(str(bus_path), "codex", "all", "STATUS", f"msg-{i}") for i in range(n)]
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_concurrent_writer, a) for a in args]
        for f in as_completed(futures):
            f.result()

    lines = bus_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == n, (
        f"expected {n} messages, got {len(lines)} (message loss detected)"
    )
    # Every message should be present exactly once.
    messages = sorted(line.split("\t")[4] for line in lines)
    expected = sorted(f"msg-{i}" for i in range(n))
    assert messages == expected


def test_cross_process_lock_creates_sibling_lock_file(tmp_path) -> None:
    """The cross-process lock must use a sibling .bus.lock file, not the bus
    file itself, so msvcrt.locking on Windows does not block os.replace.
    """
    bus_path = tmp_path / "messages.tsv"
    bus_path.write_text("existing\n", encoding="utf-8")

    with _cross_process_lock(bus_path):
        lock_file = bus_path.parent / ".bus.lock"
        assert lock_file.exists(), "sibling .bus.lock file was not created"

    # Lock file persists (it's reusable); that's fine. The bus file is untouched.
    assert bus_path.read_text(encoding="utf-8") == "existing\n"


def test_concurrent_dead_letters_lose_no_records(tmp_path) -> None:
    """Dead-letter writes must also be concurrency-safe under the cross-process
    lock.
    """
    dead_letters = tmp_path / "dead_letters.jsonl"
    n = 15

    args = [(str(dead_letters), i) for i in range(n)]
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_concurrent_dead_letter_writer, a) for a in args]
        for f in as_completed(futures):
            f.result()

    lines = dead_letters.read_text(encoding="utf-8").splitlines()
    assert len(lines) == n, f"expected {n} dead-letter records, got {len(lines)}"


def test_write_dead_letter_redacts_metadata_credentials(tmp_path) -> None:
    """#1761: dead-letter metadata with bridge_url must have credentials redacted."""
    dead_letters = tmp_path / "dead_letters.jsonl"

    write_dead_letter(
        dead_letter_path=dead_letters,
        source="bridge-client",
        reason="remote-write-failed",
        metadata={
            "bridge_url": "https://user:password@host.example.com/path"  # pragma: allowlist secret
        },
        timestamp="2026-08-15T12:00:00Z",
    )

    record = json.loads(dead_letters.read_text(encoding="utf-8").strip())
    metadata = record["metadata"]
    assert isinstance(metadata, dict)
    bridge_url = str(metadata["bridge_url"])
    assert "password" not in bridge_url
    assert "<redacted>" in bridge_url


def test_write_dead_letter_hardens_permissions_on_new_file(tmp_path) -> None:
    """D4 (#1731): dead_letters.jsonl must be 0o600 on POSIX (best-effort on Windows)."""
    dead_letters = tmp_path / "dead_letters.jsonl"

    write_dead_letter(
        dead_letter_path=dead_letters,
        source="unit-test",
        reason="boom",
        payload={"x": 1},
    )

    # On POSIX, verify 0o600. On Windows, os.chmod is a no-op for the mode bits
    # we care about, so we just verify the file was created successfully.
    if os.name != "nt":
        file_stat = dead_letters.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"
    else:
        assert dead_letters.exists()


def test_write_dead_letter_preserves_existing_file_permissions(tmp_path) -> None:
    """Permission hardening only applies to NEW files, not existing ones."""
    dead_letters = tmp_path / "dead_letters.jsonl"
    dead_letters.write_text('{"existing": true}\n', encoding="utf-8")

    if os.name != "nt":
        os.chmod(dead_letters, 0o644)

    write_dead_letter(
        dead_letter_path=dead_letters,
        source="unit-test",
        reason="boom",
    )

    if os.name != "nt":
        file_stat = dead_letters.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        assert mode == 0o644, f"existing file permissions changed: {oct(mode)}"


def test_kimi_identities_retired(tmp_path) -> None:
    """Kimi was retired 2026-04-05 — all kimi-* identities should be rejected."""
    # kimi-1 and kimi-2 were previously approved; now they should be rejected
    with pytest.raises(ValueError, match="Unapproved Kimi identity"):
        _validate_kimi_constraints("kimi-1", "STATUS", enforce=True)

    with pytest.raises(ValueError, match="Unapproved Kimi identity"):
        _validate_kimi_constraints("kimi-2", "STATUS", enforce=True)


def test_kimi_constraints_skip_non_kimi_senders() -> None:
    """Non-kimi senders should not trigger kimi constraints."""
    # Should not raise — codex is not a kimi sender
    _validate_kimi_constraints("codex", "STATUS", enforce=True)
    _validate_kimi_constraints("claude-code", "DECISION", enforce=True)
