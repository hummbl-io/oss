#!/usr/bin/env python3
"""Generate the free-model registry from the curated taxonomy.

The registry enumerates real (model × provider) pairs — every combination
of model family, parameter size, variant, and provider that is known to
actually serve traffic. Unlike the skills generator (which invents
combinatorial concepts), every entry here must correspond to a real model
endpoint that actually exists.

Axes (each composes with the previous):
  1. family       — model family (llama, qwen, gemma, mistral, ...)
  2. size         — parameter size in billions (7, 8, 13, 70, 120, 550, ...)
  3. variant      — model variant (instruct, chat, vision, reasoning, code, ...)
  4. provider     — hosting endpoint (nim, groq, sambanova, openrouter-free, ...)
  5. capabilities — feature flags (multimodal, function_calling, search_grounding, ...)

The capabilities axis is derived from the family + variant, not free-form.
A (family, size, variant, provider) tuple produces one registry entry with
capabilities computed from the family defaults + variant overrides.

Idempotent on ids: never overwrites an existing entry.

Usage:
    python tools/generate.py                          # generate full registry
    python tools/generate.py --dry-run                # list names only
    python tools/generate.py --provider groq          # only groq models
    python tools/generate.py --family llama           # only llama models
    python tools/generate.py --format json            # JSON output
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
REGISTRY_DIR = REPO_ROOT / "registry"


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# -- slug composition ----------------------------------------------------

VARIANT_MULTIMODAL = {"vision", "vl", "pixtral", "vl-instruct"}
VARIANT_REASONING = {"reasoning", "r1", "qwq", "thinking"}
VARIANT_CODE = {"coder", "codestral", "code"}


def is_multimodal(family_caps, variant_slug):
    """A model is multimodal if the family supports it AND the variant is vision-like,
    OR the family is always multimodal (gemini)."""
    if family_caps.get("multimodal"):
        return True
    return variant_slug in VARIANT_MULTIMODAL


def is_reasoning(family_caps, variant_slug):
    if family_caps.get("reasoning"):
        return True
    return variant_slug in VARIANT_REASONING


def is_code(variant_slug):
    return variant_slug in VARIANT_CODE


def compose_id(family_id, size, variant_slug, provider_id):
    """Compose a unique registry id: {family}-{size}b-{variant}-{provider}"""
    size_str = str(size).replace(".", "p")  # 0.5 -> 0p5, 397 -> 397
    return f"{family_id}-{size_str}b-{variant_slug}-{provider_id}"


def compose_label(family_name, size, variant_slug, provider_name):
    """Compose a human-readable label."""
    size_str = f"{size}B"
    variant_label = variant_slug.replace("-", " ").title()
    return f"{family_name} {size_str} {variant_label} ({provider_name})"


def compose_slug(family, size, variant, provider, providers_map):
    """Compose the provider-specific model slug.

    This is best-effort — the actual slug format varies by provider and model.
    The crawler (crawl.py) verifies and corrects these against live endpoints.
    """
    family_id = family["id"]
    vendor = family.get("vendor", family_id)
    templates = family.get("default_slug_templates", {})

    # Use provider-specific template if available
    if provider["id"] in templates:
        template = templates[provider["id"]]
        return template.format(
            vendor=vendor,
            family=family_id,
            size=size,
            variant=variant["slug"],
            Variant=variant["slug"].title(),
            version=_infer_version(family_id, size),
        )

    # Fallback: vendor/family-sizeb-variant
    return f"{vendor}/{family_id}-{size}b-{variant['slug']}"


def _infer_version(family_id, size):
    """Infer the model version number from family + size (best-effort)."""
    # These mappings are approximate — the crawler corrects them
    version_map = {
        "llama": {1: "3.2", 3: "3.2", 7: "3.1", 8: "3.1", 13: "3.1", 17: "4", 30: "3.3", 70: "3.3", 90: "3.2", 405: "3.1"},
        "qwen": {0.5: "2.5", 1.5: "2.5", 3: "2.5", 7: "2.5", 8: "3", 14: "2.5", 32: "3", 72: "2.5", 110: "3", 397: "3.5"},
        "gemma": {2: "2", 4: "3", 7: "2", 9: "2", 12: "3", 26: "4", 27: "3", 31: "4"},
        "mistral": {7: "v0.3", 12: "nemo", 22: "codestral", 24: "3.2", 32: "large", 123: "large"},
        "deepseek": {7: "v2", 8: "v3", 14: "r1-distill", 32: "r1-distill", 70: "v3", 671: "v3.1"},
        "nemotron": {9: "nano", 12: "nano", 50: "super", 120: "super", 550: "ultra"},
        "gpt-oss": {20: "20b", 120: "120b"},
        "phi": {1: "1", 2: "2", 3: "3-mini", 4: "3.5", 14: "3-medium"},
        "glm": {4: "4", 5: "5", 9: "4-9b", 12: "4-12b"},
        "yi": {6: "6b", 9: "9b", 34: "34b"},
        "lfm": {1: "1b", 2.6: "2.6b", 7: "7b"},
        "dbrx": {132: "132b"},
    }
    fam_map = version_map.get(family_id, {})
    return fam_map.get(size, "")


def compose_endpoint(provider):
    """Get the chat completions endpoint for a provider."""
    base = provider["api_base"]
    if provider["api_compat"] == "openai":
        return f"{base}/chat/completions"
    elif provider["api_compat"] == "google":
        return f"{base}/models/{{model}}:generateContent"
    elif provider["api_compat"] == "cohere":
        return f"{base}/chat"
    elif provider["api_compat"] == "cloudflare":
        return f"{base}/chat/completions"
    else:
        return f"{base}/chat/completions"


def compose_entry(family, size, variant, provider, providers_map):
    """Compose a full registry entry from a (family, size, variant, provider) tuple."""
    family_caps = family.get("capabilities", {})

    entry = {
        "id": compose_id(family["id"], size, variant["slug"], provider["id"]),
        "label": compose_label(family["name"], size, variant["slug"], provider["name"]),
        "family": family["id"],
        "family_name": family["name"],
        "vendor": family.get("vendor", family["id"]),
        "license": family.get("license", "unknown"),
        "size_b": size,
        "variant": variant["slug"],
        "variant_desc": variant["desc"],
        "provider": provider["id"],
        "provider_name": provider["name"],
        "api_compat": provider["api_compat"],
        "endpoint": compose_endpoint(provider),
        "model_slug": compose_slug(family, size, variant, provider, providers_map),
        "api_key_env": provider["api_key_env"],
        "api_key_url": provider["api_key_url"],
        "free_tier_type": provider["free_tier"]["type"],
        "free_tier_rate_limit": provider["free_tier"]["rate_limit"],
        "requires_cc": provider["free_tier"]["requires_cc"],
        "multimodal": is_multimodal(family_caps, variant["slug"]),
        "function_calling": family_caps.get("function_calling", False) and provider["features"]["function_calling"],
        "search_grounding": family_caps.get("search_grounding", False) and provider["features"]["search_grounding"],
        "streaming": provider["features"]["streaming"],
        "reasoning": is_reasoning(family_caps, variant["slug"]),
        "code_specialized": is_code(variant["slug"]),
        "context_window": _infer_context_window(family["id"], size),
        "cost_note": _cost_note(provider, family),
        "source": "curated",
        "verified": False,  # set True by crawl.py after live verification
    }
    return entry


def _infer_context_window(family_id, size):
    """Best-effort context window inference. Crawler corrects with live data."""
    # Common defaults
    defaults = {
        "llama": 128_000,
        "qwen": 131_072,
        "gemma": 262_144,
        "gemini": 1_000_000,
        "mistral": 128_000,
        "deepseek": 128_000,
        "nemotron": 1_000_000,  # ultra
        "gpt-oss": 128_000,
        "command-r": 128_000,
        "phi": 128_000,
        "glm": 200_000,
        "yi": 128_000,
        "lfm": 32_768,
        "laguna": 128_000,
        "dbrx": 32_768,
        "step": 128_000,
        "north": 128_000,
    }
    return defaults.get(family_id, 128_000)


def _cost_note(provider, family):
    """Generate a cost note for the UI."""
    if provider["free_tier"]["type"] == "permanent":
        return f"Free tier — {provider['free_tier']['rate_limit']}"
    elif provider["free_tier"]["type"] == "trial_credits":
        return f"Trial credits — {provider['free_tier']['rate_limit']}"
    else:
        return f"Freemium — {provider['free_tier']['rate_limit']}"


# -- generation ----------------------------------------------------------

def generate_registry(providers_data, families_data, filters=None):
    """Generate the full registry by composing family × size × variant × provider."""
    filters = filters or {}
    providers_list = providers_data["providers"]
    families_list = families_data["families"]

    # Build provider lookup
    providers_map = {p["id"]: p for p in providers_list}

    entries = []
    seen_ids = set()

    for family in families_list:
        if filters.get("family") and family["id"] != filters["family"]:
            continue

        for provider_id in family.get("providers", []):
            if filters.get("provider") and provider_id != filters["provider"]:
                continue

            provider = providers_map.get(provider_id)
            if not provider:
                continue

            for size in family.get("sizes", []):
                if filters.get("size") and size != filters["size"]:
                    continue

                for variant in family.get("variants", []):
                    if filters.get("variant") and variant["slug"] != filters["variant"]:
                        continue

                    entry = compose_entry(family, size, variant, provider, providers_map)
                    if entry["id"] not in seen_ids:
                        entries.append(entry)
                        seen_ids.add(entry["id"])

    return entries


def load_existing():
    """Load existing registry if present."""
    registry_file = REGISTRY_DIR / "registry.json"
    if registry_file.exists():
        with open(registry_file, encoding="utf-8") as f:
            return json.load(f)
    return []


def merge_registries(existing, generated):
    """Merge generated entries into existing. Existing entries are preserved
    (especially their 'verified' flag from the crawler). New entries are added."""
    existing_ids = {e["id"] for e in existing}
    new_entries = [e for e in generated if e["id"] not in existing_ids]

    # Update existing entries with any changed metadata from generated
    generated_map = {e["id"]: e for e in generated}
    updated = []
    for entry in existing:
        gen = generated_map.get(entry["id"])
        if gen:
            # Preserve verified flag and source from existing
            verified = entry.get("verified", False)
            source = entry.get("source", "curated")
            entry.update(gen)
            entry["verified"] = verified
            entry["source"] = source
        updated.append(entry)

    return updated + new_entries


def main():
    ap = argparse.ArgumentParser(description="Generate the free-model registry")
    ap.add_argument("--dry-run", action="store_true", help="List names only, write nothing")
    ap.add_argument("--format", choices=["json", "table"], default="json", help="Output format")
    ap.add_argument("--provider", help="Filter by provider id")
    ap.add_argument("--family", help="Filter by family id")
    ap.add_argument("--size", type=float, help="Filter by parameter size")
    ap.add_argument("--variant", help="Filter by variant slug")
    ap.add_argument("--merge", action="store_true", default=True,
                    help="Merge with existing registry (preserve verified flags)")
    ap.add_argument("--no-merge", action="store_false", dest="merge",
                    help="Overwrite registry entirely")
    ap.add_argument("--stats", action="store_true", help="Print statistics")
    args = ap.parse_args()

    providers_data = load_yaml(DATA_DIR / "providers.yaml")
    families_data = load_yaml(DATA_DIR / "families.yaml")

    filters = {}
    if args.provider:
        filters["provider"] = args.provider
    if args.family:
        filters["family"] = args.family
    if args.size:
        filters["size"] = args.size
    if args.variant:
        filters["variant"] = args.variant

    generated = generate_registry(providers_data, families_data, filters)

    if args.dry_run:
        if args.format == "table":
            for e in generated:
                print(f"  {e['id']:50s}  {e['model_slug']:50s}  {e['provider']}")
        else:
            for e in generated:
                print(f"  {e['id']}")
        print(f"\n{len(generated)} entries would be generated.")
        return

    if args.merge:
        existing = load_existing()
        final = merge_registries(existing, generated)
    else:
        final = generated

    # Write registry
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    registry_file = REGISTRY_DIR / "registry.json"
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    # Also write a TypeScript export for direct import
    ts_file = REGISTRY_DIR / "registry.ts"
    with open(ts_file, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by tools/generate.py — do not edit by hand.\n")
        f.write(f"// {len(final)} model-provider pairs across {len(providers_data['providers'])} providers.\n\n")
        f.write("export interface ModelEntry {\n")
        f.write("  id: string;\n  label: string;\n  family: string;\n")
        f.write("  family_name: string;\n  vendor: string;\n  license: string;\n")
        f.write("  size_b: number;\n  variant: string;\n  variant_desc: string;\n")
        f.write("  provider: string;\n  provider_name: string;\n  api_compat: string;\n")
        f.write("  endpoint: string;\n  model_slug: string;\n  api_key_env: string;\n")
        f.write("  api_key_url: string;\n  free_tier_type: string;\n")
        f.write("  free_tier_rate_limit: string;\n  requires_cc: boolean;\n")
        f.write("  multimodal: boolean;\n  function_calling: boolean;\n")
        f.write("  search_grounding: boolean;\n  streaming: boolean;\n")
        f.write("  reasoning: boolean;\n  code_specialized: boolean;\n")
        f.write("  context_window: number;\n  cost_note: string;\n")
        f.write("  source: string;\n  verified: boolean;\n}\n\n")
        f.write("export const REGISTRY: ModelEntry[] = ")
        f.write(json.dumps(final, indent=2, ensure_ascii=False))
        f.write(";\n")

    print(f"Generated {len(generated)} entries (total registry: {len(final)}).")
    print(f"  Written to: {registry_file}")
    print(f"  TypeScript: {ts_file}")

    if args.stats:
        print(f"\n--- Statistics ---")
        by_provider = {}
        by_family = {}
        by_compat = {}
        verified_count = 0
        multimodal_count = 0
        for e in final:
            by_provider[e["provider"]] = by_provider.get(e["provider"], 0) + 1
            by_family[e["family"]] = by_family.get(e["family"], 0) + 1
            by_compat[e["api_compat"]] = by_compat.get(e["api_compat"], 0) + 1
            if e["verified"]:
                verified_count += 1
            if e["multimodal"]:
                multimodal_count += 1

        print(f"  Total entries:       {len(final)}")
        print(f"  Verified (crawler):  {verified_count}")
        print(f"  Multimodal:          {multimodal_count}")
        print(f"\n  By provider:")
        for p, c in sorted(by_provider.items(), key=lambda x: -x[1]):
            print(f"    {p:25s}  {c}")
        print(f"\n  By family:")
        for f, c in sorted(by_family.items(), key=lambda x: -x[1]):
            print(f"    {f:25s}  {c}")
        print(f"\n  By API compatibility:")
        for a, c in sorted(by_compat.items(), key=lambda x: -x[1]):
            print(f"    {a:25s}  {c}")


if __name__ == "__main__":
    main()
