#!/usr/bin/env python3
"""Dynamic schema registry server (mock).

A stdlib-only HTTP server that serves schema files and a manifest.
Not production-ready — for testing and development only.

Usage:
    python scripts/dynamic_registry.py
    python scripts/dynamic_registry.py --port 8080 --schemas-dir /path/to/schemas

Endpoints:
    GET /registry/manifest           — list all schemas
    GET /registry/schemas/{id}       — get a specific schema
    GET /registry/schemas/{id}/versions — list versions (mock: single version)
    GET /registry/search?q=...       — search schemas by title or tuple_type

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMAS_DIR = REPO_ROOT / "schemas"


def load_schemas(schemas_dir: Path) -> dict[str, dict]:
    """Load all schema files from a directory."""
    schemas = {}
    for p in sorted(schemas_dir.glob("*.schema.json")):
        with p.open("r", encoding="utf-8") as f:
            schemas[p.name] = json.load(f)
    return schemas


def generate_manifest(schemas: dict[str, dict]) -> dict:
    """Generate a manifest from loaded schemas."""
    schema_list = []
    for name, schema in schemas.items():
        props = schema.get("properties", {})
        tuple_type = None
        tt_schema = props.get("tuple_type", {})
        if isinstance(tt_schema, dict):
            tuple_type = tt_schema.get("const")
        schema_list.append(
            {
                "schema_id": name,
                "url": schema.get("$id", ""),
                "title": schema.get("title", ""),
                "tuple_type": tuple_type,
            }
        )
    return {
        "registry_version": "0.1.0",
        "schema_count": len(schema_list),
        "schemas": schema_list,
    }


class RegistryHandler(BaseHTTPRequestHandler):
    schemas: dict[str, dict] = {}
    manifest: dict = {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/registry/manifest":
            self._json_response(200, self.manifest)
        elif path.startswith("/registry/schemas/"):
            parts = path.split("/")
            if len(parts) >= 4:
                schema_id = parts[3]
                if len(parts) >= 5 and parts[4] == "versions":
                    # Mock: single version
                    if schema_id in self.schemas:
                        self._json_response(200, {"schema_id": schema_id, "versions": ["latest"]})
                    else:
                        self._json_response(404, {"error": "Schema not found"})
                elif schema_id in self.schemas:
                    self._json_response(200, self.schemas[schema_id])
                else:
                    self._json_response(404, {"error": "Schema not found"})
            else:
                self._json_response(404, {"error": "Invalid path"})
        elif path == "/registry/search":
            q = query.get("q", [""])[0].lower()
            results = [
                s
                for s in self.manifest["schemas"]
                if q in s.get("title", "").lower() or q in str(s.get("tuple_type", "")).lower()
            ]
            self._json_response(200, {"query": q, "results": results})
        else:
            self._json_response(404, {"error": "Not found"})

    def _json_response(self, status: int, data: dict):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[registry] {args[0]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9099, help="Port to listen on")
    parser.add_argument(
        "--schemas-dir", default=str(DEFAULT_SCHEMAS_DIR), help="Directory containing schema files"
    )
    args = parser.parse_args(argv)

    schemas = load_schemas(Path(args.schemas_dir))
    manifest = generate_manifest(schemas)

    RegistryHandler.schemas = schemas
    RegistryHandler.manifest = manifest

    server = HTTPServer(("localhost", args.port), RegistryHandler)
    print(f"Schema registry server running on http://localhost:{args.port}")
    print(f"Loaded {len(schemas)} schemas")
    print("Endpoints:")
    print("  GET /registry/manifest")
    print("  GET /registry/schemas/{id}")
    print("  GET /registry/schemas/{id}/versions")
    print("  GET /registry/search?q=...")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
