"""Validate the candidate Memory System Registry.

This is intentionally stdlib-only. It validates the JSON contract, checks path
existence claims, and ensures the Markdown companion mentions each registry ID
and reserved repo candidate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = Path("docs/memory_system_registry.candidate.json")
DEFAULT_MARKDOWN = Path("docs/MEMORY_SYSTEM_REGISTRY.md")

REQUIRED_TOP_LEVEL = {
    "object_type",
    "schema_version",
    "status",
    "owner",
    "decision_authority",
    "authoritative_artifact",
    "markdown_companion",
    "purpose",
    "evidence",
    "repo_roots",
    "categories",
    "entries",
    "repo_candidates",
    "promotion_gate",
    "non_goals",
}

REQUIRED_ENTRY = {
    "id",
    "category",
    "status",
    "owner",
    "write_authority",
    "state_authority",
    "receipt_path",
    "promotion",
    "paths",
}

REQUIRED_PATH = {"repo", "path", "path_type", "exists_checked", "exists"}
REQUIRED_REPO_CANDIDATE = {"name", "scope", "promotion_status"}
PATH_TYPES = {"file", "directory", "glob"}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def _missing_keys(data: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(required - set(data))


def _resolve_repo_root(repo_roots: dict[str, str], registry_path: Path, repo: str) -> Path:
    if repo not in repo_roots:
        raise ValueError(f"unknown repo root: {repo}")
    root = Path(repo_roots[repo])
    if not root.is_absolute():
        root = registry_path.parent.parent / root
    return root.resolve()


def _path_exists(root: Path, relative_path: str, path_type: str) -> bool:
    if path_type == "glob":
        return any(root.glob(relative_path))
    target = root / relative_path
    if path_type == "file":
        return target.is_file()
    if path_type == "directory":
        return target.is_dir()
    raise ValueError(f"unknown path_type: {path_type}")


def validate_registry(
    registry_path: Path,
    markdown_path: Path,
    *,
    available_repos: set[str] | None = None,
) -> list[str]:
    """Validate the registry.

    If *available_repos* is provided, only verify path existence for repos in
    that set. Other repos are skipped (they may not be checked out in this
    context, e.g. CI). If *None*, verify all repos whose root directory exists.
    """
    errors: list[str] = []
    data = _load_json(registry_path)

    for key in _missing_keys(data, REQUIRED_TOP_LEVEL):
        errors.append(f"missing top-level key: {key}")

    categories = data.get("categories", [])
    if not isinstance(categories, list) or not categories:
        errors.append("categories must be a non-empty list")
        categories = []
    category_set = set(categories)

    repo_roots = data.get("repo_roots", {})
    if not isinstance(repo_roots, dict) or not repo_roots:
        errors.append("repo_roots must be a non-empty object")
        repo_roots = {}

    entry_ids: set[str] = set()
    for index, entry in enumerate(data.get("entries", [])):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        for key in _missing_keys(entry, REQUIRED_ENTRY):
            errors.append(f"{prefix}: missing key: {key}")
        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            if entry_id in entry_ids:
                errors.append(f"{prefix}: duplicate id: {entry_id}")
            entry_ids.add(entry_id)
        if entry.get("category") not in category_set:
            errors.append(f"{prefix}: unknown category: {entry.get('category')}")
        paths = entry.get("paths", [])
        if not isinstance(paths, list) or not paths:
            errors.append(f"{prefix}: paths must be a non-empty list")
            continue
        for path_index, path_entry in enumerate(paths):
            path_prefix = f"{prefix}.paths[{path_index}]"
            if not isinstance(path_entry, dict):
                errors.append(f"{path_prefix}: must be an object")
                continue
            for key in _missing_keys(path_entry, REQUIRED_PATH):
                errors.append(f"{path_prefix}: missing key: {key}")
            path_type = path_entry.get("path_type")
            if path_type not in PATH_TYPES:
                errors.append(f"{path_prefix}: invalid path_type: {path_type}")
                continue
            if path_entry.get("exists_checked") is True:
                repo_name = str(path_entry.get("repo"))
                if available_repos is not None and repo_name not in available_repos:
                    continue
                try:
                    root = _resolve_repo_root(repo_roots, registry_path, repo_name)
                except ValueError as exc:
                    errors.append(f"{path_prefix}: {exc}")
                    continue
                if available_repos is None and not root.exists():
                    # Repo root not present in this checkout (e.g. CI only
                    # has hummbl-governance). Skip cross-repo existence
                    # verification rather than reporting a false mismatch.
                    continue
                try:
                    actual = _path_exists(root, str(path_entry.get("path")), str(path_type))
                except ValueError as exc:
                    errors.append(f"{path_prefix}: {exc}")
                    continue
                expected = path_entry.get("exists")
                if actual != expected:
                    errors.append(
                        f"{path_prefix}: exists mismatch for {path_entry.get('repo')}:{path_entry.get('path')} "
                        f"(expected {expected}, got {actual})"
                    )

    repo_candidate_names: set[str] = set()
    for index, candidate in enumerate(data.get("repo_candidates", [])):
        prefix = f"repo_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        for key in _missing_keys(candidate, REQUIRED_REPO_CANDIDATE):
            errors.append(f"{prefix}: missing key: {key}")
        name = candidate.get("name")
        if isinstance(name, str):
            if name in repo_candidate_names:
                errors.append(f"{prefix}: duplicate name: {name}")
            repo_candidate_names.add(name)

    if markdown_path.exists():
        markdown = markdown_path.read_text(encoding="utf-8")
        for entry_id in sorted(entry_ids):
            if f"`{entry_id}`" not in markdown:
                errors.append(f"{markdown_path}: missing entry id `{entry_id}`")
        for name in sorted(repo_candidate_names):
            if f"`{name}`" not in markdown:
                errors.append(f"{markdown_path}: missing repo candidate `{name}`")
    else:
        errors.append(f"markdown companion not found: {markdown_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the candidate Memory System Registry")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--repos",
        nargs="*",
        default=None,
        help="Only verify path existence for these repos (e.g. --repos hummbl-governance). "
        "If omitted, verify all repos whose root directory exists.",
    )
    args = parser.parse_args()

    try:
        errors = validate_registry(
            args.registry,
            args.markdown,
            available_repos=set(args.repos) if args.repos is not None else None,
        )
    except ValueError as exc:
        errors = [str(exc)]

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
