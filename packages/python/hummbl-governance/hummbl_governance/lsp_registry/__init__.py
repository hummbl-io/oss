"""LSP Server Registry Package

A governed catalog of Language Server Protocol servers for hummbl-governance.
"""

from hummbl_governance.lsp_registry.install import (
    RECIPES,
    InstallRecipe,
    list_available_recipes,
    try_install,
    verify_install,
)
from hummbl_governance.lsp_registry.registry import (
    BUILTIN_SERVERS,
    LANGUAGE_BY_EXT,
    REGISTRY_SCHEMA,
    SERVER_SCHEMA,
    LSPRegistry,
    ServerContext,
    ServerDef,
    SpawnSpec,
    get_registry,
    initialize_builtin_servers,
    nearest_root,
    register_server,
    resolve_workspace_for_file,
)
from hummbl_governance.lsp_registry.workspace import (
    clear_cache,
    get_workspace_root,
    is_inside_workspace,
)

__version__ = "0.1.0"

__all__ = [
    # Core types
    "ServerDef",
    "ServerContext",
    "SpawnSpec",
    "LSPRegistry",
    # Registry functions
    "get_registry",
    "register_server",
    "initialize_builtin_servers",
    "BUILTIN_SERVERS",
    "LANGUAGE_BY_EXT",
    # Schemas
    "SERVER_SCHEMA",
    "REGISTRY_SCHEMA",
    # Workspace utilities
    "nearest_root",
    "resolve_workspace_for_file",
    "clear_cache",
    "is_inside_workspace",
    "get_workspace_root",
    # Install utilities
    "InstallRecipe",
    "RECIPES",
    "try_install",
    "verify_install",
    "list_available_recipes",
]
