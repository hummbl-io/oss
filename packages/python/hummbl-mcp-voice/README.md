# hummbl-mcp-voice

MCP stdio server for managing outbound voice calls and retrieving call artifacts asynchronously. Currently implements the Vapi API as the underlying engine.

## Tools
- `voice_dispatch_call`: Initiate an outbound call.
- `voice_retrieve_call_logs`: Fetch the structured JSONL call logs for a specific call ID.
- `voice_download_recording`: Download the stereo or mono recording for a specific call ID to a local file.

## Configuration
Set `VAPI_PRIVATE_API_KEY` in the environment. Fetch this from 1Password via the MCP or env var securely.
