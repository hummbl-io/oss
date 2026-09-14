"""GCP tool surface for HUMMBL MCP.

Strategy: shell out to `gcloud` and `gsutil` CLIs rather than depend on
google-cloud-* Python libs. Keeps us stdlib-only and lets the CLI handle
auth (service account key via GOOGLE_APPLICATION_CREDENTIALS env var).

Tools v1 scope (broad, read + write):
  - gcp_run_list:        list Cloud Run services
  - gcp_run_describe:    describe a Cloud Run service
  - gcp_run_logs_tail:   tail logs for a Cloud Run service
  - gcp_run_deploy:      trigger a deploy (from image URL)
  - gcp_build_list:      list recent Cloud Build runs
  - gcp_build_describe:  describe a specific build
  - gcp_build_trigger:   submit a new Cloud Build
  - gcp_storage_list:    list objects in a bucket
  - gcp_storage_read:    read an object's content (text only, size-capped)
  - gcp_storage_write:   write a small text object
  - gcp_logging_query:   run a Cloud Logging filter query
  - gcp_iam_list:        list IAM bindings on the project

Configuration env vars:
  GCP_PROJECT                       default project id (defaults to hummbl-prod)
  GOOGLE_APPLICATION_CREDENTIALS    path to SA key JSON (for gcloud auth)
  GCP_MAX_READ_BYTES                cap for gcp_storage_read (default 1 MB)
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from hummbl_mcp.protocol import JsonRpcError, TOOL_EXECUTION_ERROR, ToolDefinition


DEFAULT_PROJECT = os.environ.get("GCP_PROJECT", "hummbl-prod")
DEFAULT_MAX_READ_BYTES = int(os.environ.get("GCP_MAX_READ_BYTES", str(1024 * 1024)))


def _project(params: dict[str, Any]) -> str:
    return params.get("project") or DEFAULT_PROJECT


def _run_cmd(cmd: list[str], *, input_bytes: bytes | None = None, timeout: int = 60) -> str:
    """Run a subprocess, capture stdout, raise JsonRpcError on failure.

    Never shell=True. All args are pre-split.
    """
    try:
        proc = subprocess.run(
            cmd,
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as e:
        raise JsonRpcError(TOOL_EXECUTION_ERROR, f"command not found: {cmd[0]}", data=str(e))
    except subprocess.TimeoutExpired:
        raise JsonRpcError(TOOL_EXECUTION_ERROR, f"command timed out after {timeout}s: {' '.join(cmd[:3])}")

    if proc.returncode != 0:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        msg = stderr or stdout or f"exit {proc.returncode}"
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            f"gcloud error: {msg[:500]}",
            data={"cmd": cmd[:3], "returncode": proc.returncode},
        )
    return (proc.stdout or b"").decode("utf-8", errors="replace")


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise JsonRpcError(TOOL_EXECUTION_ERROR, f"non-JSON output from gcloud: {e}", data=text[:500])


# ---------------------------------------------------------------------------
# Cloud Run
# ---------------------------------------------------------------------------

def gcp_run_list(params: dict[str, Any]) -> Any:
    region = params.get("region", "us-central1")
    out = _run_cmd(["gcloud", "run", "services", "list",
                    "--project", _project(params),
                    "--region", region,
                    "--format", "json"])
    return _parse_json(out)


def gcp_run_describe(params: dict[str, Any]) -> Any:
    service = params["service"]
    region = params.get("region", "us-central1")
    out = _run_cmd(["gcloud", "run", "services", "describe", service,
                    "--project", _project(params),
                    "--region", region,
                    "--format", "json"])
    return _parse_json(out)


def gcp_run_logs_tail(params: dict[str, Any]) -> Any:
    """Returns most recent N log entries for a service. N defaults to 50, max 500."""
    service = params["service"]
    limit = min(int(params.get("limit", 50)), 500)
    log_filter = f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}"'
    out = _run_cmd(["gcloud", "logging", "read", log_filter,
                    "--project", _project(params),
                    "--limit", str(limit),
                    "--format", "json",
                    "--order", "desc"])
    return _parse_json(out)


def gcp_run_deploy(params: dict[str, Any]) -> Any:
    """Deploy a Cloud Run service from a container image URL."""
    service = params["service"]
    image = params["image"]
    region = params.get("region", "us-central1")
    allow_unauth = params.get("allow_unauthenticated", False)

    cmd = ["gcloud", "run", "deploy", service,
           "--image", image,
           "--project", _project(params),
           "--region", region,
           "--format", "json",
           "--quiet"]
    if allow_unauth:
        cmd.append("--allow-unauthenticated")
    else:
        cmd.append("--no-allow-unauthenticated")

    # Deploy can take several minutes
    out = _run_cmd(cmd, timeout=600)
    # Older gcloud versions emit non-JSON progress to stdout before the JSON result.
    # Try to find the last JSON object.
    try:
        return _parse_json(out)
    except JsonRpcError:
        # Find the JSON object in the output
        brace_start = out.find("{")
        if brace_start != -1:
            return _parse_json(out[brace_start:])
        raise


# ---------------------------------------------------------------------------
# Cloud Build
# ---------------------------------------------------------------------------

def gcp_build_list(params: dict[str, Any]) -> Any:
    limit = min(int(params.get("limit", 20)), 100)
    out = _run_cmd(["gcloud", "builds", "list",
                    "--project", _project(params),
                    "--limit", str(limit),
                    "--format", "json"])
    return _parse_json(out)


def gcp_build_describe(params: dict[str, Any]) -> Any:
    build_id = params["build_id"]
    out = _run_cmd(["gcloud", "builds", "describe", build_id,
                    "--project", _project(params),
                    "--format", "json"])
    return _parse_json(out)


def gcp_build_trigger(params: dict[str, Any]) -> Any:
    """Submit a build from a config file or inline Dockerfile context."""
    source = params["source"]  # path to a dir or tarball
    config = params.get("config")  # optional cloudbuild.yaml path
    cmd = ["gcloud", "builds", "submit", source,
           "--project", _project(params),
           "--format", "json",
           "--quiet"]
    if config:
        cmd.extend(["--config", config])
    out = _run_cmd(cmd, timeout=900)
    return _parse_json(out)


# ---------------------------------------------------------------------------
# Cloud Storage
# ---------------------------------------------------------------------------

def gcp_storage_list(params: dict[str, Any]) -> Any:
    bucket = params["bucket"]
    prefix = params.get("prefix", "")
    limit = min(int(params.get("limit", 100)), 1000)

    uri = f"gs://{bucket}/{prefix}" if prefix else f"gs://{bucket}/"
    out = _run_cmd(["gcloud", "storage", "ls", "--long", "--json", uri,
                    "--project", _project(params),
                    "--limit", str(limit)])
    return _parse_json(out) if out.strip() else []


def gcp_storage_read(params: dict[str, Any]) -> Any:
    bucket = params["bucket"]
    path = params["path"]
    max_bytes = min(int(params.get("max_bytes", DEFAULT_MAX_READ_BYTES)), DEFAULT_MAX_READ_BYTES)
    uri = f"gs://{bucket}/{path}"

    # Check size first
    out = _run_cmd(["gcloud", "storage", "objects", "describe", uri,
                    "--project", _project(params),
                    "--format", "value(size)"])
    try:
        size = int(out.strip())
    except ValueError:
        size = -1
    if size > max_bytes:
        raise JsonRpcError(
            TOOL_EXECUTION_ERROR,
            f"object size {size} exceeds max_bytes {max_bytes}",
            data={"bucket": bucket, "path": path, "size": size},
        )

    # Stream to stdout
    proc = subprocess.run(
        ["gcloud", "storage", "cat", uri, "--project", _project(params)],
        capture_output=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise JsonRpcError(TOOL_EXECUTION_ERROR, f"storage cat failed: {stderr[:500]}")
    # Decode as text; for binary, the caller should set a different tool
    content = proc.stdout.decode("utf-8", errors="replace")
    return {"bucket": bucket, "path": path, "size": size, "content": content}


def gcp_storage_write(params: dict[str, Any]) -> Any:
    """Write a text object. For binary use, pass base64=true and base64-encoded content."""
    bucket = params["bucket"]
    path = params["path"]
    content = params["content"]
    uri = f"gs://{bucket}/{path}"

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content
    proc = subprocess.run(
        ["gcloud", "storage", "cp", "-", uri, "--project", _project(params)],
        input=content_bytes,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise JsonRpcError(TOOL_EXECUTION_ERROR, f"storage cp failed: {stderr[:500]}")
    return {"bucket": bucket, "path": path, "bytes_written": len(content_bytes)}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def gcp_logging_query(params: dict[str, Any]) -> Any:
    log_filter = params["filter"]
    limit = min(int(params.get("limit", 50)), 500)
    out = _run_cmd(["gcloud", "logging", "read", log_filter,
                    "--project", _project(params),
                    "--limit", str(limit),
                    "--format", "json",
                    "--order", params.get("order", "desc")])
    return _parse_json(out) if out.strip() else []


# ---------------------------------------------------------------------------
# IAM (read-only listing)
# ---------------------------------------------------------------------------

def gcp_iam_list(params: dict[str, Any]) -> Any:
    out = _run_cmd(["gcloud", "projects", "get-iam-policy", _project(params),
                    "--format", "json"])
    return _parse_json(out)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

@dataclass
class GcpTool:
    name: str
    description: str
    handler: Any
    input_schema: dict[str, Any]


GCP_TOOLS: list[GcpTool] = [
    GcpTool(
        name="gcp_run_list",
        description="List Cloud Run services in a region.",
        handler=gcp_run_list,
        input_schema={
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "GCP project id (default: hummbl-prod)"},
                "region": {"type": "string", "description": "Region (default: us-central1)"},
            },
        },
    ),
    GcpTool(
        name="gcp_run_describe",
        description="Describe a specific Cloud Run service — URL, revision, traffic, env vars.",
        handler=gcp_run_describe,
        input_schema={
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "project": {"type": "string"},
                "region": {"type": "string"},
            },
            "required": ["service"],
        },
    ),
    GcpTool(
        name="gcp_run_logs_tail",
        description="Return the most recent log entries for a Cloud Run service (limit 1-500, default 50).",
        handler=gcp_run_logs_tail,
        input_schema={
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "project": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "required": ["service"],
        },
    ),
    GcpTool(
        name="gcp_run_deploy",
        description="Deploy a container image to Cloud Run. WRITE operation.",
        handler=gcp_run_deploy,
        input_schema={
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "image": {"type": "string", "description": "Full image URL including registry"},
                "project": {"type": "string"},
                "region": {"type": "string"},
                "allow_unauthenticated": {"type": "boolean"},
            },
            "required": ["service", "image"],
        },
    ),
    GcpTool(
        name="gcp_build_list",
        description="List recent Cloud Build runs (default 20, max 100).",
        handler=gcp_build_list,
        input_schema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
        },
    ),
    GcpTool(
        name="gcp_build_describe",
        description="Describe a specific Cloud Build run by id.",
        handler=gcp_build_describe,
        input_schema={
            "type": "object",
            "properties": {
                "build_id": {"type": "string"},
                "project": {"type": "string"},
            },
            "required": ["build_id"],
        },
    ),
    GcpTool(
        name="gcp_build_trigger",
        description="Submit a Cloud Build from a source directory or tarball. WRITE operation.",
        handler=gcp_build_trigger,
        input_schema={
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Local path or gs:// URL"},
                "config": {"type": "string", "description": "Optional cloudbuild.yaml path"},
                "project": {"type": "string"},
            },
            "required": ["source"],
        },
    ),
    GcpTool(
        name="gcp_storage_list",
        description="List objects in a GCS bucket, optionally filtered by prefix.",
        handler=gcp_storage_list,
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string"},
                "prefix": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
                "project": {"type": "string"},
            },
            "required": ["bucket"],
        },
    ),
    GcpTool(
        name="gcp_storage_read",
        description="Read a text object from GCS. Size-capped (default 1 MB, max 1 MB).",
        handler=gcp_storage_read,
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string"},
                "path": {"type": "string"},
                "max_bytes": {"type": "integer"},
                "project": {"type": "string"},
            },
            "required": ["bucket", "path"],
        },
    ),
    GcpTool(
        name="gcp_storage_write",
        description="Write a small text object to GCS. WRITE operation.",
        handler=gcp_storage_write,
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string"},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "project": {"type": "string"},
            },
            "required": ["bucket", "path", "content"],
        },
    ),
    GcpTool(
        name="gcp_logging_query",
        description="Run a Cloud Logging filter query.",
        handler=gcp_logging_query,
        input_schema={
            "type": "object",
            "properties": {
                "filter": {"type": "string", "description": "Logging filter expression"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                "order": {"type": "string", "enum": ["asc", "desc"]},
                "project": {"type": "string"},
            },
            "required": ["filter"],
        },
    ),
    GcpTool(
        name="gcp_iam_list",
        description="Get IAM policy bindings for the project.",
        handler=gcp_iam_list,
        input_schema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
            },
        },
    ),
]


def get_tool_definitions() -> list[ToolDefinition]:
    return [ToolDefinition(name=t.name, description=t.description, input_schema=t.input_schema) for t in GCP_TOOLS]


def get_handlers() -> dict[str, Any]:
    return {t.name: t.handler for t in GCP_TOOLS}
