#!/usr/bin/env python3
"""Validate the free-model registry against the schema.

Checks:
  - Every entry has all required fields
  - Every id is unique
  - Every model_slug is unique within a provider
  - Every provider id exists in providers.yaml
  - Every family id exists in families.yaml
  - Endpoint URLs are valid
  - Boolean fields are actually booleans
  - context_window is a positive integer
  - size_b is a positive number

Usage:
    python tools/validate.py              # validate registry.json
    python tools/validate.py --verbose    # show all entries
    python tools/validate.py --strict     # exit 1 on warnings
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Fix Windows console encoding for unicode output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
REGISTRY_DIR = REPO_ROOT / "registry"

REQUIRED_FIELDS = [
    "id", "label", "family", "family_name", "vendor", "license",
    "size_b", "variant", "variant_desc", "provider", "provider_name",
    "api_compat", "endpoint", "model_slug", "api_key_env", "api_key_url",
    "free_tier_type", "free_tier_rate_limit", "requires_cc",
    "multimodal", "function_calling", "search_grounding", "streaming",
    "reasoning", "code_specialized", "context_window", "cost_note",
    "source", "verified",
]

BOOLEAN_FIELDS = [
    "requires_cc", "multimodal", "function_calling", "search_grounding",
    "streaming", "reasoning", "code_specialized", "verified",
]

VALID_API_COMPAT = {"openai", "anthropic", "google", "cloudflare", "cohere", "custom"}
VALID_FREE_TIER = {"permanent", "trial_credits", "freemium"}
VALID_SOURCES = {"curated", "crawler", "manual"}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(registry, providers_data, families_data):
    errors = []
    warnings = []

    provider_ids = {p["id"] for p in providers_data["providers"]}
    family_ids = {f["id"] for f in families_data["families"]}

    seen_ids = set()
    seen_slugs = {}  # provider -> set of slugs

    for i, entry in enumerate(registry):
        eid = entry.get("id", f"<index {i}>")

        # Required fields
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{eid}: missing required field '{field}'")

        # Unique id
        if entry.get("id") in seen_ids:
            errors.append(f"{eid}: duplicate id")
        seen_ids.add(entry.get("id"))

        # Unique model_slug within provider
        slug = entry.get("model_slug", "")
        provider = entry.get("provider", "")
        if provider not in seen_slugs:
            seen_slugs[provider] = set()
        if slug in seen_slugs[provider]:
            errors.append(f"{eid}: duplicate model_slug '{slug}' for provider '{provider}'")
        seen_slugs[provider].add(slug)

        # Provider exists in taxonomy
        if provider and provider not in provider_ids:
            errors.append(f"{eid}: unknown provider '{provider}'")

        # Family exists in taxonomy
        family = entry.get("family", "")
        if family and family not in family_ids:
            warnings.append(f"{eid}: unknown family '{family}' (may be new)")

        # Boolean fields are boolean
        for field in BOOLEAN_FIELDS:
            if field in entry and not isinstance(entry[field], bool):
                errors.append(f"{eid}: field '{field}' is {type(entry[field]).__name__}, expected bool")

        # api_compat is valid
        compat = entry.get("api_compat", "")
        if compat and compat not in VALID_API_COMPAT:
            errors.append(f"{eid}: invalid api_compat '{compat}'")

        # free_tier_type is valid
        ft = entry.get("free_tier_type", "")
        if ft and ft not in VALID_FREE_TIER:
            errors.append(f"{eid}: invalid free_tier_type '{ft}'")

        # source is valid
        source = entry.get("source", "")
        if source and source not in VALID_SOURCES:
            errors.append(f"{eid}: invalid source '{source}'")

        # Endpoint is a valid URL
        endpoint = entry.get("endpoint", "")
        if endpoint and not re.match(r"^https?://", endpoint):
            errors.append(f"{eid}: invalid endpoint URL '{endpoint}'")

        # context_window is positive
        ctx = entry.get("context_window", 0)
        if not isinstance(ctx, int) or ctx <= 0:
            errors.append(f"{eid}: context_window must be positive int, got {ctx}")

        # size_b is positive
        size = entry.get("size_b", 0)
        if not isinstance(size, (int, float)) or size < 0:
            errors.append(f"{eid}: size_b must be non-negative number, got {size}")

        # model_slug is non-empty
        if not slug:
            errors.append(f"{eid}: empty model_slug")

        # api_key_env is non-empty
        if not entry.get("api_key_env"):
            errors.append(f"{eid}: empty api_key_env")

    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description="Validate the free-model registry")
    ap.add_argument("--verbose", action="store_true", help="Show all entries")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on warnings")
    args = ap.parse_args()

    registry_file = REGISTRY_DIR / "registry.json"
    if not registry_file.exists():
        print(f"ERROR: {registry_file} not found. Run generate.py first.")
        sys.exit(1)

    with open(registry_file, encoding="utf-8") as f:
        registry = json.load(f)

    providers_data = load_yaml(DATA_DIR / "providers.yaml")
    families_data = load_yaml(DATA_DIR / "families.yaml")

    print(f"Validating {len(registry)} entries...")
    errors, warnings = validate(registry, providers_data, families_data)

    if errors:
        print(f"\n{len(errors)} ERRORS:")
        for e in errors[:50]:
            print(f"  ✗ {e}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")

    if warnings:
        print(f"\n{len(warnings)} WARNINGS:")
        for w in warnings[:20]:
            print(f"  ⚠ {w}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")

    if not errors and not warnings:
        print(f"\n✓ All {len(registry)} entries valid.")
    elif not errors:
        print(f"\n✓ No errors. {len(warnings)} warnings.")

    if args.verbose:
        print(f"\n--- Entries by provider ---")
        by_provider = {}
        for e in registry:
            by_provider.setdefault(e["provider"], []).append(e)
        for p in sorted(by_provider):
            print(f"\n  {p} ({len(by_provider[p])} entries):")
            for e in by_provider[p][:5]:
                v = "✓" if e.get("verified") else " "
                print(f"    [{v}] {e['id']}")
            if len(by_provider[p]) > 5:
                print(f"    ... and {len(by_provider[p]) - 5} more")

    if errors:
        sys.exit(1)
    if args.strict and warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
