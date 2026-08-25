"""LSP Server Registry Package

A governed catalog of Language Server Protocol servers for hummbl-governance.
"""

from hummbl_governance.lsp_registry.registry import (
    ServerDef,
    ServerContext,
    SpawnSpec,
    LSPRegistry,
    get_registry,
    register_server,
    initialize_builtin_servers,
    BUILTIN_SERVERS,
    LANGUAGE_BY_EXT,
    SERVER_SCHEMA,
    REGISTRY_SCHEMA,
    nearest_root,
    resolve_workspace_for_file,
)

from hummbl_governance.lsp_registry.workspace import (
    nearest_root as _nearest_root,
    resolve_workspace_for_file as _resolve_workspace_for_file,
    clear_cache,
    is_inside_workspace,
    get_workspace_root,
)

from hummbl_governance.lsp_registry.install import (
    InstallRecipe,
    RECIPES,
    try_install,
    verify_install,
    list_available_recipes,
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