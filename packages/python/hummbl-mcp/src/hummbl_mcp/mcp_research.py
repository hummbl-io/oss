"""Research Intelligence MCP Server -- expose research findings via JSON-RPC.

Stdio-based JSON-RPC 2.0 MCP server providing search, listing, and reading
of research documents, ADRs, evidence files, and daily briefings.

MCP spec: https://spec.modelcontextprotocol.io/ (2024-11-05)

Stdlib-only: no third-party dependencies.

Usage:
    python -m hummbl_mcp.mcp_research
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

RESEARCH_DIR = _REPO_ROOT / "hummbl_mcp" / "docs" / "research"
EVIDENCE_DIR = RESEARCH_DIR / "evidence"
ADR_DIR = RESEARCH_DIR / "hummbl_mcp_adrs"
BRIEFINGS_DIR = _REPO_ROOT / "hummbl_mcp" / "state" / "briefings"

# Categories map directory prefixes / patterns to category labels
_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "adr": [],       # ADR files live in their own directory
    "evidence": [],  # Evidence files live in their own directory
    "landscape": ["landscape", "competitive", "ecosystem", "market"],
    "spec": ["spec", "prd", "technical_spec"],
    "audit": ["audit", "reconciliation", "assessment"],
}

# ---------------------------------------------------------------------------
# Server info
# ---------------------------------------------------------------------------

SERVER_NAME = "research-intelligence"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "research_search",
        "description": (
            "Search research documents by query. Ranks results by: "
            "exact filename match > title match > content match."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "research_list",
        "description": (
            "List research documents, optionally filtered by category. "
            "Categories: adr, evidence, landscape, spec, audit, all."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["adr", "evidence", "landscape", "spec", "audit", "all"],
                    "default": "all",
                    "description": "Filter by document category",
                },
            },
        },
    },
    {
        "name": "research_read",
        "description": "Read a research document. Returns first 2000 chars plus metadata.",
        "inputSchema": {
            "type": "object",
            "required": ["filename"],
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename (not full path) of the research document",
                },
            },
        },
    },
    {
        "name": "adr_status",
        "description": "List all Architecture Decision Records with ID, title, status, and date.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "briefing_latest",
        "description": "Get the most recent daily briefings with preview content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of recent briefings to return",
                    "default": 3,
                },
            },
        },
    },
    {
        "name": "evidence_list",
        "description": "List all files in the evidence directory with dates and sizes.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _file_meta(path: Path) -> dict[str, Any]:
    """Extract metadata from a file path."""
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    return {
        "filename": path.name,
        "size_bytes": stat.st_size,
        "modified_utc": mtime.isoformat(),
    }


def _extract_title(path: Path) -> str:
    """Extract title from a markdown file (first # heading or filename)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                # Skip empty lines at top
                if line and not line.startswith("---"):
                    break
    except OSError:
        pass
    return path.stem.replace("_", " ").replace("-", " ").title()


def _classify_category(path: Path) -> str:
    """Classify a research file into a category."""
    if path.parent == ADR_DIR or path.parent.name == "hummbl_mcp_adrs":
        return "adr"
    if path.parent == EVIDENCE_DIR or path.parent.name == "evidence":
        return "evidence"
    name_lower = path.name.lower()
    for category, patterns in _CATEGORY_PATTERNS.items():
        if category in ("adr", "evidence"):
            continue
        for pattern in patterns:
            if pattern in name_lower:
                return category
    return "research"


def _collect_research_files(category: str = "all") -> list[Path]:
    """Collect research files, optionally filtered by category."""
    files: list[Path] = []

    if category in ("all", "adr"):
        if ADR_DIR.is_dir():
            files.extend(sorted(ADR_DIR.glob("*.md")))

    if category in ("all", "evidence"):
        if EVIDENCE_DIR.is_dir():
            files.extend(sorted(EVIDENCE_DIR.glob("*")))

    if category == "all":
        # Add top-level research files
        if RESEARCH_DIR.is_dir():
            files.extend(sorted(RESEARCH_DIR.glob("*.md")))
    elif category not in ("adr", "evidence"):
        # Filter top-level by category patterns
        if RESEARCH_DIR.is_dir():
            patterns = _CATEGORY_PATTERNS.get(category, [])
            for f in sorted(RESEARCH_DIR.glob("*.md")):
                name_lower = f.name.lower()
                if any(p in name_lower for p in patterns):
                    files.append(f)

    return files


def _find_file(filename: str) -> Path | None:
    """Find a research file by name across all research directories."""
    # Direct match in research dir
    candidate = RESEARCH_DIR / filename
    if candidate.is_file():
        return candidate

    # ADR dir
    candidate = ADR_DIR / filename
    if candidate.is_file():
        return candidate

    # Evidence dir
    candidate = EVIDENCE_DIR / filename
    if candidate.is_file():
        return candidate

    # Briefings dir
    candidate = BRIEFINGS_DIR / filename
    if candidate.is_file():
        return candidate

    # Fuzzy: search all subdirs
    for d in (RESEARCH_DIR, ADR_DIR, EVIDENCE_DIR, BRIEFINGS_DIR):
        if d.is_dir():
            for f in d.rglob("*"):
                if f.name == filename and f.is_file():
                    return f

    return None


def _search_files(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search research files ranked by relevance.

    Ranking tiers:
        3 = exact filename match
        2 = title/heading match
        1 = content match
    """
    query_lower = query.lower()
    query_terms = re.split(r"\s+", query_lower)
    results: list[tuple[int, str, Path]] = []

    all_files = _collect_research_files("all")
    # Also include briefings in search
    if BRIEFINGS_DIR.is_dir():
        all_files.extend(sorted(BRIEFINGS_DIR.glob("*.md")))

    seen: set[str] = set()
    for path in all_files:
        if not path.is_file():
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)

        score = 0
        name_lower = path.name.lower()

        # Tier 3: exact filename match
        if query_lower in name_lower:
            score = 3
        else:
            # Tier 2: title match
            title = _extract_title(path)
            if query_lower in title.lower():
                score = 2
            else:
                # Check if all query terms appear in title
                if all(t in title.lower() for t in query_terms):
                    score = 2

        # Tier 1: content grep (only if no higher match yet)
        if score == 0:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    # Read up to 50KB for search
                    content = f.read(51200).lower()
                if query_lower in content or all(t in content for t in query_terms):
                    score = 1
            except OSError:
                continue

        if score > 0:
            results.append((score, path.name, path))

    # Sort by score descending, then filename alphabetically
    results.sort(key=lambda r: (-r[0], r[1]))

    output = []
    for score, _name, path in results[:limit]:
        tier = {3: "filename_match", 2: "title_match", 1: "content_match"}
        meta = _file_meta(path)
        meta["match_type"] = tier.get(score, "content_match")
        meta["title"] = _extract_title(path)
        meta["category"] = _classify_category(path)
        output.append(meta)

    return output


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def handle_research_search(args: dict[str, Any]) -> dict[str, Any]:
    """Search research documents by query."""
    query = args.get("query", "")
    if not query or not query.strip():
        return _error_result("Query parameter is required and must be non-empty")
    limit = args.get("limit", 10)
    if not isinstance(limit, int) or limit < 1:
        limit = 10
    results = _search_files(query.strip(), limit)
    return _ok_result({
        "query": query.strip(),
        "count": len(results),
        "results": results,
    })


def handle_research_list(args: dict[str, Any]) -> dict[str, Any]:
    """List research documents by category."""
    category = args.get("category", "all")
    if category not in ("adr", "evidence", "landscape", "spec", "audit", "all"):
        return _error_result(
            f"Invalid category: {category}. "
            "Must be one of: adr, evidence, landscape, spec, audit, all"
        )
    files = _collect_research_files(category)
    docs = []
    for path in files:
        if not path.is_file():
            continue
        meta = _file_meta(path)
        meta["title"] = _extract_title(path)
        meta["category"] = _classify_category(path)
        docs.append(meta)

    return _ok_result({
        "category": category,
        "count": len(docs),
        "documents": docs,
    })


def handle_research_read(args: dict[str, Any]) -> dict[str, Any]:
    """Read a research document with metadata."""
    filename = args.get("filename", "")
    if not filename or not filename.strip():
        return _error_result("Filename parameter is required")

    path = _find_file(filename.strip())
    if path is None:
        return _error_result(f"File not found: {filename}")

    meta = _file_meta(path)
    meta["title"] = _extract_title(path)
    meta["category"] = _classify_category(path)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(2000)
    except OSError as e:
        return _error_result(f"Error reading file: {e}")

    truncated = meta["size_bytes"] > 2000
    return _ok_result({
        "metadata": meta,
        "content": content,
        "truncated": truncated,
        "chars_returned": len(content),
    })


def handle_adr_status(args: dict[str, Any]) -> dict[str, Any]:
    """List all ADRs with extracted status information."""
    if not ADR_DIR.is_dir():
        return _ok_result({"count": 0, "adrs": [], "note": "ADR directory not found"})

    adrs = []
    for path in sorted(ADR_DIR.glob("*.md")):
        if not path.is_file():
            continue

        adr_id = ""
        title = ""
        status = "Unknown"
        date = ""

        # Parse ADR header fields
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        header = line[2:].strip()
                        # Parse "ADR-FM-001: Title" format
                        if ":" in header:
                            parts = header.split(":", 1)
                            adr_id = parts[0].strip()
                            title = parts[1].strip()
                        else:
                            title = header
                            # Try to get ID from filename
                            match = re.match(r"(ADR-FM-\d+)", path.stem)
                            if match:
                                adr_id = match.group(1)
                    elif line.lower().startswith("status:"):
                        status = line.split(":", 1)[1].strip()
                    elif line.lower().startswith("date:"):
                        date = line.split(":", 1)[1].strip()

                    # Stop after reading the header block
                    if line.startswith("## ") and not line.startswith("# "):
                        break
        except OSError:
            continue

        if not adr_id:
            match = re.match(r"(ADR-FM-\d+)", path.stem)
            adr_id = match.group(1) if match else path.stem

        adrs.append({
            "id": adr_id,
            "title": title or path.stem,
            "status": status,
            "date": date,
            "filename": path.name,
        })

    return _ok_result({"count": len(adrs), "adrs": adrs})


def handle_briefing_latest(args: dict[str, Any]) -> dict[str, Any]:
    """Return the most recent briefings with preview content."""
    count = args.get("count", 3)
    if not isinstance(count, int) or count < 1:
        count = 3

    if not BRIEFINGS_DIR.is_dir():
        return _ok_result({
            "count": 0,
            "briefings": [],
            "note": "Briefings directory not found",
        })

    # Get all briefing files sorted by name descending (date-named files)
    files = sorted(BRIEFINGS_DIR.glob("*.md"), reverse=True)

    briefings = []
    for path in files[:count]:
        if not path.is_file():
            continue
        meta = _file_meta(path)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                preview = f.read(500)
        except OSError:
            preview = "(error reading file)"
        meta["preview"] = preview
        meta["title"] = _extract_title(path)
        briefings.append(meta)

    return _ok_result({"count": len(briefings), "briefings": briefings})


def handle_evidence_list(args: dict[str, Any]) -> dict[str, Any]:
    """List all files in the evidence directory."""
    if not EVIDENCE_DIR.is_dir():
        return _ok_result({
            "count": 0,
            "files": [],
            "note": "Evidence directory not found",
        })

    files = []
    for path in sorted(EVIDENCE_DIR.iterdir()):
        if not path.is_file():
            continue
        meta = _file_meta(path)
        meta["title"] = _extract_title(path) if path.suffix == ".md" else path.name
        files.append(meta)

    return _ok_result({"count": len(files), "files": files})


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 result helpers
# ---------------------------------------------------------------------------


def _ok_result(data: Any) -> dict[str, Any]:
    """Wrap data in MCP tool result format."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(data, indent=2, default=str),
            }
        ],
        "isError": False,
    }


def _error_result(message: str) -> dict[str, Any]:
    """Wrap error in MCP tool result format."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"error": message}),
            }
        ],
        "isError": True,
    }


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 MCP Server (stdio transport)
# ---------------------------------------------------------------------------

_TOOL_HANDLERS = {
    "research_search": handle_research_search,
    "research_list": handle_research_list,
    "research_read": handle_research_read,
    "adr_status": handle_adr_status,
    "briefing_latest": handle_briefing_latest,
    "evidence_list": handle_evidence_list,
}


class ResearchMCPServer:
    """Stdio JSON-RPC 2.0 MCP server for research intelligence."""

    def __init__(
        self,
        research_dir: Path | None = None,
        evidence_dir: Path | None = None,
        adr_dir: Path | None = None,
        briefings_dir: Path | None = None,
    ) -> None:
        # Allow override for testing
        global RESEARCH_DIR, EVIDENCE_DIR, ADR_DIR, BRIEFINGS_DIR
        if research_dir is not None:
            RESEARCH_DIR = research_dir
        if evidence_dir is not None:
            EVIDENCE_DIR = evidence_dir
        if adr_dir is not None:
            ADR_DIR = adr_dir
        if briefings_dir is not None:
            BRIEFINGS_DIR = briefings_dir

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC 2.0 message and return a response."""
        jsonrpc = message.get("jsonrpc", "")
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        # Notifications (no id) -- no response required
        if msg_id is None and method == "notifications/initialized":
            logger.debug("Client initialized")
            return None

        if jsonrpc != "2.0":
            return self._rpc_error(msg_id, -32600, "Invalid Request: jsonrpc must be '2.0'")

        if method == "initialize":
            return self._handle_initialize(msg_id, params)
        elif method == "tools/list":
            return self._handle_tools_list(msg_id)
        elif method == "tools/call":
            return self._handle_tools_call(msg_id, params)
        elif method == "ping":
            return self._rpc_result(msg_id, {})
        else:
            return self._rpc_error(msg_id, -32601, f"Method not found: {method}")

    def _handle_initialize(
        self, msg_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle MCP initialize handshake."""
        return self._rpc_result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        })

    def _handle_tools_list(self, msg_id: Any) -> dict[str, Any]:
        """Return available tools."""
        return self._rpc_result(msg_id, {"tools": MCP_TOOLS})

    def _handle_tools_call(
        self, msg_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch a tool call to the appropriate handler."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = _TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return self._rpc_result(msg_id, _error_result(
                f"Unknown tool: {tool_name}. "
                f"Available: {', '.join(_TOOL_HANDLERS.keys())}"
            ))

        try:
            result = handler(arguments)
            return self._rpc_result(msg_id, result)
        except Exception as e:
            logger.exception("Tool call error: %s", tool_name)
            return self._rpc_result(msg_id, _error_result(f"Internal error: {e}"))

    @staticmethod
    def _rpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
        """Build a JSON-RPC 2.0 success response."""
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _rpc_error(
        msg_id: Any, code: int, message: str
    ) -> dict[str, Any]:
        """Build a JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }

    def run_stdio(self) -> None:
        """Run the server on stdin/stdout, reading newline-delimited JSON-RPC."""
        logger.info("Research Intelligence MCP server starting (stdio)")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError as e:
                error_resp = self._rpc_error(None, -32700, f"Parse error: {e}")
                sys.stdout.write(json.dumps(error_resp) + "\n")
                sys.stdout.flush()
                continue

            response = self.handle_message(message)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for ``python -m hummbl_mcp.mcp_research``."""
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "WARNING"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,  # Logs go to stderr, JSON-RPC goes to stdout
    )
    server = ResearchMCPServer()
    server.run_stdio()


if __name__ == "__main__":  # pragma: no cover
    main()
