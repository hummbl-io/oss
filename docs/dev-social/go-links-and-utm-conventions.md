# Canonical Dev-Social Go-Links and UTM Tracking

## Status

- **Document type:** convention specification
- **Issue:** #635
- **Date:** 2026-07-01

## Purpose

Add canonical public go-links and UTM conventions for developer social distribution so forum posts and social posts can be tracked without polluting canonical artifact URLs.

## Go-Links

Canonical go-links are short, stable URLs that redirect to the canonical artifact. They are used in social posts, forum posts, and developer social distribution. The canonical artifact URL stays clean; the go-link carries the UTM tracking parameters.

### Proposed Go-Links

| Go-Link                  | Redirects To                                                       | Purpose                  |
| ------------------------ | ------------------------------------------------------------------ | ------------------------ |
| `/go/runtime-mediation`  | `docs/public-writing/generation-is-not-release-authority.md`       | Runtime mediation essay  |
| `/go/guardrail-receipts` | `schemas/public/release_guardrail_receipt.schema.json`             | Guardrail receipt schema |
| `/go/model-router`       | `docs/model-router/full-stack-correctness-routing.md`              | Model Router v2 design   |
| `/go/ownward`            | `docs/ownward/design-gates/reflective-friction-anti-abdication.md` | Ownward design gates     |

### Go-Link Rules

1. Go-links are **stable** — once published, they do not change
2. Go-links **redirect** to the canonical artifact — they are not the artifact itself
3. Go-links are **public-safe** — no private repos, no internal paths
4. Go-links are **tracked** — UTM parameters are appended at distribution time, not baked in
5. Go-links are **canonical** — one go-link per topic, not per post

## UTM Convention

### Base UTM Parameters

| Parameter      | Value               | Description                                                                   |
| -------------- | ------------------- | ----------------------------------------------------------------------------- |
| `utm_source`   | platform name       | Where the link is posted (linkedin, x, hf_forum, langchain_forum, github)     |
| `utm_medium`   | `social` or `forum` | Distribution medium                                                           |
| `utm_campaign` | topic slug          | Topic campaign (runtime-mediation, guardrail-receipts, model-router, ownward) |
| `utm_content`  | post slug           | Specific post identifier (essay-v1, thread-v1, forum-post-v1)                 |

### Example

```
https://hummbl.dev/go/runtime-mediation?utm_source=linkedin&utm_medium=social&utm_campaign=runtime-mediation&utm_content=essay-v1
```

### UTM Rules

1. UTM parameters are **appended at distribution time**, not baked into the go-link
2. UTM parameters are **lowercase** with hyphens (not underscores)
3. `utm_source` is the **platform name**, not the account name
4. `utm_campaign` matches the **go-link slug** (e.g., `/go/runtime-mediation` → `utm_campaign=runtime-mediation`)
5. `utm_content` identifies the **specific post** (e.g., `essay-v1`, `thread-v1`, `forum-post-v1`)
6. Canonical artifact URLs **never** carry UTM parameters

## Distribution Channels

| Channel            | utm_source        | utm_medium |
| ------------------ | ----------------- | ---------- |
| LinkedIn           | `linkedin`        | `social`   |
| X/Twitter          | `x`               | `social`   |
| Hugging Face Forum | `hf_forum`        | `forum`    |
| LangChain Forum    | `langchain_forum` | `forum`    |
| GitHub             | `github`          | `social`   |
| Discord            | `discord`         | `social`   |
| Reddit             | `reddit`          | `social`   |

## Tracking Matrix

| Go-Link                  | Campaign             | Channels                               |
| ------------------------ | -------------------- | -------------------------------------- |
| `/go/runtime-mediation`  | `runtime-mediation`  | LinkedIn, X, HF Forum, LangChain Forum |
| `/go/guardrail-receipts` | `guardrail-receipts` | LinkedIn, X, HF Forum                  |
| `/go/model-router`       | `model-router`       | LinkedIn, X                            |
| `/go/ownward`            | `ownward`            | LinkedIn, X                            |

## Implementation Notes

### Go-Link Redirect Setup

Go-links can be implemented via:

1. **Cloudflare Pages redirects** (`_redirects` file)
2. **Cloudflare Workers** (programmatic redirect)
3. **Static site redirect** (meta refresh or JS redirect)

Recommended: Cloudflare Pages `_redirects` file for simplicity.

### `_redirects` file format

```
/go/runtime-mediation    /docs/public-writing/generation-is-not-release-authority.md    302
/go/guardrail-receipts   /schemas/public/release_guardrail_receipt.schema.json         302
/go/model-router         /docs/model-router/full-stack-correctness-routing.md         302
/go/ownward              /docs/ownward/design-gates/reflective-friction-anti-abdication.md    302
```

Use 302 (temporary) redirects so the go-link can be updated if the canonical artifact moves.

## Do Not Infer

- Do not infer that go-links are live (they need to be implemented in the redirect system)
- Do not infer that UTM tracking is set up (it needs analytics integration)
- Do not infer that this is a final list (go-links may be added or retired)
