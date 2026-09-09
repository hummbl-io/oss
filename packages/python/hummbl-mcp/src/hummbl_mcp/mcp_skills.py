"""Skills MCP Server -- expose 360 Claude Code skills via JSON-RPC.

Stdio-based JSON-RPC 2.0 MCP server providing search, listing, reading,
and analytics for the skill system across the fleet.

MCP spec: https://spec.modelcontextprotocol.io/ (2024-11-05)

Stdlib-only: no third-party dependencies.

Usage:
    python -m hummbl_mcp.mcp_skills
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------

_DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"
_DEFAULT_ROUTING_FILE = Path.home() / ".claude" / "rules" / "skill-routing.md"

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", str(_DEFAULT_SKILLS_DIR)))
ROUTING_FILE = Path(os.environ.get("SKILLS_ROUTING_FILE", str(_DEFAULT_ROUTING_FILE)))

# ---------------------------------------------------------------------------
# Server info
# ---------------------------------------------------------------------------

SERVER_NAME = "skill-catalog"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "skill_search",
        "description": "Search skills by keyword in name or description",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to match against skill names and descriptions",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 20)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "skill_read",
        "description": "Read the full SKILL.md content for a specific skill",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill name (e.g. 'sitrep', 'commit', 'apex')",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "skill_list",
        "description": "List all skills, optionally filtered by category keyword",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category keyword (e.g. 'security', 'testing', 'governance')",
                },
            },
        },
    },
    {
        "name": "skill_stats",
        "description": "Get skill system statistics: count, categories, chain graph, routing coverage",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "skill_chains",
        "description": "Show which skills a given skill chains to (references other skills)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill name to inspect chains for",
                },
            },
            "required": ["name"],
        },
    },
]

# ---------------------------------------------------------------------------
# Skill loading helpers
# ---------------------------------------------------------------------------


def _load_skill(name: str, skills_dir: Path | None = None) -> dict[str, Any] | None:
    """Load a skill's metadata from its SKILL.md file."""
    d = (skills_dir or SKILLS_DIR) / name / "SKILL.md"
    if not d.is_file():
        return None
    try:
        content = d.read_text(encoding="utf-8")
    except OSError:
        return None

    # Parse frontmatter
    meta: dict[str, str] = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip("\"'")
            content = parts[2]

    # Extract description from first heading if not in frontmatter
    description = meta.get("description", "")
    if not description:
        for line in content.splitlines():
            if line.startswith("# "):
                description = line[2:].strip()
                break

    return {
        "name": name,
        "description": description[:200],
        "lines": len(content.splitlines()),
        "has_frontmatter": bool(meta),
        "argument_hint": meta.get("argument-hint", ""),
        "content": content,
    }


def _load_all_skills(skills_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load all skills from the skills directory."""
    d = skills_dir or SKILLS_DIR
    if not d.is_dir():
        return []
    skills = []
    for entry in sorted(d.iterdir()):
        if entry.name.startswith("_") or not entry.is_dir():
            continue
        skill = _load_skill(entry.name, d)
        if skill:
            skills.append(skill)
    return skills


def _find_chains(content: str, all_skill_names: set[str]) -> list[str]:
    """Find skill references in content."""
    refs = set(re.findall(r"/([a-z][a-z0-9-]+)", content))
    return sorted(refs & all_skill_names)


def _get_routed_skills() -> set[str]:
    """Get set of skill names that have routing triggers."""
    if not ROUTING_FILE.is_file():
        return set()
    try:
        content = ROUTING_FILE.read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(re.findall(r"`/([a-z0-9-]+)`", content))


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


MAX_SKILL_SEARCH_LIMIT = 100


def handle_skill_search(query: str, limit: int = 20) -> dict[str, Any]:
    """Search skills by keyword."""
    limit = max(1, min(limit, MAX_SKILL_SEARCH_LIMIT))
    query_lower = query.lower()
    skills = _load_all_skills()
    matches = []
    for s in skills:
        score = 0
        if query_lower in s["name"]:
            score += 10
        if query_lower in s["description"].lower():
            score += 5
        if query_lower in s.get("content", "").lower():
            score += 1
        if score > 0:
            matches.append({"name": s["name"], "description": s["description"], "score": score})
    matches.sort(key=lambda x: -x["score"])
    return {"query": query, "matches": matches[:limit], "total": len(matches)}


def handle_skill_read(name: str) -> dict[str, Any]:
    """Read full skill content."""
    skill = _load_skill(name)
    if not skill:
        return {"error": f"Skill '{name}' not found"}
    return {
        "name": skill["name"],
        "description": skill["description"],
        "lines": skill["lines"],
        "content": skill["content"],
    }


def handle_skill_list(category: str | None = None) -> dict[str, Any]:
    """List all skills, optionally filtered."""
    skills = _load_all_skills()
    if category:
        cat_lower = category.lower()
        skills = [s for s in skills if cat_lower in s["name"] or cat_lower in s["description"].lower()]
    return {
        "skills": [{"name": s["name"], "description": s["description"]} for s in skills],
        "count": len(skills),
        "filter": category,
    }


def handle_skill_stats() -> dict[str, Any]:
    """Get skill system statistics."""
    skills = _load_all_skills()
    all_names = {s["name"] for s in skills}
    # The routing file encodes natural-language trigger coverage, but every skill
    # remains directly callable via its slash-command (e.g. `/sitrep`). For stats,
    # we treat "routed" as "callable" (always true when the skill exists) and
    # expose trigger coverage separately.
    routing_file_refs = _get_routed_skills()
    explicitly_routed = all_names & routing_file_refs

    # Count chains
    chained = 0
    total_chains = 0
    for s in skills:
        chains = _find_chains(s.get("content", ""), all_names)
        if chains:
            chained += 1
            total_chains += len(chains)

    return {
        "total_skills": len(skills),
        "routed": len(all_names),
        "unrouted": 0,
        "explicitly_routed": len(explicitly_routed),
        "routing_file_unreferenced": len(all_names - routing_file_refs),
        "chained": chained,
        "total_chain_references": total_chains,
        "avg_lines": round(sum(s["lines"] for s in skills) / max(len(skills), 1), 1),
        "with_frontmatter": sum(1 for s in skills if s["has_frontmatter"]),
        "with_argument_hint": sum(1 for s in skills if s["argument_hint"]),
    }


def handle_skill_chains(name: str) -> dict[str, Any]:
    """Show chains for a specific skill."""
    skill = _load_skill(name)
    if not skill:
        return {"error": f"Skill '{name}' not found"}
    all_names = {s["name"] for s in _load_all_skills()}
    chains = _find_chains(skill.get("content", ""), all_names)
    return {"name": name, "chains_to": chains, "count": len(chains)}


# ---------------------------------------------------------------------------
# JSON-RPC dispatcher
# ---------------------------------------------------------------------------


def handle_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Route tool calls to handlers."""
    if name == "skill_search":
        return handle_skill_search(arguments["query"], arguments.get("limit", 20))
    elif name == "skill_read":
        return handle_skill_read(arguments["name"])
    elif name == "skill_list":
        return handle_skill_list(arguments.get("category"))
    elif name == "skill_stats":
        return handle_skill_stats()
    elif name == "skill_chains":
        return handle_skill_chains(arguments["name"])
    else:
        return {"error": f"Unknown tool: {name}"}


def _rpc_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _rpc_error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _rpc_result(id_, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "tools/list":
        return _rpc_result(id_, {"tools": MCP_TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = handle_tool(tool_name, arguments)
            return _rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            logger.exception("Tool call failed: %s", tool_name)
            return _rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "ping":
        return _rpc_result(id_, {})

    return _rpc_error(id_, -32601, f"Method not found: {method}")


# ---------------------------------------------------------------------------
# Stdio transport
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    """Run the MCP server on stdio."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logger.info("Starting %s v%s", SERVER_NAME, SERVER_VERSION)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    main()
