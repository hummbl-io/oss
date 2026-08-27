#!/usr/bin/env python3
"""Tuple migration CLI.

Migrates tuple JSON files from one schema version to another.

Usage:
    python scripts/migrate_tuples.py --input old.json --output new.json --target-version v2
    python scripts/migrate_tuples.py --input-dir old_dir/ --output-dir new_dir/ --target-version v2
    python scripts/migrate_tuples.py --input old.json --output new.json --target-version v2 --dry-run

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

# Migration registry: (source_version, target_version) -> migration function
MIGRATIONS: dict[tuple[str, str], Callable[[dict[str, Any]], dict[str, Any]]] = {}


def register_migration(source: str, target: str):
    """Decorator to register a migration function."""

    def decorator(
        func: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> Callable[[dict[str, Any]], dict[str, Any]]:
        MIGRATIONS[(source, target)] = func
        return func

    return decorator


@register_migration("v1", "v2")
def migrate_v1_to_v2(tuple_dict: dict[str, Any]) -> dict[str, Any]:
    """Example migration: v1 to v2.

    v1: no previous_hash field
    v2: adds optional previous_hash field (set to None)
    """
    result = dict(tuple_dict)
    if "previous_hash" not in result:
        result["previous_hash"] = None
    return result


def detect_version(tuple_dict: dict[str, Any]) -> str:
    """Detect the schema version of a tuple by inspecting its fields.

    This is a heuristic based on field presence/absence.
    """
    if "previous_hash" in tuple_dict:
        return "v2"
    # Check tuple_data for previous_hash too
    tuple_data = tuple_dict.get("tuple_data", {})
    if isinstance(tuple_data, dict) and "previous_hash" in tuple_data:
        return "v2"
    return "v1"


def find_migration_path(source: str, target: str) -> list[str] | None:
    """Find a chain of migrations from source to target version.

    Uses BFS to find the shortest path through the migration registry.
    """
    if source == target:
        return [source]

    from collections import deque

    queue = deque([(source, [source])])
    visited = {source}

    while queue:
        current, path = queue.popleft()
        for (s, t), _ in MIGRATIONS.items():
            if s == current and t not in visited:
                new_path = path + [t]
                if t == target:
                    return new_path
                visited.add(t)
                queue.append((t, new_path))

    return None


def migrate_tuple(
    tuple_dict: dict[str, Any], target_version: str
) -> tuple[dict[str, Any], list[str]]:
    """Migrate a single tuple to the target version.

    Returns (migrated_tuple, migration_path).
    """
    source_version = detect_version(tuple_dict)

    if source_version == target_version:
        return tuple_dict, [source_version]

    path = find_migration_path(source_version, target_version)
    if path is None:
        raise ValueError(f"No migration path from {source_version} to {target_version}")

    result = dict(tuple_dict)
    for i in range(len(path) - 1):
        source, target = path[i], path[i + 1]
        migration_fn = MIGRATIONS.get((source, target))
        if migration_fn is None:
            raise ValueError(f"No migration function from {source} to {target}")
        result = migration_fn(result)

    return result, path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input tuple JSON file")
    parser.add_argument("--output", help="Output tuple JSON file")
    parser.add_argument("--input-dir", help="Input directory of tuple JSON files")
    parser.add_argument("--output-dir", help="Output directory for migrated files")
    parser.add_argument("--target-version", required=True, help="Target schema version (e.g., v2)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without writing files"
    )
    args = parser.parse_args(argv)

    if args.input and args.output:
        # Single file mode
        with Path(args.input).open("r", encoding="utf-8") as f:
            tuple_dict = json.load(f)

        source = detect_version(tuple_dict)
        migrated, path = migrate_tuple(tuple_dict, args.target_version)

        print(f"Migrated {args.input}: {source} -> {args.target_version} via {' -> '.join(path)}")

        if not args.dry_run:
            with Path(args.output).open("w", encoding="utf-8") as f:
                json.dump(migrated, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"Wrote {args.output}")

    elif args.input_dir and args.output_dir:
        # Directory mode
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for p in sorted(input_dir.glob("*.json")):
            with p.open("r", encoding="utf-8") as f:
                tuple_dict = json.load(f)

            source = detect_version(tuple_dict)
            try:
                migrated, path = migrate_tuple(tuple_dict, args.target_version)
            except ValueError as e:
                print(f"SKIP {p.name}: {e}")
                continue

            print(f"Migrated {p.name}: {source} -> {args.target_version} via {' -> '.join(path)}")

            if not args.dry_run:
                out_path = output_dir / p.name
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(migrated, f, indent=2, ensure_ascii=False)
                    f.write("\n")
            count += 1

        print(f"Migrated {count} files")
    else:
        parser.error("Must specify either --input/--output or --input-dir/--output-dir")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
