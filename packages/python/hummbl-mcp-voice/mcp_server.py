#!/usr/bin/env python3
import json
import sys
import os
import urllib.request
import urllib.error
import traceback

SERVER_NAME = "hummbl-mcp-voice"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


def get_api_key():
    key = os.environ.get("VAPI_PRIVATE_API_KEY")
    if not key:
        raise ValueError("VAPI_PRIVATE_API_KEY environment variable is missing")
    return key


def tool_voice_dispatch_call(args: dict) -> dict:
    """
    Initiates an outbound phone call via the voice infrastructure (Vapi).
    """
    phone_number = args.get("phone_number")
    assistant_id = args.get("assistant_id")

    if not phone_number or not assistant_id:
        raise ValueError("phone_number and assistant_id are required")

    api_key = get_api_key()
    url = "https://api.vapi.ai/call"

    payload = json.dumps(
        {"phoneNumberId": phone_number, "assistantId": assistant_id}
    ).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Outbound call successfully queued. Call ID: {response_data.get('id')}",
                    }
                ]
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Voice dispatch failed ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"Voice dispatch request failed: {str(e)}")


def tool_voice_retrieve_call_logs(args: dict) -> dict:
    """
    Downloads structured JSONL call logs for a specific call.
    """
    call_id = args.get("call_id")
    output_path = args.get("output_path", f"call_logs_{call_id}.jsonl.gz")

    if not call_id:
        raise ValueError("call_id is required")

    api_key = get_api_key()
    url = f"https://api.vapi.ai/call/{call_id}/call-logs"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        # urllib follows 302 redirects by default
        with urllib.request.urlopen(req) as response, open(output_path, "wb") as f_out:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f_out.write(chunk)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully retrieved call logs for {call_id} and saved to {output_path}.",
                }
            ]
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Logs not found for call {call_id}. Ensure call has completed.",
                    }
                ]
            }
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Failed to fetch call logs ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"Log retrieval failed: {str(e)}")


def tool_voice_download_recording(args: dict) -> dict:
    """
    Downloads the audio recording for a specific call.
    """
    call_id = args.get("call_id")
    recording_type = args.get("recording_type", "stereo-recording")
    output_path = args.get("output_path", f"recording_{call_id}.wav")

    if not call_id:
        raise ValueError("call_id is required")

    valid_types = [
        "mono-recording",
        "stereo-recording",
        "customer-recording",
        "assistant-recording",
    ]
    if recording_type not in valid_types:
        raise ValueError(f"recording_type must be one of: {', '.join(valid_types)}")

    api_key = get_api_key()
    url = f"https://api.vapi.ai/call/{call_id}/{recording_type}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req) as response, open(output_path, "wb") as f_out:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f_out.write(chunk)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully downloaded {recording_type} for {call_id} to {output_path}.",
                }
            ]
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Recording not found for call {call_id}. It may still be processing.",
                    }
                ]
            }
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Failed to fetch recording ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"Recording retrieval failed: {str(e)}")


def handle_request(request: dict) -> dict:
    req_id = request.get("id")
    method = request.get("method")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "voice_dispatch_call",
                        "description": "Initiate an outbound voice call.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "phone_number": {
                                    "type": "string",
                                    "description": "The target phone number to call (E.164 format)",
                                },
                                "assistant_id": {
                                    "type": "string",
                                    "description": "The ID of the Voice Assistant configuration to use",
                                },
                            },
                            "required": ["phone_number", "assistant_id"],
                        },
                    },
                    {
                        "name": "voice_retrieve_call_logs",
                        "description": "Download structured JSONL call logs for a specific call ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "call_id": {
                                    "type": "string",
                                    "description": "The unique Call ID",
                                },
                                "output_path": {
                                    "type": "string",
                                    "description": "The local file path to save the logs to (defaults to call_logs_<id>.jsonl.gz)",
                                },
                            },
                            "required": ["call_id"],
                        },
                    },
                    {
                        "name": "voice_download_recording",
                        "description": "Download the audio recording for a specific call ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "call_id": {
                                    "type": "string",
                                    "description": "The unique Call ID",
                                },
                                "recording_type": {
                                    "type": "string",
                                    "enum": [
                                        "mono-recording",
                                        "stereo-recording",
                                        "customer-recording",
                                        "assistant-recording",
                                    ],
                                    "description": "The type of recording to fetch",
                                },
                                "output_path": {
                                    "type": "string",
                                    "description": "The local file path to save the WAV/MP3 to",
                                },
                            },
                            "required": ["call_id"],
                        },
                    },
                ]
            },
        }
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            if tool_name == "voice_dispatch_call":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_voice_dispatch_call(args),
                }
            elif tool_name == "voice_retrieve_call_logs":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_voice_retrieve_call_logs(args),
                }
            elif tool_name == "voice_download_recording":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": tool_voice_download_recording(args),
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}",
                    },
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"error": str(e), "traceback": traceback.format_exc()}
                            ),
                        }
                    ]
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            sys.stdout.write(json.dumps(res) + "\\n")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()
