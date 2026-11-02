# hummbl-free-models

A registry of open-weights and free-tier language models, plus the tooling that
crawls providers, generates the registry, and validates it against a schema.

The point is a machine-readable answer to "which models can I route to at zero
marginal cost right now" — kept as data you can diff, not a hand-maintained
list in prose.

- MIT OR Apache-2.0
- Python >= 3.11, requires `pyyaml`

## Install

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-free-models
```

## Source data

| Path | Contents |
|---|---|
| `registry/registry.json` | Seed registry — 82 entries |
| `data/providers.yaml` | Provider definitions: base URL, API-key env var, models path |
| `data/families.yaml` | Model-family definitions used to normalize slugs |

These paths are relative to `packages/python/hummbl-free-models` in the
checkout. Use the editable install above to work with this source data.
The registry is a **seed**, not a complete census; catalog entries do not
prove that inference is currently available or free.

## Regenerate the registry

The shipped family definitions do not yet contain the complete `providers`,
`sizes`, and `variants` lists that generation requires, so the preview currently
produces zero entries. Populate those definitions before generating a replacement.
In particular, `--no-merge` would overwrite the seed with an empty registry while
these inputs are incomplete.

```bash
# 1. Preview generation without changing the seed
python -m hummbl_free_models.generate --dry-run

# 2. Preview the complete NVIDIA provider configuration without fetching or saving
python -m hummbl_free_models.crawl --provider nvidia-nim --dry-run --no-save

# 3. Validate against the schema
python -m hummbl_free_models.validate
```

Crawling reads provider credentials from the `api_key_env` named in
`data/providers.yaml`. No keys are bundled, and the crawler only calls each
provider's model-listing endpoint.

To fetch and save NVIDIA model-list results, supply `NVIDIA_API_KEY` through your
secret store and run `python -m hummbl_free_models.crawl --provider nvidia-nim`.
The `openai-compatible` entry is an incomplete placeholder; complete or remove it
before crawling all providers. An unfiltered crawl can fail on that placeholder
before reaching a configured provider.

## Adding a provider

Copy a complete provider entry in `data/providers.yaml` and update its ID,
name, endpoint, authentication environment variable, free-tier metadata, and
feature flags. Set `models_endpoint` to the full model-list URL: the current
crawler uses it directly and does not join `base_url` with `models_path`.

The crawler supports OpenAI-compatible model-list responses and several
provider-specific formats. It infers family, parameter size, and variant from
model slugs, then matches them against existing registry entries. Generation
merges with the existing registry by default; `--no-merge` replaces it.

## Caveat

Free tiers change without notice. A registry entry records what a provider
advertised at crawl time; re-crawl before relying on it for routing decisions.
