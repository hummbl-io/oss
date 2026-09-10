# hummbl-mcp-proton

Local MCP server (stdio) for Proton services (Mail, Drive, Calendar, Meet).

## Setup

This server communicates over standard input/output using the Model Context Protocol (MCP).

## Install

```bash
pip install hummbl-mcp-proton
```

## Run

```bash
hummbl-mcp-proton
```

To use it with Antigravity or Gemini, add the following to your `mcp_config.json`:

```json
    "proton": {
      "command": "hummbl-mcp-proton"
    }
```

## Tools Available
- `proton_mail_search`: Search emails via IMAP
- `proton_mail_send`: Send emails via SMTP
- `proton_drive_list`: List Drive files
- `proton_calendar_events`: List Calendar events

## Implementation Notes
* Mail tools require the **Proton Mail Bridge** running on the local network to expose IMAP/SMTP ports.
* Drive and Calendar implementations will require reverse-engineered APIs (e.g. `proton-python-client`) or future official bridge support.
