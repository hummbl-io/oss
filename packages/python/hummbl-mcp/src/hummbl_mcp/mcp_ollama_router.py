import sys
import os
import json
import subprocess
import threading
import time
import urllib.request
import urllib.error
import traceback
import hashlib
from pathlib import Path

from hummbl_mcp._config import SUBPROCESS_TIMEOUT_NORMAL
from hummbl_mcp._constants import (
    REMOTE_OLLAMA_URL,
    CONTENT_TYPE_JSON,
    MCP_PROTOCOL_VERSION,
)

# Import DelegationTokenManager for agent identity verification
try:
    try:
        from hummbl_governance.delegation import DelegationTokenManager, DelegationTokenCapabilityToken
    except ImportError:
        pass
    _IDP_AVAILABLE = True
except ImportError:
    _IDP_AVAILABLE = False

# Redirect sys.stdout to sys.stderr so any print() statements don't corrupt JSON-RPC
original_stdout = sys.stdout
sys.stdout = sys.stderr

def log(msg):
    sys.stderr.write(f"[mcp-ollama-router] {msg}\n")
    sys.stderr.flush()

# In-memory Thread-Safe Cache for GPU Load
class GPUCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_query = 0.0
        self.data = None

gpu_cache = GPUCache()

# Model hash verification
_MODEL_HASHES_PATH = Path(__file__).resolve().parents[2] / "docs" / "security" / "model_hashes.jsonl"

def _load_model_hashes() -> dict[str, str]:
    """Load model SHA256 hashes from allowlist."""
    hashes = {}
    if _MODEL_HASHES_PATH.exists():
        try:
            for line in _MODEL_HASHES_PATH.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                model = entry.get("model")
                sha256 = entry.get("sha256")
                if model and sha256 and sha256 != "PLACEHOLDER_HASH":
                    hashes[model] = sha256
        except Exception as e:
            log(f"Failed to load model hashes: {e}")
    return hashes

_MODEL_HASHES = _load_model_hashes()

def _verify_model_hash(model: str) -> bool:
    """
    Verify model is in hash allowlist.

    Runtime note: this currently validates allowlist membership only.
    Full blob-digest verification is planned and not yet enforced here.

    Returns True if model is in allowlist, False otherwise.
    """
    return model in _MODEL_HASHES

# Tailscale identity verification (whitelist-based stopgap)
# TODO: Integrate with Tailscale identity API for cryptographic verification
# Configure known hostnames via the MCP_KNOWN_HOSTNAMES env var (comma-separated)
_KNOWN_TAILSCALE_HOSTNAMES = set(
    h.strip() for h in os.environ.get("MCP_KNOWN_HOSTNAMES", "").split(",") if h.strip()
)

def _verify_tailscale_identity(origin_host: str) -> bool:
    """
    Verify origin_host is a known Tailscale hostname.
    
    This is a stopgap until proper Tailscale identity API integration.
    Uses hostname whitelist instead of cryptographic peer certificate validation.
    
    Returns True if origin_host is in known hostnames, False otherwise.
    """
    normalized = origin_host.lower().strip()
    return normalized in _KNOWN_TAILSCALE_HOSTNAMES

def _verify_agent_identity_token(token_str: str, expected_subject: str) -> bool:
    """
    Verify agent identity token using DelegationTokenManager.
    
    This validates that the request is from an authorized agent with a valid
    delegation capability token signed by the shared secret.
    
    Args:
        token_str: Base64-encoded DCT string from env var or request header
        expected_subject: Expected agent identity (e.g., "claude-code", "codex")
    
    Returns:
        True if token is valid and subject matches, False otherwise.
    """
    if not _IDP_AVAILABLE:
        log("IDP module not available. Skipping agent identity token verification.")
        return True  # Fail-open if IDP is not available
    
    try:
        # Get DCT_SECRET from environment
        dct_secret = os.environ.get("DCT_SECRET")
        if not dct_secret:
            log("DCT_SECRET not set. Skipping agent identity token verification.")
            return True  # Fail-open if secret is not configured
        
        # Initialize token manager
        manager = DelegationTokenManager(secret=dct_secret.encode("utf-8"))
        
        # Deserialize token
        token = DelegationTokenCapabilityToken.from_env_string(token_str)
        
        # Verify signature
        if not token.verify_signature(dct_secret.encode("utf-8")):
            log(f"Agent identity token signature verification failed for {expected_subject}")
            return False
        
        # Verify subject matches expected agent
        if token.subject != expected_subject:
            log(f"Agent identity token subject mismatch: expected {expected_subject}, got {token.subject}")
            return False
        
        # Verify token is not expired
        if token.is_expired():
            log(f"Agent identity token expired for {expected_subject}")
            return False
        
        return True
    except Exception as e:
        log(f"Agent identity token verification error: {e}")
        return False

# Endpoints configuration
# Local endpoint uses HTTP on localhost; remote endpoint uses REMOTE_OLLAMA_URL
# (typically a Tailscale interface with mTLS handled by the network layer).
ENDPOINTS = [
    {
        "hostname": "local",
        "url": "http://127.0.0.1:11434",
        "local_url": "http://127.0.0.1:11434",
        "tls_enabled": False,
    },
    {
        "hostname": "remote",
        "url": REMOTE_OLLAMA_URL,
        "local_url": REMOTE_OLLAMA_URL,
        "tls_enabled": True,
    }
]

TOOLS = [
    {
        "name": "route_ollama_request",
        "description": "Policy-enforced model inference router. Intercepts and redirects requests to appropriate endpoints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin_host": {
                    "type": "string",
                    "description": "The hostname originating the request."
                },
                "model": {
                    "type": "string",
                    "description": "The requested model name (e.g., 'qwen3:8b')."
                },
                "prompt": {
                    "type": "string",
                    "description": "Raw prompt string."
                },
                "options": {
                    "type": "object",
                    "description": "Optional generation options."
                },
                "agent_identity_token": {
                    "type": "string",
                    "description": "Base64-encoded Delegation Capability Token for agent identity verification."
                }
            },
            "required": ["origin_host", "model", "prompt"]
        }
    },
    {
        "name": "get_gpu_load",
        "description": "Retrieve active GPU metrics from nvidia-smi with a 5-second caching window to prevent execution bottleneck.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_thermal_enforcement",
        "description": "Verifies that the local GPU is locked to its configured power cap and clock locks.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_mesh_ollama_endpoints",
        "description": "Retrieve active Ollama endpoints status across the Tailscale mesh.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def query_gpu_stats():
    with gpu_cache.lock:
        now = time.time()
        if gpu_cache.data is not None and (now - gpu_cache.last_query) < 5.0:
            gpu_cache.data["cache_hit"] = True
            return gpu_cache.data

        try:
            cmd = ["nvidia-smi", "--query-gpu=power.draw,power.limit,clocks.gr,temperature.gpu,memory.total,memory.used", "--format=csv,noheader,nounits"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_NORMAL)
            if res.returncode != 0:
                raise FileNotFoundError("nvidia-smi execution returned non-zero")

            stdout = res.stdout.strip()
            parts = [p.strip() for p in stdout.split(",")]

            data = {
                "power_draw_watts": float(parts[0]),
                "power_cap_watts": float(parts[1]),
                "gpu_clock_mhz": float(parts[2]),
                "temperature_c": float(parts[3]),
                "vram_total_mb": float(parts[4]),
                "vram_used_mb": float(parts[5]),
                "cache_hit": False
            }
            gpu_cache.data = data
            gpu_cache.last_query = now
            return data
        except Exception as e:
            log(f"nvidia-smi lookup failed: {e}. Returning degraded unknown telemetry.")
            return {
                "telemetry_available": False,
                "error": str(e),
                "power_draw_watts": None,
                "power_cap_watts": None,
                "gpu_clock_mhz": None,
                "temperature_c": None,
                "vram_total_mb": None,
                "vram_used_mb": None,
                "cache_hit": False
            }

def check_endpoint_health(url):
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            return True, models
    except Exception as e:
        log(f"Ollama endpoint offline check: {url} ({e})")
        return False, []

def handle_route_ollama_request(arguments):
    origin_host = arguments.get("origin_host", "").lower()
    model = arguments.get("model", "")
    prompt = arguments.get("prompt", "")
    options = arguments.get("options", {})
    agent_identity_token = arguments.get("agent_identity_token", "")
    degraded_reasons: list[str] = []

    # 0. Verify Tailscale identity (origin_host spoofing protection)
    if not _verify_tailscale_identity(origin_host):
        log(f"Origin host {origin_host} not in known Tailscale hostnames. Rejecting request.")
        return {"content": [{"type": "text", "text": f"Origin host {origin_host} not in known Tailscale hostnames. Identity verification failed."}], "isError": True}

    # 0.5. Verify agent identity token (IDP integration)
    if agent_identity_token:
        if not _IDP_AVAILABLE:
            degraded_reasons.append("idp_module_unavailable_fail_open")
        elif not os.environ.get("DCT_SECRET"):
            degraded_reasons.append("idp_secret_missing_fail_open")

        # Extract expected subject from origin_host
        # This is a simplified mapping - in production, this should be derived from
        # the agent roster or a more sophisticated identity mapping
        expected_subject = origin_host
        if not _verify_agent_identity_token(agent_identity_token, expected_subject):
            log(f"Agent identity token verification failed for {expected_subject}. Rejecting request.")
            return {"content": [{"type": "text", "text": f"Agent identity token verification failed for {expected_subject}. IDP enforcement active."}], "isError": True}
    else:
        log("No agent identity token provided. Skipping IDP verification (fail-open).")
        degraded_reasons.append("agent_identity_token_missing_fail_open")

    # 1. Verify model hash allowlist (supply-chain protection)
    # Runtime deprecation marker: currently allowlist-membership only, not blob digest verification.
    degraded_reasons.append("model_hash_membership_only")
    if not _verify_model_hash(model):
        log(f"Model {model} not in hash allowlist. Rejecting request.")
        return {"content": [{"type": "text", "text": f"Model {model} not in hash allowlist. Supply-chain protection active."}], "isError": True}

    # 2. Target Selection — try local endpoint first, fall back to remote
    target_endpoint = "local"
    target_url = "http://127.0.0.1:11434"

    # Forward the request to Ollama
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    if options:
        payload["options"] = options

    try:
        req = urllib.request.Request(
            f"{target_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": CONTENT_TYPE_JSON}
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            response_text = resp_data.get("response", "")
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "routed_to": target_endpoint,
                        "response": response_text,
                        "policy_degraded": len(degraded_reasons) > 0,
                        "degraded_reasons": degraded_reasons
                    }, indent=2)
                }],
                "isError": False
            }
    except Exception as e:
        # Fallback to remote endpoint if local failed to connect
        log(f"Local endpoint failed: {e}. Attempting fallback to remote.")
        try:
            fallback_url = REMOTE_OLLAMA_URL
            req = urllib.request.Request(
                f"{fallback_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": CONTENT_TYPE_JSON}
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                response_text = resp_data.get("response", "")
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "routed_to": "remote",
                            "response": response_text,
                            "policy_degraded": len(degraded_reasons) > 0,
                            "degraded_reasons": degraded_reasons
                        }, indent=2)
                    }],
                    "isError": False
                }
        except Exception as fe:
            return {"content": [{"type": "text", "text": f"Ollama execution failed on both local and remote endpoints: {fe}"}], "isError": True}

        return {"content": [{"type": "text", "text": f"Ollama routing failed: {e}"}], "isError": True}

def handle_get_gpu_load():
    data = query_gpu_stats()
    return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}], "isError": False}

def handle_check_thermal_enforcement():
    stats = query_gpu_stats()
    if not stats.get("telemetry_available", True):
        result = {
            "power_cap_locked": False,
            "clock_speed_locked": False,
            "safety_status": "UNKNOWN_TELEMETRY",
            "error": stats.get("error", "GPU telemetry unavailable"),
        }
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False}

    power_cap = stats.get("power_cap_watts", 0.0)
    gpu_clock = stats.get("gpu_clock_mhz", 0.0)
    temp = stats.get("temperature_c", 0.0)

    # Power cap and clock lock checks
    power_cap_locked = (power_cap <= 270.0)
    clock_speed_locked = (gpu_clock <= 1800.0)

    safety_status = "SAFE"
    if temp >= 80.0:
        safety_status = "DANGER_THERMAL"
    elif power_cap > 270.0:
        safety_status = "WARN_DEGRADED"

    result = {
        "power_cap_locked": power_cap_locked,
        "clock_speed_locked": clock_speed_locked,
        "safety_status": safety_status
    }
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False}

def handle_list_mesh_ollama_endpoints():
    endpoints_status = []
    for ep in ENDPOINTS:
        # Check active status using local URL if local host is running mcp-server
        url_to_test = ep["local_url"] if ep["hostname"] == "local" else ep["url"]
        active, models = check_endpoint_health(url_to_test)
        endpoints_status.append({
            "hostname": ep["hostname"],
            "url": ep["url"],
            "active": active,
            "loaded_models": models
        })

    return {"content": [{"type": "text", "text": json.dumps({"endpoints": endpoints_status}, indent=2)}], "isError": False}

def main():
    log("Initializing MCP Ollama Router...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                log(f"Invalid JSON input: {line}")
                continue

            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            response = {"jsonrpc": "2.0"}
            if req_id is not None:
                response["id"] = req_id

            if method == "initialize":
                response["result"] = {
                    "protocolVersion": params.get("protocolVersion", MCP_PROTOCOL_VERSION),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mcp-ollama-router", "version": "0.1.0"}
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                response["result"] = {"tools": TOOLS}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                try:
                    if tool_name == "route_ollama_request":
                        response["result"] = handle_route_ollama_request(arguments)
                    elif tool_name == "get_gpu_load":
                        response["result"] = handle_get_gpu_load()
                    elif tool_name == "check_thermal_enforcement":
                        response["result"] = handle_check_thermal_enforcement()
                    elif tool_name == "list_mesh_ollama_endpoints":
                        response["result"] = handle_list_mesh_ollama_endpoints()
                    else:
                        response["error"] = {
                            "code": -32601,
                            "message": f"Method not found: {tool_name}"
                        }
                except Exception as ex:
                    tb = traceback.format_exc()
                    log(f"Error executing tool {tool_name}: {ex}\n{tb}")
                    response["result"] = {"content": [{"type": "text", "text": f"Internal tool execution failure: {ex}"}], "isError": True}
            else:
                response["error"] = {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }

            original_stdout.write(json.dumps(response) + "\n")
            original_stdout.flush()

        except Exception as e:
            tb = traceback.format_exc()
            log(f"Global loop error: {e}\n{tb}")
            break

if __name__ == "__main__":
    main()
