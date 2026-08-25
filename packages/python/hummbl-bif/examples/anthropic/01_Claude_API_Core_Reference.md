# Claude API — Core Reference
> Source: https://docs.anthropic.com/, https://docs.anthropic.com/llms.txt, https://docs.anthropic.com/en/api/messages, https://docs.anthropic.com/en/docs/about-claude/models
> Fetched: 2026-03-24
> Purpose: Official API documentation, model catalog, authentication, and site map for the Anthropic developer ecosystem

---

## Quick Start

**API Base URL**: `https://api.anthropic.com`

**Required headers**:
```
x-api-key: YOUR_API_KEY
anthropic-version: 2023-06-01
content-type: application/json
```

**Minimal request — curl**:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, Claude."}
    ]
  }'
```

**Minimal request — Python SDK**:
```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")  # or set ANTHROPIC_API_KEY env var

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude."}
    ]
)
print(message.content[0].text)
```

---

## Models

### Current Model Catalog (as of March 2026)

| Model | API Name | Context Window | Best For | Cost Tier |
|-------|----------|---------------|----------|-----------|
| Claude Opus 4 | `claude-opus-4-6` | 200K tokens | Complex reasoning, research, analysis | High |
| Claude Sonnet 4 | `claude-sonnet-4-6` | 200K tokens | Balanced performance + cost, production workloads | Medium |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 200K tokens | Fast, lightweight tasks, high-volume | Low |

### Model Selection Guide

| Use Case | Recommended Model |
|----------|------------------|
| Complex multi-step reasoning | claude-opus-4-6 |
| Code generation (production) | claude-sonnet-4-6 |
| Customer-facing chatbot | claude-sonnet-4-6 |
| Classification / routing | claude-haiku-4-5-20251001 |
| High-volume text processing | claude-haiku-4-5-20251001 |
| Research synthesis | claude-opus-4-6 |
| RAG Q&A | claude-sonnet-4-6 |
| Tool use (agentic) | claude-sonnet-4-6 or claude-opus-4-6 |

### Previously Available (still supported, not latest)

- `claude-3-5-sonnet-20241022` — Claude 3.5 Sonnet, still functional, not the latest generation
- `claude-3-opus-20240229` — Claude 3 Opus, still functional
- `claude-3-haiku-20240307` — Claude 3 Haiku, still functional

---

## Messages API

### Endpoint

```
POST https://api.anthropic.com/v1/messages
```

### Request Schema

```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "string or content block array"
    }
  ],
  "system": "Optional system prompt string",
  "stop_sequences": ["optional", "list", "of", "stop", "strings"],
  "stream": false,
  "temperature": 1.0,
  "top_p": null,
  "top_k": null,
  "tools": [],
  "tool_choice": null,
  "metadata": {
    "user_id": "optional"
  }
}
```

### Key Parameters Reference

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model API name (e.g. `claude-sonnet-4-6`) |
| `max_tokens` | integer | Yes | Maximum tokens to generate. Hard limit per model. |
| `messages` | array | Yes | Conversation history. Alternating user/assistant turns. |
| `system` | string | No | System prompt. Sets context, persona, instructions. |
| `stop_sequences` | string[] | No | Up to 8192 strings that halt generation when encountered |
| `stream` | boolean | No | Enable server-sent events streaming. Default: `false` |
| `temperature` | float | No | Randomness 0.0–1.0. Default 1.0. Use 0 for deterministic. |
| `top_p` | float | No | Nucleus sampling. Recommended: use temperature OR top_p, not both. |
| `tools` | array | No | Tool definitions for function/tool use. |
| `tool_choice` | object | No | Controls tool selection. `auto`, `any`, `tool` (specific). |
| `metadata.user_id` | string | No | User identifier for abuse monitoring. |

### Response Schema

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ],
  "model": "claude-sonnet-4-6",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 25,
    "output_tokens": 12
  }
}
```

### Stop Reasons

| `stop_reason` | Meaning |
|---------------|---------|
| `end_turn` | Model finished naturally |
| `max_tokens` | Hit `max_tokens` limit — may need to continue |
| `stop_sequence` | Matched one of your `stop_sequences` |
| `tool_use` | Model wants to invoke a tool (function calling) |

---

## Authentication

### API Keys

- Generated at: https://console.anthropic.com/settings/keys
- Header: `x-api-key: YOUR_KEY`
- Environment variable convention: `ANTHROPIC_API_KEY`

```python
import os
import anthropic

# SDK auto-reads ANTHROPIC_API_KEY from environment
client = anthropic.Anthropic()

# Or pass explicitly
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
```

### Workspaces

- Available on Team and Enterprise plans
- Each workspace has its own API keys and usage limits
- Useful for separating production vs. dev environments
- API keys are workspace-scoped

---

## System Prompts

A system prompt sets instructions, persona, and context before the conversation begins.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a senior Python developer. Respond with concise, production-ready code. Include type hints. Do not explain unless asked.",
    messages=[
        {"role": "user", "content": "Write a function to validate an email address."}
    ]
)
```

**Best practices for system prompts**:
- Put stable, session-level context in system (not in every user message)
- Use `<instructions>`, `<context>`, `<examples>` XML tags to organize long system prompts
- System prompts count toward input tokens — keep them tight
- System prompt is not a security boundary — treat it as soft guidance

---

## Tool Use (Function Calling)

Tools allow Claude to request data from external sources before completing a response.

### Tool Definition

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g. 'Atlanta, US'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
]
```

### Tool Use Flow

```python
import anthropic
import json

client = anthropic.Anthropic()

# Step 1: Send initial message with tools
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in Atlanta?"}
    ]
)

# Step 2: If stop_reason == "tool_use", execute the tool
if response.stop_reason == "tool_use":
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    tool_name = tool_use_block.name
    tool_input = tool_use_block.input

    # Execute your function
    result = get_weather(**tool_input)  # your implementation

    # Step 3: Return result to Claude
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather in Atlanta?"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": json.dumps(result)
                    }
                ]
            }
        ]
    )
```

---

## Streaming

Server-sent events for real-time output:

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku about recursion."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Or use the raw event stream
with client.messages.stream(...) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
```

### Streaming Event Types

| Event | When | Key Fields |
|-------|------|-----------|
| `message_start` | Beginning | `message.id`, `message.model`, initial usage |
| `content_block_start` | Each content block | `index`, `content_block.type` |
| `content_block_delta` | Each text chunk | `delta.type = "text_delta"`, `delta.text` |
| `content_block_stop` | Block complete | `index` |
| `message_delta` | Message complete | `delta.stop_reason`, final `usage` |
| `message_stop` | Stream done | — |

---

## Multi-turn Conversations

Messages maintains conversation history explicitly — you manage the array:

```python
messages = []

while True:
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a helpful assistant.",
        messages=messages
    )

    assistant_reply = response.content[0].text
    print(f"Claude: {assistant_reply}")

    messages.append({"role": "assistant", "content": assistant_reply})
```

**Important**: Always append the full `response.content` (not just extracted text) when including assistant turns — especially when tool use is involved.

---

## Vision (Image Input)

Claude can analyze images provided as base64 or URL:

```python
import base64
from pathlib import Path

# From URL
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://example.com/chart.png"
                    }
                },
                {
                    "type": "text",
                    "text": "What does this chart show?"
                }
            ]
        }
    ]
)

# From local file (base64)
image_data = base64.standard_b64encode(Path("chart.png").read_bytes()).decode("utf-8")
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                },
                {"type": "text", "text": "What does this chart show?"}
            ]
        }
    ]
)
```

### Supported Image Formats

| Format | MIME Type |
|--------|-----------|
| JPEG | `image/jpeg` |
| PNG | `image/png` |
| GIF | `image/gif` |
| WebP | `image/webp` |

---

## Extended Thinking (Beta)

Extended thinking gives Claude time to reason step-by-step before responding. Available on Opus and Sonnet models.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # Tokens Claude can use for internal reasoning
    },
    messages=[{"role": "user", "content": "Solve this complex math problem..."}]
)

# Response will include thinking blocks
for block in response.content:
    if block.type == "thinking":
        print(f"Thinking: {block.thinking}")
    elif block.type == "text":
        print(f"Answer: {block.text}")
```

---

## Error Handling

```python
import anthropic
from anthropic import APIStatusError, APIConnectionError, RateLimitError

try:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError as e:
    # 429 — back off and retry
    print(f"Rate limited: {e}")
except APIStatusError as e:
    # 4xx/5xx responses
    print(f"API error {e.status_code}: {e.message}")
except APIConnectionError as e:
    # Network issue
    print(f"Connection error: {e}")
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | — |
| 400 | Bad Request | Fix request schema |
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check permissions / account status |
| 404 | Not Found | Check endpoint URL |
| 429 | Rate Limited | Back off with exponential retry |
| 500 | Server Error | Retry with backoff |
| 529 | Overloaded | Retry with backoff (Anthropic-specific) |

---

## Token Counting

```python
# Count tokens before sending (useful for budget management)
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)
print(f"Input tokens: {token_count.input_tokens}")
```

---

## llms.txt

Anthropic provides an LLM-optimized summary of their documentation at:

- `https://docs.anthropic.com/llms.txt` — condensed summary
- `https://docs.anthropic.com/llms-full.txt` — full content dump

These are purpose-built for ingestion into AI context windows and represent the highest-priority source in BIF's source hierarchy.

---

## Anthropic Documentation Site Map

### Primary Developer Documentation (docs.anthropic.com)

**Getting Started**
- `/en/docs/welcome` — Overview of the Anthropic platform
- `/en/docs/quickstart` — Build your first Claude integration
- `/en/docs/about-claude/models` — Current model listing with API names

**Build with Claude**
- `/en/docs/build-with-claude/prompt-engineering` — Prompt engineering guide
- `/en/docs/build-with-claude/tool-use` — Tool use (function calling)
- `/en/docs/build-with-claude/vision` — Image/vision inputs
- `/en/docs/build-with-claude/pdf-support` — PDF document processing
- `/en/docs/build-with-claude/embeddings` — Text embeddings (via third party)
- `/en/docs/build-with-claude/batches` — Message Batches API
- `/en/docs/build-with-claude/token-counting` — Count tokens before sending
- `/en/docs/build-with-claude/extended-thinking` — Extended thinking (beta)
- `/en/docs/build-with-claude/computer-use` — Computer use (beta)
- `/en/docs/build-with-claude/guardrails` — Safety and content guardrails
- `/en/docs/build-with-claude/rate-limits` — Rate limits by tier
- `/en/docs/build-with-claude/multilingual` — Multilingual capabilities

**API Reference** (docs.anthropic.com/en/api)
- `/en/api/getting-started` — Authentication, versioning
- `/en/api/messages` — POST /v1/messages (primary endpoint)
- `/en/api/messages-streaming` — SSE streaming reference
- `/en/api/models` — GET /v1/models
- `/en/api/message-batches` — Batch processing
- `/en/api/files` — File uploads
- `/en/api/errors` — Error codes and handling

**Claude Code** (docs.anthropic.com/en/docs/claude-code)
- `/en/docs/claude-code/overview` — What Claude Code is
- `/en/docs/claude-code/quickstart` — Installation and first use
- `/en/docs/claude-code/cli-reference` — CLI commands
- `/en/docs/claude-code/hooks` — Pre/post action hooks
- `/en/docs/claude-code/mcp` — MCP server configuration

**Model Context Protocol** (modelcontextprotocol.io)
- `/docs/concepts/overview` — What MCP is
- `/docs/concepts/tools` — Tool definitions
- `/docs/concepts/resources` — Resource access
- `/docs/concepts/prompts` — Prompt templates
- `/sdks/python` — Python MCP SDK
- `/sdks/typescript` — TypeScript MCP SDK
- `/servers` — MCP server registry

**Platform / Console** (console.anthropic.com)
- API key management
- Usage and billing
- Workspaces
- Team management

**Engineering Blog** (anthropic.com/engineering)
- Interpretability research posts
- Constitutional AI methodology
- Frontier safety work

**Research** (anthropic.com/research)
- Model cards
- Safety papers
- Alignment papers

**Release Notes**
- `/en/release-notes` — All changes and new features

---

## LLMs.txt Summary (key entries as of March 2026)

The `llms.txt` file at docs.anthropic.com provides condensed documentation covering:

1. Claude model overview and capabilities
2. API authentication and versioning
3. Messages endpoint parameters
4. Tool use patterns
5. Streaming implementation
6. Safety and content policy
7. Rate limits by tier
8. SDK installation (`pip install anthropic`, `npm install @anthropic-ai/sdk`)

For complete ingestion, fetch `llms-full.txt` which includes the full text of all documentation pages concatenated for LLM consumption.

---

## SDK Installation

```bash
# Python
pip install anthropic

# TypeScript / Node.js
npm install @anthropic-ai/sdk

# Verify Python installation
python -c "import anthropic; print(anthropic.__version__)"
```
