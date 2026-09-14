#!/usr/bin/env python3
"""Repair the hash chain in a CLP ledger.

Recomputes previous_hash for each entry based on the actual previous VALID
line. Preserves entries with previous_hash=None (skip chain validation).
Preserves content_hash (does not recompute it — that's a separate issue).

Matches the validator's behavior: entries that fail parse or content_hash
verification are skipped (prev_line is not updated), so the chain links past
bad entries to the last good entry.

Usage:
    python repair_chain.py <ledger.jsonl> [--dry-run] [--backup]

The repair:
1. Reads all lines from the ledger.
2. For each line, parses the JSON and verifies content_hash.
3. If parse or content_hash fails: leave the line as-is, don't update prev_line.
4. If previous_hash is None: skip chain validation, update prev_line.
5. If previous_hash is set: recompute as sha256(prev_line), update if different.
6. Writes the repaired ledger (with backup if --backup).

The 12 content_hash mismatches and 2 parse errors are NOT fixed by this
script — they indicate content was modified after writing or structural
issues. Those need separate investigation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from hummbl_cognition.models import LedgerEntry, compute_content_hash


def repair_chain(ledger_path: Path, *, dry_run: bool = False, backup: bool = False) -> tuple[int, int, int]:
    """Repair the previous_hash chain in a ledger.

    Returns:
        (total_lines, repaired_count, skipped_none_count)
    """
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    repaired = 0
    skipped_none = 0
    new_lines: list[str] = []

    prev_line: str | None = None
    for i, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if not stripped:
            new_lines.append("")
            continue

        try:
            d = json.loads(stripped)
            entry = LedgerEntry.from_dict(d)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Parse error — leave as-is, don't update prev_line (matches validator)
            new_lines.append(stripped)
            continue

        # Verify content_hash (matches validator behavior)
        import re as _re
        if _re.match(r"^[a-f0-9]{64}$", entry.content_hash):
            if not entry.verify_hash():
                # content_hash mismatch — leave as-is, don't update prev_line
                new_lines.append(stripped)
                continue

        current_prev_hash = d.get("previous_hash")
        if current_prev_hash is None:
            # Skip chain validation — leave previous_hash=None
            skipped_none += 1
            new_lines.append(stripped)
            prev_line = stripped
            continue

        if prev_line is None:
            # First entry with previous_hash set but no prev_line — leave as-is
            new_lines.append(stripped)
            prev_line = stripped
            continue

        expected_prev = hashlib.sha256(prev_line.encode("utf-8")).hexdigest()
        if current_prev_hash != expected_prev:
            # Replace ONLY the previous_hash value in the original line
            # to preserve all other formatting (spaces, key order, etc.)
            # This avoids changing the line's hash for unrelated reasons.
            new_stripped = stripped.replace(
                f'"previous_hash": "{current_prev_hash}"',
                f'"previous_hash": "{expected_prev}"',
            )
            if new_stripped == stripped:
                # Fallback: try without space after colon
                new_stripped = stripped.replace(
                    f'"previous_hash":"{current_prev_hash}"',
                    f'"previous_hash":"{expected_prev}"',
                )
            if new_stripped == stripped:
                # Last resort: re-serialize (may change formatting)
                d["previous_hash"] = expected_prev
                new_stripped = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
            new_lines.append(new_stripped)
            repaired += 1
            if dry_run:
                print(f"Line {i}: would repair previous_hash for {d.get('id', '?')}")
            prev_line = new_stripped
        else:
            new_lines.append(stripped)
            prev_line = stripped

    if dry_run:
        print(f"\nDry run: {total} lines, {repaired} would be repaired, {skipped_none} skipped (previous_hash=None)")
        return total, repaired, skipped_none

    if backup:
        backup_path = ledger_path.with_suffix(ledger_path.suffix + ".bak")
        if not backup_path.exists():
            shutil.copy2(ledger_path, backup_path)
            print(f"Backup written to {backup_path}", file=sys.stderr)
        else:
            print(f"Backup already exists at {backup_path} — not overwriting", file=sys.stderr)

    ledger_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Repaired: {total} lines, {repaired} fixed, {skipped_none} skipped (previous_hash=None)")
    return total, repaired, skipped_none


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repair_chain",
        description="Repair the previous_hash chain in a CLP ledger.",
    )
    parser.add_argument("ledger", type=Path, help="Path to ledger.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be repaired without writing")
    parser.add_argument("--backup", action="store_true", help="Write a .bak backup before repairing")
    args = parser.parse_args(argv)

    if not args.ledger.exists():
        print(f"Error: ledger not found: {args.ledger}", file=sys.stderr)
        return 1

    total, repaired, skipped = repair_chain(args.ledger, dry_run=args.dry_run, backup=args.backup)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
