# hummbl-mcp-discord

Local stdio MCP server for reading and drafting Discord messages via the Discord Bot API.
Zero dependencies.

## Setup
```bash
export DISCORD_BOT_TOKEN="your-bot-token"
```

## Tools
- `discord_channel_summarize`: Fetch the last 50 messages from a channel ID.
- `discord_draft_reply`: Draft a message to a channel (posts to a dedicated drafts channel or stages it).
