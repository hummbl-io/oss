# hummbl-mcp-signal

Local stdio MCP server for sending and receiving Signal messages securely via `signal-cli`.
Zero dependencies.

## Setup
Requires `signal-cli` to be installed and available on your PATH.
You must link `signal-cli` as a secondary device to avoid deregistering your mobile device!

```bash
# Example to link as a secondary device:
signal-cli --config /path/to/isolated/config link -n "HummblMCP"
```

Then set the configuration path in your environment so the MCP server knows where to read/write state:
```bash
export SIGNAL_CONFIG_DIR="C:\\Users\\Owner\\.gemini\\config\\signal-cli-mcp"
export SIGNAL_ACCOUNT="+1234567890" # Your registered number
```

## Tools
- `signal_send_message`: Sends a message via Signal.
- `signal_receive_messages`: Pulls recent unread messages.
