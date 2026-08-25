"""LSP Server Registry — Governed catalog of Language Server Protocol servers.

This module provides a registry pattern for LSP servers compatible with
the hummbl-governance architecture. It follows the same registry pattern
as ``compliance_frameworks.py`` with declarative definitions, schema
validation, and optional MCP server exposure.

Each server definition includes:
- Server identifier and metadata
- File extension/language mappings
- Project root detection markers
- Spawn command resolution with auto-install support
- Initialization options
- Health/availability checking

The registry is designed to be:
- Extensible via entry points or programmatic registration
- Validatable against JSON schemas
- Queryable via MCP tools (when mcp_server.py exposes it)
- Auditable with receipts for governance tracking
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..schema_validator import SchemaValidator

logger = logging.getLogger("hummbl_governance.lsp_registry")

# ---------------------------------------------------------------------------
# Language ID mapping (per LSP spec)
# ---------------------------------------------------------------------------

LANGUAGE_BY_EXT: Dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".vue": "vue",
    ".svelte": "svelte",
    ".astro": "astro",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".rake": "ruby",
    ".gemspec": "ruby",
    ".ru": "ruby",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".cs": "csharp",
    ".csx": "csharp",
    ".fs": "fsharp",
    ".fsi": "fsharp",
    ".fsx": "fsharp",
    ".swift": "swift",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".jsonc": "jsonc",
    ".lua": "lua",
    ".php": "php",
    ".prisma": "prisma",
    ".dart": "dart",
    ".ml": "ocaml",
    ".mli": "ocaml",
    ".sh": "shellscript",
    ".bash": "shellscript",
    ".zsh": "shellscript",
    ".tf": "terraform",
    ".tfvars": "terraform",
    ".tex": "latex",
    ".bib": "bibtex",
    ".gleam": "gleam",
    ".clj": "clojure",
    ".cljs": "clojurescript",
    ".cljc": "clojure",
    ".edn": "clojure",
    ".nix": "nix",
    ".typ": "typst",
    ".typc": "typst",
    ".hs": "haskell",
    ".lhs": "haskell",
    ".jl": "julia",
    ".ex": "elixir",
    ".exs": "elixir",
    ".zig": "zig",
    ".zon": "zig",
    ".dockerfile": "dockerfile",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpawnSpec:
    """Resolved spawn specification for an LSP server.

    Returned by :meth:`ServerDef.resolve_spawn` when a server is applicable
    to a file and its binary can be located (or auto-installed).
    """

    command: List[str]
    workspace_root: str
    cwd: str
    env: Dict[str, str] = field(default_factory=dict)
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    seed_diagnostics_on_first_push: bool = False


@dataclass(frozen=True)
class ServerContext:
    """Context passed to spawn resolvers.

    Carries user configuration for auto-install, binary overrides,
    environment overrides, and initialization option overrides.
    """

    workspace_root: str
    install_strategy: str = "auto"  # "auto" | "manual" | "off"
    binary_overrides: Dict[str, List[str]] = field(default_factory=dict)
    env_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)
    init_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerDef:
    """Definition of one Language Server.

    Attributes:
        server_id: Unique identifier for this server (used as registry key).
        extensions: Tuple of file extensions this server handles (e.g., (".py", ".pyi")).
        language_ids: Optional explicit language IDs. If omitted, derived from LANGUAGE_BY_EXT.
        resolve_root: Callable that receives (file_path, workspace_root) and returns
            the project-specific root directory for this server, or None to skip.
        build_spawn: Callable that receives (resolved_root, ServerContext) and returns
            a SpawnSpec, or None if binary unavailable and auto-install disabled.
        description: Human-readable description.
        category: Optional category for grouping (e.g., "core", "community", "experimental").
        min_version: Optional minimum server version requirement.
        tags: Optional tags for filtering (e.g., ["microsoft", "official"]).
    """

    server_id: str
    extensions: Tuple[str, ...]
    language_ids: Tuple[str, ...] = field(default_factory=tuple)
    resolve_root: Callable[[str, str], Optional[str]] = field(default=lambda fp, ws: ws)
    build_spawn: Callable[[str, ServerContext], Optional[SpawnSpec]] = field(
        default=lambda root, ctx: None
    )
    description: str = ""
    category: str = "core"
    min_version: Optional[str] = None
    tags: Tuple[str, ...] = field(default_factory=tuple)
    seed_diagnostics_on_first_push: bool = False

    def matches(self, file_path: str) -> bool:
        """Return True iff this server handles ``file_path``."""
        ext = _file_ext_or_basename(file_path)
        return ext in self.extensions

    def language_id_for(self, file_path: str) -> str:
        """Return the LSP languageId for ``file_path``."""
        if self.language_ids:
            return self.language_ids[0]
        ext = _file_ext_or_basename(file_path)
        return LANGUAGE_BY_EXT.get(ext, "plaintext")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON schema validation / MCP exposure."""
        return {
            "server_id": self.server_id,
            "extensions": list(self.extensions),
            "language_ids": list(self.language_ids),
            "description": self.description,
            "category": self.category,
            "min_version": self.min_version,
            "tags": list(self.tags),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _file_ext_or_basename(path: str) -> str:
    """Return lower-cased extension OR full basename for extensionless files.

    Mirrors OpenCode's ``path.parse(file).ext || file`` — files like
    ``Dockerfile`` or ``Makefile`` match by basename, while normal
    files match by extension (``.py``, ``.ts``).
    """
    base = os.path.basename(path)
    _root, ext = os.path.splitext(base)
    if ext:
        return ext.lower()
    return base


def _which(*names: str) -> Optional[str]:
    """Return the full path of the first command found on PATH."""
    for n in names:
        path = shutil.which(n)
        if path:
            return path
    return None


def _root_or_workspace(
    file_path: str,
    workspace: str,
    markers: Sequence[str],
    excludes: Sequence[str] = (),
) -> Optional[str]:
    """Common pattern: try nearest_root, fall back to workspace root.

    Returns None if an exclude marker matches first (server gated off).
    """
    from .workspace import nearest_root

    found = nearest_root(
        file_path,
        markers,
        excludes=excludes,
        ceiling=os.path.dirname(workspace) if workspace else None,
    )
    if found is None and excludes:
        # Distinguish "no marker found" from "exclude hit"
        recheck = nearest_root(
            file_path,
            markers,
            ceiling=os.path.dirname(workspace) if workspace else None,
        )
        if recheck is not None:
            return None  # exclude triggered
        return workspace
    return found or workspace


def _resolve_override(ctx: ServerContext, server_id: str) -> Optional[str]:
    """User can pin a binary path in config."""
    override = ctx.binary_overrides.get(server_id)
    if override and override[0] and os.path.exists(override[0]):
        return override[0]
    return None


def _get_version(bin_path: str, version_flag: str = "--version") -> Optional[str]:
    """Extract version string from a binary."""
    try:
        result = subprocess.run(
            [bin_path, version_flag],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Workspace utilities (split to avoid circular imports)
# ---------------------------------------------------------------------------


def nearest_root(
    file_path: str,
    markers: Sequence[str],
    excludes: Sequence[str] = (),
    ceiling: Optional[str] = None,
) -> Optional[str]:
    """Find the nearest ancestor directory containing any marker file.

    Args:
        file_path: Starting file path (absolute or relative).
        markers: Filenames or glob patterns to search for.
        excludes: Filenames that, if found first, cause early return of None.
        ceiling: Stop searching at this directory (exclusive).

    Returns:
        Absolute path to the directory containing a marker, or None.
    """
    from pathlib import Path

    path = Path(file_path).resolve()
    if path.is_file():
        path = path.parent

    ceiling_path = Path(ceiling).resolve() if ceiling else None

    for parent in [path] + list(path.parents):
        if ceiling_path and parent == ceiling_path:
            break
        # Check excludes first
        for exc in excludes:
            if (parent / exc).exists():
                return None
        # Check markers
        for marker in markers:
            if (parent / marker).exists():
                return str(parent)
    return None


def resolve_workspace_for_file(file_path: str) -> Tuple[Optional[str], bool]:
    """Resolve the git workspace root for a file.

    Returns:
        Tuple of (workspace_root, gated_in). gated_in is False if
        the file is not inside a git worktree.
    """
    from pathlib import Path

    path = Path(file_path).resolve()
    if path.is_file():
        path = path.parent

    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return str(parent), True
    return None, False


# ---------------------------------------------------------------------------
# Spawn builders (core servers)
# ---------------------------------------------------------------------------


def _spawn_pyright(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "pyright") or _which("pyright-langserver", "pyright")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("pyright", ctx.install_strategy)
        if bin_path is None:
            return None
    # If we got the cli ``pyright``, the langserver is its sibling.
    base = os.path.basename(bin_path)
    if base in ("pyright", "pyright.exe"):
        sibling = os.path.join(os.path.dirname(bin_path), "pyright-langserver")
        if os.path.exists(sibling):
            bin_path = sibling
    init: Dict[str, Any] = {}
    py = _detect_python(root)
    if py:
        init["python"] = {"pythonPath": py}
    if "pyright" in ctx.init_overrides:
        init.update(ctx.init_overrides["pyright"])
    return SpawnSpec(
        command=[bin_path, "--stdio"],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("pyright", {}),
        initialization_options=init,
    )


def _detect_python(root: str) -> Optional[str]:
    candidates = []
    if os.environ.get("VIRTUAL_ENV"):
        candidates.append(os.environ["VIRTUAL_ENV"])
    candidates.extend([os.path.join(root, ".venv"), os.path.join(root, "venv")])
    for v in candidates:
        for sub in ("bin/python", "bin/python3", "Scripts/python.exe"):
            p = os.path.join(v, sub)
            if os.path.exists(p):
                return p
    return None


def _spawn_typescript(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "typescript") or _which("typescript-language-server")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("typescript-language-server", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path, "--stdio"],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("typescript", {}),
        initialization_options=ctx.init_overrides.get("typescript", {}),
        seed_diagnostics_on_first_push=True,
    )


def _spawn_gopls(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "gopls") or _which("gopls")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("gopls", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("gopls", {}),
        initialization_options=ctx.init_overrides.get("gopls", {}),
    )


def _spawn_rust_analyzer(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "rust-analyzer") or _which("rust-analyzer")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("rust-analyzer", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("rust-analyzer", {}),
        initialization_options=ctx.init_overrides.get("rust-analyzer", {}),
    )


def _spawn_clangd(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "clangd") or _which("clangd")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("clangd", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path, "--background-index", "--clang-tidy"],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("clangd", {}),
        initialization_options=ctx.init_overrides.get("clangd", {}),
    )


def _spawn_bash_ls(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "bash-language-server") or _which("bash-language-server")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("bash-language-server", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path, "start"],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("bash-language-server", {}),
        initialization_options=ctx.init_overrides.get("bash-language-server", {}),
    )


def _spawn_yaml_ls(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "yaml-language-server") or _which("yaml-language-server")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("yaml-language-server", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path, "--stdio"],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("yaml-language-server", {}),
        initialization_options=ctx.init_overrides.get("yaml-language-server", {}),
    )


def _spawn_lua_ls(root: str, ctx: ServerContext) -> Optional[SpawnSpec]:
    bin_path = _resolve_override(ctx, "lua-language-server") or _which("lua-language-server")
    if bin_path is None:
        from .install import try_install

        bin_path = try_install("lua-language-server", ctx.install_strategy)
        if bin_path is None:
            return None
    return SpawnSpec(
        command=[bin_path],
        workspace_root=root,
        cwd=root,
        env=ctx.env_overrides.get("lua-language-server", {}),
        initialization_options=ctx.init_overrides.get("lua-language-server", {}),
    )


# ---------------------------------------------------------------------------
# Root resolvers
# ---------------------------------------------------------------------------


def _root_python(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(
        file_path,
        workspace,
        ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "pyrightconfig.json"],
    )


def _root_typescript(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(
        file_path,
        workspace,
        [
            "package-lock.json",
            "bun.lockb",
            "bun.lock",
            "pnpm-lock.yaml",
            "yarn.lock",
            "package.json",
            "tsconfig.json",
        ],
        excludes=["deno.json", "deno.jsonc"],
    )


def _root_go(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(file_path, workspace, ["go.work", "go.mod", "go.sum"])


def _root_rust(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(file_path, workspace, ["Cargo.toml", "Cargo.lock"])


def _root_clangd(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(
        file_path, workspace, ["compile_commands.json", "compile_flags.txt", ".clangd"]
    )


def _root_bash(file_path: str, workspace: str) -> str:
    return workspace


def _root_yaml(file_path: str, workspace: str) -> str:
    return workspace


def _root_lua(file_path: str, workspace: str) -> Optional[str]:
    return _root_or_workspace(
        file_path,
        workspace,
        [
            ".luarc.json",
            ".luarc.jsonc",
            ".luacheckrc",
            ".stylua.toml",
            "stylua.toml",
            "selene.toml",
            "selene.yml",
        ],
    )


# ---------------------------------------------------------------------------
# The Registry
# ---------------------------------------------------------------------------


class LSPRegistry:
    """Registry of Language Server definitions.

    Provides registration, lookup, validation, and enumeration.
    Thread-safe for concurrent reads; registration is expected at
    initialization time (single-threaded).
    """

    def __init__(self) -> None:
        self._servers: Dict[str, ServerDef] = {}
        self._by_extension: Dict[str, List[ServerDef]] = {}
        self._validator = SchemaValidator()

    def register(self, server: ServerDef) -> None:
        """Register a server definition.

        Raises:
            ValueError: If server_id already registered.
        """
        if server.server_id in self._servers:
            raise ValueError(f"Server already registered: {server.server_id}")
        self._servers[server.server_id] = server
        for ext in server.extensions:
            self._by_extension.setdefault(ext, []).append(server)
        logger.debug("Registered LSP server: %s", server.server_id)

    def unregister(self, server_id: str) -> bool:
        """Unregister a server. Returns True if it was present."""
        server = self._servers.pop(server_id, None)
        if server is None:
            return False
        for ext in server.extensions:
            if ext in self._by_extension:
                self._by_extension[ext] = [s for s in self._by_extension[ext] if s.server_id != server_id]
        return True

    def get(self, server_id: str) -> Optional[ServerDef]:
        """Get a server by ID."""
        return self._servers.get(server_id)

    def find_for_file(self, file_path: str) -> Optional[ServerDef]:
        """Return the first server that handles ``file_path``.

        Servers are checked in registration order. For deterministic
        behavior, register more specific servers first.
        """
        ext = _file_ext_or_basename(file_path)
        candidates = self._by_extension.get(ext, [])
        for srv in candidates:
            if srv.matches(file_path):
                return srv
        return None

    def find_all_for_file(self, file_path: str) -> List[ServerDef]:
        """Return all servers that handle ``file_path``."""
        ext = _file_ext_or_basename(file_path)
        return [s for s in self._by_extension.get(ext, []) if s.matches(file_path)]

    def list_servers(
        self,
        *,
        category: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> List[ServerDef]:
        """List servers with optional filtering."""
        result = list(self._servers.values())
        if category:
            result = [s for s in result if s.category == category]
        if tags:
            tag_set = set(tags)
            result = [s for s in result if tag_set.intersection(s.tags)]
        return result

    def all_server_ids(self) -> List[str]:
        return sorted(self._servers.keys())

    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all registered servers against the schema.

        Returns:
            Dict mapping server_id to list of validation errors (empty = valid).
        """
        errors: Dict[str, List[str]] = {}
        for sid, server in self._servers.items():
            server_dict = server.to_dict()
            # Use a lightweight schema for validation
            server_schema = {
                "type": "object",
                "required": ["server_id", "extensions", "description", "category"],
                "properties": {
                    "server_id": {"type": "string"},
                    "extensions": {"type": "array", "items": {"type": "string"}},
                    "language_ids": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                    "category": {"type": "string"},
                    "min_version": {"type": ["string", "null"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            }
            ve = self._validator.validate(server_dict, server_schema)
            if ve:
                errors[sid] = ve
        return errors


# Global registry instance
_REGISTRY = LSPRegistry()


def get_registry() -> LSPRegistry:
    """Return the global LSP registry instance."""
    return _REGISTRY


def register_server(server: ServerDef) -> None:
    """Convenience function to register a server globally."""
    _REGISTRY.register(server)


# ---------------------------------------------------------------------------
# Built-in server definitions
# ---------------------------------------------------------------------------


BUILTIN_SERVERS: List[ServerDef] = [
    ServerDef(
        server_id="pyright",
        extensions=(".py", ".pyi"),
        language_ids=("python",),
        resolve_root=_root_python,
        build_spawn=_spawn_pyright,
        description="Python — Microsoft pyright",
        category="core",
        tags=("microsoft", "official", "type-checking"),
    ),
    ServerDef(
        server_id="typescript",
        extensions=(".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"),
        language_ids=("typescript", "typescriptreact", "javascript", "javascriptreact"),
        resolve_root=_root_typescript,
        build_spawn=_spawn_typescript,
        description="JavaScript/TypeScript — typescript-language-server",
        category="core",
        tags=("microsoft", "official"),
        seed_diagnostics_on_first_push=True,
    ),
    ServerDef(
        server_id="gopls",
        extensions=(".go",),
        language_ids=("go",),
        resolve_root=_root_go,
        build_spawn=_spawn_gopls,
        description="Go — gopls",
        category="core",
        tags=("google", "official"),
    ),
    ServerDef(
        server_id="rust-analyzer",
        extensions=(".rs",),
        language_ids=("rust",),
        resolve_root=_root_rust,
        build_spawn=_spawn_rust_analyzer,
        description="Rust — rust-analyzer",
        category="core",
        tags=("rust-lang", "official"),
    ),
    ServerDef(
        server_id="clangd",
        extensions=(".c", ".cpp", ".cc", ".cxx", ".h", ".hh", ".hpp", ".hxx"),
        language_ids=("c", "cpp"),
        resolve_root=_root_clangd,
        build_spawn=_spawn_clangd,
        description="C/C++ — clangd",
        category="core",
        tags=("llvm", "official"),
    ),
    ServerDef(
        server_id="bash-language-server",
        extensions=(".sh", ".bash", ".zsh", ".ksh"),
        language_ids=("shellscript",),
        resolve_root=_root_bash,
        build_spawn=_spawn_bash_ls,
        description="Bash — bash-language-server",
        category="core",
        tags=("community"),
    ),
    ServerDef(
        server_id="yaml-language-server",
        extensions=(".yaml", ".yml"),
        language_ids=("yaml",),
        resolve_root=_root_yaml,
        build_spawn=_spawn_yaml_ls,
        description="YAML — yaml-language-server",
        category="core",
        tags=("redhat", "official"),
    ),
    ServerDef(
        server_id="lua-language-server",
        extensions=(".lua",),
        language_ids=("lua",),
        resolve_root=_root_lua,
        build_spawn=_spawn_lua_ls,
        description="Lua — lua-language-server",
        category="core",
        tags=("community"),
    ),
]


def initialize_builtin_servers() -> None:
    """Register all built-in servers with the global registry."""
    for server in BUILTIN_SERVERS:
        try:
            _REGISTRY.register(server)
        except ValueError:
            pass  # Already registered


# Auto-initialize on import
initialize_builtin_servers()


# ---------------------------------------------------------------------------
# JSON Schema for server definitions (for config validation)
# ---------------------------------------------------------------------------

SERVER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LSP Server Definition",
    "type": "object",
    "required": ["server_id", "extensions", "description", "category"],
    "properties": {
        "server_id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "extensions": {
            "type": "array",
            "items": {"type": "string", "pattern": "^\\..+$|^[A-Za-z0-9_-]+$"},
            "minItems": 1,
        },
        "language_ids": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"},
        "category": {"type": "string", "enum": ["core", "community", "experimental"]},
        "min_version": {"type": ["string", "null"]},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}

REGISTRY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LSP Registry Configuration",
    "type": "object",
    "properties": {
        "servers": {
            "type": "array",
            "items": SERVER_SCHEMA,
        },
        "install_strategy": {"type": "string", "enum": ["auto", "manual", "off"]},
        "disabled_servers": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


__all__ = [
    "ServerDef",
    "ServerContext",
    "SpawnSpec",
    "LSPRegistry",
    "get_registry",
    "register_server",
    "initialize_builtin_servers",
    "BUILTIN_SERVERS",
    "LANGUAGE_BY_EXT",
    "SERVER_SCHEMA",
    "REGISTRY_SCHEMA",
    "nearest_root",
    "resolve_workspace_for_file",
]