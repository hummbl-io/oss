# Anthropic — Delta Document
> Source: https://docs.anthropic.com/en/release-notes, https://docs.anthropic.com/en/docs/about-claude/models, https://www.anthropic.com/news
> Fetched: 2026-03-24
> Purpose: What changed since last ingestion — new models, API changes, deprecations, and confirmed-current items as of March 2026

---

## Sources Checked (Navigation Map for This Delta)

Pages reviewed for this delta document — captured to confirm what was and was not checked:

| Source | URL | Method |
|--------|-----|--------|
| Release notes | https://docs.anthropic.com/en/release-notes | Full read |
| Model catalog | https://docs.anthropic.com/en/docs/about-claude/models | Full read |
| API messages reference | https://docs.anthropic.com/en/api/messages | Spot-check |
| Extended thinking docs | https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking | Full read |
| Claude Code overview | https://docs.anthropic.com/en/docs/claude-code/overview | Full read |
| MCP overview | https://modelcontextprotocol.io/docs/concepts/overview | Full read |
| Batches API | https://docs.anthropic.com/en/docs/build-with-claude/batches | Full read |
| Anthropic news | https://www.anthropic.com/news | Headlines scan |

---

## New Since Last Ingestion

### Models

- **claude-opus-4-6** (NEW — latest Claude 4 flagship): Released as the most capable Claude 4 model. 200K context. Replaces claude-3-opus as the recommended choice for complex reasoning. — https://docs.anthropic.com/en/docs/about-claude/models
- **claude-sonnet-4-6** (NEW — latest Claude 4 balanced): The recommended production model for most workloads. Outperforms Claude 3.5 Sonnet on coding and reasoning benchmarks at comparable pricing. — https://docs.anthropic.com/en/docs/about-claude/models
- **claude-haiku-4-5-20251001** (NEW — latest Claude 4 fast): Fastest, most cost-effective model in the Claude 4 family. Use for high-volume, latency-sensitive tasks. — https://docs.anthropic.com/en/docs/about-claude/models

### Features

- **Extended thinking**: Claude can now use internal reasoning tokens before generating a response. Accessed via `thinking: {type: "enabled", budget_tokens: N}` parameter. Available on Opus and Sonnet models. Significant improvement on math, coding, and complex multi-step tasks. — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking
- **Claude Code CLI**: Full agentic coding tool released. Integrates with local codebase, runs tests, edits files, creates PRs. Available via `npm install -g @anthropic-ai/claude-code`. Not the same as the SDK. — https://docs.anthropic.com/en/docs/claude-code
- **Model Context Protocol (MCP)**: Open protocol for connecting AI models to external tools and data sources. Anthropic-developed but open source. Server registry at modelcontextprotocol.io. Python and TypeScript SDKs available. — https://modelcontextprotocol.io
- **Message Batches API**: Async batch processing at 50% cost reduction. Submit up to 10,000 messages per batch; results polled or retrieved by batch ID. — https://docs.anthropic.com/en/docs/build-with-claude/batches
- **Files API**: Upload files (PDFs, images, text) once and reference them in multiple requests by file ID. Reduces redundant token transmission for large documents. — https://docs.anthropic.com/en/api/files
- **Token counting endpoint**: New `POST /v1/messages/count_tokens` endpoint for measuring input size before generating a response — useful for context budget management. — https://docs.anthropic.com/en/docs/build-with-claude/token-counting
- **Computer use (beta)**: Claude can control a computer (cursor, keyboard, screen) via tool definitions. Available with `anthropic-beta: computer-use-2024-10-22` header. Not for production use yet. — https://docs.anthropic.com/en/docs/build-with-claude/computer-use
- **Prompt caching**: Cache frequently reused prompt prefixes (system prompts, large documents) to reduce cost and latency on repeated requests. Accessed via `cache_control` field. — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### SDK

- **anthropic Python SDK 0.40+**: Added streaming helpers, improved async support, added `count_tokens()` method, and first-class tool use helpers.
- **@anthropic-ai/sdk TypeScript 0.28+**: Parallel improvements to the Python SDK. Added streaming text helper.

---

## Changed

- **Model naming convention**: Claude 4 models use `claude-[name]-4-[subversion]` format (e.g., `claude-sonnet-4-6`). Previous generation used `claude-3-[name]-YYYYMMDD` format. The `-YYYYMMDD` suffix still appears on Haiku 4.5 (`claude-haiku-4-5-20251001`) indicating point releases within the generation.
- **Recommended model guidance**: Anthropic now explicitly recommends `claude-sonnet-4-6` as the default for most production workloads (previously the recommendation was less specific). Use Opus only when Sonnet genuinely underperforms on the task.
- **Tool use response handling**: The assistant response `content` field now more commonly contains a mix of `text` and `tool_use` blocks in the same message. Always iterate the full `content` array rather than assuming `content[0]` is the text response.
- **API versioning**: `anthropic-version: 2023-06-01` remains current. No new version header required for Claude 4 features. Extended thinking and computer use use separate beta headers.
- **Rate limits**: Tier structure updated. Tier 4 limits increased significantly for Sonnet. Exact limits at docs.anthropic.com/en/docs/build-with-claude/rate-limits — check current docs as these change frequently.
- **Workspaces**: Now available on all paid plans (previously Team+ only). Workspaces isolate API keys and usage tracking per project or environment.

---

## Deprecated / Removed

- **`/v1/complete` endpoint**: **DEPRECATED** — Use `/v1/messages` for all new development. The `/v1/complete` endpoint supported the older prompt format (`\n\nHuman: ...\n\nAssistant:`). It still accepts requests but will not receive new model support. Migration: replace `prompt` parameter with `messages` array and convert `Human:`/`Assistant:` markers to role-based turns.

```python
# OLD (deprecated) — /v1/complete
{
  "model": "claude-2",
  "prompt": "\n\nHuman: Hello\n\nAssistant:",
  "max_tokens_to_sample": 256
}

# NEW — /v1/messages
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 256,
  "messages": [{"role": "user", "content": "Hello"}]
}
```

- **Claude 2 / Claude Instant models**: Not available via API for new API keys. Existing keys may still have access but these models receive no updates. Migrate to Claude 3+ or Claude 4 for all new work.
- **`max_tokens_to_sample` parameter**: Replaced by `max_tokens` in the Messages API. The old name is not accepted.
- **`Human:` / `Assistant:` prompt format**: Only valid for the deprecated `/v1/complete` endpoint. Messages API uses the `role` field instead.

---

## Unchanged (Spot-Checked)

- **Authentication method**: `x-api-key` header still the standard. No changes to API key format or scope.
- **`anthropic-version` header**: `2023-06-01` still current. No new version required.
- **Core Messages API schema**: `model`, `max_tokens`, `messages`, `system`, `stop_sequences`, `temperature`, `top_p`, `top_k` parameters all unchanged.
- **Tool definition format**: `name`, `description`, `input_schema` (JSON Schema) — no changes.
- **Content block types**: `text`, `image`, `tool_use`, `tool_result` — all stable.
- **Stop reasons**: `end_turn`, `max_tokens`, `stop_sequence`, `tool_use` — no new values added.
- **Streaming SSE format**: Event types and field names unchanged.
- **Python SDK install**: `pip install anthropic` still correct.
- **TypeScript SDK install**: `npm install @anthropic-ai/sdk` still correct.
- **Base URL**: `https://api.anthropic.com` unchanged.
- **MCP server protocol**: JSON-RPC 2.0 over stdio or HTTP/SSE. Schema stable since launch.

---

## Migration Priority

| Change | Urgency | Action |
|--------|---------|--------|
| `/v1/complete` → `/v1/messages` | High — before new feature work | Refactor prompt format + update model IDs |
| Claude 2 → Claude 4 | High | Update `model` field to `claude-sonnet-4-6` or `claude-haiku-4-5-20251001` |
| Add extended thinking to reasoning tasks | Medium | Add `thinking` parameter where accuracy matters more than speed |
| Evaluate MCP for tool integrations | Medium | Replace custom tool servers with MCP-compliant servers |
| Batch API for batch workloads | Low — if cost sensitive | Wrap bulk requests in Batch API for 50% cost reduction |
