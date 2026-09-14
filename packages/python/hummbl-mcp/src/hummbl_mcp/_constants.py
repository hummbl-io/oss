"""Constants stub — lazy-loaded from config when available."""
import os

MCP_PROTOCOL_VERSION: str = "2024-11-05"
PORT_BUS_BRIDGE: int = 18790
REMOTE_OPEN_BRAIN_URL: str = os.environ.get("REMOTE_OPEN_BRAIN_URL", "http://127.0.0.1:11435")
REMOTE_OLLAMA_URL: str = os.environ.get("REMOTE_OLLAMA_URL", "http://127.0.0.1:11434")
BUS_CANONICAL_BRIDGE_URL: str = os.environ.get("BUS_CANONICAL_BRIDGE_URL", "http://127.0.0.1:18790")
CONTENT_TYPE_JSON: str = "application/json"
